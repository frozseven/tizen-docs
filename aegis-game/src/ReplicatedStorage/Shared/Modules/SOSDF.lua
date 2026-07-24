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

-- assert(value, message) returns both value and message when value is
-- truthy, so calling it inline as the last argument of a multi-arg call
-- (e.g. CFrame.new(x, y, assert(z, "..."))) splices the message in as an
-- extra argument. Wrapping it in a function with a single `return` avoids
-- that.
local function toNumber(value: string?, fieldName: string): number
	local result = tonumber(value)
	assert(result ~= nil, `SOSDF: invalid {fieldName} field`)
	return result :: number
end

function SOSDF.DecodeVehicle(data: string): { VehicleNode }
	local nodes: { VehicleNode } = {}
	if data == "" then
		return nodes
	end

	for _, segment in string.split(data, NODE_DELIMITER) do
		local fields = string.split(segment, FIELD_DELIMITER)
		table.insert(nodes, {
			UID = toNumber(fields[1], "UID"),
			TypeId = toNumber(fields[2], "TypeID"),
			CFrame = CFrame.new(toNumber(fields[3], "X"), toNumber(fields[4], "Y"), toNumber(fields[5], "Z"))
				* CFrame.Angles(toNumber(fields[6], "RX"), toNumber(fields[7], "RY"), toNumber(fields[8], "RZ")),
		})
	end

	return nodes
end

return SOSDF
