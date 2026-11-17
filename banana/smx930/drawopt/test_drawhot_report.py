import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from drawhot_report import analyze
class DrawHotParser(unittest.TestCase):
 def test_window_and_order(self):
  x=analyze('[vk] pace cost up to frame 12: draw-hot us: prepare 12.10, hazards 3.40, pass 50.00, texmask 9.00, key 1.00\n')
  self.assertEqual(x['sample_windows'],1)
  self.assertEqual(x['largest_median_phase'],'pass')
  self.assertEqual(x['median_microseconds_per_sampled_draw_by_phase']['prepare'],12.10)
 def test_missing_data_is_unknown(self):
  x=analyze('old build lacks profile')
  self.assertIsNone(x['median_microseconds_per_sampled_draw_by_phase'])
  self.assertIsNone(x['largest_median_phase'])
if __name__=='__main__':unittest.main()
