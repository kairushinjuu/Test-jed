#!/usr/bin/env python3
"""SM-X930 v0.20: safe boot policy experiment, isolated from v0.19."""
import argparse
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("root", type=Path)
ap.add_argument("--check", action="store_true")
a = ap.parse_args()
p = a.root / "android/app/src/main/java/dev/nxnative/android/MaliSmx930.java"
s = p.read_text()
edits = {
    '"DM_VK_PREWARM=1",': '"DM_VK_PREWARM=0",',
    '"DM_MEM_FILEBACK_KINDS=shader,texture",': '"DM_MEM_FILEBACK_KINDS=shader",',
    '"DM_VK_IMG_DIAG=10",': '"DM_VK_IMG_DIAG=5",',
    '"DM_VK_SLOT_POOL=1"': '"DM_VK_PRUNE_MS=2",        // bounded texture prune work per frame\n        "DM_MOVIE_SKIP=1",         // skip intro video to reach scene quickly\n        "DM_VK_SLOT_POOL=1"'
}
modified = s
for old, new in edits.items():
    if new in modified:
        continue
    if modified.count(old) != 1:
        raise ValueError(f"expected one anchor {old!r}, found {modified.count(old)}")
    modified = modified.replace(old, new)
if 'DM_MEM_FILEBACK_KINDS=shader,texture' in modified:
    raise ValueError("texture file-backing must not be default in v0.20")
if a.check:
    print("v0.20 policy patch check OK")
else:
    p.write_text(modified)
    print("v0.20 policy patch applied")
