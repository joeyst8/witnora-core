"""Full verification-report / trust-card presentation parity against Python."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest

from witnora_core.verification_report import (
    render_verification_report_markdown,
    render_trust_card_markdown,
    trust_card_from_report,
)


RUST_BIN = os.environ.get("WITNORA_RUST_VERIFICATION_VIEW_BIN")


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "native verification-view binary built only in GitHub CI")
class NativeVerificationViewTests(unittest.TestCase):
    def run_mode(self, mode, data, *, project=None):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            output = root / "rendered.out"
            source.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            cmd = [RUST_BIN, mode, str(source), "--out", str(output)]
            if project is not None:
                cmd.extend(["--project", project])
            native = subprocess.run(cmd, capture_output=True)
            self.assertEqual(native.returncode, 0, native.stderr.decode(errors="replace"))
            return output.read_bytes()

    def compare_report(self, report, *, project="Witnora-Core"):
        expected_report = render_verification_report_markdown(report).encode("utf-8")
        self.assertEqual(self.run_mode("report-markdown", report), expected_report)
        card = trust_card_from_report(report, project=project)
        native_card = json.loads(self.run_mode("trust-card", report, project=project))
        self.assertEqual(native_card, card)
        expected_card = render_trust_card_markdown(card).encode("utf-8")
        self.assertEqual(self.run_mode("trust-markdown", card), expected_card)

    def test_empty_metadata_and_partial_replay_controls(self):
        self.compare_report({})
        self.compare_report({"claim": "Witnora evidence is bounded", "verdict": "VERIFIED",
                             "verification_depth": "metadata_hash_checks_only"})
        self.compare_report({
            "claim": "Selected proof replay only", "verdict": "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS",
            "verification_depth": "partial_replay", "replay_depth": "partial",
            "selection_policy": "largest", "risk_flags": ["PROOF_SELECTION_LIMITED"],
            "selected_evidence": [{"instance_id": "case1", "c": 3,
                                   "cap_profile": None, "public_category": "UNSAT_XOR_NATIVE_ONLY"}],
            "checks_performed": [{"name": "external", "status": "PASS", "depth": "partial"}],
        }, project="Witnora research")

    def test_128_seeded_byte_parity(self):
        rng = random.Random(5092026)
        verdicts = ["VERIFIED", "PARTIALLY_VERIFIED", "OVERCLAIM", "NOT_VERIFIED",
                    "ARTIFACT_INTEGRITY_VERIFIED", "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS"]
        for trial in range(128):
            depth = rng.choice(["metadata_hash_checks_only", "partial_replay", "full"])
            report = {
                "claim": f"Claim {trial} 🙂", "verdict": rng.choice(verdicts),
                "certification_level": rng.choice(["ARTIFACT", "PARTIAL", "NONE"]),
                "verification_depth": depth, "replay_depth": rng.choice(["partial", "full", None]),
                "selection_policy": rng.choice(["largest", "first", None]),
                "claim_scan_depth": "heuristic_text_scan",
                "last_verification_timestamp": "2026-11-05T00:00:00Z",
                "reproducibility_status": rng.choice(["REPRODUCIBLE", "NOT_ASSESSED"]),
                "evidence_files": [f"file_{i}.drat" for i in range(rng.randrange(0, 5))],
                "selected_evidence": [{"instance_id": f"case_{i}", "c": i,
                    "cap_profile": rng.choice(["bounded", None]),
                    "public_category": "UNSAT_DRAT_EXPORTED_VERIFIED"}
                    for i in range(rng.randrange(0, 5))],
                "checks_performed": [{"name": f"check_{i}",
                    "status": rng.choice(["PASS", "FAIL", "SKIP"]), "depth": depth}
                    for i in range(rng.randrange(0, 7))],
                "checker_results": [{"checker": "drat-trim", "passed": rng.choice([True, False])},
                                    {"check": "source_identity", "verified": rng.choice([True, False])}],
                "evidence_checked": [{"path": f"proof{i}", "kind": "drat",
                    "status": rng.choice(["PASS", "MISSING"]),
                    "sha256_expected": "a" * 64, "sha256_actual": "b" * 64}
                    for i in range(rng.randrange(0, 3))],
                "external_checkers": ["drat-trim"] if rng.randrange(2) else [],
                "proof_syntax_checks": [{"instance_id": "x", "status": "PASS", "message": "ok"}]
                    if rng.randrange(2) else [],
                "drat_trim_log_checks": [{"instance_id": "x", "status": "FAIL", "message": "bad"}]
                    if rng.randrange(2) else [],
                "independent_checker_replay": [],
                "drat_trim_replay": [{"instance_id": "x", "status": "PASS", "message": "checked"}]
                    if rng.randrange(2) else [],
                "artifact_hashes": {f"file{i}": "c" * 64 for i in range(rng.randrange(0, 3))},
                "allowed_claims": ["scoped evidence", "bounded result"],
                "forbidden_claims": ["P vs NP", "industrial benchmark success"],
                "risk_flags": [rng.choice(["METADATA_ONLY", "PROOF_SELECTION_LIMITED",
                                           "UNVERIFIED_CLAIM", "DRAT_TRIM_NOT_RERUN"])
                               for _ in range(rng.randrange(0, 4))],
            }
            with self.subTest(trial=trial):
                self.compare_report(report, project=f"Witnora-{trial}")

    def test_malformed_json_fails_without_output(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "broken.json"
            output = root / "never.md"
            source.write_text("{invalid", encoding="utf-8")
            result = subprocess.run([RUST_BIN, "report-markdown", str(source),
                                     "--out", str(output)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())

    def test_help_and_option_order(self):
        help_result = subprocess.run([RUST_BIN, "--help"], capture_output=True)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(b"usage:", help_result.stdout)
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.json"
            output = root / "view.md"
            source.write_text("{}", encoding="utf-8")
            result = subprocess.run([RUST_BIN, "--out", str(output),
                                     "report-markdown", str(source)], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Witnora Verification Report", output.read_text())


if __name__ == "__main__":
    unittest.main()
