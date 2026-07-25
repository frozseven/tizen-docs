--!strict
-- Player data persistence: ProfileStore for auto-saving/session-locking,
-- SOSDF for compact vehicle storage within a profile.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local ProfileStore = require(ServerScriptService.ServerPackages.ProfileStore)
local SOSDF = require(ReplicatedStorage.Shared.Modules.SOSDF)
local ProfileTemplate = require(script.Parent.ProfileTemplate)

type VehicleNode = SOSDF.VehicleNode

local PlayerStore = ProfileStore.New("PlayerData", ProfileTemplate)

local Profiles: { [Player]: typeof(PlayerStore:StartSessionAsync(...)) } = {}

local DataHandler = {}

-- leaderstats is a Roblox convention (a "leaderstats" Folder of Value
-- instances under the Player) that both auto-populates the default player
-- list and gives clients an easy, already-replicated way to read Cash/Level
-- without a dedicated RemoteEvent - PlayerHUD reads these directly.
local function createLeaderstats(player: Player, profile): Folder
	local leaderstats = Instance.new("Folder")
	leaderstats.Name = "leaderstats"

	local cash = Instance.new("IntValue")
	cash.Name = "Cash"
	cash.Value = profile.Data.Cash
	cash.Parent = leaderstats

	local level = Instance.new("IntValue")
	level.Name = "Level"
	level.Value = profile.Data.Level
	level.Parent = leaderstats

	leaderstats.Parent = player
	return leaderstats
end

local function onPlayerAdded(player: Player)
	local profile = PlayerStore:StartSessionAsync(`{player.UserId}`, {
		Cancel = function()
			return player.Parent ~= Players
		end,
	})

	if profile == nil then
		player:Kick("Your data failed to load. Please rejoin.")
		return
	end

	profile:AddUserId(player.UserId)
	profile:Reconcile()

	profile.OnSessionEnd:Connect(function()
		Profiles[player] = nil
		player:Kick("Your data session was taken over by another server.")
	end)

	if player.Parent ~= Players then
		profile:EndSession()
		return
	end

	Profiles[player] = profile
	createLeaderstats(player, profile)
end

local function onPlayerRemoving(player: Player)
	local profile = Profiles[player]
	if profile ~= nil then
		profile:EndSession()
	end
end

function DataHandler.GetProfile(player: Player)
	return Profiles[player]
end

-- Profile loading is asynchronous (StartSessionAsync), so it may not be
-- ready yet the moment a character first spawns; poll instead of assuming.
function DataHandler.WaitForProfile(player: Player, timeout: number)
	local start = os.clock()
	while os.clock() - start < timeout do
		local profile = Profiles[player]
		if profile ~= nil then
			return profile
		end
		task.wait(0.1)
	end
	return nil
end

function DataHandler.SaveVehicle(player: Player, vehicleId: string, name: string, nodes: { VehicleNode }): boolean
	local profile = Profiles[player]
	if profile == nil then
		return false
	end

	profile.Data.Vehicles[vehicleId] = {
		Name = name,
		Data = SOSDF.EncodeVehicle(nodes),
	}

	return true
end

-- Call after any change to profile.Data.Cash/Level (contract payout, soft-
-- permadeath wipe, etc.) so the client-visible leaderstats stay in sync.
function DataHandler.SyncLeaderstats(player: Player)
	local profile = Profiles[player]
	if profile == nil then
		return
	end

	local leaderstats = player:FindFirstChild("leaderstats")
	if leaderstats == nil then
		return
	end

	local cash = leaderstats:FindFirstChild("Cash") :: IntValue?
	local level = leaderstats:FindFirstChild("Level") :: IntValue?
	if cash ~= nil then
		cash.Value = profile.Data.Cash
	end
	if level ~= nil then
		level.Value = profile.Data.Level
	end
end

function DataHandler.LoadVehicle(player: Player, vehicleId: string): { VehicleNode }?
	local profile = Profiles[player]
	if profile == nil then
		return nil
	end

	local record = profile.Data.Vehicles[vehicleId]
	if record == nil then
		return nil
	end

	return SOSDF.DecodeVehicle(record.Data)
end

function DataHandler.Init()
	for _, player in Players:GetPlayers() do
		task.spawn(onPlayerAdded, player)
	end

	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)
end

return DataHandler
