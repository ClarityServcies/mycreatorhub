# BeamNG.Drive | Creator Experience — instrument UI design

**Date:** 2026-07-29  
**Product name:** BeamNG.Drive | Creator Experience  
**Short label (UI chrome):** `CREATOR EXPERIENCE` / minimize pill `HUB`  
**Mod package:** `ExplosionLab` (live unpacked path unchanged)  
**Approach:** Greenfield in-game UI rewrite (AngularJS CEF) over existing `hubDirector` backend  
**Status:** Design approved in brainstorm — awaiting Alex review of this file before implementation plan

---

## 1. Vision

Creator Experience is an **in-game, hidable control instrument** — not a software settings tree.

Feel:

- MPC / drum machine / Ableton Push / Stream Deck
- Racing dash + cinematic console
- Same product lineage as ExplosionLab Creator Hub, rebuilt as pads

User presses large pads. World reacts. Deep file paths stay hidden.

Preview is the **game world** through a clear cutout (no embedded live video stream in CEF for this slice).

---

## 2. Architecture

### Keep

| Layer | What |
|-------|------|
| Package | `ExplosionLab` mod folder + companion mods (bollards, traps, CharacterTexFix, etc.) |
| Lua | `hubDirector.lua` and existing theater APIs |
| Bridge | `bngApi.engineLua` + `guihooks` (`hubDirectorState` ~10 Hz, dirty fields) |
| Hide | Whole UI → one floating **HUB** pill; restore opens full instrument |

### Replace

| Layer | What |
|-------|------|
| UI shell | Current giant Angular template / Script Lab panel IA |
| Chrome | New three-zone instrument layout + bank/pad system |
| Version | UI bump to **v4.0.0** with `.bak_pre_instrument*` backups |

### Stack (BeamNG-forced)

- AngularJS 1.5.8 `beamng.apps` directive inside CEF
- ASCII-only decorative chrome (CEF mojibake policy)
- Visual tokens: dark cinematic + cyan accent (evolve cyber-sigilism; one accent family)
- No Vue-for-mods, no ImGui in-game for this product

### Three zones (always)

```
+----------------------------------+
|  PREVIEW CUTOUT (clear / glass)  |  game world = live view
+----------------------------------+
|  BANK TABS + PAD GRID            |  the instrument
+----------------------------------+
|  STATUS / LOG STRIP              |
+----------------------------------+
```

### Perf (non-negotiable)

- Do not rebuild playlist / castSetup DOM on every 10 Hz push
- Heavy trees: `ng-if` when hidden; frequent chrome: `ng-show`
- Pad press → direct Lua; no confirm spam for common actions
- No heavy particle systems in v1 (optional later behind PERF flag)

---

## 3. Banks and pads

### Mental model

Sampler banks. One bank visible. Pads fire immediately. Deep edit = another bank or slide-up drawer — never nested “Scene → Vehicles → Configure → Spawn”.

### Bank tabs

| Bank | Job |
|------|-----|
| **SCENE** | Load/reset world context: map helpers, weather, time, reset; spawn vehicle / object / character; random scene |
| **SHOW** | Theater transport: scene select, LAUNCH, PLAY, STOP, PLAY SHOW, skip, clear cast (preserves Script Lab verbs) |
| **PHYSICS** | Crash test, ragdoll, gravity, explosion, launch, flip, freeze, reset damage |
| **CAM** | Follow, cinema, slow-mo, replay, drone, screenshot, record |
| **CONTENT** | Favorites, recent, custom vehicles/props/characters, scenes, packs |

### Pad grid

- Default layout: **4 columns × 2 rows** (8 pads) per bank page
- Overflow: second page via bank page dots or a `>` pad — not nested menus
- Pad labels: max ~14 ASCII chars; prefer verb style (`LAUNCH`, `PLAY SHOW`, `CLEAR CAST`)

### Pad rules

- Large hit target; icon + short ASCII label
- States: idle / hover / armed / pressing / disabled
- Press feedback: scale-down + edge glow pulse (CSS, CEF-cheap)
- Color = state only (cyan armed, amber warn/confirm, red stop, green go)
- Disabled = dim; optional one-line tooltip reason
- Common actions = **one press**
- Implementation order: SHOW Live pads first → CONTENT/SCENE Live → Soft → Stub

### Wiring tiers

| Tier | Meaning | Examples |
|------|---------|----------|
| **Live** | Existing Lua/API | LAUNCH, PLAY, STOP, PLAY SHOW, CLEAR CAST, RANDOM SCENE, favorite spawn, bank switch |
| **Soft** | Wire if GE API known; else disabled with reason | Weather, time, some cam modes |
| **Stub** | Visible pad; status explains TBD or opens pack stub | Full macros e.g. `GIANT HAMMER TEST` |

### SHOW bank contract (must not regress)

