# SM-X930 Ocarina fast iteration: skip the opening movie

Date: 2026-11-17. Title `0400486024DEC000`, target `dev.nxnative.android.malig925mass` v0.12.1.

## No APK build or shader preparation required

In the game's **Performance > Advanced > Extra environment**, set:

```
DM_MOVIE_SKIP=1
DM_VK_PREWARM=0
DM_VK_SLOT_POOL=0
```

This preserves the no-prewarm setting and tests only command-pool-off relative to the previous device log, while enabling a *test-only* intro bypass.

## Evidence in existing compiled source

- `dm/host/hle_codec_video.c` declares `DM_MOVIE_SKIP`; `1` affects session decoders 2 and above and marks the fifth submitted packet as end-of-stream, then drops later packets until Stop/Flush. `all` affects *every* decoder and is not advised.
- `dm/games/0400486024DEC000/README.md` explicitly says the opening movie is on decoder 2 and later and `DM_MOVIE_SKIP=1` bypasses it, **but it has not been tested on the phone**.
- `docs/reference/movies.md`: non-console semantics; some game players abort if the host fabricates an early end-of-stream. Thus verify it reaches 3D correctly; remove `DM_MOVIE_SKIP=1` if it aborts.
- Verified byte strings `DM_MOVIE_SKIP`, `session decoder`, and `ends its stream` in the actual v0.12.1 OOT host `.so` inside the APK: **rebuild not necessary**.

## Fallback: use a legitimate save checkpoint

`dm/games/0400486024DEC000/README.md` describes a Kokiri Forest Autosave with `slot_00/progress.sav` and `slot_00/caption.sav`. A save *created by the user's own copy of the game* may be backed up and loaded from the game's title menu to avoid replaying New Game's movie. The save files were not present in the source snapshot, and none were supplied by the user, so do not manufacture one or claim we imported it. A public third-party save may differ by game version; do not overwrite existing progress.

## Keep data

Do not remove v0.8/v0.12.1 or wipe `saves`, `packs`, `temp`/PanVK cache. Hold same PanVK faux123 v1.1.8, game and graphics configuration. If skip succeeds, compare post-intro FPS and process termination with previous 15:35 log, not movie FPS. Keep VMAs/audio/compute encoder instrumentation; no claim of 50 FPS improvement without new device measurements.
