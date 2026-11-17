import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze import parse
class TestSkip(unittest.TestCase):
    def test_skip_and_draw_ranking(self):
        log='\n'.join([
            '[nxlaunch] env DM_MOVIE_SKIP=1',
            '[nxlaunch] env DM_VK_SLOT_POOL=1',
            '[nxlaunch] env DM_VK_SLOT_POOL=0',
            '[nxlaunch] [RED] DM_VK_SLOT_POOL (the game\'s settings) is not a switch of this build: nothing reads it',
            '[dm] [vk] swapchain 1280x720, 5 images',
            '[dm] [codec] DM_MOVIE_SKIP: AV1 decoder 1 (session decoder 2) ends its stream at packet 5',
            '[dm] [codec] AV1 decoder 1: end of stream after 5 pictures',
            '[dm] [vk] pace cost up to frame 852, a frame: recording 352.6 ms = draws 272.7 + texture prepare 0.0 + submission start 0.4 + commit 13.2 (encoder drain 4.2, uploads 1.4, queue submit 6.0) + other records 66.3; draw path 265.49 us a draw (1 in 16 timed: resolve 6.68, layout 0.13, images+pass+key 253.32, vertex input 0.04)',
        ])
        x=parse(log,'out of memory: Android closed it')
        assert x['movie_skip_confirmed'] and x['movie_skip_packet']==5
        assert x['environment']['DM_VK_SLOT_POOL']=='0'
        assert x['mali_slot_pool_validator_warning']
        assert not x['mali_slot_pool_activation_logged']
        assert x['draw_path_last_sample']['images_pass_key_us']==253.32
        assert x['draw_path_last_sample']['draw_recording_ms']==272.7
        assert x['digest_oom_classification'] and 'MOVIE_SKIP_CONFIRMED' in x['flags']
        assert 'DRAW_RESOURCE_RESOLUTION_OVER_100US' in x['flags']
    def test_unknown_fields_not_fabricated(self):
        x=parse('[dm] [vk] swapchain 1280x720, 5 images')
        assert not x['movie_skip_confirmed']
        assert x['movie_skip_packet'] is None
        assert not x['mali_slot_pool_validator_warning']
        assert x['draw_path_last_sample'] is None
        assert not x['mali_slot_pool_activation_logged']
    def test_activation_only_when_explicit_in_log(self):
        x=parse('[dm] [vk] swapchain 1280x720, 5 images\n[dm] [vk] Mali command pools: one pool per completed replay slot; pool resets, no individual buffer resets')
        assert x['mali_slot_pool_activation_logged']
        assert not x['mali_slot_pool_validator_warning']
if __name__=='__main__':unittest.main()
