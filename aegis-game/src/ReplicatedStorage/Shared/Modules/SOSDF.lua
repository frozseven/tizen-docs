--!strict
-- Super Optimized Serialization Data Format.
-- Encodes a vehicle's component graph as a delimited string instead of a
-- nested table, keeping saved vehicles well under the DataStore size limit.
-- Format: "UID:TypeID:X:Y:Z:RX:RY:RZ|UID:TypeID:X:Y:Z:RX:RY:RZ|..."
-- Every node's CFrame is expected to already be relative to the vehicle's
-- root chassis (ObjectSpace), so no parent/edge field is needed: all nodes
-- attach directly to the root.

local FIELD_DELIMITER = ":"
local NODE_DELIMITER = "|"

export type VehicleNode = {
	UID: number,
	TypeId: number,
	CFrame: CFrame,
}

local SOSDF = {}

function SOSDF.EncodeNode(uid: number, typeId: number, cframe: CFrame): string
	local position = cframe.Position
	local rx, ry, rz = cframe:ToEulerAnglesXYZ()
	return table.concat({ uid, typeId, position.X, position.Y, position.Z, rx, ry, rz }, FIELD_DELIMITER)
end

function SOSDF.EncodeVehicle(nodes: { VehicleNode }): string
	local segments = table.create(#nodes)
	for index, node in nodes do
		segments[index] = SOSDF.EncodeNode(node.UID, node.TypeId, node.CFrame)
	end
	return table.concat(segments, NODE_DELIMITER)
end

function SOSDF.DecodeVehicle(data: string): { VehicleNode }
	local nodes: { VehicleNode } = {}
	if data == "" then
		return nodes
	end

	for _, segment in string.split(data, NODE_DELIMITER) do
		local fields = string.split(segment, FIELD_DELIMITER)
		table.insert(nodes, {
			UID = assert(tonumber(fields[1]), "SOSDF: invalid UID field"),
			TypeId = assert(tonumber(fields[2]), "SOSDF: invalid TypeID field"),
			CFrame = CFrame.new(
				assert(tonumber(fields[3]), "SOSDF: invalid X field"),
				assert(tonumber(fields[4]), "SOSDF: invalid Y field"),
				assert(tonumber(fields[5]), "SOSDF: invalid Z field")
			) * CFrame.Angles(
				assert(tonumber(fields[6]), "SOSDF: invalid RX field"),
				assert(tonumber(fields[7]), "SOSDF: invalid RY field"),
				assert(tonumber(fields[8]), "SOSDF: invalid RZ field")
			),
		})
	end

	return nodes
end

return SOSDF
