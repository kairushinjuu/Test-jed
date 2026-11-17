# Banana Native SM-X930: reuse prepared shaders across APKs

Date: 2026-11-17. Source verified against pinned Banana Native v0.8/v0.12.1 fork and the user's v0.8 game log.

## Confirmed compatibility

- Game title: Ocarina of Time Switch 2 Edition `0400486024DEC000`.
- v0.8's log reports **42,848 shaders**, **52,863 modules**, in a **695.6 MB** `dmsh_vk.lib`, at Vulkan chain `19662e4c4a25`, profile inputs `0a7aeafde2d0`.
- v0.12.1's source `dm/gfx/nvn/dmsh_chain_vk.h` expects Vulkan chain `19662e4c4a25`, ABI `4fbeb79f5ab7`; the new application verifies the library and profile stamp.
- The shaders are **not in the APK**. They are generated in the game pack on the device. The v0.8 log shows:
  `/storage/emulated/0/Android/data/dev.nxnative.android.malig925lab/files/packs/0400486024DEC000/shaders/v-19662e4c4a25/dmsh_vk.lib`
- v0.12.1 package is `dev.nxnative.android.malig925mass`; Android's scoped storage prevents one app from simply browsing another app's Android/data directory, hence the export/import workflow.

## Quickest fully supported method: built-in Export pack / Import pack

1. In **v0.8**, open the Ocarina game page, **Storage** tab, **Export pack**. Pick a public folder such as `Download`.
2. The export creates `banana-pack-0400486024DEC000-<version>.zip`. Wait until completed; don't close or stop the app during export. It copies the game code and `shaders/v-19662e4c4a25/dmsh_vk.lib` **without retranslating the shaders**.
3. Open **v0.12.1**. If the game is not listed, use **Add Game** to select the *same* `.nup` (or dump folder).
4. Game page → **Storage** → **Import pack** → **ZIP file**. Select the archive from `Download`. The application checks title/game build and atomically installs the pack into its own storage.
5. In the new game's **Storage → Details** check the shader library is present and the pack folder matches the new app. On launch, the log should report 42,848 shaders and Vulkan chain `19662e4c4a25`. Do **not** run Prepare again if the imported pack is ready.
6. Keep v0.8 intact until the new app successfully launches. Exporting reads the old pack; it doesn't delete it.

**Storage requirement:** Pack export is a stored (uncompressed) ZIP including code and other pack files. For a while the tablet will hold the original pack, exported ZIP and imported pack; ensure sufficient free storage. Importing may take several minutes, but it avoids the expensive shader translation.

## Better for repeated forks: a single shared pack folder

Instead of using Import pack for every new package ID, export once and extract the ZIP into a shared folder *beside your game file*, for example:

`/storage/emulated/0/Download/games/0400486024DEC000-work/android-pack/`

**Important:** `pack.tsv` must be directly inside `android-pack/`, alongside the `shaders/` directory and code files; do not leave an extra ZIP-name wrapper directory.

Open v0.12.1's game page → **Storage → Folders → Pack and shader folder → Pick** and select `android-pack/`. Subsequent builds can use exactly that pack folder. If the app discovers it automatically beside the `.nup`, confirm it in Storage → Details. Only let one emulator/Prepare process write to that shared pack at a time.

This shared-directory method avoids multiplying the ~696 MB shader library for every experimental APK, subject to app storage permissions. Don't remove the original until the shared pack works.

## Different cache: compiled Vulkan driver pipelines

A prepared `dmsh_vk.lib` is the translated game shader library, not PanVK's native GPU pipeline cache. v0.8's log also identifies:

`/storage/emulated/0/Android/data/dev.nxnative.android.malig925lab/files/temp/0400486024DEC000/vk_pipelines-PanVK_faux123_v1.1.8-fp0.bin`

The v0.8 log reports 11,271,632 bytes read, and a separate `vk_pipelines.keys` prewarming list containing 3,456 entries. These files live under **`temp/`**, not inside `packs/`, and the built-in Export pack **does not include them**.

Consequently, importing the pack avoids the ~1-hour shader-library generation, **but some first-run Vulkan pipeline compilation may still occur**. The pipeline `.bin` is driver/UUID-specific; any future migration must copy its matching `.lib` stamp and `vk_pipelines.keys`, and must not force-load it when the GPU driver or Vulkan cache UUID differs. Never rename arbitrary GPU caches as a substitute for validation.

## Prevent recurrence in future builds

Use the **same package ID and persistent app-signing key** for future test APKs to preserve game packs, settings and caches through ordinary Android updates. Current CI uses ephemeral debug-signing keys, so changing only the package ID is insufficient: signing certificates must also match. Do not commit private signing material to a public GitHub repository.

No game files or shader binaries are distributed with this guide.
