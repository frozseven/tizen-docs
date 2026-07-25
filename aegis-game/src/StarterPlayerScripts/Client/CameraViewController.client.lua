--!strict
-- Lets each player choose their own camera view: Third Person (avatar
-- always visible) or First Person (locked, no avatar - standard FPS view).
-- Purely cosmetic/client-side, so it needs no server involvement.
--
-- By default, Roblox's camera lets you zoom in past a threshold where it
-- silently switches to first person and hides your own avatar - which is
-- what looked like a "transparent player" bug. Third Person mode here
-- pins CameraMinZoomDistance above that threshold so it can never happen
-- by accident; First Person mode uses Roblox's real locked first-person
-- camera instead, for players who prefer that on purpose.

local Players = game:GetService("Players")
local UserInputService = game:GetService("UserInputService")

local player = Players.LocalPlayer

local THIRD_PERSON_MIN_ZOOM = 10 -- studs; comfortably above the built-in first-person threshold
local TOGGLE_KEY = Enum.KeyCode.V

local isFirstPerson = false

local function applyMode()
	if isFirstPerson then
		player.CameraMode = Enum.CameraMode.LockFirstPerson
	else
		player.CameraMode = Enum.CameraMode.Classic
		player.CameraMinZoomDistance = THIRD_PERSON_MIN_ZOOM
	end
end

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "CameraViewToggle"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local button = Instance.new("TextButton")
button.Name = "ViewToggleButton"
button.Size = UDim2.new(0, 170, 0, 36)
button.Position = UDim2.new(1, -180, 0, 10)
button.BackgroundColor3 = Color3.fromRGB(30, 30, 30)
button.BackgroundTransparency = 0.2
button.TextColor3 = Color3.fromRGB(255, 255, 255)
button.Font = Enum.Font.GothamBold
button.TextSize = 16
button.Text = "View: Third Person (V)"
button.Parent = screenGui

local corner = Instance.new("UICorner")
corner.CornerRadius = UDim.new(0, 6)
corner.Parent = button

local function updateButtonText()
	button.Text = if isFirstPerson then "View: First Person (V)" else "View: Third Person (V)"
end

local function toggleView()
	isFirstPerson = not isFirstPerson
	applyMode()
	updateButtonText()
end

button.MouseButton1Click:Connect(toggleView)

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end
	if input.KeyCode == TOGGLE_KEY then
		toggleView()
	end
end)

applyMode()
