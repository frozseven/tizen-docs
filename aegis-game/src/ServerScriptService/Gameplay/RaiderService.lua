--!strict
-- Hostile NPCs guarding the extraction zone: give "Warfare" real stakes -
-- a reason to use ProjectileService defensively, and a threat that makes
-- dying near extraction meaningfully risky (SoftPermadeathService already
-- triggers on any death inside the zone, raider-caused or not).
--
-- Two raider kinds for variety: Melee closes distance and hits in melee
-- range; Ranged holds its distance and pelts the player from afar with a
-- raycast "hitscan" shot (a fast visual tracer, not a simulated projectile
-- like ProjectileService) - a reasonable simplification for an NPC attack
-- at this foundation stage.
--
-- Movement is simple direct chase (Humanoid:MoveTo toward the nearest
-- player in range) rather than full pathfinding - a reasonable
-- simplification for this foundation on open, obstacle-free terrain.
-- Raiders are ordinary Humanoids, so they take damage from
-- ProjectileService's existing hit logic with no changes needed there.

local Debris = game:GetService("Debris")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local HealthBar = require(ReplicatedStorage.Shared.Modules.HealthBar)

type RaiderKind = "Melee" | "Ranged"
type RaiderSpawn = { Kind: RaiderKind, CFrame: CFrame }

local RAIDER_SPAWNS: { RaiderSpawn } = {
	{ Kind = "Melee", CFrame = CFrame.new(10, 1, 15) },
	{ Kind = "Melee", CFrame = CFrame.new(-10, 1, 15) },
	{ Kind = "Ranged", CFrame = CFrame.new(0, 1, 22) },
}

local RESPAWN_DELAY = 10 -- seconds after a raider dies before a replacement spawns
local AGGRO_RADIUS = 40 -- studs
local MOVE_TICK_INTERVAL = 0.5 -- seconds between chase-target updates
local DEATH_CLEANUP_DELAY = 2
local HIT_STAGGER_DURATION = 0.4 -- seconds a raider freezes in place after taking damage

local MELEE_HEALTH = 60
local MELEE_RANGE = 5
local MELEE_DAMAGE = 10
local MELEE_INTERVAL = 1 -- seconds between melee hits
local MELEE_COLOR = Color3.fromRGB(120, 30, 30)

local RANGED_HEALTH = 40
local RANGED_ATTACK_RANGE = 26 -- holds this distance and shoots instead of closing in
local RANGED_DAMAGE = 12
local RANGED_ATTACK_INTERVAL = 1.5
local RANGED_COLOR = Color3.fromRGB(60, 40, 130)
local TRACER_SPEED = 150 -- studs/s; purely visual, damage is applied instantly via raycast

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

local function fireTracer(origin: Vector3, targetPosition: Vector3, hit: boolean)
	local distance = (targetPosition - origin).Magnitude
	if distance < 0.01 then
		return
	end

	local tracer = Instance.new("Part")
	tracer.Name = "RaiderShot"
	tracer.Size = Vector3.new(0.3, 0.3, distance)
	tracer.CFrame = CFrame.lookAt(origin, targetPosition) * CFrame.new(0, 0, -distance / 2)
	tracer.Color = if hit then Color3.fromRGB(255, 90, 90) else Color3.fromRGB(150, 150, 150)
	tracer.Material = Enum.Material.Neon
	tracer.Anchored = true
	tracer.CanCollide = false
	tracer.CanQuery = false
	tracer.Parent = Workspace

	Debris:AddItem(tracer, distance / TRACER_SPEED + 0.05)
end

local function createRaiderModel(spawnCFrame: CFrame, color: Color3, maxHealth: number): (Model, BasePart, BasePart, Humanoid)
	local model = Instance.new("Model")
	model.Name = "Raider"

	local root = Instance.new("Part")
	root.Name = "HumanoidRootPart"
	root.Size = Vector3.new(2, 2, 1)
	root.Transparency = 1
	root.CanCollide = false
	root.Anchored = false
	root.CFrame = spawnCFrame
	root.Parent = model

	local torso = Instance.new("Part")
	torso.Name = "Torso"
	torso.Size = Vector3.new(2, 2, 1)
	torso.Color = color
	torso.Material = Enum.Material.Slate
	torso.CanCollide = true
	torso.Anchored = false
	torso.CFrame = spawnCFrame
	torso.Parent = model

	local weld = Instance.new("WeldConstraint")
	weld.Part0 = root
	weld.Part1 = torso
	weld.Parent = torso

	local humanoid = Instance.new("Humanoid")
	humanoid.MaxHealth = maxHealth
	humanoid.Health = maxHealth
	humanoid.WalkSpeed = 12
	humanoid.Parent = model

	model.PrimaryPart = root
	model.Parent = Workspace

	HealthBar.Attach(humanoid, torso)

	return model, root, torso, humanoid