| UI | Lua | Effect |
|----|-----|--------|
| Scene pick (drawer/list) | `selectScene` | Detail only — **no spawn** |
| LAUNCH | `launch` / `launchWithSetup` | Stage frozen |
| PLAY | `play` | Release motion |
| PLAY SHOW | `runShow` | Show flow |
| STOP / CLEAR | existing stop/clear | Teardown |

### Drawers (escape hatch)

Slide-up from pad zone / status edge:

- Scene list (group chips + playlist)
- Cast editor (weaponlab-style select/add/remove/presets where already shipped)
- Favorites / content browser (v1: thin list + search if cheap)

Close drawer → back to pads. Backdrop slightly darkens; preview cutout still shows world.

### Collections / packs

- A pack is a named set of pads / macro steps (e.g. “Brain Rot Pack”)
- v1: JSON shape + one built-in stub pack; full pack editor = later slice
- Future: one pad runs multi-step workflow (map → spawn → cam → record → event)

---

## 4. Preview, motion, status

### Preview cutout

- Top zone mostly transparent — sim is the live preview
- Thin glass readout: product title `BeamNG.Drive | Creator Experience` (or compact `CREATOR EXPERIENCE`), scene name, phase chip (`IDLE` / `SELECTED` / `STAGED` / `ROLLING`), map + vehicle one-liners
- Optional “about to create” card when a CONTENT/macro pad is armed (text + cached thumbs if available — not a CEF 3D renderer)
- Loading: step checklist (`Preparing scene` with done/active/pending marks) — never bare “Loading…”

### Motion

- Pad: scale-down + glow pulse
- Bank switch: short crossfade / slight slide
- Drawer: slide up; short backdrop dim
- Minimize: full instrument → one **HUB** pill (no orphan tab strips)
- v1: no particle dust/sparks (CEF cost)

### Status strip

- One live line: last action + result
- Compact: phase, cast count, `t`, pool/perf as small toggles
- Tap expands last ~20 log lines; folded by default

### Visual tokens

| Role | Value |
|------|-------|
| Near-black / page | `#080B10` (panels; cutout stays clear) |
| Panel | `#111722` |
| Secondary | `#182230` |
| Accent | Electric blue / cyan |
| Warn | Amber |
| Error | Red |
| Success | Green |

### Sound

- v1: visual only
- Later: short UI click via game audio if cheap

---

## 5. Data flow, errors, migration

### Data flow

```
Pad / drawer
  → engineLua (hubDirector.* / GE helpers)
  ← hubDirectorState (dirty-gated)
  → cheap scope patch
  → list/cast rebuild only when dirty
```

### Confirms

- None for SPAWN / LAUNCH / PLAY / STOP
- Destructive (CLEAR CAST, RESET WORLD): second press within ~1.5s while pad armed amber

### Errors

- Fail → red status one-liner; pad returns idle
- Missing extension → related pads disabled + reason
- No silent no-op on Live pads

### Migration

1. Backup `app.js` / styles / `info.json` → `.bak_pre_instrument*`
2. Ship greenfield UI as major version bump
3. Prefer Lua-stable; add APIs only when a Live pad requires it
4. Rollback = restore bak + Ctrl+L / Ctrl+U

### Offline verify / honesty

- `node --check` on app JS
- ASCII UI scan (non-ASCII decorative = 0)
- `luaparse` if Lua touched
- **In-game QA = Alex spawn only** — no agent in-game claims

---

## 6. Out of scope (this slice)

- Embedded live video / Sunshine / Moonlight / Browser Director AAA shell
- Full node-based Scene Builder
- Full macro editor UI (stub pack OK)
- External ImGui app
- Heavy CEF particle atmospheres
- Rewriting bollard/hazard/trap Lua (consume as-is)

---

## 7. Success criteria

1. Open Creator Experience → pick bank → press pad → world reacts in seconds  
2. Hide → single HUB pill; restore → full instrument  
3. SHOW path unbroken: select → LAUNCH → PLAY / PLAY SHOW  
4. Offline gates pass; Alex confirms in-game feel  
5. UI reads as an instrument, not a settings app  

---

## 8. Naming

| Context | String |
|---------|--------|
| Product | **BeamNG.Drive \| Creator Experience** |
| Compact header | `CREATOR EXPERIENCE` |
| Minimize pill | `HUB` |
| Mod folder / app id | Keep `ExplosionLab` for path compatibility unless a later rename pass is explicit |
| Browser Director | Unchanged side tool; not this product’s shell |

---

## 9. Decisions log (brainstorm)

| Topic | Decision |
|-------|----------|
| Shell host | In-game ExplosionLab CEF app (hidable) |
| Not chosen for this product | Browser Director-first, ImGui-first |
| Live stream in UI | Deferred elsewhere; cutout = game view |
| UI strategy | Greenfield rewrite (approach 3) |
| First instrument metaphor | MPC / Stream Deck pads + banks |
| Script Lab survival | SHOW bank + drawers |
