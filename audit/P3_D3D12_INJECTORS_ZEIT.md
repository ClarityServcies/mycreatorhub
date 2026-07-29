# P3 follow-up — D3D12 / Special K / Zeit

**Date:** 2026-07-29

## Graphics path

| Setting | Value |
|---------|-------|
| `game-settings.json` → `Video.displayDevice` | **D3D12** (already set) |
| Shader quality | High |
| GPU | RTX 4070 |

No change needed for D3D12 switch — already on it.

## Injectors = Special K (parked)

`Bin64\dxgi.dll` (~16 MB) identified as **Special K** (string hits: SpecialK / RTSS / Overlay).  
`Bin64\dinput8.dll` companion proxy (2024).

**Why park (not “update”):** Special K wraps DXGI and fights BeamNG 0.39’s native D3D12 path — extra load, overlay bloat, crash risk. Stock D3D12 + GT7 lighting is the 0.39 graphics stack; SK does not make that faster.

**Parked to (restoreable):**  
`C:\Users\disrv\Documents\beamng-studio\_parked\injectors_specialk_pre_d3d12_2026-07-29\`  
(+ `RESTORE.txt`)

Also leftover SKIF log under `C:\Program Files\Special K\` (install mostly empty).

## Zeit — found (was not missing)

| Where | What |
|-------|------|
| `mods\repo\renderer_components_loadsave_zeit.zip` (~32 MB) | Zeit Render Components **v18.4b** |
| `mods\db.json` key `renderer_components_loadsave_zeit` | Was **active:true** |
| `settings\zeit\rendercomponents\` | Your profiles (Brainrot, vanillaplus, best, LOW…) |

Repo mods don’t show under `mods\unpacked\` — that’s why the earlier scan said “gone.”

**Action for less bloat / 0.39 stock lighting:** set `active:false` in `db.json`.  
Profiles left intact under `settings\zeit\`.  
DB backup: `mods\db.json.bak_pre_zeit_off_2026-07-29`

Zeit is postFX/shader UI on the old render-components path — overlaps hard with 0.39’s new lighting/tonemapper. Re-enable later only if a Zeit build explicitly supports 0.39 D3D12.

## After this

Restart BeamNG once (clean load without SK + without Zeit). Expect faster boot / fewer overlay hooks.
