# SM-X930 MemGuard v0.20 — 2026-11-18

## Baseline and build
- Branch: banana-mali-g925-20261117.
- Existing v0.19 OOMGuard CI is the starting point. All previous patchers run in the same order, followed by memguard/apply_memguard.py.
- Workflow: .github/workflows/smx930-memguard-ci.yml; run 44228887586.
- Isolated application ID: dev.nxnative.android.malig925memguard.
- Version: 0.3.40-mali-v0.20.0, version code 34200.
- APK output: banana-native-smx930-memguard-v0.20.0.apk.
- Source-patch tests: banana/smx930/memguard/test_memguard.py.

## Experiment: isolate file-backed textures
- DM_MEM_FILEBACK=1, DM_MEM_FILEBACK_KINDS=shader (texture is deliberately excluded).
- DM_VK_PREWARM=0, DM_VK_PSO_SLOTS=1 (v0.19 policy continues).
- DM_VK_PRUNE_MS=2: bound eviction budget by replay-thread elapsed time, not image count.
- DM_MOVIE_SKIP=1 for rapid crash reproduction.
- DM_VK_IMG_DIAG=5 (every 5 seconds) to observe pressure and eviction.
- DM_VK_IMG_RESERVE_MB=1536 remains unchanged from v0.19 to avoid changing two memory variables.
- Other SM-X930 defaults from existing source retained.
- User-provided Extra environment and env.txt retain normal precedence.

## Known pre-existing observations
- v0.18 ended via confirmed Android ApplicationExitInfo LOW_MEMORY / OOM KILL.
- v0.19 log terminated after frame ~1075; ~2973 MiB tracked Vulkan, ~1245 MiB images, and swap climbed toward 2590 MiB. v0.19 Android exit-reason needs confirmation.
- v0.19 logs reported DM_VK_DRAW_FAST_SCAN, DM_VK_IMG_BURST_REFRESH_MB and DM_MEM_FILEBACK_EVICT as unknown switches. Direct source contains implementations of the latter two: likely registry mismatch; do not infer absence of implementation solely from launcher validation. v0.20 does not add those switches to Extra environment.
- No claim that this fixes OOM until on-device test.

## Required validation and next action
- CI validation unit tests, native build, APK integrity, package ID and manifest checks.
- User installs APK and imports their own game/shader pack. Do not clear the older apps or shader caches.
- After crash, capture ApplicationExitInfo for package dev.nxnative.android.malig925memguard; record RSS, PSS, swap, GPU allocations, major faults and lmkd line.

## Rollback
- Leave v0.19 intact. Reinstall prior OOMGuard APK or launch old package.
- Never overwrite saved game data or delete shader pack.
