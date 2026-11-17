#!/usr/bin/env python3
"""Conservative comparison for runs that crash at the first 3D scene.

No steady FPS conclusion is possible; this tool ONLY compares observed pressure signals.
"""
import argparse,json,statistics
from pathlib import Path
TUNING=('DM_VK_TL_HOST','DM_VK_PSO_ASYNC','DM_DBG_AU_FRAMES','DM_VK_IMG_RESERVE_MB','DM_MEM_FILEBACK','DM_MEM_FILEBACK_KINDS')
QUALITY=('DM_GRAPHICS_SCALE','DM_VK_NDSR','DM_ROMFS_OVERLAY')

def compare_scene(a,b):
    reasons=[]
    for k in ('game_title_id','gpu','driver'):
        if a.get(k)!=b.get(k):reasons.append('different '+k)
    ae=a.get('environment') or {};be=b.get('environment') or {}
    for k in QUALITY:
        if ae.get(k)!=be.get(k):reasons.append('quality differs: '+k)
    changed=[k for k in TUNING if ae.get(k)!=be.get(k)]
    if len(changed)!=1:reasons.append('A/B requires exactly one changed tuning control')
    if not (a.get('intro_complete') and b.get('intro_complete')):reasons.append('both runs must finish the AV1 intro')
    if not (a.get('after_movie_scene_windows') and b.get('after_movie_scene_windows')):reasons.append('both runs must reach scene transition')
    # Never claim a steady-state FPS comparison with a crash or too few observed post-intro samples.
    def summary(x):
        scenes=x.get('after_movie_scene_windows') or []
        aud_n=x.get('audio_callback_windows') or 0
        return {
         'observed_scene_window_fps':[s.get('fps') for s in scenes],
         'observed_scene_gpu_p50_ms':[s.get('gpu_p50_ms') for s in scenes],
         'worst_frame_ms':(x.get('worst_longframe') or {}).get('whole_ms'),
         'worst_frame_pipeline_compile_ms':(x.get('worst_longframe') or {}).get('pipeline_creation_ms'),
         'last_tracked_graphics_mib':x.get('last_tracked_graphics_allocation_mib'),
         'audio_underruns_per_2000_callbacks':round((x['audio_underflow_events']/aud_n),2) if aud_n and x.get('audio_underflow_events') is not None else None,
         'audio_silence_ms_per_2000_callbacks':round((x['audio_zero_padded_ms']/aud_n),2) if aud_n and x.get('audio_zero_padded_ms') is not None else None,
        }
    return {'scene_pressure_comparable':not reasons,'reasons':reasons,
     'one_tuning_variable_changed':changed,
     'baseline':summary(a),'candidate':summary(b),
     'steady_gameplay_50fps_claim_permitted':False,
     'caveat':'Scene startup and crash windows do not establish sustained FPS; audio window durations and scene content must be checked manually.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path)
    ns=p.parse_args();print(json.dumps(compare_scene(json.loads(ns.baseline.read_text()),json.loads(ns.candidate.read_text())),indent=2))
