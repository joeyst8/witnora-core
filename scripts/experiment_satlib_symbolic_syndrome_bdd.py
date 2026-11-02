"""Exact source-bound syndrome-set compilation by local-factor DP + ROBDD.

Each local assignment contributes a 32-bit XOR syndrome. The DP merges equal
live-frontier assignments and combines their syndrome sets by BDD union,
using XOR-coordinate permutation for every chosen variable. The final BDD
represents *all* feasible right syndromes, not a sample or learned subset.

This is established variable elimination and reduced ordered decision-diagram
technology; it is an exploratory performance gate, not a novelty claim.
"""
from __future__ import annotations

import argparse
import json
from functools import lru_cache
from hashlib import sha256
from multiprocessing import get_context
from time import perf_counter

from scripts.benchmark_real_satlib_parity_gate import fetch_file
from scripts.experiment_satlib_affine_quotient import FIXED_SHA
from scripts.experiment_satlib_incremental_syndrome_oracle import (
    _source_side_solver, assumptions_for_syndrome, make_syndrome_oracle,
)
from scripts.experiment_satlib_syndrome_mitm import (
    candidate_natural_separators, exact_separator_counts,
    lift_original_xor_variables, parity_columns, source_local_global,
    split_local_factors,
)


class SymbolicLimit(Exception):
    """Exact compilation did not finish inside a preregistered resource cap."""


class SyndromeBDD:
    """Canonical ROBDD for sets of width-bit unsigned syndrome vectors."""

    def __init__(self, width=32, *, node_cap=500_000, memo_cap=1_000_000):
        if not (1 <= width <= 32 and node_cap >= width + 2):
            raise ValueError("invalid exact decision diagram width or node cap")
        self.width = width
        self.node_cap = node_cap
        self.memo_cap = memo_cap
        self.nodes = [None, None]  # False, True
        self.unique = {}
        self.unions = {}
        self.intersections = {}
        self.shifts = {}
        self.union_calls = 0
        self.shift_calls = 0
        self.zero_vector = 1
        for bit in reversed(range(width)):
            self.zero_vector = self.node(bit, self.zero_vector, 0)

    def node(self, bit, lo, hi):
        if lo == hi:
            return lo
        key = (bit, lo, hi)
        found = self.unique.get(key)
        if found is not None:
            return found
        if len(self.nodes) - 2 >= self.node_cap:
            raise SymbolicLimit("BDD_NODE_CAP")
        result = len(self.nodes)
        self.nodes.append(key)
        self.unique[key] = result
        return result

    def union(self, a, b):
        if a == b or b == 0:
            return a
        if a == 0 or b == 1:
            return b
        if a == 1:
            return a
        if b < a:
            a, b = b, a
        key = (a, b)
        old = self.unions.get(key)
        if old is not None:
            return old
        self.union_calls += 1
        if len(self.unions) >= self.memo_cap:
            raise SymbolicLimit("BDD_UNION_MEMO_CAP")
        x, xa, xb = self.nodes[a]
        y, ya, yb = self.nodes[b]
        bit = min(x, y)
        a0, a1 = (xa, xb) if x == bit else (a, a)
        b0, b1 = (ya, yb) if y == bit else (b, b)
        result = self.node(bit, self.union(a0, b0), self.union(a1, b1))
        self.unions[key] = result
        return result

    def xor_translate(self, root, mask):
        if mask & ~((1 << self.width) - 1):
            raise ValueError("syndrome column outside BDD width")
        if root <= 1 or mask == 0:
            return root
        key = (root, mask)
        old = self.shifts.get(key)
        if old is not None:
            return old
        self.shift_calls += 1
        if len(self.shifts) >= self.memo_cap:
            raise SymbolicLimit("BDD_XOR_MEMO_CAP")
        bit, lo, hi = self.nodes[root]
        lo = self.xor_translate(lo, mask)
        hi = self.xor_translate(hi, mask)
        result = self.node(bit, hi, lo) if mask & (1 << bit) else self.node(bit, lo, hi)
        self.shifts[key] = result
        return result

    def intersect(self, a, b):
        """Exact shared-manager conjunction of two syndrome sets."""
        if a == b or b == 1:
            return a
        if b == 0 or a == 0:
            return 0
        if a == 1:
            return b
        if b < a:
            a, b = b, a
        key = (a, b)
        old = self.intersections.get(key)
        if old is not None:
            return old
        if len(self.intersections) >= self.memo_cap:
            raise SymbolicLimit("BDD_INTERSECT_MEMO_CAP")
        x, xa, xb = self.nodes[a]
        y, ya, yb = self.nodes[b]
        bit = min(x, y)
        a0, a1 = (xa, xb) if x == bit else (a, a)
        b0, b1 = (ya, yb) if y == bit else (b, b)
        result = self.node(bit, self.intersect(a0, b0), self.intersect(a1, b1))
        self.intersections[key] = result
        return result

    def choose_member(self, root):
        """Produce a true syndrome or None if this exact set is empty."""
        if root == 0:
            return None
        value = 0
        while root > 1:
            bit, lo, hi = self.nodes[root]
            if lo != 0:
                root = lo
            else:
                value |= 1 << bit
                root = hi
        return value

    def contains(self, root, signature):
        if not 0 <= signature < (1 << self.width):
            return False
        while root > 1:
            bit, lo, hi = self.nodes[root]
            root = hi if signature & (1 << bit) else lo
        return root == 1

    def reachable_nodes(self, root):
        seen = set()
        pending = [root]
        while pending:
            current = pending.pop()
            if current <= 1 or current in seen:
                continue
            seen.add(current)
            _, lo, hi = self.nodes[current]
            pending.extend((lo, hi))
        return len(seen)

    def cardinality(self, root):
        """Exact number of satisfying width-bit syndromes (including skipped bits)."""
        @lru_cache(None)
        def from_node(node):
            if node == 0:
                return 0
            if node == 1:
                return 1
            bit, lo, hi = self.nodes[node]

            def suffix(child):
                if child == 0:
                    return 0
                if child == 1:
                    return 1 << (self.width - bit - 1)
                next_bit = self.nodes[child][0]
                return (1 << (next_bit - bit - 1)) * from_node(child)

            return suffix(lo) + suffix(hi)

        if root <= 1:
            return (1 << self.width) if root else 0
        return (1 << self.nodes[root][0]) * from_node(root)


