# Banana Native SM-X930 SoftGuard v0.24 — action ledger
Date: 2026-11-18 | Branch: `banana-mali-g925-20261117` | Repository: `kairushinjuu/Test-jed`

## Recovered baseline and diagnostic evidence
- Source: full v0.18 source checkpoint, extracted and reviewed locally; later production changes recovered from GitHub source patchers v0.19–v0.23. No source was restarted or replaced wholesale.
- Hardware: Samsung SM-X930, 11.24 GiB physical RAM, Android 17 API 37, Mali-G925 Immortalis MC12, PanVK faux123 v1.1.8. Driver reports Vulkan sparse binding/residency unavailable and max single allocation 4095 MiB.
- Earlier confirmed Android v0.20 foreground `LOW_MEMORY` process exit at 3.7 GiB RSS. v0.21–v0.23 logs consistently show 2.4–3.0 GiB Vulkan allocations, 4.2 GiB highest sampled process swap in shader-only fileback variants, and guest 6.20 GiB heap plus 2.74 GiB aliased virtual pages. Do not sum host Vulkan, guest charge, RSS, and swap without accounting for overlap.
- v0.23 reported 8 GiB caused reproducible early SIGSEGV `main+0xf942ac`, address `0x440`, whereas explicit 9 GiB report restored the later image-allocation failure. The patch restores `DM_APP_POOL_MB=9216`.
- The 12288x12288 D16_UNORM GPU-written image (serial 6393) occupies 297 MiB; source `pool_fit=0`. Driver sparse image support is absent: neither dropping nor aliasing it arbitrarily is safe.
- v0.22 8-frame working set ~1176/1221 MiB images: naive eviction upper bound ~45 MiB; not a meaningful gigabyte fix. ~40k VMAs / 65530 is not a hard map ceiling. v0.19 file-backed span ~3003 MiB but *nonzero copied data* ~558 MiB, v0.22 shader-only ~341 MiB, so 3 GiB of file span does not imply 3 GiB physical savings.
- v0.22 images by format: ASTC 228 MiB, BCn 300 MiB, other 653 MiB, GPU-written 555 MiB (GPU-written overlaps the other categories). Existing vka_soft.h algorithm omits one finest mip only for eligible large packaged compressed 2D images and hardens them on a required copy. Idealized upper bound = 75%*(228+300)=396 MiB, **not a forecast**: actual eligible texture data not provided by logs.

## Extensive static and host validation before compilation
- Source audited: `dm/host/hle_svc.c` (real APP_POOL/map limit vs report-only total), `dm/gfx/vk_android/vka_mem.c` (placed mapping/file backing), `vka_fileback.h`, `vka_tex.c` (image duplicate backing, GPU ownership, soft hardening), `vka_imgmem.c`, `vka_soft.h`, `vka_texlimit.h`.
- 12 existing production-source tests compiled and executed with Clang/ASan/UBSan and passed: `t_android_fileback`, `t_android_soft`, `t_android_texlimit`, `t_android_zshare`, `t_android_livemap`, `t_android_smap`, `t_android_mapbudget`, `t_android_gmem`, `t_android_poolslot`, `t_android_imgmem`, `t_android_lowram`, `t_android_place`.
- Added 250,000 deterministic synthetic cases against actual `vka_soft.h`: 46,275 allowed and 203,725 rejected, every accepted mip-view remap within range. ASan/UBSan passed; nominal BC7 2048x1024 mip-chain level-0 proportion 75.00%.
- `t_svc_memory` Android ARM64 production test cannot compile on this x86_64 host because of platform-specific `asm/sigcontext.h`, `process_vm_readv` and `MINCORE_INCORE` declarations: host portability issue, not a proven Android failure.
- `t_android_texown` functional tests pass with LSan disabled but its test harness retains ~8 KiB hashmap at process exit; not evidence of runtime leak. Documented rather than silently ignored.
- Local analysis archive: `BananaNative_v024_Static_Audit.zip` (report, CSV/JSON derived from five available dated logs, extraction program, test results and simulation). Persisted at `https://drive.google.com/file/d/16kvcPp7otkQpkgQNSo5qqo9wRk8oYuTm/view`. Private raw log files were NOT pushed to GitHub.

