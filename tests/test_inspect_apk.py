import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_apk import inspect


class TestApkInspection(unittest.TestCase):
    def test_inspection_lists_architectures(self):
        with tempfile.TemporaryDirectory() as td:
            apk = Path(td) / "sample.apk"
            with zipfile.ZipFile(apk, "w") as z:
                z.writestr("AndroidManifest.xml", "manifest")
                z.writestr("classes.dex", "dex")
                z.writestr("lib/arm64-v8a/libassembly-store.so", "store")
                z.writestr("lib/arm64-v8a/libaot-Takoboto.dll.so", "aot")
            result = inspect(apk)
            self.assertEqual(result["zip_crc"], "OK")
            self.assertEqual(result["abis"], ["arm64-v8a"])
            self.assertEqual(len(result["assembly_stores"]), 1)
            self.assertEqual(len(result["aot_libraries"]), 1)
            self.assertEqual(result["sha256"], hashlib.sha256(apk.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
