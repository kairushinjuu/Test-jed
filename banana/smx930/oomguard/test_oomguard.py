import os, subprocess, tempfile, unittest
from pathlib import Path
ROOT=Path(os.environ.get('OOMGUARD_SOURCE_ROOT','.'))
PATCH=Path(__file__).resolve().with_name('apply_oomguard.py')
class OomGuardTest(unittest.TestCase):
 def test_g925_default_and_override(self):
  s=(ROOT/'dm/gfx/vk_android/vka_pso.c').read_text()
  self.assertIn('strstr(V.props.deviceName, "G925")',s)
  self.assertIn('VKA_ENV("DM_VK_PSO_SLOTS", gate_g925() ? 1',s)
 def test_burst_probes_not_per_frame(self):
  s=(ROOT/'dm/gfx/vk_android/vka_tex.c').read_text()
  self.assertIn('if (due_burst && (g_img_burst_refreshes <= 8 || !(g_img_burst_refreshes & 15)))',s)
  self.assertIn('oomguard residency:',s)
 def test_compiled_mem_parser(self):
  code=r'''#define _GNU_SOURCE
#include "vka_oomdiag.h"
#include <assert.h>
int main(void) {
 char s[]="Rss: 10240 kB\nPss: 5120 kB\nAnonymous: 3072 kB\nSwap: 128 kB\n";
 FILE *f=fmemopen(s,sizeof(s)-1,"r");assert(f);
 vko_resident r=vko_parse_rollup(f);fclose(f);
 assert(r.valid && r.rss_kb==10240 && r.pss_kb==5120 && r.anon_kb==3072 && r.swap_kb==128);
 return 0;
}'''
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'t.c';p.write_text(code);exe=Path(d)/'run'
   subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I',str(ROOT/'dm/gfx/vk_android'),str(p),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
 def test_patcher_idempotent(self):
  r=subprocess.run(['python3',str(PATCH),str(ROOT),'--check'],capture_output=True,text=True)
  self.assertEqual(0,r.returncode,r.stderr)
  self.assertIn('check OK 0',r.stdout)
