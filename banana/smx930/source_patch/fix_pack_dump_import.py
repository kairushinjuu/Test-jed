#!/usr/bin/env python3
"""Fix pinned shader_split.py pack_dump import in the on-device tool layout.
The archive has scripts/pack_dump.py beside dm/, not inside dm/scripts/.
Refuse unknown source revisions; safe to rerun."""
from pathlib import Path
import argparse

REL=Path("dm/gfx/tools/shader_split.py")
OLD="sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'scripts'))"
NEW="sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'scripts'))"

def patch(root: Path, check=False):
    path=root/REL
    content=path.read_text(encoding="utf-8")
    if NEW in content:
        if content.count(NEW)!=1:
            raise RuntimeError("ambiguous corrected import")
        return "already corrected"
    if content.count(OLD)!=1:
        raise RuntimeError("unknown shader_split.py revision: refusing blind patch")
    if not check:
        path.write_text(content.replace(OLD, NEW, 1), encoding="utf-8")
    return "verified" if check else "patched"

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    print(patch(args.root,args.check))
