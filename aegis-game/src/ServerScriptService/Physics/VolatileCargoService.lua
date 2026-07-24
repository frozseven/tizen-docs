--!strict
-- Server-authoritative simulation for volatile cargo. While airborne, each
-- piece of cargo is driven entirely by ExponentialDrag's exact solver
-- (position/velocity set directly each frame) rather than Roblox's default
-- rigid-body integration, so trajectories stay exact regardless of frame
-- rate. CanCollide is off during flight to avoid the engine fighting our
-- own position updates; once landed, cargo either rests normally (physics
-- takes over) or, for crystal spires above the impact-speed threshold,
-- shatters into debris.
--
-- Ground height is detected once per spawn via a single downward raycast
-- rather than continuous collision detection - a deliberate simplification
-- for this foundation (assumes a single flat landing surface per throw).

local Debris = game:GetService("Debris")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local ExponentialDrag = require(ReplicatedStorage.Shared.Modules.ExponentialDrag)
local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local GRAVITY = Vector3.new(0, -Workspace.Gravity, 0)
local DRAG_COEFFICIENT = 0.4
local LAUNCH_SPEED = 40
local SHATTER_SPEED_THRESHOLD = 20 -- studs/s impact speed treated as "high G-force"
local DEBRIS_COUNT = 6
local DEBRIS_LIFETIME = 5

type CargoKind = "Liquid" | "Crystal"

type CargoState = {
	Kind: CargoKind,
	Velocity: Vector3,
	GroundY: number,
}

local activeCargo: { [BasePart]: CargoState } = {}

-- Every cargo part (in flight, landed, or debris) lives in this folder so
-- ground raycasts can exclude it - otherwise a throw could "land" on top
-- of a previously-landed piece of cargo instead of the real floor.
local cargoFolder: Folder = nil :: any -- assigned in Init()

local VolatileCargoService = {}

local function findGroundY(position: Vector3): number
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { cargoFolder }

	local result = Workspace:Raycast(position, Vector3.new(0, -1000, 0), params)
	if result == nil then
		return position.Y - 1000
	end
	return result.Position.Y
end

local function createCargoPart(kind: CargoKind, cframe: CFrame): BasePart
	local part = Instance.new("Part")
	part.CFrame = cframe
	part.Anchored = false
	part.CanCollide = false -- re-enabled on landing; see module comment

	if kind == "Liquid" then
		part.Name = "LiquidReservoir"
		part.Shape = Enum.PartType.Cylinder
		part.Size = Vector3.new(4, 4, 4)
		part.Color = Color3.fromRGB(60, 140, 200)
		part.Material = Enum.Material.Glass
		part.Transparency = 0.2
	else
		part.Name = "CrystallineSpire"
		part.Size = Vector3.new(2, 6, 2)
		part.Color = Color3.fromRGB(180, 90, 220)
		part.Material = Enum.Material.Neon
	end

	return part
end

local function shatterCrystal(part: BasePart, impactVelocity: Vector3)
	local origin = part.CFrame
	part:Destroy()

	for _ = 1, DEBRIS_COUNT do
		local shard = Instance.new("Part")
		shard.Name = "CrystalShard"
		local scale = math.random(50, 100) / 100
		shard.Size = Vector3.new(scale, scale, scale)
		shard.Color = Color3.fromRGB(180, 90, 220)
		shard.Material = Enum.Material.Neon
		shard.CFrame = origin
		shard.Anchored = false
		shard.CanCollide = true
		shard.AssemblyLinearVelocity = impactVelocity * 0.3
			+ Vector3.new(math.random(-10, 10), math.random(2, 10), math.random(-10, 10))
		shard.Parent = cargoFolder

		Debris:AddItem(shard, DEBRIS_LIFETIME)
	end
end

local function spawnCargo(player: Player, kind: unknown)
	if kind ~= "Liquid" and kind ~= "Crystal" then
		return
	end

	local character = player.Character
	if character == nil or character.PrimaryPart == nil then
		return
	end

	local spawnCFrame = character.PrimaryPart.CFrame * CFrame.new(0, 4, -6)
	local groundY = findGroundY(spawnCFrame.Position)

	local part = createCargoPart(kind :: CargoKind, spawnCFrame)
	part.Parent = cargoFolder

	local launchVelocity = character.PrimaryPart.CFrame.LookVector * LAUNCH_SPEED + Vector3.new(0, LAUNCH_SPEED * 0.4, 0)

	activeCargo[part] = {
		Kind = kind :: CargoKind,
		Velocity = launchVelocity,
		GroundY = groundY,
	}
end

local function stepCargo(dt: number)
	for part, state in activeCargo do
		local newPosition, newVelocity = ExponentialDrag.Step(part.Position, state.Velocity, GRAVITY, DRAG_COEFFICIENT, dt)

		local landed = newPosition.Y <= state.GroundY + part.Size.Y / 2 and newVelocity.Y <= 0
		if landed then
			activeCargo[part] = nil

			if state.Kind == "Crystal" and newVelocity.Magnitude >= SHATTER_SPEED_THRESHOLD then
				shatterCrystal(part, newVelocity)
			else
				part.CFrame = CFrame.new(newPosition.X, state.GroundY + part.Size.Y / 2, newPosition.Z)
				part.CanCollide = true
			end
			continue
		end

		-- Liquid sloshing: tilt opposite the horizontal acceleration, an
		-- approximation of a tank's center of gravity resisting a change
		-- in direction.
		local tilt = CFrame.new()
		if state.Kind == "Liquid" then
			local horizontalAcceleration = Vector3.new(newVelocity.X - state.Velocity.X, 0, newVelocity.Z - state.Velocity.Z) / dt
			local tiltAxis = Vector3.new(-horizontalAcceleration.Z, 0, horizontalAcceleration.X)
			if tiltAxis.Magnitude > 0.01 then
				local tiltAngle = math.clamp(horizontalAcceleration.Magnitude * 0.01, 0, math.rad(25))
				tilt = CFrame.fromAxisAngle(tiltAxis.Unit, tiltAngle)
			end
		end

		part.CFrame = CFrame.new(newPosition) * tilt
		state.Velocity = newVelocity
	end
end

function VolatileCargoService.Init()
	cargoFolder = Instance.new("Folder")
	cargoFolder.Name = "Cargo"
	cargoFolder.Parent = Workspace

	RemoteEvents.Get("SpawnCargo").OnServerEvent:Connect(spawnCargo)
	RunService.Heartbeat:Connect(stepCargo)
end

return VolatileCargoService
