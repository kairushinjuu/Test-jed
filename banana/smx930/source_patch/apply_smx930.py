#!/usr/bin/env python3
"""Apply *only* SM-X930 game policy to the pinned, existing Mali-patched tree.
Never overwrite unrecognized source. Repeatable on an already patched tree.
"""
from pathlib import Path
import argparse
import shutil

REL='android/app/src/main/java/dev/nxnative/android'
ANCHOR='        return gpuNote;\n    }\n    private String readinessLine;'
REPLACE='''        if (MaliSmx930.apply(Build.MODEL, id, env))
            unknownNotes.add("[smx930] bounded Mali policy: one compiler, no prewarm, RAM saver, 1536 MiB image reserve; user overrides still win");
        return gpuNote;
    }
    private String readinessLine;'''

def apply(root:Path, source:Path, check:bool=False) -> None:
    game=root/REL/'GameActivity.java'
    policy=root/REL/'MaliSmx930.java'
    if not game.is_file():raise RuntimeError(f'expected GameActivity source: {game}')
    old=game.read_text()
    if REPLACE in old:
        print('Already applied: GameActivity')
    elif old.count(ANCHOR)==1:
        if not check:game.write_text(old.replace(ANCHOR,REPLACE,1))
        print('Validated GameActivity anchor')
    else:raise RuntimeError('Unknown upstream GameActivity revision; refusing blind patch')
    candidate=(source/'MaliSmx930.java').read_text()
    if policy.is_file() and policy.read_text()!=candidate:raise RuntimeError('MaliSmx930 source differs; refusing overwrite')
    if not check and not policy.is_file():shutil.copyfile(source/'MaliSmx930.java',policy)
    print('Validated dedicated SM-X930 profile')

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    apply(args.root,Path(__file__).resolve().parent,args.check)
