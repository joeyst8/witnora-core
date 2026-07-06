import unittest
from pathlib import Path

from witnora_core.reproducibility_package import external_review_packet_text, validate_package, build_reproducibility_package


class ReproductionScriptsTest(unittest.TestCase):
    def test_external_review_packet(self):
        packet = external_review_packet_text()
        for section in [
            "## What Witnora claims",
            "## What Witnora does not claim",
            "## How to reproduce",
            "## What to inspect first",
            "## Known weaknesses",
            "## Requested reviewer questions",
            "## Proof obligations",
            "## Future work",
        ]:
            self.assertIn(section, packet)
        self.assertIn("Is the empirical edge delta label honest?", packet)
        print("EXTERNAL_REVIEW_PACKET_PASS")

    def test_reproduction_and_validation_scripts_present(self):
        reproduce = Path("scripts/reproduce_v2_12_package.py")
        validate = Path("scripts/validate_v2_12_package.py")
        self.assertTrue(reproduce.is_file())
        self.assertTrue(validate.is_file())
        self.assertIn("unittest", reproduce.read_text(encoding="utf-8"))
        self.assertIn("validate_package", validate.read_text(encoding="utf-8"))
        print("REPRODUCTION_SCRIPT_PRESENT_PASS")
        print("VALIDATION_SCRIPT_PRESENT_PASS")

    def test_validation_script_logic(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            result = build_reproducibility_package(out_root=Path(tmp) / "pkg", zip_path="")
            validation = validate_package(result["out_root"])
        self.assertEqual(validation["verification_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
