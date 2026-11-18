#!/usr/bin/env python3
"""v0.21: reclaim unused Mali image blocks and add bounded allocation attribution."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
changes={}
def patch(rel,old,new):
 f=a.root/rel
 s=changes.get(f,f.read_text())
 if new in s:return
 if s.count(old)!=1:raise RuntimeError(f'{rel}: expected one anchor, got {s.count(old)}')
 changes[f]=s.replace(old,new,1)
patch('dm/gfx/vk_android/vka_imgmem.c','''        if (empties > 1) {
            for (iblock **p = &g_blocks[b->type]; *p; p = &(*p)->next) if (*p == b) { *p = b->next; break; }
            gone = b; S.blocks--; S.freed++;
        }''','''        // v0.21: release fully empty 64 MiB blocks on G925 rather than
        // retaining a spare allocation; only blocks with zero live runs qualify.
        // DM_VK_IMGMEM_KEEP_EMPTY=1 restores the previous behavior.
        int keep_empty = VKA_ENV("DM_VK_IMGMEM_KEEP_EMPTY", strstr(V.props.deviceName, "G925") ? 0 : 1);
        if (empties > 1 || !keep_empty) {
            for (iblock **p = &g_blocks[b->type]; *p; p = &(*p)->next) if (*p == b) { *p = b->next; break; }
            gone = b; S.blocks--; S.freed++;
        }''')
patch('dm/gfx/vk_android/vka_imgmem.c','''    if (gone) { vk.vkFreeMemory(V.dev, gone->dm, NULL); vke_fini(&gone->free); free(gone); }
    memset(m, 0, sizeof *m);''','''    if (gone) {
        vk.vkFreeMemory(V.dev, gone->dm, NULL);
        static _Atomic unsigned released;
        unsigned count = atomic_fetch_add(&released, 1) + 1;
        if (count <= 16 || !(count & 63))
            VLOG("v021 image memory: empty 64 MiB block freed (type %u, total %u; DM_VK_IMGMEM_KEEP_EMPTY controls reserve)", gone->type, count);
        vke_fini(&gone->free); free(gone);
    }
    memset(m, 0, sizeof *m);''')
patch('dm/host/hle_svc.c','''static _Atomic int nref; if (atomic_fetch_add(&nref, 1) < 8) LOG("[mem] MapPhysicalMemory +%#zx refused: %.2f GB mapped, the application pool is full (ResultLimitReached, the SDK frees cached pages and retries)",
                                                                       size, atomic_load(&g_alias_mapped) / 1073741824.0);''','''static _Atomic int nref; if (atomic_fetch_add(&nref, 1) < 8) LOG("[mem] MapPhysicalMemory +%#zx refused: %.2f GB mapped, the application pool is full (ResultLimitReached, the SDK frees cached pages and retries); v021 accounting: pool %.2f GiB, heap %.2f GiB, alias %.2f GiB, used %.2f GiB, big-bss %.2f GiB, remaining %.2f MiB, requested new %.2f MiB",
                                                                       size, atomic_load(&g_alias_mapped) / 1073741824.0,
                                                                       APP_POOL / 1073741824.0, (double)g_heap_cur / 1073741824.0,
                                                                       (double)atomic_load(&g_alias_mapped) / 1073741824.0,
                                                                       (double)DM_GAME_MEM_USED / 1073741824.0, (double)big_bss_bytes() / 1073741824.0,
                                                                       (double)room / 1048576.0, (double)need / 1048576.0);''')
patch('dm/gfx/vk_android/vka_tex.c','''    if ((u & (VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT)) && im->w >= 1024 && im->levels == 1 && im->layers == 1) {''','''    // v0.21 allocation attribution: no unsafe resizing or live-image eviction.
    if (mr.size >= (VkDeviceSize)(64ull << 20)) {
        static _Atomic unsigned n;
        if (atomic_fetch_add(&n, 1) < 32)
            VLOG("v021 large image attribution: serial=%llu size=%.1f MiB pool-storage=%.1f MiB pool_fit=%d gpu-write-capable=%d zero-shared=%d dedicated=%d",
                 (unsigned long long)t->serial, mr.size / 1048576.0, t->L.size / 1048576.0,
                 im->pool_fit, (u & (VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_STORAGE_BIT)) != 0,
                 im->m.z != 0, im->m.blk == NULL);
    }
    if ((u & (VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT)) && im->w >= 1024 && im->levels == 1 && im->layers == 1) {''')
patch('dm/gfx/vk_android/vka_tex.c','''        if (res.valid) VLOG("oomguard residency: RSS=%llu MiB PSS=%llu MiB anonymous=%llu MiB swap=%llu MiB (smaps_rollup; process-wide)",
            (unsigned long long)(res.rss_kb >> 10), (unsigned long long)(res.pss_kb >> 10),
            (unsigned long long)(res.anon_kb >> 10), (unsigned long long)(res.swap_kb >> 10));''','''        if (res.valid) VLOG("oomguard residency: RSS=%llu MiB PSS=%llu MiB anonymous=%llu MiB swap=%llu MiB (smaps_rollup; process-wide)",
            (unsigned long long)(res.rss_kb >> 10), (unsigned long long)(res.pss_kb >> 10),
            (unsigned long long)(res.anon_kb >> 10), (unsigned long long)(res.swap_kb >> 10));
        char imstat[768]; vka_imem_stats(imstat, sizeof imstat);
        VLOG("v021 allocation breakdown: %s; image cache=%llu MiB (GPU allocation sizes, not RSS)",
             imstat, (unsigned long long)((g_img_bytes + vka_imem_zbytes()) >> 20));''')
if not a.check:
 for f,s in changes.items():f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s)
print(('check OK' if a.check else 'applied'),len(changes))
