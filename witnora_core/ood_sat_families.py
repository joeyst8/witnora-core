"""Out-of-distribution CNF generators never used for operator training.

Each family is constructed independently of Witnora's operator search. The
SAT claims are checked against independent solvers during experiments.
"""
from __future__ import annotations

from itertools import combinations
import random

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


def pigeonhole(pigeons: int, holes: int, *, backend: str = "python") -> CNFFormula:
    if pigeons < 1 or holes < 1:
        raise ValueError("positive pigeonhole dimensions required")
    if backend == "rust":
        from witnora_ve import ood_pigeonhole_native
        return CNFFormula.from_raw_clauses(ood_pigeonhole_native(pigeons, holes))
    if backend != "python":
        raise ValueError("unknown OOD backend")
    def v(p, h):
        return 1 + p * holes + h
    clauses = []
    for p in range(pigeons):
        clauses.append([v(p, h) for h in range(holes)])
    for h in range(holes):
        for p, q in combinations(range(pigeons), 2):
            clauses.append([-v(p, h), -v(q, h)])
    return CNFFormula.from_raw_clauses(clauses)


def graph_coloring(vertices: int, edges: list[tuple[int, int]],
                   colors: int, *, backend: str = "python") -> CNFFormula:
    if vertices < 1 or colors < 1:
        raise ValueError("positive vertices and colors required")
    if backend == "rust":
        from witnora_ve import ood_graph_coloring_native
        return CNFFormula.from_raw_clauses(
            ood_graph_coloring_native(vertices, edges, colors))
    if backend != "python":
        raise ValueError("unknown OOD backend")
    def v(node, color):
        return (node - 1) * colors + color
    clauses = []
    for node in range(1, vertices + 1):
        clauses.append([v(node, c) for c in range(1, colors + 1)])
        for c, d in combinations(range(1, colors + 1), 2):
            clauses.append([-v(node, c), -v(node, d)])
    for u, w in edges:
        if not 1 <= u <= vertices or not 1 <= w <= vertices or u == w:
            raise ValueError("invalid graph edge")
        for c in range(1, colors + 1):
            clauses.append([-v(u, c), -v(w, c)])
    return CNFFormula.from_raw_clauses(clauses)


def tseitin_k4(*, contradictory: bool, backend: str = "python") -> CNFFormula:
    if backend == "rust":
        return tseitin_complete_graph(4, contradictory=contradictory, backend="rust")
    if backend != "python":
        raise ValueError("unknown OOD backend")
    # Six edge variables, each K4 vertex has exactly three incident edges.
    edges = list(combinations(range(1, 5), 2))
    clauses = []
    for vertex in range(1, 5):
        incident = [i + 1 for i, (u, v) in enumerate(edges)
                    if vertex in (u, v)]
        rhs = int(contradictory and vertex == 1)
        clauses.extend(canonical_xor_cnf_clauses(incident, rhs))
    return CNFFormula.from_raw_clauses(clauses)


def n_queens(n: int, *, backend: str = "python") -> CNFFormula:
    if n < 1:
        raise ValueError("positive board size required")
    if backend == "rust":
        from witnora_ve import ood_n_queens_native
        return CNFFormula.from_raw_clauses(ood_n_queens_native(n))
    if backend != "python":
        raise ValueError("unknown OOD backend")
    def v(r, c):
        return 1 + r * n + c
    clauses = []
    for r in range(n):
        clauses.append([v(r, c) for c in range(n)])
        for c, d in combinations(range(n), 2):
            clauses.append([-v(r, c), -v(r, d)])
    for c in range(n):
        for r, s in combinations(range(n), 2):
            clauses.append([-v(r, c), -v(s, c)])
    for (r, c), (s, d) in combinations(
            [(r, c) for r in range(n) for c in range(n)], 2):
        if abs(r - s) == abs(c - d):
            clauses.append([-v(r, c), -v(s, d)])
    return CNFFormula.from_raw_clauses(clauses)


