--!strict
-- Shows contract assignment/completion notifications using Roblox's
-- built-in notification UI - no custom GUI needed for this foundation.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)

RemoteEvents.Get("ContractNotification").OnClientEvent:Connect(function(title: string, text: string)
	StarterGui:SetCore("SendNotification", {
		Title = title,
		Text = text,
		Duration = 8,
	})
end)
