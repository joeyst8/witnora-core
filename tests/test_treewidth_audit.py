import subprocess
import tempfile
import unittest
from pathlib import Path

from witnora_core.cnf import CNFFormula
from witnora_core.dimacs import parse_dimacs
from witnora_core.public_benchmarks import find_cnfgen_cli
from witnora_core.treewidth_audit import (
    EXACT_WIDTH_FOUND,
    SKIPPED_TOO_MANY_VARIABLES,
    exact_width_audit,
)


def pigeonhole_formula(pigeons: int, holes: int) -> CNFFormula:
    def var(pigeon: int, hole: int) -> int:
        return (pigeon - 1) * holes + hole

    clauses = []
    for pigeon in range(1, pigeons + 1):
        clauses.append([var(pigeon, hole) for hole in range(1, holes + 1)])
    for hole in range(1, holes + 1):
        for p1 in range(1, pigeons + 1):
            for p2 in range(p1 + 1, pigeons + 1):
                clauses.append([-var(p1, hole), -var(p2, hole)])
    return CNFFormula.from_raw_clauses(clauses)


class TreewidthAuditTest(unittest.TestCase):
    def test_path_width_one(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [2, 3], [3, 4]])
        audit = exact_width_audit(
            formula,
            instance_name="path4",
            max_c=3,
            max_vars=10,
            timeout_seconds=5,
        )
        self.assertEqual(audit["status"], EXACT_WIDTH_FOUND)
        self.assertEqual(audit["exact_width_found"], 1)
        print("TREEWIDTH_AUDIT_PATH_PASS")

    def test_clique_k5_width_four(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3, 4, 5]])
        audit = exact_width_audit(
            formula,
            instance_name="k5",
            max_c=5,
            max_vars=10,
            timeout_seconds=5,
        )
        self.assertEqual(audit["status"], EXACT_WIDTH_FOUND)
        self.assertEqual(audit["exact_width_found"], 4)
        print("TREEWIDTH_AUDIT_CLIQUE_PASS")

    def test_found_order_is_verified(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [3, 4], [4, 5]])
        audit = exact_width_audit(
            formula,
            instance_name="small_verified",
            max_c=4,
            max_vars=10,
            timeout_seconds=5,
        )
        self.assertEqual(audit["status"], EXACT_WIDTH_FOUND)
        self.assertEqual(sorted(audit["exact_order"]), [1, 2, 3, 4, 5])
        self.assertLessEqual(audit["exact_width_found"], 2)
        print("TREEWIDTH_AUDIT_ORDER_VERIFY_PASS")

    def test_skip_large_formula(self):
        formula = CNFFormula.from_raw_clauses([[i] for i in range(1, 31)])
        audit = exact_width_audit(
            formula,
            instance_name="large_units",
            max_c=2,
            max_vars=10,
            timeout_seconds=5,
        )
        self.assertEqual(audit["status"], SKIPPED_TOO_MANY_VARIABLES)
        print("TREEWIDTH_AUDIT_SKIP_LARGE_PASS")

    def test_php_4_3_treewidth_audit(self):
        cli = find_cnfgen_cli()
        if cli is not None:
            proc = subprocess.run(
                [cli, "php", "4", "3"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            formula = parse_dimacs(proc.stdout)
        else:
            formula = pigeonhole_formula(4, 3)
        audit = exact_width_audit(
            formula,
            instance_name="php_4_3",
            max_c=8,
            max_vars=20,
            timeout_seconds=30,
        )
        self.assertIn(audit["status"], {EXACT_WIDTH_FOUND, "NOT_FOUND_UP_TO_MAX_C", "TIMEOUT"})
        if audit["status"] == EXACT_WIDTH_FOUND:
            self.assertIsInstance(audit["exact_width_found"], int)
        print("PHP_4_3_TREEWIDTH_AUDIT_PASS")


if __name__ == "__main__":
    unittest.main()
