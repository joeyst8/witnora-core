"""Experimental parity-spoke collapse family (not a novelty claim).

For each middle variable y_i, the two equations
    x XOR y_i = left_i
    y_i XOR z = right_i
imply x XOR z = left_i XOR right_i. Conflicting spoke syndromes
prove UNSAT for arbitrarily many spokes, by SpokeCollapse.lean.

The *recognizer* is deliberately restricted to an exact generated CNF.
This is a research baseline, not an unrestricted CNF solver.
"""
from __future__ import annotations

from dataclasses import dataclass

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


@dataclass(frozen=True)
class ParitySpoke:
    middle: int
    left: int
    right: int

    def __post_init__(self):
        if (type(self.middle) is not int or self.middle < 3
                or type(self.left) is not int or self.left not in (0, 1)
                or type(self.right) is not int or self.right not in (0, 1)):
            raise ValueError("invalid parity spoke")

    @property
    def syndrome(self) -> int:
        return self.left ^ self.right


def spoke_cnf(spokes: tuple[ParitySpoke, ...]) -> CNFFormula:
    """Exactly two width-2 XOR encodings per distinct middle variable."""
    mids = [spoke.middle for spoke in spokes]
    if len(set(mids)) != len(mids):
        raise ValueError("spoke intermediates must be distinct")
    clauses: set[tuple[int, ...]] = set()
    for spoke in spokes:
        clauses.update(canonical_xor_cnf_clauses((1, spoke.middle), spoke.left))
        clauses.update(canonical_xor_cnf_clauses((spoke.middle, 2), spoke.right))
    return CNFFormula.from_raw_clauses(sorted(clauses))


def collapse_spokes(
    formula: CNFFormula, spokes: tuple[ParitySpoke, ...]
) -> dict[str, object]:
    """Check exact scope before using the signature contradiction rule."""
    if type(spokes) is not tuple or not spokes:
        return {"status": "UNSUPPORTED"}
    try:
        expected = spoke_cnf(spokes)
    except ValueError:
        return {"status": "UNSUPPORTED"}
    if formula.to_clause_lists() != expected.to_clause_lists():
        return {"status": "UNSUPPORTED"}
    first: dict[int, int] = {}
    for idx, spoke in enumerate(spokes):
        if spoke.syndrome in first:
            continue
        if first:
            earlier = next(iter(first.values()))
            return {
                "status": "UNSAT_BY_SPOKE_SYNDROME",
                "conflicting_indices": [earlier, idx],
                "syndromes": [spokes[earlier].syndrome, spoke.syndrome],
                "claim_boundary": "exact generated spoke CNF; independent Lean theorem",
            }
        first[spoke.syndrome] = idx
    # For distinct intermediates, equal syndromes admit an explicit model.
    signature = spokes[0].syndrome
    assignment = {1: False, 2: bool(signature)}
    assignment.update({spoke.middle: bool(spoke.left) for spoke in spokes})
    return {"status": "SAT_WITH_WITNESS", "assignment": assignment}


def make_spoke_family(count: int, *, contradictory: bool) -> tuple[CNFFormula, tuple[ParitySpoke, ...]]:
    if type(count) is not int or count < 2:
        raise ValueError("need at least two spokes")
    spokes = tuple(
        ParitySpoke(i + 3, i % 2, (i % 2) ^ (int(contradictory) if i == count - 1 else 0))
        for i in range(count)
    )
    return spoke_cnf(spokes), spokes
