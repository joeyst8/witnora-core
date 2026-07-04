"""Independent raw-clause checker for Witnora .wcert bundles.

This module intentionally avoids importing Witnora solver/collapse modules. It
uses only raw tuples, set operations, JSON parsing, and hashing.
"""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

CHECKER = "independent_raw_checker_v0.4"
TRUSTED_IMPORTS = ["argparse", "collections", "hashlib", "json", "pathlib", "typing"]
FORBIDDEN_STATUSES = {"HARD", "UNKNOWN", "PROBABLY_UNSAT", "PROBABLY_HARD"}

ClauseRaw = tuple[int, ...]
FormulaRaw = tuple[ClauseRaw, ...]


def _fail(error: str, failed_check: str) -> dict[str, Any]:
    return {
        "verified": False,
        "error": error,
        "failed_check": failed_check,
        "checker": CHECKER,
        "trusted_imports": TRUSTED_IMPORTS,
    }


def stable_json_raw(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_text_raw(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def canonicalize_clause_raw(literals: Iterable[int]) -> ClauseRaw | None:
    seen: set[int] = set()
    for lit in literals:
        if not isinstance(lit, int):
            raise ValueError(f"literal is not an integer: {lit!r}")
        if lit == 0:
            raise ValueError("literal 0 is reserved as a DIMACS terminator")
        if -lit in seen:
            return None
        seen.add(lit)
    return tuple(sorted(seen))


def canonicalize_formula_raw(formula: Iterable[Iterable[int]]) -> FormulaRaw:
    clauses: dict[ClauseRaw, ClauseRaw] = {}
    for raw_clause in formula:
        clause = canonicalize_clause_raw(raw_clause)
        if clause is None:
            continue
        clauses[clause] = clause
    return tuple(sorted(clauses))


def parse_dimacs_raw(text: str) -> FormulaRaw:
    if not text.strip():
        raise ValueError("empty DIMACS")
    header_seen = False
    declared_vars: int | None = None
    declared_clauses: int | None = None
    current: list[int] = []
    clauses: list[list[int]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        tokens = line.split()
        if tokens[0] == "p":
            if header_seen:
                raise ValueError(f"duplicate header at line {line_no}")
            if len(tokens) != 4 or tokens[1] != "cnf":
                raise ValueError(f"invalid header at line {line_no}")
            declared_vars = int(tokens[2])
            declared_clauses = int(tokens[3])
            header_seen = True
            continue
        if not header_seen:
            raise ValueError(f"missing header before line {line_no}")
        for token in tokens:
            lit = int(token)
            if lit == 0:
                clauses.append(current)
                current = []
                continue
            if declared_vars is not None and abs(lit) > declared_vars:
                raise ValueError(f"variable {abs(lit)} exceeds header")
            current.append(lit)
    if not header_seen:
        raise ValueError("missing header")
    if current:
        raise ValueError("missing terminating 0")
    if declared_clauses is not None and len(clauses) != declared_clauses:
        raise ValueError("clause count mismatch")
    return canonicalize_formula_raw(clauses)


def variables_raw(formula: FormulaRaw) -> tuple[int, ...]:
    return tuple(sorted({abs(lit) for clause in formula for lit in clause}))


def canonical_dimacs_raw(formula: FormulaRaw) -> str:
    max_var = max(variables_raw(formula), default=0)
    lines = [f"p cnf {max_var} {len(formula)}"]
    for clause in formula:
        lines.append((" ".join(str(lit) for lit in clause) + " 0") if clause else "0")
    return "\n".join(lines) + "\n"


def hash_formula_raw(formula: FormulaRaw) -> str:
    return sha256_text_raw(canonical_dimacs_raw(formula))


def clause_satisfied_raw(clause: ClauseRaw, assignment: dict[int, bool]) -> bool:
    for lit in clause:
        value = assignment.get(abs(lit))
        if value is not None and (value if lit > 0 else not value):
            return True
    return False


def formula_satisfied_raw(formula: FormulaRaw, assignment: dict[int, bool]) -> bool:
    return all(clause_satisfied_raw(clause, assignment) for clause in formula)


def _literal_true_default_false(lit: int, assignment: dict[int, bool]) -> bool:
    value = assignment.get(abs(lit), False)
    return value if lit > 0 else not value


def _clause_satisfied_default_false(clause: ClauseRaw, assignment: dict[int, bool]) -> bool:
    return any(_literal_true_default_false(lit, assignment) for lit in clause)


def is_tautology_raw(clause: Iterable[int]) -> bool:
    seen: set[int] = set()
    for lit in clause:
        if -lit in seen:
            return True
        seen.add(lit)
    return False


def resolve_raw(clause_a: ClauseRaw, clause_b: ClauseRaw, pivot_lit: int) -> ClauseRaw | None:
    return canonicalize_clause_raw(
        [lit for lit in clause_a if lit != pivot_lit]
        + [lit for lit in clause_b if lit != -pivot_lit]
    )


def _raw_resolvent_for_log(clause_a: ClauseRaw, clause_b: ClauseRaw, pivot_lit: int) -> list[int]:
    return sorted(
        [lit for lit in clause_a if lit != pivot_lit]
        + [lit for lit in clause_b if lit != -pivot_lit]
    )


def _literal_sort_key(lit: int) -> tuple[int, int]:
    return abs(lit), 0 if lit > 0 else 1


def _clauses_equal_raw(left: Iterable[Iterable[int]], right: Iterable[Iterable[int]]) -> bool:
    return sorted([list(canonicalize_clause_raw(item) or ()) for item in left]) == sorted(
        [list(canonicalize_clause_raw(item) or ()) for item in right]
    )


def _formula_without_clause(current_formula: FormulaRaw, removed: ClauseRaw) -> FormulaRaw:
    return tuple(clause for clause in current_formula if clause != removed)


def check_up_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any]) -> FormulaRaw:
    units = [clause for clause in current_formula if len(clause) == 1]
    if not units:
        raise ValueError("UP step has no unit clause")
    unit = sorted(units)[0]
    lit = unit[0]
    kept: list[ClauseRaw] = []
    removed: list[ClauseRaw] = []
    added: list[ClauseRaw] = []
    shortened: list[dict[str, list[int]]] = []
    for clause in current_formula:
        if lit in clause:
            removed.append(clause)
            continue
        if -lit in clause:
            removed.append(clause)
            new_clause = canonicalize_clause_raw(x for x in clause if x != -lit)
            if new_clause is None:
                raise ValueError("UP generated tautology unexpectedly")
            added.append(new_clause)
            shortened.append({"from": list(clause), "to": list(new_clause)})
            continue
        kept.append(clause)
    output = canonicalize_formula_raw([*kept, *added])
    expected_removed = [clause for clause in removed if lit in clause] + [
        tuple(item["from"]) for item in shortened
    ]
    expected_added = [tuple(item["to"]) for item in shortened]
    if log_entry.get("assigned_literals") != [lit]:
        raise ValueError("UP assigned literal mismatch")
    if not _clauses_equal_raw(log_entry.get("removed_clauses", []), expected_removed):
        raise ValueError("UP removed clauses mismatch")
    if not _clauses_equal_raw(log_entry.get("added_clauses", []), expected_added):
        raise ValueError("UP added clauses mismatch")
    if log_entry.get("output_formula_hash") != hash_formula_raw(output):
        raise ValueError("UP output hash mismatch")
    return output


def check_ple_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any]) -> FormulaRaw:
    signs: dict[int, set[int]] = {}
    for clause in current_formula:
        for lit in clause:
            signs.setdefault(abs(lit), set()).add(1 if lit > 0 else -1)
    pure_literals: list[int] = []
    for var, var_signs in signs.items():
        if var_signs == {1}:
            pure_literals.append(var)
        elif var_signs == {-1}:
            pure_literals.append(-var)
    if not pure_literals:
        raise ValueError("PLE step has no pure literal")
    lit = sorted(pure_literals, key=_literal_sort_key)[0]
    removed = [clause for clause in current_formula if lit in clause]
    output = canonicalize_formula_raw(clause for clause in current_formula if lit not in clause)
    if log_entry.get("assigned_literals") != [lit]:
        raise ValueError("PLE assigned literal mismatch")
    if not _clauses_equal_raw(log_entry.get("removed_clauses", []), removed):
        raise ValueError("PLE removed clauses mismatch")
    if log_entry.get("output_formula_hash") != hash_formula_raw(output):
        raise ValueError("PLE output hash mismatch")
    return output


