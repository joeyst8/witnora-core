"""Exact Markdown-output regression for the opt-in Rust benchmark renderer."""

from __future__ import annotations

import random
import unittest

from witnora_core.report import generate_markdown_report


class PythonReportCompatibility(unittest.TestCase):
    def test_python_default_matches_explicit_backend(self):
        payload = {"version": "v1", "summary": {"total_cases": 0}, "per_case_results": []}
        self.assertEqual(generate_markdown_report(payload),
                         generate_markdown_report(payload, backend="python"))

    def test_unknown_renderer_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown benchmark"):
            generate_markdown_report({}, backend="invented")


class NativeReportDifferential(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from witnora_ve import benchmark_report_markdown_native  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native wheel unavailable; GitHub CI builds it")

    def assert_report(self, payload):
        self.assertEqual(generate_markdown_report(payload, backend="rust"),
                         generate_markdown_report(payload, backend="python"))

    def test_empty_report_exact_text(self):
        self.assert_report({})

    def test_explicit_empty_sections(self):
        self.assert_report({"summary": {}, "per_case_results": []})

    def test_no_collapse_and_width_skips(self):
        self.assert_report({"version": "v3", "per_case_results": [
            {"case_name": "a", "solved_route": "NO_COLLAPSE", "original_num_vars": 9,
             "original_num_clauses": 31, "failure_reason": "no-proof",
             "post_s_width_order_status": "SKIPPED_SIZE_CAP", "post_s_num_vars": 9,
             "post_s_width_order_skip_reason": "budget"},
            {"case_name": "b", "solved_route": "RUST", "determinism_pass": False},
        ]})

    def test_boolean_and_missing_metadata(self):
        self.assert_report({"summary": {"solved_count": 3}, "per_case_results": [
            {"case_name": "b", "solved_route": None, "determinism_pass": False},
            {"case_name": "c", "determinism_pass": True, "collapse_path_length": 4},
            {"case_name": "a", "num_bce_removed": 11},
        ]})

    def test_seeded_reports_against_python(self):
        rng = random.Random(5032026)
        for _ in range(128):
            rows = []
            for index in range(rng.randrange(0, 12)):
                row = {"case_name": f"instance_{index}",
                       "solved_route": rng.choice(("NO_COLLAPSE", "RUST", "PYTHON", "")),
                       "status": rng.choice(("SAT", "UNSAT", "UNKNOWN")),
                       "determinism_pass": rng.choice((True, False, None)),
                       "post_s_width_order_status": rng.choice(("OK", "SKIPPED_SIZE_CAP")),
                       "failure_reason": rng.choice(("NONE", "TIMEOUT")),
                       "collapse_path_length": rng.randrange(10),
                       "original_num_vars": rng.randrange(30),
                       "original_num_clauses": rng.randrange(80),
                       "post_s_num_vars": rng.randrange(30),
                       "post_s_width_order_skip_reason": "cap"}
                for field in ("num_bce_removed", "num_ple_assignments", "num_up_assignments",
                              "num_subsumed_clauses", "num_vars_eliminated"):
                    if rng.randrange(2):
                        row[field] = rng.randrange(10)
                rows.append(row)
            report = {"version": "0.9.4", "c_parameter": rng.randrange(2, 5),
                      "scale": "small", "timestamp": "deterministic",
                      "summary": {"solved_count": rng.randrange(50),
                                  "average_collapse_path_length": rng.randrange(100) / 10.0,
                                  "average_clause_reduction_pct": rng.randrange(100) / 10.0,
                                  "certificate_hash_determinism_pass_rate": rng.randrange(101) / 100.0},
                      "per_case_results": rows}
            self.assert_report(report)


if __name__ == "__main__":
    unittest.main()
