"""Exact low-width nonlinear-plus-local-XOR bridge on original SATLIB PARITY.

Tests whether source-derived narrow parity checks can be absorbed by exact
integer factor elimination without losing the residual graph's locality.
No solver-speed/novelty claim; wide checks remain unprocessed unless a later
method handles them with independently verified source witnesses.
"""
from __future__ import annotations

import argparse
import json
from math import log2

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_satlib_residual_fourier import _bits, source_residual_parity_rows
from scripts.experiment_satlib_residual_geometry import (
    _minfill_upper_bound, exact_bounded_width_count,
)
from witnora_core.treewidth import verify_elimination_order


def syndrome_frontier(order, global_rows):
    """Number of XOR checks spanning each elimination-order boundary.

    This is an upper-bound state-size proxy for an explicit syndrome transfer,
    not a proved minimum rank or hardness lower bound.
    """
    if len(order) != len(set(order)):
        raise ValueError("repeated variable in elimination order")
    pos = {v: i for i, v in enumerate(order)}
    changes = [0] * (len(order) + 1)
    for variables, _ in global_rows:
        if not set(variables).issubset(pos):
            raise ValueError("global parity check outside variable domain")
        if not variables:
            continue
        start, end = min(pos[v] for v in variables), max(pos[v] for v in variables)
        changes[start] += 1
        changes[end] -= 1
    active = 0
    per_cut = []
    for k in range(len(order) - 1):
        active += changes[k]
        per_cut.append(active)
    return {"maximum_active_global_rows": max(per_cut, default=0),
            "mean_active_global_rows": round(sum(per_cut) / len(per_cut), 3)
                if per_cut else 0,
            "cuts_with_more_than_16_active_rows": sum(v > 16 for v in per_cut),
            "cuts_with_more_than_24_active_rows": sum(v > 24 for v in per_cut)}


def syndrome_cut_rank(order, global_rows):
    """Binary-matroid connectivity of the wide-row column space across cuts.

    Unlike a raw count of active checks, lambda(A) = rank(M_A) + rank(M_B)
    - rank(M) is invariant under invertible XOR row operations. It measures
    the shared parity-message dimension for a partition, but is not a proof
    of general SAT or tensor-network lower bounds.
    """
    if len(order) != len(set(order)):
        raise ValueError("repeated variable in elimination order")
    position = {v: i for i, v in enumerate(order)}
    columns = [0] * len(order)
    for row_index, (variables, _) in enumerate(global_rows):
        for variable in variables:
            if variable not in position:
                raise ValueError("parity variable absent from elimination domain")
            columns[position[variable]] ^= 1 << row_index

    def add_basis(basis, value):
        while value:
            bit = value.bit_length() - 1
            if bit not in basis:
                basis[bit] = value
                return
            value ^= basis[bit]

    prefix_rank = []
    basis = {}
    for column in columns:
        add_basis(basis, column)
        prefix_rank.append(len(basis))
    full_rank = len(basis)
    suffix_rank = [0] * (len(columns) + 1)
    basis = {}
    for i in range(len(columns) - 1, -1, -1):
        add_basis(basis, columns[i])
        suffix_rank[i] = len(basis)
    connectivity = [prefix_rank[i] + suffix_rank[i + 1] - full_rank
                    for i in range(len(columns) - 1)]
    if any(v < 0 for v in connectivity):
        raise AssertionError("negative binary-matroid connectivity")
    return {"global_row_rank": full_rank,
            "maximum_cut_connectivity_rank": max(connectivity, default=0),
            "mean_cut_connectivity_rank": round(sum(connectivity) / len(connectivity), 3)
                if connectivity else 0,
            "cuts_with_rank_over_16": sum(v > 16 for v in connectivity),
            "cuts_with_rank_over_24": sum(v > 24 for v in connectivity)}


def local_bridge(clauses, nvars, *, max_local_width=3, max_graph_width=12):
    if max_local_width != 3 or not (1 <= max_graph_width <= 12):
        raise ValueError("operator gate parameters are frozen")
    residual, variables, rows, metadata = source_residual_parity_rows(clauses, nvars)
    local = [(tuple(_bits(mask)), rhs) for mask, rhs in rows if mask.bit_count() <= 3]
    wide = [(tuple(_bits(mask)), rhs) for mask, rhs in rows if mask.bit_count() > 3]
    supports = [tuple(abs(lit) for lit in c) for c in residual]
    original = _minfill_upper_bound(variables, supports)
    with_local = _minfill_upper_bound(
        variables, supports + [tuple(vs) for vs, _ in local], include_order=True)
    estimate = with_local["minfill_upper_bound_width"]
    result = {"original_residual_graph_width_upper_bound": original["minfill_upper_bound_width"],
              "local_plus_residual_graph_width_upper_bound": estimate,
              "source_derived_local_xor_rows": len(local),
              "unprocessed_global_xor_rows": len(wide),
              "global_row_widths": [len(vs) for vs, _ in wide],
              "source_xor_rank": metadata["independent_xor_rank"],
              "remaining_linear_free_dimensions": nvars - metadata["independent_xor_rank"],
              "width_cap": max_graph_width}
    if estimate > max_graph_width:
        result["status"] = "SKIP_WIDTH_CAP"
        return result
    graph = {v: set() for v in variables}
    from itertools import combinations
    for support in supports + [tuple(vs) for vs, _ in local]:
        for a, b in combinations(set(support), 2):
            graph[a].add(b)
            graph[b].add(a)
    order = with_local["elimination_order"]
    certified = verify_elimination_order(graph, order)
    if certified != estimate:
        raise AssertionError("local bridge width certificate invalid")
    count, max_scope = exact_bounded_width_count(residual, variables, order,
                                                 parity_equations=local,
                                                 max_scope_cap=max_graph_width + 1)
    if max_scope > estimate + 1:
        raise AssertionError("local bridge exceeded certified factor width")
    if count == 0:
        raise AssertionError("the known SAT source cannot have zero local models")
    natural_order = sorted(variables)
    reverse_order = list(reversed(natural_order))
    result.update({"status": "EXACT_LOCAL_COUNT", "width_certificate_verified": True,
                   "max_counting_factor_scope": max_scope,
                   "exact_residual_plus_local_models": str(count),
                   "local_model_log2": round(log2(count), 5),
                   "uniform_global_rhs_expected_solutions_log2": round(log2(count) - len(wide), 5),
                   "syndrome_frontier_minfill": syndrome_frontier(order, wide),
                   "syndrome_frontier_natural": syndrome_frontier(natural_order, wide),
                   "syndrome_frontier_reverse": syndrome_frontier(reverse_order, wide),
                   "cut_rank_minfill": syndrome_cut_rank(order, wide),
                   "cut_rank_natural": syndrome_cut_rank(natural_order, wide),
                   "cut_rank_reverse": syndrome_cut_rank(reverse_order, wide),
                   "graph_width_natural_order": verify_elimination_order(graph, natural_order),
                   "graph_width_reverse_order": verify_elimination_order(graph, reverse_order)})
    return result


def benchmark(name="par32-1-c.cnf.Z"):
    if name not in FIXED_SHA:
        raise ValueError("holdout locked")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("source changed")
    return {"benchmark": name, "source_sha": source["dimacs_sha256"],
            "local_bridge": local_bridge(source["clause_lists"], source["variables"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="par32-1-c.cnf.Z")
    args = parser.parse_args()
    print(json.dumps(benchmark(args.name), indent=2))
