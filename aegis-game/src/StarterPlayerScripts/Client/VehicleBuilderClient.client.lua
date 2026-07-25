--!strict
-- Vehicle building: aim with the mouse over an adjustable horizontal build
-- layer relative to your chassis, see a live ghost preview of where the
-- selected component will land, and left-click to place it. This replaces
-- the earlier keypress-only harness (which placed parts in a fixed row
-- regardless of where you were looking) with something closer to how a
-- real player would actually build.
--
-- All placement is still validated and grid-snapped authoritatively on the
-- server (VehicleAssemblyService/VehicleNodeSystem) - the client-side snap
-- here is only a preview and can't be trusted.
--
-- P: spawn a bare chassis in front of you
-- T: spawn a complete, correctly-assembled starter truck (4 wheels + seat)
-- B: toggle Build Mode (shows the ghost preview, enables placing)
-- 1-4: select StructuralFrame / Wheel / Motor / Suspension to place
-- 5: select DriverSeat to place
-- Q / E: lower / raise the build layer by one grid step
-- Left Click (while Build Mode is on): place the selected component
-- K: save the vehicle
-- L: load the saved vehicle
-- C: request a new delivery contract

local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local GRID_SIZE = 4 -- studs; mirrors VehicleNodeSystem's grid resolution for the preview only
local VEHICLE_ROOT_TAG = "VehicleRoot"
local MAX_PLACEMENT_DISTANCE = 40 -- studs; mirrors VehicleAssemblyService's server-side clamp for the preview only
local VEHICLE_ID = "Test"

type ComponentDefinition = { Name: string, Size: Vector3, Color: Color3 }

-- Cosmetic mirror of VehicleAssemblyService's COMPONENT_DEFINITIONS, used
-- only to size/color the ghost preview - the server is the actual authority
-- on what each typeId means.
local COMPONENT_DEFINITIONS: { [number]: ComponentDefinition } = {
	[1] = { Name = "StructuralFrame", Size = Vector3.new(4, 1, 4), Color = Color3.fromRGB(120, 120, 130) },
	[2] = { Name = "Wheel", Size = Vector3.new(2, 2, 1), Color = Color3.fromRGB(40, 40, 40) },
	[3] = { Name = "Motor", Size = Vector3.new(2, 2, 2), Color = Color3.fromRGB(180, 60, 40) },
	[4] = { Name = "Suspension", Size = Vector3.new(1, 3, 1), Color = Color3.fromRGB(60, 90, 160) },
	[5] = { Name = "DriverSeat", Size = Vector3.new(2, 1, 2), Color = Color3.fromRGB(200, 200, 60) },
}

local player = Players.LocalPlayer

local buildModeActive = false
local selectedTypeId = 2 -- Wheel by default, the most commonly placed part
local buildHeight = 0 -- studs, relative to the chassis root
local currentOffset: Vector3? = nil

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "VehicleBuildHUD"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local statusLabel = Instance.new("TextLabel")
statusLabel.Name = "BuildStatus"
statusLabel.AnchorPoint = Vector2.new(0, 1)
statusLabel.Position = UDim2.new(0, 10, 1, -10)
statusLabel.Size = UDim2.new(0, 420, 0, 26)
statusLabel.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
statusLabel.BackgroundTransparency = 0.3
statusLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
statusLabel.Font = Enum.Font.Gotham
statusLabel.TextSize = 14
statusLabel.TextXAlignment = Enum.TextXAlignment.Left
statusLabel.Text = "Build Mode: OFF (press B)"
statusLabel.Visible = false
statusLabel.Parent = screenGui

local statusCorner = Instance.new("UICorner")
statusCorner.CornerRadius = UDim.new(0, 4)
statusCorner.Parent = statusLabel

local ghost = Instance.new("Part")
ghost.Name = "BuildGhost"
ghost.Anchored = true
ghost.CanCollide = false
ghost.CanQuery = false
ghost.CastShadow = false
ghost.Transparency = 0.5
ghost.Material = Enum.Material.ForceField
ghost.Parent = nil

local function findOwnVehicleRoot(): BasePart?
	for _, instance in CollectionService:GetTagged(VEHICLE_ROOT_TAG) do
		if instance:IsA("BasePart") and instance:GetAttribute("OwnerUserId") == player.UserId then
			return instance
		end
	end
	return nil
end

