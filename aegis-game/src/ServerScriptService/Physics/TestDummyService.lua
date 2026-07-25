--!strict
-- TEST-ONLY: spawns a simple stationary humanoid dummy to shoot at, for
-- verifying ProjectileService's hit/damage detection without a second
-- player. Not part of core gameplay; safe to delete once no longer
-- needed for testing.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local TestDummyService = {}

local function spawnDummy(player: Player)
	local character = player.Character
	local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local spawnCFrame = if rootPart ~= nil then rootPart.CFrame * CFrame.new(0, 0, -15) else CFrame.new(0, 5, -15)

	local existing = Workspace:FindFirstChild("TestDummy")
	if existing ~= nil then
		existing:Destroy()
	end

	local dummy = Instance.new("Model")
	dummy.Name = "TestDummy"

	local dummyRoot = Instance.new("Part")
	dummyRoot.Name = "HumanoidRootPart"
	dummyRoot.Size = Vector3.new(2, 2, 1)
	dummyRoot.Transparency = 1
	dummyRoot.CanCollide = false
	dummyRoot.Anchored = true
	dummyRoot.CFrame = spawnCFrame
	dummyRoot.Parent = dummy

	local torso = Instance.new("Part")
	torso.Name = "Torso"
	torso.Size = Vector3.new(2, 2, 1)
	torso.Color = Color3.fromRGB(200, 80, 80)
	torso.CanCollide = true
	torso.Anchored = true
	torso.CFrame = spawnCFrame
	torso.Parent = dummy

	local humanoid = Instance.new("Humanoid")
	humanoid.MaxHealth = 100
	humanoid.Health = 100
	humanoid.Parent = dummy

	humanoid.HealthChanged:Connect(function(health)
		print(`[TestDummy] Health: {health}/{humanoid.MaxHealth}`)
	end)
	humanoid.Died:Connect(function()
		print("[TestDummy] Died!")
	end)

	dummy.PrimaryPart = dummyRoot
	dummy.Parent = Workspace
end

function TestDummyService.Init()
	RemoteEvents.Get("SpawnTestDummy").OnServerEvent:Connect(spawnDummy)
end

return TestDummyService
