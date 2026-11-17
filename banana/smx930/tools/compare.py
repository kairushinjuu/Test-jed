#!/usr/bin/env python3
"""Conservative A/B comparison; refuses to rank incomparable runs."""
import argparse,json
from pathlib import Path

def compare(a,b,allow_quality_change=False):
    checks=[]
    for k in ('game_title_id','gpu'):
        if a.get(k)!=b.get(k): checks.append(f'{k}: {a.get(k)} != {b.get(k)}')
    for k in ('DM_GRAPHICS_SCALE','DM_ROMFS_OVERLAY','DM_VK_NDSR'):
        if (a.get('environment') or {}).get(k)!=(b.get('environment') or {}).get(k) and not allow_quality_change:
            checks.append('quality mismatch '+k)
    if a.get('driver')!=b.get('driver'):checks.append('driver differs (a driver A/B is not a code/performance A/B)')
    enough = all(x.get('post_intro_fps_samples',0)>=10 for x in (a,b))
    # Keep the experiment controlled: more than one performance knob changed
    # makes it impossible to attribute any FPS or audio difference.
    knobs=('DM_VK_TL_HOST','DM_DBG_AU_FRAMES','DM_VK_WORKER','DM_VK_PSO_SLOTS','DM_VK_IMG_RESERVE_MB','DM_MEM_FILEBACK','DM_MEM_FILEBACK_KINDS','DM_CODEC_THREAD','DM_AV1_RGBA_EARLY')
    changes=[k for k in knobs if (a.get('environment') or {}).get(k)!=(b.get('environment') or {}).get(k)]
    if len(changes)>1: checks.append('multiple tuning changes in one A/B: '+', '.join(changes))
    if not enough: checks.append('at least 10 observed gameplay FPS samples required in both runs')
    gain = None
    if enough:
        base = a['post_intro_median_fps']
        gain=round(100*(b['post_intro_median_fps']-base)/base,2) if base else None
    return {'comparable':not checks, 'reasons':checks, 'tuning_variables_changed':changes, 'median_gameplay_fps_change_pct':gain, 'target_passed_in_candidate':b.get('target_met_on_observed_gameplay',False) if not checks else False}

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('baseline',type=Path);ap.add_argument('candidate',type=Path)
    ap.add_argument('--allow-quality-change',action='store_true')
    ns=ap.parse_args()
    print(json.dumps(compare(json.loads(ns.baseline.read_text()),json.loads(ns.candidate.read_text()),ns.allow_quality_change),indent=2))
