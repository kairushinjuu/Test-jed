import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse
class Test153541(unittest.TestCase):
 def test_encoder_wait_and_long_gpu_part(self):
  s="[dm] [vk] swapchain 300x400, 3 images\n[dm] [RED] vk: command encoder: the replay thread has waited 0.5 s for the encoder (tail 89871344, want 89871344, head 89871344, encoder awake, in record -1)\n[dm] [vk] GPU time: a part ran 212.0 ms (part 1 of 3 of a submission of frame 10196; the longest so far)\n[dm] [vk] pace cost up to frame 10198, a frame: recording 117.2 ms = draws 15.2 + commit 16.0 + other records 85.3; encoder calls ms (count): push descriptors 0.10 (399), dispatches 42.55 (27), part submits 0.31 (70)"
  r=parse(s);self.assertEqual(r['encoder_wait_watchdog'][0]['wait_s'],0.5);self.assertEqual(r['longest_gpu_part_ms'],212.);self.assertEqual(r['last_encoder_dispatch_cost_ms_per_frame'],42.55);self.assertIn('GPU_PART_OVER_200MS',r['flags'])
 def test_no_fabricated_data(self):
  r=parse('[dm] [vk] swapchain 300x400, 3 images');self.assertEqual(r['encoder_wait_watchdog'],[]);self.assertIsNone(r['longest_gpu_part_ms']);self.assertIsNone(r['last_encoder_dispatch_cost_ms_per_frame'])
if __name__=='__main__':unittest.main()
