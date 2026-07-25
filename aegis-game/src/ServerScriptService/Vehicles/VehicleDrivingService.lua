--!strict
-- Server-authoritative vehicle driving. VehicleSeat.Throttle/.Steer are
-- replicated and clamped to [-1, 1] by the engine itself when a player
-- sits in and drives it, so reading them here is safe - the server still
-- owns how those inputs translate into actual motion. The whole
-- assembled vehicle is one welded rigid body (see VehicleAssemblyService),
-- so driving it just means moving the seat's assembly directly.
--
-- Motion is applied through LinearVelocity/AngularVelocity constraints
-- (created alongside the seat in VehicleAssemblyService) rather than
-- writing AssemblyLinearVelocity directly - a raw property write gets
-- fought/overridden every step by the physics solver resolving the
-- assembly's WeldConstraints, while a constraint is a first-class part
-- of that same solve. There's no per-wheel suspension/torque simulation
-- in this foundation.

local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local VEHICLE_SEAT_TAG = "VehicleSeat"
local MAX_SPEED = 60 -- studs/s
local ACCELERATION = 40 -- studs/s^2
local MAX_TURN_RATE = math.rad(90) -- radians/s at full speed; scaled down at low speed

local VehicleDrivingService = {}

local function driveSeat(seat: VehicleSeat, dt: number)
	local linearVelocity = seat:FindFirstChild("DriveLinearVelocity") :: LinearVelocity?
	local angularVelocity = seat:FindFirstChild("DriveAngularVelocity") :: AngularVelocity?
	if linearVelocity == nil or angularVelocity == nil then
		return
	end

	if seat.Occupant == nil then
		-- No driver: don't keep applying whatever throttle/steer was last
		-- commanded - otherwise an abandoned vehicle keeps crawling under
		-- its last input forever instead of coming to rest, since nothing
		-- else ever clears these constraints.
		linearVelocity.VectorVelocity = Vector3.zero
		angularVelocity.AngularVelocity = Vector3.zero
		return
	end

	local forward = seat.CFrame.LookVector
	local currentVelocity = seat.AssemblyLinearVelocity
	local currentForwardSpeed = currentVelocity:Dot(forward)

	local targetSpeed = seat.Throttle * MAX_SPEED
	local speedDelta = targetSpeed - currentForwardSpeed
	local maxDelta = ACCELERATION * dt
	local newForwardSpeed = currentForwardSpeed + math.clamp(speedDelta, -maxDelta, maxDelta)

	-- Y is left at 0 here: the constraint has zero force on world Y (see
	-- VehicleAssemblyService), so this component is never actually applied.
	linearVelocity.VectorVelocity = forward * newForwardSpeed

	-- Negated: a positive rotation about world +Y turns LookVector toward
	-- -X (left), but positive Steer means the player pressed right.
	local speedFraction = math.clamp(math.abs(newForwardSpeed) / MAX_SPEED, 0.2, 1)
	angularVelocity.AngularVelocity = Vector3.new(0, -seat.Steer * MAX_TURN_RATE * speedFraction, 0)
end

local function step(dt: number)
	for _, instance in CollectionService:GetTagged(VEHICLE_SEAT_TAG) do
		if instance:IsA("VehicleSeat") then
			driveSeat(instance, dt)
		end
	end
end

function VehicleDrivingService.Init()
	RunService.Heartbeat:Connect(step)
end

return VehicleDrivingService
