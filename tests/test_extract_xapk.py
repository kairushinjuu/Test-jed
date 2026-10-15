import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from extract_xapk import extract


class TestXapkExtract(unittest.TestCase):
    def test_extracts_split_apks_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            xapk = root / "sample.xapk"
            with zipfile.ZipFile(xapk, "w") as archive:
                archive.writestr("jp.takoboto.apk", b"base-apk")
                archive.writestr("config.xhdpi.apk", b"density-split")
                archive.writestr("manifest.json", b'{"version_name":"2.1.7"}')
                archive.writestr("icon.png", b"icon")
            good, bad = extract(xapk, root / "extracted")
            self.assertEqual(len(good), 3)
            self.assertEqual(len(bad), 0)
            self.assertEqual((root / "extracted" / "jp.takoboto.apk").read_bytes(), b"base-apk")
            self.assertFalse((root / "extracted" / "icon.png").exists())

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            xapk = root / "sample.xapk"
            with zipfile.ZipFile(xapk, "w") as archive:
                archive.writestr("../other.apk", b"malicious")
            good, bad = extract(xapk, root / "extracted")
            self.assertEqual(good, [])
            self.assertEqual(len(bad), 1)
            self.assertFalse((root / "other.apk").exists())

if __name__ == "__main__":
    unittest.main()
