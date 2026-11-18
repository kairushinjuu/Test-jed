#!/usr/bin/env python3
"""v0.23 SM-X930: reduce *reported* guest RAM for SDK cache sizing, not hard limits.

The source's hle_svc.c reported_total() uses DM_APP_POOL_MB to tune the
Switch SDK's cached-page target; it deliberately does not lower the true
APP_POOL, SetHeapSize bound, or MapPhysicalMemory bound. User env overrides
still precede the SM-X930 profile and win.
"""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
f=a.root/'android/app/src/main/java/dev/nxnative/android/MaliSmx930.java'
s=f.read_text()
old='        "DM_MEM_FILEBACK_KINDS=shader",'
new='''        "DM_MEM_FILEBACK_KINDS=shader",
        // v0.23: tell the guest SDK that ~8 GiB are available for its own
        // allocator/cache planning; leave the actual 9 GiB safety bound intact.
        // The SDK must remain free to reclaim caches and grow to the true
        // pool when needed. User overrides (Advanced/env.txt) take priority.
        "DM_APP_POOL_MB=8192",'''
if new not in s:
    if s.count(old)!=1:raise ValueError(f'expected one Mali profile anchor, found {s.count(old)}')
    s=s.replace(old,new,1)
svc=a.root/'dm/host/hle_svc.c'
h=svc.read_text()
needle='''    t = low && low < APP_POOL ? low : APP_POOL;
    if (atomic_compare_exchange_strong(&g_rep_total, &exp, t) && (mb > 0 || DM_GAME_LOW_RAM_APP_POOL_MB))'''
repl='''    t = low && low < APP_POOL ? low : APP_POOL;
    // v0.23 traces requested vs actual pool without affecting the hard
    // application-pool map limit or memory validity checks.
    if (mb > 0) LOG("[mem] v023 guest memory policy: requested %lld MiB, reported %.2f GiB, hard pool %.2f GiB (report-only; SDK can lift later)",
                    mb, t / 1073741824.0, APP_POOL / 1073741824.0);
    if (atomic_compare_exchange_strong(&g_rep_total, &exp, t) && (mb > 0 || DM_GAME_LOW_RAM_APP_POOL_MB))'''
if repl not in h:
    if h.count(needle)!=1:raise ValueError(f'expected exact guest policy source, found {h.count(needle)}')
    h=h.replace(needle,repl,1)
if not a.check:
    f.write_text(s);svc.write_text(h)
print('v0.23 low-memory guest reporting',('verified' if a.check else 'applied'))
