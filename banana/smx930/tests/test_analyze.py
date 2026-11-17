import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse

ROOT=Path(__file__).resolve().parents[1]
class TestAnalyzer(unittest.TestCase):
    def test_black_screen(self):
        x=parse((ROOT/'tests/fixtures/black-screen.log').read_text())
        self.assertGreater(x['invalid_external_handle_errors'],0)
        self.assertFalse(x['target_met_on_observed_gameplay'])
        self.assertIn('NO_SUCCESSFUL_SWAPCHAIN_OBSERVED',x['flags'])
    def test_intro_not_gameplay(self):
        x=parse((ROOT/'tests/fixtures/faux-intro.log').read_text(), 'out of memory: Android closed it')
        self.assertTrue(x['intro_complete'])
        self.assertEqual(x['intro_fps_median'],30.0)
        self.assertEqual(x['post_intro_fps_samples'],0)
        self.assertEqual(x['peak_graphics_allocation_mib'],2491)
        self.assertFalse(x['target_met_on_observed_gameplay'])
    def test_measured_gameplay(self):
        s='[dm] [vk] swapchain 2960x1848, 5 images, format 37\n[dm] [codec] AV1 decoder 1: end of stream\n'
        s+='\n'.join(f'[dm] [vk] fps: {v}.0 game frames a second (20 ms), {v}.0 presented' for v in [50,50,50,50,50,50,50,50,50,50,51])
        x=parse(s)
        self.assertTrue(x['target_met_on_observed_gameplay'])
    def test_uncertain_crash_does_not_claim_lmkd(self):
        x=parse('[dm] [vk] swapchain 1x1, 3 images, format 37')
        self.assertNotIn('APP_DIGEST_REPORTS_OOM_NOT_PROVEN_BY_LOG',x['flags'])
        self.assertFalse(x['target_met_on_observed_gameplay'])
    def test_drops(self):
        x=parse('[dm] [nvn] on-screen up to frame 300: 270 frames, dropped 30 (discarded 0), p99 66.66 ms; footprint 4000 MiB')
        self.assertAlmostEqual(x['observed_drop_ratio'],0.1)
    def test_no_shader_default_automatic_promotion(self):
        x=parse('[dm] [vk] fps: 30.0 game frames a second (33.3 ms), 30.0 presented')
        self.assertFalse(x['target_met_on_observed_gameplay'])
        self.assertIn('INSUFFICIENT_GAMEPLAY_FPS_SAMPLES',x['flags'])
if __name__=='__main__':unittest.main()
