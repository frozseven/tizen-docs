--!strict
-- Server-authoritative projectile ballistics (the "Warfare" side of the
-- sandbox). Projectiles are simulated with ExponentialDrag - the same
-- exact-integration approach as VolatileCargoService - and hit detection
-- uses a swept raycast covering each step's movement segment, not a
-- point check at the new position: a fast-moving projectile can tunnel
-- past a thin target within a single frame otherwise.
--
-- Dying to a projectile only triggers the soft-permadeath wipe if it
-- happens inside the extraction zone (ExtractionZoneService checks that
-- independently at the moment of death) - everywhere else it's a normal
-- respawn, same as any other death.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local ExponentialDrag = require(ReplicatedStorage.Shared.Modules.ExponentialDrag)
local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local GRAVITY = Vector3.new(0, -Workspace.Gravity, 0)
local DRAG_COEFFICIENT = 0.2
local LAUNCH_SPEED = 150
local DAMAGE = 20
local MAX_LIFETIME = 5 -- seconds before a projectile despawns if it hits nothing
local FIRE_COOLDOWN = 0.5 -- seconds between shots per player

type ProjectileState = {
	Part: BasePart,
	Velocity: Vector3,
	SpawnTime: number,
	RaycastParams: RaycastParams,
}

local activeProjectiles: { ProjectileState } = {}
local lastFireTime: { [Player]: number } = {}

local ProjectileService = {}

local function createProjectilePart(cframe: CFrame): BasePart
	local part = Instance.new("Part")
	part.Name = "Projectile"
	part.Shape = Enum.PartType.Ball
	part.Size = Vector3.new(0.6, 0.6, 0.6)
	part.Color = Color3.fromRGB(255, 200, 60)
	part.Material = Enum.Material.Neon
	part.CanCollide = false
	part.CanQuery = false
	part.Anchored = true -- fully server-simulated via manual CFrame updates
	part.CFrame = cframe
	part.Parent = Workspace
	return part
end

local function applyHit(hitPart: BasePart)
	local character = hitPart:FindFirstAncestorOfClass("Model")
	if character == nil then
		return
	end

	local humanoid = character:FindFirstChildOfClass("Humanoid")
	if humanoid == nil then
		return
	end

	-- No friendly fire: this is a co-op game, not PvP. Excludes every real
	-- player, not just the shooter - only raiders/dummies (Humanoids with no
	-- associated Player) take projectile damage.
	if Players:GetPlayerFromCharacter(character) ~= nil then
		return
	end

	humanoid:TakeDamage(DAMAGE)
end

local function onFireProjectile(player: Player, aimDirection: unknown)
	local now = os.clock()
	local last = lastFireTime[player] or 0
	if now - last < FIRE_COOLDOWN then
		return
	end
	lastFireTime[player] = now

	local character = player.Character
	local rootPart = character and character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if rootPart == nil then
		return
	end

	-- Prefer the client-reported camera aim direction (where the player is
	-- actually looking) over the character's body-facing LookVector: in
	-- third-person, the body doesn't turn to match the camera unless the
	-- player is also moving, so firing along LookVector made shots miss
	-- whatever the player was visually aiming at. The client input is
	-- untrusted, so it's validated and re-normalized here rather than used
	-- as-is - a malformed or non-unit vector just falls back to LookVector.
	local direction = rootPart.CFrame.LookVector
	if typeof(aimDirection) == "Vector3" and aimDirection.Magnitude > 0.01 then
		direction = aimDirection.Unit
	end

	local spawnCFrame = CFrame.lookAt(rootPart.Position + Vector3.new(0, 1, 0), rootPart.Position + Vector3.new(0, 1, 0) + direction)
	local part = createProjectilePart(spawnCFrame)

	local raycastParams = RaycastParams.new()
	raycastParams.FilterType = Enum.RaycastFilterType.Exclude
	raycastParams.FilterDescendantsInstances = if character ~= nil then { part, character } else { part }

	table.insert(activeProjectiles, {
		Part = part,
		Velocity = direction * LAUNCH_SPEED,
		SpawnTime = now,
		RaycastParams = raycastParams,
	})
end

local function destroyProjectile(index: number)
	activeProjectiles[index].Part:Destroy()
	table.remove(activeProjectiles, index)
end

local function step(dt: number)
	local now = os.clock()

	for index = #activeProjectiles, 1, -1 do
		local state = activeProjectiles[index]

		if now - state.SpawnTime > MAX_LIFETIME then
			destroyProjectile(index)
			continue
		end

		local previousPosition = state.Part.Position
		local newPosition, newVelocity =
			ExponentialDrag.Step(previousPosition, state.Velocity, GRAVITY, DRAG_COEFFICIENT, dt)

		local result = Workspace:Raycast(previousPosition, newPosition - previousPosition, state.RaycastParams)
		if result ~= nil then
			applyHit(result.Instance)
			destroyProjectile(index)
			continue
		end

		state.Part.CFrame = CFrame.new(newPosition)
		state.Velocity = newVelocity
	end
end

function ProjectileService.Init()
	RemoteEvents.Get("FireProjectile").OnServerEvent:Connect(onFireProjectile)
	RunService.Heartbeat:Connect(step)

	Players.PlayerRemoving:Connect(function(player)
		lastFireTime[player] = nil
	end)
end

return ProjectileService
