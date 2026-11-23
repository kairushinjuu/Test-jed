# Hokkaido v0.25 — append-only action ledger
2026-11-23 JST. Work is continued from the prior Hokkaido security-audit and low-RAM package (no restart).

001. Inspected pre-existing `/mnt/data/Hokkaido_Source_feb08ad9.zip`, previous `Hokkaido_Safety_Audit_LowRAM_FINAL_20261123.zip` and extracted source/ledger in `/mnt/data/hokkaido_audit/`.
002. Audited Hokkaido `vulkan_device.cpp` GetDeviceMemoryUsage/GetDeviceMemorySlack/GetDeviceMemoryBudget, `vulkan_memory_allocator.cpp` VMA stats, `texture_cache.h` GC and runtime, `texture_cache_base.h` cache state, and memory report interfaces.
003. Determined VMA block slack and GPU-fence-retired objects are already accounted for in the current Hokkaido cache and driver. Rejected unsafe blind VMA defragmentation and duplicate governor approaches.
004. Compared Triforce/Linux `vram_compact.h`, `vram_pressure.h`, NX2navi `mem_budget.h/.c`, ReLink pipeline cache, and desktop Lichii `eviction_age.h` (existing `RetentionBudget` unreferenced in production).
005. Copied previously audited source to `/mnt/data/Hokkaido_v025/source` for a clean stage, preserving pristine 29 MB archive.
006. Implemented per-instance `held_device_budget` and opt-in `HOKKAIDO_BUDGET_HYSTERESIS=1` using the source-tested Lichii retention policy for cache thresholds only.
007. Implemented opt-in `HOKKAIDO_VRAM_DIAG=1` metrics every 120 frames: driver usage, budget, main-heap VMA slack, cache-accounted bytes, sentenced objects and allocator-pressure counters.
008. Ran `clang++ -std=c++20 -fsanitize=address,undefined` over 250,000 source-level budget and eviction cases; PASS (10,305 immediate drops, 239,430 bounded rises); verified rapid 11→8→10 GiB budgets.
009. Replayed earlier v0.24 source patch and source security inventory on the pristine verified ZIP; pressure tests PASS; scanner heuristic counts recorded in earlier audit.
010. Added 3-unit-test VRAM log parser and demonstrated correct missing-data handling and sample aggregation; PASS.
011. Constructed cumulative v0.24+v0.25 unified patch against pristine pinned source, checked with GNU patch `--fuzz=0` and compared all five resulting source files byte-for-byte; PASS. SHA-256 of patch: `9399076fc0625fc023fbc525648b04c7c67230b632e69d38e52c15197174b9c3`.
012. Uploaded patch and budget test to persistent Library `/Development/Hokkaido-v025/`, then committed exact text to private `kairushinjuu/Test-jed` branch `banana-mali-g925-20261117`; normalized missing trailing newlines.
013. Created `.github/workflows/hokkaido-v025-android.yml` commit `e2f1cb7b84c0af912c150c1cb2984a7d0edc1c44`: pin source SHA, strict patch, separate APK package ID, sanitizer test, Android build and signature/archive gates.
014. Triggered Actions run `45110615213` at workflow creation. Its status must be queried before claiming an APK exists. No device installation.
015. Prepared engineering report, reproducible parser, source patch and present-state archive for persistent handoff.

022. Re-ran Clang ASan/UBSan budget/eviction 250,000-case test and three Python log-parser tests locally on 2026-11-23; all PASS. Both Actions runs 45110615213 and 45110800028 remain in the actual Android native compilation step; no verified APK yet.
023. Added rootless ADB capture script hokkaido/v025/capture_hokkaido_v025.sh (commit d360303ef13d60147468065354295fc6418bbcfb). Captures only local device telemetry (MemAvailable, SwapFree, PSI, per-app PSS, ApplicationExitInfo and app-PID logcat), no root and no automatic uploads. Bash syntax checks passed; not device-tested.
024. Reviewed Android native env.txt loader and verified it derives the isolated package name from /proc/self/cmdline and calls setenv before normal initialization; use files/env.txt for opt-in v0.25 flags.
