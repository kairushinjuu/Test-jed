# Input files and requirements

## Original user-supplied package

The originally uploaded file was named `Japanese+Dictionary+Takoboto_2.1.7_APKPure.xapk`, version 2.1.7, and contains:

| Name | Uncompressed bytes | Purpose |
|---|---:|---|
| `jp.takoboto.apk` | 52,552,990 | Base APK |
| `config.armeabi_v7a.apk` | 13,955,117 | ARMv7 split |
| `config.xhdpi.apk` | 152,978 | Display-density split |
| `manifest.json` | 4,117 | XAPK metadata |

Original XAPK SHA256: `52bb9c9428e8b982ff45dc91ff8a2a93e4ed7f16b17e82b49488dffdf1a76d43`.

The uploaded XAPK has a CRC failure on `config.armeabi_v7a.apk`; the damaged split should not be used to construct an installable application.

To extract the intact pieces locally:

```bash
python scripts/extract_xapk.py input/Japanese+Dictionary+Takoboto_2.1.7_APKPure.xapk --output input/from_xapk
```

The extractor returns exit code 1 when any entry is corrupt, even if other entries were successfully extracted.

## Preferred complete publisher APK

Publisher download previously tested:

https://takoboto.jp/download/android/jp.takoboto.apk

The copy previously retrieved on 2026-10-15 had:

- Size: 112,894,054 bytes
- SHA256: `bbbe3c24adb886c6154bb8fdab3ec3534be4398b2091f9cd9805681240cbe253`

Use `scripts/recover_assembly.py` against this APK to obtain `Takoboto.dll` and its managed dependency assemblies. The publisher may change the file over time, so check version and checksum against the values above.

## For investigation

1. **APK inputs:** intact publisher APK, or base + valid architecture split APK(s).
2. **Managed application code:** `output/recovered/Takoboto.dll`, extracted from the assembly store, plus `output/recovered/managed_dependencies/`.
3. **Optional readable C# inspection:** ILSpy output in `output/decompiled/`. This is decompiled code, not the original developer's .NET solution, build assets, or project.
4. **Android inspection utilities:** Python 3.10+, `lz4`, .NET SDK and ILSpy.
5. **Packaging/verification:** Android SDK `zipalign`, `apksigner`, and optionally ADB for device tests.
6. **Signing material:** a keystore and alias belonging to the person building the APK. Do not commit secrets.

## Limitations

The public repository contains extraction, inspection, and signing utilities. It does not contain the original developer source, the original APK, a complete APK reassembly mechanism, or the earlier research experiment's managed IL patcher.

A replacement application build is not the same as recompiling the developer's original source. Xamarin assembly-store structure, native AOT loading, and certificate/package compatibility must each be addressed independently.
