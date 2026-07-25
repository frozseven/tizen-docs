--!strict
-- Creates (server) and fetches (server + client) the shared RemoteEvents
-- used by gameplay systems. Call Init() once from the server boot script
-- before anything requires Get() from either side.

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local REMOTE_NAMES = {
	"SpawnChassis",
	"PlaceComponent",
	"SaveVehicle",
	"LoadVehicle",
	"SpawnCargo",
	"ContractNotification",
	"SpawnStarterTruck",
	"RequestContract",
	"FireProjectile",
}

local RemoteEvents = {}

function RemoteEvents.Init()
	local folder = ReplicatedStorage:FindFirstChild("GameRemotes")
	if folder == nil then
		folder = Instance.new("Folder")
		folder.Name = "GameRemotes"
		folder.Parent = ReplicatedStorage
	end

	for _, name in REMOTE_NAMES do
		if folder:FindFirstChild(name) == nil then
			local remote = Instance.new("RemoteEvent")
			remote.Name = name
			remote.Parent = folder
		end
	end
end

function RemoteEvents.Get(name: string): RemoteEvent
	local folder = ReplicatedStorage:WaitForChild("GameRemotes", 10)
	return folder:WaitForChild(name, 10) :: RemoteEvent
end

return RemoteEvents