end

-- A hit should give the player breathing room, not just tick down a number
-- while the raider keeps closing/attacking at full speed - returns a check
-- function the movement loop polls to skip acting while recently hit.
local function attachHitStagger(humanoid: Humanoid, root: BasePart): () -> boolean
	local staggerUntil = 0
	local lastHealth = humanoid.Health

	humanoid.HealthChanged:Connect(function(newHealth)
		if newHealth < lastHealth then
			staggerUntil = os.clock() + HIT_STAGGER_DURATION
			humanoid:MoveTo(root.Position)
		end
		lastHealth = newHealth
	end)

	return function(): boolean
		return os.clock() < staggerUntil
	end
end

local function spawnMeleeRaider(spawnCFrame: CFrame)
	local model, root, torso, humanoid = createRaiderModel(spawnCFrame, MELEE_COLOR, MELEE_HEALTH)
	local isStaggered = attachHitStagger(humanoid, root)

	local lastMeleeTime = 0
	local lastMoveTickTime = 0

	local heartbeatConnection: RBXScriptConnection
	heartbeatConnection = RunService.Heartbeat:Connect(function()
		if humanoid.Health <= 0 or isStaggered() then
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
		spawnMeleeRaider(spawnCFrame)
	end)
end

local function spawnRangedRaider(spawnCFrame: CFrame)
	local model, root, torso, humanoid = createRaiderModel(spawnCFrame, RANGED_COLOR, RANGED_HEALTH)
	local isStaggered = attachHitStagger(humanoid, root)

	local lastAttackTime = 0
	local lastMoveTickTime = 0

	local raycastParams = RaycastParams.new()
	raycastParams.FilterType = Enum.RaycastFilterType.Exclude
	raycastParams.FilterDescendantsInstances = { model }

	local heartbeatConnection: RBXScriptConnection
	heartbeatConnection = RunService.Heartbeat:Connect(function()
		if humanoid.Health <= 0 or isStaggered() then
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
		if distance > RANGED_ATTACK_RANGE then
			humanoid:MoveTo(targetRoot.Position)
			return
		end

		-- In range: hold position and shoot instead of closing in further.
		humanoid:MoveTo(root.Position)

		if now - lastAttackTime < RANGED_ATTACK_INTERVAL then
			return
		end
		lastAttackTime = now

		local origin = root.Position
		local direction = targetRoot.Position - origin
		local result = Workspace:Raycast(origin, direction, raycastParams)

		local hitTargetHumanoid: Humanoid? = nil
		local tracerEndpoint = targetRoot.Position
		if result ~= nil then
			tracerEndpoint = result.Position
			local hitCharacter = result.Instance:FindFirstAncestorOfClass("Model")
			local candidateHumanoid = hitCharacter and hitCharacter:FindFirstChildOfClass("Humanoid")
			if candidateHumanoid ~= nil and Players:GetPlayerFromCharacter(hitCharacter :: Model) ~= nil then
				hitTargetHumanoid = candidateHumanoid
			end
		end

		fireTracer(origin, tracerEndpoint, hitTargetHumanoid ~= nil)
		if hitTargetHumanoid ~= nil then
			hitTargetHumanoid:TakeDamage(RANGED_DAMAGE)
		end
	end)

	humanoid.Died:Connect(function()
		heartbeatConnection:Disconnect()
		torso.CanCollide = false
		torso.CanQuery = false

		task.wait(DEATH_CLEANUP_DELAY)
		model:Destroy()

		task.wait(RESPAWN_DELAY)
		spawnRangedRaider(spawnCFrame)
	end)
end

function RaiderService.Init()
	for _, spawn in RAIDER_SPAWNS do
		if spawn.Kind == "Melee" then
			spawnMeleeRaider(spawn.CFrame)
		else
			spawnRangedRaider(spawn.CFrame)
		end
	end
end

return RaiderService
