# Aegis: Abyssal Logistics & Warfare (codename Strandline)

Roblox Luau source for a server-authoritative, physics-based cooperative
logistics/vehicle-building sandbox. Built with [Rojo](https://rojo.space/)
and [Wally](https://wally.run/).

## Layout

- `src/ReplicatedStorage/Shared/Modules` — code shared by client and server
  (SOSDF vehicle serialization, exponential-drag math, game config).
- `src/ReplicatedStorage/Remotes` — RemoteEvent/RemoteFunction definitions.
- `src/ServerScriptService/Data` — ProfileStore-backed save/load (`DataHandler`).
- `src/ServerScriptService/Physics` — server-authoritative projectile and
  volatile cargo simulation.
- `src/ServerScriptService/AntiCheat` — server-side movement/speed/teleport
  validation.
- `src/ServerScriptService/Vehicles` — vehicle assembly/node snapping system.
- `src/ServerScriptService/Gameplay` — FTUE, extraction zones, soft-permadeath.
- `src/ServerScriptService/Economy` — delivery contracts.
- `src/ServerStorage/{VehicleTemplates,CargoTemplates}` — non-replicated
  template models referenced by the assembly and cargo systems.
- `src/StarterPlayerScripts/Client` — client input, vehicle builder UI hooks.

## Setup

```
wally install
rojo serve
```

then connect from Roblox Studio via the Rojo plugin.
