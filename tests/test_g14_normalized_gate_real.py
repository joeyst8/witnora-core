"""Real Lean acceptance/rejection for Python-normalized G14 branch partitions."""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.lean_g14_gate import _check_partitions_with_lean
from witnora_core.separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
)


class ProductionG14NormalizedPartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Every separator branch reduces two contradictory unit pairs
        # to duplicate empty clauses. Python deduplicates these into one.
        cls.formula = CNFFormula.from_raw_clauses(
            [[1], [-1], [2], [-2]]
        )
        specs = _component_dicts(cls.formula, [1, 2])
        cls.partitions = []
        for assignment in _all_assignments([1, 2]):
            _residual, parts, errors = _condition_by_separator(
                cls.formula, assignment, specs
            )
            if errors:
                raise ValueError(errors)
            cls.partitions.append((assignment, list(parts.values())))

    def test_duplicate_empty_clauses_accept_under_lean(self):
        digest = _check_partitions_with_lean(
            self.formula, self.partitions,
            timeout_seconds=180, project_root=None,
        )
        self.assertEqual(len(digest), 64)

    def test_missing_canonical_empty_clause_fails_closed(self):
        bad = list(self.partitions)
        branch, _parts = bad[0]
        bad[0] = (branch, [CNFFormula()])
        with self.assertRaisesRegex(
            ValueError, "Lean rejected G14 conditioning or partition"
        ):
            _check_partitions_with_lean(
                self.formula, bad,
                timeout_seconds=180, project_root=None,
            )

    def test_swapped_or_incomplete_branch_enumeration_fails(self):
        with self.assertRaisesRegex(
            ValueError, "Lean rejected G14 conditioning or partition"
        ):
            _check_partitions_with_lean(
                self.formula, self.partitions[:-1],
                timeout_seconds=180, project_root=None,
            )


if __name__ == "__main__":
    unittest.main()
