import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_source import scan

class TestSourceAudit(unittest.TestCase):
    def test_finds_purchase_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.cs").write_text(
                'bool x = true;\nvar a = "subscribe_purchase_ok";\n',
                encoding="utf-8",
            )
            hits = scan(root)
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0][1], 2)

    def test_does_not_scan_other_extensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.txt").write_text("billing")
            self.assertEqual(scan(root), [])

if __name__ == "__main__":
    unittest.main()
