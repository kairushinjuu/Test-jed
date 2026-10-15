# Takoboto Android research toolkit

Repeatable Xamarin/.NET Android application analysis, managed assembly recovery, static C# inspection, and Android APK signing.

## Setup

Requirements: Python 3.10+, .NET 8 SDK, and (for signing) Android SDK build-tools.

```bash
git clone https://github.com/kairushinjuu/Test-jed.git
cd Test-jed
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Obtain an APK for local analysis

The original XAPK is not committed to this public repository. See [docs/inputs.md](docs/inputs.md) for the original file inventory, its known CRC error, and a verified publisher download.

To extract the intact parts from a local XAPK:

```bash
python scripts/extract_xapk.py input/Japanese+Dictionary+Takoboto_2.1.7_APKPure.xapk --output input/from_xapk
```

Or obtain the publisher's universal APK directly from https://takoboto.jp/download/android/jp.takoboto.apk and place it at `input/takoboto.apk`.

## Inspect a local APK

Place the original APK at `input/takoboto.apk`:

```bash
python scripts/inspect_apk.py input/takoboto.apk
python scripts/recover_assembly.py input/takoboto.apk --output output/recovered
```

This extracts `Takoboto.dll`, managed dependencies, and an assembly inventory.

## Decompile and audit

```bash
dotnet tool install --tool-path .tools ilspycmd --version 11.1.0.9782
.tools/ilspycmd -p -o output/decompiled output/recovered/Takoboto.dll
python scripts/audit_source.py output/decompiled --output output/audit
```

On Windows invoke `.tools\ilspycmd.exe` instead of `.tools/ilspycmd`.

The `scripts/run_audit.sh` helper runs the preceding inspection steps on Linux/macOS.

## Align and sign an unsigned APK

```bash
bash scripts/sign_apk.sh input/unsigned.apk output/signed.apk /path/to/keystore.jks your-alias
```

You must already have an unsigned APK; the signing helper does not modify its application logic. A different signing certificate prevents in-place updates over the officially signed app.

## Source and provenance

- Original codebase: Xamarin/.NET Android, with C# inside XABA/XALZ assembly stores.
- Java/DEX wrappers, ARM native AOT binaries, and separate cloud-service authorization are present.
- Earlier clean APK: SHA-256 `bbbe3c24adb886c6154bb8fdab3ec3534be4398b2091f9cd9805681240cbe253`, 112894054 bytes (may change with publisher updates).
- Earlier managed-IL verification: [private research PR #2](https://github.com/kairushinjuu/testweb/pull/2).
- See [docs/findings.md](docs/findings.md) and [docs/build_status.md](docs/build_status.md).

This public repository excludes original APKs, decompiled proprietary source, signing credentials, premium-bypass patch implementation, and a verified full APK-rebuild pipeline.
