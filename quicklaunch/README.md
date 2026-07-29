# BeamNG QuickLaunch

Skip the main menu / level selector / vehicle selector. Pick **Map + Vehicle + Config → SPAWN**. Lands in freeroam.

**Stack:** Python 3.10+ / **Tkinter** (stdlib only — no pip needed). Retail BeamNG.drive via `-level` + `-lua`.

## Run (fastest)

1. Double-click Desktop shortcut **BeamNG QuickLaunch**  
   (or `run.bat` in this folder)
2. First open: hit **Refresh Scan** (threaded; cached after).
3. Pick map / car / config → **SPAWN** (or Enter).

Create / refresh the shortcut:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\Install-Shortcut.ps1"
```

## How the skip-menu trick works (0.39)

1. **`-level <id>`** — sets `$levelToLoad`. On GE boot, `main.lua` routes through `core_loadMapCmd.set({level="levels/<id>/info.json"})` so stock **and** modded maps wait for the mod manager. **This is the reliable “skip menu, load map” path on 0.39.**
2. **`-lua "<chunk>"`** — runs `LuaExecuteQueueString`. Default chunk registers `onClientStartMission` then calls `core_vehicles.replaceVehicle` / `spawnNewVehicle` fallbacks so your car replaces the level default after load.

You **cannot** skip map streaming. You **can** skip menus.

## Fix Lua if an API renamed

**Edit Startup Lua** in the UI. Placeholders:

| Token | Example |
|-------|---------|
| `{LEVEL_ID}` | `west_coast_usa` |
| `{VEHICLE_MODEL}` | `etk800` |
| `{CONFIG_PATH}` | `vehicles/etk800/sport.pc` (empty if Default) |

Verified on this machine’s 0.39 install:

- `freeroam_freeroam.startFreeroam` / `startFreeroamByName`
- `core_vehicles.replaceVehicle` / `spawnNewVehicle`

If spawn fails: open `console.log` under your userfolder (status bar shows the path).

## Launch modes

| Mode | What it runs |
|------|----------------|
| **Direct exe** (default) | `Bin64\BeamNG.drive.x64.exe` + args, cwd = Bin64 |
| **Steam** | `steam.exe -applaunch 284160 <args>` |
| **Tech / BeamNGpy** | Settings checkbox only — **off**. Needs BeamNG.tech + `beamngpy` (not installed here). |

## Graphics (0.39)

Default: **`-gfx d3d12`** (forced unless you override in Settings / extra args).

Also supported: `d3d11`, `vulkan`. Header shows Steam buildid + integrity build date so you can see you’re on the latest patch.

**Keep D3D12 clean:** do **not** put SpecialK / DXGI proxy DLLs back in `Bin64`. QuickLaunch warns if it sees them. Theater park paths stay parked.

## Vehicle spawn (faster than Lua replace)

Default mode **Native CLI**: `-vehicle` + `-vehicleConfig` + `-useDefaultPc` so the car is chosen during level load (parseArgs), not replaced after. Lua hook is optional fallback in Settings.

See [PIPELINE.md](PIPELINE.md) for which AAA load/handoff ideas we applied vs. what would break BeamNG.

## Speed

- Fingerprint cache: reopen skips full zip scan if content mtimes unchanged
- Parallel level/vehicle zip workers
- Fast scan skips `mods/repo` + `_parked` + recursive mod zip crawl (optional “Slow scan” in Settings)
- Map thumb cache + debounced filter |

Settings JSON lives next to the app: `config.json` (never browser storage).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Opens to main menu | Lua error → userfolder `console.log`. Edit Startup Lua. Confirm `-level` id matches folder/zip name. |
| Wrong / no car | Config path; try Default; try `spawnNewVehicle` in Lua editor. |
| Scan empty | Settings → Auto-detect. Userfolder on modern installs is `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current` (not Documents). |
| Paths wrong | Settings overrides; always pass `-userpath` when set so scan + launch match. |

## Optional .exe

```bat
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name BeamNGQuickLaunch main.py
```

See `quicklaunch.spec` if present.
