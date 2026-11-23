# Hokkaido v0.26 — append-only action ledger

Date: 2026-11-23. Branch: `kairushinjuu/Test-jed:banana-mali-g925-20261117`.

1. Preserved v0.25 source and memory policy; user requested skipping the Ocarina title intro in Hokkaido's own engine.
2. Read exact Hokkaido pinned source from `/mnt/data/Hokkaido_Source_feb08ad9.zip` and locally recovered v0.25 patched source, verifying `src/core/hle/service/nx2_gsv.h` matched pristine byte for byte.
3. Inspected `src/video_core/ocarina_movie.h`, `src/video_core/engines/kepler_compute.cpp`, `src/video_core/host1x/nx2_video_decoder.cpp`, and `src/core/hle/service/nx2_gsv.h`. Established that the existing `OcarinaMovie` shader bypass does NOT skip playback; NX2 decoder output gives the game completion via a real output image, incremented GPU syncpoint and GetOutputInfo EOS bit.
4. Avoided the incorrect approach of simply suppressing the movie frame or failing the decoder. Implemented a first-stream-only, title-specific synthetic EOS queued through existing `m_decoded`, processed by the unmodified decode worker and output IPC. The first packet never reaches MediaCodec; subsequent packets in that stream are accepted without decoding. Full game state depends on guest handling of early EOS, still unproven.
5. Added `src/core/hle/service/nx2_intro_skip.h`, and modified `nx2_gsv.h` via a strictly anchored reproducible patch. Opt-in environment switch `HOKKAIDO_OOT_SKIP_INTRO=1`; one-time claim of first AV1 decoder only, scoped by exact Ocarina title ID. Stop/Flush restores normal decoder behavior for later movies. Applied no changes to embedded Banana Native engine or game files.
6. Ran 250,000 deterministic source-level policy sessions under Clang ASan/UBSan: PASS (7,881 selected, 242,119 rejected); confirmed single EOS emitted per accepted session, strict title and codec matching, env handling, future-stream exclusion and no extra packets after Stop.
7. Verified v0.26 patch applies cleanly with `patch -p1 --batch --fuzz=0 --dry-run` to local v0.25 code. First unit compilation failed due heterogeneous initializer-list types; repaired test-only type declaration and reran successfully. No service-level guest IPC simulation or tablet test yet.
8. Confirmed `android_env_file.cpp` loads `env.txt` for the current Android application package at process startup, including early static initializers.

9. Moved synthetic-EOS reply outside m_mutex, and verified patch byte-for-byte replay on top of v0.25 (SHA256 486dd21296c96b7be33202e8561dc7267d7e3a9e0114c6c6c2b19177452a1e74).
10. Added non-destructive wireless ADB enable/disable script, syntax checked and exercised against mock ADB; uploaded to Library and committed private GitHub commit 5622a4b5 [skip ci]. This helper has NOT been run against a real tablet.
11. Published full v0.26 source handover ZIP and SHA manifest: https://drive.google.com/file/d/1za39YoWmOzrNs6mCpbUcu-OYEBDzdxCC/view. No proprietary game data or keys included.
12. Isolated v0.26 native Android CI run 45116306354: source patch and sanitizer phase passed; latest observation Android native compilation in progress. No apk or runtime result claimed before CI verifies it.
