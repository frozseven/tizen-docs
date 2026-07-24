--!strict
-- First-time user experience: on a new player's first spawn, place them
-- at the shipyard, grant a bare starter truck, and assign the first
-- delivery contract - no tutorial text, straight into play.

local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local DataHandler = require(ServerScriptService.Data.DataHandler)
local VehicleAssemblyService = require(ServerScriptService.Vehicles.VehicleAssemblyService)
local ContractService = require(ServerScriptService.Economy.ContractService)

local SHIPYARD_SPAWN_NAME = "ShipyardSpawn"
local FALLBACK_SPAWN = CFrame.new(0, 5, 0)
local PROFILE_WAIT_TIMEOUT = 10

local FTUEController = {}

local function getShipyardSpawnCFrame(): CFrame
	local marker = Workspace:FindFirstChild(SHIPYARD_SPAWN_NAME)
	if marker ~= nil and marker:IsA("BasePart") then
		return marker.CFrame + Vector3.new(0, 3, 0)
	end
	return FALLBACK_SPAWN
end

local function runFTUE(player: Player, character: Model)
	local rootPart = character:WaitForChild("HumanoidRootPart", 5) :: BasePart?
	if rootPart ~= nil then
		rootPart.CFrame = getShipyardSpawnCFrame()
	end

	VehicleAssemblyService.SpawnStarterTruck(player)
	ContractService.AssignRiverCampContract(player)
end

local function onCharacterAdded(player: Player, character: Model)
	local profile = DataHandler.WaitForProfile(player, PROFILE_WAIT_TIMEOUT)
	if profile == nil then
		return
	end

	if profile.Data.HasCompletedFTUE then
		return
	end

	profile.Data.HasCompletedFTUE = true
	runFTUE(player, character)
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		onCharacterAdded(player, character)
	end)
end

function FTUEController.Init()
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	Players.PlayerAdded:Connect(onPlayerAdded)
end

return FTUEController
