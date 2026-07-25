--!strict
-- Persistent on-screen HUD: the player's own health, cash, level, and
-- current contract description. Cash/Level come from the player's
-- leaderstats (kept in sync with the profile by DataHandler); contract
-- text piggybacks on the existing ContractNotification remote already used
-- for toast popups, so no new remote is needed.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local player = Players.LocalPlayer

local screenGui = Instance.new("ScreenGui")
screenGui.Name = "PlayerHUD"
screenGui.ResetOnSpawn = false
screenGui.Parent = player:WaitForChild("PlayerGui")

local container = Instance.new("Frame")
container.Name = "HUDContainer"
container.Size = UDim2.new(0, 260, 0, 112)
container.Position = UDim2.new(0, 10, 0, 10)
container.BackgroundColor3 = Color3.fromRGB(20, 20, 20)
container.BackgroundTransparency = 0.3
container.Parent = screenGui

local containerCorner = Instance.new("UICorner")
containerCorner.CornerRadius = UDim.new(0, 6)
containerCorner.Parent = container

local padding = Instance.new("UIPadding")
padding.PaddingLeft = UDim.new(0, 10)
padding.PaddingRight = UDim.new(0, 10)
padding.PaddingTop = UDim.new(0, 8)
padding.PaddingBottom = UDim.new(0, 8)
padding.Parent = container

local layout = Instance.new("UIListLayout")
layout.SortOrder = Enum.SortOrder.LayoutOrder
layout.Padding = UDim.new(0, 4)
layout.Parent = container

local healthBarBackground = Instance.new("Frame")
healthBarBackground.Name = "HealthBarBackground"
healthBarBackground.LayoutOrder = 1
healthBarBackground.Size = UDim2.new(1, 0, 0, 18)
healthBarBackground.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
healthBarBackground.BorderSizePixel = 0
healthBarBackground.Parent = container

local healthBarCorner = Instance.new("UICorner")
healthBarCorner.CornerRadius = UDim.new(0, 4)
healthBarCorner.Parent = healthBarBackground

local healthBarFill = Instance.new("Frame")
healthBarFill.Name = "Fill"
healthBarFill.Size = UDim2.new(1, 0, 1, 0)
healthBarFill.BackgroundColor3 = Color3.fromRGB(60, 200, 90)
healthBarFill.BorderSizePixel = 0
healthBarFill.Parent = healthBarBackground

local healthFillCorner = Instance.new("UICorner")
healthFillCorner.CornerRadius = UDim.new(0, 4)
healthFillCorner.Parent = healthBarFill

local healthLabel = Instance.new("TextLabel")
healthLabel.BackgroundTransparency = 1
healthLabel.Size = UDim2.new(1, 0, 1, 0)
healthLabel.Font = Enum.Font.GothamBold
healthLabel.TextSize = 14
healthLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
healthLabel.Text = "100 / 100"
healthLabel.ZIndex = 2
healthLabel.Parent = healthBarBackground

local statsLabel = Instance.new("TextLabel")
statsLabel.Name = "StatsLabel"
statsLabel.LayoutOrder = 2
statsLabel.BackgroundTransparency = 1
statsLabel.Size = UDim2.new(1, 0, 0, 20)
statsLabel.Font = Enum.Font.Gotham
statsLabel.TextSize = 15
statsLabel.TextColor3 = Color3.fromRGB(255, 255, 255)
statsLabel.TextXAlignment = Enum.TextXAlignment.Left
statsLabel.Text = "Cash: 0   Level: 1"
statsLabel.Parent = container

local contractLabel = Instance.new("TextLabel")
contractLabel.Name = "ContractLabel"
contractLabel.LayoutOrder = 3
contractLabel.BackgroundTransparency = 1
contractLabel.Size = UDim2.new(1, 0, 0, 36)
contractLabel.Font = Enum.Font.Gotham
contractLabel.TextSize = 14
contractLabel.TextWrapped = true
contractLabel.TextColor3 = Color3.fromRGB(230, 230, 150)
contractLabel.TextXAlignment = Enum.TextXAlignment.Left
contractLabel.TextYAlignment = Enum.TextYAlignment.Top
contractLabel.Text = "No active contract"
contractLabel.Parent = container

local function updateHealth(humanoid: Humanoid)
	local fraction = math.clamp(humanoid.Health / humanoid.MaxHealth, 0, 1)
	healthBarFill.Size = UDim2.new(fraction, 0, 1, 0)
	healthBarFill.BackgroundColor3 = Color3.fromRGB(60, 200, 90):Lerp(Color3.fromRGB(200, 60, 60), 1 - fraction)
	healthLabel.Text = `{math.floor(humanoid.Health)} / {math.floor(humanoid.MaxHealth)}`
end

local function onCharacterAdded(character: Model)
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	updateHealth(humanoid)
	humanoid.HealthChanged:Connect(function()
		updateHealth(humanoid)
	end)
end

if player.Character ~= nil then
	onCharacterAdded(player.Character)
end
player.CharacterAdded:Connect(onCharacterAdded)

local function updateStats()
	local leaderstats = player:FindFirstChild("leaderstats")
	if leaderstats == nil then
		return
	end
	local cash = leaderstats:FindFirstChild("Cash") :: IntValue?
	local level = leaderstats:FindFirstChild("Level") :: IntValue?
	local cashValue = if cash ~= nil then cash.Value else 0
	local levelValue = if level ~= nil then level.Value else 1
	statsLabel.Text = `Cash: {cashValue}   Level: {levelValue}`
end

local function watchLeaderstats()
	local leaderstats = player:WaitForChild("leaderstats", 10)
	if leaderstats == nil then
		return
	end

	local cash = leaderstats:WaitForChild("Cash", 10)
	local level = leaderstats:WaitForChild("Level", 10)
	if cash ~= nil then
		(cash :: IntValue).Changed:Connect(updateStats)
	end
	if level ~= nil then
		(level :: IntValue).Changed:Connect(updateStats)
	end
	updateStats()
end

task.spawn(watchLeaderstats)

RemoteEvents.Get("ContractNotification").OnClientEvent:Connect(function(title: string, text: string)
	if title == "New Contract" then
		contractLabel.Text = `Contract: {text}`
	elseif title == "Contract Complete" then
		contractLabel.Text = `Delivered! {text} - next contract incoming...`
	end
end)
