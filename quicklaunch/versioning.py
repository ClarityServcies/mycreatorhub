"""BeamNG install version / patch checks."""
from __future__ import annotations

import json
import re
from pathlib import Path


def read_integrity_buildinfo(game_install: Path | str | None) -> str:
    if not game_install:
        return ""
    p = Path(game_install) / "integrity.json"
    if not p.is_file():
        return ""
    try:
        # file can be huge; only need the head
        head = p.read_text(encoding="utf-8", errors="ignore")[:2000]
        m = re.search(r'"buildinfo"\s*:\s*"([^"]+)"', head)
        return m.group(1) if m else ""
    except OSError:
        return ""


def read_steam_buildid(steam_apps: Path | None = None) -> str:
    roots = []
    if steam_apps:
        roots.append(steam_apps)
    roots.append(Path(r"C:\Program Files (x86)\Steam\steamapps"))
    for root in roots:
        mf = root / "appmanifest_284160.acf"
        if not mf.is_file():
            continue
        try:
            text = mf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r'"buildid"\s+"(\d+)"', text)
        target = re.search(r'"TargetBuildID"\s+"(\d+)"', text)
        bid = m.group(1) if m else ""
        tid = target.group(1) if target else ""
        if bid and tid and bid != tid:
            return f"{bid} (update pending → {tid})"
        return bid
    return ""


def userfolder_version_hint(userfolder: Path | str | None) -> str:
    if not userfolder:
        return ""
    uf = Path(userfolder)
    # .../BeamNG.drive/current → sibling update markers / parent listing
    parent = uf.parent if uf.name == "current" else uf
    markers = []
    if parent.is_dir():
        for child in parent.iterdir():
            name = child.name
            if "v0.39" in name or name.startswith("0.39"):
                markers.append(name)
    return "0.39" if markers or (uf / "mods").is_dir() else ""


def version_status(game_install: Path | str | None, userfolder: Path | str | None = None) -> dict:
    buildinfo = read_integrity_buildinfo(game_install)
    buildid = read_steam_buildid()
    hint = userfolder_version_hint(userfolder)
    on_039 = ("0.39" in (hint or "")) or ("2026" in buildinfo) or bool(buildinfo)
    # Steam TargetBuildID == buildid means fully updated
    pending = "update pending" in (buildid or "")
    return {
        "buildinfo": buildinfo,
        "steam_buildid": buildid,
        "userfolder_hint": hint,
        "looks_like_039": on_039,
        "update_pending": pending,
        "summary": _summary(buildinfo, buildid, pending, on_039),
    }


def _summary(buildinfo: str, buildid: str, pending: bool, on_039: bool) -> str:
    bits = []
    if on_039:
        bits.append("v0.39")
    if buildinfo:
        # e.g. buildbot build 20859 on winbuildbot - 28/07/2026
        short = buildinfo
        if " - " in short:
            short = short.split(" - ", 1)[-1]
        bits.append(short)
    if buildid:
        bits.append(f"Steam {buildid}")
    if pending:
        bits.append("STEAM UPDATE PENDING")
    return " · ".join(bits) if bits else "version unknown"
