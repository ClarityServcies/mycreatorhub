# BeamNG.drive — Multi-Instance 4K Capture Rig

**Integrated into QuickLaunch as a SEPARATE button: `MULTICAM RIG` (does not replace SPAWN / LAUNCH).**

Full architecture + OBS / VRAM / affinity plan lives in this doc (from Alex’s master build).  
Launcher code: `multicam.py` + UI panel. Batch: `Launch-Multicam-Rig.bat`.

---

## QuickLaunch wiring

| Control | Action |
|---------|--------|
| **LAUNCH / SPAWN** | Single instance, D3D12, normal theater/play |
| **MULTICAM RIG** | Opens panel → START MULTICAM RIG (×3 staggered) + optional OBS |

Default multicam isolation on this PC: **`-userpath C:\BNG1|2|3`** (Sandboxie not installed).  
Gfx default for ×3: **`d3d11`** (lighter than three D3D12). Single SPAWN still uses **d3d12**.

### Correction vs Part 0 of the master draft

| Claim in draft | On Alex’s 0.39 install |
|----------------|------------------------|
| `-userpath` is not a launch arg | **FALSE here** — QuickLaunch already uses it; `parseArgs` / engine accept it. Used for BNG1/2/3 isolation when Sandboxie missing |
| `-gfx dx11` | Use **`-gfx d3d11`** (exe token). `dx11` is not the 0.39 string |
| Sandboxie required | Preferred for true FS overlay; **userpath fallback works** for write isolation of caches |

Keep space-free paths: `C:\BNG1` not `C:\BeamNG Profiles\1`.

---

## Affinity (14700F corrected)

| Process | Logical | Mask |
|---------|---------|------|
| BeamNG 1 hero | 0–7 P | `FF` |
| BeamNG 2 | 8–15 P | `FF00` |
| BeamNG 3 | 16–23 E | `FF0000` |
| OBS | 24–27 E | `F000000` |

Priority: Beam **High**, OBS **Above Normal**, never Realtime.  
Stagger: **20s** cold / **10s** warm.

---

## Pre-session (still on you)

- Game Mode OFF, Background App Max Frame Rate OFF  
- RTSS 60 FPS on BeamNG.drive  
- Borderless 1280×720, Low textures on all three  
- OBS 3840×2160, Window Capture ×3, Lanczos, preview OFF while recording  
- Warm caches once per profile (drive the map on each BNG#)  
- Process Lasso optional for persistence across crash-relaunch  

---

## Parts 1–16 (master plan summary)

1. **Isolation** — Sandboxie boxes *or* `C:\BNG1..3` userpaths *or* thin installs  
2. **CPU** — P-cores for hero/side; E for overhead + OBS  
3. **Launch** — kill orphans → stagger → OBS last  
4. **Small window → 4K** — 720p internal, OBS upscale tiles (not three native 4K)  
5. **Frame pacing** — 60 cap ×3; don’t uncapped waste GPU  
6. **Encode** — one OBS, one NVENC AV1/HEVC session  
7. **VRAM** — textures Low first; stay under ~10GB of 12  
8. **Cache warm** — never record cold  
9. **Mods** — production pack only  
10. **Scenario** — three camera roles, not three identical views  

Full checklist / failure modes / OBS grid coords: see original master build paste in chat history; UI panel encodes the launch automation half.
