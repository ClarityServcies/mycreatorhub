# BeamNG v0.39 Discovery + Triage

**Generated:** 2026-07-29  
**Root:** `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current`  
**Method:** WORKING METHOD steps 1–2 only — **STOP for review** (no fix batches yet)

---

## Inventory counts

| Bucket | Count |
|--------|------:|
| Mods unpacked | 15 |
| Mods zip (active) | 35 |
| Mods parked | 5 |
| Vehicles in userfolder | 24 |
| Vehicles in unpacked mods | 131 |
| Unique vehicle entries in zips | 32 |
| BOM on info/jbeam (loose) | 0 |
| Bare-comma jbeams (loose) | 1 |
| Bad info_2d / info_rc_car (zips) | 18 path hits |

Detail files: `inventory_*.txt`, `findings_*.txt`, `DISCOVERY_COUNTS.json`

---

## Phase 1 theater — DONE (pre-discovery)

| Item | Status |
|------|--------|
| Bollard vs ExplosionLab `input_actions.json` | Renamed to unique filenames |
| `pit_trap_mk2.bak_*` | Parked under `mods\_parked\` |
| majora_moon under `/vehicles/common/` | Moved to `/vehicles/<name>/` |
| mock_crab_walker spawn | **SPAWN WORKS** (jbeam parse fixed) |

### mock_crab_walker fix notes
- Root cause was not only BOM — jbeam was **invalid JSON** for 0.39 decoder:
  - 136 knee nodes pasted inside `hydros` (moved into `nodes`)
  - 16 bare-comma empty beam rows (removed)
  - premature `],` closing `beams` before G29 knee block (fixed; close before `triangles`)
- `.pc` set to format 2 + `mainPartName`
- MCP spawn: collada import + vehicle load OK
- **Follow-up (NEEDS-REVIEW):** first spawn showed insane speed (`~1e25`) — cage explode / physics QA separately (not a selector/parse blocker)

---

## TRIAGE

### OK (leave alone for now)
- Stock install vehicles
- Parked mods in `_parked` (intentional)
- majora_moon vehicle paths (post-move)
- mock_crab parse/spawn path (physics separate)

### AUTO-FIXABLE (safe batch later)
| Class | Evidence | Action |
|-------|----------|--------|
| Bad `info_2d` / `info_rc_car` | 18 hits in zips (Jake, McQLava, Tung, Ballerina, Police Truck…) | Park/rename ignore configs or strip from zip rebuild |
| Bare commas in jbeam | `BollardContoller\...\bollard_hitch.jbeam` | Strip bare-comma lines (same as mock_crab) |
| Duplicate kart wheel/tire parts | Live log: parts in both `/vehicles/mock_crab_walker/` resolve path and `/vehicles/common/` | Deduplicate / stop shadowing common |
| AgentY Dummy bad jbeam | Log: unable to decode `agenty_dummy_mod_intcollision_seats_R-automation.jbeam` | Park or fix JSON |
| Filesystem MCP path stale | `mcp.json` still old BeamNG path | Point at `BeamNG\BeamNG.drive` |
| Zip name noise | Many `FIXED - *.zip` | Rename for sanity (cosmetic) |

### NEEDS-REVIEW (do not auto-guess)
| Class | Why |
|-------|-----|
| **hammer.zip vs SledgeHammer.zip** | Both ship `vehicles/hammer/input_actions*.json` → VFS collision |
| Multiple vehicle `input_actions.json` in zips | Per-vehicle OK unless same vehicle folder duplicated across zips |
| mock_crab explode / instability | Spawn OK; cage may need spring/weight pass |
| `kanderman/skyride` / hubSkyrideGuard | Earlier FATAL on vehicle Lua load — confirm if still active |
| Zeit on 0.39 | May need disable until update |
| dxgi / dinput8 injectors | Security/stability review |
| Emissive→nits / GT7 re-grade | Materials batch — flag first, don’t bake brightness |
| Translations / missions / plates / SDF / hydraulic sounds | BREAKING list — batch after this review |
| Tomas21 / MQ skins / Bus Eater atlas / BNGP_31 particles | Asset-specific |
| Folders with spaces in vehicle names | Selector / tooling risk |
| torsion coupler zip under `vehicles/common/pickup` | Intentional shared parts? confirm |

---

## Recommended next batches (after you say go)

1. **AUTO:** strip bollard bare commas · park/repair AgentY jbeam · bad info_* in FIXED zips  
2. **REVIEW:** hammer vs SledgeHammer collision · skyride · Zeit  
3. **BREAKING:** translations / missions / plates / SDF / config names / hydraulic sounds  
4. **Materials:** emissive→nits flags + GT7  
5. **Mesh:** one asset via Blender MCP  

---

## STOP

Discovery + triage complete. No further fix batches until you pick a lane.
