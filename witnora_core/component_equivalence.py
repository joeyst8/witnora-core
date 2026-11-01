"""Bounded exact CNF equivalence under variable permutation and polarity flips.

Only declares equivalence after every transformed clause matches exactly.
Never treats an invariant fingerprint as proof of equivalence.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import permutations, product


def _canonical_rows(rows):
    return tuple(sorted(set(tuple(sorted(row)) for row in rows)))


def _features(rows):
    vars_ = sorted({abs(lit) for row in rows for lit in row})
    positives = Counter(lit for row in rows for lit in row if lit > 0)
    negatives = Counter(-lit for row in rows for lit in row if lit < 0)
    features = {v: tuple(sorted((positives[v], negatives[v])))
                for v in vars_}
    shape = (tuple(sorted(len(row) for row in rows)),
             tuple(sorted(features.values())))
    return vars_, features, shape


def exact_signed_isomorphism(left, right, max_vars=6):
    """Return a witnessed variable/sign mapping or None.

    Inputs are CNF clause sequences. Equal shapes are only a filter; the
    returned witness must transform the complete signed clause set.
    """
    lv, lf, ls = _features(left)
    rv, rf, rs = _features(right)
    if ls != rs or len(lv) > max_vars:
        return None
    targets = defaultdict(list)
    for v in rv:
        targets[rf[v]].append(v)
    buckets = []
    for v in lv:
        buckets.append(tuple(targets[lf[v]]))
    right_canon = _canonical_rows(right)
    for assignment in product(*buckets):
        if len(set(assignment)) != len(lv):
            continue
        for flips in product((False, True), repeat=len(lv)):
            mapping = {v: (w, flip)
                       for v, w, flip in zip(lv, assignment, flips)}
            transformed = _canonical_rows([
                [(mapping[abs(lit)][0] if
                  ((lit > 0) != mapping[abs(lit)][1]) else
                  -mapping[abs(lit)][0]) for lit in row]
                for row in left
            ])
            if transformed == right_canon:
                return mapping
    return None


def cheap_shape(rows):
    return _features(rows)[2]


def refined_shape(rows):
    """Stronger necessary invariant under variable renaming/sign inversion.

    Along with the cheap shape, collect each variable's clause-width profile
    and multiset of co-occurrence counts. These are unchanged by polarity
    flips and label permutations. Equality is still not a proof of isomorphism.
    """
    variables = sorted({abs(lit) for row in rows for lit in row})
    profile = Counter()
    neighbors = {v: Counter() for v in variables}
    for row in rows:
        members = sorted({abs(lit) for lit in row})
        for v in members:
            profile[(v, len(row))] += 1
            for u in members:
                if u != v:
                    neighbors[v][u] += 1
    fingerprints = []
    for v in variables:
        width_profile = tuple(sorted(
            (size, n) for (w, size), n in profile.items() if w == v))
        fingerprints.append((width_profile,
                             tuple(sorted(neighbors[v].values()))))
    return cheap_shape(rows), tuple(sorted(fingerprints))
