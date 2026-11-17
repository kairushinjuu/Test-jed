# SM-X930 Mali lab action ledger

2026-11-17 baseline: carried forward v0.5 Mali fork, official pinned source, faux123 driver success and user device logs. Source and logs local in prior workspace; no user game assets included here.

- Inspected current source (`GameActivity.java`, `vka_pso.c`, `vka_lowram.h`, `vka_texlimit.h`, title `game.tsv`, FPS frame-step controller) and prior logs. Found 60-Hz whole-vsync step policy; no direct evidence of gameplay FPS after movie.
- Consulted Arm/Khronos recommendations: tile-based GPU bandwidth, load/store ops, specific Vulkan sync barriers, Mali memory limits. No unverified renderer-level substitutions applied.
- Wrote stdlib-only analyzer separating intro/post-intro, respecting absent data. Parsed 1,710-line faux123 log: swapchain 1 success, median intro 30.0 FPS, 0 post-intro FPS samples, 2,491 MiB peak tracked Vulkan allocations, 1,874 MiB smallest logged MemAvailable, 33,920 memory maps, 17,700ms slow pipeline compile. Digested OOM is suspected, not proven by direct LMKD lines.
- Added strict A/B comparator, synthetic fixtures and 10 local Python tests; all passed.
- Added deterministic `MaliSmx930.java` startup defaults and standalone JVM policy tests; passed. Scoped to model SM-X930, title 0400486024DEC000, and user overrides retained.
- Safe anchor-patcher first refused mismatching whitespace; corrected and tested successful patch and dry run. No native image-format/mesh/render-pass semantics changed.
- Added read-only ADB collector for 600 s sample, model checked, battery/thermal/meminfo/logcat; no root.
- Added baseline/stability/balanced/quality env profiles and acceptance/quality gates; no shader cache deletion.
- Pending GitHub CI integration, cloud Android compilation, and physical-device verification.

## 2026-11-17 12:14 JST — v0.7 preparation error
- User image showed `ModuleNotFoundError: No module named 'pack_dump' (shader_split.py:3704)` at 6% / 42,848 shaders while preparing Ocarina of Time in the lab app.
- Opened full upstream+patched source ZIP and inspected v0.7 APK. `assets/pack/tools.zip` contains both `dm/gfx/tools/shader_split.py` and `scripts/pack_dump.py`; the problem is not an omitted module.
- Found `shader_split.py:3703` inserts `../../scripts` relative to `dm/gfx/tools`, erroneously resolving to `dm/scripts`; corrected to `../../../scripts`, resolving to package-root `scripts`.
- Added exact-anchor fail-closed patch `source_patch/fix_pack_dump_import.py` and regression `tests/test_pack_dump_import.py`; full local Python regression suite passes (13 tests); confirmed a corrected real v0.7 tools.zip import resolves `pack_dump`.
- Next: integrate with CI, build/verify v0.8, upload APK and checkpoints; do not discard previous v0.5 shader cache or user game data.

## 2026-11-17 13:39 JST — v0.8 on-device intro log follow-up

- Identified user-uploaded private Drive log `nxnative log 0400486024DEC000-20261117-133558.log` (size 140625 bytes), fetched it through the authenticated Drive connector and decoded with UTF-8 replacement for one malformed sequence.
- Verified v0.8 app, SM-X930, PanVK faux123 v1.1.8, full 42848-shader library, successful swapchain, user-initiated stop. No confirmed gameplay FPS, no observed LMKD.
- Parsed 837 lines: 1731 on-screen, 94 dropped (5.15%); 101 AAudio underruns / 375 ms zero fill; median per-window queue-submit CPU 9.8 ms/frame, GPU busy 2.2 ms; worst 1364.4 ms frame, GPU fences 1330.8 ms; no current PSI pressure.
- Inspected pinned v0.8 sources `dm/host/hle_audio.c`, `hle_codec_video.c`, `dm/gfx/vk_android/vka_dev.c`, `vka_exec.c`, `hle_fpslock.c`: existing experimental flags `DM_VK_TL_HOST`, `DM_DBG_AU_FRAMES`, `DM_CODEC_STATS`; their correct semantics checked in source.
- Upgraded stdlib log parser with AAudio/device callback, per-frame CPU queue-submit and GPU cost, longframe/fence cost, memory footprint, AV1 busy notices and environment toggles.
- Added independent introductory A/B profiles and 3 new tests. Full test suite: 16 passing. Added comparator guard against changing multiple perf variables simultaneously.
- Safest immediate follow-up: v0.8 unchanged, a baseline intro run with DM_CODEC_STATS=1, an isolated DM_VK_TL_HOST=1 run, then (separately) a 5760-frame AAudio buffer run; compare exported logs.
- Do not bake host timeline changes into the APK until measured; changing the app signature would require reinstallation and loss of newly prepared 695.6 MB shader cache.
- Pending GitHub test-run and Drive backup (record tool results below).
- Completed 2026-11-17: uploaded `BananaNative_SM-X930_Intro_Audio_AB_Lab_v0.9.zip` and individual report/profiles/analyzer/tests to the existing Google Drive `SMX930_Lab` folder; each upload acknowledged success. ZIP SHA-256 `26c53f58193cbe25bc55089b880949698ba99e555f09b262da9f8dd503ab5d24`.
- Committed sanitized metrics/test updates and independent A/B profiles to GitHub isolated branch as commit `6d8fef5d9979f7cc08cb47902f94da0438bd19a5`. No private raw log or user game assets committed.
- Changed full APK compilation workflow to manual dispatch for this branch; added fast automatic log-analysis regression CI for tools and profiles. GitHub Actions run 44019795259 completed SUCCESS (all tests and no-private-raw-log check), URL https://github.com/kairushinjuu/Test-jed/actions/runs/44019795259.
- Retain current installed v0.8, PanVK faux123 v1.1.8 and 42,848-shader library. **No new APK** because the first optimization is a reversible existing Vulkan timeline mode, and rebuilding would need device reinstallation and shader repacking. A/B has not been run on hardware yet.