## v0.24 implementation and CI
1. Source patch `banana/smx930/softguard/apply_softguard.py`, commit `440694eacbd799a908992cb003c5af74c74bd17e`. This applies after the v0.23 script in the existing chain, restores reported pool 9216 MiB, enables `DM_VK_TEX_SOFT=1` and `DM_VK_TEX_SOFT_LEVELS=1` only for this tablet/title. All prior restrictions remain, including file backing shader-only and bounded Vulkan staging. Explicit Advanced overrides still win.
2. Reproducible source header stress test `banana/smx930/softguard/t_v024_policy.c`, commit `5e72a04506a18c609d87882fbbce4ec4459df08f`, tests actual source policy under ASan/UBSan.
3. New isolated CI workflow `.github/workflows/smx930-softguard-ci.yml`, commit `f8bcfea675cf71eedfa2a7fbdabdd19f033b19cd`; added all 12 host tests and 250k simulations **before** native Android link.
4. Verified GitHub Actions `https://github.com/kairushinjuu/Test-jed/actions/runs/44291684356`: `validate SUCCESS` and `build SUCCESS`. Full Gradle native ARM64 build `BUILD SUCCESSFUL in 1m 29s`.
5. GitHub artifact `banana-native-smx930-softguard-build-v024`, ID `14420969678` (ephemeral 3-day retention). Downloaded ZIP and extracted real APK. ZIP CRC intact; APK archive valid; binary manifest `dev.nxnative.android.malig925softguard`, version `0.3.40-mali-v0.24.0`; 2 DEX files; 11 arm64 libraries, including `libnxhost_0400486024DEC000.so`; APK v2 signing-block magic present. Full cryptographic `apksigner verify` not available locally; do not overstate as independently verified.
6. Verified APK file `BananaNative_SM-X930_SoftGuard_v0.24.0.apk`, size **31,497,075 bytes**, SHA-256 **f38c9e5c47c9188e1733806a15e8ff00343bd40665f9b1e80ab4dcc225acad8b**, matching artifact's sha256 manifest.
7. Persisted APK to Google Drive, read back metadata: `https://drive.google.com/file/d/1L3miM-yRPHkS0YV9x75LNr0SPpYaPL1M/view`.

## Device test and acceptance criteria
- User still must test on physical G925; neither host simulation nor GitHub CI can replicate PanVK and Android LMKD or prove gameplay.
- Install APK (isolated package) and import own game/shader data as necessary. Do not delete prior APKs or saves. No copyrighted assets included.
- On launch check `DM_APP_POOL_MB=9216`, `DM_VK_TEX_SOFT=1`, and logs containing `soft texture serial` and `soft textures: ... MiB ... left out`. Capture whether copy operations cause textures to become whole again and whether actual saved MiB exceeds ~200 MiB.
- Compare with v0.23 **with 9 GiB override** and same scene: reached frame, exact image cache/working set, swap, system memory, and Android ApplicationExitInfo. Only repeated successful scene traversal without memory kill counts as a fix.
- To A/B toggle in the same v0.24 app: set `DM_VK_TEX_SOFT=0` in Advanced/env, restart, compare. Do not alter guest pool, GPU image dimensions or use unverified overrides.
- If savings are small or OOM continues, the next effort must investigate real guest/Vulkan duplicate storage and GPU-written render targets, not repeat cache/staging parameter changes.

## Remaining open issues
- No full device-specific Vulkan shader execution simulation can be performed in Linux x86_64 without G925/PanVK or the player's private game data.
- Driver memory may include internal shadows beyond VkMemory allocation statistics; Android PSS and VkHeap allocations are not directly additive. Actual device evidence is necessary.
- The 9 GiB guest pool plus physical 11.24 GiB RAM and unrecoverable GPU allocations may exceed feasible resident headroom without substantial ownership architecture changes.
