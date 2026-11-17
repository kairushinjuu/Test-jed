#!/usr/bin/env python3
"""Idempotent narrow draw binding scan optimization for pinned v0.12.1 source."""
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
f=a.root/'dm/gfx/vk_android/vka_draw.c'
s=f.read_text()
changes=[]
def replace(old,new,tag):
 global s
 if new in s: return
 if s.count(old)!=1: raise RuntimeError(f'{tag}: expected exactly one anchor, found {s.count(old)}')
 s=s.replace(old,new);changes.append(tag)
replace('static int g_inst_on;   // DM_VK_INSTANCE (the instanced runs below)', '''static int g_inst_on;   // DM_VK_INSTANCE (the instanced runs below)
// OOT/Mali: compact binding scans, not a cache of Vulkan/guest objects. A draw still walks guest
// bindings afresh, probes every referenced image for pending construction, and respects barriers.
// DM_VK_DRAW_FAST_SCAN=0 restores the original full descriptor loops for an A/B test.
static int g_draw_fast_scan = 1;''','flag')
replace('g_vattr_clear = VKA_ENV("DM_VK_VATTR_CLEAR", 1);', 'g_vattr_clear = VKA_ENV("DM_VK_VATTR_CLEAR", 1);\n    g_draw_fast_scan = VKA_ENV("DM_VK_DRAW_FAST_SCAN", 1);','init')
replace('static struct { int n[VKA_NSTAGE], pool[VKA_NSTAGE]; char why[VKA_NSTAGE][200]; vka_res r[VKA_NSTAGE][512]; } g_wk;', '''static struct {
    int n[VKA_NSTAGE], pool[VKA_NSTAGE]; char why[VKA_NSTAGE][200]; vka_res r[VKA_NSTAGE][512];
    // Indices, not copies: tex_masks can retype the descriptor's dim after walk_all.
    // The original order (each stage's images, then its buffer textures) is retained.
    uint16_t img_at[VKA_NSTAGE][512], tbuf_at[VKA_NSTAGE][512];
    uint16_t nimg[VKA_NSTAGE], ntbuf[VKA_NSTAGE];
    uint8_t writes[VKA_NSTAGE];
} g_wk;''','wk')
replace('''        g_wk.n[st] = vka_walk(&d->b, st, s->e, s->b, s->lib->h->ssbo_align, V.sb_align, rd_cb, NULL, g_wk.r[st], 512, &g_wk.pool[st], g_wk.why[st], sizeof g_wk.why[st]);
    }
    if (g_prof) g_ps[0] += cntvct() - t0_;''','''        g_wk.n[st] = vka_walk(&d->b, st, s->e, s->b, s->lib->h->ssbo_align, V.sb_align, rd_cb, NULL, g_wk.r[st], 512, &g_wk.pool[st], g_wk.why[st], sizeof g_wk.why[st]);
        // Build a per-draw compact index, never retaining the descriptor across draws or submissions.
        // All Vulkan handles and pending state are re-queried at actual use (make_images).
        if (g_draw_fast_scan && g_wk.n[st] > 0) for (int i = 0; i < g_wk.n[st]; i++) {
            const vka_res *r = &g_wk.r[st][i];
            if ((r->flags & DMSH_VK_BF_RW) || r->what == VKA_R_IMG || r->what == VKA_R_GMEM_LOG) g_wk.writes[st] = 1;
            if (!r->tid) continue;
            if (r->what == VKA_R_TEX || r->what == VKA_R_IMG) g_wk.img_at[st][g_wk.nimg[st]++] = (uint16_t)i;
            if (r->what == VKA_R_TEX) g_wk.tbuf_at[st][g_wk.ntbuf[st]++] = (uint16_t)i;
        }
    }
    if (g_prof) g_ps[0] += cntvct() - t0_;''','walk')
replace('''        vka_shader *s = sh[st]; g_wk.n[st] = 0; g_wk.pool[st] = 0; if (!s) continue;''','''        vka_shader *s = sh[st]; g_wk.n[st] = 0; g_wk.pool[st] = 0;
        g_wk.nimg[st] = g_wk.ntbuf[st] = 0; g_wk.writes[st] = 0;
        if (!s) continue;''','reset')
old='''        for (int i = 0; i < g_wk.n[st]; i++) if ((r[i].what == VKA_R_TEX || r[i].what == VKA_R_IMG) && r[i].tid
                                                 && (vka_tex_id_pending_rec(r[i].tid, r[i].dim) || (r[i].what == VKA_R_IMG && vka_tex_id_storage_pending(r[i].tid)))) {   // (an image remade with storage use copies its content: outside the pass)
            any = 1; if (dry) return 1;
            vka_tex_id_view(r[i].tid, g_cb, r[i].dim, wbf_view_of_binding(r[i].what == VKA_R_IMG, r[i].flags, DMSH_VK_BF_RW), NULL);
        }
        for (int i = 0; i < g_wk.n[st]; i++) if (r[i].what == VKA_R_TEX && r[i].tid && vka_tbuf_pending(r[i].tid, r[i].dim)) {   // a buffer texture read as an image: its copy (vka_tbuf.c), outside the pass
            any = 1; if (dry) return 1;
            vka_tbuf_refresh(r[i].tid, r[i].dim, g_cb);
        }'''
new='''        // The compact index omits non-texture bindings only. It must NOT remember pending
        // status: a prior draw/dispatch/texture upload may have changed texture residency.
        int ni = g_draw_fast_scan ? (int)g_wk.nimg[st] : g_wk.n[st];
        for (int j = 0; j < ni; j++) {
            int i = g_draw_fast_scan ? (int)g_wk.img_at[st][j] : j;
            if ((r[i].what == VKA_R_TEX || r[i].what == VKA_R_IMG) && r[i].tid
                && (vka_tex_id_pending_rec(r[i].tid, r[i].dim) || (r[i].what == VKA_R_IMG && vka_tex_id_storage_pending(r[i].tid)))) {
                any = 1; if (dry) return 1;
                vka_tex_id_view(r[i].tid, g_cb, r[i].dim, wbf_view_of_binding(r[i].what == VKA_R_IMG, r[i].flags, DMSH_VK_BF_RW), NULL);
            }
        }
        int nb = g_draw_fast_scan ? (int)g_wk.ntbuf[st] : g_wk.n[st];
        for (int j = 0; j < nb; j++) {
            int i = g_draw_fast_scan ? (int)g_wk.tbuf_at[st][j] : j;
            if (r[i].what == VKA_R_TEX && r[i].tid && vka_tbuf_pending(r[i].tid, r[i].dim)) {
                any = 1; if (dry) return 1;
                vka_tbuf_refresh(r[i].tid, r[i].dim, g_cb);
            }
        }'''
replace(old,new,'make_images')
replace('''        const vka_res *r = g_wk.r[st];
        for (int i = 0; i < g_wk.n[st]; i++) if ((r[i].flags & DMSH_VK_BF_RW) || r[i].what == VKA_R_IMG || r[i].what == VKA_R_GMEM_LOG) return 1;
    }
    return 0;
}
// After a game barrier''','''        if (g_draw_fast_scan) { if (g_wk.writes[st]) return 1; continue; }
        const vka_res *r = g_wk.r[st];
        for (int i = 0; i < g_wk.n[st]; i++) if ((r[i].flags & DMSH_VK_BF_RW) || r[i].what == VKA_R_IMG || r[i].what == VKA_R_GMEM_LOG) return 1;
    }
    return 0;
}
// After a game barrier''','writes')
if a.check:print('check OK; potential changes:',changes)
else:f.write_text(s);print('applied',changes)
