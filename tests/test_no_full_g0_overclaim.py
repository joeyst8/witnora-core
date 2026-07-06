import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.strictness_proof import run_strictness_proof


def _status_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.endswith("status") or key in {"status", "checker_status", "strictness_status", "obstruction_status"}:
                yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


class NoFullG0OverclaimTest(unittest.TestCase):
    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "strictness"
            run_strictness_proof(instances=["tseitin_10"], cap_c=4, out_root=root, zip_path="")
            payloads = [
                json.loads((root / "width_obstruction_certificates.json").read_text(encoding="utf-8")),
                json.loads((root / "xor_upper_bound_certificates.json").read_text(encoding="utf-8")),
                json.loads((root / "strictness_proof_records.json").read_text(encoding="utf-8")),
                json.loads((root / "restricted_g0_g1_theorem_candidate.json").read_text(encoding="utf-8")),
            ]
        statuses = [value for payload in payloads for value in _status_values(payload)]
        self.assertNotIn("HARD", statuses)
        self.assertNotIn("UNKNOWN", statuses)
        print("NO_HARD_UNKNOWN_STATUS_PASS")

    def test_no_full_g0_claim_in_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_strictness_proof(instances=["tseitin_10"], cap_c=4, out_root=Path(tmp) / "strictness", zip_path="")
        record_text = json.dumps(result["strictness_proof_records"], sort_keys=True)
        self.assertIn("FULL_G0_STRICTNESS_NOT_CLAIMED", record_text)
        self.assertNotIn("full G0_BASE strictness is proven", record_text)
        print("FULL_G0_STRICTNESS_NOT_CLAIMED_PASS")


if __name__ == "__main__":
    unittest.main()

