"""Launcher → game handoff helpers (safe, retail-only).

No AC/DRM bypass. No DXGI/SpecialK reinjection.
Prewarm Steam, validate Bin64 cleanliness for D3D12, path cache.
"""
from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from paths import app_dir, steam_exe

# Overlay / proxy DLLs that commonly break BeamNG D3D12 (parked for 0.39 theater)
SUSPECT_BIN64_NAMES = (
    "dxgi.dll",  # often SpecialK / ReShade proxy — stock game does NOT ship this in Bin64
    "d3d11.dll",  # proxy wrappers (not the system DLL)
    "dinput8.dll",
    "version.dll",
    "winmm.dll",
    "SpecialK64.dll",
    "SpecialK32.dll",
    "ReShade64.dll",
    "ReShade32.dll",
)


@dataclass
class HandoffReport:
    steam_ready: bool = False
    steam_started: bool = False
    injector_warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        bits = []
        if self.steam_started:
            bits.append("Steam prewarmed")
        elif self.steam_ready:
            bits.append("Steam already up")
        else:
            bits.append("Steam not found")
        if self.injector_warnings:
            bits.append(f"{len(self.injector_warnings)} injector warn")
        return " · ".join(bits)


def _path_cache_file() -> Path:
    return app_dir() / "cache" / "path_cache.json"


def load_path_cache() -> dict:
    p = _path_cache_file()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_path_cache(data: dict) -> None:
    p = _path_cache_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def steam_running() -> bool:
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq steam.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return "steam.exe" in (out.stdout or "").lower()
    except (OSError, subprocess.TimeoutExpired):
        return False


def ensure_steam(silent: bool = True, wait_s: float = 2.5) -> tuple[bool, bool]:
    """Return (ready, started_now). Soft-start Steam if cold — DRM/ticket warm."""
    if steam_running():
        return True, False
    exe = steam_exe()
    if not exe or not exe.is_file():
        return False, False
    try:
        CREATE_NO_WINDOW = 0x08000000
        flags = (
            getattr(subprocess, "DETACHED_PROCESS", 0x8)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
            | CREATE_NO_WINDOW
        )
        subprocess.Popen(
            [str(exe), "-silent"],
            cwd=str(exe.parent),
            close_fds=True,
            creationflags=flags if silent else 0,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # brief wait so ticket store is warm — don't block forever
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if steam_running():
                return True, True
            time.sleep(0.25)
        return steam_running(), True
    except OSError:
        return False, False


def scan_bin64_injectors(bin64: Path | str | None) -> list[str]:
    """Warn on proxy DLLs in Bin64 that fight D3D12. Never delete — report only."""
    if not bin64:
        return []
    root = Path(bin64)
    if not root.is_dir():
        # allow passing exe path
        if root.is_file():
            root = root.parent
        else:
            return []
    warns: list[str] = []
    for name in SUSPECT_BIN64_NAMES:
        p = root / name
        if p.is_file():
            warns.append(
                f"{p.name} in Bin64 ({p.stat().st_size} bytes) — can break D3D12. "
                f"Keep parked (see theater strip / SpecialK park)."
            )
    return warns


def prepare_handoff(
    *,
    exe_path: str,
    prewarm_steam: bool = True,
    check_injectors: bool = True,
) -> HandoffReport:
    report = HandoffReport()
    if prewarm_steam:
        ready, started = ensure_steam()
        report.steam_ready = ready
        report.steam_started = started
        if started:
            report.notes.append("Started Steam -silent for ticket warm")
    else:
        report.steam_ready = steam_running()

    if check_injectors:
        report.injector_warnings = scan_bin64_injectors(exe_path)
        report.notes.extend(report.injector_warnings)

    # refresh path cache for next cold start (no re-registry scan if used later)
    cache = load_path_cache()
    cache["exe_path"] = exe_path
    cache["last_handoff"] = time.time()
    save_path_cache(cache)
    return report
