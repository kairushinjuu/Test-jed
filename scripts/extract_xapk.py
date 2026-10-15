#!/usr/bin/env python3
"""Extract Android split packages from an XAPK, reporting corrupt entries."""
import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

def extract(xapk, dest):
    dest.mkdir(parents=True, exist_ok=True)
    successes, failures = [], []
    with zipfile.ZipFile(xapk, "r") as container:
        for entry in container.infolist():
            if not (entry.filename.endswith(".apk") or entry.filename == "manifest.json"):
                continue
            if "/" in entry.filename or ".." in entry.filename:
                failures.append((entry.filename, "unsafe path"))
                continue
            target = dest / entry.filename
            try:
                with container.open(entry) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst, 1024 * 1024)
                with target.open("rb") as stream:
                    checksum = hashlib.sha256(stream.read()).hexdigest()
                successes.append((target, target.stat().st_size, checksum))
            except (zipfile.BadZipFile, OSError, EOFError) as exc:
                target.unlink(missing_ok=True)
                failures.append((entry.filename, str(exc)))
    return successes, failures

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xapk")
    parser.add_argument("--output", default="input/from_xapk")
    args = parser.parse_args()
    source = Path(args.xapk)
    if not source.is_file():
        parser.error(f"Not a file: {source}")
    try:
        good, bad = extract(source, Path(args.output))
    except (zipfile.BadZipFile, OSError) as exc:
        print(f"Cannot read XAPK: {exc}", file=sys.stderr)
        return 2
    for path, size, digest in good:
        print(f"OK      {path} | {size} bytes | SHA256 {digest}")
    for name, problem in bad:
        print(f"CORRUPT {name}: {problem}", file=sys.stderr)
    if bad:
        print(f"Valid files saved ({len(good)}); {len(bad)} failed integrity check", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
