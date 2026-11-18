#!/usr/bin/env python3
"""v0.24 SoftGuard: restore safe guest total, enable source-tested soft mip residency.

Only affects SM-X930 / Ocarina via MaliSmx930. The production vksoft_candidate()
restricts eligibility to packaged, block-compressed, non-sparse 2D textures with
3+ mip levels and sufficiently large dimensions. GPU write/copy paths harden
images on demand. Explicit user env overrides continue to win.
"""
import argparse
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument("root",type=Path);ap.add_argument("--check",action="store_true");args=ap.parse_args()
p=args.root/"android/app/src/main/java/dev/nxnative/android/MaliSmx930.java"
s=p.read_text()
old='        "DM_APP_POOL_MB=8192",'
new='''        "DM_APP_POOL_MB=9216",  // v0.23's 8 GiB report caused pre-menu SIGSEGV; real 9 GiB restored
        "DM_VK_TEX_SOFT=1",     // v0.24: large packaged BCn/ASTC textures omit finest mip when safe
        "DM_VK_TEX_SOFT_LEVELS=1", // explicit one-level, source-tested mode; copies can harden
'''
if new not in s:
    if s.count(old)!=1:raise RuntimeError(f"exact v0.23 anchor not found once: {s.count(old)}")
    s=s.replace(old,new,1)
if s.count('"DM_APP_POOL_MB=9216"') != 1 or '"DM_APP_POOL_MB=8192"' in s:
    raise RuntimeError("unsafe low-memory report still present")
if s.count('"DM_VK_TEX_SOFT=1"') != 1:raise RuntimeError("soft toggle missing")
if not args.check:p.write_text(s)
print("v0.24 SoftGuard profile", "verified" if args.check else "applied")
