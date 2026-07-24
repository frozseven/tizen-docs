local ServerScriptService = game:GetService("ServerScriptService")

local DataHandler = require(ServerScriptService.Data.DataHandler)
local AntiCheatService = require(ServerScriptService.AntiCheat.AntiCheatService)

DataHandler.Init()
AntiCheatService.Init()
