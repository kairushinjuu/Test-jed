#!/usr/bin/env python3
"""v0.19 G925 OOM guard: conservative PSO gate and bounded process residency."""
import argparse
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--check',action='store_true');args=ap.parse_args()
changes={}
def patch(path,old,new):
 s=changes.get(path,path.read_text())
 if new in s:return
 if s.count(old)!=1:raise RuntimeError(f'{path}: expected one anchor, got {s.count(old)}')
 changes[path]=s.replace(old,new)
p=args.root/'dm/gfx/vk_android/vka_pso.c'
patch(p,'static int gate_cap(void) { return VKA_ENV("DM_VK_PSO_SLOTS", vkpg_cap_default(V.driver_id == VK_DRIVER_ID_MESA_TURNIP)); }','''// v0.19: conservative G925 PSO compile overlap after Android confirmed OOM KILL.
// Explicit DM_VK_PSO_SLOTS still overrides this default for comparisons.
static int gate_g925(void) { return strstr(V.props.deviceName, "G925") != NULL; }
static int gate_cap(void) { return VKA_ENV("DM_VK_PSO_SLOTS", gate_g925() ? 1 : vkpg_cap_default(V.driver_id == VK_DRIVER_ID_MESA_TURNIP)); }''')
patch(p,'cap, getenv("DM_VK_PSO_SLOTS") ? "" : V.driver_id == VK_DRIVER_ID_MESA_TURNIP ? ", 1 on Turnip by default" : "");','''cap, getenv("DM_VK_PSO_SLOTS") ? "" : gate_g925() ? ", 1 on G925 OOM guard by default" : V.driver_id == VK_DRIVER_ID_MESA_TURNIP ? ", 1 on Turnip by default" : "");''')
header='''// v0.19 sampled process-local memory diagnostic; no per-frame scanning.
#pragma once
#include <stdio.h>
#include <stdint.h>
#include <string.h>
typedef struct { uint64_t rss_kb, pss_kb, anon_kb, swap_kb; int valid; } vko_resident;
static inline vko_resident vko_parse_rollup(FILE *f) {
    vko_resident x = {0}; char line[160], key[48]; unsigned long long kb;
    while (f && fgets(line, sizeof line, f)) {
        if (sscanf(line, "%47[^:]: %llu kB", key, &kb) != 2) continue;
        if (!strcmp(key,"Rss")) { x.rss_kb=kb; x.valid=1; }
        else if (!strcmp(key,"Pss")) x.pss_kb=kb;
        else if (!strcmp(key,"Anonymous")) x.anon_kb=kb;
        else if (!strcmp(key,"Swap")) x.swap_kb=kb;
    }
    return x;
}
static inline vko_resident vko_read_resident(void) {
    FILE *f=fopen("/proc/self/smaps_rollup","re");
    vko_resident x=vko_parse_rollup(f);
    if (f) fclose(f);
    return x;
}
'''
h=args.root/'dm/gfx/vk_android/vka_oomdiag.h'
if not h.exists():changes[h]=header
elif h.read_text()!=header:raise RuntimeError('unexpected resident diagnostic header')
t=args.root/'dm/gfx/vk_android/vka_tex.c'
patch(t,'#include "vka_texlimit.h"','#include "vka_texlimit.h"\n#include "vka_oomdiag.h"')
patch(t,'    vktl_in in = {.img_bytes = imgs, .psi_some10 = -1};','''    // Bounded memory profile at large texture bursts, not on every draw.
    if (due_burst && (g_img_burst_refreshes <= 8 || !(g_img_burst_refreshes & 15))) {
        vko_resident res = vko_read_resident();
        if (res.valid) VLOG("oomguard residency: RSS=%llu MiB PSS=%llu MiB anonymous=%llu MiB swap=%llu MiB (smaps_rollup; process-wide)",
            (unsigned long long)(res.rss_kb >> 10), (unsigned long long)(res.pss_kb >> 10),
            (unsigned long long)(res.anon_kb >> 10), (unsigned long long)(res.swap_kb >> 10));
    }
    vktl_in in = {.img_bytes = imgs, .psi_some10 = -1};''')
if not args.check:
 for f,s in changes.items():f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
print(('check OK' if args.check else 'applied'),len(changes))
