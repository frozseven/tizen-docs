--!strict
-- Minimal keyboard test harness for volatile cargo physics.
-- G: launch a liquid reservoir
-- H: launch a crystalline spire (thrown hard enough to shatter on impact)

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local KEY_ACTIONS: { [Enum.KeyCode]: () -> () } = {
	[Enum.KeyCode.G] = function()
		RemoteEvents.Get("SpawnCargo"):FireServer("Liquid")
	end,
	[Enum.KeyCode.H] = function()
		RemoteEvents.Get("SpawnCargo"):FireServer("Crystal")
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
