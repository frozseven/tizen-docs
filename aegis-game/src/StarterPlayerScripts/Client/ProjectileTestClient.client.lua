--!strict
-- Minimal keyboard test harness for projectile ballistics.
-- F: fire a projectile toward where the camera is aimed (screen center)
-- Y: spawn/respawn a stationary test dummy 15 studs in front of you

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

local KEY_ACTIONS: { [Enum.KeyCode]: () -> () } = {
	[Enum.KeyCode.F] = function()
		-- Send the camera's look direction, not the character's facing
		-- direction: in third-person the body doesn't track the camera
		-- unless you're also moving, so firing along the body's LookVector
		-- made shots go wherever you last walked instead of where you're
		-- aiming.
		local camera = Workspace.CurrentCamera
		local aimDirection = if camera ~= nil then camera.CFrame.LookVector else Vector3.new(0, 0, -1)
		RemoteEvents.Get("FireProjectile"):FireServer(aimDirection)
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
