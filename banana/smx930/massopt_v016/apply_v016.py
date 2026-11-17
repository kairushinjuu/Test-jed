#!/usr/bin/env python3
"""SM-X930 v0.16: opt-in exact-binding walk cache, burst-aware image memory policy, per-draw subprofiler.
Only for pinned and already MassOpt-v0.12.1-patched source. Refuses unknown trees.
"""
from pathlib import Path
import argparse

def change(root,rel,old,new,check=False):
    p=root/rel
    s=p.read_text()
    if s.count(new)==1:
        print('already patched',rel);return
    if s.count(old)!=1:
        raise ValueError(f'{rel}: expected exactly 1 anchor; got {s.count(old)}')
    if not check: p.write_text(s.replace(old,new,1))
    print('check' if check else 'patched',rel)

def patch(root,check=False):
    r='dm/gfx/vk_android/vka_draw.c'
    old='''static struct { int n[VKA_NSTAGE], pool[VKA_NSTAGE]; char why[VKA_NSTAGE][200]; vka_res r[VKA_NSTAGE][512]; } g_wk;
static void walk_all(const vka_dstate *d, vka_shader *const sh[VKA_NSTAGE]) {
    uint64_t t0_ = g_prof ? cntvct() : 0;
    vka_texu_elem = VKA_ENV("DM_VK_TEXU_ELEM", 1);   // see vka_bind.h (live, A/B)
    for (int st = 0; st < VKA_NSTAGE; st++) {
        vka_shader *s = sh[st]; g_wk.n[st] = 0; g_wk.pool[st] = 0; if (!s) continue;
        g_wk.n[st] = vka_walk(&d->b, st, s->e, s->b, s->lib->h->ssbo_align, V.sb_align, rd_cb, NULL, g_wk.r[st], 512, &g_wk.pool[st], g_wk.why[st], sizeof g_wk.why[st]);
    }
    if (g_prof) g_ps[0] += cntvct() - t0_;
}'''
    new='''static struct { int n[VKA_NSTAGE], pool[VKA_NSTAGE]; char why[VKA_NSTAGE][200]; vka_res r[VKA_NSTAGE][512]; } g_wk;
// A per-stage, single-entry memo of *binding records*, not of image objects/views.
// The walk has no Vulkan side effects. It is safe to reuse only when descriptors
// are determined entirely by the recorded bind state. UBO-indirect texture,
// image, sampler and storage-buffer handles can change through GPU/guest writes
// WITHOUT a bind record, so those shaders always take the original walk.
// Cache the unmodified records BEFORE tex_masks() adds view-class flags.
typedef struct {
    int valid, static_checked, static_bindings, n, pool, tex_base, samp_base, texu;
    uint64_t ssbo_stamp, tex_stamp;
    const vka_shader *shader;
    const dmsh_vk_entry *entry;
    const dmsh_vk_bind *bindings;
    vka_range ubo[16];
    char why[200];
    vka_res r[512];
} mali_walk_memo;
static mali_walk_memo g_mali_walk[VKA_NSTAGE];
static uint64_t g_mali_walk_hits, g_mali_walk_miss, g_mali_walk_dynamic;
static int mali_walk_static(const vka_shader *s) {
    for (unsigned i = 0; i < s->e->bind_count; i++) {
        const dmsh_vk_bind *b = &s->b[i];
        if (b->kind == DMSH_VK_KIND_SBUF_UBO || b->kind == DMSH_VK_KIND_TEX_UBO ||
            b->kind == DMSH_VK_KIND_IMG_UBO || b->kind == DMSH_VK_KIND_SAMP_UBO ||
            b->skind == DMSH_VK_KIND_SAMP_UBO) return 0;
    }
    return 1;
}
static void walk_all(const vka_dstate *d, vka_shader *const sh[VKA_NSTAGE]) {
    uint64_t t0_ = g_prof ? cntvct() : 0;
    vka_texu_elem = VKA_ENV("DM_VK_TEXU_ELEM", 1);   // see vka_bind.h (live, A/B)
    const int use_memo = V.props.vendorID == 0x13B5u && VKA_ENV("DM_VK_BIND_WALK_MEMO", 0);
    for (int st = 0; st < VKA_NSTAGE; st++) {
        vka_shader *s = sh[st]; g_wk.n[st] = 0; g_wk.pool[st] = 0; if (!s) continue;
        mali_walk_memo *m = &g_mali_walk[st];
        // Shader binding layouts are immutable for this source version. Classify
        // once per stage/shader, rather than walking the layout to check it on
        // every draw. A new shader or descriptor layout invalidates the memo.
        if (use_memo && (!m->static_checked || m->shader != s || m->entry != s->e || m->bindings != s->b)) {
            m->valid = 0; m->shader = s; m->entry = s->e; m->bindings = s->b;
            m->static_bindings = mali_walk_static(s); m->static_checked = 1;
        }
        int eligible = use_memo && m->static_bindings;
        if (eligible && m->valid && m->shader == s && m->entry == s->e && m->bindings == s->b &&
            m->ssbo_stamp == d->s_ssbo[st] && m->tex_stamp == d->s_tex[st] &&
            m->tex_base == d->b.tex_base && m->samp_base == d->b.samp_base &&
            m->texu == vka_texu_elem && !memcmp(m->ubo, d->b.ubo[st], sizeof m->ubo)) {
            g_wk.n[st] = m->n; g_wk.pool[st] = m->pool;
            memcpy(g_wk.r[st], m->r, (size_t)m->n * sizeof m->r[0]);
            memcpy(g_wk.why[st], m->why, sizeof m->why);
            g_mali_walk_hits++;
            continue;
        }
        g_wk.n[st] = vka_walk(&d->b, st, s->e, s->b, s->lib->h->ssbo_align, V.sb_align, rd_cb, NULL, g_wk.r[st], 512, &g_wk.pool[st], g_wk.why[st], sizeof g_wk.why[st]);
        if (use_memo && !eligible) g_mali_walk_dynamic++;
        else if (eligible) {
            g_mali_walk_miss++;
            // Never memoize invalid/unbounded walks; the caller must see the error again.
            if (g_wk.n[st] >= 0 && g_wk.n[st] <= 512) {
                m->valid = 0;
                m->shader = s; m->entry = s->e; m->bindings = s->b;
                m->ssbo_stamp = d->s_ssbo[st]; m->tex_stamp = d->s_tex[st];
                m->tex_base = d->b.tex_base; m->samp_base = d->b.samp_base;
                m->texu = vka_texu_elem; m->n = g_wk.n[st]; m->pool = g_wk.pool[st];
                memcpy(m->ubo, d->b.ubo[st], sizeof m->ubo);
                memcpy(m->r, g_wk.r[st], (size_t)m->n * sizeof m->r[0]);
                memcpy(m->why, g_wk.why[st], sizeof m->why);
                m->valid = 1;
            } else m->valid = 0;
        }
    }
    if (g_prof) g_ps[0] += cntvct() - t0_;
}'''
    change(root,r,old,new,check)
    # Cache-stat telemetry added to existing low-cost pace line rather than logging every draw.
    old='''    if (o < n) o += (size_t)snprintf(b + o, n - o, "%svertex input kept %.0f %% (DM_VK_VIN_SKIP), vertex buffers kept %.0f %%, driver segments %.0f %% by their inputs (DM_VK_DRV_STAMP) of %.0f %% bound again",
                                      o ? "; " : "", vk + vb ? 100.0 * vk / (double)(vk + vb) : 0.0, bk + bb ? 100.0 * bk / (double)(bk + bb) : 0.0, dh ? 100.0 * ds / (double)dh : 0.0, dh + dm ? 100.0 * dh / (double)(dh + dm) : 0.0);
}'''
    new='''    if (o < n) o += (size_t)snprintf(b + o, n - o, "%svertex input kept %.0f %% (DM_VK_VIN_SKIP), vertex buffers kept %.0f %%, driver segments %.0f %% by their inputs (DM_VK_DRV_STAMP) of %.0f %% bound again",
                                      o ? "; " : "", vk + vb ? 100.0 * vk / (double)(vk + vb) : 0.0, bk + bb ? 100.0 * bk / (double)(bk + bb) : 0.0, dh ? 100.0 * ds / (double)dh : 0.0, dh + dm ? 100.0 * dh / (double)(dh + dm) : 0.0);
    static uint64_t wh, wm, wd;
    uint64_t h = g_mali_walk_hits - wh, m = g_mali_walk_miss - wm, dyn = g_mali_walk_dynamic - wd;
    wh = g_mali_walk_hits; wm = g_mali_walk_miss; wd = g_mali_walk_dynamic;
    if ((h || m || dyn) && o < n)
        o += (size_t)snprintf(b + o, n - o, "; Mali binding walk reused %llu/%llu eligible stages, %llu dynamic-UBO stages walked (DM_VK_BIND_WALK_MEMO)",
                              (unsigned long long)h, (unsigned long long)(h + m), (unsigned long long)dyn);
    static uint64_t prev[3];
    uint64_t sub[3]; for (int i = 0; i < 3; i++) { sub[i] = g_mali_phase[i] - prev[i]; prev[i] = g_mali_phase[i]; }
    if (d.n && o < n) { double us = tick_us() / (double)d.n;
        o += (size_t)snprintf(b + o, n - o, "; Mali PT2 (us/draw): walk %.2f, images+hazards+pass %.2f, key %.2f",
                              sub[0] * us, sub[1] * us, sub[2] * us);
    }
}'''
    # forward declare phase timing before vka_draw_pace
    old2='''typedef struct { uint64_t pt[9], ps[6], n, tot; } dprof;'''
    new2='''static uint64_t g_mali_phase[3];  // sampled draw PT2: walk, images/hazards/render-pass, pipeline key
// No guest or GPU state is memoized by these counters.
typedef struct { uint64_t pt[9], ps[6], n, tot; } dprof;'''
    change(root,r,old2,new2,check)
    change(root,r,old,new,check)
    old='''    PT(2);
    walk_all(d, sh);'''
    new='''    PT(2);
    uint64_t mali_pt2 = g_prof ? cntvct() : 0;
    walk_all(d, sh);
    if (g_prof) { uint64_t now_ = cntvct(); g_mali_phase[0] += now_ - mali_pt2; mali_pt2 = now_; }'''
    change(root,r,old,new,check)
    old='''    if (!rp_begin(rt, has_rt, sc, has_sc, d)) { g_skipped++; return; }
    if ((R.df || R.sf) && !R.dread && depth_sampled(sh, d)) R.dread = 1;'''
    new='''    if (!rp_begin(rt, has_rt, sc, has_sc, d)) { g_skipped++; return; }
    if (g_prof) { uint64_t now_ = cntvct(); g_mali_phase[1] += now_ - mali_pt2; mali_pt2 = now_; }
    if ((R.df || R.sf) && !R.dread && depth_sampled(sh, d)) R.dread = 1;'''
    change(root,r,old,new,check)
    old='''    PT(3);
    if (!mesh) vin_build_kept(d, sh[0], &k);'''
    new='''    if (g_prof) g_mali_phase[2] += cntvct() - mali_pt2;
    PT(3);
    if (!mesh) vin_build_kept(d, sh[0], &k);'''
    change(root,r,old,new,check)
    r='dm/gfx/vk_android/vka_tex.c'
    old='''static uint64_t g_img_lim, g_lim_frame, g_prune_dry, g_img_ws;   // g_img_ws: the working set at the last limit update (vktl_in ws_bytes)'''
    new='''static uint64_t g_img_lim, g_lim_frame, g_prune_dry, g_img_ws;   // g_img_ws: the working set at the last limit update (vktl_in ws_bytes)
static uint64_t g_mali_lim_images, g_mali_lim_ns;  // burst-sensitive refresh, never a new eviction policy'''
    change(root,r,old,new,check)
    old='''    g_img_pinned = env > 0;
    if (g_img_lim && cur_frame < g_lim_frame + (g_psi.pressed ? 15 : 60)) return;
    g_lim_frame = cur_frame;
    uint64_t imgs = g_img_bytes + vka_imem_zbytes();'''
    new='''    g_img_pinned = env > 0;
    uint64_t imgs = g_img_bytes + vka_imem_zbytes();
    if (g_img_lim && cur_frame < g_lim_frame + (g_psi.pressed ? 15 : 60)) {
        // A first 3D scene can allocate >1 GiB within 13 frames (SM-X930).
        // Its old 60-frame cache limit is then stale while MemAvailable falls.
        // Remeasure after a bounded large burst; normal frames pay no /proc I/O.
        int burst_mb = V.props.vendorID == 0x13B5u ? VKA_ENV("DM_VK_IMG_BURST_REFRESH_MB", 0) : 0;
        uint64_t now_ = now_ns();
        if (env > 0 || burst_mb <= 0 || burst_mb > 2048 ||
            imgs < g_mali_lim_images || imgs - g_mali_lim_images < (uint64_t)burst_mb * 1048576ull ||
            now_ < g_mali_lim_ns || now_ - g_mali_lim_ns < 100000000ull) return;
    }
    g_lim_frame = cur_frame;
    g_mali_lim_images = imgs; g_mali_lim_ns = now_ns();'''
    change(root,r,old,new,check)
    r='android/app/src/main/java/dev/nxnative/android/MaliSmx930.java'
    old='''        "DM_VK_IMG_DIAG=10",            // periodic diagnostic samples, not every frame
        "DM_VK_SLOT_POOL=1"             // Mali per-slot pool reset avoids repetitive individual buffer resets'''
    new='''        "DM_VK_IMG_DIAG=10",            // periodic diagnostic samples, not every frame
        "DM_VK_IMG_BURST_REFRESH_MB=128", // remeasure cache budget during rapid first-scene allocations
        "DM_VK_BIND_WALK_MEMO=1",       // cache only bindings with no dynamic UBO-derived resource handles
        "DM_VK_SLOT_POOL=0"             // default off until Mali driver correctness is proven'''
    change(root,r,old,new,check)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('root',type=Path);a.add_argument('--check',action='store_true');x=a.parse_args();patch(x.root,x.check)
