import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.operator_genesis import GENERATED_CANDIDATE, run_operator_genesis


def _status_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.endswith("status") or key == "status" or key == "current_status":
                yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


class OperatorGenesisReportsTest(unittest.TestCase):
    def test_operator_genesis_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "genesis"
            result = run_operator_genesis(
                families=["pigeonhole", "parity", "graph-coloring", "clique", "subset-sum", "adversarial-mixed", "random-structured"],
                out_root=root,
                strict=True,
            )
            required = [
                "obstruction_fingerprints.json",
                "generated_operator_candidates.json",
                "operator_promotion_queue.json",
                "certificate_obligation_matrix.json",
                "theorem_candidate_queue.json",
                "operator_schema_language.json",
                "OPERATOR_GENESIS_REPORT.md",
            ]
            for name in required:
                self.assertTrue((root / name).exists(), name)
            report = (root / "OPERATOR_GENESIS_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("v2.4 generates candidate operator schemas", report)
        self.assertIn("does not claim that generated candidates are implemented", report)
        self.assertGreaterEqual(len(result["generated_operator_candidates"]), 7)
        print("OPERATOR_GENESIS_REPORT_PASS")

    def test_no_fake_implementation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_operator_genesis(families=["pigeonhole", "parity"], out_root=Path(tmp) / "genesis")
        for candidate in result["generated_operator_candidates"]:
            self.assertEqual(candidate["status"], GENERATED_CANDIDATE)
            self.assertIn("Generated candidate is not implemented.", candidate["forbidden_interpretations"])
        print("NO_FAKE_IMPLEMENTATION_PASS")

    def test_no_fake_operator_solved_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "genesis"
            result = run_operator_genesis(families=["pigeonhole", "parity"], out_root=root)
            text = "\n".join(
                [
                    json.dumps(result["generated_operator_candidates"], sort_keys=True),
                    (root / "OPERATOR_GENESIS_REPORT.md").read_text(encoding="utf-8"),
                ]
            )
        self.assertIn("No generated candidate is implemented", text)
        self.assertNotIn("discovered and implemented a new working operator", text)
        self.assertNotIn("generated operator solved", text.lower().replace("operator solved-claim", "operator claim"))
        print("NO_FAKE_OPERATOR_SOLVED_CLAIM_PASS")

    def test_no_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "genesis"
            run_operator_genesis(families=["pigeonhole", "parity"], out_root=root)
            report = (root / "OPERATOR_GENESIS_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("no P vs NP progress claim", report)
        self.assertNotIn("proves P vs NP", report)
        self.assertNotIn("P = NP", report)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "genesis"
            run_operator_genesis(families=["pigeonhole", "parity", "random-structured"], out_root=root)
            payloads = [
                json.loads((root / "generated_operator_candidates.json").read_text(encoding="utf-8")),
                json.loads((root / "operator_promotion_queue.json").read_text(encoding="utf-8")),
                json.loads((root / "theorem_candidate_queue.json").read_text(encoding="utf-8")),
            ]
        statuses = [value for payload in payloads for value in _status_values(payload)]
        self.assertNotIn("HARD", statuses)
        self.assertNotIn("UNKNOWN", statuses)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
