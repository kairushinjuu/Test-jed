import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"source_patch"))
from fix_pack_dump_import import OLD, NEW, patch

class TestPackDumpImport(unittest.TestCase):
    def test_import_from_exact_pack_layout(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            script=root/"dm/gfx/tools/shader_split.py"
            script.parent.mkdir(parents=True)
            script.write_text("import os,sys\n"+OLD+"\nimport pack_dump\n")
            module=root/"scripts/pack_dump.py"
            module.parent.mkdir()
            module.write_text("PACK_DUMP_IMPORT_OK=True\n")
            self.assertEqual(patch(root,check=True),"verified")
            self.assertIn(OLD,script.read_text())
            self.assertEqual(patch(root),"patched")
            self.assertEqual(patch(root),"already corrected")
            before=sys.path[:]
            try:
                local={"__file__":str(script)}
                exec(script.read_text(),local)
                self.assertTrue(local["pack_dump"].PACK_DUMP_IMPORT_OK)
            finally:
                sys.path[:]=before
                sys.modules.pop("pack_dump",None)
    def test_unknown_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            script=root/"dm/gfx/tools/shader_split.py"
            script.parent.mkdir(parents=True)
            script.write_text("import pack_dump\n")
            with self.assertRaises(RuntimeError):
                patch(root)
    def test_correct_relative_depth(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            script=root/"dm/gfx/tools/shader_split.py"
            self.assertEqual((script.parent/"../../../scripts").resolve(),(root/"scripts").resolve())
            self.assertNotEqual((script.parent/"../../scripts").resolve(),(root/"scripts").resolve())

if __name__=="__main__":
    unittest.main()