def check_subsumption_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any]) -> FormulaRaw:
    found: tuple[ClauseRaw, ClauseRaw] | None = None
    for subsumer in current_formula:
        subsumer_set = set(subsumer)
        for removed in current_formula:
            if subsumer == removed or len(subsumer) >= len(removed):
                continue
            if subsumer_set.issubset(removed):
                found = subsumer, removed
                break
        if found is not None:
            break
    if found is None:
        raise ValueError("SUB step has no valid subsumption")
    subsumer, removed = found
    output = _formula_without_clause(current_formula, removed)
    if log_entry.get("details", {}).get("subsuming_clause") != list(subsumer):
        raise ValueError("SUB subsuming clause mismatch")
    if log_entry.get("removed_clauses") != [list(removed)]:
        raise ValueError("SUB removed clause mismatch")
    if log_entry.get("output_formula_hash") != hash_formula_raw(output):
        raise ValueError("SUB output hash mismatch")
    return output


def check_bce_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any]) -> FormulaRaw:
    removed_items = log_entry.get("removed_clauses", [])
    if len(removed_items) != 1:
        raise ValueError("BCE must remove exactly one clause")
    removed = canonicalize_clause_raw(removed_items[0])
    if removed is None or removed not in current_formula:
        raise ValueError("BCE removed clause not present")
    blocked_literal = int(log_entry.get("details", {}).get("blocked_literal", 0))
    if blocked_literal not in removed:
        raise ValueError("BCE blocked literal not in removed clause")
    opposite = [
        clause
        for clause in current_formula
        if clause != removed and -blocked_literal in clause
    ]
    expected_checked: list[dict[str, Any]] = []
    for other in opposite:
        raw_resolvent = _raw_resolvent_for_log(removed, other, blocked_literal)
        tautological = is_tautology_raw(raw_resolvent)
        expected_checked.append(
            {
                "against_clause": list(other),
                "resolvent": raw_resolvent,
                "tautological": tautological,
            }
        )
        if not tautological:
            raise ValueError("BCE non-tautological resolvent exists")
    details = log_entry.get("details", {})
    if details.get("opposite_clauses", []) != [list(clause) for clause in opposite]:
        raise ValueError("BCE opposite clause log mismatch")
    if details.get("checked_resolvents", []) != expected_checked:
        raise ValueError("BCE checked resolvent log mismatch")
    output = _formula_without_clause(current_formula, removed)
    if log_entry.get("output_formula_hash") != hash_formula_raw(output):
        raise ValueError("BCE output hash mismatch")
    return output


