# QuickLaunch pipeline — what AAA ideas we applied (BeamNG retail)

We **cannot** rewrite BeamNG’s engine (no UE Level Streaming, no PSO bundling inside the game).  
We **can** optimize everything we own: launcher → handoff → CLI → keep D3D12 clean.

## Applied (safe)

| Stage | AAA idea | What QuickLaunch does |
|-------|----------|------------------------|
| Launcher load | Show UI immediately / defer work | Fingerprint cache (~2ms reopen); wallpaper after first paint; Steam prewarm on background thread |
| Launcher→game | Prewarm / cut double-init | Start Steam `-silent` if cold; path cache; one SPAWN payload (no chatty IPC) |
| EXE load | Pick API early | **`-gfx d3d12` first** in argv (latest graphics path on 0.39) |
| Level load | Skip menus / critical path | **`-level <id>`** → `core_loadMapCmd` (waits for mod manager) |
| Vehicle spawn | Spawn on critical path, not post-hoc | **`-vehicle` + `-vehicleConfig` + `-useDefaultPc`** (native parseArgs) instead of replace-after-load Lua |
| Stutter / injectors | Don’t fight the renderer | Warn on Bin64 `dxgi.dll` / SpecialK proxies; **never reinject**; keep SpecialK/Zeit parked for D3D12 |
| Perceived wait | Mask, don’t fake long | Status strip `HANDOFF → D3D12 · map · car…` — no artificial 5s spinner |

## Explicitly NOT done (would break game / out of scope)

| Idea | Why not |
|------|---------|
| SpecialK / DXGI “injectors” for “perf” | Broke / parked for 0.39 D3D12 theater |
| AC/DRM / multiplayer inject timing | Not optimization — won’t help |
| Engine async streaming / PSO cache ship | BeamNG owns that; we don’t patch the exe |
| Fake long loading bars | Contested UX; we prefer instant handoff |
| Keep multiple levels loaded-but-hidden | Memory bomb; not available via retail CLI |

## Default SPAWN argv (0.39)

```
BeamNG.drive.x64.exe
  -gfx d3d12
  -userpath <userfolder>
  -vehicle <model>
  -vehicleConfig <model>/<cfg>.pc   # omitted if Default
  -useDefaultPc
  -level <level_id>
```

Lua replace hook is **off by default** (`vehicle_spawn_mode=native`). Use Settings → Lua / Both only if native spawn fails.

## Injectors scope (this project)

= **mod/content + overlay DLL hygiene**, not cheat injectors.

1. Cache resolved paths (no re-scan Steam every click)  
2. Inject/launch at right lifecycle: after Steam warm, with `-gfx`/`-level`/`-vehicle` set before first frame  
3. Batch CLI args once — no per-asset launcher chatter  
4. Keep proxy DLLs **out** of Bin64 so D3D12 stays stock  
