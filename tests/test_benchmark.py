import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.benchmark import (
    BenchmarkCase,
    CSV_COLUMNS,
    run_case,
    run_dimacs_dir_benchmark,
    run_synthetic_benchmark,
    write_csv,
)
from witnora_core.certificate import NO_COLLAPSE, SAT
from witnora_core.compare import generate_compare_report
from witnora_core.families import (
    blocked_clique_collapse_family,
    random_3sat_family,
)
from witnora_core.proof import verify_certificate_bundle
from witnora_core.report import generate_markdown_report


class BenchmarkTest(unittest.TestCase):
    def test_synthetic_benchmark(self):
        data = run_synthetic_benchmark(2, timestamp="TEST_TIMESTAMP")
        self.assertIn("per_case_results", data)
        self.assertIn("summary", data)
        self.assertEqual(data["version"], "0.5.1")
        self.assertEqual(data["c_parameter"], 2)
        self.assertEqual(data["scale"], "small")
        self.assertGreaterEqual(data["summary"]["total_cases"], 8)
        self.assertGreater(data["summary"]["solved_count"], 0)
        print("BENCHMARK_SYNTHETIC_PASS")

    def test_benchmark_determinism(self):
        first = run_synthetic_benchmark(
            1,
            determinism_check=True,
            timestamp="TEST_TIMESTAMP",
        )
        second = run_synthetic_benchmark(
            1,
            determinism_check=True,
            timestamp="TEST_TIMESTAMP",
        )
        first_hashes = [
            result["certificate_hash"] for result in first["per_case_results"]
        ]
        second_hashes = [
            result["certificate_hash"] for result in second["per_case_results"]
        ]
        self.assertEqual(first_hashes, second_hashes)
        self.assertEqual(first["summary"]["certificate_hash_determinism_pass_rate"], 1.0)
        self.assertTrue(
            all(result["determinism_pass"] for result in first["per_case_results"])
        )
        print("BENCHMARK_DETERMINISM_PASS")

    def test_blocked_clique_metrics(self):
        case = BenchmarkCase(
            "blocked_clique_n6",
            "blocked_clique_collapse",
            blocked_clique_collapse_family(6),
            "test",
        )
        result = run_case(case, 1, determinism_check=True)
        self.assertGreaterEqual(result.original_clique_lower_bound, 6)
        self.assertTrue(result.post_s_width_order_found)
        self.assertEqual(result.status, SAT)
        self.assertTrue(result.original_verification)
        print("BLOCKED_CLIQUE_METRICS_PASS")

    def test_random_3sat_no_collapse_safe(self):
        case = BenchmarkCase(
            "random_3sat_seed13",
            "random_3sat",
            random_3sat_family(8, 24, seed=13),
            "test",
        )
        result = run_case(case, 1)
        if result.status == NO_COLLAPSE:
            self.assertEqual(result.status, NO_COLLAPSE)
        payload = json.dumps(result.to_dict()).upper()
        self.assertNotIn("HARD", payload)
        self.assertNotIn("UNKNOWN", payload)
        print("RANDOM_3SAT_NO_COLLAPSE_SAFE_PASS")

    def test_dimacs_dir_benchmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unit.cnf").write_text("p cnf 1 1\n1 0\n", encoding="utf-8")
            (root / "unsat.cnf").write_text(
                "p cnf 1 2\n1 0\n-1 0\n",
                encoding="utf-8",
            )
            (root / "bce.dimacs").write_text(
                "p cnf 3 3\n1 2 3 0\n-1 -2 0\n-1 -3 0\n",
                encoding="utf-8",
            )

            data = run_dimacs_dir_benchmark(
                root,
                2,
                determinism_check=True,
                timestamp="TEST_TIMESTAMP",
            )
        self.assertEqual(data["summary"]["total_cases"], 3)
        self.assertEqual(len(data["per_case_results"]), 3)
        self.assertEqual(data["summary"]["certificate_hash_determinism_pass_rate"], 1.0)
        self.assertGreater(data["summary"]["solved_count"], 0)
        print("DIMACS_DIR_BENCHMARK_PASS")

    def test_width_skip_reporting(self):
        case = BenchmarkCase(
            "random_3sat_skip_probe",
            "random_3sat",
            random_3sat_family(8, 24, seed=13),
            "test",
        )
        result = run_case(case, 1, max_width_search_vars=3)
        self.assertIsNone(result.post_s_width_order_found)
        self.assertEqual(result.post_s_width_order_status, "SKIPPED_SIZE_CAP")
        self.assertEqual(
            result.post_s_width_order_skip_reason,
            "num_vars_exceeds_max_width_search_vars",
        )
        print("WIDTH_SKIP_REPORTING_PASS")

    def test_medium_scale_safe(self):
        data = run_synthetic_benchmark(
            1,
            scale="medium",
            determinism_check=True,
            max_width_search_vars=8,
            timestamp="TEST_TIMESTAMP",
        )
        self.assertEqual(data["scale"], "medium")
        self.assertGreater(data["summary"]["total_cases"], 8)
        self.assertEqual(data["summary"]["certificate_hash_determinism_pass_rate"], 1.0)
        self.assertTrue(
            any(
                result["post_s_width_order_status"] == "SKIPPED_SIZE_CAP"
                for result in data["per_case_results"]
            )
        )
        print("BENCHMARK_MEDIUM_SAFE_PASS")

    def test_csv_export(self):
        data = run_synthetic_benchmark(1, timestamp="TEST_TIMESTAMP")
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "results.csv"
            write_csv(data, csv_path)
            lines = csv_path.read_text(encoding="utf-8").splitlines()
        self.assertTrue(lines)
        self.assertEqual(lines[0].split(","), CSV_COLUMNS)
        self.assertIn("blocked_clique_n6", lines[1])
        print("BENCHMARK_CSV_EXPORT_PASS")

    def test_report_generation(self):
        data = run_synthetic_benchmark(
            1,
            determinism_check=True,
            max_width_search_vars=3,
            timestamp="TEST_TIMESTAMP",
        )
        report = generate_markdown_report(data)
        self.assertIn("## Benchmark Overview", report)
        self.assertIn("## Width Measurement Skips", report)
        self.assertIn("## Claims Allowed / Claims Forbidden", report)
        print("BENCHMARK_REPORT_GENERATION_PASS")

    def test_compare_generation(self):
        left = run_synthetic_benchmark(
            1,
            determinism_check=True,
            timestamp="TEST_TIMESTAMP",
        )
        right = run_synthetic_benchmark(
            2,
            determinism_check=True,
            timestamp="TEST_TIMESTAMP",
        )
        report = generate_compare_report(left, right)
        self.assertIn("## Summary Delta", report)
        self.assertIn("## Cases That Changed Route", report)
        self.assertIn("bounded_treewidth_chain_n5", report)
        print("BENCHMARK_COMPARE_PASS")

    def test_benchmark_certificate_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            cert_root = Path(tmp) / "certs"
            data = run_synthetic_benchmark(
                2,
                timestamp="TEST_TIMESTAMP",
                export_certs_dir=cert_root,
            )
            first = data["per_case_results"][0]
            self.assertTrue(first["certificate_bundle_path"])
            verified = verify_certificate_bundle(first["certificate_bundle_path"])
        self.assertTrue(verified["verified"], verified)
        print("BENCHMARK_CERT_EXPORT_PASS")


if __name__ == "__main__":
    unittest.main()
