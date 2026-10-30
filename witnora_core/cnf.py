"""Canonical immutable CNF data structures."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from typing import Iterable, Iterator

Literal = int


class CNFError(ValueError):
    """Raised when a CNF object cannot be constructed safely."""


def literal_sort_key(lit: Literal) -> tuple[int, int]:
    """Sort by variable id, positive before negative for deterministic scans."""

    return (abs(lit), 0 if lit > 0 else 1)


def canonical_literal_tuple(literals: Iterable[Literal]) -> tuple[Literal, ...] | None:
    """Return a sorted duplicate-free tuple, or None for a tautology."""

    seen: set[int] = set()
    tautological = False
    for lit in literals:
        if type(lit) is not int:
            raise CNFError(f"literal is not an integer: {lit!r}")
        if lit == 0:
            raise CNFError("literal 0 is reserved as a DIMACS clause terminator")
        if -lit in seen:
            tautological = True
        seen.add(lit)
    if tautological:
        return None
    return tuple(sorted(seen))


@dataclass(frozen=True, order=True)
class Clause:
    """An immutable canonical clause.

    Tautological clauses are represented by ``None`` from ``from_literals`` and
    are therefore absent from normalized formulas. An empty Clause is a real
    contradiction.
    """

    literals: tuple[Literal, ...]

    def __init__(self, literals: Iterable[Literal] = ()):
        canonical = canonical_literal_tuple(literals)
        if canonical is None:
            raise CNFError("tautological clause cannot be represented as Clause")
        object.__setattr__(self, "literals", canonical)

    @classmethod
    def from_literals(cls, literals: Iterable[Literal]) -> "Clause | None":
        canonical = canonical_literal_tuple(literals)
        if canonical is None:
            return None
        return cls(canonical)

    def __iter__(self) -> Iterator[Literal]:
        return iter(self.literals)

    def __len__(self) -> int:
        return len(self.literals)

    def __contains__(self, item: object) -> bool:
        return item in self.literals

    @property
    def variables(self) -> tuple[int, ...]:
        return tuple(sorted({abs(lit) for lit in self.literals}))

    def without(self, lit: Literal) -> "Clause | None":
        return Clause.from_literals(x for x in self.literals if x != lit)

    def is_subset_of(self, other: "Clause") -> bool:
        return set(self.literals).issubset(other.literals)

    def to_list(self) -> list[int]:
        return list(self.literals)


@dataclass(frozen=True)
class CNFFormula:
    """An immutable normalized CNF formula."""

    clauses: tuple[Clause, ...]

    def __init__(self, clauses: Iterable[Clause | Iterable[Literal]] = ()):
        normalized: dict[tuple[int, ...], Clause] = {}
        for item in clauses:
            if isinstance(item, Clause):
                clause = item
            else:
                maybe_clause = Clause.from_literals(item)
                if maybe_clause is None:
                    continue
                clause = maybe_clause
            normalized[clause.literals] = clause
        object.__setattr__(self, "clauses", tuple(sorted(normalized.values(), key=lambda c: c.literals)))

    @classmethod
    def from_raw_clauses(cls, clauses: Iterable[Iterable[Literal]]) -> "CNFFormula":
        return cls(clauses)

    def __iter__(self) -> Iterator[Clause]:
        return iter(self.clauses)

    def __len__(self) -> int:
        return len(self.clauses)

    def __hash__(self) -> int:
        return hash(self.clauses)

    @property
    def variables(self) -> tuple[int, ...]:
        return tuple(sorted({abs(lit) for clause in self.clauses for lit in clause}))

    @property
    def num_vars(self) -> int:
        return len(self.variables)

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)

    @property
    def max_var(self) -> int:
        return max(self.variables, default=0)

    @property
    def contains_empty_clause(self) -> bool:
        return any(len(clause) == 0 for clause in self.clauses)

    @property
    def is_empty(self) -> bool:
        return len(self.clauses) == 0

    @property
    def is_2cnf(self) -> bool:
        return all(len(clause) <= 2 for clause in self.clauses)

    def canonical_dimacs(self) -> str:
        lines = [f"p cnf {self.max_var} {len(self.clauses)}"]
        for clause in self.clauses:
            if clause.literals:
                lines.append(" ".join(str(lit) for lit in clause.literals) + " 0")
            else:
                lines.append("0")
        return "\n".join(lines) + "\n"

    @property
    def formula_hash(self) -> str:
        return sha256(self.canonical_dimacs().encode("utf-8")).hexdigest()

    def to_clause_lists(self) -> list[list[int]]:
        return [clause.to_list() for clause in self.clauses]

    def without_clause(self, target: Clause) -> "CNFFormula":
        removed = False
        kept: list[Clause] = []
        for clause in self.clauses:
            if not removed and clause == target:
                removed = True
                continue
            kept.append(clause)
        return CNFFormula(kept)


def clause_satisfied(clause: Clause, assignment: dict[int, bool]) -> bool:
    return any(literal_satisfied(lit, assignment) for lit in clause)


def literal_satisfied(lit: Literal, assignment: dict[int, bool]) -> bool:
    value = assignment.get(abs(lit))
    if value is None:
        return False
    return value if lit > 0 else not value


def clause_falsified(clause: Clause, assignment: dict[int, bool]) -> bool:
    for lit in clause:
        var = abs(lit)
        if var not in assignment:
            return False
        if literal_satisfied(lit, assignment):
            return False
    return True


def formula_satisfied(formula: CNFFormula, assignment: dict[int, bool]) -> bool:
    return all(clause_satisfied(clause, assignment) for clause in formula)


def has_tautology(literals: Iterable[Literal]) -> bool:
    seen: set[int] = set()
    for lit in literals:
        if -lit in seen:
            return True
        seen.add(lit)
    return False


def resolvent(a: Clause, b: Clause, pivot: Literal) -> Clause | None:
    lits = [lit for lit in a if lit != pivot] + [lit for lit in b if lit != -pivot]
    return Clause.from_literals(lits)


def all_clause_pairs_variables(clause: Clause) -> Iterator[tuple[int, int]]:
    for a, b in combinations(clause.variables, 2):
        yield (a, b) if a < b else (b, a)


def clause_from_json(data: Iterable[int]) -> Clause:
    return Clause(data)


def formula_from_json(data: Iterable[Iterable[int]]) -> CNFFormula:
    return CNFFormula(Clause(item) for item in data)
