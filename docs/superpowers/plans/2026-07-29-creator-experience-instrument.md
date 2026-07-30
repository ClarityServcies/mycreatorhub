# Creator Experience Instrument — Implementation Plan

> **For agentic workers:** execute task-by-task. No fake/demo scenes.

**Goal:** Replace ExplosionLab CEF UI with BeamNG.Drive | Creator Experience MPC instrument (v4.0.0).

**Architecture:** Greenfield `app.js` Angular directive (same `explosionLab` id). `hubDirector` backend unchanged. Empty scene list — scene builder later.

**Tech Stack:** AngularJS 1.5.8, CEF, hubDirector guihooks

## Global Constraints

- Product name: BeamNG.Drive | Creator Experience
- ASCII-only UI chrome
- No fake/stock scenes in UI or mod for this ship
- Minimize → one HUB pill
- Version 4.0.0 + `.bak_pre_instrument*`

## Tasks

- [x] Backup live app.js / app.json / info.json
- [x] Greenfield instrument UI (banks + pads + status + empty scenes)
- [x] Offline verify + STATUS/HANDOFF
