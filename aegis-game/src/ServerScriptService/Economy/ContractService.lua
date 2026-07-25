--!strict
-- Delivery-contract economy loop: assigns a contract, detects completion
-- by the player's VEHICLE (not character) reaching the dropoff zone, pays
-- out, and immediately assigns a new (different) contract - a repeatable
-- loop rather than a one-shot demo.
--
-- Completion is checked periodically via spatial overlap
-- (GetPartBoundsInBox) rather than Touched/TouchEnded - the extraction
-- zone work showed Touched is unreliable for a fast-moving, non-colliding
-- object passing through a thin zone.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)
local DataHandler = require(ServerScriptService.Data.DataHandler)
local VehicleAssemblyService = require(ServerScriptService.Vehicles.VehicleAssemblyService)

local CHECK_INTERVAL = 1 -- seconds between dropoff checks per player

type Contract = {
	Id: string,
	Description: string,
	DropoffPartName: string,
	Reward: number,
}

local CONTRACTS: { Contract } = {
	{
		Id = "RiverCampDelivery",
		Description = "Deliver to the river camp",
		DropoffPartName = "RiverCampDropoff",
		Reward = 50,
	},
	{
		Id = "MountainDepotDelivery",
		Description = "Deliver to the mountain depot",
		DropoffPartName = "MountainDepotDropoff",
		Reward = 75,
	},
	{
		Id = "CoastalOutpostDelivery",
		Description = "Deliver to the coastal outpost",
		DropoffPartName = "CoastalOutpostDropoff",
		Reward = 100,
	},
}

local activeContracts: { [Player]: Contract } = {}
local lastCheckTime: { [Player]: number } = {}

local ContractService = {}

local function notifyPlayer(player: Player, title: string, text: string)
	RemoteEvents.Get("ContractNotification"):FireClient(player, title, text)
end

local function pickNextContract(excludeId: string?): Contract
	local candidates: { Contract } = {}
	for _, contract in CONTRACTS do
		if contract.Id ~= excludeId then
			table.insert(candidates, contract)
		end
	end
	if #candidates == 0 then
		candidates = CONTRACTS
	end
	return candidates[math.random(1, #candidates)]
end

local function assignContract(player: Player, contract: Contract)
	activeContracts[player] = contract
	lastCheckTime[player] = os.clock()
	notifyPlayer(player, "New Contract", contract.Description)
end

local function completeContract(player: Player, contract: Contract)
	local profile = DataHandler.GetProfile(player)
	if profile ~= nil then
		profile.Data.Cash += contract.Reward
	end

	notifyPlayer(player, "Contract Complete", `+{contract.Reward} cash`)

	assignContract(player, pickNextContract(contract.Id))
end

local function isVehicleAtDropoff(player: Player, contract: Contract): boolean
	local zone = Workspace:FindFirstChild(contract.DropoffPartName)
	if zone == nil or not zone:IsA("BasePart") then
		return false
	end

	local vehicleModel = VehicleAssemblyService.GetVehicleModel(player)
	if vehicleModel == nil then
		return false
	end

	local overlapParams = OverlapParams.new()
	overlapParams.FilterType = Enum.RaycastFilterType.Include
	overlapParams.FilterDescendantsInstances = { vehicleModel }

	return #Workspace:GetPartBoundsInBox(zone.CFrame, zone.Size, overlapParams) > 0
end

local function step()
	local now = os.clock()

	for player, contract in activeContracts do
		local last = lastCheckTime[player] or 0
		if now - last < CHECK_INTERVAL then
			continue
		end
		lastCheckTime[player] = now

		if isVehicleAtDropoff(player, contract) then
			completeContract(player, contract)
		end
	end
end

function ContractService.AssignNextContract(player: Player)
	assignContract(player, pickNextContract(nil))
end

function ContractService.Init()
	RunService.Heartbeat:Connect(step)

	Players.PlayerRemoving:Connect(function(player)
		activeContracts[player] = nil
		lastCheckTime[player] = nil
	end)
end

return ContractService
