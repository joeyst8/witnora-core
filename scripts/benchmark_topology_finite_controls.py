"""W-CROSSDOMAIN-005: exhaustive small-source topology controls (Python oracle).

Research orchestration only. Rust owns the production structural diagnostic.
No solver-speed, generalized #SAT, or novelty claim is derived from this run.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations, permutations
import json

from tests.test_structural_profile_rust import graph_profile


EXAMPLES = (
    ((1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (4, 6), (5, 6)),
    ((1, 2), (1, 3), (1, 4), (2, 5), (2, 6), (3, 5), (4, 6)),
)


def monotone_count(edges: tuple[tuple[int, int], ...], n: int = 6) -> int:
    return sum(
        all(((assignment >> (u - 1)) & 1) or ((assignment >> (v - 1)) & 1)
            for u, v in edges)
        for assignment in range(1 << n)
    )


def signed_count(edges: tuple[tuple[int, int], ...], signs: int, n: int = 6) -> int:
    """Each of the two literal polarities per edge is independently selected."""
    return sum(
        all(
            (((assignment >> (u - 1)) & 1) == ((signs >> (2 * j)) & 1))
            or (((assignment >> (v - 1)) & 1) == ((signs >> (2 * j + 1)) & 1))
            for j, (u, v) in enumerate(edges)
        ) for assignment in range(1 << n)
    )


def audit() -> dict:
    edges = list(combinations(range(1, 7), 2))
    groups: dict[tuple[int | None, int], list[int]] = defaultdict(list)
    isomorphism_classes: dict[tuple[int | None, int], set[tuple]] = defaultdict(set)
    relabelings = tuple(permutations(range(1, 7)))
    for selected in combinations(edges, 7):
        profile = graph_profile(6, list(selected))
        if profile["initial_components"] != 1:
            continue
        key = (profile["separator_order_le2"], profile["primal_flag_beta1_mod2"])
        groups[key].append(monotone_count(selected))
        if key[0] == 2:
            canonical = min(
                tuple(sorted((min(perm[u - 1], perm[v - 1]),
                              max(perm[u - 1], perm[v - 1]))
                             for u, v in selected))
                for perm in relabelings
            )
            isomorphism_classes[key].add(canonical)

    group_rows = []
    for (separator, beta), counts in sorted(
        groups.items(), key=lambda entry: (99 if entry[0][0] is None else entry[0][0], entry[0][1])
    ):
        group_rows.append({
            "separator_order_le2": separator, "flag_beta1_mod2": beta,
            "labeled_graphs": len(counts), "min_models": min(counts),
            "max_models": max(counts), "sum_models": sum(counts),
            "unlabeled_classes_if_separator_two":
                len(isomorphism_classes[(separator, beta)]) if separator == 2 else None,
        })

    sign_rows = []
    for example in EXAMPLES:
        profile = graph_profile(6, list(example))
        histogram = Counter(signed_count(example, signs)
                            for signs in range(1 << (2 * len(example))))
        sign_rows.append({
            "flag_beta1_mod2": profile["primal_flag_beta1_mod2"],
            "separator_order_le2": profile["separator_order_le2"],
            "signings": sum(histogram.values()),
            "distinct_model_counts": sorted(histogram),
            "minimum_models": min(histogram), "maximum_models": max(histogram),
        })
    return {
        "experiment": "W-CROSSDOMAIN-005",
        "source_family": "six-variable seven-clause positive 2-CNF; signed variants for two examples",
        "all_labeled_seven_edge_graphs": 6435,
        "connected_graphs": sum(row["labeled_graphs"] for row in group_rows),
        "groups": group_rows,
        "signed_negative_controls": sign_rows,
        "scope": "finite exhaustive data; no statistical independence or solver-time claim",
    }


def main() -> None:
    print(json.dumps(audit(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
