--!strict
-- Minimal keyboard-driven test harness for the vehicle assembly system.
-- A real placement UI (mouse raycasting, ghost preview) is future work;
-- this exists to exercise and demonstrate the server-authoritative
-- assembly/save/load pipeline end to end.
--
-- P: spawn a chassis in front of you
-- 1-4: place StructuralFrame / Wheel / Motor / Suspension at the next grid slot
-- K: save the vehicle
-- L: load the saved vehicle

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local GRID_SIZE = 4
local COLUMNS = 5
local VEHICLE_ID = "Test"

local placementIndex = 0

local function nextOffset(): Vector3
	local column = placementIndex % COLUMNS
	local row = math.floor(placementIndex / COLUMNS)
	placementIndex += 1
	return Vector3.new(column * GRID_SIZE, 0, row * GRID_SIZE)
end

local KEY_ACTIONS: { [Enum.KeyCode]: () -> () } = {
	[Enum.KeyCode.P] = function()
		RemoteEvents.Get("SpawnChassis"):FireServer()
		placementIndex = 0
	end,
	[Enum.KeyCode.One] = function()
		RemoteEvents.Get("PlaceComponent"):FireServer(1, nextOffset())
	end,
	[Enum.KeyCode.Two] = function()
		RemoteEvents.Get("PlaceComponent"):FireServer(2, nextOffset())
	end,
	[Enum.KeyCode.Three] = function()
		RemoteEvents.Get("PlaceComponent"):FireServer(3, nextOffset())
	end,
	[Enum.KeyCode.Four] = function()
		RemoteEvents.Get("PlaceComponent"):FireServer(4, nextOffset())
	end,
	[Enum.KeyCode.K] = function()
		RemoteEvents.Get("SaveVehicle"):FireServer(VEHICLE_ID, "My Truck")
	end,
	[Enum.KeyCode.L] = function()
		RemoteEvents.Get("LoadVehicle"):FireServer(VEHICLE_ID)
	end,
}

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end

	local action = KEY_ACTIONS[input.KeyCode]
	if action ~= nil then
		action()
	end
end)
