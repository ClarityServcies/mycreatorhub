# Smoke — ExplosionLab + Bollard (0.39)

**Date:** 2026-07-29

## File / mount check — PASS

| Check | Result |
|-------|--------|
| ExplosionLab active | yes (`unpacked`) |
| BollardContoller active | yes (`unpacked`) |
| Colliding `input_actions.json` | **gone** |
| ExplosionLab actions file | `input_actions_explosionlab.json` (18 actions) |
| Bollard actions file | `input_actions_bollard.json` (4 actions) |
| Creator Hub `app.json` | present v3.16.5 |
| Bollard Control `app.json` | present v8.5.1 |

### ExplosionLab actions (sample)
`explosionLabUI`, `explosionLabBoom`, `brainrot_run_show`, `brainrot_stop_show`, spawn hammer/slap/tph, …

### Bollard actions
`toggleBollardControl`, `bollardRaiseAll`, `bollardLowerAll`, `bollardSpawn`

## Live MCP — BLOCKED

Game MCP not up (`127.0.0.1:29292` down). Can’t confirm action registry / app open in-session.

**Alex QA after restart (`-enablemcp` or Options → Enable MCP):**
1. Apps → add **Creator Hub** + **Bollard Control**
2. Confirm binds for `explosionLabUI` / `toggleBollardControl` / Brainrot run-stop
3. No “missing action” spam in console

## Next after that

Session audit is effectively closed unless a **named** break appears.
