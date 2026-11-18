# Banana Native SM-X930 LiveGuard v0.21 — action ledger (2026-11-18)

## Preserved baseline
- Private diagnostics: v0.18 Android ApplicationExitInfo LOW_MEMORY OOM KILL; v0.20 Android ApplicationExitInfo LOW_MEMORY, game PID 13508, foreground importance 100, 3.7 GB RSS at exit (not PSS).
- v0.20 log: `0400486024DEC000-20261118-152215.log`. Shader-only file-backing active, 2.74 GiB alias-map refusals while application pool was full, 297 MiB GPU image with guest backing, 40,331 maps, PSS/RSS falling while Swap rises to 2,873 MiB. These are separate accounting domains and must not be summed naively.
- Existing gameplay profile Switch 2 Ocarina of Time ID 0400486024DEC000, update 131072; preserve user ROMFS/shaders and prior APKs.
- Source pinned at Banana Native v0.3.40 plus previously tested local patch chain; do not discard v0.19/v0.20 changes.

## Work done
1. Read v0.21 source checkpoint and actual `dm/host/hle_svc.c`, `dm/gfx/vk_android/vka_tex.c`, and `vka_imgmem.c`; confirmed guest `MapPhysicalMemory` refusal is deliberate application-pool protection. Do not remove its limit.
2. Added `banana/smx930/liveguard/apply_liveguard.py` commit `0138847ea9b06d04f4a17b2c8baa774fd3d665af`: on G925 release completely empty 64 MiB image allocator blocks, rollback with `DM_VK_IMGMEM_KEEP_EMPTY=1`. Does not unbind or free live textures. Add bounded allocation logging and fuller guest memory accounting; never resize/release the 297 MiB render target without a proven lifetime.
3. Added `.github/workflows/smx930-liveguard-ci.yml` commit `2f05caf06cf5632d7dda0da24f1f29d052718aeb`. Existing patch chain through v0.20 runs first, v0.21 last. Source anchors are exact-match checks, fail closed.
4. CI `https://github.com/kairushinjuu/Test-jed/actions/runs/44256437776`: validate SUCCESS, Android native build SUCCESS. Artifact `banana-native-smx930-liveguard-build-v021` ID 14405338971.
5. Downloaded CI ZIP, extracted real signed APK, verified ZIP integrity, DEX, ARM64 libnxhost_0400486024DEC000.so, AndroidManifest containing `dev.nxnative.android.malig925liveguard`, version 0.3.40-mali-v0.21.0, signing block, APK SHA256 `fca05836f49b316b1034e874ec592ad20dc0e2e3f4cd85f8caccfc2b476826c4` (31,497,079 bytes).
6. Uploaded verified APK to Google Drive: `https://drive.google.com/file/d/1dEFXMu8AFCZn_MXcidjcblGKR6qUuWVr/view`. Created Drive folder `https://drive.google.com/drive/folders/1AqMm9rcavdwnCkiMGb-AuBLtCOiB5_sD` for future checkpoint.
7. Confirmed v0.21 package is distinct from v0.19 and v0.20. APK build is correct, physical-device launch and memory savings not yet measured. Avoid claiming an OOM fix.

## Next manual device test
- Install APK normally or `adb install ~/storage/downloads/BananaNative_SM-X930_LiveGuard_v0.21.0.apk`; source data/shader pack may need re-import into the isolated package.
- No extra environment overrides for baseline. Do not clear other APK caches.
- Reproduce first 3D scene, upload game log and `adb shell dumpsys activity exit-info dev.nxnative.android.malig925liveguard`.
- Look for `v021 image memory: empty 64 MiB block freed`, `v021 large image attribution`, `v021 allocation breakdown`, `v021 accounting`, and compare same phase with v0.20. If new block reclaim never triggers, it cannot provide significant RAM benefit and should not be advertised as a fix.
- Prioritize real memory lifetime and root cause; do not disable guest pool limit or prune live GPU images.

## Reproduction
`banana/smx930/liveguard/apply_liveguard.py` and workflow are stored in branch `banana-mali-g925-20261117`. CI artifact GitHub is ephemeral; Google Drive APK is durable. No background monitoring scheduled.
