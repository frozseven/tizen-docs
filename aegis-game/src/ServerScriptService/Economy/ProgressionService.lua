--!strict
-- Simple leveling: completing contracts grants XP; crossing a level's XP
-- threshold increases Level and grants a small MaxHealth bonus, applied
-- immediately if the player is currently alive. Level (and the XP/health
-- bonus that comes with it) resets to 1 on soft-permadeath, matching the
-- spec's "respawn as a Level 1 engineer" - progression is meant to reset
-- along with everything else the wipe takes.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local DataHandler = require(ServerScriptService.Data.DataHandler)
local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local BASE_MAX_HEALTH = 100
local MAX_HEALTH_PER_LEVEL = 20 -- bonus max health per level above 1

local ProgressionService = {}

local function xpToNextLevel(level: number): number
	return level * 100
end

local function computeMaxHealth(level: number): number
	return BASE_MAX_HEALTH + (level - 1) * MAX_HEALTH_PER_LEVEL
end

local function applyMaxHealth(player: Player, level: number)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if humanoid == nil then
		return
	end

	local newMaxHealth = computeMaxHealth(level)
	local wasFull = humanoid.Health >= humanoid.MaxHealth
	humanoid.MaxHealth = newMaxHealth
	if wasFull then
		humanoid.Health = newMaxHealth
	end
end

-- Call whenever a player earns XP (currently just contract completion).
function ProgressionService.AddXP(player: Player, amount: number)
	local profile = DataHandler.GetProfile(player)
	if profile == nil then
		return
	end

	profile.Data.XP += amount

	local leveledUp = false
	while profile.Data.XP >= xpToNextLevel(profile.Data.Level) do
		profile.Data.XP -= xpToNextLevel(profile.Data.Level)
		profile.Data.Level += 1
		leveledUp = true
	end

	DataHandler.SyncLeaderstats(player)

	if leveledUp then
		applyMaxHealth(player, profile.Data.Level)
		RemoteEvents.Get("ContractNotification"):FireClient(
			player,
			"Level Up!",
			`You are now Level {profile.Data.Level} (+{MAX_HEALTH_PER_LEVEL} max health)`
		)
	end
end

local function onCharacterAdded(player: Player, character: Model)
	local profile = DataHandler.WaitForProfile(player, 10)
	if profile == nil then
		return
	end
	applyMaxHealth(player, profile.Data.Level)
end

function ProgressionService.Init()
	local function handlePlayer(player: Player)
		player.CharacterAdded:Connect(function(character)
			onCharacterAdded(player, character)
		end)
		if player.Character ~= nil then
			task.spawn(onCharacterAdded, player, player.Character)
		end
	end

	for _, player in Players:GetPlayers() do
		handlePlayer(player)
	end
	Players.PlayerAdded:Connect(handlePlayer)
end

return ProgressionService
