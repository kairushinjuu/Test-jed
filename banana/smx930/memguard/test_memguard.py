import pathlib, tempfile, subprocess, sys, unittest
SCRIPT = pathlib.Path(__file__).with_name("apply_memguard.py")
BASE = '''package dev.nxnative.android;
final class MaliSmx930 {
  static final String[] STABLE = {
        "DM_VK_PREWARM=1",
        "DM_MEM_FILEBACK_KINDS=shader,texture",
        "DM_VK_IMG_DIAG=10",
        "DM_VK_SLOT_POOL=1"
  };
}'''
class TestMemGuard(unittest.TestCase):
    def test_patcher_and_idempotence(self):
        with tempfile.TemporaryDirectory() as t:
            p=pathlib.Path(t)/"android/app/src/main/java/dev/nxnative/android/MaliSmx930.java"
            p.parent.mkdir(parents=True)
            p.write_text(BASE)
            subprocess.run([sys.executable,str(SCRIPT),t,"--check"],check=True)
            assert p.read_text()==BASE
            subprocess.run([sys.executable,str(SCRIPT),t],check=True)
            s=p.read_text()
            for entry in ("DM_VK_PREWARM=0","DM_MEM_FILEBACK_KINDS=shader","DM_VK_PRUNE_MS=2","DM_MOVIE_SKIP=1","DM_VK_IMG_DIAG=5"):
                self.assertIn(entry,s)
            self.assertNotIn("DM_MEM_FILEBACK_KINDS=shader,texture",s)
            subprocess.run([sys.executable,str(SCRIPT),t],check=True)
            self.assertEqual(s,p.read_text())
if __name__ == "__main__": unittest.main()
