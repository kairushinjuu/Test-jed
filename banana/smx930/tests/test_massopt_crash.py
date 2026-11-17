import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse

class MassOptCrashTests(unittest.TestCase):
    def sample(self):
        return "\n".join([
          '[dm] [vk] swapchain 2960x1848, 5 images',
          '[dm] [vk] prewarm: 150 of 3456 pipeline keys in 45.9 s on 1 threads: 150 made, 0 already there, 0 dropped',
          '[dm] [vk] Mali prewarm: stopped at 3030 MiB MemAvailable (floor 3072 MiB); game work takes priority',
          '[dm] [RED] audio #0: the AAudio stream did not stop (state AAUDIO_STREAM_STATE_DISCONNECTED): closing it',
          '[dm] [codec] AV1 decoder 1: end of stream after 9252 pictures',
          '[dm] [vk] pipeline cache: 20915012 bytes written to /some/private/file (260 pipelines made this run), prewarm list 0 keys, 30 ms',
          '[dm] [vk] pace up to frame 10472 (33.1 s): interval 2 93 %, 3 7 %; 3.7 fps; GPU busy p50/p90 1.6/2.4 ms, recording start to GPU end p50/p90 13.4/16.0 ms; replay recording 247.3 ms a frame (its CPU 236.0), 112 draws',
          '[dm] [vk] pace cost up to frame 10472, a frame: recording 247.3 ms = draws 4.9 + commit 13.0 + other records 228.6; all queue submits 6.1 a frame'
        ])
    def test_finds_real_causes_without_inventing_oom(self):
        r=parse(self.sample(),'-- verdict\n killed by Android: Android closed it without saying why.')
        self.assertEqual(r['massopt_prewarm_progress']['made'],150)
        self.assertEqual(r['massopt_prewarm_stop']['threshold_mib'],3072)
        self.assertEqual(r['aaudio_disconnections'],1)
        self.assertEqual(r['massopt_saved_pipeline_cache']['made_in_run'],260)
        self.assertEqual(r['after_movie_scene_windows'][0]['replay_cpu_ms'],236.0)
        self.assertEqual(r['after_movie_replay_other_records_ms'],228.6)
        self.assertIn('GAMEPLAY_REPLAY_CPU_OVER_100MS',r['flags'])
        self.assertIn('ANDROID_CLOSED_CAUSE_UNCONFIRMED',r['flags'])
        self.assertFalse(r['digest_oom_classification'])
    def test_missing_stats_remain_unknown(self):
        r=parse('[dm] [vk] swapchain 800x600, 3 images')
        self.assertIsNone(r['massopt_prewarm_progress'])
        self.assertIsNone(r['massopt_saved_pipeline_cache'])
        self.assertIsNone(r['after_movie_replay_other_records_ms'])
        self.assertFalse(r['digest_android_closed_unknown_cause'])
        self.assertEqual(r['aaudio_disconnections'],0)
        self.assertFalse(r['target_met_on_observed_gameplay'])
    def test_out_of_memory_is_only_digest_classification(self):
        r=parse('[dm] [vk] swapchain 800x600, 3 images','out of memory: Android closed it')
        self.assertTrue(r['digest_oom_classification'])
        self.assertFalse(r['digest_android_closed_unknown_cause'])
if __name__=='__main__':unittest.main()
