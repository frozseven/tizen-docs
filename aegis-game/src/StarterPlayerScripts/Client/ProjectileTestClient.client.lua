--!strict
-- Minimal keyboard test harness for projectile ballistics.
-- F: fire a projectile in the direction you're facing

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

UserInputService.InputBegan:Connect(function(input, gameProcessed)
	if gameProcessed then
		return
	end

	if input.KeyCode == Enum.KeyCode.F then
		RemoteEvents.Get("FireProjectile"):FireServer()
	end
end)
