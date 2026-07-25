--!strict
-- Minimal keyboard test harness for projectile ballistics.
-- F: fire a projectile in the direction you're facing
-- Y: spawn/respawn a stationary test dummy 15 studs in front of you

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local KEY_ACTIONS: { [Enum.KeyCode]: () -> () } = {
	[Enum.KeyCode.F] = function()
		RemoteEvents.Get("FireProjectile"):FireServer()
	end,
	[Enum.KeyCode.Y] = function()
		RemoteEvents.Get("SpawnTestDummy"):FireServer()
	end,
}

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end

	local action = KEY_ACTIONS[input.KeyCode]
	if action ~= nil then
		action()
	end
end)
