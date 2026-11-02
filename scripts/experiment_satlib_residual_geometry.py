"""Structural map of SATLIB's source-bound residual/nonlinear bottleneck.

This is hypothesis triage, not a new SAT algorithm or a proof of optimal
treewidth. It estimates upper bounds using deterministic min-fill, checks
whether elementary binary-implication SCCs add linear facts, and measures the
loss of locality when residual CNF is projected into GF(2) coordinates.

Only the locked historical par32-1-c development instance is accepted.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations
from math import log2

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_affine_dimension_diagnostic import gf2_dimension
from scripts.experiment_verified_flip_orbits import kernel_basis
from witnora_core.cnf import CNFFormula
from witnora_core.xor import detect_cnf_xor_patterns


def _minfill_upper_bound(vertices, clauses, *, include_order=False):
    """Elimination-order *upper bound* on primal treewidth, not a lower bound."""
    graph = {v: set() for v in vertices}
    for clause in clauses:
        for a, b in combinations(sorted(set(clause)), 2):
            graph[a].add(b)
            graph[b].add(a)
    max_width = 0
    first_widths = []
    initial_edges = sum(len(s) for s in graph.values()) // 2
    order = []
    while graph:
        def score(v):
            neighbors = graph[v]
            fill = sum(int(b not in graph[a]) for a, b in combinations(sorted(neighbors), 2))
            return (fill, len(neighbors), v)
        pivot = min(graph, key=score)
        order.append(pivot)
        neighbors = graph[pivot]
        width = len(neighbors)
        max_width = max(max_width, width)
        if len(first_widths) < 10:
            first_widths.append(width)
        for a, b in combinations(sorted(neighbors), 2):
            graph[a].add(b)
            graph[b].add(a)
        for a in neighbors:
            graph[a].discard(pivot)
        del graph[pivot]
    summary = {"minfill_upper_bound_width": max_width, "primal_edges": initial_edges,
               "first_ten_elimination_widths": first_widths}
    if include_order:
        summary["elimination_order"] = order
    return summary


def exact_bounded_width_count(clauses, variables, order, *, parity_variables=(),
                              parity_equations=(), max_scope_cap=16):
    """Exact #SAT of *residual CNF alone* by integer-valued bucket elimination.

    No probabilistic approximation and no use of affine parity equations.
    Every intermediate factor has at most one plus the certified width bits.
    """
    universe = set(variables)
    if len(order) != len(universe) or set(order) != universe:
        raise ValueError("elimination order is not a permutation of variables")
    if not set(parity_variables).issubset(universe):
        raise ValueError("Fourier parity support exceeds source variable domain")
    factors = []
    for clause in clauses:
        scope = tuple(sorted({abs(lit) for lit in clause}))
        if not set(scope).issubset(universe):
            raise ValueError("clause variable outside elimination domain")
        table = []
        for value in range(1 << len(scope)):
            assignment = {v: bool(value & (1 << j)) for j, v in enumerate(scope)}
            table.append(int(any(assignment[abs(lit)] == (lit > 0) for lit in clause)))
        factors.append((scope, table))
    for support, rhs in parity_equations:
        scope = tuple(sorted(set(support)))
        if rhs not in (0, 1) or not set(scope).issubset(universe):
            raise ValueError("malformed local XOR factor")
        if len(scope) > max_scope_cap:
            raise ValueError("local parity equation exceeds factor-width safety cap")
        table = [int((value.bit_count() & 1) == rhs)
                 for value in range(1 << len(scope))]
        factors.append((scope, table))
    for variable in sorted(set(parity_variables)):
        # Exactly compute sum_{x satisfies residual} (-1)^(mask dot x).
        factors.append(((variable,), [1, -1]))
    max_scope = max((len(scope) for scope, _ in factors), default=0)
    for var in order:
        touching = [(scope, table) for scope, table in factors if var in scope]
        factors = [(scope, table) for scope, table in factors if var not in scope]
        if not touching:
            factors.append(((), [2]))
            continue
        union = tuple(sorted(set().union(*(set(scope) for scope, _ in touching))))
        if len(union) > max_scope_cap:
            raise ValueError("joined factor exceeds width safety cap")
        max_scope = max(max_scope, len(union))
        remaining = tuple(v for v in union if v != var)
        positions = {v: i for i, v in enumerate(remaining)}
        projected = []
        for outcome in range(1 << len(remaining)):
            summation = 0
            for truth in (False, True):
                product = 1
                for scope, table in touching:
                    index = 0
                    for j, v in enumerate(scope):
                        bit = int(truth) if v == var else (outcome >> positions[v]) & 1
                        index |= bit << j
                    product *= table[index]
                    if not product:
                        break
                summation += product
            projected.append(summation)
        factors.append((remaining, projected))
    if any(scope for scope, _ in factors):
        raise AssertionError("elimination left variables unresolved")
    count = 1
    for _, table in factors:
        count *= table[0]
    return count, max_scope


def _components(vertices, clauses):
    parent = {v: v for v in vertices}

    def root(x):
        while x != parent[x]:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for clause in clauses:
        values = list(set(clause))
        for x in values[1:]:
            a, b = root(values[0]), root(x)
            parent[a] = b
    counts = Counter(root(v) for v in vertices)
    return sorted(counts.values(), reverse=True)


def binary_scc_equalities(binary_clauses):
    """Equalities implied by 2-SAT literal SCCs; no use of parity row guesses."""
    graph = defaultdict(list)
    reverse = defaultdict(list)
    literals = set()
    for a, b in binary_clauses:
        for source, target in ((-a, b), (-b, a)):
            graph[source].append(target)
            reverse[target].append(source)
            literals.update((source, target, -source, -target))
    seen = set()
    finish = []
    for node in sorted(literals):
        if node in seen:
            continue
        stack = [(node, 0)]
        seen.add(node)
        while stack:
            v, next_index = stack[-1]
            adjacent = graph[v]
            if next_index < len(adjacent):
                neighbor = adjacent[next_index]
                stack[-1] = (v, next_index + 1)
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append((neighbor, 0))
            else:
                finish.append(v)
                stack.pop()
    component = {}
    sizes = []
    for node in reversed(finish):
        if node in component:
            continue
        idx = len(sizes)
        pending = [node]
        component[node] = idx
        n = 0
        while pending:
            v = pending.pop()
            n += 1
            for neighbor in reverse[v]:
                if neighbor not in component:
                    component[neighbor] = idx
                    pending.append(neighbor)
        sizes.append(n)
    if any(component.get(v) == component.get(-v) for v in literals):
        raise AssertionError("binary residual appears UNSAT but source is known SAT")
    groups = defaultdict(list)
    for literal, group in component.items():
        groups[group].append(literal)
    equalities = []
    for group in groups.values():
        if len(group) < 2:
            continue
        base = group[0]
        for other in group[1:]:
            mask = (1 << (abs(base) - 1)) ^ (1 << (abs(other) - 1))
            rhs = int(base * other < 0)
            if mask:
                equalities.append((mask, rhs))
    return equalities, {"scc_count": len(sizes), "nontrivial_scc_count": sum(x > 1 for x in sizes),
                        "max_scc_size": max(sizes, default=0),
                        "literal_scc_equality_candidates": len(equalities)}


def residual_structure(clauses, nvars):
    formula = CNFFormula(clauses)
    detected = detect_cnf_xor_patterns(formula)
    equations = [eq for eq in detected.equations if eq.safe_use and eq.exact_full_encoding]
    source = {tuple(c) for eq in equations for c in eq.source_clauses}
    residual = [tuple(c.literals) for c in formula.clauses if c.literals not in source]
    original_vars = sorted({abs(lit) for clause in residual for lit in clause})
    original_supports = [tuple(sorted({abs(lit) for lit in clause})) for clause in residual]
    rows = [(sum(1 << (v - 1) for v in eq.variables), eq.rhs) for eq in equations]
    dimension = gf2_dimension(nvars, rows)
    if dimension is None:
        raise AssertionError("source XOR constraints inconsistent")
    kernel = kernel_basis(tuple(mask for mask, _ in rows), nvars)
    if len(kernel) != dimension:
        raise AssertionError("invalid source nullspace")
    coordinate_masks = [0] * (nvars + 1)
    for j, vector in enumerate(kernel):
        while vector:
            low = vector & -vector
            coordinate_masks[low.bit_length()] |= 1 << j
            vector ^= low
    projected_supports = []
    for clause in residual:
        support = 0
        for literal in clause:
            support |= coordinate_masks[abs(literal)]
        projected_supports.append(tuple(j for j in range(dimension) if support & (1 << j)))
    binary = [c for c in residual if len(c) == 2]
    added, scc_info = binary_scc_equalities(binary)
    enhanced_dimension = gf2_dimension(nvars, rows + added)
    residual_width = _minfill_upper_bound(original_vars, original_supports,
                                          include_order=True)
    # The order itself is a short, independently checkable certificate of the
    # width bound, unlike the min-fill heuristic's approximation to optimality.
    from witnora_core.treewidth import verify_elimination_order
    graph = {v: set() for v in original_vars}
    for support in original_supports:
        for a, b in combinations(support, 2):
            graph[a].add(b)
            graph[b].add(a)
    certified_width = verify_elimination_order(graph, residual_width["elimination_order"])
    if certified_width != residual_width["minfill_upper_bound_width"]:
        raise AssertionError("residual width certificate verification failed")
    residual_count, max_scope = exact_bounded_width_count(residual, original_vars,
                                                          residual_width["elimination_order"])
    if max_scope > certified_width + 1:
        raise AssertionError("counting factor exceeds graph width certificate")
    log_models = log2(residual_count) if residual_count else None
    deficit = len(original_vars) - log_models if log_models is not None else None
    return {"original_variables": nvars, "source_xor_rows": len(rows),
            "affine_free_dimension": dimension, "source_residual_clauses": len(residual),
            "residual_lengths": dict(sorted(Counter(map(len, residual)).items())),
            "residual_variable_count": len(original_vars),
            "residual_primal": residual_width,
            "residual_width_certificate_verified": True,
            "residual_exact_model_count": str(residual_count),
            "residual_exact_count_factor_max_scope": max_scope,
            "residual_solution_entropy_bits": round(log_models, 5) if log_models is not None else None,
            "residual_clause_entropy_deficit_bits": round(deficit, 5) if deficit is not None else None,
            "random_affine_coset_expected_intersection_log2": round(dimension - deficit, 5)
                if deficit is not None else None,
            "residual_component_sizes": _components(original_vars, original_supports),
            "projected_primal": _minfill_upper_bound(range(dimension), projected_supports),
            "projected_component_sizes": _components(range(dimension), projected_supports),
            "scc": scc_info,
            "scc_derived_extra_rank": dimension - enhanced_dimension,
            "scc_enhanced_affine_dimension": enhanced_dimension,
            "all_residual_support_variables_identified": set(original_vars).issubset(set(range(1, nvars + 1)))}


def benchmark(name="par32-1-c.cnf.Z"):
    if name not in FIXED_SHA:
        raise ValueError("holdout locked: only preregistered source allowed")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("official source SHA changed")
    return {"name": name, "source_sha": source["dimacs_sha256"],
            "structural": residual_structure(source["clause_lists"], source["variables"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="par32-1-c.cnf.Z")
    args = parser.parse_args()
    print(json.dumps(benchmark(name=args.name), indent=2))
