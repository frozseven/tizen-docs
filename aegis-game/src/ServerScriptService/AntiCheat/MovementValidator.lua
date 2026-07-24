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

return MovementValidator
