import tempfile
import unittest
from pathlib import Path

from witnora_core.reproducibility_package import (
    PACKAGE_ID,
    build_reproducibility_package,
)


class ReproducibilityPackageTest(unittest.TestCase):
    def test_reproducibility_package_schema_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_reproducibility_package(out_root=Path(tmp) / "pkg", zip_path="")
            root = Path(result["out_root"])
            manifest = result["manifest"]
            self.assertEqual(manifest["package_id"], PACKAGE_ID)
            self.assertEqual(manifest["version"], "v2.12-paper-reproducibility-package")
            self.assertEqual(manifest["expected_test_count"], 463)
            self.assertIn("REPRODUCIBILITY_MANIFEST.json", {path.name for path in root.iterdir()})
            self.assertTrue((root / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md").is_file())
            self.assertEqual(result["validation"]["verification_status"], "PASS")
        print("REPRODUCIBILITY_PACKAGE_SCHEMA_PASS")
        print("REPRODUCIBILITY_PACKAGE_FILES_PASS")


if __name__ == "__main__":
    unittest.main()
