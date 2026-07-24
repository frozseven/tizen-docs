--!strict
-- Server-authoritative vehicle assembly: spawns a chassis, validates and
-- welds components onto it at grid-snapped offsets, and bridges the live
-- node graph to ProfileStore via SOSDF for save/load.
--
-- Placeholder geometry (plain colored Parts) stands in for real component
-- models; swap CreateComponentPart's Instance.new("Part") calls for real
-- assets once art exists. Chassis/components are anchored here since
-- unanchored rigid-body driving physics is a separate later task.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)
local VehicleNodeSystem = require(script.Parent.VehicleNodeSystem)
local DataHandler = require(ServerScriptService.Data.DataHandler)

local MAX_PLACEMENT_DISTANCE = 40 -- studs from root chassis
local MAX_COMPONENTS_PER_VEHICLE = 200
local MAX_ID_LENGTH = 32

type ComponentDefinition = {
	Name: string,
	Size: Vector3,
	Color: Color3,
}

local COMPONENT_DEFINITIONS: { [number]: ComponentDefinition } = {
	[1] = { Name = "StructuralFrame", Size = Vector3.new(4, 1, 4), Color = Color3.fromRGB(120, 120, 130) },
	[2] = { Name = "Wheel", Size = Vector3.new(2, 2, 1), Color = Color3.fromRGB(40, 40, 40) },
	[3] = { Name = "Motor", Size = Vector3.new(2, 2, 2), Color = Color3.fromRGB(180, 60, 40) },
	[4] = { Name = "Suspension", Size = Vector3.new(1, 3, 1), Color = Color3.fromRGB(60, 90, 160) },
}

type VehicleState = {
	RootPart: BasePart,
	Model: Model,
	Graph: VehicleNodeSystem.Graph,
}

local vehicles: { [Player]: VehicleState } = {}

local VehicleAssemblyService = {}

local function createChassis(cframe: CFrame): (Model, BasePart)
	local root = Instance.new("Part")
	root.Name = "ChassisRoot"
	root.Size = Vector3.new(6, 1, 10)
	root.Color = Color3.fromRGB(200, 180, 60)
	root.CFrame = cframe
	root.Anchored = true

	local model = Instance.new("Model")
	model.Name = "Vehicle"
	root.Parent = model
	model.PrimaryPart = root

	return model, root
end

local function createComponentPart(typeId: number, worldCFrame: CFrame): BasePart?
	local definition = COMPONENT_DEFINITIONS[typeId]
	if definition == nil then
		return nil
	end

	local part = Instance.new("Part")
	part.Name = definition.Name
	part.Size = definition.Size
	part.Color = definition.Color
	part.CFrame = worldCFrame
	part.Anchored = true
	return part
end

local function weldToRoot(root: BasePart, part: BasePart)
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = root
	weld.Part1 = part
	weld.Parent = part
end

local function onSpawnChassis(player: Player)
	local existing = vehicles[player]
	if existing ~= nil then
		existing.Model:Destroy()
	end

	local character = player.Character
	local spawnCFrame = if character ~= nil and character.PrimaryPart ~= nil
		then character.PrimaryPart.CFrame * CFrame.new(0, 3, -10)
		else CFrame.new(0, 5, 0)

	local model, root = createChassis(spawnCFrame)
	model.Parent = Workspace

	vehicles[player] = {
		RootPart = root,
		Model = model,
		Graph = VehicleNodeSystem.new(),
	}
end

