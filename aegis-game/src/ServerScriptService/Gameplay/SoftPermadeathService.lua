--!strict
-- Soft-permadeath: killed in the extraction zone means an economic wipe,
-- not a ban. Cash/vehicles/progress reset to a fresh start, and rejoining
-- is blocked for a cooldown window rather than any account-level action.

local Players = game:GetService("Players")
local ServerScriptService = game:GetService("ServerScriptService")

local DataHandler = require(ServerScriptService.Data.DataHandler)
local VehicleAssemblyService = require(ServerScriptService.Vehicles.VehicleAssemblyService)

-- TESTING VALUE: 60 seconds so the loop can be safely tested repeatedly.
-- Set to 45 * 60 for the real spec'd 45-minute matchmaking timeout before
-- treating this as production-ready - ProfileStore data is tied to your
-- real account even in Studio, so testing with the real value risks
-- locking yourself out for the full 45 minutes.
local TIMEOUT_SECONDS = 60

local SoftPermadeathService = {}

function SoftPermadeathService.TriggerWipe(player: Player)
	local profile = DataHandler.GetProfile(player)
	if profile == nil then
		return
	end

	profile.Data.Cash = 0
	profile.Data.Level = 1
	profile.Data.Vehicles = {}
	profile.Data.HasCompletedFTUE = false
	profile.Data.RespawnAvailableAt = os.time() + TIMEOUT_SECONDS

	VehicleAssemblyService.DestroyVehicle(player)

	player:Kick(
		`Eliminated in the extraction zone. Your gear was wiped - you can rejoin in {math.ceil(TIMEOUT_SECONDS / 60)} minute(s).`
	)
end

function SoftPermadeathService.Init()
	Players.PlayerAdded:Connect(function(player)
		local profile = DataHandler.WaitForProfile(player, 10)
		if profile == nil then
			return
		end

		local remaining = profile.Data.RespawnAvailableAt - os.time()
		if remaining > 0 then
			player:Kick(`Matchmaking timeout: try again in {math.ceil(remaining / 60)} minute(s).`)
		end
	end)
end

return SoftPermadeathService
