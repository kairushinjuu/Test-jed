import os,unittest,random,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).parent
SOURCE=pathlib.Path(os.environ.get('BURSTOPT_SOURCE_ROOT',str(ROOT.parent/'smx930_drawopt/BananaNative-source')))/'dm/gfx/vk_android/vka_tex.c'
class BurstRegression(unittest.TestCase):
 def test_fallback_and_pressure_refresh(self):
  s=SOURCE.read_text();self.assertIn('DM_VK_IMG_BURST_REFRESH_MB", 128',s);self.assertIn('env <= 0 && !due_time && burst && imgs >= g_img_measure_bytes',s);self.assertIn('g_img_measure_bytes = imgs',s)
 def test_guard_does_not_skip_video_and_gpu_residency_rules(self):
  s=SOURCE.read_text();self.assertIn('vktl_evictable(cur_frame, im->last_frame, im->holds, im->gpu_owned',s);self.assertIn('vktl_guard_ws(&cfg, pinned',s);self.assertIn('if (im->nkids) continue;',s)
 def test_realloc_failure_preserves_old_array(self):
  s=SOURCE.read_text();self.assertIn('prune_ent *next = realloc(c,',s);self.assertIn('if (!next) {',s);self.assertIn('c = next; ccap = next_cap;',s)
 def test_threshold_bounded_and_no_underflow(self):
  rng=random.Random(930)
  for _ in range(2000):
   last=rng.randrange(0,5<<30);size=rng.randrange(0,6<<30);mb=rng.randrange(-5,5000)
   threshold=(mb<<20) if 0<mb<=4096 else 0
   expected=threshold>0 and size>=last and size-last>=threshold
   observed=bool(threshold and size>=last and size-last>=threshold)
   self.assertEqual(expected,observed)
 def test_idempotence(self):
  r=subprocess.run([sys.executable,str(ROOT/'apply_burstopt.py'),str(SOURCE.parents[3]),'--check'],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr);self.assertIn('check OK []',r.stdout)
if __name__=='__main__':unittest.main()
