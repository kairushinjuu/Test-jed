# SM-X930 StageGuard v0.22 — engineering ledger (2026-11-18)

## Baseline and objective
- Branch: `banana-mali-g925-20261117`; repository `kairushinjuu/Test-jed`.
- Preserve v0.19 OOMGuard, v0.20 MemGuard and v0.21 LiveGuard packages; v0.22 has isolated package ID `dev.nxnative.android.malig925stageguard`.
- v0.20 ApplicationExitInfo confirmed Android LOW_MEMORY kill in game (foreground importance 100, RSS 3.7 GB at exit).
- v0.21 log: peak sampled swap ~4.2 GiB; last tracked Vulkan ~2.46 GiB; 297 MiB GPU-written D16 image at 12288×12288; guest MapPhysicalMemory refusals; free 64 MiB image blocks none. Systemwide exit-info shows other apps killed for LOW_MEMORY around time of failure, but no v0.21 game exit record. Do not claim independent v0.21 LMK certainty.

## External research and key safety decision
- GitHub reports: EdenOptimized memory governor; Vivsi1/Eden-NS2-Android notes discuss ASTC image expansion; leefao/bcn_layer and wrapper discuss BCn alternatives; Lichii issue #96 reports pipeline build memory ballooning for the exact title, on a different device.
- Read actual Banana Native source (v0.3.40 checkpoint): native BC/ASTC VkFormats exist in vka_tex.c and already have image sharing/learned views; vka_dev.c has GPU-fence-retired staging blocks and upload batch throttling; vka_tex.c defers image freeing until GPU completion.
- The largest Ocarina allocations are *GPU-written depth/render targets*, not safely BCn-compressible textures. No blind BCn transcoder, guest pool-limit removal, unsafe gpu-image free, or render target shrinking.

## Implementation
- Source patch: `banana/smx930/stageguard/apply_stageguard.py` (commit `cc917ef24c34ca89d4fcfb8fc6b3797f9b782fef`).
- On Arm Mali vendor 0x13B5 only: default first-content upload batch 64 → 16 MiB; max staging in-flight 256 → 64 MiB; idle scratch cache 64 → 16 MiB. Explicit `DM_VK_UPLOAD_BATCH_MB`, `DM_VK_UPLOAD_INFLIGHT_MB`, `DM_VK_SCRATCH_IDLE_MB` still override; other vendors preserve upstream defaults.
- Keep all busy scratch blocks and live images unchanged, honoring GPU completion fences; allow requests larger than cap (the cap concerns in-flight residency, not a fixed maximum request size).
- Add bounded per-burst `v022 image formats` log by categorizing existing `vka_img` VkFormat and requested memory into ASTC, BCn, other, and GPU-written. Reads under existing g_tmu lock and does NOT re-lock. Counts may overlap; these are Vulkan allocations, not physical RSS or driver-internal shadows.

## CI and tests
- Workflow `.github/workflows/smx930-stageguard-ci.yml`, pipeline patch chain v0.8 → v0.21 → v0.22.
- Initial workflow commit `95c6946fc79fd1b5b0a6e7a6ee4d12bb3f9c2eb6`: source-order test failed (v0.22 attempted before v0.21 instrumentation was inserted). No APK from that run.
- Fixed workflow patch order `a330ecaa17b46baa15db20b34e6459328d30ef77` and reran.
- Successful GitHub Actions run: `https://github.com/kairushinjuu/Test-jed/actions/runs/44280074779`; validate and Android native build both SUCCESS.
- Artifact `banana-native-smx930-stageguard-build-v022` ID `14416372687` (GitHub Actions retention three days).
- Verified archive CRC, APK ZIP integrity, `AndroidManifest.xml`, DEX, 11 arm64 libraries including `libnxhost_0400486024DEC000.so`, APK v2/v3 signing block signature marker, embedded version and package string. Full Android platform signature verification on tablet not yet run.
- Final APK size 31,497,079 bytes. SHA-256 `cc65375dfabd716670e565473c1e835c5b02d104f5a702086492c16b5867c057`.
- Durable Google Drive APK `https://drive.google.com/file/d/1namEdaLMWoirueQQ-7N_nsVHgqnyJGoT/view`.
- No physical-device run yet and NO claim that the OOM has been solved.

## Next A/B test on SM-X930
1. Install `BananaNative_SM-X930_StageGuard_v0.22.0.apk` as new package. Import game/shader pack without clearing older version.
2. In one test launch with default profile, capture timestamped game log and `adb shell dumpsys activity exit-info dev.nxnative.android.malig925stageguard` quickly after any crash.
3. Look for `v022 image formats`, `v021 allocation breakdown`, `oomguard residency`, `memory: placed pools`, GPU driver name, `MapPhysicalMemory refused`, and upload batch wait statistics.
4. Compare equivalent frame/scene and peak observed memory against v0.21. If memory unchanged or crash persists, do not keep tuning staging. Investigate the 1 GiB+ dedicated GPU-written images and duplicate format image allocations with exact lifetimes.
5. For rollback, use v0.21 or set the three explicit environment variables to 64, 256, and 64 respectively. Other builds remain installed.

## Notes
- Software patch and CI logs are public in the existing repository; never publish game dumps, private device files, sensitive logs or game assets.
- Driver BC=1 does not prove compressed image physical residency; no claim of Mali BCn shadow reduction without measuring actual driver.
