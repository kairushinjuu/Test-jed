#!/usr/bin/env python3
"""Source-bound Mali G925 draw/texture preflight optimization + sampled phase profiler.
Run on already-patched Banana Native SM-X930 0.12.1 source.
Fails closed on unexpected upstream source, idempotent. No driver barriers changed.
"""
from pathlib import Path
import argparse


def replace(root, name, old, new, check):
    p=root/name
    s=p.read_text()
    if s.count(new)==1:
        print('already patched', name);return
    if s.count(old)!=1:
        raise ValueError(f'{name}: anchor found {s.count(old)} times; refusing mutation')
    if not check:p.write_text(s.replace(old,new,1))
    print('checked' if check else 'patched',name)


def main(root,check=False):
    h='dm/gfx/vk_android/vka.h'
    replace(root,h,
'''int vka_tex_id_pending_rec(int id, uint8_t dim);
int vka_tex_id_storage_pending(int id);''',
'''int vka_tex_id_pending_rec(int id, uint8_t dim);
int vka_tex_id_prepare_pending_rec(int id, uint8_t dim, int storage); // same checks with one registry lock for storage bindings (Mali fast scan)
int vka_tex_id_storage_pending(int id);''',check)
    t='dm/gfx/vk_android/vka_tex.c'
    replace(root,t,
'''int vka_tex_id_storage_pending(int id) {
    pthread_mutex_lock(&g_tmu);''',
'''// The render-pass preflight used to take two separate texture-registry locks for
// every storage image: first to ask whether it was ever made, then to ask if the
// existing image needs storage usage or private memory. Both questions are read
// from the same registry generation under ONE lock. It does not mutate images,
// create views or bypass any needed pass break. For sampled-only textures keep
// the existing versioned recording-thread memo and its fast return.
int vka_tex_id_prepare_pending_rec(int id, uint8_t dim, int storage) {
    if (!storage) return vka_tex_id_pending_rec(id, dim);
    if (id <= 0) return 0;
    pthread_mutex_lock(&g_tmu);
    int needed = 0;
    if (id < g_ntreg && g_treg[id].t.serial) {
        const treg_ent *te = &g_treg[id];
        smap_ent *e = map_get(te->t.serial);
        if ((te->t.d.target != NVN_TEXTURE_TARGET_BUFFER || !VKA_ENV("DM_VK_TBUF", 1)) && !e) needed = 1;
        if (!needed && e && e->im &&
            ((!(e->im->usage & VK_IMAGE_USAGE_STORAGE_BIT) && storage_able(e->im, VK_FORMAT_UNDEFINED) && !e->im->holds) || e->im->m.z)) needed = 1;
    }
    pthread_mutex_unlock(&g_tmu);
    return needed;
}
int vka_tex_id_storage_pending(int id) {
    pthread_mutex_lock(&g_tmu);''',check)
    d='dm/gfx/vk_android/vka_draw.c'
    replace(root,d,
'''static int make_images(const vka_dstate *d, vka_shader *const sh[VKA_NSTAGE], int dry) {
    (void)d; int any = 0;''',
'''static int make_images(const vka_dstate *d, vka_shader *const sh[VKA_NSTAGE], int dry) {
    (void)d; int any = 0;
    // This is a pure preflight query; never change the order of actual image
    // creation after ending a pass. Keep the old query path on other GPUs or
    // when disabled for a same-settings A/B comparison.
    int fast = V.props.vendorID == 0x13B5u && VKA_ENV("DM_VK_DRAW_PREP_FAST", 1);''',check)
    replace(root,d,
'''&& (vka_tex_id_pending_rec(r[i].tid, r[i].dim) || (r[i].what == VKA_R_IMG && vka_tex_id_storage_pending(r[i].tid)))) {''',
'''&& (fast ? vka_tex_id_prepare_pending_rec(r[i].tid, r[i].dim, r[i].what == VKA_R_IMG)
                                                          : (vka_tex_id_pending_rec(r[i].tid, r[i].dim) || (r[i].what == VKA_R_IMG && vka_tex_id_storage_pending(r[i].tid))))) {''',check)
    # Sampled phase timings: separate the hot PT(2)->PT(3) section without per-draw logs.
    replace(root,d,
'''typedef struct { uint64_t pt[9], ps[6], n, tot; } dprof;''',
'''// Breakdown of the costly PT(2) images+pass+key phase; only 1 in 16
// draws by default. No extra GPU calls, locks, or heap allocations.
enum { DH_PREP, DH_HAZARD, DH_PASS, DH_MASK, DH_KEY, DH_N };
static uint64_t g_dhot[DH_N];
#define HOT_BEGIN() (g_prof ? cntvct() : 0)
#define HOT_END(i, t) do { if (g_prof) g_dhot[i] += cntvct() - (t); } while (0)
typedef struct { uint64_t pt[9], ps[6], n, tot; } dprof;''',check)
    replace(root,d,
'''    if (make_images(d, sh, 1)) { vka_rp_end(); make_images(d, sh, 0); }
    if (R.on && R.bar_pending''',
'''    uint64_t hot = HOT_BEGIN();
    if (make_images(d, sh, 1)) { vka_rp_end(); make_images(d, sh, 0); }
    HOT_END(DH_PREP, hot); hot = HOT_BEGIN();
    if (R.on && R.bar_pending''',check)
    replace(root,d,
'''    if (!rp_begin(rt, has_rt, sc, has_sc, d)) { g_skipped++; return; }
    if ((R.df || R.sf)''',
'''    HOT_END(DH_HAZARD, hot); hot = HOT_BEGIN();
    if (!rp_begin(rt, has_rt, sc, has_sc, d)) { g_skipped++; return; }
    HOT_END(DH_PASS, hot); hot = HOT_BEGIN();
    if ((R.df || R.sf)''',check)
    replace(root,d,
'''    tex_masks(sh, k.tex_u, k.tex_s);
    if (g_fs_sub)''',
'''    tex_masks(sh, k.tex_u, k.tex_s);
    HOT_END(DH_MASK, hot); hot = HOT_BEGIN();
    if (g_fs_sub)''',check)
    replace(root,d,
'''    PT(3);
    if (!mesh) vin_build_kept''',
'''    HOT_END(DH_KEY, hot);
    PT(3);
    if (!mesh) vin_build_kept''',check)
    replace(root,d,
'''    static dprof last; static uint64_t vk0, vb0, vk1, vb1, dh0, dm0, ds0;
    dprof d; dprof_take(&last, &d);''',
'''    static dprof last; static uint64_t vk0, vb0, vk1, vb1, dh0, dm0, ds0, hot0[DH_N];
    uint64_t h[DH_N]; for (int i = 0; i < DH_N; i++) { h[i] = g_dhot[i] - hot0[i]; hot0[i] = g_dhot[i]; }
    dprof d; dprof_take(&last, &d);''',check)
    replace(root,d,
'''        if (o < n) o += (size_t)snprintf(b + o, n - o, "; sets: walk %.2f, writes %.2f (%.1f images %.2f, driver segments %.2f), push %.2f)", d.ps[0] * us, d.ps[1] * us, d.ps[5] / (double)d.n, d.ps[4] * us, d.ps[3] * us, d.ps[2] * us);
    }
    if (o < n) o += (size_t)snprintf''',
'''        if (o < n) o += (size_t)snprintf(b + o, n - o, "; sets: walk %.2f, writes %.2f (%.1f images %.2f, driver segments %.2f), push %.2f)", d.ps[0] * us, d.ps[1] * us, d.ps[5] / (double)d.n, d.ps[4] * us, d.ps[3] * us, d.ps[2] * us);
        if (o < n) o += (size_t)snprintf(b + o, n - o, "; draw-hot us: prepare %.2f, hazards %.2f, pass %.2f, texmask %.2f, key %.2f", h[DH_PREP]*us, h[DH_HAZARD]*us, h[DH_PASS]*us, h[DH_MASK]*us, h[DH_KEY]*us);
    }
    if (o < n) o += (size_t)snprintf''',check)
    doc='docs/env_switches.tsv'
    replace(root,doc,
'''DM_VK_PREWARM\tswitch\t''',
'''DM_VK_DRAW_PREP_FAST\tswitch\t`=0` disables the Mali-G925 combined image/storage preflight (the old separate registry queries); default 1 on Arm vendor 0x13b5, off on other GPUs. Same image/view creation and pass ordering either way; source dm/gfx/vk_android/vka_draw.c and vka_tex.c.\nDM_VK_SLOT_POOL\tswitch\t`=0` uses the legacy command buffer pool instead of the experimental per-slot pools on Mali (source vka_exec.c).\nDM_VK_PREWARM\tswitch\t''',check)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('source',type=Path);a.add_argument('--check',action='store_true');ns=a.parse_args();main(ns.source,ns.check)
