--!strict
-- Default shape for a new player's ProfileStore document.

export type VehicleRecord = {
	Name: string,
	Data: string, -- SOSDF-encoded component graph
}

export type ProfileData = {
	Cash: number,
	Level: number,
	Vehicles: { [string]: VehicleRecord },
	HasCompletedFTUE: boolean,
	RespawnAvailableAt: number, -- os.time() timestamp; 0 = no restriction
}

return {
	Cash = 0,
	Level = 1,
	Vehicles = {},
	HasCompletedFTUE = false,
	RespawnAvailableAt = 0,
} :: ProfileData