def random_planted_3cnf(n: int, clauses: int, seed: int, *,
                        backend: str = "python") -> CNFFormula:
    if n < 3 or clauses < 0:
        raise ValueError("invalid planted CNF dimensions")
    if backend not in ("python", "rust"):
        raise ValueError("unknown OOD backend")
    rng = random.Random(seed)
    witness = {v: bool(rng.getrandbits(1)) for v in range(1, n + 1)}
    rows = []
    for _ in range(clauses):
        variables = rng.sample(range(1, n + 1), 3)
        row = [v if rng.getrandbits(1) else -v for v in variables]
        if not any((lit > 0) == witness[abs(lit)] for lit in row):
            v = variables[0]
            row[0] = v if witness[v] else -v
        rows.append(row)
    if backend == "rust":
        from witnora_ve import ood_planted_samples_native
        return CNFFormula.from_raw_clauses(ood_planted_samples_native(
            n, [witness[v] for v in range(1, n + 1)], rows))
    return CNFFormula.from_raw_clauses(rows)


def out_of_distribution_cases(seed: int, *, backend: str = "python") -> list[tuple[str, str, CNFFormula, bool | None]]:
    k4_edges = list(combinations(range(1, 5), 2))
    odd_cycle = [(1, 2), (2, 3), (3, 4), (4, 5), (5, 1)]
    return [
        ("pigeonhole", "php_3_into_2", pigeonhole(3, 2, backend=backend), False),
        ("pigeonhole", "php_4_into_3", pigeonhole(4, 3, backend=backend), False),
        ("graph_coloring", "k4_3color", graph_coloring(4, k4_edges, 3, backend=backend), False),
        ("graph_coloring", "odd_cycle_2color", graph_coloring(5, odd_cycle, 2, backend=backend), False),
        ("graph_coloring", "path_3color", graph_coloring(
            5, [(1, 2), (2, 3), (3, 4), (4, 5)], 3, backend=backend), True),
        ("tseitin_3xor", "k4_inconsistent", tseitin_k4(contradictory=True, backend=backend), False),
        ("tseitin_3xor", "k4_consistent", tseitin_k4(contradictory=False, backend=backend), True),
        ("n_queens", "n_queens_3", n_queens(3, backend=backend), False),
        ("n_queens", "n_queens_4", n_queens(4, backend=backend), True),
        ("planted_3cnf", f"planted_{seed}", random_planted_3cnf(10, 42, seed, backend=backend), True),
    ]


def tseitin_complete_graph(vertices: int, *, contradictory: bool,
                           backend: str = "python") -> CNFFormula:
    if vertices < 3 or vertices > 7:
        raise ValueError("bounded complete-graph XOR family requires 3..7 vertices")
    if backend == "rust":
        from witnora_ve import ood_tseitin_complete_native
        return CNFFormula.from_raw_clauses(
            ood_tseitin_complete_native(vertices, contradictory))
    if backend != "python":
        raise ValueError("unknown OOD backend")
    edges = list(combinations(range(1, vertices + 1), 2))
    clauses = []
    for vertex in range(1, vertices + 1):
        incident = [i + 1 for i, (u, v) in enumerate(edges)
                    if vertex in (u, v)]
        rhs = int(contradictory and vertex == 1)
        clauses.extend(canonical_xor_cnf_clauses(incident, rhs))
    return CNFFormula.from_raw_clauses(clauses)


def larger_unseen_cases(seed: int, *, backend: str = "python") -> list[tuple[str, str, CNFFormula, bool | None]]:
    k5 = list(combinations(range(1, 6), 2))
    return [
        ("pigeonhole", "php_5_into_4", pigeonhole(5, 4, backend=backend), False),
        ("pigeonhole", "php_6_into_5", pigeonhole(6, 5, backend=backend), False),
        ("graph_coloring", "k5_4color", graph_coloring(5, k5, 4, backend=backend), False),
        ("tseitin_higher_arity", "k6_inconsistent",
         tseitin_complete_graph(6, contradictory=True, backend=backend), False),
        ("tseitin_higher_arity", "k6_consistent",
         tseitin_complete_graph(6, contradictory=False, backend=backend), True),
        ("n_queens", "n_queens_5", n_queens(5, backend=backend), True),
        ("n_queens", "n_queens_6", n_queens(6, backend=backend), True),
        ("planted_3cnf", f"planted_30_{seed}",
         random_planted_3cnf(30, 130, seed, backend=backend), True),
    ]
