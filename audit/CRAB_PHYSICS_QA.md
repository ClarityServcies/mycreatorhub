# mock_crab physics QA

**Result:** STABLE after controller fix

| Condition | Damage @ ~3s |
|-----------|-------------:|
| With old controller | ~1,600,000 |
| Controller disabled | ~350 |
| Settle 2s + soft idle ramp | ~830 @ 10s |

**Cause:** `mock_crab_walk_ctrl` applied plant~0.9 / knee idle on frame 1 → hydro snap shreds cage.

**Fix (deployed):** 2s zero-hydro settle → 3s ramp → mild idle targets. Walk blocked until ramp done.
