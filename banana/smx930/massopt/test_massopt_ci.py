"""Static and idempotence regression suite for an already patched Android tree.
SOURCE_ROOT must point at an actual pinned v0.8 tree after v0.12 massopt was applied.
"""
import os, unittest, tempfile, shutil, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from apply_massopt import main
ROOT=Path(os.environ.get('SOURCE_ROOT','/mnt/data/smx930_massopt/BananaNative-source'))
RELS=['android/app/src/main/java/dev/nxnative/android/MaliSmx930.java','dm/gfx/vk_android/vka.h','dm/gfx/vk_android/vka_exec.c','dm/gfx/vk_android/vka_pso.c','dm/gfx/vk_android/vka_dev.c']
class TestPatches(unittest.TestCase):
 def test_source_present_and_idempotent(self):
  self.assertTrue(all((ROOT/n).is_file() for n in RELS))
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for n in RELS:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
   before={n:(root/n).read_bytes() for n in RELS}
   main(root,False)
   self.assertEqual(before,{n:(root/n).read_bytes() for n in RELS})
 def test_slot_resets_only_after_wait(self):
  code=(ROOT/RELS[2]).read_text()
  wait=code.index('if (g_slot[k].vf_on)')
  reset=code.index('vk.vkResetCommandPool(V.dev, g_slot[k].pool, 0)')
  self.assertLess(wait,reset)
  self.assertIn('if (!g_slot_pool_mode) vk.vkResetCommandBuffer(cb, 0)',code)
  self.assertIn('vka_enc_sync();\n        VkResult rr',code)
 def test_flags_safe_disable(self):
  code=(ROOT/RELS[2]).read_text();j=(ROOT/RELS[0]).read_text()
  self.assertIn('VKA_ENV("DM_VK_SLOT_POOL", 0)',code)
  self.assertIn('"DM_VK_PREWARM_MAX=256"',j)
  self.assertIn('"DM_VK_PREWARM_MALI_MIN_MB=3072"',j)
 def test_no_driver_barrier_deletion(self):
  code=(ROOT/RELS[2]).read_text()
  self.assertIn('vk.vkCmdPipelineBarrier(g_cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_HOST_BIT',code)
 def test_prewarmer_conservative(self):
  s=(ROOT/RELS[3]).read_text()
  self.assertIn('VKA_ENV("DM_VK_PREWARM_MALI_MIN_MB", 0)',s)
  self.assertIn('if (floor_mb > 0 && avail_mb && avail_mb < (uint64_t)floor_mb)',s)
  self.assertIn('setpriority(PRIO_PROCESS, 0, 10)',s)
 def test_submit_logging_bounded(self):
  s=(ROOT/RELS[4]).read_text()
  self.assertIn('VKA_ENV("DM_VK_SUBMIT_TRACE", 0)',s)
  self.assertIn('if (budget > 2048) budget = 2048',s)
  self.assertIn('Mali submit trace:',s)
if __name__=='__main__': unittest.main()
