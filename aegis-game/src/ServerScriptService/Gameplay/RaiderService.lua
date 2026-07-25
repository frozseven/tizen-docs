--!strict
-- Hostile NPCs guarding the extraction zone: give "Warfare" real stakes -
-- a reason to use ProjectileService defensively, and a threat that makes
-- dying near extraction meaningfully risky (SoftPermadeathService already
-- triggers on any death inside the zone, raider-caused or not).
--
-- Movement is simple direct chase (Humanoid:MoveTo toward the nearest
-- player in range) rather than full pathfinding - a reasonable
-- simplification for this foundation on open, obstacle-free terrain.
-- Raiders are ordinary Humanoids, so they take damage from
-- ProjectileService's existing hit logic with no changes needed there.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local SPAWN_POSITION = CFrame.new(10, 1, 15) -- near ExtractionZone
local MAX_RAIDERS = 2
local RESPAWN_DELAY = 10 -- seconds after a raider dies before a replacement spawns
local AGGRO_RADIUS = 40 -- studs
local MELEE_RANGE = 5
local MELEE_DAMAGE = 10
local MELEE_INTERVAL = 1 -- seconds between melee hits
local MOVE_TICK_INTERVAL = 0.5 -- seconds between chase-target updates
local RAIDER_HEALTH = 60
local DEATH_CLEANUP_DELAY = 2

local RaiderService = {}

local function findNearestPlayerRoot(position: Vector3, radius: number): BasePart?
	local nearest: BasePart? = nil
	local nearestDistance = radius

	for _, player in Players:GetPlayers() do
		local character = player.Character
		local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if rootPart == nil then
			continue
		end

		local distance = (rootPart.Position - position).Magnitude
		if distance <= nearestDistance then
			nearest = rootPart
			nearestDistance = distance
		end
	end

	return nearest
end

local function spawnRaider()
	local model = Instance.new("Model")
	model.Name = "Raider"

	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = Vector3.new(2, 2, 1)
	root.Transparency = 1
	root.CanCollide = false
	root.Anchored = false
	root.CFrame = SPAWN_POSITION
	root.Parent = model

	local torso = Instance.new("Part")
	torso.Name = "Torso"
	torso.Size = Vector3.new(2, 2, 1)
	torso.Color = Color3.fromRGB(120, 30, 30)
	torso.Material = Enum.Material.Slate
	torso.CanCollide = true
	torso.Anchored = false
	torso.CFrame = SPAWN_POSITION
	torso.Parent = model

	local weld = Instance.new("WeldConstraint")
	weld.Part0 = root
	weld.Part1 = torso
	weld.Parent = torso

	local humanoid = Instance.new("Humanoid")
	humanoid.MaxHealth = RAIDER_HEALTH
	humanoid.Health = RAIDER_HEALTH
	humanoid.WalkSpeed = 12
	humanoid.Parent = model

	model.PrimaryPart = root
	model.Parent = Workspace

	local lastMeleeTime = 0
	local lastMoveTickTime = 0

	local heartbeatConnection: RBXScriptConnection
	heartbeatConnection = RunService.Heartbeat:Connect(function()
		if humanoid.Health <= 0 then
			return
		end

		local now = os.clock()
		if now - lastMoveTickTime < MOVE_TICK_INTERVAL then
			return
		end
		lastMoveTickTime = now

		local targetRoot = findNearestPlayerRoot(root.Position, AGGRO_RADIUS)
		if targetRoot == nil then
			return
		end

		local distance = (targetRoot.Position - root.Position).Magnitude
		if distance <= MELEE_RANGE then
			if now - lastMeleeTime >= MELEE_INTERVAL then
				lastMeleeTime = now
				local targetCharacter = targetRoot.Parent
				local targetHumanoid = targetCharacter and targetCharacter:FindFirstChildOfClass("Humanoid")
				if targetHumanoid ~= nil then
					targetHumanoid:TakeDamage(MELEE_DAMAGE)
				end
			end
		else
			humanoid:MoveTo(targetRoot.Position)
		end
	end)

	humanoid.Died:Connect(function()
		heartbeatConnection:Disconnect()
		torso.CanCollide = false
		torso.CanQuery = false

		task.wait(DEATH_CLEANUP_DELAY)
		model:Destroy()

		task.wait(RESPAWN_DELAY)
		spawnRaider()
	end)
end

function RaiderService.Init()
	for _ = 1, MAX_RAIDERS do
		spawnRaider()
	end
end

return RaiderService
