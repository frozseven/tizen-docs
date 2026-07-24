local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)
local DataHandler = require(ServerScriptService.Data.DataHandler)
local AntiCheatService = require(ServerScriptService.AntiCheat.AntiCheatService)
local VehicleAssemblyService = require(ServerScriptService.Vehicles.VehicleAssemblyService)
local VolatileCargoService = require(ServerScriptService.Physics.VolatileCargoService)

RemoteEvents.Init()
DataHandler.Init()
AntiCheatService.Init()
VehicleAssemblyService.Init()
VolatileCargoService.Init()
