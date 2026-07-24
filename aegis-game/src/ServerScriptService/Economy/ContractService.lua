--!strict
-- Minimal delivery-contract system: assign a contract and detect
-- completion by proximity to a marked dropoff zone, paying out on
-- completion. Completion is currently driven by the player's character
-- reaching the zone rather than the vehicle itself - actual vehicle
-- driving physics is a separate later task, so this keeps contracts
-- testable today.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)
local DataHandler = require(ServerScriptService.Data.DataHandler)

type Contract = {
	Id: string,
	Description: string,
	DropoffPartName: string,
	Reward: number,
}

local RIVER_CAMP_CONTRACT: Contract = {
	Id = "RiverCampDelivery",
	Description = "Deliver to the river camp",
	DropoffPartName = "RiverCampDropoff",
	Reward = 50,
}

local activeContracts: { [Player]: Contract } = {}

local ContractService = {}

local function notifyPlayer(player: Player, title: string, text: string)
	RemoteEvents.Get("ContractNotification"):FireClient(player, title, text)
end

local function assignContract(player: Player, contract: Contract)
	activeContracts[player] = contract
	notifyPlayer(player, "New Contract", contract.Description)
end

local function completeContract(player: Player, contract: Contract)
	activeContracts[player] = nil

	local profile = DataHandler.GetProfile(player)
	if profile ~= nil then
		profile.Data.Cash += contract.Reward
	end

	notifyPlayer(player, "Contract Complete", `+{contract.Reward} cash`)
end

local function onDropoffTouched(hit: BasePart)
	local character = hit:FindFirstAncestorOfClass("Model")
	if character == nil then
		return
	end

	local player = Players:GetPlayerFromCharacter(character)
	if player == nil then
		return
	end

	local contract = activeContracts[player]
	if contract == nil then
		return
	end

	completeContract(player, contract)
end

function ContractService.AssignRiverCampContract(player: Player)
	assignContract(player, RIVER_CAMP_CONTRACT)
end

function ContractService.Init()
	local dropoff = Workspace:FindFirstChild(RIVER_CAMP_CONTRACT.DropoffPartName)
	if dropoff ~= nil and dropoff:IsA("BasePart") then
		dropoff.Touched:Connect(onDropoffTouched)
	end

	Players.PlayerRemoving:Connect(function(player)
		activeContracts[player] = nil
	end)
end

return ContractService
