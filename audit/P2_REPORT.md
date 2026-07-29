# P2 leftovers batch

**Date:** 2026-07-29

## Applied

| Item | Action |
|------|--------|
| majora cooker (10 remaining) | Renamed bare PNGs → `.color` / `.normal` / `.data`; rewrote materials |
| `bollard_hitch.jbeam` | Removed 2 bare-comma rows (0.39 JSON) |
| grinning_hollow | Already done in mesh pass #1 |

## Checked / OK for now

| Item | Notes |
|------|-------|
| Bus Eater atlas | Referenced `bse_*.png` files **present** on disk — not missing |
| madcat_ghost | Folder exists under userfolder vehicles — intentional ghost mech? leave |

## Still open (NEEDS-REVIEW / later)

| Item | Path / note |
|------|-------------|
| Tomas.zip | `mods\Tomas.zip` |
| New_Crash_Particle_3.zip | particle pack — verify vs BNGP_31 note |
| Space in vehicle name | `CharacterTexFix\vehicles\Resizable Lightning Mcqueen` |
| Bad `info_2d` / `info_rc_car` | Inside `FIXED - *.zip` packs (see `findings_bad_info_zip.txt`) |
| hammer.zip vs SledgeHammer.zip | VFS `vehicles/hammer/` collision |
| kart wheel/tire dupes | Live log vs `/vehicles/common/` |
| Bus Eater cooker suffixes | Still legacy `bse_bus.png` not `.color.png` — optional cook pass |

## Next

P3: Zeit 0.39 · injectors · cut unused · filesystem MCP path
