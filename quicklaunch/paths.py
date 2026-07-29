"""Steam / BeamNG install + userfolder discovery (Windows-first, paths overrideable)."""
from __future__ import annotations

import os
import re
import sys
import winreg
from pathlib import Path


APP_ID = 284160
EXE_NAME = "BeamNG.drive.x64.exe"


def app_dir() -> Path:
    return Path(__file__).resolve().parent


def steam_roots() -> list[Path]:
    roots: list[Path] = []
    keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
    ]
    if sys.platform == "win32":
        for hive, sub, name in keys:
            try:
                with winreg.OpenKey(hive, sub) as key:
                    val, _ = winreg.QueryValueEx(key, name)
                    if val:
                        p = Path(str(val).replace("/", "\\"))
                        if p.is_dir() and p not in roots:
                            roots.append(p)
            except OSError:
                pass
    for common in (
        Path(r"C:\Program Files (x86)\Steam"),
        Path(r"C:\Program Files\Steam"),
        Path.home() / ".steam" / "steam",
        Path.home() / ".local" / "share" / "Steam",
    ):
        if common.is_dir() and common not in roots:
            roots.append(common)
    return roots


def steam_exe(steam_root: Path | None = None) -> Path | None:
    roots = [steam_root] if steam_root else steam_roots()
    for root in roots:
        if not root:
            continue
        cand = root / "steam.exe"
        if cand.is_file():
            return cand
    return None


def parse_libraryfolders(vdf: Path) -> list[Path]:
    if not vdf.is_file():
        return []
    text = vdf.read_text(encoding="utf-8", errors="ignore")
    paths = []
    for m in re.finditer(r'"path"\s+"([^"]+)"', text):
        p = Path(m.group(1).replace("\\\\", "\\"))
        if p.is_dir():
            paths.append(p)
    return paths


def find_game_install() -> Path | None:
    for root in steam_roots():
        libs = [root] + parse_libraryfolders(root / "steamapps" / "libraryfolders.vdf")
        seen: set[Path] = set()
        for lib in libs:
            if lib in seen:
                continue
            seen.add(lib)
            install = lib / "steamapps" / "common" / "BeamNG.drive"
            exe = install / "Bin64" / EXE_NAME
            if exe.is_file():
                return install
    return None


def find_exe(install: Path | None = None) -> Path | None:
    inst = install or find_game_install()
    if not inst:
        return None
    exe = inst / "Bin64" / EXE_NAME
    return exe if exe.is_file() else None


def _version_key(name: str) -> tuple:
    parts = []
    for bit in re.split(r"[^\d]+", name):
        if bit.isdigit():
            parts.append(int(bit))
    return tuple(parts) if parts else (0,)


def find_userfolder() -> Path | None:
    """Prefer modern LocalAppData\\BeamNG\\BeamNG.drive\\current, then versioned trees."""
    candidates: list[Path] = []

    modern_root = Path(os.environ.get("LOCALAPPDATA", "")) / "BeamNG" / "BeamNG.drive"
    if modern_root.is_dir():
        current = modern_root / "current"
        if current.is_dir():
            candidates.append(current)
        versions = sorted(
            [p for p in modern_root.iterdir() if p.is_dir() and re.match(r"^\d+\.\d+", p.name)],
            key=lambda p: _version_key(p.name),
            reverse=True,
        )
        candidates.extend(versions)
        candidates.append(modern_root)

    legacy = Path(os.environ.get("LOCALAPPDATA", "")) / "BeamNG.drive"
    if legacy.is_dir():
        versions = sorted(
            [p for p in legacy.iterdir() if p.is_dir() and re.match(r"^\d+\.\d+", p.name)],
            key=lambda p: _version_key(p.name),
            reverse=True,
        )
        candidates.extend(versions)
        candidates.append(legacy)

    docs = Path.home() / "Documents" / "BeamNG.drive"
    if docs.is_dir():
        versions = sorted(
            [p for p in docs.iterdir() if p.is_dir() and re.match(r"^\d+\.\d+", p.name)],
            key=lambda p: _version_key(p.name),
            reverse=True,
        )
        candidates.extend(versions)
        candidates.append(docs)

    for c in candidates:
        if c.is_dir() and ((c / "mods").is_dir() or (c / "vehicles").is_dir() or (c / "settings").is_dir()):
            return c
    return candidates[0] if candidates else None


def console_log_path(userfolder: Path | None) -> Path | None:
    if not userfolder:
        return None
    for name in ("console.log", "beamng.log"):
        p = userfolder / name
        if p.is_file():
            return p
    return userfolder / "console.log"
