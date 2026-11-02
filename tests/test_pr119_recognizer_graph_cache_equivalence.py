"""Regression: per-invocation graph reuse must not alter recognizer decisions."""

import unittest
from unittest.mock import patch

from research.pr119_separator_selection_benchmark import (
    legacy_uncached_cut,
    random_three_sat_control,
    relabel_formula,
    source_formula,
)
from witnora_core import separator_affine_family_theorem as saf


class RecognizerGraphCacheEquivalenceTests(unittest.TestCase):
    def assert_cached_matches_uncached(self, formula, *, c, r):
        original_graph = saf.primal_graph
        original_components = saf._component_dicts

        with patch.object(saf, "primal_graph", wraps=original_graph) as graph_spy:
            cached = saf.recognize_separator_affine_family(formula, c=c, r=r)
        self.assertEqual(graph_spy.call_count, 1, "recognizer must construct one graph")

        def legacy_component_dicts(formula, separator, *, graph=None):
            # Deliberately ignore the injected cache: old per-candidate path.
            return original_components(formula, separator)

        with (patch.object(saf, "_component_dicts", side_effect=legacy_component_dicts),
              patch.object(saf, "primal_graph", wraps=original_graph) as graph_spy):
            uncached = saf.recognize_separator_affine_family(formula, c=c, r=r)
        self.assertEqual(graph_spy.call_count, len(uncached["trace"]) + 1)
        self.assertEqual(cached, uncached, "statuses, separators, components and entire traces must match")
        # Independent replay of the historical algorithm, which did costly
        # validation even after seeing that a candidate was not a graph cut.
        historical = legacy_uncached_cut(formula, c, r)
        self.assertEqual(cached["separator_variables"], historical["cut"])
        self.assertEqual(len(cached["trace"]), historical["candidate_count"])
        return cached

    def test_small_sat_and_unsat_family_cases(self):
        for name in ("saf_sat_chain_4", "saf_unsat_cover_4", "saf_balanced_sat_4"):
            with self.subTest(name=name):
                formula = saf.make_separator_affine_instance(name).formula
                self.assert_cached_matches_uncached(formula, c=1, r=2)

    def test_archived_tc063_source_and_relabel(self):
        source = source_formula()
        for name, formula in (("source", source), ("relabel11", relabel_formula(source, 11))):
            with self.subTest(name=name):
                result = self.assert_cached_matches_uncached(formula, c=2, r=3)
                self.assertEqual(result["status"], saf.SEPARATOR_AFFINE_FAMILY_RECOGNIZED)
                separator = result["separator_variables"]
                instance = saf.SeparatorAffineFamilyInstance(
                    instance_id="cache_equiv_" + name,
                    formula=formula,
                    separator_variables=separator,
                    separator_bound_c=2,
                    affine_arity_bound_r=3,
                    expected_result=saf.UNSAT_CERTIFIED,
                    family="graph-cache-equivalence",
                    n=len(formula.variables),
                )
                baseline = saf.build_separator_affine_certificate(instance).to_dict()
                with patch.object(saf, "_component_dicts", side_effect=lambda f, s, *, graph=None: saf_legacy_components(f, s)):
                    replay = saf.build_separator_affine_certificate(instance).to_dict()
                self.assertEqual(baseline, replay)
                check = saf.check_separator_affine_certificate(formula, baseline)
                self.assertEqual(check["checker_status"], saf.SEPARATOR_AFFINE_CERTIFICATE_VERIFIED)
                self.assertEqual(baseline["final_result"], saf.UNSAT_CERTIFIED)

    def test_dense_random_negative_control(self):
        formula = random_three_sat_control(20261102)
        result = self.assert_cached_matches_uncached(formula, c=2, r=3)
        self.assertEqual(result["status"], saf.DIAGNOSTIC_ONLY)
        self.assertEqual(result["separator_variables"], [])


def saf_legacy_components(formula, separator):
    """Invoke the unmodified per-candidate component builder independently."""
    return _ORIGINAL_COMPONENT_DICTS(formula, separator)


_ORIGINAL_COMPONENT_DICTS = saf._component_dicts


if __name__ == "__main__":
    unittest.main()
