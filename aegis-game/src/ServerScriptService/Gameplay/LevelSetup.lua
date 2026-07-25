--!strict
-- Creates the placeholder test-level geometry (baseplate, shipyard spawn,
-- delivery dropoffs, extraction zone) on every server start if it doesn't
-- already exist. Real level art replaces this eventually; this exists so
-- the foundation is testable without hand-placing parts in Studio, which
-- don't survive an unsaved place reload.

local Workspace = game:GetService("Workspace")

local LevelSetup = {}

local function ensurePart(name: string, cframe: CFrame, size: Vector3, color: Color3, canCollide: boolean): BasePart
	local existing = Workspace:FindFirstChild(name)
	if existing ~= nil and existing:IsA("BasePart") then
		return existing
	end

	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.CanCollide = canCollide
	part.Size = size
	part.CFrame = cframe
	part.Color = color
	part.Parent = Workspace
	return part
end

function LevelSetup.Init()
	ensurePart("Baseplate", CFrame.new(0, -10, 0), Vector3.new(512, 20, 512), Color3.fromRGB(150, 150, 160), true)
	ensurePart("ShipyardSpawn", CFrame.new(0, 0.5, 0), Vector3.new(6, 1, 6), Color3.fromRGB(120, 120, 130), true)
	ensurePart("RiverCampDropoff", CFrame.new(30, 0.5, 0), Vector3.new(6, 1, 6), Color3.fromRGB(80, 140, 200), false)
	ensurePart("MountainDepotDropoff", CFrame.new(0, 0.5, -30), Vector3.new(6, 1, 6), Color3.fromRGB(139, 115, 85), false)
	ensurePart("CoastalOutpostDropoff", CFrame.new(-30, 0.5, 0), Vector3.new(6, 1, 6), Color3.fromRGB(70, 180, 170), false)
	ensurePart("ExtractionZone", CFrame.new(0, 0.5, 15), Vector3.new(6, 1, 6), Color3.fromRGB(200, 60, 60), false)
end

return LevelSetup
