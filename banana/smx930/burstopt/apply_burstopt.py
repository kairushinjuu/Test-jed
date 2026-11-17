#!/usr/bin/env python3
"""Opt-out bounded image cache pressure refresh for rapid image creation bursts."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
f=a.root/'dm/gfx/vk_android/vka_tex.c'
s=f.read_text(); edits=[]
def patch(old,new,name):
 global s
 if new in s:return
 n=s.count(old)
 if n!=1:raise RuntimeError(f'{name}: expected 1 matching anchor, got {n}')
 s=s.replace(old,new);edits.append(name)
patch('static uint64_t g_img_lim, g_lim_frame, g_prune_dry, g_img_ws;',
'''// Sampled image memory size at the last cache budget update; refreshed on large within-frame bursts.
static uint64_t g_img_measure_bytes;
static uint64_t g_img_burst_refreshes;
static uint64_t g_img_lim, g_lim_frame, g_prune_dry, g_img_ws;''','state')
patch('''    if (g_img_lim && cur_frame < g_lim_frame + (g_psi.pressed ? 15 : 60)) return;
    g_lim_frame = cur_frame;
    uint64_t imgs = g_img_bytes + vka_imem_zbytes();''',
'''    uint64_t imgs = g_img_bytes + vka_imem_zbytes();
    // The ordinary budget refresh runs every 60 frames (15 under PSI pressure). A scene can
    // create hundreds of images in ONE frame; the 60-frame cached limit misses that burst.
    // Refresh after a bounded growth threshold instead of refreshing on every image.
    // DM_VK_IMG_BURST_REFRESH_MB=0 restores the original time-only refresh behavior.
    int burst_mb = VKA_ENV("DM_VK_IMG_BURST_REFRESH_MB", 128);
    uint64_t burst = burst_mb > 0 && burst_mb <= 4096 ? (uint64_t)burst_mb << 20 : 0;
    int due_time = !g_img_lim || cur_frame >= g_lim_frame + (g_psi.pressed ? 15 : 60);
    int due_burst = env <= 0 && !due_time && burst && imgs >= g_img_measure_bytes
                 && imgs - g_img_measure_bytes >= burst;
    if (!due_time && !due_burst) return;
    g_lim_frame = cur_frame;
    g_img_measure_bytes = imgs;
    if (due_burst) {
        g_img_burst_refreshes++;
        if (g_img_burst_refreshes <= 8 || !(g_img_burst_refreshes & 15))
            VLOG("image cache burst refresh: +%llu MiB in one refresh interval, %llu pressure samples so far (DM_VK_IMG_BURST_REFRESH_MB=%d)",
                 (unsigned long long)(burst >> 20), (unsigned long long)g_img_burst_refreshes, burst_mb);
    }''','burst_refresh')
# Harden candidate vector reallocation during memory pressure: do not corrupt state or run qsort over NULL.
patch('''    if (ccap < g_nlive) { ccap = g_nlive + 256; c = realloc(c, (size_t)ccap * sizeof *c); }
    uint64_t done_fence''',
'''    if (ccap < g_nlive) {
        int next_cap = g_nlive + 256;
        prune_ent *next = realloc(c, (size_t)next_cap * sizeof *c);
        if (!next) {
            static _Atomic int n;
            if (atomic_fetch_add(&n, 1) < 4) VRED("image cache: cannot grow prune candidate array: leaves existing images intact");
            return;  // Keep the old array and every image unchanged on host OOM.
        }
        c = next; ccap = next_cap;
    }
    uint64_t done_fence''','oom_guard')
if a.check:print('check OK',edits)
else:f.write_text(s);print('applied',edits)
