"""Local JSON settings — app folder only, never browser storage."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from paths import app_dir, find_exe, find_game_install, find_userfolder

DEFAULT_LUA_TEMPLATE = (
    "extensions.setCompletedCallback('onClientStartMission', function() "
    "pcall(function() "
    "if core_vehicles and core_vehicles.replaceVehicle then "
    "core_vehicles.replaceVehicle('{VEHICLE_MODEL}', { config = '{CONFIG_PATH}' }) "
    "elseif core_vehicles and core_vehicles.spawnNewVehicle then "
    "core_vehicles.spawnNewVehicle('{VEHICLE_MODEL}', { config = '{CONFIG_PATH}' }) "
    "end end) end); "
    "if freeroam_freeroam and freeroam_freeroam.startFreeroamByName then "
    "freeroam_freeroam.startFreeroamByName('{LEVEL_ID}') "
    "elseif freeroam_freeroam and freeroam_freeroam.startFreeroam then "
    "freeroam_freeroam.startFreeroam('/levels/{LEVEL_ID}/info.json') end"
)

# When using -level for the map (recommended), only the vehicle hook runs in -lua.
DEFAULT_LUA_VEHICLE_ONLY = (
    "extensions.setCompletedCallback('onClientStartMission', function() "
    "pcall(function() "
    "if core_vehicles and core_vehicles.replaceVehicle then "
    "core_vehicles.replaceVehicle('{VEHICLE_MODEL}', { config = '{CONFIG_PATH}' }) "
    "elseif core_vehicles and core_vehicles.spawnNewVehicle then "
    "core_vehicles.spawnNewVehicle('{VEHICLE_MODEL}', { config = '{CONFIG_PATH}' }) "
    "end end) end)"
)


def default_settings() -> dict[str, Any]:
    install = find_game_install()
    exe = find_exe(install)
    user = find_userfolder()
    return {
        "game_install": str(install) if install else "",
        "exe_path": str(exe) if exe else "",
        "userfolder": str(user) if user else "",
        "launch_mode": "direct",  # direct | steam
        "gfx_mode": "d3d12",  # d3d12 | d3d11 | vulkan | ""
        "vehicle_spawn_mode": "native",  # native (-vehicle) | lua | both
        "prewarm_steam": True,
        "check_injectors": True,
        "close_launcher_when_game_opens": True,
        "use_level_flag": True,  # pass -level for map
        "extra_args": "",
        "fast_scan": True,  # skip mods/repo deep zip crawl
        "scan_mod_zips": True,  # top-level mods/*.zip only (never repo/_parked rglob)
        "lua_template": DEFAULT_LUA_VEHICLE_ONLY,
        "lua_template_full": DEFAULT_LUA_TEMPLATE,
        "custom_lua": "",  # if set, used as-is (after placeholder sub) over template
        "spawn_point": "",
        "time_of_day": "",
        "tech_mode": False,
        "tech_install": "",
        "last_selection": {
            "level_id": "west_coast_usa",
            "vehicle_id": "etk800",
            "config_name": "Default",
        },
        "favorites": [],
    }


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (app_dir() / "config.json")
        self.data = default_settings()
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            # fill auto-detect into fresh file
            self.save()
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            base = default_settings()
            base.update({k: v for k, v in raw.items() if k in base or k in raw})
            # merge known keys; keep unknown for forward compat
            merged = default_settings()
            for k, v in raw.items():
                merged[k] = v
            # ensure nested defaults
            if "last_selection" not in merged or not isinstance(merged["last_selection"], dict):
                merged["last_selection"] = default_settings()["last_selection"]
            if "favorites" not in merged or not isinstance(merged["favorites"], list):
                merged["favorites"] = []
            # if paths empty, auto-fill
            if not merged.get("game_install"):
                merged["game_install"] = default_settings()["game_install"]
            if not merged.get("exe_path"):
                merged["exe_path"] = default_settings()["exe_path"]
            if not merged.get("userfolder"):
                merged["userfolder"] = default_settings()["userfolder"]
            if not merged.get("lua_template"):
                merged["lua_template"] = DEFAULT_LUA_VEHICLE_ONLY
            if not merged.get("gfx_mode"):
                merged["gfx_mode"] = "d3d12"
            if not merged.get("vehicle_spawn_mode"):
                merged["vehicle_spawn_mode"] = "native"
            if "scan_mod_zips" not in merged:
                merged["scan_mod_zips"] = True
            if "prewarm_steam" not in merged:
                merged["prewarm_steam"] = True
            if "check_injectors" not in merged:
                merged["check_injectors"] = True
            if "close_launcher_when_game_opens" not in merged:
                merged["close_launcher_when_game_opens"] = True
            # drop shelved multicam key if present in old configs
            merged.pop("multicam", None)
            self.data = merged
        except (OSError, json.JSONDecodeError):
            self.data = default_settings()
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self.data)
