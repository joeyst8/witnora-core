"""Independent serializer checks, mutation tests, and structured graph probes.

Only a bounded handpicked extension is exported for kernel checking.
Randomized cases test Python serialization invariants, not universal refinement.
"""
from __future__ import annotations

import random

from .lean_ascii_certificate_export import serialize_ascii_certificate
from .lean_color_certificate_export import (
    _validate, find_matching_clique,
)
from .nonedge_matching_bound import _dsatur_greedy_coloring


def graph_case(name: str, n: int, edges: tuple[tuple[int, int], ...]):
    colors = _dsatur_greedy_coloring(n, edges)["coloring"]
    k = max(colors) + 1
    clique = find_matching_clique(n, edges, k)
    if clique is None:
        raise ValueError(f"{name} has no matching clique witness")
    _validate(n, edges, colors, clique)
    return name, n, edges, colors, clique


def multipartite_edges(parts: tuple[int, ...]):
    if not parts or any(size < 1 for size in parts):
        raise ValueError("nonempty positive-size partitions required")
    groups = [g for g, size in enumerate(parts) for _ in range(size)]
    return tuple((u, v) for u in range(len(groups))
                 for v in range(u + 1, len(groups))
                 if groups[u] != groups[v])


def generate_structured_cases():
    return (
        graph_case("starFive", 5, tuple((0, v) for v in range(1, 5))),
        graph_case("threePartSix", 6, multipartite_edges((2, 2, 2))),
        graph_case("bipartiteSix", 6, multipartite_edges((3, 3))),
        graph_case("cliqueAndIsolates", 6, ((0, 1), (0, 2), (1, 2))),
    )


def independent_reference_bytes(n, edges, colors, clique):
    """Assemble bytes field by field without using the production join formatter."""
    k = _validate(n, edges, colors, clique)
    result = bytearray()

    def integer(value):
        result.extend(str(value).encode("ascii"))

    integer(n - 1)
    result.append(124)
    integer(k - 1)
    result.append(124)
    for j, (u, v) in enumerate(edges):
        if j:
            result.append(59)
        integer(u)
        result.append(44)
        integer(v)
    result.append(124)
    for j, color in enumerate(colors):
        if j:
            result.append(44)
        integer(color)
    result.append(124)
    for j, vertex in enumerate(clique):
        if j:
            result.append(44)
        integer(vertex)
    return bytes(result)


def mutate_bytes(data: bytes):
    """Deterministic structural and range-invalid variants."""
    variants = (
        b"x" + data[1:],
        b"0" + data,
        data + b"|",
        data.replace(b"|", b"||", 1),
        data.replace(b",", b";", 1),
        data.replace(b"|", b"|-", 1),
        data.replace(b"|", b"|999999", 1),
    )
    return tuple(dict.fromkeys(variants))


def exercise_seeded_cases(seed=20261031, count=200):
    rng = random.Random(seed)
    outcomes = []
    for i in range(count):
        n = rng.randrange(2, 9)
        number_of_groups = rng.randrange(1, min(n, 5) + 1)
        assignments = list(range(number_of_groups))
        assignments += [rng.randrange(number_of_groups) for _ in range(n - number_of_groups)]
        rng.shuffle(assignments)
        edges = tuple((u, v) for u in range(n) for v in range(u + 1, n)
                      if assignments[u] != assignments[v])
        case = graph_case(f"random{i}", n, edges)
        _, _, _, colors, clique = case
        data = serialize_ascii_certificate(n, edges, colors, clique)
        reference = independent_reference_bytes(n, edges, colors, clique)
        if data != reference:
            raise AssertionError(f"serializer mismatch for case {i}")
        if not all(32 <= byte <= 126 for byte in data):
            raise AssertionError("non-printable byte")
        outcomes.append((case, data, mutate_bytes(data)))
    return tuple(outcomes)
