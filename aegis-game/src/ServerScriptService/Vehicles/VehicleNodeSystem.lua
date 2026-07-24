--!strict
-- In-memory node graph for a single assembled vehicle. Mirrors the shape
-- SOSDF serializes: every node's CFrame is relative to the root chassis,
-- and all nodes attach directly to the root (star topology).

local GRID_SIZE = 4 -- studs; component placement snaps to this resolution

export type Node = {
	TypeId: number,
	CFrame: CFrame,
	Instance: Instance?,
}

export type SerializedNode = {
	UID: number,
	TypeId: number,
	CFrame: CFrame,
}

export type Graph = {
	NextUID: number,
	Nodes: { [number]: Node },
}

local VehicleNodeSystem = {}

function VehicleNodeSystem.new(): Graph
	return {
		NextUID = 1,
		Nodes = {},
	}
end

function VehicleNodeSystem.SnapToGrid(offset: Vector3): Vector3
	return Vector3.new(
		math.round(offset.X / GRID_SIZE) * GRID_SIZE,
		math.round(offset.Y / GRID_SIZE) * GRID_SIZE,
		math.round(offset.Z / GRID_SIZE) * GRID_SIZE
	)
end

function VehicleNodeSystem.AddNode(graph: Graph, typeId: number, relativeCFrame: CFrame, instance: Instance?): number
	local uid = graph.NextUID
	graph.NextUID += 1
	graph.Nodes[uid] = {
		TypeId = typeId,
		CFrame = relativeCFrame,
		Instance = instance,
	}
	return uid
end

function VehicleNodeSystem.IsOccupied(graph: Graph, relativeCFrame: CFrame): boolean
	local targetPosition = relativeCFrame.Position
	for _, node in graph.Nodes do
		if (node.CFrame.Position - targetPosition).Magnitude < GRID_SIZE * 0.5 then
			return true
		end
	end
	return false
end

function VehicleNodeSystem.Serialize(graph: Graph): { SerializedNode }
	local nodes = {}
	for uid, node in graph.Nodes do
		table.insert(nodes, {
			UID = uid,
			TypeId = node.TypeId,
			CFrame = node.CFrame,
		})
	end
	return nodes
end

return VehicleNodeSystem
