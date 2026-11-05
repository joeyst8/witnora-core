"""Experimental structure-guided failed-literal probing.

This is an established SAT inference technique, not a novel theorem or rule.
The resulting CNF preserves SAT/UNSAT, not necessarily the original model set.
"""
from __future__ import annotations

from .cnf import CNFFormula
from .experimental_operator_search import unit_propagation


def unit_conflict(formula: CNFFormula, assumed_literal: int) -> bool:
    """Does unit propagation derive a contradiction under this assumption?"""
    assigned: dict[int, bool] = {}
    pending = [assumed_literal]
    while pending:
        lit = pending.pop()
        var, value = abs(lit), lit > 0
        if var in assigned:
            if assigned[var] != value:
                return True
            continue
        assigned[var] = value
        for clause in formula.clauses:
            undecided = []
            satisfied = False
            for item in clause:
                known = assigned.get(abs(item))
                if known is None:
                    undecided.append(item)
                elif known == (item > 0):
                    satisfied = True
                    break
            if satisfied:
                continue
            if not undecided:
                return True
            if len(undecided) == 1:
                pending.append(undecided[0])
    return False


def probe_forced_relations(formula: CNFFormula, *, max_probes: int = 12
                           ) -> tuple[CNFFormula, dict]:
    """Check high-occurrence variables first and add only justified forced units."""
    if not 0 <= max_probes <= 256:
        raise ValueError("invalid bounded probing budget")
    occurrences = {var: 0 for var in formula.variables}
    for clause in formula.clauses:
        for lit in clause:
            occurrences[abs(lit)] += 1
    pivots = sorted(formula.variables, key=lambda v: (-occurrences[v], v))
    augmented = formula
    forced = []
    checked = 0
    both_conflict = False
    for pivot in pivots[:max_probes]:
        positive_fails = unit_conflict(augmented, pivot)
        negative_fails = unit_conflict(augmented, -pivot)
        checked += 1
        if positive_fails and negative_fails:
            augmented = CNFFormula.from_raw_clauses([[]])
            both_conflict = True
            break
        if positive_fails != negative_fails:
            forced_lit = -pivot if positive_fails else pivot
            forced.append(forced_lit)
            augmented = CNFFormula([*augmented.clauses, [forced_lit]])
    simplified = unit_propagation(augmented)
    return simplified, {
        "checked_variables": checked,
        "forced_literals": forced,
        "both_assumptions_conflict": both_conflict,
        "source_sha256": formula.formula_hash,
        "candidate_sha256": simplified.formula_hash,
        "rule": "bounded_failed_literal_probing",
        "novelty_verified": False, "lean_verified": False, "promoted": False,
    }


def unit_conflict_rust(formula: CNFFormula, assumed_literal: int) -> bool:
    """Opt-in Rust assumption-propagation conflict check."""
    from witnora_ve import unit_conflict_native

    return bool(unit_conflict_native(formula.to_clause_lists(), assumed_literal))


def probe_forced_relations_rust(
    formula: CNFFormula, *, max_probes: int = 12,
) -> tuple[CNFFormula, dict]:
    """Opt-in Rust bounded failed-literal probing with original metadata."""
    from witnora_ve import probe_forced_relations_native

    clauses, checked, forced, both, source_hash, candidate_hash = (
        probe_forced_relations_native(formula.to_clause_lists(), max_probes)
    )
    return CNFFormula.from_raw_clauses(clauses), {
        "checked_variables": checked,
        "forced_literals": list(forced),
        "both_assumptions_conflict": bool(both),
        "source_sha256": source_hash,
        "candidate_sha256": candidate_hash,
        "rule": "bounded_failed_literal_probing",
        "novelty_verified": False, "lean_verified": False, "promoted": False,
    }
