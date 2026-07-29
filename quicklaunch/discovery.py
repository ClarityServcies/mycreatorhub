"""Scan install + userfolder for levels, vehicles, configs (zip-aware, fast)."""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Iterable
import zipfile

ProgressCb = Callable[[str, float], None]

SKIP_DIR_NAMES = {"_parked", "repo", ".git", "__pycache__", "temp", "cache"}


@dataclass
class LevelInfo:
    id: str
    name: str
    preview: str = ""
    source: str = ""


@dataclass
class VehicleInfo:
    id: str
    name: str
    preview: str = ""
    source: str = ""
    configs: list[str] = field(default_factory=list)


@dataclass
class ScanCache:
    levels: list[LevelInfo] = field(default_factory=list)
    vehicles: list[VehicleInfo] = field(default_factory=list)
    fingerprint: str = ""

    def to_json(self) -> dict:
        return {
            "fingerprint": self.fingerprint,
            "levels": [asdict(x) for x in self.levels],
            "vehicles": [asdict(x) for x in self.vehicles],
        }

    @classmethod
    def from_json(cls, data: dict) -> "ScanCache":
        levels = [LevelInfo(**x) for x in data.get("levels", [])]
        vehicles = [VehicleInfo(**x) for x in data.get("vehicles", [])]
        return cls(levels=levels, vehicles=vehicles, fingerprint=str(data.get("fingerprint", "")))


def _read_json_bytes(raw: bytes) -> dict | None:
    try:
        return json.loads(raw.decode("utf-8", errors="ignore"))
    except json.JSONDecodeError:
        return None


