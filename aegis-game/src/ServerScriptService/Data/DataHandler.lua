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
