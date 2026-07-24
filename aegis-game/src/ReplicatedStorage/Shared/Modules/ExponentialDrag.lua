--!strict
-- Exact analytical solution for exponential (linear) drag, used for
-- projectile ballistics and volatile cargo motion. Frame-rate independent:
-- correct regardless of dt, unlike a per-frame `velocity *= 0.98` multiplier
-- which drifts as the interval between frames changes.
--
-- Model: dv/dt = acceleration - k * v
-- Closed-form solution (k > 0):
--   v(t) = v_terminal + (v0 - v_terminal) * exp(-k * t)
--   p(t) = p0 + v_terminal * t + (v0 - v_terminal) * (1 - exp(-k * t)) / k
-- where v_terminal = acceleration / k.

local EPSILON = 1e-6

local ExponentialDrag = {}

-- Pure drag decay with no external acceleration: v(t) = v0 * exp(-k * t).
function ExponentialDrag.Velocity(v0: Vector3, k: number, t: number): Vector3
	return v0 * math.exp(-k * t)
end

-- Exact integral of Velocity() over [0, t] with no external acceleration.
function ExponentialDrag.Position(p0: Vector3, v0: Vector3, k: number, t: number): Vector3
	if k < EPSILON then
		return p0 + v0 * t
	end
	return p0 + (v0 / k) * (1 - math.exp(-k * t))
end

-- Advances position/velocity by dt under drag plus a constant acceleration
-- (e.g. gravity), using the exact closed-form solution rather than
-- iterative Euler steps. Stable and correct for any dt, including the
-- large or irregular frame times a busy server produces under load with
-- 1,000+ simultaneous projectiles.
function ExponentialDrag.Step(
	position: Vector3,
	velocity: Vector3,
	acceleration: Vector3,
	k: number,
	dt: number
): (Vector3, Vector3)
	if k < EPSILON then
		-- No drag: plain constant-acceleration kinematics.
		local newVelocity = velocity + acceleration * dt
		local newPosition = position + velocity * dt + 0.5 * acceleration * dt * dt
		return newPosition, newVelocity
	end

	local terminalVelocity = acceleration / k
	local decay = math.exp(-k * dt)
	local velocityDelta = velocity - terminalVelocity

	local newVelocity = terminalVelocity + velocityDelta * decay
	local newPosition = position + terminalVelocity * dt + velocityDelta * (1 - decay) / k

	return newPosition, newVelocity
end

return ExponentialDrag