def check_ve_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any], c_parameter: int) -> FormulaRaw:
    data = log_entry.get("reconstruction_data", {})
    var = int(data.get("eliminated_variable", log_entry.get("details", {}).get("eliminated_variable", 0)))
    if var <= 0:
        raise ValueError("VE eliminated variable missing")
    pos = [clause for clause in current_formula if var in clause]
    neg = [clause for clause in current_formula if -var in clause]
    removed = sorted(pos + neg)
    kept = [clause for clause in current_formula if var not in clause and -var not in clause]
    resolvents: dict[ClauseRaw, ClauseRaw] = {}
    for pos_clause in sorted(pos):
        for neg_clause in sorted(neg):
            raw = _raw_resolvent_for_log(pos_clause, neg_clause, var)
            if is_tautology_raw(raw):
                continue
            resolvent = resolve_raw(pos_clause, neg_clause, var)
            if resolvent is None:
                continue
            if len(resolvent) > c_parameter:
                raise ValueError("VE width cap violation")
            resolvents[resolvent] = resolvent
    expected_added = sorted(resolvents)
    output = canonicalize_formula_raw([*kept, *expected_added])
    if not _clauses_equal_raw(log_entry.get("removed_clauses", []), removed):
        raise ValueError("VE removed clauses mismatch")
    if not _clauses_equal_raw(log_entry.get("added_clauses", []), expected_added):
        raise ValueError("VE added resolvents mismatch")
    if log_entry.get("output_formula_hash") != hash_formula_raw(output):
        raise ValueError("VE output hash mismatch")
    if any(len(clause) > c_parameter for clause in expected_added):
        raise ValueError("VE width cap violation")
    return output


