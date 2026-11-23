# EXP-002: v0.25 system-driver baseline

On 2026-11-23, SM-X930 (API 37) ran the existing v0.25 APK (SHA-256 `88f1b952616802ac172d6ff4b10a265a3fa5f1a3d295bcb373e99392621e9529`), Hokkaido engine, NCE, 0.5x resolution, and system Mali r49p1 driver. The scene-load memory limit remained Auto; opt-in v0.25 environment flags were absent. Main game build ID began `e0f3ccfa`. This is not a PanVK test.

The opening video and subsequent in-engine cutscene appeared, with visible rendering defects; interactive gameplay was not reached. Android lmkd reclaimed the foreground process under memory pressure, and ApplicationExitInfo classified the same process as LOW_MEMORY. Last app sample: PSS 6,672,912 KiB, RSS 5,778,061 KiB, swap PSS 1,031,522 KiB; MemAvailable was 690,068 KiB shortly afterward. Android reported GL mtrack 4,524,932 KiB in the app sample; do not add it to PSS or interpret it as a direct VMA allocation total.

The runtime repeatedly reported a compute storage buffer skipped at driver limit 32 and a compute descriptor count mismatch (expected 39, got 38). This is a separate suspected rendering issue; no causal link to the memory kill is established. The system Vulkan capability report contained no `VK_EXT_memory_budget` string. Source returns zero budget without that extension before entering the Android pressure-policy code. Verify actual emulator-instance capabilities and allocation ownership before changing policy.

The existing capture helper failed to collect MemAvailable on this device because remote shell argument quoting broke `grep`. The adjacent workspace copy runs the filter on the host; shell syntax and the filter were checked against the tablet. Its full capture workflow still needs a subsequent device run. Raw logs and screenshots are retained locally and excluded from this commit.

The v0.26 isolated APK from Actions run 45116306354 was independently verified (SHA-256 `9b6295853abb503ab8e5f9ee89ef770889fb3d90aaeee303c22d9c0549b911a1`, package `dev.lichii.android.lowramv026`, ARM64 host library present, debug v2 signature valid) and installed separately. Its intro-skip behavior has not been tested.
