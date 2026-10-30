"""Experimental contradiction discovery on arbitrary binary-XOR cycles.

Discovery is not a proof. A returned walk is a candidate until the independent
Lean source-bound gate checks every complete XOR pattern and its odd closed
parity. This is standard GF(2) graph consistency, not a novelty claim.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .cnf import CNFFormula
from .spoke_discovery import extract_binary_xor_equations


def _existing_path(
    adjacency: dict[int, list[tuple[int, int]]],
    start: int,
    target: int,
) -> list[tuple[int, int]] | None:
    queue = deque([start])
    parent: dict[int, tuple[int, int] | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == target:
            break
        for neighbor, rhs in sorted(adjacency[current]):
            if neighbor not in parent:
                parent[neighbor] = (current, rhs)
                queue.append(neighbor)
    if target not in parent:
        return None
    reversed_steps: list[tuple[int, int]] = []
    node = target
    while node != start:
        link = parent[node]
        assert link is not None
        prev, rhs = link
        reversed_steps.append((node, rhs))
        node = prev
    return list(reversed(reversed_steps))


def discover_odd_xor_cycle(formula: CNFFormula) -> dict[str, Any] | None:
    """Return an odd-parity closed-walk witness or None.

    Every proposed edge is an exact two-clause CNF XOR pattern. All
    discovery outcomes are UNVERIFIED until a Lean source proof succeeds.
    """
    adjacency: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for u, v, rhs in extract_binary_xor_equations(formula):
        path = _existing_path(adjacency, u, v)
        if path is not None:
            syndrome = 0
            for _, bit in path:
                syndrome ^= bit
            if syndrome != rhs:
                steps = path + [(u, rhs)]
                return {
                    "operator": "ODD_XOR_CYCLE",
                    "status": "UNVERIFIED_STRUCTURAL_CANDIDATE",
                    "formal_status": "NOT_LEAN_VERIFIED",
                    "start": u,
                    "steps": [
                        {"next": vertex, "rhs": bit}
                        for vertex, bit in steps
                    ],
                    "cycle_length": len(steps),
                    "reason": "closed walk requires contradictory XOR parity",
                }
        adjacency[u].append((v, rhs))
        adjacency[v].append((u, rhs))
    return None
