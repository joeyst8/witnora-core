"""Experimental root-offset compression of exact source binary XOR patterns.

No general-CNF equisatisfiability or novelty is claimed. The returned
certificate is UNVERIFIED until Lean independently checks the offsets.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .cnf import CNFFormula
from .spoke_discovery import extract_binary_xor_equations


def compress_binary_xor_components(formula: CNFFormula) -> dict[str, Any]:
    equations = extract_binary_xor_equations(formula)
    vertices = sorted({v for u, w, _ in equations for v in (u, w)})
    adj: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, rhs in equations:
        adj[u].append((v, rhs))
        adj[v].append((u, rhs))

    roots: dict[int, int] = {}
    offsets: dict[int, int] = {}
    paths: dict[int, list[list[int]]] = {}
    for start in vertices:
        if start in roots:
            continue
        roots[start] = start
        offsets[start] = 0
        paths[start] = []
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v, rhs in sorted(adj[u]):
                proposal = offsets[u] ^ rhs
                if v in roots:
                    if roots[v] != start or offsets[v] != proposal:
                        return {
                            "operator": "PARITY_COMPONENT_COMPRESSION",
                            "status": "INCONSISTENT_XOR_EQUATIONS",
                            "formal_status": "NOT_LEAN_VERIFIED",
                            "conflict_edge": [u, v, rhs],
                        }
                else:
                    roots[v] = start
                    offsets[v] = proposal
                    paths[v] = paths[u] + [[v, rhs]]
                    queue.append(v)
    if not all(roots[u] == roots[v] and offsets[u] ^ offsets[v] == rhs
               for u, v, rhs in equations):
        raise AssertionError("invalid root-offset component representation")
    return {
        "operator": "PARITY_COMPONENT_COMPRESSION",
        "status": "UNVERIFIED_STRUCTURAL_CANDIDATE",
        "formal_status": "NOT_LEAN_VERIFIED",
        "equations": [list(e) for e in equations],
        "roots": [[v, roots[v]] for v in vertices],
        "offsets": [[v, offsets[v]] for v in vertices],
        "source_paths": [[v, paths[v]] for v in vertices],
        "input_vertices": len(vertices),
        "component_count": len(set(roots.values())),
        "root_variables_saved": len(vertices) - len(set(roots.values())),
        "claim_boundary": "only extracted binary XOR constraints; arbitrary CNF residual is untouched",
    }


def reconstruct_values(compression: dict[str, Any], root_values: dict[int, int]) -> dict[int, int]:
    if compression.get("status") != "UNVERIFIED_STRUCTURAL_CANDIDATE":
        raise ValueError("no consistent compression certificate")
    roots = dict(compression["roots"])
    offsets = dict(compression["offsets"])
    if not all(type(root_values.get(root)) is int and root_values[root] in (0, 1)
               for root in set(roots.values())):
        raise ValueError("missing or invalid root assignment")
    return {v: root_values[root] ^ offsets[v] for v, root in roots.items()}


def substitute_residual_formula(formula: CNFFormula,
                                compression: dict[str, Any]) -> CNFFormula:
    """Syntactically substitute parity-root variables into every CNF clause.

    This is an experimental Python output. A tautological rewritten clause
    may disappear under CNFFormula canonicalization; the separately proved
    Lean literal rewrite covers the pre-normalized semantic transformation.
    The caller must not promote this as Lean-verified without checking the
    source path and residual correspondence for the concrete instance.
    """
    if compression.get("status") != "UNVERIFIED_STRUCTURAL_CANDIDATE":
        raise ValueError("no consistent parity component certificate")
    roots = dict(compression["roots"])
    offsets = dict(compression["offsets"])
    rewritten = []
    for clause in formula.to_clause_lists():
        new_clause = []
        for lit in clause:
            var = abs(lit)
            root = roots.get(var, var)
            flipped = offsets.get(var, 0)
            new_clause.append(root if (lit > 0) != bool(flipped) else -root)
        rewritten.append(new_clause)
    return CNFFormula.from_raw_clauses(rewritten)