def _component_details_raw(formula: FormulaRaw, parent_component_id: str | None = None) -> dict[str, Any]:
    if not formula:
        components: list[FormulaRaw] = []
    else:
        var_to_clauses: dict[int, list[int]] = defaultdict(list)
        for idx, clause in enumerate(formula):
            for var in sorted({abs(lit) for lit in clause}):
                var_to_clauses[var].append(idx)
        seen_clauses: set[int] = set()
        component_clause_ids: list[list[int]] = []
        for start in range(len(formula)):
            if start in seen_clauses:
                continue
            queue: deque[tuple[str, int]] = deque([("c", start)])
            ids: set[int] = set()
            seen_vars: set[int] = set()
            while queue:
                kind, node = queue.popleft()
                if kind == "c":
                    if node in seen_clauses:
                        continue
                    seen_clauses.add(node)
                    ids.add(node)
                    for var in sorted({abs(lit) for lit in formula[node]}):
                        if var not in seen_vars:
                            queue.append(("v", var))
                else:
                    if node in seen_vars:
                        continue
                    seen_vars.add(node)
                    for clause_idx in var_to_clauses[node]:
                        if clause_idx not in seen_clauses:
                            queue.append(("c", clause_idx))
            component_clause_ids.append(sorted(ids))
        components = [
            canonicalize_formula_raw(formula[idx] for idx in ids)
            for ids in component_clause_ids
        ]
    clause_to_index = {clause: idx for idx, clause in enumerate(formula)}
    details_components: list[dict[str, Any]] = []
    for idx, component in enumerate(components):
        component_id = str(idx) if parent_component_id is None else f"{parent_component_id}.{idx}"
        details_components.append(
            {
                "component_id": component_id,
                "formula_hash": hash_formula_raw(component),
                "variables": list(variables_raw(component)),
                "clauses": [list(clause) for clause in component],
                "clause_indices": [clause_to_index[clause] for clause in component],
            }
        )
    return {
        "component_count": len(components),
        "incidence_edges": [
            [var, idx]
            for idx, clause in enumerate(formula)
            for var in sorted({abs(lit) for lit in clause})
        ],
        "components": details_components,
    }


def check_component_decomposition_raw(current_formula: FormulaRaw, log_entry: dict[str, Any]) -> dict[str, FormulaRaw]:
    parent_component_id = log_entry.get("details", {}).get("parent_component_id")
    parent_component_id = None if parent_component_id is None else str(parent_component_id)
    expected = _component_details_raw(current_formula, parent_component_id)
    details = log_entry.get("details", {})
    if log_entry.get("output_formula_hash") != hash_formula_raw(current_formula):
        raise ValueError("CD output hash mismatch")
    if details.get("component_count") != expected["component_count"]:
        raise ValueError("CD component count mismatch")
    if details.get("incidence_edges") != expected["incidence_edges"]:
        raise ValueError("CD incidence edges mismatch")
    logged_components = details.get("components", [])
    if len(logged_components) != len(expected["components"]):
        raise ValueError("CD logged component length mismatch")
    child_states: dict[str, FormulaRaw] = {}
    all_clause_indices: list[int] = []
    owner_by_var: dict[int, str] = {}
    for logged, exp in zip(logged_components, expected["components"]):
        if str(logged.get("component_id")) != exp["component_id"]:
            raise ValueError("CD component id mismatch")
        for key in ["formula_hash", "variables", "clauses", "clause_indices"]:
            if logged.get(key) != exp[key]:
                raise ValueError(f"CD component {key} mismatch")
        component_id = str(logged.get("component_id"))
        variables = {int(v) for v in logged.get("variables", [])}
        all_clause_indices.extend(int(i) for i in logged.get("clause_indices", []))
        for var in variables:
            previous = owner_by_var.get(var)
            if previous is not None and previous != component_id:
                raise ValueError("CD variable partition conflict")
            owner_by_var[var] = component_id
        for raw_clause in logged.get("clauses", []):
            clause = canonicalize_clause_raw(raw_clause)
            if clause is None or not {abs(lit) for lit in clause}.issubset(variables):
                raise ValueError("CD clause crosses component")
        child_states[component_id] = canonicalize_formula_raw(logged.get("clauses", []))
    if sorted(all_clause_indices) != list(range(len(current_formula))):
        raise ValueError("CD clauses are not an exact partition")
    return child_states


