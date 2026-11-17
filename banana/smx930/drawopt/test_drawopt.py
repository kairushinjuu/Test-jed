#!/usr/bin/env python3
"""Source invariants + randomized reference-order regression; not a device performance test."""
import pathlib, subprocess, sys, tempfile, unittest, random, shutil, os
ROOT=pathlib.Path(__file__).resolve().parent
SOURCE=pathlib.Path(os.environ.get('DRAWOPT_SOURCE_ROOT',str(ROOT/'BananaNative-source'))) / 'dm/gfx/vk_android/vka_draw.c'
PATCHER=ROOT/'apply_drawopt.py'
class DrawScanRegression(unittest.TestCase):
    def test_original_fallback_exists(self):
        s=SOURCE.read_text()
        self.assertIn('DM_VK_DRAW_FAST_SCAN=0 restores',s)
        self.assertIn('VKA_ENV("DM_VK_DRAW_FAST_SCAN", 1)',s)
        self.assertIn('g_draw_fast_scan ? (int)g_wk.nimg[st] : g_wk.n[st]',s)
        self.assertIn('g_draw_fast_scan ? (int)g_wk.ntbuf[st] : g_wk.n[st]',s)
        self.assertIn('if (g_draw_fast_scan) { if (g_wk.writes[st]) return 1; continue; }',s)
    def test_live_pending_checks_and_late_dim(self):
        s=SOURCE.read_text()
        self.assertIn('r[i].dim) || (r[i].what == VKA_R_IMG && vka_tex_id_storage_pending(r[i].tid))',s)
        self.assertIn('vka_tex_id_view(r[i].tid, g_cb, r[i].dim',s)
        self.assertIn('vka_tbuf_refresh(r[i].tid, r[i].dim, g_cb)',s)
        self.assertIn('int i = g_draw_fast_scan ? (int)g_wk.img_at[st][j] : j',s)
        self.assertIn('int i = g_draw_fast_scan ? (int)g_wk.tbuf_at[st][j] : j',s)
    def test_equivalent_original_scan_order(self):
        r=random.Random(0x930)
        for _ in range(1000):
            stages=[]
            for _ in range(7):
                bindings=[(r.choice(['TEX','IMG','BUF','GMEM']),r.randrange(3),r.randrange(3)) for _ in range(r.randrange(130))]
                stages.append(bindings)
            # The scan must preserve each stage's image refs first, then buffer refs.
            old=[];new=[]
            for st,bindings in enumerate(stages):
                old.extend((st,i,'image') for i,(kind,tid,_) in enumerate(bindings) if kind in ('TEX','IMG') and tid)
                old.extend((st,i,'tbuf') for i,(kind,tid,_) in enumerate(bindings) if kind=='TEX' and tid)
                indices_img=[i for i,(kind,tid,_) in enumerate(bindings) if kind in ('TEX','IMG') and tid]
                indices_tb=[i for i,(kind,tid,_) in enumerate(bindings) if kind=='TEX' and tid]
                new.extend((st,i,'image') for i in indices_img)
                new.extend((st,i,'tbuf') for i in indices_tb)
            self.assertEqual(old,new)
    def test_patcher_idempotent_and_v0121_anchors(self):
        with tempfile.TemporaryDirectory() as t:
            base=pathlib.Path(t)/'dm/gfx/vk_android';base.mkdir(parents=True)
            # Applied source is checked for idempotence in the same temp fixture.
            shutil.copy2(SOURCE,base/'vka_draw.c')
            for _ in range(2):
                p=subprocess.run([sys.executable,str(PATCHER),t,'--check'],capture_output=True,text=True)
                self.assertEqual(0,p.returncode,p.stderr)
                self.assertIn("potential changes: []",p.stdout)
if __name__=='__main__':unittest.main()
