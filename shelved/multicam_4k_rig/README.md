# SHELVED — Multi-Instance 4K Capture Rig

**Status:** parked out of QuickLaunch (2026-07-29).  
**Not deleted** — all code/docs/batch live here until you want it wired back.

## Contents

| File | What |
|------|------|
| `multicam.py` | Launch logic: Sandboxie / `C:\BNG1..3` userpath, affinity, stagger, OBS |
| `Launch-Multicam-Rig.bat` | Standalone batch launcher |
| `docs/MULTICAM_4K_RIG.md` | Architecture + OBS / VRAM / affinity notes |
| `config_multicam_snapshot.json` | Settings block stripped from QuickLaunch `config.json` |

## Restore into QuickLaunch

1. Copy `multicam.py` → `quicklaunch/multicam.py`
2. Copy `docs/MULTICAM_4K_RIG.md` → `quicklaunch/docs/`
3. Re-add MULTICAM button + panel to `quicklaunch/ui.py` (git history / this shelf)
4. Merge `config_multicam_snapshot.json` into settings under key `multicam`
5. Do **not** replace single-player SPAWN — keep as separate button

## Standalone (without QuickLaunch UI)

```bat
shelved\multicam_4k_rig\Launch-Multicam-Rig.bat
```

Or from Python (after copying `multicam.py` onto `PYTHONPATH` with `paths.py` available):

```python
from multicam import MulticamConfig, launch_rig
launch_rig(MulticamConfig(exe_path=r"...\Bin64\BeamNG.drive.x64.exe"))
```

## Note

Single-instance QuickLaunch SPAWN (D3D12, `-level`, native `-vehicle`) is unaffected.
