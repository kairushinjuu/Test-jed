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
