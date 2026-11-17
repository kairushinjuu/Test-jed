import unittest
from pathlib import Path
class TestCollector(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.script=(Path(__file__).resolve().parents[1]/"tools/collect-adb.sh").read_text()
    def test_exact_lab_package(self):
        self.assertIn("PKG='dev.nxnative.android.malig925lab'",self.script)
        self.assertIn('SM-X930',self.script)
        self.assertIn('"$ADB" shell dumpsys meminfo "$PKG:game"',self.script)
    def test_filtered_live_lmkd_capture(self):
        self.assertIn('killtrace-live.txt',self.script)
        self.assertIn('killtrace-tail.txt',self.script)
        self.assertIn("'lmkd:*'",self.script)
        self.assertNotIn('logcat -d -v threadtime >',self.script)
    def test_collector_does_not_mutate_device(self):
        for bad in ('logcat -c','pm uninstall','pm clear','rm -rf','adb reboot'):
            self.assertNotIn(bad,self.script)
if __name__=='__main__':unittest.main()
