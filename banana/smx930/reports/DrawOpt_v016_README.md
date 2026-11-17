# Banana Native SM-X930 DrawOpt v0.16.0

## What was implemented

A narrow, opt-out optimization in `dm/gfx/vk_android/vka_draw.c` builds compact per-draw indices for texture/image descriptors and buffer textures, plus stage write flags, while the Vulkan binding walker processes current guest bindings. `make_images` traverses those indices instead of every non-texture descriptor on each dry and wet scan. `draw_writes` uses the current draw's write flags. This does **not** cache Vulkan views, pending texture state, shader/resource bindings or guest memory between draws. Image pending checks, texture refresh calls, render-pass transitions, barriers, and per-stage image-then-buffer order remain in place. `DM_VK_DRAW_FAST_SCAN=0` returns to the original full-loop implementation.

### Limits

This is an engineering hypothesis supported by source-level invariants, not a measured FPS increase. It does not yet fix the peak GPU memory footprint or Android termination. Neither reliable gameplay FPS nor 50 FPS performance is established. Test on actual Samsung Tab S11 Ultra with PanVK faux123 v1.1.8.

## Install without touching v0.12.1

Because the original v0.12.1 APK's signing key is unavailable to the CI builder, the new build has a **different application ID**, `dev.nxnative.android.malig925drawopt`; installing over `dev.nxnative.android.malig925mass` would fail signature checks. Install the new APK side by side. Do not clear the old app data.

Transfer the prepared shader library (42,848 shaders) from the old app: open the existing MassOpt v0.12.1 app, Game → Storage → Export pack. In the DrawOpt app, Game → Storage → Import pack, choose that ZIP (or a prepared shared `android-pack/` folder with `pack.tsv` + `shaders/`). This avoids retranslating shaders. The device-driver Vulkan pipeline cache in the old app's private `temp` path does **not** migrate with the shader pack; initial new pipeline compilation may be slow. Select PanVK faux123 v1.1.8 in the new app. Do not uninstall v0.12.1 until the new build is verified.

Recommended fast reproduction via Game → Performance → Advanced → Extra environment:

```
DM_MOVIE_SKIP=1
DM_VK_PREWARM=0
DM_VK_SLOT_POOL=0
DM_VK_DRAW_FAST_SCAN=1
```

For an A/B test of **only** the new optimization, change the last line to `DM_VK_DRAW_FAST_SCAN=0`, preserving all other settings and imported shaders.

## Provenance

Source branch `kairushinjuu/Test-jed`, `banana-mali-g925-20261117`, patch `banana/smx930/drawopt/apply_drawopt.py`; pinned `BananaNative e6b6f0d07a` with v0.12.1 patches applied before DrawOpt. Four local regression tests passed. CI native compilation and final APK verification documented separately in the ledger. No copyrighted game content or prepared shaders are distributed.