def _implication_graph_raw(formula: FormulaRaw) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = {lit: set() for var in variables_raw(formula) for lit in (var, -var)}
    for clause in formula:
        if len(clause) == 0:
            continue
        if len(clause) == 1:
            a = clause[0]
            graph.setdefault(-a, set()).add(a)
            graph.setdefault(a, set())
        elif len(clause) == 2:
            a, b = clause
            graph.setdefault(-a, set()).add(b)
            graph.setdefault(b, set())
            graph.setdefault(-b, set()).add(a)
            graph.setdefault(a, set())
        else:
            raise ValueError("2SAT formula contains wide clause")
    return {node: set(sorted(neighs)) for node, neighs in sorted(graph.items())}


def _scc_raw(graph: dict[int, set[int]]) -> dict[int, int]:
    reverse: dict[int, set[int]] = {node: set() for node in graph}
    for src, dsts in graph.items():
        for dst in dsts:
            reverse.setdefault(dst, set()).add(src)
    seen: set[int] = set()
    order: list[int] = []

    def dfs1(node: int) -> None:
        seen.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in seen:
                dfs1(nxt)
        order.append(node)

    def dfs2(node: int, comp_id: int) -> None:
        comp[node] = comp_id
        for nxt in sorted(reverse.get(node, ())):
            if nxt not in comp:
                dfs2(nxt, comp_id)

    for node in sorted(graph):
        if node not in seen:
            dfs1(node)
    comp: dict[int, int] = {}
    comp_id = 0
    for node in reversed(order):
        if node not in comp:
            dfs2(node, comp_id)
            comp_id += 1
    return comp


def check_2sat_result_raw(component_formula: FormulaRaw, log_entry: dict[str, Any]) -> tuple[FormulaRaw, bool]:
    if any(len(clause) > 2 for clause in component_formula):
        raise ValueError("2SAT_SOLVE formula is not 2-CNF")
    if log_entry.get("output_formula_hash") != hash_formula_raw(component_formula):
        raise ValueError("2SAT_SOLVE output hash mismatch")
    status = log_entry.get("details", {}).get("status")
    if status == "SAT":
        assignment = {
            int(var): bool(value)
            for var, value in log_entry.get("details", {}).get("assignment", {}).items()
        }
        if not formula_satisfied_raw(component_formula, assignment):
            raise ValueError("2SAT_SOLVE SAT assignment does not satisfy formula")
        return component_formula, False
    if status == "UNSAT":
        if () in component_formula:
            return component_formula, True
        graph = _implication_graph_raw(component_formula)
        comp = _scc_raw(graph)
        conflict = any(comp.get(var) == comp.get(-var) for var in variables_raw(component_formula))
        if not conflict:
            raise ValueError("2SAT_SOLVE UNSAT has no independent SCC contradiction")
        return component_formula, True
    raise ValueError("2SAT_SOLVE status missing")


def check_treewidth_solve_step_raw(current_formula: FormulaRaw, log_entry: dict[str, Any], c_parameter: int) -> FormulaRaw:
    if log_entry.get("output_formula_hash") != hash_formula_raw(current_formula):
        raise ValueError("TREEWIDTH_SOLVE output hash mismatch")
    details = log_entry.get("details", {})
    if int(details.get("width_cap", c_parameter)) != c_parameter:
        raise ValueError("TREEWIDTH_SOLVE width cap mismatch")
    if int(details.get("width_observed", 0)) > c_parameter:
        raise ValueError("TREEWIDTH_SOLVE logged width exceeds cap")
    return current_formula


def _union_component_states(states: dict[str, FormulaRaw]) -> FormulaRaw:
    return canonicalize_formula_raw(
        clause
        for component_id in sorted(states)
        for clause in states[component_id]
    )


