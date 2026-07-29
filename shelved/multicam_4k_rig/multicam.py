"""Multi-instance 4K capture rig — separate from single SPAWN.

Isolation:
  sandboxie  — Sandboxie-Plus /box:BNG1..3 (preferred if installed)
  userpath   — -userpath C:\\BNG1..3 (works on this 0.39 install; space-free)
  thin       — three game copies with their own startup.ini (paths in settings)

Affinity (14700F corrected):
  BNG1 FF, BNG2 FF00, BNG3 FF0000, OBS F000000
"""
from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from paths import find_exe, find_game_install

StatusCb = Callable[[str], None]

# 14700F: logical 0-15 P-cores (HT), 16-27 E-cores
AFFINITY = {
    "bng1": 0xFF,  # 0-7
    "bng2": 0xFF00,  # 8-15
    "bng3": 0xFF0000,  # 16-23
    "obs": 0xF000000,  # 24-27
}
PRIORITY_HIGH = 0x00000080
PRIORITY_ABOVE = 0x00008000

SANDBOXIE_CANDIDATES = (
    Path(r"C:\Program Files\Sandboxie-Plus\Start.exe"),
    Path(r"C:\Program Files\Sandboxie\Start.exe"),
)
OBS_CANDIDATES = (
    Path(r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"),
    Path(r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe"),
)

DEFAULT_PROFILES = (Path(r"C:\BNG1"), Path(r"C:\BNG2"), Path(r"C:\BNG3"))
BOX_NAMES = ("BNG1", "BNG2", "BNG3")


@dataclass
class MulticamConfig:
    exe_path: str = ""
    isolation: str = "userpath"  # sandboxie | userpath | thin
    gfx_mode: str = "d3d11"  # capture-rig default (lighter than d3d12×3)
    level_id: str = "west_coast_usa"
    vehicle_id: str = "etk800"
    config_name: str = "Default"
    stagger_s: float = 20.0
    kill_orphans: bool = True
    launch_obs: bool = True
    obs_path: str = ""
    sandboxie_path: str = ""
    profiles: tuple[str, str, str] = ("C:\\BNG1", "C:\\BNG2", "C:\\BNG3")
    thin_exes: tuple[str, str, str] = ("", "", "")
    use_level: bool = True
    use_vehicle: bool = True
    # Process priority: High for Beam, AboveNormal for OBS — never Realtime
    beam_priority: int = PRIORITY_HIGH
    obs_priority: int = PRIORITY_ABOVE


@dataclass
class MulticamReport:
    pids: list[int] = field(default_factory=list)
    isolation: str = ""
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def find_sandboxie() -> Path | None:
    for p in SANDBOXIE_CANDIDATES:
        if p.is_file():
            return p
    return None


def find_obs(override: str = "") -> Path | None:
    if override and Path(override).is_file():
        return Path(override)
    for p in OBS_CANDIDATES:
        if p.is_file():
            return p
    return None


def ensure_profile_dirs(profiles: tuple[str, str, str]) -> list[str]:
    notes: list[str] = []
    for raw in profiles:
        p = Path(raw)
        if " " in str(p):
            raise RuntimeError(f"Userpath has spaces (BeamNG crash risk): {p}")
        p.mkdir(parents=True, exist_ok=True)
        notes.append(f"profile ready: {p}")
    return notes


def kill_beam_orphans() -> None:
    if sys.platform != "win32":
        return
    for name in ("BeamNG.drive.x64.exe", "BeamNG.drive.exe"):
        subprocess.run(
            ["taskkill", "/F", "/IM", name],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )


def _set_affinity_priority(pid: int, affinity: int, priority: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes
    from ctypes import wintypes

    PROCESS_SET_INFORMATION = 0x0200
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_SET_QUOTA = 0x0100
    access = PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION | PROCESS_SET_QUOTA
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(access, False, pid)
    if not handle:
        return
    try:
        k32.SetProcessAffinityMask(handle, ctypes.c_size_t(affinity))
        k32.SetPriorityClass(handle, wintypes.DWORD(priority))
    finally:
        k32.CloseHandle(handle)


def _vehicle_config_cli(vehicle_id: str, config_name: str) -> str:
    if not config_name or config_name == "Default":
        return ""
    name = config_name if config_name.lower().endswith(".pc") else f"{config_name}.pc"
    name = name.replace("\\", "/")
    if name.startswith("vehicles/"):
        name = name[len("vehicles/") :]
    if "/" in name:
        return name
    return f"{vehicle_id}/{name}"


def build_instance_args(cfg: MulticamConfig, userpath: str | None) -> list[str]:
    args: list[str] = ["-gfx", cfg.gfx_mode]
    if userpath:
        args += ["-userpath", userpath]
    if cfg.use_vehicle and cfg.vehicle_id:
        args += ["-vehicle", cfg.vehicle_id]
        vcfg = _vehicle_config_cli(cfg.vehicle_id, cfg.config_name)
        if vcfg:
            args += ["-vehicleConfig", vcfg]
        args += ["-useDefaultPc"]
    if cfg.use_level and cfg.level_id:
        args += ["-level", cfg.level_id]
    return args


def resolve_isolation(cfg: MulticamConfig) -> str:
    mode = (cfg.isolation or "userpath").lower()
    if mode == "sandboxie":
        sb = Path(cfg.sandboxie_path) if cfg.sandboxie_path else find_sandboxie()
        if sb and sb.is_file():
            return "sandboxie"
        return "userpath"  # auto-fallback
    if mode == "thin":
        if all(cfg.thin_exes) and all(Path(p).is_file() for p in cfg.thin_exes):
            return "thin"
        return "userpath"
    return "userpath"


def launch_rig(cfg: MulticamConfig, status: StatusCb | None = None) -> MulticamReport:
    def say(msg: str) -> None:
        if status:
            status(msg)

    report = MulticamReport()
    exe = Path(cfg.exe_path) if cfg.exe_path else find_exe(find_game_install())
    if not exe or not exe.is_file():
        report.errors.append("BeamNG exe not found")
        return report

    mode = resolve_isolation(cfg)
    report.isolation = mode
    if mode != cfg.isolation:
        report.notes.append(f"isolation fell back: {cfg.isolation} → {mode}")

    if mode == "userpath":
        try:
            report.notes.extend(ensure_profile_dirs(cfg.profiles))
        except RuntimeError as ex:
            report.errors.append(str(ex))
            return report

    if cfg.kill_orphans:
        say("Killing orphan BeamNG processes…")
        kill_beam_orphans()
        time.sleep(2.0)

    sandboxie = None
    if mode == "sandboxie":
        sandboxie = Path(cfg.sandboxie_path) if cfg.sandboxie_path else find_sandboxie()
        if not sandboxie or not sandboxie.is_file():
            report.errors.append("Sandboxie Start.exe not found")
            return report

    keys = ("bng1", "bng2", "bng3")
    for i, key in enumerate(keys):
        say(f"Launching instance {i + 1}/3 ({key}, affinity {hex(AFFINITY[key])})…")
        if mode == "thin":
            game = Path(cfg.thin_exes[i])
            userpath = None
            cwd = str(game.parent)
            game_argv = [str(game), *build_instance_args(cfg, None)]
        elif mode == "sandboxie":
            game = exe
            userpath = None  # sandbox isolates writes
            cwd = str(exe.parent)
            inner = [str(game), *build_instance_args(cfg, None)]
            game_argv = [str(sandboxie), f"/box:{BOX_NAMES[i]}", *inner]
        else:
            game = exe
            userpath = cfg.profiles[i]
            cwd = str(exe.parent)
            game_argv = [str(game), *build_instance_args(cfg, userpath)]

        flags = 0
        if sys.platform == "win32":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0x8) | getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200
            )
        proc = subprocess.Popen(game_argv, cwd=cwd, close_fds=True, creationflags=flags)
        if proc.pid:
            report.pids.append(proc.pid)
            # settle then pin THIS instance only (do not re-pin earlier PIDs)
            time.sleep(1.5)
            _set_affinity_priority(proc.pid, AFFINITY[key], cfg.beam_priority)
            if mode == "sandboxie":
                # Sandboxie Start.exe is parent — pin newest BeamNG child not already tracked
                _pin_newest_beam_child(AFFINITY[key], cfg.beam_priority, set(report.pids), report)

        if i < 2:
            say(f"Stagger wait {cfg.stagger_s:.0f}s (shader/VRAM spike)…")
            time.sleep(max(0.5, cfg.stagger_s))

    if cfg.launch_obs:
        obs = find_obs(cfg.obs_path)
        if obs:
            say("Launching OBS…")
            time.sleep(2.0)
            flags = 0
            if sys.platform == "win32":
                flags = getattr(subprocess, "DETACHED_PROCESS", 0x8) | getattr(
                    subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200
                )
            op = subprocess.Popen(
                [str(obs)],
                cwd=str(obs.parent),
                close_fds=True,
                creationflags=flags,
            )
            if op.pid:
                time.sleep(1.0)
                _set_affinity_priority(op.pid, AFFINITY["obs"], cfg.obs_priority)
                report.pids.append(op.pid)
                report.notes.append(f"OBS pid {op.pid}")
        else:
            report.notes.append("OBS not found — launch manually")

    say("Rig up. Verify 3 windows before record.")
    report.notes.append(f"isolation={mode} gfx={cfg.gfx_mode} pids={report.pids}")
    return report


def _pin_newest_beam_child(
    affinity: int,
    priority: int,
    already: set[int],
    report: MulticamReport,
) -> None:
    """Pin one new BeamNG.drive.x64.exe PID not in already (Sandboxie child)."""
    if sys.platform != "win32":
        return
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq BeamNG.drive.x64.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        candidates: list[int] = []
        for line in (out.stdout or "").splitlines():
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 2:
                try:
                    pid = int(parts[1].strip('"'))
                except ValueError:
                    continue
                if pid not in already:
                    candidates.append(pid)
        if not candidates:
            return
        # highest PID ≈ newest on Windows
        pid = max(candidates)
        _set_affinity_priority(pid, affinity, priority)
        report.pids.append(pid)
        report.notes.append(f"pinned Beam child pid {pid} affinity {hex(affinity)}")
    except (OSError, subprocess.TimeoutExpired):
        pass


def write_batch_launcher(path: Path, cfg: MulticamConfig) -> Path:
    """Emit a .bat matching Part 4 of the master doc (editable / double-click)."""
    exe = Path(cfg.exe_path) if cfg.exe_path else find_exe(find_game_install())
    sb = find_sandboxie()
    obs = find_obs(cfg.obs_path)
    mode = resolve_isolation(cfg)
    lines = [
        "@echo off",
        "setlocal",
        f"set GAME={exe}",
        f"set ARGS=-gfx {cfg.gfx_mode}",
        f"if not \"%LEVEL%\"==\"\" set ARGS=%ARGS% -level %LEVEL%",
        "",
        "echo === Killing existing BeamNG processes ===",
        "taskkill /F /IM BeamNG.drive.exe 2>nul",
        "taskkill /F /IM BeamNG.drive.x64.exe 2>nul",
        "timeout /t 3 /nobreak >nul",
        "",
    ]
    if mode == "sandboxie" and sb:
        lines += [
            f'set SANDBOX="{sb}"',
            "echo === Instance 1 (affinity FF) ===",
            f'start "BNG1" /affinity FF %SANDBOX% /box:BNG1 %GAME% %ARGS%',
            f"timeout /t {int(cfg.stagger_s)} /nobreak >nul",
            "echo === Instance 2 (affinity FF00) ===",
            f'start "BNG2" /affinity FF00 %SANDBOX% /box:BNG2 %GAME% %ARGS%',
            f"timeout /t {int(cfg.stagger_s)} /nobreak >nul",
            "echo === Instance 3 (affinity FF0000) ===",
            f'start "BNG3" /affinity FF0000 %SANDBOX% /box:BNG3 %GAME% %ARGS%',
        ]
    else:
        for i, (prof, aff) in enumerate(
            zip(cfg.profiles, ("FF", "FF00", "FF0000"), strict=True), start=1
        ):
            lines += [
                f"echo === Instance {i} (affinity {aff}, userpath {prof}) ===",
                f'if not exist "{prof}" mkdir "{prof}"',
                f'start "BNG{i}" /affinity {aff} %GAME% %ARGS% -userpath "{prof}"',
            ]
            if i < 3:
                lines.append(f"timeout /t {int(cfg.stagger_s)} /nobreak >nul")
    lines += ["", f"timeout /t {int(cfg.stagger_s)} /nobreak >nul"]
    if obs:
        lines += [
            "echo === OBS ===",
            f'start "OBS" /affinity F000000 "{obs}"',
        ]
    lines += ["echo === Rig up ===", "pause"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return path
