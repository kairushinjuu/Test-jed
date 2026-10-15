#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

def inspect(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path) as z:
        damaged = z.testzip()
        names = z.namelist()
        stores = [n for n in names if n.endswith("/libassembly-store.so")]
        aot = [n for n in names if "/libaot-" in n and n.endswith(".so")]
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": digest,
            "zip_crc": "OK" if damaged is None else "FAILED: " + damaged,
            "entries": len(names),
            "assembly_stores": stores,
            "aot_libraries": aot,
            "has_manifest": "AndroidManifest.xml" in names,
            "has_dex": any(n.endswith(".dex") for n in names),
            "abis": sorted({n.split("/")[1] for n in names if n.startswith("lib/") and len(n.split("/")) > 2}),
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk")
    args = parser.parse_args()
    try:
        result = inspect(args.apk)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["zip_crc"] != "OK" else 0

if __name__ == "__main__":
    raise SystemExit(main())