def replay_collapse_path_raw(
    original_formula: FormulaRaw,
    collapse_path: list[dict[str, Any]],
    c_parameter: int,
) -> tuple[FormulaRaw, dict[str, bool]]:
    current = original_formula
    component_states: dict[str, FormulaRaw] = {}
    checks = {
        "bce_steps": True,
        "ve_steps": True,
        "component_steps": True,
        "two_sat_steps": True,
        "treewidth_steps": True,
    }
    saw_unsat_2sat = False
    expected_step_id = 1
    for step in collapse_path:
        if int(step.get("step_id", 0)) != expected_step_id:
            raise ValueError("step id mismatch")
        expected_step_id += 1
        context_id = step.get("details", {}).get("component_id")
        parent_context_id = step.get("details", {}).get("parent_component_id") if step.get("type") == "CD" else None
        context_id = None if context_id is None else str(context_id)
        parent_context_id = None if parent_context_id is None else str(parent_context_id)
        if step.get("type") == "CD":
            context_formula = current if parent_context_id is None else component_states.get(parent_context_id)
            if context_formula is None:
                raise ValueError("CD parent component missing")
        elif context_id is not None:
            context_formula = component_states.get(context_id)
            if context_formula is None:
                raise ValueError("component context missing")
        else:
            if component_states:
                raise ValueError("component-local step missing component_id")
            context_formula = current
        if step.get("input_formula_hash") != hash_formula_raw(context_formula):
            raise ValueError(f"{step.get('type')} input hash mismatch")
        step_type = step.get("type")
        if step_type == "UP":
            next_formula = check_up_step_raw(context_formula, step)
        elif step_type == "PLE":
            next_formula = check_ple_step_raw(context_formula, step)
        elif step_type == "SUB":
            next_formula = check_subsumption_step_raw(context_formula, step)
        elif step_type == "BCE":
            next_formula = check_bce_step_raw(context_formula, step)
        elif step_type == "VE":
            next_formula = check_ve_step_raw(context_formula, step, c_parameter)
        elif step_type == "TREEWIDTH_SOLVE":
            next_formula = check_treewidth_solve_step_raw(context_formula, step, c_parameter)
        elif step_type == "2SAT_SOLVE":
            next_formula, unsat = check_2sat_result_raw(context_formula, step)
            saw_unsat_2sat = saw_unsat_2sat or unsat
        elif step_type == "CD":
            child_states = check_component_decomposition_raw(context_formula, step)
            next_formula = context_formula
            if parent_context_id is not None:
                component_states.pop(parent_context_id, None)
            component_states.update(child_states)
        else:
            raise ValueError(f"unsupported step type {step_type}")
        if step_type != "CD":
            if context_id is None:
                current = next_formula
            else:
                component_states[context_id] = next_formula
    final_formula = _union_component_states(component_states) if component_states else current
    checks["unsat_2sat_contradiction"] = saw_unsat_2sat
    checks["explicit_empty_clause"] = () in final_formula
    return final_formula, checks


def check_reconstruction_trace_raw(
    original_formula: FormulaRaw,
    collapse_path: list[dict[str, Any]],
    final_assignment: dict[int, bool],
    reconstruction_trace: dict[str, Any],
) -> dict[int, bool]:
    assignment = dict(final_assignment)
    for step in reversed(collapse_path):
        step_type = step.get("type")
        if step_type in {"2SAT_SOLVE", "TREEWIDTH_SOLVE", "SUB", "CD"}:
            continue
        if step_type in {"UP", "PLE"}:
            assigned = step.get("assigned_literals", [])
            if not assigned:
                raise ValueError(f"{step_type} missing assigned literal")
            lit = int(assigned[0])
            var = abs(lit)
            value = lit > 0
            if var in assignment and assignment[var] != value:
                raise ValueError(f"{step_type} assignment conflict")
            assignment[var] = value
            continue
        if step_type == "BCE":
            data = step.get("reconstruction_data", {})
            removed = canonicalize_clause_raw(data.get("removed_clause", []))
            if removed is None:
                raise ValueError("BCE reconstruction removed clause invalid")
            blocked_literal = int(data.get("blocked_literal", 0))
            if not _clause_satisfied_default_false(removed, assignment):
                assignment[abs(blocked_literal)] = blocked_literal > 0
            if not _clause_satisfied_default_false(removed, assignment):
                raise ValueError("BCE reconstruction failed")
            continue
        if step_type == "VE":
            data = step.get("reconstruction_data", {})
            var = int(data.get("eliminated_variable", 0))
            desired: bool | None = None
            for raw_clause in data.get("removed_clauses", []):
                clause = canonicalize_clause_raw(raw_clause)
                if clause is None or (var not in clause and -var not in clause):
                    raise ValueError("VE reconstruction clause invalid")
                rest = [lit for lit in clause if abs(lit) != var]
                if any(_literal_true_default_false(lit, assignment) for lit in rest):
                    continue
                needed = var in clause
                if desired is not None and desired != needed:
                    raise ValueError("VE reconstruction sign conflict")
                desired = needed
            assignment.setdefault(var, False if desired is None else desired)
            if desired is not None and assignment[var] != desired:
                raise ValueError("VE reconstruction assignment conflict")
            continue
    for var in variables_raw(original_formula):
        assignment.setdefault(var, False)
    logged = {
        int(var): bool(value)
        for var, value in reconstruction_trace.get("reconstructed_original_assignment", {}).items()
    }
    if assignment != logged:
        raise ValueError("reconstruction trace assignment mismatch")
    return assignment


