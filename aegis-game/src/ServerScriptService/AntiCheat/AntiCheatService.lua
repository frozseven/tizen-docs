--!strict
-- Server-authoritative movement validation loop. Samples each player's
-- HumanoidRootPart position on a fixed interval and flags horizontal
-- speed/teleport violations. Never trusts the client.

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local MovementValidator = require(script.Parent.MovementValidator)

local CHECK_INTERVAL = 0.25 -- seconds between samples per player
local MAX_WALK_SPEED_STUDS_PER_SECOND = 40 -- headroom above default 16 stud/s WalkSpeed
local MAX_TELEPORT_STUDS = 50 -- max horizontal displacement allowed between samples

type PlayerState = {
	LastPosition: Vector3,
	LastCheckTime: number,
}

local playerStates: { [Player]: PlayerState } = {}

local AntiCheatService = {}

local function getRootPart(player: Player): BasePart?
	local character = player.Character
	if character == nil then
		return nil
	end
	return character:FindFirstChild("HumanoidRootPart") :: BasePart?
end

local function onViolation(player: Player, kind: string, lastPosition: Vector3)
	warn(`[AntiCheat] {player.Name} flagged for {kind}`)

	local rootPart = getRootPart(player)
	if rootPart ~= nil then
		rootPart.CFrame = CFrame.new(lastPosition)
	end
end

local function trackCharacter(player: Player, character: Model)
	local rootPart = character:WaitForChild("HumanoidRootPart", 5) :: BasePart?
	playerStates[player] = {
		LastPosition = if rootPart then rootPart.Position else Vector3.zero,
		LastCheckTime = os.clock(),
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

		local rootPart = getRootPart(player)
		if rootPart == nil then
			continue
		end

		local currentPosition = rootPart.Position

		if MovementValidator.CheckTeleport(state.LastPosition, currentPosition, MAX_TELEPORT_STUDS) then
			onViolation(player, "Teleport", state.LastPosition)
		elseif MovementValidator.CheckSpeed(state.LastPosition, currentPosition, dt, MAX_WALK_SPEED_STUDS_PER_SECOND) then
			onViolation(player, "Speed", state.LastPosition)
		else
			state.LastPosition = currentPosition
		end

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
