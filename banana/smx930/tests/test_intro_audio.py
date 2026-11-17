import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse
from compare import compare
class TestIntroAudio(unittest.TestCase):
    def test_audio_and_submit_metrics(self):
        s='[dm] audio #0 AAudio stream: 48000 Hz, 2 channels, burst 960 frames, buffer 3840 frames (asked 3840), not low latency, shared, device 2309\n[dm] audio #0 device callbacks 2000: 1–960 frames each, 4.0 blocks queued on average at callback; in these 2000, 20 underruns, 155.0 ms zero-padded\n[dm] audio #0 device callbacks 4000: 1–960 frames each, 4.0 blocks queued on average at callback; in these 2000, 29 underruns, 70.0 ms zero-padded\n[dm] [vk] pace up to frame 500 (5.0 s): interval 2 100 %; 30.0 fps; GPU busy p50/p90 2.0/3.8 ms\n[dm] [vk] pace cost up to frame 500, a frame: recording 8.7 ms = draws 0.1 + commit 8.6 (encoder drain 0.5, uploads 0.0, queue submit 7.7)\n[dm] [longframe] frame 1302 (47.67 s) whole frame 1364.4 ms, submit+present 0.0 ms, GPU 0.3 ms; waits: GPU fences 1330.8, acquire 18.4\n'
        r=parse(s)
        self.assertEqual(r['audio_underflow_events'],49)
        self.assertEqual(r['audio_zero_padded_ms'],225.0)
        self.assertEqual(r['aaudio_stream']['buffer_frames'],3840)
        self.assertEqual(r['median_vk_queue_submit_cpu_ms_per_frame'],7.7)
        self.assertEqual(r['median_gpu_busy_p50_ms'],2.0)
        self.assertEqual(r['worst_longframe']['gpu_fence_wait_ms'],1330.8)
        self.assertIn('LONG_FRAME_STALL_OVER_100MS',r['flags'])
        self.assertFalse(r['intro_complete'])
        self.assertFalse(r['target_met_on_observed_gameplay'])
    def test_no_underruns_is_unknown(self):
        r=parse('[dm] [vk] swapchain 800x600, 3 images')
        self.assertIsNone(r['audio_underflow_events'])
    def test_one_tuning_change_allowed(self):
        a={'game_title_id':'x','gpu':'Mali-G925','driver':'faux','environment':{'DM_VK_TL_HOST':None,'DM_DBG_AU_FRAMES':None},'post_intro_fps_samples':15,'post_intro_median_fps':50}
        b={**a,'environment':{'DM_VK_TL_HOST':'1','DM_DBG_AU_FRAMES':None}}
        res=compare(a,b)
        self.assertTrue(res['comparable'])
        self.assertEqual(res['tuning_variables_changed'],['DM_VK_TL_HOST'])
        b['environment']['DM_DBG_AU_FRAMES']='5760'
        self.assertFalse(compare(a,b)['comparable'])
if __name__=='__main__':unittest.main()
