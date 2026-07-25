--!strict
-- Detects whether a player died inside the extraction zone (a marked
-- "ExtractionZone" part). Checks spatial overlap directly at the moment
-- of death rather than tracking occupancy via Touched/TouchEnded over
-- time - the zone is non-colliding (players can walk through it), so a
-- falling or moving character can touch and un-touch it within a single
-- frame, making continuous occupancy tracking unreliable.

local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local SoftPermadeathService = require(ServerScriptService.Gameplay.SoftPermadeathService)

local EXTRACTION_ZONE_NAME = "ExtractionZone"

local ExtractionZoneService = {}

local function diedInExtractionZone(character: Model): boolean
	local zone = Workspace:FindFirstChild(EXTRACTION_ZONE_NAME)
	if zone == nil or not zone:IsA("BasePart") then
		return false
	end

	local overlapParams = OverlapParams.new()
	overlapParams.FilterType = Enum.RaycastFilterType.Include
	overlapParams.FilterDescendantsInstances = { character }

	local overlapping = Workspace:GetPartBoundsInBox(zone.CFrame, zone.Size, overlapParams)
	return #overlapping > 0
end

local function onCharacterAdded(player: Player, character: Model)
	local humanoid = character:WaitForChild("Humanoid", 5) :: Humanoid?
	if humanoid == nil then
		return
	end

	humanoid.Died:Connect(function()
		if diedInExtractionZone(character) then
			SoftPermadeathService.TriggerWipe(player)
		end
	end)
end

local function onPlayerAdded(player: Player)
	if player.Character ~= nil then
		onCharacterAdded(player, player.Character)
	end

	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
end

function ExtractionZoneService.Init()
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	Players.PlayerAdded:Connect(onPlayerAdded)
end

return ExtractionZoneService
