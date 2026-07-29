# NOTES — verify against your BeamNG v0.39

Checklist of assumptions this app makes. Tick against your install if something doesn’t spawn.

## Paths (verified on Alex’s machine 2026-07-29)

| Assumption | Value / check |
|------------|----------------|
| Steam app id | `284160` |
| Game install | `...\steamapps\common\BeamNG.drive` |
| Exe | `Bin64\BeamNG.drive.x64.exe` |
| Userfolder (modern) | `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current` |
| Legacy docs path | `%USERPROFILE%\Documents\BeamNG.drive\<ver>\` (may be absent) |
| Content levels | `content\levels\*.zip` with `info.json` |
| Content vehicles | `content\vehicles\*.zip` |
| Console log | userfolder `console.log` / `beamng.log` |

## Launch CLI (0.39 source)

| Flag | Behavior to verify |
|------|--------------------|
| `-level <name>` | `parseArgs.lua` → `$levelToLoad` → `main.lua` ~1495 → `core_loadMapCmd.set({level="levels/<name>/info.json"}, true)` |
| `-lua <chunk>` | `LuaExecuteQueueString(nextArg)` during arg parse |
| `-userpath <path>` | Must match folder we scanned |
| `-gfx d3d12` | Confirmed token in 0.39 exe (`d3d12`, also `d3d11` / `vulkan`). Default in QuickLaunch. |
| `-vehicle <model>` | Sets `$beamngVehicleArgs` — preferred spawn path |
| `-vehicleConfig model/cfg.pc` | No `vehicles/` prefix; game prefixes it |
| `-useDefaultPc` | Skip freeroam “last driven” override |
| `-onLevelLoad_ext` | Fallback if needed (not default) |
| Lua replace | Optional (`vehicle_spawn_mode=lua\|both`) — slower / racey vs native |

## Patch / version (Alex machine 2026-07-29)

| Check | Value |
|-------|--------|
| Userfolder | `...\BeamNG.drive\current` + `update_to_v0.39.0.0` marker |
| integrity.json buildinfo | `buildbot build 20859 … 28/07/2026` |
| Steam buildid | `24449824` (== TargetBuildID → fully updated) |

## Freeroam APIs (`lua/ge/extensions/freeroam/freeroam.lua`)

| API | Exported as | Notes |
|-----|-------------|--------|
| `startFreeroam(level, …)` | `M.startFreeroam` → `freeroam_freeroam.startFreeroam` | level path or table |
| `startFreeroamByName(levelName, …)` | `M.startFreeroamByName` | used when `-level` flag is OFF |

Default UI mode uses **`-level` for the map** and **does not** call `startFreeroam*` in the vehicle-only Lua template (avoids double-load).

## Vehicle APIs (`lua/ge/extensions/core/vehicles.lua`)

| API | Line (approx) | Notes |
|-----|---------------|--------|
| `replaceVehicle(modelName, opt, …)` | ~1866 / `M.replaceVehicle` | Preferred after mission start |
| `spawnNewVehicle(modelName, opt)` | ~1825 / `M.spawnNewVehicle` | Fallback in template |
| `spawnDefault` | `M.spawnDefault` | Last-resort fallback (not in default template) |
| `opt.config` | string path like `vehicles/<model>/<cfg>.pc` | Empty string for Default |

## Hooks

| Hook | Why |
|------|-----|
| `onClientStartMission` via `extensions.setCompletedCallback` | Vehicle replace after level live |
| `onClientPostStartMission` | Alternate if StartMission fires too early |
| `onWorldReadyState == 2` | Heavier / safer for UI; needs tiny extension if `-lua` alone is flaky |

## If vehicle replace is flaky

1. Edit Startup Lua → wrap replace in `onClientPostStartMission`.
2. Or write a tiny extension under `userfolder/mods/unpacked/quicklaunch_spawn/` and use `-onLevelLoad_ext` — **tell the user the exact path; never overwrite existing mods.**

## Tech mode

BeamNGpy = BeamNG.**tech** only. Retail `.drive` path stays `-level`/`-lua`. Flag stays off by default.
