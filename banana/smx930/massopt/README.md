# Banana Native SM-X930 Mali-G925 v0.12.1.1 experimental mass optimization

**Status:** source optimizations / build verification; NOT verified 50 FPS. Ocarina of Time Switch 2 Edition title `0400486024DEC000`. Experimental build is separate (`dev.nxnative.android.malig925mass`), so v0.8 and its prepared shader library are not overwritten.

## Why these changes

Three device bottlenecks were observed: six submissions/frame and ~10 ms of Vulkan driver queue-submit CPU overhead during the 30-FPS intro, 1.2–1.3-second fence stalls, and 24.6 seconds for 72 first-3D pipelines with image allocations rising above 3 GiB. This patch **does not eliminate** queue/fence stalls or the 70ms 3D GPU time; further profiling/driver work is required.

The biggest safe near-term wins may be **removing first-scene shader compilation from gameplay** and **reducing individual command-buffer reset overhead**. Neither gain has been measured yet.

## Changes

1. **Bounded one-thread Vulkan pipeline prewarming:** use the title's prewarm seed, up to 256 keys, at nice +10. Stop starting new speculative builds when `/proc/meminfo` MemAvailable is below 3072 MiB. Overrides: `DM_VK_PREWARM=0` off, `DM_VK_PREWARM_MAX=N`, `DM_VK_PREWARM_MALI_MIN_MB=N`.
2. **Per-completed-slot Vulkan command pools:** one pool per replay slot, reuse with `vkResetCommandPool` only after the slot's fence has completed; avoids `RESET_COMMAND_BUFFER_BIT` and per-command-buffer reset on Mali. Disable with `DM_VK_SLOT_POOL=0`. All other GPUs use the existing code path.
3. **Pipeline cache persistence:** `DM_VK_PCACHE_SAVE_SLOW_S=1`, separate per-driver cache, existing validation retained. Shader translation and visual features unchanged.
4. **Bounded GPU submit tracing:** `DM_VK_SUBMIT_TRACE=100` prints at most 100 queue-lock and driver timing records. Default zero to avoid log overhead; hard cap 2048. First pass identifies wait/signal/fence types, not precise guest event cause.

**Do not merge Vulkan submits or drop barriers blindly.** Guest NVN events, signal values, fence order, and GPU/host visibility must remain correct. Arm's Mali synchronization recommendations favor precise barriers and avoiding cache invalidations, not removing required synchronization.

## Build/run

After applying the existing pinned v0.8 Mali patch workflow from `banana-mali-g925-20261117`, execute:

```bash
python3 banana/smx930/massopt/apply_massopt.py source/banananative --check
python3 banana/smx930/massopt/apply_massopt.py source/banananative
SOURCE_ROOT=source/banananative python3 -m unittest discover -s banana/smx930/massopt -p 'test_massopt_ci.py' -v
```

CI uses Android SDK 36, NDK 28.2, Gradle and the matching 0.3.40 native packing tools. Original shader pack/game dump are **not** distributed. Target independent gameplay performance gate: median >=50 FPS, p10 >=45, p99 frame interval <=40ms, no crash for 10 min, no visual corruption. The 30-FPS movie must be assessed separately.

### Caution

Prewarm can *worsen* audio and intro pacing if it overlaps a busy scene. The Mali floor avoids starting new speculative jobs under low memory but cannot cancel an already-running Vulkan compile. The per-slot pool change is spec-valid on paper but unproven with this PanVK driver. Start with an isolated test app and preserve v0.8. An APK checksum and CI success do not imply GPU correctness or an FPS increase.

**v0.12.1 safety hardening:** On Mali slot-pool mode, do not reset a pool or recycle buffers after a command-slot GPU-fence timeout or a failed timeline retirement; abandon that frame instead of violating Vulkan command-buffer lifetime rules. This is particularly important for prior 6+ second stalls.
