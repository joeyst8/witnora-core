import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.benchmark import (
    BenchmarkCase,
    run_case,
    run_dimacs_dir_benchmark,
    run_synthetic_benchmark,
)
from witnora_core.certificate import NO_COLLAPSE, SAT
from witnora_core.families import (
    blocked_clique_collapse_family,
    random_3sat_family,
)


class BenchmarkTest(unittest.TestCase):
    def test_synthetic_benchmark(self):
        data = run_synthetic_benchmark(2, timestamp="TEST_TIMESTAMP")
        self.assertIn("per_case_results", data)
        self.assertIn("summary", data)
        self.assertEqual(data["version"], "0.1.0")
        self.assertEqual(data["c_parameter"], 2)
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


if __name__ == "__main__":
    unittest.main()
