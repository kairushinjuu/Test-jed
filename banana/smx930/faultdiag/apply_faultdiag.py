#!/usr/bin/env python3
"""v0.18 safe opt-out cache-eviction diagnostic and bounded major-fault sampling."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
changes={}
def patch(path,old,new):
 s=changes.get(path,path.read_text())
 if new in s:return
 if s.count(old)!=1:raise RuntimeError(f'{path}: expected 1 anchor got {s.count(old)}')
 changes[path]=s.replace(old,new)
h=a.root/'dm/gfx/vk_android/vka_fileback.h'
m=a.root/'dm/gfx/vk_android/vka_mem.c'
patch(h,'''static inline void vkfb_drop(int fd, uint64_t off, uint8_t *t, uint64_t a, uint64_t b) {
    if (b <= a) return;
    sync_file_range(fd, (off64_t)(off + a), (off64_t)(b - a), SYNC_FILE_RANGE_WAIT_BEFORE | SYNC_FILE_RANGE_WRITE | SYNC_FILE_RANGE_WAIT_AFTER);
    madvise(t + a, b - a, MADV_DONTNEED);
    posix_fadvise(fd, (off_t)(off + a), (off_t)(b - a), POSIX_FADV_DONTNEED);
}''','''// DM_MEM_FILEBACK_EVICT=0 diagnostic: leave clean cache pages available for reuse.
// Default 1 retains existing low-RAM behavior. Disabling may INCREASE Android OOM risk.
static inline int vkfb_evict_enabled(void) {
    const char *e = getenv("DM_MEM_FILEBACK_EVICT");
    return !e || strcmp(e, "0") != 0;
}
static inline void vkfb_drop(int fd, uint64_t off, uint8_t *t, uint64_t a, uint64_t b) {
    if (b <= a) return;
    sync_file_range(fd, (off64_t)(off + a), (off64_t)(b - a), SYNC_FILE_RANGE_WAIT_BEFORE | SYNC_FILE_RANGE_WRITE | SYNC_FILE_RANGE_WAIT_AFTER);
    if (vkfb_evict_enabled()) {
        madvise(t + a, b - a, MADV_DONTNEED);
        posix_fadvise(fd, (off_t)(off + a), (off_t)(b - a), POSIX_FADV_DONTNEED);
    }
}''')
patch(m,'#include <sys/mman.h>','#include <sys/mman.h>\n#include <sys/resource.h>')
patch(m,'''    uint64_t t0 = mono_ns();
    pthread_mutex_lock(&g_pl);   // no placement over it meanwhile''','''    uint64_t t0 = mono_ns();
    struct rusage fb_ru0 = {0}, fb_ru1 = {0};
    int fb_ru_ok = getrusage(RUSAGE_SELF, &fb_ru0) == 0;
    pthread_mutex_lock(&g_pl);   // no placement over it meanwhile''')
patch(m,'''    if (!r) sync_file_range(g_fb_fd, off, (off64_t)size, SYNC_FILE_RANGE_WRITE);''','''    // Process-wide deltas include other threads: correlation only, not causal attribution.
    // nlog limits samples to first 8 pools and every 64th subsequent pool.
    if (nlog && fb_ru_ok && getrusage(RUSAGE_SELF, &fb_ru1) == 0)
        VLOG("fileback faultdiag: kind=%s bytes=%llu copied=%llu major_delta=%ld minor_delta=%ld elapsed_ms=%.1f eviction=%d (process-wide concurrent threads included)",
             what, (unsigned long long)size, (unsigned long long)copied,
             fb_ru1.ru_majflt - fb_ru0.ru_majflt, fb_ru1.ru_minflt - fb_ru0.ru_minflt,
             (mono_ns() - t0) / 1e6, vkfb_evict_enabled());
    if (!r) sync_file_range(g_fb_fd, off, (off64_t)size, SYNC_FILE_RANGE_WRITE);''')
if not a.check:
 for f,s in changes.items():f.write_text(s)
print(('check OK' if a.check else 'applied'),len(changes))
