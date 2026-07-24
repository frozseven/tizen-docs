--!strict
-- Server-authoritative movement validation loop. Samples each player's
-- HumanoidRootPart position on a fixed interval and flags horizontal
-- speed/teleport violations plus vertical fly/jump-height violations.
-- Never trusts the client.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local MovementValidator = require(script.Parent.MovementValidator)

local CHECK_INTERVAL = 0.25 -- seconds between samples per player
local MAX_WALK_SPEED_STUDS_PER_SECOND = 40 -- headroom above default 16 stud/s WalkSpeed
local MAX_TELEPORT_STUDS = 50 -- max horizontal displacement allowed between samples
local MAX_JUMP_SPEED_STUDS_PER_SECOND = 60 -- headroom above default 50 stud/s JumpPower
local MAX_AIRBORNE_SECONDS = 3 -- how long off the ground before flying is suspected
local MIN_FALL_SPEED_STUDS_PER_SECOND = 20 -- below this while airborne past the timeout, suspected flying

type PlayerState = {
	LastPosition: Vector3,
	LastCheckTime: number,
	WasGrounded: boolean,
	AirborneSince: number?,
}

local playerStates: { [Player]: PlayerState } = {}

local AntiCheatService = {}

local function getCharacterParts(player: Player): (BasePart?, Humanoid?)
	local character = player.Character
	if character == nil then
		return nil, nil
	end
	local rootPart = character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	return rootPart, humanoid
end

local function onViolation(player: Player, kind: string, lastPosition: Vector3)
	warn(`[AntiCheat] {player.Name} flagged for {kind}`)

	local rootPart = getCharacterParts(player)
	if rootPart ~= nil then
		rootPart.CFrame = CFrame.new(lastPosition)
	end
end

local function trackCharacter(player: Player, character: Model)
	local rootPart = character:WaitForChild("HumanoidRootPart", 5) :: BasePart?
	playerStates[player] = {
		LastPosition = if rootPart then rootPart.Position else Vector3.zero,
		LastCheckTime = os.clock(),
		WasGrounded = true,
		AirborneSince = nil,
	}
end

local function onPlayerAdded(player: Player)
	player.CharacterAdded:Connect(function(character)
		trackCharacter(player, character)
	end)

	if player.Character ~= nil then
		trackCharacter(player, player.Character)
	end
end

local function onPlayerRemoving(player: Player)
	playerStates[player] = nil
end

local function step()
	local now = os.clock()

	for player, state in playerStates do
		local dt = now - state.LastCheckTime
		if dt < CHECK_INTERVAL then
			continue
		end

		local rootPart, humanoid = getCharacterParts(player)
		if rootPart == nil then
			continue
		end

		local currentPosition = rootPart.Position
		local verticalVelocity = (currentPosition.Y - state.LastPosition.Y) / dt
		local isGrounded = humanoid == nil or humanoid.FloorMaterial ~= Enum.Material.Air

		if MovementValidator.CheckTeleport(state.LastPosition, currentPosition, MAX_TELEPORT_STUDS) then
			onViolation(player, "Teleport", state.LastPosition)
			state.LastCheckTime = now
			continue
		end

		if MovementValidator.CheckSpeed(state.LastPosition, currentPosition, dt, MAX_WALK_SPEED_STUDS_PER_SECOND) then
			onViolation(player, "Speed", state.LastPosition)
			state.LastCheckTime = now
			continue
		end

		if not isGrounded and state.WasGrounded and MovementValidator.CheckJump(verticalVelocity, MAX_JUMP_SPEED_STUDS_PER_SECOND) then
			onViolation(player, "Jump", state.LastPosition)
			state.WasGrounded = isGrounded
			state.AirborneSince = nil
			state.LastCheckTime = now
			continue
		end

		if isGrounded then
			state.AirborneSince = nil
		else
			state.AirborneSince = state.AirborneSince or now
			local airborneDuration = now - state.AirborneSince
			if MovementValidator.CheckFly(verticalVelocity, airborneDuration, MAX_AIRBORNE_SECONDS, MIN_FALL_SPEED_STUDS_PER_SECOND) then
				onViolation(player, "Fly", state.LastPosition)
				state.WasGrounded = isGrounded
				state.AirborneSince = nil
				state.LastCheckTime = now
				continue
			end
		end

		state.LastPosition = currentPosition
		state.WasGrounded = isGrounded
		state.LastCheckTime = now
	end
end

function AntiCheatService.Init()
	for _, player in Players:GetPlayers() do
		onPlayerAdded(player)
	end

	Players.PlayerAdded:Connect(onPlayerAdded)
	Players.PlayerRemoving:Connect(onPlayerRemoving)

	RunService.Heartbeat:Connect(step)
end

return AntiCheatService
