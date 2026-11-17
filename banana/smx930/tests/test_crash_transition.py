import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse
class TestCrashTransition(unittest.TestCase):
    def test_pipeline_and_gpu_transition(self):
        s='\n'.join([
         '[dm] [vk] swapchain 2960x1848, 5 images',
         '[dm] [codec] AV1 decoder 1: end of stream after 9252 pictures',
         '[dm] [vk] pace up to frame 10367 (5.1 s): interval 1 8 %, 3 92 %; 4.8 fps; GPU busy p50/p90 70.0/115.0 ms, recording start to GPU end p50/p90 128.4/733.0 ms; replay recording 165.0 ms a frame',
         '[dm] [longframe] frame 10343 (376.74 s) whole frame 27312.1 ms, new pipelines 72 + shader libraries 0, 24577.1 ms in all; texture uploads 244 first + 0 re-uploads, 321.6 MB / 924.2 ms; waits: GPU fences 27211.7, acquire 0.0; page faults 26078 major / 1897258 minor',
         '[dm] [vk] memory: placed pools 1225 MiB, images 1809 MiB (593), sparse tile blocks 0 MiB, scratch 96 MiB (6 blocks): 3130 MiB'])
        r=parse(s,'out of memory: Android closed it')
        self.assertEqual(r['after_movie_scene_windows'][0]['gpu_p50_ms'],70)
        self.assertEqual(r['after_movie_scene_windows'][0]['fps'],4.8)
        self.assertEqual(r['worst_longframe']['pipeline_creation_ms'],24577.1)
        self.assertEqual(r['worst_longframe']['major_faults'],26078)
        self.assertIn('GAMEPLAY_TRANSITION_GPU_OVER_50MS',r['flags'])
        self.assertIn('SCENE_TRANSITION_PIPELINES_OVER_10S',r['flags'])
        self.assertFalse(r['target_met_on_observed_gameplay'])
    def test_unchanged_intro_does_not_pass(self):
        s='[dm] [vk] pace up to frame 500 (5 s): interval 2 100 %; 30.0 fps; GPU busy p50/p90 2.0/3.8 ms, recording start to GPU end p50/p90 10/11 ms; replay recording 10 ms a frame'
        r=parse(s)
        self.assertFalse(r['after_movie_scene_windows'])
        self.assertFalse(r['target_met_on_observed_gameplay'])
    def test_small_drop_ratios_are_not_rounded_to_zero(self):
        s='[dm] [nvn] on-screen up to frame 10300: 10023 frames, dropped 31 (discarded 0), p99 66.69 ms; footprint 3100 MiB'
        r=parse(s)
        self.assertGreater(r['observed_drop_ratio'],0)
if __name__=='__main__':unittest.main()
