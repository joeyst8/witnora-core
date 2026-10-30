"""Experimental multi-operator search. Results are hypotheses, not certificates.

Generate small compositions of established SAT-equivalent transformations,
measure structural changes, and test promising combinations on held-out CNFs.
No operator is considered novel or Lean verified because of a score.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from typing import Callable

from .cnf import CNFFormula, Clause, resolvent
from .parity_compression import compress_binary_xor_components, substitute_residual_formula
from .structural_operator_invention import (
    min_fill_elimination, xor_boundary_elimination, max_release_elimination,
)

RESEARCH_STATUS = "UNVERIFIED_DISCOVERY_CANDIDATE"
OPERATORS = ("parity_root", "unit_propagation", "subsumption", "bounded_elimination",
             "invariant_min_fill", "invariant_xor_boundary", "invariant_max_release")


@dataclass(frozen=True)
class Hypothesis:
    sequence: tuple[str, ...]
    formula: CNFFormula
    score: float

    def record(self, original: CNFFormula) -> dict:
        return {
            "operator_sequence": list(self.sequence),
            "source_formula_sha256": original.formula_hash,
            "candidate_formula_sha256": self.formula.formula_hash,
            "source_variables": original.num_vars,
            "source_clauses": original.num_clauses,
            "candidate_variables": self.formula.num_vars,
            "candidate_clauses": self.formula.num_clauses,
            "variables_removed": original.num_vars - self.formula.num_vars,
            "clauses_removed": original.num_clauses - self.formula.num_clauses,
            "structural_score": round(self.score, 6),
            "status": RESEARCH_STATUS,
            "lean_verified": False,
            "novelty_verified": False,
            "performance_advantage_verified": False,
            "promoted": False,
        }


def unit_propagation(formula: CNFFormula) -> CNFFormula:
    rows = [set(c.literals) for c in formula.clauses]
    assignments: dict[int, bool] = {}
    while True:
        unit = next((next(iter(row)) for row in rows if len(row) == 1), None)
        if unit is None:
            return CNFFormula.from_raw_clauses(rows)
        var, value = abs(unit), unit > 0
        if var in assignments and assignments[var] != value:
            return CNFFormula.from_raw_clauses([[]])
        assignments[var] = value
        reduced = []
        for row in rows:
            if unit in row:
                continue
            without = row - {-unit}
            if not without:
                return CNFFormula.from_raw_clauses([[]])
            reduced.append(without)
        rows = reduced


def remove_subsumed(formula: CNFFormula) -> CNFFormula:
    ordered = sorted((frozenset(c.literals) for c in formula.clauses),
                     key=lambda c: (len(c), tuple(sorted(c))))
    retained: list[frozenset[int]] = []
    for clause in ordered:
        if not any(previous.issubset(clause) for previous in retained):
            retained.append(clause)
    return CNFFormula.from_raw_clauses(retained)


def bounded_elimination(formula: CNFFormula, *, max_pairs: int = 12) -> CNFFormula:
    """One Davis-Putnam elimination, only if it strictly reduces clause count."""
    best: CNFFormula | None = None
    for v in formula.variables:
        positive = [c for c in formula.clauses if v in c]
        negative = [c for c in formula.clauses if -v in c]
        if not positive and not negative:
            continue
        if len(positive) * len(negative) > max_pairs:
            continue
        residual = [c for c in formula.clauses if v not in c and -v not in c]
        for p in positive:
            for n in negative:
                clause = resolvent(p, n, v)
                if clause is not None:
                    residual.append(clause)
        reduced = CNFFormula(residual)
        if reduced.num_clauses >= formula.num_clauses:
            continue
        if best is None or (reduced.num_vars, reduced.num_clauses, reduced.formula_hash) < (
                best.num_vars, best.num_clauses, best.formula_hash):
            best = reduced
    return best if best is not None else formula


def parity_root(formula: CNFFormula) -> CNFFormula:
    candidate = compress_binary_xor_components(formula)
    if candidate.get("status") != "UNVERIFIED_STRUCTURAL_CANDIDATE":
        return formula
    return substitute_residual_formula(formula, candidate)


TRANSFORMS: dict[str, Callable[[CNFFormula], CNFFormula]] = {
    "parity_root": parity_root,
    "unit_propagation": unit_propagation,
    "subsumption": remove_subsumed,
    "bounded_elimination": bounded_elimination,
    "invariant_min_fill": min_fill_elimination,
    "invariant_xor_boundary": xor_boundary_elimination,
    "invariant_max_release": max_release_elimination,
}


def structural_score(original: CNFFormula, candidate: CNFFormula) -> float:
    # Fixed coefficients merely rank experiments; they are not a prediction
    # of runtime nor evidence of mathematical novelty.
    return (original.num_vars - candidate.num_vars) * 4.0 + (
        original.num_clauses - candidate.num_clauses) + (
        sum(len(c) for c in original.clauses) -
        sum(len(c) for c in candidate.clauses)) * 0.1


def explore_operators(formula: CNFFormula, *, depth: int = 3,
                      beam_width: int = 12) -> list[Hypothesis]:
    if not 1 <= depth <= 5 or not 1 <= beam_width <= 100:
        raise ValueError("bounded experimental search requires depth 1..5 and beam 1..100")
    frontier = [Hypothesis((), formula, 0.0)]
    seen: dict[str, Hypothesis] = {formula.formula_hash: frontier[0]}
    for _ in range(depth):
        expanded = []
        for node in frontier:
            for name in OPERATORS:
                after = TRANSFORMS[name](node.formula)
                if after == node.formula:
                    continue
                sequence = node.sequence + (name,)
                hypothesis = Hypothesis(sequence, after, structural_score(formula, after))
                prior = seen.get(after.formula_hash)
                if prior is None or (len(sequence), sequence) < (len(prior.sequence), prior.sequence):
                    seen[after.formula_hash] = hypothesis
                    expanded.append(hypothesis)
        if not expanded:
            break
        expanded.sort(key=lambda h: (-h.score, len(h.sequence), h.sequence, h.formula.formula_hash))
        frontier = expanded[:beam_width]
    return sorted(
        (h for h in seen.values() if h.sequence),
        key=lambda h: (-h.score, len(h.sequence), h.sequence, h.formula.formula_hash),
    )[:beam_width]


def independent_sat(formula: CNFFormula) -> dict[str, bool]:
    from pysat.solvers import Glucose3, Minisat22
    outcomes = {}
    for name, cls in (("glucose3", Glucose3), ("minisat22", Minisat22)):
        with cls(bootstrap_with=formula.to_clause_lists()) as solver:
            outcomes[name] = bool(solver.solve())
    if len(set(outcomes.values())) != 1:
        raise AssertionError("independent SAT solvers disagree")
    return outcomes


def assess_hypothesis(original: CNFFormula, hypothesis: Hypothesis) -> dict:
    reference = independent_sat(original)
    comparison = independent_sat(hypothesis.formula)
    agreement = reference == comparison
    best_single = max(structural_score(original, TRANSFORMS[name](original))
                      for name in OPERATORS)
    interaction_gain = hypothesis.score - best_single
    return {
        **hypothesis.record(original),
        "original_satisfiable": reference["glucose3"],
        "candidate_satisfiable": comparison["glucose3"],
        "oracle_agreement": agreement,
        "structural_improvement": hypothesis.score > 0,
        "interaction_gain_over_best_single": round(interaction_gain, 6),
        "operator_interaction_candidate": len(hypothesis.sequence) > 1 and interaction_gain > 0,
        "eligible_for_promotion": False,
        "validation": "ORACLE_AGREEMENT_EXPERIMENTAL" if agreement
                      else "REJECTED_SAT_MISMATCH",
    }