def project_side_factors(split, side, boundary_bits):
    """Substitute fixed boundary bits in original local CNF and local XOR."""
    boundary = {v: bool(boundary_bits & (1 << i))
                for i, v in enumerate(split["boundary"])}
    factors = []
    for clause in split[f"{side}_clauses"]:
        if any(boundary.get(abs(l), None) == (l > 0) for l in clause
               if abs(l) in boundary):
            continue
        rest = tuple(l for l in clause if abs(l) not in boundary)
        if not rest:
            return None
        factors.append(("cnf", rest, False))
    for support, rhs in split[f"{side}_xors"]:
        reduced_rhs = int(rhs)
        rest = []
        for var in support:
            if var in boundary:
                reduced_rhs ^= int(boundary[var])
            else:
                rest.append(var)
        if not rest:
            if reduced_rhs:
                return None
            continue
        factors.append(("xor", tuple(rest), bool(reduced_rhs)))
    return factors


def symbolic_side_syndromes(split, side, boundary_bits, columns, *,
                            width=32, deadline=None, node_cap=500_000,
                            state_cap=100_000, bdd=None):
    """Compile all local-valid side-interior syndromes; count source models too.

    State (live frontier assignment -> (syndrome ROBDD, number of paths))
    is exact: factor validity is checked when each factor's last variable
    enters. Eliminated past variables affect only the accumulated syndrome.
    """
    interior = tuple(v for v in split[f"{side}_vars"]
                     if v not in split["boundary"])
    factors = project_side_factors(split, side, boundary_bits)
    if bdd is None:
        bdd = SyndromeBDD(width, node_cap=node_cap)
    elif bdd.width != width:
        raise ValueError("shared BDD manager width mismatch")
    before_nodes = len(bdd.nodes) - 2
    if factors is None:
        return bdd, 0, {"models": 0, "states_peak": 0, "bdd_nodes": 0}
    end_at = {v: [] for v in interior}
    last_mention = {v: v for v in interior}
    for kind, literals, rhs in factors:
        scope = tuple(abs(l) if kind == "cnf" else l for l in literals)
        if not scope or any(v not in last_mention for v in scope):
            raise AssertionError("bad projected factor support")
        final_var = max(scope)
        end_at[final_var].append((kind, literals, rhs))
        for v in scope:
            last_mention[v] = max(last_mention[v], final_var)
    active = ()
    states = {0: (bdd.zero_vector, 1)}
    max_states = 1
    max_frontier = 0
    processed = 0
    for v in interior:
        if deadline is not None and perf_counter() > deadline:
            raise SymbolicLimit("SYMBOLIC_TIME_BUDGET")
        bit = 1 << (v - 1)
        keep = tuple(w for w in active + (v,) if last_mention[w] > v)
        keep_mask = sum(1 << (w - 1) for w in keep)
        next_states = {}
        for oldmask, (root, count) in states.items():
            for truth in (False, True):
                assignment = oldmask | bit if truth else oldmask
                valid = True
                for kind, literals, rhs in end_at[v]:
                    if kind == "cnf":
                        if not any(bool(assignment & (1 << (abs(l) - 1))) == (l > 0)
                                   for l in literals):
                            valid = False
                            break
                    elif (sum(bool(assignment & (1 << (u - 1)))
                              for u in literals) & 1) != int(rhs):
                        valid = False
                        break
                if not valid:
                    continue
                newmask = assignment & keep_mask
                contribution = bdd.xor_translate(root, columns.get(v, 0)) if truth else root
                old = next_states.get(newmask)
                if old is None:
                    next_states[newmask] = (contribution, count)
                else:
                    next_states[newmask] = (bdd.union(old[0], contribution), old[1] + count)
        states = next_states
        active = keep
        processed += 1
        max_states = max(max_states, len(states))
        max_frontier = max(max_frontier, len(active))
        if len(states) > state_cap:
            raise SymbolicLimit("DP_STATE_CAP")
        if not states:
            break
    if states and set(states) != {0}:
        raise AssertionError("nonempty variable frontier at final step")
    root, models = states.get(0, (0, 0))
    stats = {"models": models, "processed_variables": processed,
             "states_peak": max_states, "frontier_width_peak": max_frontier,
             "bdd_nodes_allocated": len(bdd.nodes) - 2,
             "bdd_nodes_allocated_during_side": len(bdd.nodes) - 2 - before_nodes,
             "bdd_nodes_reachable": bdd.reachable_nodes(root),
             "bdd_unique_syndromes": bdd.cardinality(root),
             "bdd_union_calls": bdd.union_calls, "bdd_xor_translate_calls": bdd.shift_calls}
    if stats["bdd_unique_syndromes"] > models:
        raise AssertionError("symbolic feasible syndrome count exceeds source models")
    return bdd, root, stats