## 2026-11-17 — 14:03 crash follow-up (v0.10)

- Authenticated Drive search found the latest `0400486024DEC000-20261117-140307.log` (1843 lines, 429148 bytes) and its digest. Downloaded into the working container. The raw log is **not** included in the public repository or toolkit.
- Reproduced state v0.8 SM-X930 / Mali-G925 / faux123 1.1.8 with `DM_VK_TL_HOST=1` and `DM_CODEC_STATS=1`. Digest classifies OOM; no kernel kill record in the in-process log.
- Scene transition at frame 10343: 27.312 s stall, 72 new pipelines taking 24.577 s, 321.6 MB uploaded, 26078 major/1897258 minor faults. GPU time 70/115 ms p50/p90 in later scene sample, 4.8 FPS. Graphics allocations 1327 to 3130 MiB, images 73 to 1809 MiB. 565 AAudio underruns / 1645 ms inserted silence.
- Source audit: reserve is an image-cache policy, not a hard GPU-memory cap; fileback may add I/O; asynchronous workers and GPU timeline alternatives carry separate costs. No unverified renderer change made.
- Upgraded stdlib analyzer to report post-movie scene windows, pipeline creation, upload and fault metrics; fixed rounding of small drop ratios. Added three synthetic regression tests: 19 tests total passed.
- Created safe independent Recovery A (turn host timelines off) and Recovery B (one shader pipeline worker), plus a clearly labelled high-risk fileback candidate for later; **do not use the third yet**.
- Pending: GitHub publication of sanitized analyzer/tests, backup of v0.10 lab to Drive, next on-tablet comparison. No APK rebuild so shader cache and signing remain untouched.
- Added conservative `tools/compare_scene.py` (scene pressure only, does not call 50 FPS success) and four synthetic tests; updated normal `compare.py` to include fileback kind as a controlled variable. All **23 tests pass**. The recovery lab is packaged without raw logs.

- Found a regression in the old ADB sampler: it targeted the obsolete v0.5 package `dev.nxnative.android.malig925`; fixed to the actual v0.8 lab `dev.nxnative.android.malig925lab`, both main/:game PIDs, and added live filtered LMKD/AndroidRuntime logcat for independent evidence. Added 3 synthetic/static tests.


## 2026-11-17 14:23 JST — user terminated Test B early
- Located Drive log `nxnative log 0400486024DEC000-20261117-142334.log` (file ID 1SrN3ikjxxlHYZrg-8oEruOlzeIVv7wPe), fetched authenticated raw bytes and analyzed 901 lines. Raw log is private; do not commit to public GitHub.
- Confirmed effective `DM_VK_TL_HOST=0`, `DM_VK_PSO_ASYNC=1`, `DM_CODEC_STATS=1`. First environment line showing 2 is overridden by later Extra environment entry 1.
- Intro only: 138 AAudio underruns in 10,000 callbacks, 435 ms silence, median 10.3 ms queue-submit CPU / 2.2 ms GPU; 6 queue submissions per intro frame; worst 1,240.9 ms frame (1,209.1 ms GPU fence wait), no pipeline creation. The current user stopped normally. No intro end or 3D scene, so cannot infer crash recovery or FPS improvement.
- Compared older 13:35 introduction with 101 underruns in 8,000 callbacks, 375 ms silence, 9.8 ms median queue submit, 1,364.4 ms stall; effects small / runs temporally non-identical and two variables changed vs prior 14:03 crash run. No causal A/B ranking.
- Read v0.8 source `vka_dev.c`, `vka_exec.c`, and `hle_audio.c`: queue submissions are ordered through `submit_x`, often around guest synchronization; `DM_VK_CHUNK` is 600 draws (intro only ~2–5 per frame) and not expected to reduce six calls; audio buffer 3840 at 48 kHz = 80 ms; cache hits make async compiler changes irrelevant to intro.
- Next branch priority: instrument submit reasons and fence waits, then correctness-gated Mali-only batching; separately address the heavy-3D pipeline-memory problem. Avoid rebuild until concrete source fix.

- Refined comparison using real 13:35 log and v0.8 source: auto-probed GPU-signalled timeline in prior intro run, explicitly GPU-signalled in latest. `DM_VK_PSO_ASYNC=2 → 1` only reduced worker threads; both runs had `DM_VK_PSO_SLOTS=1`, so effective costly compiler concurrency remained 1. Earlier run had shader-cache misses, latest run 17 hits/0 misses, limiting attribution.
