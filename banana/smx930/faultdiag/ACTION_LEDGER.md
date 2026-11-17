# SM-X930 FaultDiag v0.18 action ledger — 2026-11-17

## Recovery
- Full v0.17 handover recovered from five authenticated Drive parts, exact SHA-256 ae0f70847927098b0a803ecdd985488a73d2e76d669e18c20191cea3d1e08769 and ZIP CRC PASS.
- Verified branch at 43772aaeb27cdd79a7386e2114d7784a267bc2d0 before changes. Reviewed mandatory handover, source, previous report and PRIVATE device logs locally (never committed).
- Existing v0.17 remains unplayable during demanding first 3D scene; 141,884 major faults across first 3 heavy frames; about 25 s cold PSO compile, LMKD not independently established.

## Code
- Inspected vka_mem.c and vka_fileback.h: vkfb_drop explicitly synchronizes and drops file-backed page cache. This can cause subsequent cold page reads, but not proven as crash root cause.
- Added reproducible patches/apply_faultdiag.py equivalent at banana/smx930/faultdiag/apply_faultdiag.py: default behavior unchanged; DM_MEM_FILEBACK_EVICT=0 optionally retains clean page cache, at risk of HIGHER RAM pressure/OOM, for controlled diagnostic only.
- Added bounded getrusage(RUSAGE_SELF) major/minor fault counts around conversions, sampled only on first 8 successful pools and every 64th, with explicit process-wide attribution limitation.
- Existing DrawOpt/BurstOpt 9 regressions PASS; new FaultDiag 3 regressions PASS; t_android_fileback.c compiled and PASS with default, EVICT=0 and EVICT=1.
- Initial local test errors due to legacy default source path fixed with environment overrides; patcher same-file staging and test anchor bugs fixed and retested.
- GitHub patcher commit 36098fb46531824cdc4ad81956540ec912ea3160; tests 8ab0a89a6e652ca48e9523f12e0a1858e35bff01; test path correction 016b1c7f1fb3ab4fb963144267f63191096df613.
- Dedicated v0.18 Android workflow committed at bb21482cb4b1835c679bbccae52065561b66697b. Isolated package malig925faultdiag because prior CI signer stability is NOT established; never replace installed v0.17 with a mismatched signature. Fresh app means cold driver PSO cache, so cross-package performance comparisons are confounded.
- Android native workflow run https://github.com/kairushinjuu/Test-jed/actions/runs/44080254917; final status should be verified before claims of native build success.

## Unverified / next
- No v0.18 tablet run or FPS evidence, no proven crash fix.
- Recheck CI build/artifact and signer; preserve existing app data, game dumps, 42,848 shader library and cached pipelines. Do not clear data or uninstall old apps.
- Next performance direction: true Android exit reason + memory pressure and frame-level file faults, then stable same-package signer and controlled A/B; separate the approximately 25-second cold PSO compiler stall from fault bursts.