def add_bdd_acceptance_gate(solver, bdd, root, syndrome_indicators, xor_shift):
    """Enforce BDD acceptance of indicator XOR xor_shift with exact CNF.

    A true node variable implies acceptance of the selected successor. The
    root is required true; unvisited nodes may be assigned false. The
    encoding is equisatisfiable for every fixed indicator assignment.
    """
    if len(syndrome_indicators) != bdd.width:
        raise ValueError("syndrome indicator width mismatch")
    if xor_shift & ~((1 << bdd.width) - 1):
        raise ValueError("syndrome shift outside width")
    if root == 0:
        solver.add_clause([])
        return {"bdd_gate_nodes": 0, "bdd_gate_clauses": 1}
    if root == 1:
        return {"bdd_gate_nodes": 0, "bdd_gate_clauses": 0}
    seen = set()
    todo = [root]
    while todo:
        current = todo.pop()
        if current <= 1 or current in seen:
            continue
        seen.add(current)
        _, lo, hi = bdd.nodes[current]
        todo.extend((lo, hi))
    next_var = max(syndrome_indicators) + 1
    gate_vars = {node: next_var + i for i, node in enumerate(sorted(seen))}
    clauses = 0
    solver.add_clause([gate_vars[root]])
    clauses += 1
    for node in sorted(seen):
        bit, lo, hi = bdd.nodes[node]
        x = syndrome_indicators[bit]
        if xor_shift & (1 << bit):
            x = -x
        parent_false = -gate_vars[node]
        # Low successor selected when x is false.
        if lo != 1:
            solver.add_clause([parent_false, x] + ([gate_vars[lo]] if lo else []))
            clauses += 1
        # High successor selected when x is true.
        if hi != 1:
            solver.add_clause([parent_false, -x] + ([gate_vars[hi]] if hi else []))
            clauses += 1
    return {"bdd_gate_nodes": len(seen), "bdd_gate_clauses": clauses}