local function updateStatusLabel()
	local definition = COMPONENT_DEFINITIONS[selectedTypeId]
	local name = if definition ~= nil then definition.Name else "?"
	statusLabel.Text = `Build Mode: ON | Placing: {name} (1-5) | Layer: {buildHeight} (Q/E) | Click to place`
end

local function setBuildMode(active: boolean)
	buildModeActive = active
	statusLabel.Visible = active
	if active then
		updateStatusLabel()
	else
		ghost.Parent = nil
		currentOffset = nil
	end
end

local function rayPlaneIntersection(origin: Vector3, direction: Vector3, planeY: number): Vector3?
	if math.abs(direction.Y) < 1e-4 then
		return nil
	end
	local t = (planeY - origin.Y) / direction.Y
	if t < 0 then
		return nil
	end
	return origin + direction * t
end

local function snapToGrid(value: number): number
	return math.round(value / GRID_SIZE) * GRID_SIZE
end

local function updateGhost()
	if not buildModeActive then
		return
	end

	local root = findOwnVehicleRoot()
	local camera = Workspace.CurrentCamera
	if root == nil or camera == nil then
		ghost.Parent = nil
		currentOffset = nil
		return
	end

	local mouseLocation = UserInputService:GetMouseLocation()
	local ray = camera:ViewportPointToRay(mouseLocation.X, mouseLocation.Y)
	local planeY = root.Position.Y + buildHeight

	local worldPoint = rayPlaneIntersection(ray.Origin, ray.Direction.Unit, planeY)
	if worldPoint == nil then
		ghost.Parent = nil
		currentOffset = nil
		return
	end

	local localPoint = root.CFrame:PointToObjectSpace(worldPoint)
	local snappedOffset = Vector3.new(snapToGrid(localPoint.X), buildHeight, snapToGrid(localPoint.Z))
	currentOffset = snappedOffset

	local definition = COMPONENT_DEFINITIONS[selectedTypeId]
	if definition == nil then
		ghost.Parent = nil
		return
	end

	ghost.Size = definition.Size
	ghost.CFrame = root.CFrame * CFrame.new(snappedOffset)
	ghost.Color = if snappedOffset.Magnitude <= MAX_PLACEMENT_DISTANCE
		then definition.Color
		else Color3.fromRGB(200, 60, 60)
	ghost.Parent = Workspace
end

local function placeSelected()
	if not buildModeActive or currentOffset == nil then
		return
	end
	RemoteEvents.Get("PlaceComponent"):FireServer(selectedTypeId, currentOffset)
end

local SELECT_KEYS: { [Enum.KeyCode]: number } = {
	[Enum.KeyCode.One] = 1,
	[Enum.KeyCode.Two] = 2,
	[Enum.KeyCode.Three] = 3,
	[Enum.KeyCode.Four] = 4,
	[Enum.KeyCode.Five] = 5,
}

local OTHER_ACTIONS: { [Enum.KeyCode]: () -> () } = {
	[Enum.KeyCode.P] = function()
		RemoteEvents.Get("SpawnChassis"):FireServer()
	end,
	[Enum.KeyCode.T] = function()
		RemoteEvents.Get("SpawnStarterTruck"):FireServer()
	end,
	[Enum.KeyCode.B] = function()
		setBuildMode(not buildModeActive)
	end,
	[Enum.KeyCode.Q] = function()
		if buildModeActive then
			buildHeight -= GRID_SIZE
			updateStatusLabel()
		end
	end,
	[Enum.KeyCode.E] = function()
		if buildModeActive then
			buildHeight += GRID_SIZE
			updateStatusLabel()
		end
	end,
	[Enum.KeyCode.K] = function()
		RemoteEvents.Get("SaveVehicle"):FireServer(VEHICLE_ID, "My Truck")
	end,
	[Enum.KeyCode.L] = function()
		RemoteEvents.Get("LoadVehicle"):FireServer(VEHICLE_ID)
	end,
	[Enum.KeyCode.C] = function()
		RemoteEvents.Get("RequestContract"):FireServer()
	end,
}

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end

	if input.UserInputType == Enum.UserInputType.MouseButton1 then
		placeSelected()
		return
	end

	local selectType = SELECT_KEYS[input.KeyCode]
	if selectType ~= nil then
		selectedTypeId = selectType
		if buildModeActive then
			updateStatusLabel()
		end
		return
	end

	local action = OTHER_ACTIONS[input.KeyCode]
	if action ~= nil then
		action()
	end
end)

RunService.RenderStepped:Connect(updateGhost)
