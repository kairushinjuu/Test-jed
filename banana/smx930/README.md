# Banana Native — SM-X930 / Mali-G925 engineering lab

**Scope:** Samsung Galaxy Tab S11 Ultra `SM-X930`, Android 17 (API 37), GPU `Mali-G925-Immortalis MC12`, 11.2 GiB *OS-visible* RAM. Game under test: Zelda Ocarina of Time Switch 2 Edition (`0400486024DEC000`), user-owned content only.

**Objective:** stable *measured gameplay* **50 FPS** (20 ms per frame) with no obvious loss of textures, lighting, geometry, or shadow quality. This is a **target**, not an achieved result. The game's approximately 30-FPS intro/movie must never count against a gameplay target. A 60-Hz display and fixed-vsync game steps can make 50-FPS delivery uneven; don't force `DM_FPS_LIMIT=50` until timing behavior has been verified on-device. Judge pacing and audio synchronization, not an FPS counter alone.

## Current evidence (2026-11-17)

- Earlier PanVK 26.3.1: swapchain `VK_ERROR_INVALID_EXTERNAL_HANDLE` (-1000072003), black screen.
- faux123 PanVK v1.1.8: Vulkan swapchain **created (5 images)**, intro **played around 30 FPS**, AV1 decoder **ended normally**, post-intro black-screen blocker solved.
- faux123 session ended around the transition to gameplay. Launcher digest classified an Android memory kill, but **no independent LMKD tombstone was captured**. Rendered allocations climbed to **2,491 MiB**, including a **297 MiB 12288×12288 image**; ~33,920 virtual-memory mappings and a 17.7-second pipeline compile occurred. Available RAM once reached ~1,874 MiB; CPU and shader workload require staged measurements.
- **There is no reliable gameplay FPS number yet.** Never report a 50-FPS success from the cutscene data.

## Method: 1980s engineering discipline

1. **Count bytes and work.** Bounded pools, one expensive compilation at a time, no speculative allocations when memory is tight. Always measure resident memory, map count, GPU frame time and stalls.
2. **One independent change per run.** A/B with the *same* driver, same game build, same scene/resolution and warm-state, where possible. Driver changes require a new reference baseline.
3. **Do not drop correctness for benchmarks.** No automatic shader skipping, mesh hiding, forced half precision, unsafe barrier removal, or hard clipping of the game's 12K texture without identifying whether it is essential.
4. **The simplest workable renderer wins.** Optimize bandwidth on Mali's tile-based architecture only after captures identify the dominant cost. Arm recommends appropriate attachment load/store operations and specific synchronization; this fork must preserve guest-visible NVN semantics.
5. **Keep the system alive.** A stable 45-FPS game beats a 55-FPS demo that is killed by Android after the intro. Do not confuse protected virtual address space with committed physical RAM.

## Repository layout

- `source_patch/MaliSmx930.java` — game+device scoped startup defaults; pure Java, no render-thread work, all user switches still override it.
- `source_patch/apply_smx930.py` — exact-anchor safe source patch for the v0.3.40 Mali fork.
- `source_patch/MaliSmx930JvmTest.java` — pure-JVM tests, no Android emulator needed.
- `tools/analyze.py` — stdlib-only log analyzer, **intro vs gameplay** separation, statistics and conservative verdict.
- `tools/compare.py` — rejects non-comparable A/B logs and checks quality-relevant setting changes.
- `tools/collect-adb.sh` — read-only performance snapshot from exactly `SM-X930`, requires a connected PC with adb (no root).
- `profiles/` — copy into **Game settings → Advanced → Extra environment**. Do not paste comments beginning with `#`.
- `tests/` — synthetic log fixtures and regression tests (no user game files, private logs or copyrighted assets).
- `reports/` — baseline analysis derived from actual supplied logs.

## Start-to-finish experiment sequence

1. **Preserve the installed v0.8 and its completed 42,848-shader cache** (keep v0.5 as an older independent comparison). Record a reference run on faux123 v1.1.8 using the `40-intro-baseline.env` settings. Launch and collect the full exported log and digest. Test on battery >50%, unplugged, at a repeatable cool starting temperature, fixed screen brightness and unchanged resolution.
2. **First objective = survive the intro and save.** A log that reaches the gameplay area, remains responsive for 10 minutes and has no crash/tombstone earns a stability pass. Collect three such sessions; be consistent about intro skipping or using the same save point.
3. **Second objective = warm, comparable five-minute gameplay benchmark.** Log at least 10 distinct gameplay FPS observations. Treat 20 ms as the 50-FPS target. Acceptance: median ≥50 FPS, p10 ≥45 FPS, post-intro p99 display interval ≤40 ms and dropped frames ≤3%, with **no crash**. This is a project-specific engineering gate, not a guarantee of perfectly constant 50 FPS.
4. **Third objective = quality check.** Compare screenshots of the same camera position and scene at 540p performance then 720p balanced. Inspect text legibility, vegetation, shadows, LOD, motion, and missing geometry; don't accept broken visuals to win a few frames.
5. **Fourth objective = optimize the real bottleneck.** GPU-bound → tile bandwidth and shader register pressure; CPU-bound → replay/driver calls, scheduler, texture upload churn; memory-bound → bound compilation, image lifetime and actual resident working set. Reproduce before any native renderer modification.

