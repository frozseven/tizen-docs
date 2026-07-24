--!strict
-- Tracks which players are currently standing inside the extraction zone
-- (a marked "ExtractionZone" part). If a player's character dies while
-- inside, that's a soft-permadeath trigger rather than a normal respawn.

local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local SoftPermadeathService = require(ServerScriptService.Gameplay.SoftPermadeathService)

local EXTRACTION_ZONE_NAME = "ExtractionZone"

local playersInZone: { [Player]: boolean } = {}

local ExtractionZoneService = {}

local function getPlayerFromZoneTouch(hit: BasePart): Player?
	local character = hit:FindFirstAncestorOfClass("Model")
	if character == nil then
		return nil
	end
	return Players:GetPlayerFromCharacter(character)
end

local function onZoneTouched(hit: BasePart)
	local player = getPlayerFromZoneTouch(hit)
	if player ~= nil then
		playersInZone[player] = true
	end
end

local function onZoneTouchEnded(hit: BasePart)
	local player = getPlayerFromZoneTouch(hit)
	if player ~= nil then
		playersInZone[player] = nil
	end
end

local function onCharacterAdded(player: Player, character: Model)
	local humanoid = character:WaitForChild("Humanoid", 5) :: Humanoid?
	if humanoid == nil then
		return
	end

	humanoid.Died:Connect(function()
		if playersInZone[player] then
			playersInZone[player] = nil
			SoftPermadeathService.TriggerWipe(player)
		end
	end)
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
end

function ExtractionZoneService.Init()
	local zone = Workspace:FindFirstChild(EXTRACTION_ZONE_NAME)
	if zone ~= nil and zone:IsA("BasePart") then
		zone.Touched:Connect(onZoneTouched)
		zone.TouchEnded:Connect(onZoneTouchEnded)
	end

	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end
	Players.PlayerAdded:Connect(onPlayerAdded)

	Players.PlayerRemoving:Connect(function(player)
		playersInZone[player] = nil
	end)
end

return ExtractionZoneService
