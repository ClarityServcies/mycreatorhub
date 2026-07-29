"""Build BeamNG args + launch via direct exe or Steam.

Retail path: -gfx d3d12 + -level + native -vehicle/-vehicleConfig (preferred)
over post-load Lua replace. Handoff prewarms Steam; never touches injectors.
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

from handoff import HandoffReport, prepare_handoff
from paths import APP_ID, console_log_path, steam_exe

# Verified in BeamNG.drive.x64.exe / parseArgs (0.39)
DEFAULT_GFX = "d3d12"
# native | lua | both — native uses parseArgs -vehicle / -vehicleConfig
DEFAULT_VEHICLE_MODE = "native"


@dataclass
class LaunchRequest:
    level_id: str
    vehicle_id: str
    config_name: str  # "Default" or stem
    lua_template: str
    use_level_flag: bool = True
    extra_args: str = ""
    spawn_point: str = ""
    time_of_day: str = ""
    userfolder: str = ""
    exe_path: str = ""
    launch_mode: str = "direct"  # direct | steam
    gfx_mode: str = DEFAULT_GFX  # d3d12 | d3d11 | vulkan | ""
    vehicle_spawn_mode: str = DEFAULT_VEHICLE_MODE  # native | lua | both
    prewarm_steam: bool = True
    check_injectors: bool = True


@dataclass
class LaunchPlan:
    argv: list[str]
    display: str
    lua_chunk: str
    working_dir: str
    console_log: str
    handoff: HandoffReport = field(default_factory=HandoffReport)


def config_path_for(vehicle_id: str, config_name: str) -> str:
    """Full VFS path vehicles/<model>/<cfg>.pc (for Lua)."""
    if not config_name or config_name == "Default":
        return ""
    if config_name.lower().endswith(".pc"):
        name = config_name
    else:
        name = f"{config_name}.pc"
    if "/" in name or "\\" in name:
        return name.replace("\\", "/")
    return f"vehicles/{vehicle_id}/{name}"


def vehicle_config_cli(vehicle_id: str, config_name: str) -> str:
    """parseArgs -vehicleConfig form: model/name.pc (no vehicles/ prefix)."""
    if not config_name or config_name == "Default":
        return ""
    name = config_name if config_name.lower().endswith(".pc") else f"{config_name}.pc"
    name = name.replace("\\", "/")
    if name.startswith("vehicles/"):
        name = name[len("vehicles/") :]
    if "/" in name:
        return name
    return f"{vehicle_id}/{name}"


def render_lua(template: str, level_id: str, vehicle_id: str, config_name: str) -> str:
    cfg = config_path_for(vehicle_id, config_name)
    chunk = (
        template.replace("{LEVEL_ID}", level_id)
        .replace("{VEHICLE_MODEL}", vehicle_id)
        .replace("{CONFIG_PATH}", cfg)
        .replace("{CONFIG_PATH_OR_NAME}", cfg or config_name)
        .replace("{CONFIG}", cfg or "")
    )
    return " ".join(line.strip() for line in chunk.splitlines() if line.strip())


def _split_extra(extra_args: str) -> list[str]:
    if not extra_args.strip():
        return []
    try:
        return shlex.split(extra_args, posix=False)
    except ValueError:
        return extra_args.split()


def _extra_has(extra: list[str], flag: str) -> bool:
    fl = flag.lower()
    for tok in extra:
        if tok.lower() == fl or tok.lower().startswith(fl + "="):
            return True
    return False


def build_beamng_args(req: LaunchRequest) -> tuple[list[str], str]:
    mode = (req.vehicle_spawn_mode or DEFAULT_VEHICLE_MODE).lower()
    use_native = mode in ("native", "both")
    use_lua = mode in ("lua", "both")

    lua = ""
    if use_lua:
        lua = render_lua(req.lua_template, req.level_id, req.vehicle_id, req.config_name)

    args: list[str] = []
    extra = _split_extra(req.extra_args)

    # 1) GFX first — device selected early in boot
    gfx = (req.gfx_mode or "").strip().lower()
    if gfx and not _extra_has(extra, "-gfx"):
        args += ["-gfx", gfx]

    # 2) userpath before content resolve
    if req.userfolder:
        args += ["-userpath", req.userfolder]

    # 3) native vehicle (preferred) — spawn as player car during level load
    #    parseArgs: -vehicle <model>, -vehicleConfig "model/cfg.pc", -useDefaultPc
    if use_native and req.vehicle_id and not _extra_has(extra, "-vehicle"):
        args += ["-vehicle", req.vehicle_id]
        vcfg = vehicle_config_cli(req.vehicle_id, req.config_name)
        if vcfg and not _extra_has(extra, "-vehicleConfig"):
            args += ["-vehicleConfig", vcfg]
        if not _extra_has(extra, "-useDefaultPc"):
            # skip freeroam "last driven" override so our pick wins
            args += ["-useDefaultPc"]

    # 4) level — skip menu; core_loadMapCmd waits for mod manager (0.39)
    if req.use_level_flag and req.level_id and not _extra_has(extra, "-level"):
        args += ["-level", req.level_id]

    # 5) lua only if mode asks (native alone is faster / fewer race hooks)
    if use_lua and lua.strip() and not _extra_has(extra, "-lua"):
        args += ["-lua", lua]

    args.extend(extra)
    return args, lua


def build_plan(req: LaunchRequest) -> LaunchPlan:
    args, lua = build_beamng_args(req)
    uf = Path(req.userfolder) if req.userfolder else None
    clog = console_log_path(uf)
    clog_s = str(clog) if clog else ""

    if req.launch_mode == "steam":
        sexe = steam_exe()
        if not sexe:
            raise FileNotFoundError("Steam.exe not found (registry / common paths).")
        argv = [str(sexe), "-applaunch", str(APP_ID), *args]
        display = subprocess.list2cmdline(argv)
        return LaunchPlan(
            argv=argv,
            display=display,
            lua_chunk=lua,
            working_dir=str(sexe.parent),
            console_log=clog_s,
        )

    exe = Path(req.exe_path) if req.exe_path else None
    if not exe or not exe.is_file():
        raise FileNotFoundError(f"BeamNG exe not found: {req.exe_path!r}")
    argv = [str(exe), *args]
    display = subprocess.list2cmdline(argv)
    return LaunchPlan(
        argv=argv,
        display=display,
        lua_chunk=lua,
        working_dir=str(exe.parent),
        console_log=clog_s,
    )


def validate_paths(req: LaunchRequest) -> list[str]:
    errors: list[str] = []
    if req.launch_mode == "direct":
        if not req.exe_path or not Path(req.exe_path).is_file():
            errors.append(f"Exe missing: {req.exe_path}")
    else:
        if not steam_exe():
            errors.append("Steam.exe not found")
    if req.userfolder and not Path(req.userfolder).is_dir():
        errors.append(f"Userfolder missing: {req.userfolder}")
    if not req.level_id:
        errors.append("No level selected")
    if not req.vehicle_id:
        errors.append("No vehicle selected")
    gfx = (req.gfx_mode or "").lower()
    if gfx and gfx not in ("d3d12", "d3d11", "vulkan", "null", ""):
        errors.append(f"Unknown gfx_mode: {req.gfx_mode}")
    return errors


def launch(req: LaunchRequest) -> LaunchPlan:
    errors = validate_paths(req)
    if errors:
        raise RuntimeError("; ".join(errors))

    handoff = prepare_handoff(
        exe_path=req.exe_path,
        prewarm_steam=req.prewarm_steam,
        check_injectors=req.check_injectors,
    )
    # Hard-stop only if user wants — warnings alone don't block (theater may park later)
    plan = build_plan(req)
    plan.handoff = handoff

    kwargs: dict = {
        "args": plan.argv,
        "cwd": plan.working_dir,
        "close_fds": True,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            getattr(subprocess, "DETACHED_PROCESS", 0x8)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
            | 0x8000  # ABOVE_NORMAL_PRIORITY_CLASS
        )
    subprocess.Popen(**kwargs)
    return plan


def steam_run_url(args: list[str]) -> str:
    encoded = quote(" ".join(args), safe="")
    return f"steam://run/{APP_ID}//{encoded}"
