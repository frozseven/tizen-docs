--!strict
-- Pure validation logic for server-authoritative movement checks.
-- Y (vertical) is ignored throughout: legitimate falls, launches, and
-- jumps produce large vertical speed that isn't exploit signal, while
-- horizontal displacement is what speed/teleport hacks actually abuse.

local MovementValidator = {}

function MovementValidator.HorizontalDistance(a: Vector3, b: Vector3): number
	local delta = b - a
	return Vector2.new(delta.X, delta.Z).Magnitude
end

function MovementValidator.CheckSpeed(
	previousPosition: Vector3,
	currentPosition: Vector3,
	dt: number,
	maxStudsPerSecond: number
): boolean
	if dt <= 0 then
		return false
	end
	local horizontalSpeed = MovementValidator.HorizontalDistance(previousPosition, currentPosition) / dt
	return horizontalSpeed > maxStudsPerSecond
end

function MovementValidator.CheckTeleport(previousPosition: Vector3, currentPosition: Vector3, maxStuds: number): boolean
	return MovementValidator.HorizontalDistance(previousPosition, currentPosition) > maxStuds
end

-- A legitimate jump's initial vertical velocity is capped by the
-- Humanoid's JumpPower and can only decrease afterward as gravity takes
-- over, so any sampled upward velocity above that ceiling - at any point
-- during the jump, not just the instant of liftoff - is evidence of a
-- jump-height hack, never a false positive from sampling timing.
function MovementValidator.CheckJump(verticalVelocity: number, maxJumpSpeed: number): boolean
	return verticalVelocity > maxJumpSpeed
end

-- Real falls have increasingly negative vertical velocity; sustained
-- airtime without that downward acceleration - hovering or slowly
-- rising - indicates flying rather than a normal jump/fall arc.
function MovementValidator.CheckFly(verticalVelocity: number, airborneDuration: number, maxAirborneTime: number, minFallSpeed: number): boolean
	if airborneDuration < maxAirborneTime then
		return false
	end
	return verticalVelocity > -minFallSpeed
end

return MovementValidator