def sparse_side_syndromes(split, side, boundary_bits, columns, *,
                          deadline=None, entry_cap=250_000):
    """Exact sparse frontier transfer with one source witness per syndrome.

    This is a constrained-control counterpart to ROBDD compilation. It is
    allowed only on the pre-counted smaller side and checked against the
    independent bucket-elimination count, so there is no hidden truncation.
    """
    interior = tuple(v for v in split[f"{side}_vars"]
                     if v not in split["boundary"])
    factors = project_side_factors(split, side, boundary_bits)
    if factors is None:
        return {}, {"models": 0, "unique_syndromes": 0, "peak_entries": 0}
    end_at = {v: [] for v in interior}
    last_mention = {v: v for v in interior}
    for kind, literals, rhs in factors:
        scope = tuple(abs(l) if kind == "cnf" else l for l in literals)
        if not scope or any(v not in last_mention for v in scope):
            raise AssertionError("bad sparse projected factor")
        final_var = max(scope)
        end_at[final_var].append((kind, literals, rhs))
        for v in scope:
            last_mention[v] = max(last_mention[v], final_var)
    # Build the complete width-bounded live-frontier transition graph first.
    # Backward reachability from the terminal state prunes prefixes that are
    # locally consistent so far but cannot satisfy later source factors.
    active = ()
    reachable = {0}
    transition_layers = []
    peak_frontier = 0
    for v in interior:
        bit = 1 << (v - 1)
        keep = tuple(w for w in active + (v,) if last_mention[w] > v)
        keep_mask = sum(1 << (w - 1) for w in keep)
        layer = {}
        new_reachable = set()
        for oldmask in reachable:
            choices = []
            for truth in (False, True):
                assignment = oldmask | bit if truth else oldmask
                valid = True
                for kind, literals, rhs in end_at[v]:
                    if kind == "cnf":
                        if not any(bool(assignment & (1 << (abs(l) - 1))) == (l > 0)
                                   for l in literals):
                            valid = False
                            break
                    elif (sum(bool(assignment & (1 << (u - 1)))
                              for u in literals) & 1) != int(rhs):
                        valid = False
                        break
                if valid:
                    newmask = assignment & keep_mask
                    choices.append((newmask, truth))
                    new_reachable.add(newmask)
            if choices:
                layer[oldmask] = choices
        transition_layers.append(layer)
        reachable = new_reachable
        active = keep
        peak_frontier = max(peak_frontier, len(active))
    viable_after = {0}
    pruned_layers = [None] * len(interior)
    for i in reversed(range(len(interior))):
        layer = {}
        for oldmask, choices in transition_layers[i].items():
            kept = [choice for choice in choices if choice[0] in viable_after]
            if kept:
                layer[oldmask] = kept
        pruned_layers[i] = layer
        viable_after = set(layer)
    if 0 not in viable_after:
        return {}, {"models": 0, "unique_syndromes": 0,
                    "peak_entries": 0, "peak_frontier_width": peak_frontier}

    states = {0: ({0: 0}, 1)}
    peak_entries = 1
    for v, layer in zip(interior, pruned_layers):
        if deadline is not None and perf_counter() > deadline:
            raise SymbolicLimit("SPARSE_TIME_BUDGET")
        bit = 1 << (v - 1)
        next_states = {}
        for oldmask, (signatures, count) in states.items():
            for newmask, truth in layer.get(oldmask, ()):
                old = next_states.get(newmask)
                if old is None:
                    old = ({}, 0)
                output, previous_count = old
                next_states[newmask] = (output, previous_count + count)
                column = columns.get(v, 0) if truth else 0
                for signature, witness in signatures.items():
                    output.setdefault(signature ^ column, witness | bit if truth else witness)
        states = next_states
        total_entries = sum(len(sigs) for sigs, _ in states.values())
        peak_entries = max(peak_entries, total_entries)
        if total_entries > entry_cap:
            raise SymbolicLimit("SPARSE_ENTRY_CAP")
    if states and set(states) != {0}:
        raise AssertionError("sparse live frontier at final variable")
    signatures, models = states.get(0, ({}, 0))
    return signatures, {"models": models, "unique_syndromes": len(signatures),
                        "peak_entries": peak_entries,
                        "peak_frontier_width": peak_frontier}


