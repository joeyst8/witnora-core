import tempfile
import unittest
from pathlib import Path

from witnora_core.strictness_proof import (
    FULL_G0_STRICTNESS_NOT_CLAIMED,
    PROVEN_RESTRICTED_THEOREM,
    SCALABLE_FAMILY_PROOF_OBLIGATION,
    run_strictness_proof,
)


class RestrictedG0G1TheoremTest(unittest.TestCase):
    def test_no_full_g0_overclaim_and_scalable_not_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_strictness_proof(instances=["tseitin_10"], cap_c=4, out_root=Path(tmp) / "strictness", zip_path="")
        candidate = result["restricted_g0_g1_theorem_candidate"]
        self.assertEqual(candidate["full_g0_base_status"], FULL_G0_STRICTNESS_NOT_CLAIMED)
        self.assertEqual(candidate["scalable_family_status"], SCALABLE_FAMILY_PROOF_OBLIGATION)
        text = str(candidate)
        self.assertNotIn(PROVEN_RESTRICTED_THEOREM, text)
        print("FULL_G0_STRICTNESS_NOT_CLAIMED_PASS")
        print("SCALABLE_FAMILY_NOT_MARKED_PROVEN_PASS")
        print("PROVEN_REQUIRES_PROOF_FILE_PASS")

    def test_restricted_theorem_doc(self):
        text = Path("theory/RESTRICTED_G0_G1_STRICTNESS_THEOREM.md").read_text(encoding="utf-8")
        self.assertIn("G0_WIDTH_C", text)
        self.assertIn("This does not prove full `G0_BASE` strictness", text)
        self.assertIn("This does not prove P vs NP", text)
        print("RESTRICTED_THEOREM_DOC_PASS")


if __name__ == "__main__":
    unittest.main()

