# Banana Native / SM-X930 Mali-G925 — DrawOpt v0.16 engineering patch

**Status:** implemented and locally source-tested; native Android compilation and device GPU correctness must be verified separately. The 50 FPS target is not demonstrated.

## Evidence and priorities

Latest 2026-11-17 15:57:57 test with early AV1 intro bypass reached 3D at ~35 s; heavy scene replay recording 352.6 ms/frame, **272.7 ms/frame draw preparation**, sampled `images+pass+key` 253.32 µs/draw, 2.9 GiB graphics allocations, minimum 1.57 GiB MemAvailable, 231.1 ms GPU part and launcher out-of-memory verdict (not kernel-confirmed). Earlier tests with `DM_VK_PREWARM=0` and `DM_VK_SLOT_POOL=0` still failed. Data were collected with PanVK faux123 1.1.8 and imported original 42,848 shaders.

## Native changes

1. `vka_draw.c` opt-in **Mali-only exact binding-walk memo**. Reuse per-shader-stage `vka_walk` result when all CPU bind state keys match: shader, descriptor layout, UBO address/size arrays, SSBO and texture stamps, texture/sampler pool bases and TEXU element setting. Shader layouts using UBO-indirect sampled textures, images, samplers, or storage pointers **never** use this cache: guest or GPU memory can change underneath an identical bind record. Results are stored before per-draw view-class modification, and only valid walks are cached. It does *not* cache Vulkan image views or shader outputs; `make_images`, feedback, render-pass hazard checks and barriers run normally. `DM_VK_BIND_WALK_MEMO=0` disables it.
2. `vka_tex.c` **Mali-only burst-aware image cache budget refresh**. Existing cache reevaluates Android MemAvailable every 60 frames (15 with PSI). The SM-X930 heavy scene allocates >1 GiB in ~13 frames, so the budget is stale. During >128 MiB growth (and at most once per 100ms), recalculate the *existing* image limit and run its existing pruning checks. Does not evict live, in-flight, pinned working set or GPU-written images beyond existing safe rules. `DM_VK_IMG_BURST_REFRESH_MB=0` disables; `128` is default SM-X930 policy, capped at 2048. **Cannot solve a working set that actually exceeds available RAM.**
3. `vka_draw.c` **split PT2 sampled profiler** into binding walk; image/hazard/render pass; pipeline key. Also emit cache hit/miss and dynamic-UBO bypass statistics in existing paced log, no per-frame spam. Existing `DM_VK_PACE_PROF` controls one-in-16 sampling. Only used when profiler samples a draw.
4. SM-X930 startup policy: `DM_VK_BIND_WALK_MEMO=1`, `DM_VK_IMG_BURST_REFRESH_MB=128`, `DM_VK_SLOT_POOL=0` (unproven experimental pool disabled by default). **Prewarm remains user-overridable** and should be set `DM_VK_PREWARM=0` while comparing gameplay. No resolution, shader format, draw/mesh omission or GPU sync change.

## Reproducible application

Apply **after** the pinned v0.12.1 MassOpt source patch:

```bash
python3 banana/smx930/massopt_v016/apply_v016.py source/banananative --check
python3 banana/smx930/massopt_v016/apply_v016.py source/banananative
SOURCE_ROOT=source/banananative python3 -m unittest discover -s banana/smx930/massopt_v016 -p 'test_v016_ci.py' -v
```

Source files changed: `dm/gfx/vk_android/vka_draw.c`, `dm/gfx/vk_android/vka_tex.c`, `android/app/src/main/java/dev/nxnative/android/MaliSmx930.java`. The patcher is idempotent and fails closed if known source anchors are absent.

## Reproduction and safety

For future tests in the **same installed APK**, preserve caches and use:

```text
DM_MOVIE_SKIP=1
DM_VK_PREWARM=0
DM_VK_SLOT_POOL=0
```

On a new DrawOpt APK, import the *existing* exported pack rather than retranslating 42,848 shaders. Keep v0.12.1 installed. New package IDs isolate driver cache and signatures; **the Vulkan pipeline cache is not transferred by pack export**. Native APK compilation does not imply Android process safety or FPS gains. Record real `ApplicationExitInfo`, `lmkd`, or tombstone if another Android kill occurs.

## Go/no-go

1. Native Android build passes and expected ARM64 library is packaged.
2. Device successfully starts, imports prepared shaders, skips video, draws 3D. Cache hit percentage and PT2 breakdown are logged.
3. 10-minute stability and at least 5-minute warm gameplay before claiming any FPS increase; no visual corruption or regression in audio.

This patch addresses limited, auditable parts of the measured hot path. A future memory lifetime audit may be required if the current **actively used** images, rather than stale cache entries, dominate the scene spike.
