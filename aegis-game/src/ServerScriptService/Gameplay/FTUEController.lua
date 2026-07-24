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

-- DataHandler loads a profile asynchronously on join, so it may not be
-- ready yet the moment a character first spawns; wait for it rather than
-- silently skipping FTUE.
local function waitForProfile(player: Player, timeout: number)
	local start = os.clock()
	while os.clock() - start < timeout do
		local profile = DataHandler.GetProfile(player)
		if profile ~= nil then
			return profile
		end
		task.wait(0.1)
	end
	return nil
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
	local profile = waitForProfile(player, PROFILE_WAIT_TIMEOUT)
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
