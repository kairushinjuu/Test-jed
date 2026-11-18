# SM-X930 GuestBudget v0.23 — action ledger (2026-11-18)

## Baseline
- Private project branch: `kairushinjuu/Test-jed@banana-mali-g925-20261117`.
- Existing packages v0.19–v0.22 preserved. v0.23 uses isolated application ID `dev.nxnative.android.malig925guestbudget`.
- v0.22 actual game log `0400486024DEC000-20261118-190604.log`: guest heap 6.20 GiB, aliased guest pages 2.74 GiB, swap sampled 4178 MiB, RSS 206 MiB in latest sample, 1005 MiB dedicated Vulkan image allocations, 1221 MiB image cache total, 297 MiB GPU-written render target, 40237 process mappings. Latest tracked Vulkan sum 2641 MiB; the values have overlapping accounting and should not be naively summed.
- v0.22 returned MapPhysicalMemory ResultLimitReached to guest at the REAL 9 GiB pool limit; this is intentional protection and not evidence of a host malloc failure. The digest describes OOM, but a v0.22 Android process-specific ApplicationExitInfo is not attached.

## v0.23 rationale
- Recovered and inspected `dm/host/hle_svc.c` from the original v0.17 handover and v0.22 runtime profiles. The actual source has a `reported_total()` function that honors `DM_APP_POOL_MB` for SDK GetInfo memory sizing and automatically lifts the reported total back to the real app pool if the guest usage approaches the smaller reported figure. It does **not** change `APP_POOL`, `SetHeapSize`, or `MapPhysicalMemory` real hard bounds.
- Goal: test whether a lower initial memory report reduces the guest's cache of nominally free but still mapped pages and avoids the 4 GiB swap thrash. This is a *hypothesis*, not a proved fix. The guest could ignore the hint or automatically lift it.
- No live GPU images freed, no forced heap cap, no render target resize, no unverified BCn conversion or guest allocation limit removal.

## Implementation
1. Added `banana/smx930/guestbudget/apply_guestbudget.py` commit `f2b63bd88ab5b31e44749f355d522afde80239b6`.
2. It patches the final SM-X930 Java profile after v0.22 to add `DM_APP_POOL_MB=8192`, subject to existing user-specified environment overrides taking precedence.
3. It adds a bounded `[mem] v023 guest memory policy` diagnostic to `reported_total()` showing the requested, reported, and actual hard pool. This helps verify whether the SDK receives the smaller initial report. It also works when the SDK later lifts the total.
4. Added `.github/workflows/smx930-guestbudget-ci.yml` commit `48892fd5607cb0cb24dc136d0277bba10cdbb67c`, preserving v0.19 through v0.22 patch chain. Source patches are exact-match and fail closed. Java policy and host source guard checks added.
5. GitHub Actions `https://github.com/kairushinjuu/Test-jed/actions/runs/44287277626`: validate **SUCCESS**; native ARM64 APK build **SUCCESS**.
6. GitHub artifact `banana-native-smx930-guestbudget-build-v023`, ID `14418768550`, retention three days. Downloaded CI ZIP and extracted actual APK.
7. Verified CI archive CRC, APK ZIP integrity, two DEX, 11 arm64 shared libraries including `libnxhost_0400486024DEC000.so`, binary manifest contains package and version in UTF-16LE, APK Signature Block 42 marker; full `apksigner verify` not available in the local container but CI Gradle packaged the app successfully.
8. APK path `BananaNative_SM-X930_GuestBudget_v0.23.0.apk`, 31,497,079 bytes, SHA-256 `ebc67312a433d3e080004b2794c82f271f4fc2af7e12c9cb5cddf8a0e75bff3d`. Matched the hash inside CI artifact.
9. Uploaded APK to persistent Google Drive and read back metadata: `https://drive.google.com/file/d/1jh7h88vbkIFeLRV0OMi3N3OyRI0q_ImN/view`.
10. **No device test yet**. Do not claim the low-memory problem is fixed.

## Test and rollback
- Install APK normally / `adb install ~/storage/downloads/BananaNative_SM-X930_GuestBudget_v0.23.0.apk`. Package is isolated so older versions remain installed. Re-import game assets and shader pack if required; no copyrighted game data distributed.
- First run: default SM-X930 settings; verify `[mem] v023 guest memory policy: requested 8192 MiB, reported 8.00 GiB, hard pool 9.00 GiB`; check for a later `reported total lifted` line. If the game ignores the hint, call the experiment unsuccessful.
- Compare time / frame reached, peak or sampled RSS, PSS, swap, image count, app pool alias mapping, `MapPhysicalMemory` failures, and any Android LMK data against v0.22.
- To restore v0.22 behavior in v0.23, override `DM_APP_POOL_MB=9216` in Advanced/environment or use the separate v0.22 app. The true app pool remains 9 GiB.
- If the v0.23 memory report is automatically lifted early with no change in mapped/resident memory, do not continue tuning this knob. Next priority: trace exact live guest heap/alias ownership, lifetime and compression, then actual PanVK backing. Never drop a live mapping solely to make RAM usage appear lower.

## Safety/privacy
- This ledger includes no private device files, game dumps, shader pack content, or customer assets. It records only non-sensitive statistics and public-source patch metadata.