## Commands (host PC with adb, or local Python for logs)

```bash
python3 -m unittest discover -s tests -v
javac -d /tmp/smx930-java source_patch/MaliSmx930.java source_patch/MaliSmx930JvmTest.java
java -cp /tmp/smx930-java dev.nxnative.android.MaliSmx930JvmTest
python3 tools/analyze.py game.log.txt --digest game.digest.txt --json run.json --md run.md
python3 tools/compare.py baseline.json candidate.json
DURATION=600 INTERVAL=5 bash tools/collect-adb.sh
```

`collect-adb.sh` checks model `SM-X930` before data collection and records only read-only device dumps. It does *not* access game assets or automatically submit logs to GitHub. It does not require elevated privileges; some measurements may be unavailable due to Android sandbox restrictions.

## Build, app data and signing

The GitHub Actions build assembles the pinned official `e6b6f0d07a` source + existing v0.5 Mali changes + `source_patch/`, plus the matching v0.3.40 native packing runtime. **No game data is included.** Android SDK 36, NDK 28.2.13676358, CMake 3.22.1 and JDK 17 are fetched in Actions.

The test package ID is `dev.nxnative.android.malig925lab` (separate from `dev.nxnative.android.malig925` v0.5), so the existing app/game cache remains untouched. Different CI runs use ephemeral debug signing keys; future builds under the *same* lab package ID may require uninstall/reinstall unless an independently secured persistent signing setup is adopted. Never publish a private signing key into a public repository.

**Limit:** CI can compile, lint, test profiles and analyze logs, but cannot test actual Mali frame pacing or quality without device execution. The remaining GPU experiments require the attached Tab S11 Ultra.

## 2026-11-17 13:35 SM-X930 v0.8 intro A/B campaign

The completed 42,848-shader library removed the previous preparation failure, but the current intro still has 101 AAudio underruns (375 ms inserted silence), 94 dropped presentation frames across seven observation windows, and a 1,364 ms GPU-fence stall. Shader work is not the recurring bottleneck: measured Vulkan CPU queue-submit cost is 9.8 ms/frame while the GPU reports ~2.2 ms busy. Full report: `reports/v08-20261117-133558.md`; machine-readable summary: `.json`.

To test without reinstalling the APK or losing shader caches, copy **one** of `profiles/40-intro-baseline.env`, `41-intro-host-timeline.env`, `42-intro-audio-buffer.env` into **Game settings → Advanced → Extra environment**. The timeline and audio profiles are alternative A/B experiments, **not simultaneous settings**. Driver and resolution should remain unchanged. `DM_CODEC_STATS=1` is diagnostic and common to all three.

Use `python3 tools/analyze.py <exported.log> --json run.json --md run.md` and compare matching experimental runs. The report never promotes 30 FPS movie data to 50 FPS gameplay success. No device credentials, game dump, or original user log should be committed to the public GitHub test repository.

## 2026-11-17 v0.10 scene-crash recovery

The 14:03:07 log identified a 27.3-second first-scene shader/fence stall and ~3.1 GiB tracked Vulkan allocations; the launcher classifies the abrupt termination as memory-related. See `reports/20261117-140307-timeline-crash.md`. The game log does not contain independent LMKD evidence.

`profiles/50-revert-host-timeline.env` returns to the previous GPU-signalled timeline mode without reinstalling. `51-single-background-compiler.env` is a **separate** one-worker PSO experiment for the next run. `52-shader-only-fileback-LATER.env` is **not recommended until memory is captured**, because avoiding file-backed texture storage increases RAM use. No changes to APK and no shader reprepare.

### Comparing crashes before 10 FPS observations

The original `tools/compare.py` intentionally refuses to rank FPS without ≥10 post-intro observations. For scene-start crashes, use `tools/compare_scene.py` instead: it compares controlled settings and side-by-side *observations* (fence wait, pipeline time, image memory, audio events), with no false FPS-success claim. Keep exact game build, driver, resolution and scene. The first comparison is timeline host on vs off; a later comparison can isolate `DM_VK_PSO_ASYNC=2` vs 1.

### Capturing an actual Android low-memory kill (optional ADB)

The log digest alone is insufficient to prove LMKD. The `tools/collect-adb.sh` capture now targets **`dev.nxnative.android.malig925lab`**, not the older v0.5 package. It records both the main and `:game` process memory, process pressure, thermal state, and a filtered live low-memory/abort logcat stream. It does not clear logs, reboot, touch game files, or collect the unfiltered private device log. Requires a connected ADB host, no root. Start this script immediately before playing and export the game's own log separately. Never upload raw logcat to public GitHub.
