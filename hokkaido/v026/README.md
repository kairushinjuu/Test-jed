# Hokkaido v0.26 — Ocarina opening cinematic skip (experimental)

Base: Hokkaido `feb08ad9ff87714b31219ad01b4bfbd6c8a69056`, plus exact Hokkaido v0.25 cumulative patch, plus `patches/hokkaido-v026-intro.patch`.

## Motivation and correct API
Hokkaido's own NX2 video decoder (`core/hle/service/nx2_gsv.h`) emits a frame via output image, GPU syncpoint, output-ready event, and `GetOutputInfo` EOS flag. Skipping shaders, suppressing rendered movie frames, or bypassing only MediaCodec could hang the guest. This patch queues exactly one synthetic EOS in the existing decoded-frame queue; the unmodified output pipeline then returns it to the guest with an actual signalled syncpoint. It does **not** patch the ROM, affect the embedded Banana Native engine, or inject a save state.

## Scope
Opt-in `HOKKAIDO_OOT_SKIP_INTRO=1`, only title `0400486024DEC000`, first decoder `video/av1` or `video/av01*`, once per process; later movies normally decode. On Stop/Flush current session resumes normal decoding. `0` or absence means no change.

**Limit:** The game might not advance after an early synthetic EOS: no device test has established the guest's movie state machine or audio dependencies. This is an experiment, not a proven skip. There is no guarantee that the first AV1 stream on all game versions is the title intro.

## Enabling before launch
For the isolated debug build (package `dev.lichii.android.lowramv026`), put these lines in its `Android/data/dev.lichii.android.lowramv026/files/env.txt` file:

```
HOKKAIDO_OOT_SKIP_INTRO=1
HOKKAIDO_VRAM_DIAG=1
HOKKAIDO_BUDGET_HYSTERESIS=1
EDEN_NX2_VDEC_TRACE=1
```

The Android JNI loader (`android_env_file.cpp`) reads this on app startup. Do not set `DM_MOVIE_SKIP` for Hokkaido's own engine: that only affects the embedded Banana Native engine. Remove the skip line or set `HOKKAIDO_OOT_SKIP_INTRO=0` to A/B compare. The build is isolated from v0.25; it does not migrate your game data automatically.

## Host validation
```
clang++ -std=c++20 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer -I source/src tests/t_intro_skip.cpp -o /tmp/t_intro_skip
ASAN_OPTIONS=detect_leaks=1 /tmp/t_intro_skip
```
The tests exercise source-accurate policy, not all IPC service logic or game state. The APK must pass the Android native build and a physical device test.
