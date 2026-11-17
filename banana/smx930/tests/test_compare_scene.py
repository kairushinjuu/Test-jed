import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compare_scene import compare_scene

class TestSceneCompare(unittest.TestCase):
    def m(self):
        return {'game_title_id':'0400486024DEC000','gpu':'Mali-G925','driver':'panvk_faux123',
         'environment':{'DM_GRAPHICS_SCALE':'2','DM_VK_NDSR':'4','DM_ROMFS_OVERLAY':'/test','DM_VK_TL_HOST':'1','DM_VK_PSO_ASYNC':'2'},
         'intro_complete':True,'after_movie_scene_windows':[{'fps':4.8,'gpu_p50_ms':70}],
         'worst_longframe':{'whole_ms':27312,'pipeline_creation_ms':24577},
         'last_tracked_graphics_allocation_mib':3130,'audio_underflow_events':565,'audio_zero_padded_ms':1645,'audio_callback_windows':19}
    def test_one_changed_knob_comparable_but_not_fps_pass(self):
        a=self.m();b=self.m();b['environment']=dict(a['environment'],DM_VK_TL_HOST='0');r=compare_scene(a,b)
        self.assertTrue(r['scene_pressure_comparable'])
        self.assertFalse(r['steady_gameplay_50fps_claim_permitted'])
        self.assertEqual(r['baseline']['audio_underruns_per_2000_callbacks'],29.74)
    def test_no_scene_is_incomparable(self):
        a=self.m();b=self.m();b['environment']=dict(a['environment'],DM_VK_TL_HOST='0');b['after_movie_scene_windows']=[]
        self.assertFalse(compare_scene(a,b)['scene_pressure_comparable'])
    def test_two_changes_is_incomparable(self):
        a=self.m();b=self.m();b['environment']=dict(a['environment'],DM_VK_TL_HOST='0',DM_VK_PSO_ASYNC='1')
        self.assertFalse(compare_scene(a,b)['scene_pressure_comparable'])
    def test_different_quality_incomparable(self):
        a=self.m();b=self.m();b['environment']=dict(a['environment'],DM_VK_TL_HOST='0',DM_GRAPHICS_SCALE='1')
        self.assertFalse(compare_scene(a,b)['scene_pressure_comparable'])
if __name__=='__main__':unittest.main()
