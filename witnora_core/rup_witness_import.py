"""Fail-closed DRUP-to-explicit-RUP witness elaboration.

A CDCL solver supplies *proposed* DRUP additions. Witnora reconstructs
unit-propagation witnesses for each addition. The Lean GeneralRUP checker
then decides whether the annotated proof is valid; the external UNSAT
verdict, DRUP text and Python elaborator are not trusted proof authorities.

Deletions are omitted: retaining additional previously proved clauses is
logically sound for RUP additions. RAT-only clauses are rejected, never
silently accepted. No polynomial proof-size or proof-search claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from .cnf import Clause
from .drat_check import parse_drat_text
from .rup_indexed_propagation import indexed_unit_conflict_witness


@dataclass(frozen=True)
class RUPWitness:
    clause: tuple[int, ...]
    units: tuple[int, ...]


def _clause(literals: Iterable[int]) -> tuple[int, ...]:
    return Clause(literals).literals


def unit_conflict_witness(
    database: list[tuple[int, ...]],
    clause: tuple[int, ...],
    *,
    max_units: int = 100000,
) -> tuple[int, ...] | None:
    """Find a deterministic unit propagation conflict under negated clause.

    Every produced unit has an explicit supporting source/derived clause.
    The Lean checker recomputes the justification and final conflict.
    """
    if max_units < 0:
        raise ValueError("max_units must be nonnegative")
    assumptions = {-lit for lit in clause}
    units: list[int] = []
    for _ in range(max_units + 1):
        forced: int | None = None
        for row in sorted(database, key=lambda r: (len(r), r)):
            if any(lit in assumptions for lit in row):
                continue  # already true under the partial assignment
            unassigned = [lit for lit in row if -lit not in assumptions]
            if not unassigned:
                return tuple(units)
            if len(unassigned) == 1 and forced is None:
                forced = unassigned[0]
        if forced is None or len(units) >= max_units:
            return None
        if forced in assumptions:
            return None
        assumptions.add(forced)
        units.append(forced)
    return None


def verify_native_witness(
    source: list[list[int]],
    proof: list[RUPWitness],
) -> bool:
    """Independent replay for tests; never authorizes a Lean proof status."""
    database = [_clause(row) for row in source]
    for item in proof:
        assumptions = {-lit for lit in item.clause}
        for lit in item.units:
            if not any(
                lit in row and all(x == lit or -x in assumptions for x in row)
                for row in database
            ):
                return False
            assumptions.add(lit)
        if not any(all(-x in assumptions for x in row) for row in database):
            return False
        database.append(item.clause)
    return any(len(row) == 0 for row in database)


def annotate_drup(
    source: list[list[int]],
    proof_lines: list[str],
    *,
    max_additions: int = 20000,
    max_units: int = 100000,
    indexed_propagation: bool = False,
) -> dict:
    """Annotate a solver-generated DRUP trace, rejecting uncheckable lines.

    Returns only witness data and provenance metadata. Acceptance in this
    function is NOT the same as a Lean-verified UNSAT assertion.
    """
    if max_additions <= 0:
        raise ValueError("max_additions must be positive")
    parsed = parse_drat_text("\n".join(proof_lines))
    database = [_clause(row) for row in source]
    additions: list[RUPWitness] = []
    deletions_ignored = 0
    for deletion, clause in parsed:
        if deletion:
            deletions_ignored += 1
            continue
        if len(additions) >= max_additions:
            raise RuntimeError("RUP proof-size bound exceeded")
        producer = indexed_unit_conflict_witness if indexed_propagation else unit_conflict_witness
        units = producer(database, clause, max_units=max_units)
        if units is None:
            raise ValueError("CDCL proof contains an uncheckable RUP addition")
        additions.append(RUPWitness(clause, units))
        database.append(clause)
        if not clause:
            break
    if not additions or additions[-1].clause:
        raise ValueError("DRUP proof never derived the empty clause")
    joined = "\n".join(proof_lines).encode("utf-8")
    return {
        "status": "LEAN_CHECK_PENDING",
        "witness_algorithm": "indexed_occurrence" if indexed_propagation else "reference_full_scan",
        "proof_sha256": sha256(joined).hexdigest(),
        "source_clauses": len(source),
        "original_drup_lines": len(parsed),
        "additions": additions,
        "deletions_ignored": deletions_ignored,
        "unit_witness_literals": sum(len(item.units) for item in additions),
    }


@dataclass(frozen=True)
class IndexedRUPWitness:
    """Untrusted row-index hints for the Lean GeneralRUPIndexed checker."""
    clause: tuple[int, ...]
    units: tuple[tuple[int, int], ...]  # (forced literal, exact reason row ID)
    conflict_id: int


def attach_reason_indices(
    source: list[list[int]],
    additions: list[RUPWitness],
) -> list[IndexedRUPWitness]:
    """Find concrete source/derived row IDs for each proposed unit/conflict.

    Retains every previously proved row, including solver deletion hints
    that were ignored by annotate_drup. The output is never labeled Lean
    verified until GeneralRUPIndexed checks every reference independently.
    """
    database = [_clause(row) for row in source]
    occurrence: dict[int, list[int]] = {}
    for i, row in enumerate(database):
        for lit in row:
            occurrence.setdefault(lit, []).append(i)
    indexed: list[IndexedRUPWitness] = []
    for item in additions:
        assumptions = {-lit for lit in item.clause}
        reasons: list[tuple[int, int]] = []
        for lit in item.units:
            matching = next((i for i in occurrence.get(lit, ())
                             if all(x == lit or -x in assumptions
                                    for x in database[i])), None)
            if matching is None:
                raise ValueError("unit lacks a present, valid indexed reason")
            reasons.append((lit, matching))
            assumptions.add(lit)
        conflict = next((i for i, row in enumerate(database)
                         if all(-x in assumptions for x in row)), None)
        if conflict is None:
            raise ValueError("RUP witness has no present conflict row")
        indexed.append(IndexedRUPWitness(item.clause, tuple(reasons), conflict))
        new_id = len(database)
        database.append(item.clause)
        for lit in item.clause:
            occurrence.setdefault(lit, []).append(new_id)
    if not indexed or indexed[-1].clause:
        raise ValueError("indexed RUP certificate must end with empty clause")
    return indexed


def verify_native_indexed_witness(
    source: list[list[int]],
    proof: list[IndexedRUPWitness],
) -> bool:
    """Direct indexed reason replay for tests, never a Lean trust boundary."""
    database = [_clause(row) for row in source]
    for item in proof:
        assumptions = {-lit for lit in item.clause}
        for lit, row_id in item.units:
            if not (0 <= row_id < len(database)):
                return False
            row = database[row_id]
            if lit not in row or not all(
                x == lit or -x in assumptions for x in row
            ):
                return False
            assumptions.add(lit)
        if not (0 <= item.conflict_id < len(database)):
            return False
        if not all(-lit in assumptions for lit in database[item.conflict_id]):
            return False
        database.append(item.clause)
    return any(not row for row in database)