def _display_from_info(data: dict | None, fallback: str) -> str:
    if not data:
        return fallback
    for key in ("Name", "name", "title", "Title"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return fallback


def _norm(p: str) -> str:
    return p.replace("\\", "/")


def _should_skip_path(path: Path) -> bool:
    return any(part.lower() in SKIP_DIR_NAMES or part.lower().startswith("_parked") for part in path.parts)


def _mtime_sig(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def content_fingerprint(game_install: Path, userfolder: Path) -> str:
    """Cheap invalidation key — folder mtimes, not full zip reads."""
    parts: list[str] = []
    for p in (
        game_install / "content" / "levels",
        game_install / "content" / "vehicles",
        game_install / "integrity.json",
        userfolder / "vehicles",
        userfolder / "mods",
        userfolder / "mods" / "unpacked",
    ):
        parts.append(f"{p}:{_mtime_sig(p):.0f}")
    # top-level mod zip names + mtimes (fast)
    mods = userfolder / "mods"
    if mods.is_dir():
        try:
            zips = sorted(
                f"{c.name}:{_mtime_sig(c):.0f}"
                for c in mods.iterdir()
                if c.is_file() and c.suffix.lower() == ".zip"
            )
            parts.append("modzips:" + ",".join(zips[:80]))
        except OSError:
            pass
    return "|".join(parts)


def _iter_zip_names(zpath: Path) -> list[str]:
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            return zf.namelist()
    except (OSError, zipfile.BadZipFile):
        return []


def _zip_read(zpath: Path, inner: str) -> bytes | None:
    try:
        with zipfile.ZipFile(zpath, "r") as zf:
            try:
                return zf.read(inner)
            except KeyError:
                lower = inner.replace("\\", "/").lower()
                for name in zf.namelist():
                    if name.replace("\\", "/").lower() == lower:
                        return zf.read(name)
                return None
    except (OSError, zipfile.BadZipFile):
        return None


def _preview_cache_dir() -> Path:
    from paths import app_dir

    d = app_dir() / "cache" / "previews"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _extract_level_preview(zpath: Path, level_id: str, names: list[str]) -> str:
    for ext in (".jpg", ".png"):
        cache = _preview_cache_dir() / f"{level_id}{ext}"
        if cache.is_file() and cache.stat().st_size > 1000:
            return str(cache)
    scored: list[tuple[int, str]] = []
    lid = level_id.lower()
    for n in names:
        nrm = _norm(n)
        low = nrm.lower()
        if not (low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".png")):
            continue
        if "preview" not in low:
            continue
        score = 0
        if low.endswith(f"{lid}_preview1.jpg") or low.endswith(f"{lid}_preview.jpg"):
            score += 50
        if f"levels/{lid}/" in low:
            score += 10
        if "/facilities/" in low or "/driftspots/" in low or "/delivery/" in low:
            score -= 20
        if nrm.count("/") <= 3:
            score += 5
        scored.append((score, nrm))
    scored.sort(key=lambda x: -x[0])
    for score, nrm in scored[:6]:
        if score < 0:
            continue
        raw = _zip_read(zpath, nrm)
        if not raw or len(raw) < 1000:
            continue
        ext = ".png" if nrm.lower().endswith(".png") else ".jpg"
        out = _preview_cache_dir() / f"{level_id}{ext}"
        try:
            out.write_bytes(raw)
            return str(out)
        except OSError:
            continue
    return ""


def _scan_level_dir(folder: Path, level_id: str, source: str) -> LevelInfo | None:
    info = folder / "info.json"
    if not info.is_file():
        return None
    data = _read_json_bytes(info.read_bytes())
    name = _display_from_info(data, level_id)
    preview = ""
    for cand in ("preview.png", "preview.jpg", "default.jpg", "default.png"):
        p = folder / cand
        if p.is_file():
            preview = str(p)
            break
    return LevelInfo(id=level_id, name=name, preview=preview, source=source)


def _scan_level_zip(zpath: Path) -> list[LevelInfo]:
    out: list[LevelInfo] = []
    names = _iter_zip_names(zpath)
    info_entries = [n for n in names if _norm(n).endswith("/info.json") or _norm(n) == "info.json"]
    if not info_entries:
        info_entries = [n for n in names if n.lower().endswith("info.json")]
    seen_ids: set[str] = set()
    for entry in info_entries:
        nrm = _norm(entry)
        if nrm == "info.json":
            level_id = zpath.stem
        else:
            parts = nrm.split("/")
            if len(parts) >= 2 and parts[0] == "levels":
                level_id = parts[1]
            else:
                level_id = parts[0] if parts[0] != "info.json" else zpath.stem
        if level_id in seen_ids or level_id.startswith("."):
            continue
        seen_ids.add(level_id)
        raw = _zip_read(zpath, entry)
        data = _read_json_bytes(raw) if raw else None
        name = _display_from_info(data, level_id)
        preview = _extract_level_preview(zpath, level_id, names)
        out.append(LevelInfo(id=level_id, name=name, preview=preview, source=str(zpath)))
    if not out:
        raw = _zip_read(zpath, "info.json")
        if raw:
            data = _read_json_bytes(raw)
            preview = _extract_level_preview(zpath, zpath.stem, names)
            out.append(
                LevelInfo(
                    id=zpath.stem,
                    name=_display_from_info(data, zpath.stem),
                    preview=preview,
                    source=str(zpath),
                )
            )
    return out


def _vehicle_configs_from_names(names: Iterable[str], vehicle_id: str) -> list[str]:
    configs: set[str] = set()
    for n in names:
        nrm = _norm(n)
        if not nrm.lower().endswith(".pc"):
            continue
        configs.add(Path(nrm).stem)
    return sorted(configs, key=str.lower)


def _scan_vehicle_dir(folder: Path, vehicle_id: str, source: str) -> VehicleInfo | None:
    infos = list(folder.glob("info_*.json")) + list(folder.glob("info.json"))
    name = vehicle_id
    for info in infos:
        data = _read_json_bytes(info.read_bytes())
        name = _display_from_info(data, name)
        break
    if not infos and not list(folder.glob("*.jbeam")) and not list(folder.glob("*.pc")):
        return None
    configs = ["Default"] + sorted({p.stem for p in folder.glob("*.pc")}, key=str.lower)
    preview = ""
    for cand in (f"{vehicle_id}.png", "default.png", "preview.png"):
        p = folder / cand
        if p.is_file():
            preview = str(p)
            break
    return VehicleInfo(id=vehicle_id, name=name, preview=preview, source=source, configs=configs)


def _scan_vehicle_zip(zpath: Path) -> VehicleInfo | None:
    names = _iter_zip_names(zpath)
    if not names:
        return None
    vehicle_id = zpath.stem
    for n in names:
        parts = _norm(n).split("/")
        if len(parts) >= 2 and parts[0] == "vehicles" and parts[1]:
            vehicle_id = parts[1]
            break
    name = vehicle_id
    for n in names:
        bn = Path(_norm(n)).name.lower()
        if (bn.startswith("info_") and bn.endswith(".json")) or bn == "info.json":
            raw = _zip_read(zpath, n)
            data = _read_json_bytes(raw) if raw else None
            name = _display_from_info(data, name)
            break
    configs = ["Default"] + _vehicle_configs_from_names(names, vehicle_id)
    return VehicleInfo(id=vehicle_id, name=name, source=str(zpath), configs=configs)


def _walk_mod_level_dirs(root: Path) -> list[Path]:
    found: list[Path] = []
    levels_root = root / "levels"
    if levels_root.is_dir():
        for child in levels_root.iterdir():
            if child.is_dir():
                found.append(child)
    unpacked = root / "mods" / "unpacked"
    if unpacked.is_dir():
        for path in unpacked.rglob("levels"):
            if _should_skip_path(path) or not path.is_dir():
                continue
            for child in path.iterdir():
                if child.is_dir():
                    found.append(child)
    return found


def _add_vehicle(vehicles: dict[str, VehicleInfo], vi: VehicleInfo) -> None:
    if not vi.id:
        return
    if vi.id in vehicles:
        existing = vehicles[vi.id]
        merged = sorted(set(existing.configs) | set(vi.configs), key=str.lower)
        if "Default" in merged:
            merged = ["Default"] + [c for c in merged if c != "Default"]
        existing.configs = merged
        if not existing.preview and vi.preview:
            existing.preview = vi.preview
    else:
        if "Default" not in vi.configs:
            vi.configs = ["Default"] + vi.configs
        vehicles[vi.id] = vi


def scan_all(
    game_install: Path,
    userfolder: Path,
    progress: ProgressCb | None = None,
    *,
    scan_mod_zips: bool = False,
    workers: int | None = None,
) -> ScanCache:
    levels: dict[str, LevelInfo] = {}
    vehicles: dict[str, VehicleInfo] = {}
    fp = content_fingerprint(game_install, userfolder)
    nworkers = workers or min(8, (os.cpu_count() or 4))

    def prog(msg: str, frac: float) -> None:
        if progress:
            progress(msg, frac)

    # --- levels: content zips in parallel ---
    content_levels = game_install / "content" / "levels"
    level_zips = (
        [p for p in content_levels.iterdir() if p.suffix.lower() == ".zip"]
        if content_levels.is_dir()
        else []
    )
    prog(f"Scanning {len(level_zips)} level zips…", 0.05)
    with ThreadPoolExecutor(max_workers=nworkers) as pool:
        futs = {pool.submit(_scan_level_zip, zp): zp for zp in level_zips}
        done = 0
        for fut in as_completed(futs):
            done += 1
            for li in fut.result() or []:
                if li.id and li.id not in levels:
                    levels[li.id] = li
            if done % 4 == 0:
                prog(f"Levels {done}/{len(level_zips)}", 0.05 + 0.35 * done / max(len(level_zips), 1))

    # --- levels: unpacked userfolder ---
    if userfolder.is_dir():
        for folder in _walk_mod_level_dirs(userfolder):
            li = _scan_level_dir(folder, folder.name, str(folder))
            if li and li.id not in levels:
                levels[li.id] = li

    # --- vehicles: content zips in parallel ---
    content_vehs = game_install / "content" / "vehicles"
    veh_zips = []
    if content_vehs.is_dir():
        veh_zips = [
            p
            for p in content_vehs.iterdir()
            if p.suffix.lower() == ".zip" and not p.name.startswith("_") and p.stem.lower() != "common"
        ]
    prog(f"Scanning {len(veh_zips)} vehicle zips…", 0.45)
    with ThreadPoolExecutor(max_workers=nworkers) as pool:
        futs = {pool.submit(_scan_vehicle_zip, zp): zp for zp in veh_zips}
        done = 0
        for fut in as_completed(futs):
            done += 1
            vi = fut.result()
            if vi:
                _add_vehicle(vehicles, vi)
            if done % 10 == 0:
                prog(f"Vehicles {done}/{len(veh_zips)}", 0.45 + 0.35 * done / max(len(veh_zips), 1))

    # --- userfolder vehicles (unpacked — fast) ---
    if userfolder.is_dir():
        uv = userfolder / "vehicles"
        if uv.is_dir():
            for child in uv.iterdir():
                if child.is_dir() and not child.name.startswith("_"):
                    vi = _scan_vehicle_dir(child, child.name, str(child))
                    if vi:
                        _add_vehicle(vehicles, vi)

        # mods/unpacked only (skip repo + parked)
        unpacked = userfolder / "mods" / "unpacked"
        if unpacked.is_dir():
            for veh_root in unpacked.rglob("vehicles"):
                if _should_skip_path(veh_root) or not veh_root.is_dir():
                    continue
                for child in veh_root.iterdir():
                    if child.is_dir() and not child.name.startswith("_"):
                        vi = _scan_vehicle_dir(child, child.name, str(child))
                        if vi:
                            _add_vehicle(vehicles, vi)

        # optional: top-level mods/*.zip only (NOT repo recursive)
        if scan_mod_zips:
            mods = userfolder / "mods"
            if mods.is_dir():
                top_zips = [
                    p
                    for p in mods.iterdir()
                    if p.is_file() and p.suffix.lower() == ".zip" and not p.name.startswith("_")
                ]
                prog(f"Mod zips {len(top_zips)}…", 0.85)

                def _mod_zip_vehicles(zp: Path) -> list[VehicleInfo]:
                    names = _iter_zip_names(zp)
                    if not names:
                        return []
                    has_veh_path = any(_norm(n).lower().startswith("vehicles/") for n in names)
                    out: list[VehicleInfo] = []
                    if has_veh_path:
                        ids: set[str] = set()
                        for n in names:
                            parts = _norm(n).split("/")
                            if len(parts) >= 2 and parts[0] == "vehicles" and parts[1]:
                                ids.add(parts[1])
                        for vid in ids:
                            subset = [n for n in names if _norm(n).startswith(f"vehicles/{vid}/")]
                            name = vid
                            for n in subset:
                                bn = Path(_norm(n)).name.lower()
                                if bn.startswith("info_") and bn.endswith(".json"):
                                    raw = _zip_read(zp, n)
                                    data = _read_json_bytes(raw) if raw else None
                                    name = _display_from_info(data, name)
                                    break
                            out.append(
                                VehicleInfo(
                                    id=vid,
                                    name=name,
                                    source=str(zp),
                                    configs=["Default"] + _vehicle_configs_from_names(subset, vid),
                                )
                            )
                    else:
                        # loose vehicle zip (jbeam/info at root)
                        if any(n.lower().endswith(".jbeam") for n in names) or any(
                            Path(_norm(n)).name.lower().startswith("info_") for n in names
                        ):
                            vi = _scan_vehicle_zip(zp)
                            if vi:
                                out.append(vi)
                    return out

                with ThreadPoolExecutor(max_workers=nworkers) as pool:
                    for fut in as_completed([pool.submit(_mod_zip_vehicles, zp) for zp in top_zips]):
                        for vi in fut.result():
                            _add_vehicle(vehicles, vi)

    prog("Scan complete", 1.0)
    return ScanCache(
        levels=sorted(levels.values(), key=lambda x: x.name.lower()),
        vehicles=sorted(vehicles.values(), key=lambda x: x.name.lower()),
        fingerprint=fp,
    )


def load_cache(path: Path) -> ScanCache | None:
    if not path.is_file():
        return None
    try:
        return ScanCache.from_json(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def save_cache(path: Path, cache: ScanCache) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache.to_json(), indent=2), encoding="utf-8")


def cache_is_fresh(path: Path, game_install: Path, userfolder: Path) -> ScanCache | None:
    cache = load_cache(path)
    if not cache or not cache.levels:
        return None
    if cache.fingerprint and cache.fingerprint == content_fingerprint(game_install, userfolder):
        return cache
    return None
