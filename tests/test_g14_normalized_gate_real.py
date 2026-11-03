"""Real Lean acceptance/rejection for Python-normalized G14 branch partitions."""
import unittest
from dataclasses import replace

from witnora_core.cnf import CNFFormula
from witnora_core.lean_g14_gate import (
    _check_partitions_with_lean, verify_g14_unsat_cover_with_lean,
)
from witnora_core.separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
    build_separator_affine_certificate, make_separator_affine_instance,
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

    def test_real_combined_source_dimacs_g14_g5_certificate_accepted(self):
        instance = make_separator_affine_instance("saf_unsat_cover_2")
        formula = instance.formula
        certificate = build_separator_affine_certificate(instance)
        raw = formula.to_clause_lists()
        tokens = [lit for clause in raw for lit in (*clause, 0)]
        result = verify_g14_unsat_cover_with_lean(
            formula, certificate,
            raw_clauses=raw,
            source_tokens=tokens,
            source_spellings=list(map(str, tokens)),
            source_text=formula.canonical_dimacs(),
            timeout_seconds=240,
        )
        self.assertTrue(result["verified"], result)
        self.assertEqual(
            result["lean_formal_status"],
            "LEAN_END_TO_END_G14_UNSAT_VERIFIED",
        )

    def test_real_source_high_variable_ids_accept_without_bound_scan(self):
        # Preserve the same affine UNSAT instance while replacing its four
        # nonseparator variable names by million-scale sparse IDs.
        original = make_separator_affine_instance("saf_unsat_cover_2")
        renaming = {2: 1048576, 3: 1048577, 4: 1048578, 5: 1048579}
        clauses = [
            [(1 if lit > 0 else -1) *
             renaming.get(abs(lit), abs(lit)) for lit in clause]
            for clause in original.formula.to_clause_lists()
        ]
        formula = CNFFormula.from_raw_clauses(clauses)
        instance = replace(
            original, instance_id="saf_unsat_cover_sparse_large_ids",
            formula=formula,
        )
        certificate = build_separator_affine_certificate(instance)
        raw = formula.to_clause_lists()
        tokens = [lit for clause in raw for lit in (*clause, 0)]
        result = verify_g14_unsat_cover_with_lean(
            formula, certificate,
            raw_clauses=raw,
            source_tokens=tokens,
            source_spellings=list(map(str, tokens)),
            source_text=formula.canonical_dimacs(),
            timeout_seconds=240,
        )
        self.assertTrue(result["verified"], result)
        self.assertEqual(
            result["lean_formal_status"],
            "LEAN_END_TO_END_G14_UNSAT_VERIFIED",
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
