--!strict
-- Shared floating health bar (BillboardGui) for non-player Humanoids, e.g.
-- TestDummyService and RaiderService. Real player characters use Roblox's
-- own HUD instead of this.
--
-- Also turns off Roblox's built-in automatic health display: it anchors
-- to a Head part, which these bare Humanoids don't have, so it was
-- rendering in an unrelated corner of the screen instead of over the
-- target.

local HealthBar = {}

function HealthBar.Attach(humanoid: Humanoid, anchor: BasePart)
	humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff

	local billboard = Instance.new("BillboardGui")
	billboard.Name = "HealthBillboard"
	billboard.Size = UDim2.new(4, 0, 0.6, 0)
	billboard.StudsOffset = Vector3.new(0, 2.5, 0)
	billboard.AlwaysOnTop = true
	billboard.Parent = anchor

	local background = Instance.new("Frame")
	background.Size = UDim2.new(1, 0, 1, 0)
	background.BackgroundColor3 = Color3.fromRGB(40, 40, 40)
	background.BorderSizePixel = 0
	background.Parent = billboard

	local fill = Instance.new("Frame")
	fill.Name = "Fill"
	fill.Size = UDim2.new(1, 0, 1, 0)
	fill.BackgroundColor3 = Color3.fromRGB(60, 200, 90)
	fill.BorderSizePixel = 0
	fill.Parent = background

	humanoid.HealthChanged:Connect(function(health)
		local fraction = math.clamp(health / humanoid.MaxHealth, 0, 1)
		fill.Size = UDim2.new(fraction, 0, 1, 0)
		fill.BackgroundColor3 = Color3.fromRGB(60, 200, 90):Lerp(Color3.fromRGB(200, 60, 60), 1 - fraction)
	end)
end

return HealthBar
