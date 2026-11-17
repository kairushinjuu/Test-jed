import os
from pathlib import Path
import subprocess
import unittest
ROOT=Path(os.environ.get('FAULTDIAG_SOURCE_ROOT',str(Path(__file__).resolve().parents[1]/'source')))
PATCH=Path(__file__).resolve().parent/'apply_faultdiag.py'
class FaultDiagTest(unittest.TestCase):
 def test_evict_optout_and_default(self):
  s=(ROOT/'dm/gfx/vk_android/vka_fileback.h').read_text()
  self.assertIn('DM_MEM_FILEBACK_EVICT',s)
  self.assertIn('return !e || strcmp(e, "0") != 0;',s)
  b=s[s.index('static inline void vkfb_drop('):s.index('// Anonymous [lo, lo + n) to the file',s.index('static inline void vkfb_drop('))]
  self.assertLess(b.index('sync_file_range'),b.index('if (vkfb_evict_enabled())'))
  self.assertIn('POSIX_FADV_DONTNEED',b)
 def test_bounded_sampling(self):
  s=(ROOT/'dm/gfx/vk_android/vka_mem.c').read_text()
  self.assertIn('if (nlog && fb_ru_ok && getrusage(RUSAGE_SELF, &fb_ru1) == 0)',s)
  self.assertIn('process-wide concurrent threads included',s)
 def test_idempotence(self):
  r=subprocess.run(['python3',str(PATCH),str(ROOT),'--check'],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr)
  self.assertIn('check OK 0',r.stdout)
