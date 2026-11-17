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
