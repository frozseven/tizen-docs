local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerScriptService = game:GetService("ServerScriptService")

local RemoteEvents = require(ReplicatedStorage.Remotes.RemoteEvents)
local DataHandler = require(ServerScriptService.Data.DataHandler)
local AntiCheatService = require(ServerScriptService.AntiCheat.AntiCheatService)
local VehicleAssemblyService = require(ServerScriptService.Vehicles.VehicleAssemblyService)

RemoteEvents.Init()
DataHandler.Init()
AntiCheatService.Init()
VehicleAssemblyService.Init()
