# Takoboto 2.1.7: recovered architecture

The recovered clean APK uses Xamarin/.NET Android. Its principal managed assembly, `Takoboto.dll`, is packaged inside architecture-specific XABA assembly stores (`libassembly-store.so`), with XALZ/LZ4 compression.

## Components located

- `MainActivity` and `WordActivity`: entry and word-display screens.
- `KanjiSearchActivity`: kanji search UI.
- `WordsListsFragmentOnline`: network word-list interface.
- `GameSelectorActivity`: study-game interface.
- `SubscribeActivity`: subscription UI and account-related operations.
- An obfuscated Google Play Billing manager manages product queries, subscriptions, and one-time purchases.

## Recorded identifiers

Android preference keys include `subscribe_purchase_ok`, `extra_purchase_ok`, and feature values `extra_kanjidraw`, `extra_audio`, `extra_game`.

Google Play product identifiers include `takoboto.cloud.monthly`, `takoboto.cloud.yearly`, `takoboto.cloud.lifetime`, `takoboto.cloud.oneyear`, `takoboto.cloud.threeyears`, plus individual `takoboto.feature.*` products.

Remote cloud authorization is a separate process from local application flags.

## Status

An isolated earlier GitHub run recovered the application DLL, decompiled it through ILSpy, rewrote four client-side method bodies, and verified that the resulting managed assembly could be opened with Mono.Cecil. This did not establish a working Android APK, particularly because native AOT compatibility, APK signing, and device testing were not completed.

Do not commit proprietary decompiled C# or extracted APK data to this public repository.
