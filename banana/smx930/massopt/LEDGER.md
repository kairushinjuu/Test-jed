# SM-X930 Mali-G925 optimization ledger — v0.12 experiment

2026-11-17 — recovered exact complete v0.8 modified source from mounted prior-artifact ZIP. Extracted to isolated `/mnt/data/smx930_massopt/BananaNative-source` (no customer game data).

Confirmed bottlenecks from supplied 13:35, 14:03 and 14:23 tablet logs: ~6 Vulkan submits/frame, 9.8–10.3 ms CPU submit cost, >1.2 s fence stalls and AAudio starvation during 30-FPS intro; first 3D scene had 72 new pipelines/24.6 s cold compilation, 3.1 GiB tracked allocations, and 26k major page faults. Real 50-FPS gameplay remains unverified.

Read Arm Mali Vulkan optimization guidelines and current PanVK beta release notes. Adopted correctness-first improvements with opt-out controls; no arbitrary barriers removed, image formats changed, or mesh draws skipped.

Implemented pinned v0.8→v0.12 source patcher, checked exact source anchors, applied to extracted source. Includes:
- per-slot Vulkan command pools with reset-on-retirement; fallback to legacy pool if creation fails, opt-out `DM_VK_SLOT_POOL=0`, check before reuse;
- one-worker shader-pipeline prewarming from bundled OOT seed (cap 256), stopping new speculative work when MemAvailable below 3072 MiB; prompt save of slow pipeline cache results;
- bounded, opt-in Vulkan submit trace, printing driver call, queue-lock time and synchronization fields; off normally and capped at 2048 lines.

Pending: synthetic/source regression, GitHub CI native build and actual tablet validation. These are *hypotheses*, not measured FPS gains. Preserve original v0.8 and shader cache; new test APK gets a separate package ID.

Added portable pinned-source CI tests (6 pass), Java startup tests (pass) and a source-grounded README. Tests check command-pool reset only after slot fence, bounded memory-guarded prewarm, no deletion of host access barrier, and bounded trace. Native Android compile still pending.

After the first successful v0.12 native build, code review identified upstream reuse of command buffers even after a 6s GPU-fence timeout; per-slot pool resets would then be invalid. Added v0.12.1 Mali-only failure guards for unsuccessful fence/timeline retirement (retains upstream fallback when DM_VK_SLOT_POOL=0), a targeted seventh regression, and will rebuild. Existing v0.12 should be superseded for device tests.

## 2026-11-17 — reuse already prepared shaders across APKs
- Inspected source PackUi, PackZip, AppStorage, PackFind, Folders, BuildConfig shader chain and v0.8 device log. Old 42,848-shader, 695.6 MB lib is in app data (not APK), `shaders/v-19662e4c4a25/dmsh_vk.lib`; same chain expected in v0.12.1.
- Confirmed v0.8 Game → Storage → Export pack and v0.12.1 Game → Storage → Import pack (ZIP) copy and validate complete pack, including the built shader library; no shader retranslation. The export omits `shaders/layer` and the GPU driver's `DM_TEMP/vk_pipelines*.bin` native pipeline cache.
- Alternative future-proof single shared pack folder: export ZIP once, extract to public `Download/games/0400486024DEC000-work/android-pack`, pick under game's Storage → Folders. Avoid simultaneous writers and retain old app until confirmed.
- Uploaded migration document to Google Drive ID 1EEvmY0EYaUI0OsVNp97-1_9JonU-1y5m, committed GitHub guide `banana/smx930/SHADER_MIGRATION.md`. Future CI needs a persistent signing key plus stable package ID for in-place updates to retain caches; never commit private keys.
