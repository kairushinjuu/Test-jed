# SM-X930 BurstOpt v0.17 (experimental)

Source: pinned BananaNative e6b6f0d07a + Mali v0.12.1 patches + DrawOpt v0.16 + bounded burst pressure refresh.

Changes in dm/gfx/vk_android/vka_tex.c:
- Recompute image-memory budget on within-frame +128 MiB image growth, not only after 60 frames (15 when PSI-pressed). This matters when 320 images load in a single frame. Explicit fixed image-budget mode preserves old behavior.
- Do not corrupt the candidate array on `realloc` failure under low memory. Keep old pointer and images.
- Existing GPU ownership, working-set, fence holds, render target behavior and eviction priorities unchanged.

Environment: `DM_VK_IMG_BURST_REFRESH_MB=128` default; `=0` disables only the new rule; 1..4096 sets threshold (MiB). Unsupported values behave as off.

Limit: The 218k major page faults and cold PSO compilation are NOT fixed by this patch; it changes budget sampling only. GPU-heavy live images may be non-evictable for correctness. No real device FPS or memory improvements are established.

APK signing: new isolated `dev.nxnative.android.malig925burst` because GitHub build signer differs from installed v0.16. Keep v0.16; migrate prepared shaders through Game → Storage → Export pack / Import pack. Avoid unnecessary reinstall or data clear. New app has independent cold PanVK driver cache.

For a first fast-scene run use `DM_MOVIE_SKIP=1`, `DM_VK_PREWARM=0`, `DM_VK_SLOT_POOL=0`, `DM_VK_DRAW_FAST_SCAN=1`, `DM_VK_IMG_BURST_REFRESH_MB=128` and the same PanVK driver. For isolated A/B change ONLY last line to `=0`. Future separate experiment: `DM_MEM_FILEBACK_KINDS=shader` removes large texture-pool file backing, trading potentially fewer flash faults for higher anonymous memory pressure; do not treat it as an established improvement.

### Release proof (CI)
- Successful GitHub Actions: https://github.com/kairushinjuu/Test-jed/actions/runs/44067208149
- APK SHA-256: `81122d5499d282b97fcecf1f906b90aa481dc3e64d61b00091070d5254a5e121`
- Native `libnxhost_0400486024DEC000.so` and switch string embedded; new application ID `dev.nxnative.android.malig925burst`. APK v2 signing block present.
- No physical device validation yet. The previous 218,802 major page faults/3 frames are observational baseline, not a measured v0.17 improvement.