local function onPlaceComponent(player: Player, typeId: unknown, offset: unknown)
	local vehicle = vehicles[player]
	if vehicle == nil then
		return
	end

	if typeof(typeId) ~= "number" or COMPONENT_DEFINITIONS[typeId] == nil then
		return
	end

	if typeof(offset) ~= "Vector3" or (offset :: Vector3).Magnitude > MAX_PLACEMENT_DISTANCE then
		return
	end

	if vehicle.Graph.NextUID > MAX_COMPONENTS_PER_VEHICLE then
		return
	end

	local snappedOffset = VehicleNodeSystem.SnapToGrid(offset :: Vector3)
	local relativeCFrame = CFrame.new(snappedOffset)

	if VehicleNodeSystem.IsOccupied(vehicle.Graph, relativeCFrame) then
		return
	end

	local worldCFrame = vehicle.RootPart.CFrame * relativeCFrame
	local part = createComponentPart(typeId, worldCFrame)
	if part == nil then
		return
	end
	part.Parent = vehicle.Model
	weldToRoot(vehicle.RootPart, part)

	VehicleNodeSystem.AddNode(vehicle.Graph, typeId, relativeCFrame, part)
end

local function isValidId(value: unknown): boolean
	return typeof(value) == "string" and #(value :: string) > 0 and #(value :: string) <= MAX_ID_LENGTH
end

local function onSaveVehicle(player: Player, vehicleId: unknown, name: unknown)
	local vehicle = vehicles[player]
	if vehicle == nil then
		return
	end

	if not isValidId(vehicleId) or not isValidId(name) then
		return
	end

	local nodes = VehicleNodeSystem.Serialize(vehicle.Graph)
	DataHandler.SaveVehicle(player, vehicleId :: string, name :: string, nodes)
end

local function onLoadVehicle(player: Player, vehicleId: unknown)
	if not isValidId(vehicleId) then
		return
	end

	local nodes = DataHandler.LoadVehicle(player, vehicleId :: string)
	if nodes == nil then
		return
	end

	onSpawnChassis(player)
	local vehicle = vehicles[player]
	if vehicle == nil then
		return
	end

	for _, node in nodes do
		local worldCFrame = vehicle.RootPart.CFrame * node.CFrame
		local part = createComponentPart(node.TypeId, worldCFrame)
		if part == nil then
			continue
		end
		part.Parent = vehicle.Model
		weldToRoot(vehicle.RootPart, part)

		VehicleNodeSystem.AddNode(vehicle.Graph, node.TypeId, node.CFrame, part)
	end
end

local STARTER_WHEEL_OFFSETS = {
	Vector3.new(-4, 0, -4),
	Vector3.new(4, 0, -4),
	Vector3.new(-4, 0, 4),
	Vector3.new(4, 0, 4),
}
local WHEEL_TYPE_ID = 2

-- Server-initiated (not client-requested), for the FTUE controller: spawns
-- a chassis and welds four wheels onto it symmetrically, bypassing the
-- RemoteEvent path entirely since there's no player input to validate.
function VehicleAssemblyService.SpawnStarterTruck(player: Player)
	onSpawnChassis(player)
	local vehicle = vehicles[player]
	if vehicle == nil then
		return
	end

	for _, offset in STARTER_WHEEL_OFFSETS do
		local relativeCFrame = CFrame.new(VehicleNodeSystem.SnapToGrid(offset))
		local worldCFrame = vehicle.RootPart.CFrame * relativeCFrame
		local part = createComponentPart(WHEEL_TYPE_ID, worldCFrame)
		if part == nil then
			continue
		end
		part.Parent = vehicle.Model
		weldToRoot(vehicle.RootPart, part)

		VehicleNodeSystem.AddNode(vehicle.Graph, WHEEL_TYPE_ID, relativeCFrame, part)
	end
end

local function onPlayerRemoving(player: Player)
	local vehicle = vehicles[player]
	if vehicle ~= nil then
		vehicle.Model:Destroy()
		vehicles[player] = nil
	end
end

function VehicleAssemblyService.Init()
	RemoteEvents.Get("SpawnChassis").OnServerEvent:Connect(onSpawnChassis)
	RemoteEvents.Get("PlaceComponent").OnServerEvent:Connect(onPlaceComponent)
	RemoteEvents.Get("SaveVehicle").OnServerEvent:Connect(onSaveVehicle)
	RemoteEvents.Get("LoadVehicle").OnServerEvent:Connect(onLoadVehicle)

	Players.PlayerRemoving:Connect(onPlayerRemoving)
end

return VehicleAssemblyService