def check_sat_assignment_against_original_raw(original_formula: FormulaRaw, assignment: dict[int, bool]) -> bool:
    return formula_satisfied_raw(original_formula, assignment)


def check_unsat_contradiction_raw(final_state: FormulaRaw, replay_checks: dict[str, bool]) -> tuple[bool, str]:
    if () in final_state or replay_checks.get("explicit_empty_clause"):
        return True, "EXPLICIT_EMPTY_CLAUSE"
    if replay_checks.get("unsat_2sat_contradiction"):
        return True, "INDEPENDENT_2SAT_SCC"
    return False, "UNSAT requires independently checkable contradiction or future LRAT/FRAT proof"


def _normalise_assignment_for_hash(assignment: dict[str, Any]) -> dict[str, bool]:
    return {
        str(int(var)): bool(value)
        for var, value in sorted(assignment.items(), key=lambda item: int(item[0]))
    }


def _normalise_component_results_for_hash(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalised = []
    for result in sorted(results, key=lambda item: str(item.get("component_id", ""))):
        normalised.append(
            {
                "component_id": str(result.get("component_id", "")),
                "status": str(result.get("status", "")),
                "final_class": str(result.get("final_class", "")),
                "formula_hash": str(result.get("formula_hash", "")),
                "assignment": _normalise_assignment_for_hash(result.get("assignment", {})),
            }
        )
    return normalised


def compute_certificate_hash_raw(result_data: dict[str, Any]) -> str:
    payload = {
        "original_formula_hash": result_data["original_formula_hash"],
        "c_parameter": int(result_data["c_parameter"]),
        "collapse_path": result_data.get("collapse_path", []),
        "final_class": result_data["final_class"],
        "final_assignment": _normalise_assignment_for_hash(result_data.get("final_assignment", {})),
        "reconstructed_original_assignment": _normalise_assignment_for_hash(
            result_data.get("reconstructed_original_assignment", {})
        ),
        "original_verification": bool(result_data.get("original_verification", False)),
        "component_results": _normalise_component_results_for_hash(result_data.get("component_results", [])),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256_text_raw(encoded)


def _load_package_raw(path: str | Path) -> tuple[dict[str, Any], dict[str, str]]:
    source = Path(path)
    if source.is_dir():
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        files = {
            name: (source / name).read_text(encoding="utf-8")
            for name in manifest.get("files", {})
        }
        return manifest, files
    data = json.loads(source.read_text(encoding="utf-8"))
    return data["manifest"], {str(name): str(content) for name, content in data["files"].items()}


def verify_wcert_raw(path: str | Path) -> dict[str, Any]:
    try:
        manifest, files = _load_package_raw(path)
    except Exception as exc:
        return _fail(str(exc), "package_load")
    checks: dict[str, bool] = {
        "file_hashes": False,
        "certificate_hash": False,
        "bce_steps": False,
        "ve_steps": False,
        "component_steps": False,
        "two_sat_steps": False,
        "sat_assignment": False,
    }
    if str(manifest.get("status", "")) in FORBIDDEN_STATUSES:
        return _fail("forbidden status present", "forbidden_status")
    for name, meta in manifest.get("files", {}).items():
        if name not in files:
            return _fail(f"missing file {name}", "file_hashes")
        if sha256_text_raw(files[name]) != meta.get("sha256"):
            return _fail(f"file hash mismatch for {name}", "file_hashes")
    checks["file_hashes"] = True
    try:
        result_data = json.loads(files["result.json"])
        collapse_data = json.loads(files["collapse_path.json"])
        component_results = json.loads(files["component_results.json"])
        reconstruction_trace = json.loads(files["reconstruction_trace.json"])
        original = parse_dimacs_raw(files["original.dimacs"])
        normalized = parse_dimacs_raw(files["normalized.dimacs"])
    except Exception as exc:
        return _fail(str(exc), "parse")
    if str(result_data.get("status", "")) in FORBIDDEN_STATUSES:
        return _fail("forbidden status present", "forbidden_status")
    if manifest.get("status") != result_data.get("status"):
        return _fail("manifest status mismatch", "manifest")
    if manifest.get("final_class") != result_data.get("final_class"):
        return _fail("manifest final_class mismatch", "manifest")
    if int(manifest.get("c_parameter", -1)) != int(result_data.get("c_parameter", -2)):
        return _fail("manifest c_parameter mismatch", "manifest")
    if hash_formula_raw(original) != manifest.get("original_formula_hash"):
        return _fail("original formula hash mismatch", "formula_hash")
    if hash_formula_raw(normalized) != manifest.get("normalized_formula_hash"):
        return _fail("normalized formula hash mismatch", "formula_hash")
    if original != normalized:
        return _fail("normalized formula differs from original normalization", "formula_hash")
    stripped_steps = [
        {key: value for key, value in step.items() if key != "external_proof_status"}
        for step in collapse_data.get("steps", [])
    ]
    if stripped_steps != result_data.get("collapse_path", []):
        return _fail("collapse_path.json differs from result.json", "collapse_path")
    if component_results != result_data.get("component_results", []):
        return _fail("component_results mismatch", "component_results")
    recomputed_hash = compute_certificate_hash_raw(result_data)
    if recomputed_hash != manifest.get("certificate_hash"):
        return _fail("certificate hash mismatch", "certificate_hash")
    if files.get("certificate_hash.txt", "").strip() != recomputed_hash:
        return _fail("certificate_hash.txt mismatch", "certificate_hash")
    checks["certificate_hash"] = True
    try:
        final_formula, replay_checks = replay_collapse_path_raw(
            original,
            result_data.get("collapse_path", []),
            int(result_data.get("c_parameter", 0)),
        )
    except Exception as exc:
        return _fail(str(exc), "collapse_replay")
    if hash_formula_raw(final_formula) != result_data.get("final_formula_hash"):
        return _fail("final formula hash mismatch", "collapse_replay")
    checks.update({
        "bce_steps": replay_checks["bce_steps"],
        "ve_steps": replay_checks["ve_steps"],
        "component_steps": replay_checks["component_steps"],
        "two_sat_steps": replay_checks["two_sat_steps"],
    })
    status = result_data.get("status")
    if status == "SAT":
        final_assignment = {
            int(var): bool(value)
            for var, value in result_data.get("final_assignment", {}).items()
        }
        try:
            reconstructed = check_reconstruction_trace_raw(
                original,
                result_data.get("collapse_path", []),
                final_assignment,
                reconstruction_trace,
            )
        except Exception as exc:
            return _fail(str(exc), "reconstruction_trace")
        if not check_sat_assignment_against_original_raw(original, reconstructed):
            return _fail("SAT assignment does not satisfy original formula", "sat_assignment")
        checks["sat_assignment"] = True
    elif status == "UNSAT":
        ok, reason = check_unsat_contradiction_raw(final_formula, replay_checks)
        if not ok:
            return _fail(reason, "unsat_external_certification")
        checks["unsat_contradiction"] = True
    elif status == "NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C":
        checks["no_collapse_report"] = True
    else:
        return _fail(f"unsupported status {status}", "status")
    return {
        "verified": True,
        "status": status,
        "certificate_hash": recomputed_hash,
        "checker": CHECKER,
        "trusted_imports": TRUSTED_IMPORTS,
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Independent raw Witnora .wcert checker")
    parser.add_argument("certificate", help=".wcert directory or .wcert.json file")
    args = parser.parse_args(argv)
    result = verify_wcert_raw(args.certificate)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("verified") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
