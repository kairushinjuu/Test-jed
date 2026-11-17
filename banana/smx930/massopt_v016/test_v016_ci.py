"""SM-X930 Mali v0.16 source behavior smoke tests and idempotence.
These cannot substitute for GPU execution and a measured FPS win.
"""
import os,sys,tempfile,shutil,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_v016 import patch
ROOT=Path(os.environ.get('SOURCE_ROOT','/mnt/data/smx930_v016/BananaNative-source'))
FILES=['dm/gfx/vk_android/vka_draw.c','dm/gfx/vk_android/vka_tex.c','android/app/src/main/java/dev/nxnative/android/MaliSmx930.java']
class TestMaliV016(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.draw=(ROOT/FILES[0]).read_text();cls.tex=(ROOT/FILES[1]).read_text();cls.java=(ROOT/FILES[2]).read_text()
    def test_patcher_idempotent_on_actual_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for f in FILES:
                (root/f).parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(ROOT/f,root/f)
            before={f:(root/f).read_bytes() for f in FILES}
            patch(root,False)
            self.assertEqual(before,{f:(root/f).read_bytes() for f in FILES})
    def test_no_unvalidated_memo_on_gpu_mutated_ubo_handles(self):
        for kind in ('SBUF_UBO','TEX_UBO','IMG_UBO','SAMP_UBO'):
            self.assertIn('b->kind == DMSH_VK_KIND_'+kind,self.draw)
        self.assertIn('b->skind == DMSH_VK_KIND_SAMP_UBO',self.draw)
    def test_exact_snapshot_key_includes_cpu_bound_resources(self):
        for req in ('m->ssbo_stamp == d->s_ssbo[st]','m->tex_stamp == d->s_tex[st]',
                    'm->tex_base == d->b.tex_base','m->samp_base == d->b.samp_base',
                    '!memcmp(m->ubo, d->b.ubo[st], sizeof m->ubo)',
                    'm->shader == s','m->entry == s->e','m->bindings == s->b'):
            self.assertIn(req,self.draw)
    def test_cache_copies_records_before_view_class_mutation(self):
        self.assertLess(self.draw.index('memcpy(m->r, g_wk.r[st]'),self.draw.index('static void tex_masks('))
        self.assertLess(self.draw.index('walk_all(d, sh);'),self.draw.index('    tex_masks(sh, k.tex_u, k.tex_s);'))
    def test_cache_is_opt_in_with_mali_vendor_guard(self):
        self.assertIn('V.props.vendorID == 0x13B5u && VKA_ENV("DM_VK_BIND_WALK_MEMO", 0)',self.draw)
        self.assertIn('"DM_VK_BIND_WALK_MEMO=1"',self.java)
    def test_no_memo_of_refused_walks(self):
        self.assertIn('g_wk.n[st] >= 0 && g_wk.n[st] <= 512',self.draw)
        self.assertIn('m->valid = 0;',self.draw)
    def test_burst_refresh_does_not_touch_other_gpu_or_fixed_limit(self):
        self.assertIn('V.props.vendorID == 0x13B5u ? VKA_ENV("DM_VK_IMG_BURST_REFRESH_MB", 0) : 0',self.tex)
        self.assertIn('env > 0 || burst_mb <= 0',self.tex)
        self.assertIn('now_ - g_mali_lim_ns < 100000000ull',self.tex)
        self.assertIn('"DM_VK_IMG_BURST_REFRESH_MB=128"',self.java)
    def test_memory_policy_still_guards_live_and_gpu_images(self):
        for req in ('vktl_evictable(', 'vktl_skip_ws(', 'vktl_guard_ws(', 'im->last_fence && done_fence < im->last_fence'):
            self.assertIn(req,self.tex)
        self.assertIn('img_limit_update(cur_frame);',self.tex)
    def test_trace_reports_all_three_components(self):
        for x in ('g_mali_phase[0]','g_mali_phase[1]','g_mali_phase[2]',
                  'Mali PT2 (us/draw): walk', 'images+hazards+pass','key %.2f'):
            self.assertIn(x,self.draw)
    def test_keep_original_driver_and_shader_quality(self):
        self.assertIn('"DM_VK_PREWARM=1"',self.java) # Override remains user-controlled
        self.assertIn('"DM_VK_SLOT_POOL=0"',self.java)
        self.assertIn('vka_tex_id_pending_rec',self.draw)
        self.assertIn('vka_tex_id_storage_pending',self.draw)
        self.assertIn('if (!rp_begin(rt, has_rt, sc, has_sc, d))',self.draw)
if __name__=='__main__':unittest.main()
