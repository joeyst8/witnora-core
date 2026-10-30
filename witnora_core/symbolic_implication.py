"""Axiom-relative symbolic implication triage; never a Lean proof.

Every rewrite is backed by a named established graph fact. Non-derivability
means only that this intentionally incomplete rule system did not find proof.
"""
from __future__ import annotations

from collections import deque

from .conjecture_triage import triage
from .expression_conjecture_search import expression_pool

KNOWN_BOUNDS = {
    ("alpha", "n"), ("tau", "n"), ("tau", "m"),
    ("omega", "chi"), ("omega", "n"), ("chi", "n"),
    ("nu", "n"), ("nu", "tau"), ("nu", "m"),
    ("delta", "n"), ("delta", "m"),
}
KNOWN_IDENTITIES = {
    ("+", frozenset(("alpha", "tau"))): ("n", "alpha+tau=n"),
    ("-", ("n", "tau")): ("alpha", "n-tau=alpha"),
    ("-", ("n", "alpha")): ("tau", "n-alpha=tau"),
}


def bound_path(smaller: str, larger: str) -> list[str] | None:
    if smaller == larger:
        return []
    queue = deque([(smaller, [])])
    seen = {smaller}
    while queue:
        current, path = queue.popleft()
        for a, b in sorted(KNOWN_BOUNDS):
            if a != current or b in seen:
                continue
            updated = path + [f"{a}<={b}"]
            if b == larger:
                return updated
            seen.add(b)
            queue.append((b, updated))
    return None


def normalize(expression) -> tuple[str, list[str]]:
    if expression.op == "atom":
        return expression.a, []
    op, a, b = expression.op, expression.a, expression.b
    if op == "+" and frozenset((a, b)) == frozenset(("alpha", "tau")):
        value, rule = KNOWN_IDENTITIES[("+", frozenset(("alpha", "tau")))]
        return value, [rule]
    if (op, (a, b)) in KNOWN_IDENTITIES:
        value, rule = KNOWN_IDENTITIES[(op, (a, b))]
        return value, [rule]
    if op in ("min", "max"):
        path = bound_path(a, b)
        if path is not None:
            return (a if op == "min" else b), path
        path = bound_path(b, a)
        if path is not None:
            return (b if op == "min" else a), path
    return expression.label, []


def derive_equality(title: str) -> dict:
    index = {expr.label: expr for expr in expression_pool()}
    left, right = title.split(" = ", 1)
    if left not in index or right not in index:
        raise ValueError("non-grammar expression")
    normalized_left, left_rules = normalize(index[left])
    normalized_right, right_rules = normalize(index[right])
    derivable = normalized_left == normalized_right
    return {
        "conjecture": title,
        "left_normal_form": normalized_left,
        "right_normal_form": normalized_right,
        "axiom_references": sorted(set(left_rules + right_rules)),
        "classification": ("DERIVABLE_RELATIVE_TO_LISTED_AXIOMS"
                           if derivable else "UNRESOLVED_BY_THIS_RULE_SET"),
        "lean_verified": False,
        "novelty_verified": False,
        "theorem_proven": False,
    }


def triage_with_implications() -> dict:
    previous = triage()
    derived = []
    unresolved = []
    for title in previous["unclassified_survivors"]:
        result = derive_equality(title)
        (derived if result["classification"].startswith("DERIVABLE")
         else unresolved).append(result)
    return {
        "original_unclassified": len(previous["unclassified_survivors"]),
        "derived_relative_to_axioms": derived,
        "unresolved": unresolved,
        "known_axioms": sorted(f"{a}<={b}" for a, b in KNOWN_BOUNDS)
                        + ["alpha+tau=n", "n-tau=alpha", "n-alpha=tau"],
        "axioms_formally_verified_in_this_experiment": False,
        "lean_review_queue": [{
            "statement": row["conjecture"],
            "status": "PENDING_FORMALIZATION_AND_PRIOR_ART_REVIEW",
            "lean_verified": False, "novelty_verified": False,
        } for row in unresolved[:10]],
        "lean_verified": False, "novelty_verified": False,
        "theorem_proven": False, "promoted": False,
    }
