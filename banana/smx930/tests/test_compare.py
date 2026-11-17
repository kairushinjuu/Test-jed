import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compare import compare

class TestCompare(unittest.TestCase):
    def runmeta(self,fps=50):
        return {'game_title_id':'0400486024DEC000','gpu':'Mali-G925-Immortalis MC12','environment':{'DM_GRAPHICS_SCALE':'2','DM_VK_NDSR':'4'},'driver':'faux123','post_intro_fps_samples':20,'post_intro_median_fps':fps,'target_met_on_observed_gameplay':fps>=50}
    def test_comparable(self):
        r=compare(self.runmeta(42),self.runmeta(50))
        self.assertTrue(r['comparable']);self.assertEqual(r['median_gameplay_fps_change_pct'],19.05)
    def test_prevent_quality_regression(self):
        b=self.runmeta(50);b['environment']['DM_GRAPHICS_SCALE']='3'
        self.assertFalse(compare(self.runmeta(45),b)['comparable'])
    def test_driver_not_comparable(self):
        b=self.runmeta();b['driver']='another'
        self.assertFalse(compare(self.runmeta(),b)['comparable'])
    def test_no_gameplay_data(self):
        b=self.runmeta();b['post_intro_fps_samples']=0
        self.assertFalse(compare(self.runmeta(),b)['comparable'])