def symbolic_syndrome_search(raw_clauses, nvars, *, time_budget_s=30,
                             node_cap=500_000, state_cap=100_000,
                             two_sided=False, bdd_gated=False, sparse_join=True):
    if not (0 < time_budget_s <= 60 and 100 <= node_cap <= 2_000_000):
        raise ValueError("invalid frozen symbolic gate")
    if sum((bool(two_sided), bool(bdd_gated), bool(sparse_join))) > 1:
        raise ValueError("choose one exact symbolic join strategy")
    start = perf_counter()
    deadline = start + time_budget_s
    try:
        residual, variables, local, global_rows, _, source_equations = source_local_global(
            raw_clauses, nvars, return_source_equations=True)
        candidates = candidate_natural_separators(variables, residual, local)
        split = split_local_factors(residual, variables, local, candidates[0])
        source_ms = round((perf_counter() - start) * 1000, 2)
        counts = exact_separator_counts(split)
        count_ms = round((perf_counter() - start) * 1000 - source_ms, 2)
        if counts["local_model_count_from_join"] != 704494193:
            raise AssertionError("local model count disagrees with source audit")
        columns, target = parity_columns(global_rows)
        boundary = split["boundary"]
        batches = sorted(counts["conditional_model_counts"],
                         key=lambda r: (-(r["left"] * r["right"]), r["boundary_bits"]))
        records = []
        for batch in batches:
            b = batch["boundary_bits"]
            small = "left" if batch["left"] <= batch["right"] else "right"
            large = "right" if small == "left" else "left"
            if min(batch["left"], batch["right"]) > 50000:
                records.append({"boundary_bits": b, "status": "SKIP_SMALL_SIDE_CAP"})
                continue
            if perf_counter() > deadline:
                raise SymbolicLimit("SYMBOLIC_TIME_BUDGET")
            build_start = perf_counter()
            shared_bdd = SyndromeBDD(32, node_cap=node_cap) if two_sided else None
            bdd, root, stats = symbolic_side_syndromes(
                split, large, b, columns, deadline=deadline,
                node_cap=node_cap, state_cap=state_cap, bdd=shared_bdd)
            build_ms = round((perf_counter() - build_start) * 1000, 2)
            if stats["models"] != batch[large]:
                raise AssertionError("symbolic model count disagrees with exact bucket count")
            bsyndrome = 0
            for j, v in enumerate(boundary):
                if b & (1 << j):
                    bsyndrome ^= columns.get(v, 0)
            if two_sided:
                _, small_root, small_stats = symbolic_side_syndromes(
                    split, small, b, columns, deadline=deadline,
                    node_cap=node_cap, state_cap=state_cap, bdd=bdd)
                if small_stats["models"] != batch[small]:
                    raise AssertionError("small symbolic count disagrees with exact bucket count")
                needed = target ^ bsyndrome
                compatible = bdd.intersect(small_root, bdd.xor_translate(root, needed))
                left_syndrome = bdd.choose_member(compatible)
                if left_syndrome is None:
                    records.append({"boundary_bits": b, "status": "EXACT_BDD_NO_JOIN",
                                    "small_symbolic": small_stats, "large_symbolic": stats})
                    continue
                right_syndrome = left_syndrome ^ needed
                chosen_models = {}
                for which, signature in ((small, left_syndrome), (large, right_syndrome)):
                    solver, indicators = make_syndrome_oracle(split, which, b,
                                                               global_rows, nvars)
                    sat, model = solver.solve(
                        assumptions=assumptions_for_syndrome(indicators, signature))
                    if not sat:
                        raise AssertionError("BDD join contradicted by native source side")
                    chosen_models[which] = model
                combined = sum(1 << (v - 1) for j, v in enumerate(boundary)
                               if b & (1 << j))
                for which in (small, large):
                    for v in split[f"{which}_vars"]:
                        if v not in boundary and chosen_models[which][v]:
                            combined |= 1 << (v - 1)
                assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
                full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                                   source_equations=source_equations)
                digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
                return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                        "matched_boundary_bits": b,
                        "large_symbolic": stats, "small_symbolic": small_stats,
                        "bdd_join_nodes_reachable": bdd.reachable_nodes(compatible),
                        "bdd_nodes_total": len(bdd.nodes) - 2,
                        "source_ms": source_ms, "exact_count_ms": count_ms,
                        "compile_and_join_ms": round((perf_counter() - build_start) * 1000, 2),
                        "side_oracle_queries": 2,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                        "records": records}
            if sparse_join:
                sparse_start = perf_counter()
                small_signatures, small_stats = sparse_side_syndromes(
                    split, small, b, columns, deadline=deadline)
                if small_stats["models"] != batch[small]:
                    raise AssertionError("sparse left model count violates exact count")
                needed = target ^ bsyndrome
                matched = next(((signature, witness, signature ^ needed)
                                for signature, witness in small_signatures.items()
                                if bdd.contains(root, signature ^ needed)), None)
                if matched is None:
                    records.append({"boundary_bits": b, "status": "EXACT_SPARSE_BDD_NO_JOIN",
                                    "symbolic": stats, "small_sparse": small_stats})
                    continue
                _, smallmask, wanted = matched
                large_solver, indicators = make_syndrome_oracle(
                    split, large, b, global_rows, nvars)
                sat_large, large_model = large_solver.solve(
                    assumptions=assumptions_for_syndrome(indicators, wanted))
                if not sat_large:
                    raise AssertionError("exact sparse/BDD join contradicted native side")
                combined = smallmask | sum(1 << (v - 1)
                                           for j, v in enumerate(boundary) if b & (1 << j))
                for v in split[f"{large}_vars"]:
                    if v not in boundary and large_model[v]:
                        combined |= 1 << (v - 1)
                assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
                full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                                   source_equations=source_equations)
                digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
                return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                        "matched_boundary_bits": b,
                        "symbolic": stats, "small_sparse": small_stats,
                        "source_ms": source_ms, "exact_count_ms": count_ms,
                        "compile_ms": build_ms,
                        "sparse_join_and_verify_ms": round((perf_counter() - sparse_start) * 1000, 2),
                        "right_oracle_queries": 1,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                        "records": records}
            if bdd_gated:
                gate_start = perf_counter()
                needed = target ^ bsyndrome
                small_solver, small_indicators = make_syndrome_oracle(
                    split, small, b, global_rows, nvars)
                gate_stats = add_bdd_acceptance_gate(
                    small_solver, bdd, root, small_indicators, needed)
                sat_small, small_model = small_solver.solve()
                if not sat_small:
                    records.append({"boundary_bits": b, "status": "EXACT_BDD_GATED_NO_JOIN",
                                    "symbolic": stats, "gate": gate_stats})
                    continue
                small_interior = tuple(v for v in split[f"{small}_vars"]
                                       if v not in boundary)
                large_interior = tuple(v for v in split[f"{large}_vars"]
                                       if v not in boundary)
                smallsig = 0
                combined = sum(1 << (v - 1) for j, v in enumerate(boundary)
                               if b & (1 << j))
                for v in small_interior:
                    if small_model[v]:
                        smallsig ^= columns.get(v, 0)
                        combined |= 1 << (v - 1)
                wanted = needed ^ smallsig
                if not bdd.contains(root, wanted):
                    raise AssertionError("symbolic SAT gate accepted a forbidden syndrome")
                large_solver, large_indicators = make_syndrome_oracle(
                    split, large, b, global_rows, nvars)
                sat_large, large_model = large_solver.solve(
                    assumptions=assumptions_for_syndrome(large_indicators, wanted))
                if not sat_large:
                    raise AssertionError("exact BDD membership contradicted native side")
                for v in large_interior:
                    if large_model[v]:
                        combined |= 1 << (v - 1)
                assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
                full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                                   source_equations=source_equations)
                digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
                return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                        "matched_boundary_bits": b, "symbolic": stats,
                        "gate": gate_stats,
                        "source_ms": source_ms, "exact_count_ms": count_ms,
                        "compile_ms": build_ms,
                        "gate_solve_and_verify_ms": round((perf_counter() - gate_start) * 1000, 2),
                        "side_oracle_queries": 2,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                        "records": records}
            small_solver = _source_side_solver(split, small, b)
            large_solver, indicators = make_syndrome_oracle(split, large, b,
                                                             global_rows, nvars)
            small_interior = tuple(v for v in split[f"{small}_vars"] if v not in boundary)
            large_interior = tuple(v for v in split[f"{large}_vars"] if v not in boundary)
            bmask = sum((1 << (v - 1)) for j, v in enumerate(boundary) if b & (1 << j))
            attempts = 0
            while perf_counter() < deadline:
                sat, model = small_solver.solve()
                if not sat:
                    if attempts != batch[small]:
                        raise AssertionError("small side count disagrees with exact count")
                    records.append({"boundary_bits": b, "status": "EXHAUSTIVE_BATCH_UNSAT",
                                    "symbolic": stats, "compile_ms": build_ms})
                    break
                attempts += 1
                smallmask = 0
                smallsyndrome = 0
                block = []
                for v in small_interior:
                    truth = bool(model[v])
                    block.append(-v if truth else v)
                    if truth:
                        smallmask |= 1 << (v - 1)
                        smallsyndrome ^= columns.get(v, 0)
                small_solver.add_clause(block)
                wanted = target ^ bsyndrome ^ smallsyndrome
                if not bdd.contains(root, wanted):
                    continue
                # A single independent SAT oracle call certifies a BDD-positive
                # signature and reconstructs a complete source-checked model.
                sat_right, right_model = large_solver.solve(
                    assumptions=assumptions_for_syndrome(indicators, wanted))
                if not sat_right:
                    raise AssertionError("BDD membership contradicted original side")
                largemask = sum(1 << (v - 1) for v in large_interior if right_model[v])
                combined = bmask | smallmask | largemask
                assignment = {v: bool(combined & (1 << (v - 1))) for v in variables}
                full = lift_original_xor_variables(raw_clauses, nvars, assignment,
                                                   source_equations=source_equations)
                digest = sha256(bytes(int(full[v]) for v in range(1, nvars + 1))).hexdigest()
                return {"status": "SAT_VERIFIED_ORIGINAL", "model_sha256": digest,
                        "matched_boundary_bits": b, "symbolic": stats,
                        "source_ms": source_ms, "exact_count_ms": count_ms,
                        "compile_ms": build_ms, "small_models": attempts,
                        "right_oracle_queries": 1,
                        "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                        "records": records}
            else:
                raise SymbolicLimit("SYMBOLIC_TIME_BUDGET")
    except SymbolicLimit as exc:
        return {"status": "UNKNOWN_SYMBOLIC_RESOURCE_CAP", "reason": str(exc),
                "elapsed_ms": round((perf_counter() - start) * 1000, 2),
                "no_unsat_inference": True}
    return {"status": "UNKNOWN_INCOMPLETE", "records": records,
            "elapsed_ms": round((perf_counter() - start) * 1000, 2),
            "no_unsat_inference": True}


def _worker(clauses, nvars, budget_s, node_cap, state_cap,
            two_sided, bdd_gated, sparse_join, queue):
    try:
        queue.put(symbolic_syndrome_search(clauses, nvars,
                                           time_budget_s=budget_s,
                                           node_cap=node_cap, state_cap=state_cap,
                                           two_sided=two_sided, bdd_gated=bdd_gated,
                                           sparse_join=sparse_join))
    except Exception as exc:
        queue.put({"status": "ERROR", "error": repr(exc)})


def bounded_symbolic_syndromes(clauses, nvars, *, budget_s=30,
                              node_cap=500_000, state_cap=100_000,
                              two_sided=False, bdd_gated=False, sparse_join=True):
    if not (0 < budget_s <= 60):
        raise ValueError("invalid worker cap")
    ctx = get_context("fork")
    queue = ctx.Queue()
    worker = ctx.Process(target=_worker,
                         args=(clauses, nvars, budget_s, node_cap, state_cap,
                               two_sided, bdd_gated, sparse_join, queue))
    start = perf_counter()
    worker.start()
    worker.join(budget_s)
    if worker.is_alive():
        worker.terminate()
        worker.join(2)
        if worker.is_alive():
            worker.kill()
            worker.join(2)
        queue.close()
        return {"status": "UNKNOWN_TIMEOUT", "wall_ms": round((perf_counter() - start) * 1000, 2)}
    if queue.empty():
        queue.close()
        return {"status": "ERROR", "error": "symbolic worker returned no data"}
    result = queue.get()
    queue.close()
    result["wall_ms"] = round((perf_counter() - start) * 1000, 2)
    return result


def benchmark(name="par32-1-c.cnf.Z", *, budget=30, node_cap=500_000,
              state_cap=100_000, two_sided=False, bdd_gated=False,
              sparse_join=True):
    if name not in FIXED_SHA:
        raise ValueError("holdout is sealed")
    source = fetch_file(name, True)
    if source["dimacs_sha256"] != FIXED_SHA[name]:
        raise AssertionError("official source digest mismatch")
    return {"source": name, "dimacs_sha256": source["dimacs_sha256"],
            "solver": "exact frontier-DP/ROBDD; pycryptosat 5.17.0 source check",
            "holdout_untouched": True, "node_cap": node_cap,
            "two_sided": two_sided, "bdd_gated": bdd_gated,
            "sparse_join": sparse_join,
            "symbolic_bdd": bounded_symbolic_syndromes(
                source["clause_lists"], source["variables"],
                budget_s=budget, node_cap=node_cap, state_cap=state_cap,
                two_sided=two_sided, bdd_gated=bdd_gated,
                sparse_join=sparse_join)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=30)
    parser.add_argument("--node-cap", type=int, default=500_000)
    parser.add_argument("--state-cap", type=int, default=100_000)
    parser.add_argument("--one-sided", action="store_true")
    parser.add_argument("--two-sided", action="store_true")
    parser.add_argument("--bdd-gated", action="store_true")
    args = parser.parse_args()
    if sum((args.one_sided, args.two_sided, args.bdd_gated)) > 1:
        parser.error("choose only one strategy")
    print(json.dumps(benchmark(budget=args.budget, node_cap=args.node_cap,
                               state_cap=args.state_cap,
                               two_sided=args.two_sided,
                               bdd_gated=args.bdd_gated,
                               sparse_join=not (args.one_sided or args.two_sided
                                                or args.bdd_gated)),
                     indent=2))
