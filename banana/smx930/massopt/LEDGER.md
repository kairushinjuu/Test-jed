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
