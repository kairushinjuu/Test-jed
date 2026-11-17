#!/usr/bin/env python3
"""Semantic and source integrity checks for Mali one-lock readiness preflight.
Does not require Android game data, a Vulkan GPU, or network access.
"""
import os,random,sys,tempfile,shutil,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_drawopt import main
ROOT=Path(os.environ.get('SOURCE_ROOT','/mnt/data/smx930_drawopt/BananaNative-source'))
FILES=('dm/gfx/vk_android/vka.h','dm/gfx/vk_android/vka_tex.c','dm/gfx/vk_android/vka_draw.c','docs/env_switches.tsv')

# Logical states under a held g_tmu mutex: storage_able, holds and zero-shared
# are values read from the same mapped image in both implementations.
def old_result(reg,not_buffer_or_tbuf_disabled,map_present,im_present,storage,usage_storage,able,holds,zero):
    pending=bool(reg and not_buffer_or_tbuf_disabled and not map_present)
    if not storage or pending:return pending
    return bool(reg and map_present and im_present and ((not usage_storage and able and not holds) or zero))

def new_result(reg,not_buffer_or_tbuf_disabled,map_present,im_present,storage,usage_storage,able,holds,zero):
    if not reg:return False
    pending=bool(not_buffer_or_tbuf_disabled and not map_present)
    if storage and not pending and map_present and im_present:
        pending=bool((not usage_storage and able and not holds) or zero)
    return pending

class DrawOpt(unittest.TestCase):
    def test_truth_table_all_states(self):
        # Every combination of registry, presence, usage, alias ownership and flags.
        import itertools
        for bits in itertools.product((False,True),repeat=9):
            self.assertEqual(old_result(*bits),new_result(*bits),str(bits))
    def test_patch_is_idempotent_and_pinned(self):
        for f in FILES:self.assertTrue((ROOT/f).exists(),f)
        with tempfile.TemporaryDirectory() as d:
            for f in FILES:
                p=Path(d)/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy(ROOT/f,p)
            before={f:(Path(d)/f).read_bytes() for f in FILES}
            main(Path(d))
            self.assertEqual(before,{f:(Path(d)/f).read_bytes() for f in FILES})
    def test_no_barrier_change_and_mali_gate(self):
        code=(ROOT/'dm/gfx/vk_android/vka_draw.c').read_text()
        self.assertIn('V.props.vendorID == 0x13B5u && VKA_ENV("DM_VK_DRAW_PREP_FAST", 1)',code)
        self.assertIn('vka_rp_end(); make_images(d, sh, 0);',code)
        self.assertIn('vka_tex_id_pending_rec(r[i].tid, r[i].dim)',code)
        self.assertIn('vka_tex_id_storage_pending(r[i].tid)',code)
    def test_one_lock_and_no_mutations(self):
        c=(ROOT/'dm/gfx/vk_android/vka_tex.c').read_text()
        a=c.index('int vka_tex_id_prepare_pending_rec(')
        b=c.index('int vka_tex_id_storage_pending(',a)
        f=c[a:b]
        self.assertEqual(f.count('pthread_mutex_lock(&g_tmu)'),1)
        self.assertEqual(f.count('pthread_mutex_unlock(&g_tmu)'),1)
        self.assertIn('map_get(te->t.serial)',f)
        for unsafe in ('img_create(', 'img_storage_upgrade(', 'img_own(', 'vka_barrier(', 'vkCmd', 'vka_rp_end('):
            self.assertNotIn(unsafe,f)
    def test_profiler_is_sampled_and_has_phase_breakdown(self):
        c=(ROOT/'dm/gfx/vk_android/vka_draw.c').read_text()
        self.assertIn('if (g_prof) g_dhot[i] += cntvct() - (t)',c)
        self.assertIn('draw-hot us: prepare',c)
        for name in ('DH_PREP','DH_HAZARD','DH_PASS','DH_MASK','DH_KEY'):
            self.assertIn(f'HOT_END({name}',c)
        self.assertIn('g_prof_every = VKA_ENV("DM_VK_PACE_LOG", 5000)',c)
    def test_docs_include_reversible_flags(self):
        d=(ROOT/'docs/env_switches.tsv').read_text()
        self.assertIn('DM_VK_DRAW_PREP_FAST\tswitch\t',d)
        self.assertIn('DM_VK_SLOT_POOL\tswitch\t',d)

if __name__=='__main__':unittest.main()
