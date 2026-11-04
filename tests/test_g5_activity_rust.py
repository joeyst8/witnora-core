"""R-054 exact Rust/Python G5 activity, cancellation and cross-merge parity."""
from __future__ import annotations

from itertools import combinations
import os
import random
import unittest

from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations, activity_from_g5_operations_rust,
    ranked_pair_candidates, ranked_pair_candidates_rust,
    pairwise_cross_merge_activity, pairwise_cross_merge_activity_rust,
)


def scored_oracle(operations, variables):
    """Independent finite score accumulation without the production Counter."""
    universe = sorted(set(variables))
    touches = {v: 0 for v in universe}
    cancelled = {v: 0 for v in universe}
    scores = {pair: 0 for pair in combinations(universe, 2)}
    xors = events = 0
    for operation in operations:
        if operation["operation"] == "SWAP_ROWS":
            continue
        xors += 1
        before = set(operation["before"]["coefficients"])
        source = set(operation["source"]["coefficients"])
        for v in universe:
            touches[v] += int(v in before or v in source)
            cancelled[v] += int(v in before and v in source)
        for u, v in scores:
            # Score exclusive variables on opposite source sides.
            if ((u in before-source and v in source-before)
                    or (v in before-source and u in source-before)):
                scores[(u, v)] += 1
                events += 1
    return touches, cancelled, scores, xors, events


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust migration CI")
class TestNativeG5Activity(unittest.TestCase):
    def test_1000_random_operation_streams_and_independent_scores(self):
        rng = random.Random(54112026)
        count = 0
        for n in range(20):
            for case in range(50):
                universe = sorted(rng.sample(range(1, 280), n))
                operations = []
                for _ in range(rng.randrange(0, 17)):
                    if rng.random() < 0.22:
                        operations.append({"operation": "SWAP_ROWS"})
                        continue
                    before = rng.sample(universe, rng.randrange(n+1))
                    source = rng.sample(universe, rng.randrange(n+1))
                    operations.append({
                        "operation": "ADD_ROW_XOR",
                        "before": {"coefficients": before},
                        "source": {"coefficients": source},
                    })
                with self.subTest(n=n, case=case):
                    original = activity_from_g5_operations(operations, universe)
                    native = activity_from_g5_operations_rust(operations, universe)
                    self.assertEqual(native, original)
                    baseline = scored_oracle(operations, universe)
                    self.assertEqual(native["touches"], baseline[0])
                    self.assertEqual(native["cancellations"], baseline[1])
                    self.assertEqual(native["xor_operations"], baseline[3])
                    for limit in (None, 0, 1, 2, n, n+7):
                        self.assertEqual(ranked_pair_candidates_rust(native, limit),
                                         ranked_pair_candidates(original, limit))
                    cross = pairwise_cross_merge_activity(operations, universe)
                    native_cross = pairwise_cross_merge_activity_rust(
                        operations, universe
                    )
                    self.assertEqual(native_cross, cross)
                    self.assertEqual(native_cross["scores"], baseline[2])
                    self.assertEqual(native_cross["cross_merge_events"],
                                     baseline[4])
                    self.assertEqual(len(native_cross["ranked_pairs"]),
                                     n*(n-1)//2)
                count += 1
        self.assertEqual(count, 1000)

    def test_malformed_operations_and_limits_fail_closed(self):
        cases = [
            ([{"operation": "INVALID"}], [1, 2]),
            ([{"operation": "ADD_ROW_XOR",
               "before": {"coefficients": [1, 1]},
               "source": {"coefficients": [2]}}], [1, 2]),
            ([{"operation": "ADD_ROW_XOR",
               "before": {"coefficients": [1, 3]},
               "source": {"coefficients": [2]}}], [1, 2]),
            ([{"operation": "ADD_ROW_XOR",
               "before": {"coefficients": [True]},
               "source": {"coefficients": [2]}}], [1, 2]),
            ([{"operation": "ADD_ROW_XOR",
               "before": None,
               "source": {"coefficients": [2]}}], [1, 2]),
        ]
        for operations, universe in cases:
            with self.subTest(ops=operations):
                for func in (
                    activity_from_g5_operations_rust,
                    pairwise_cross_merge_activity_rust,
                    activity_from_g5_operations,
                    pairwise_cross_merge_activity,
                ):
                    with self.assertRaises(ValueError):
                        func(operations, universe)
        normal = activity_from_g5_operations_rust([], [1, 2])
        for limit in (-1, True, 2.5):
            with self.assertRaises(ValueError):
                ranked_pair_candidates_rust(normal, limit)
            with self.assertRaises(ValueError):
                ranked_pair_candidates(normal, limit)


if __name__ == "__main__":
    unittest.main()
