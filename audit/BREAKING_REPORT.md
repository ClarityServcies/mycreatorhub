# v0.39 BREAKING migration scan

**Generated:** 2026-07-29  
**Scope:** `%LOCALAPPDATA%\BeamNG\BeamNG.drive\current` mods (unpacked + zip)

---

## Results

| # | Change | Hits in your mods | Action |
|---|--------|-------------------|--------|
| 1 | Translations → `locales/translations/<locale>/` | **0** old `locales/*.json` | None |
| 2 | Missions → `gameplay/missions/<levelID>/` | **0** mission packs | None |
| 3 | License plates → Skia templates | **See below** | Review / convert later |
| 4 | TextureDrawPrimitive SDF API | **0** Lua uses | None |
| 5 | Config display names in `info.json` | Literal strings OK (back-compat) | Optional later |
| 6 | Hydraulic sound event renames | **0** event refs found | None |

---

## License plates (only real BREAKING surface)

### Empty mount stubs (likely OK)
Stock-style empty plate *parts* (slot holders only):

- `Bus_Eater/vehicles/buseater/buseater_licenseplate*.jbeam`
- `Mock_Eater/vehicles/mockeater/mockeater_licenseplate*.jbeam`

These are empty `slotType` stubs — not old Skia-incompatible *design* packs. Leave unless spawn/log shows plate errors.

### Zip
- `SpiderMan_2__Wheel_Bike.zip` → `scetk800_licenseplate*.jbeam` — flag; convert or park if plates pink/broken in-game.

### majora_moon (NEEDS-REVIEW)
Multiple majora vehicles use `slotType: ["licenseplate_design_2_1", "licenseplate_design_52_11", …]` to hang props on the plate-design slot. That hitchhiked the old plate-design system. Skia may change how those slots resolve — **do not auto-rewrite** without a live attach test.

---

## Verdict

BREAKING batch for this userfolder is mostly **clean**. No auto-migrations applied (nothing safe + required).

Next plan step: **materials / emissive→nits + GT7 flags**.
