# Banana Native SM-X930 Mali G925 DrawOpt v0.16 — source patch

## Target and status

Experimental source patch for an **already SM-X930 patched Banana Native v0.12.1** tree. Intended title `0400486024DEC000`, firmware/build 131072. Only Samsung SM-X930 / Mali-G925 has the one-lock optimization enabled by default; other devices retain the original texture registry checks. No claims of 50 FPS or crash resolution without a device test. Game asset, original shader pack and save files are **not included**.

## Source changes

1. One-lock, read-only `vka_tex_id_prepare_pending_rec`: for storage image bindings, combine *first creation pending* and *storage upgrade pending* queries, previously two separate mutex/serial-map lookups. No changes to when the render pass ends, image views are made, storage upgrades happen, or GPU barriers. Regular sampled texture bindings still use versioned memo. `DM_VK_DRAW_PREP_FAST=0` restores the old branch.
2. Sample-only timing of five subcomponents in `vka_draw.c`: image preparation, hazard decisions, render-pass begin, texture numeric retyping, and pipeline-key creation. The game already times one in 16 draws (`DM_VK_PACE_PROF`); the new counters piggyback on that and appear under `draw-hot us:` in the existing pace log, no dedicated per-draw spam.
3. Add documentation for `DM_VK_DRAW_PREP_FAST` and `DM_VK_SLOT_POOL` so the launcher validator recognizes the latter experimental flag.

The v0.15 253.32 µs/draw for `images+pass+key` is an **aggregate sampled CPU interval**, NOT proof the new one-lock optimization is a major gain. The finer profiler identifies which part can be safely optimized next. Native compilation and real device results are separate gates.

## Apply and validate

```
python3 apply_drawopt.py /path/to/SM-X930-v0.12.1-source --check
python3 apply_drawopt.py /path/to/SM-X930-v0.12.1-source
SOURCE_ROOT=/path/to/SM-X930-v0.12.1-source python3 -m unittest discover -s . -p 'test_*.py' -v
```

CI rebuilds pinned original code with the prior patches, then applies this patch. The v0.16 APK uses a separate package suffix **`malig925draw`** because signing keys vary across builds: it cannot replace v0.12.1 in place. Import the previous **shader pack ZIP** rather than running the hour-long shader translator, or select the shared shader-pack folder. PanVK's per-package compiled driver pipeline cache will NOT migrate through pack export, so some driver pipeline compiles can still recur. Do not delete either previous app or its shader files.

### Fast scene test profile

```
DM_MOVIE_SKIP=1
DM_VK_PREWARM=0
DM_VK_SLOT_POOL=0
```

Keep GPU driver PanVK faux123 v1.1.8 and resolution at the same values. The fast preflight is on by default on Mali; add `DM_VK_DRAW_PREP_FAST=0` only to isolate it in an A/B comparison. Future log: `python3 drawhot_report.py logfile.txt` outputs the dominant subphase; code changes should target *that*, not speculate.

## Memory caveats

The v0.15 heavy-scene log observed ~2,913 MiB Vulkan allocations and 1,567 MiB `MemAvailable`, but no verified LMKD trace or tombstone. GPU-written live images and render target aliases must not be evicted or downscaled blindly. This patch does not change image residency and is not a confirmed OOM fix.
