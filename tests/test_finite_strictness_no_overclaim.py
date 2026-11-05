import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.finite_strictness_certificate import build_outputs
from witnora_core.strictness_proof import FULL_G0_STRICTNESS_NOT_CLAIMED, SCALABLE_FAMILY_PROOF_OBLIGATION


def _status_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.endswith("status") or key in {"status", "checker_status", "strictness_status"}:
                yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


class FiniteStrictnessNoOverclaimTest(unittest.TestCase):
    def test_no_full_g0_or_family_theorem_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_outputs(instances=["tseitin_10"], cap_c=4, out_root=Path(tmp) / "finite", zip_path="")
        cert = result["finite_strictness_certificate"]
        self.assertEqual(cert["bound_profile"]["full_g0_base_claim"], FULL_G0_STRICTNESS_NOT_CLAIMED)
        self.assertNotIn("PROVEN_FAMILY_THEOREM", json.dumps(cert))
        self.assertIn("not scalable family theorem", json.dumps(cert))
        print("FINITE_STRICTNESS_NO_FULL_G0_CLAIM_PASS")
        print("FINITE_STRICTNESS_NO_FAMILY_THEOREM_CLAIM_PASS")

    def test_scalable_family_remains_proof_obligation_and_no_false_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "finite"
            result = build_outputs(instances=["tseitin_10"], cap_c=4, out_root=root, zip_path="")
            payloads = [
                json.loads((root / "finite_strictness_certificate.json").read_text(encoding="utf-8")),
                json.loads((root / "scalable_family_proof_obligations.json").read_text(encoding="utf-8")),
            ]
        cert_text = json.dumps(payloads, sort_keys=True)
        self.assertEqual(result["finite_strictness_certificate"]["scalable_family_status"], SCALABLE_FAMILY_PROOF_OBLIGATION)
        self.assertNotIn("full G0_BASE strictness is proven", cert_text)
        self.assertNotIn("hierarchy completeness is proven", cert_text)
        self.assertNotIn("proves P vs NP", cert_text)
        statuses = [value for payload in payloads for value in _status_values(payload)]
        self.assertNotIn("HARD", statuses)
        self.assertNotIn("UNKNOWN", statuses)
        print("SCALABLE_FAMILY_REMAINS_PROOF_OBLIGATION_PASS")
        print("NO_FALSE_LOWER_BOUND_CLAIM_PASS")
        print("NO_HIERARCHY_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
