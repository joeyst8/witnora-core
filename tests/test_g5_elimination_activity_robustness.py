"""Adversarial relabeling and row-order study for G5 activity separator ranks.

This is an empirical audit, not a proof of separator quality. We deliberately
record losses and counterexamples rather than filtering them away.
"""

import json
import random
import statistics
import unittest
from itertools import combinations

from witnora_core.g5_elimination_activity import (
    activity_from_g5_operations,
    ranked_pair_candidates,
)
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from tests.test_g5_elimination_activity import two_bridge_equations


class G5ActivityRobustnessTest(unittest.TestCase):
    def test_relabel_and_row_order_study(self):
        randomizer = random.Random(630632)
        original = (1, 2, 3, 4, 9, 10)
        trials = 96
        records = []
        for trial in range(trials):
            labels = randomizer.sample(range(1, 128), len(original))
            mapping = dict(zip(original, labels))
            equations = two_bridge_equations()
            randomizer.shuffle(equations)
            translated = [
                {
                    "variables": [mapping[v] for v in eq["variables"]],
                    "parity_bit": eq["parity_bit"],
                }
                for eq in equations
            ]
            trace = gaussian_eliminate_gf2(translated)
            activity = activity_from_g5_operations(
                trace["row_operations"], mapping.values()
            )
            intended = {mapping[9], mapping[10]}
            g5_pairs = ranked_pair_candidates(activity)
            numeric_pairs = tuple(combinations(sorted(mapping.values()), 2))
            g5_rank = next(
                i + 1 for i, pair in enumerate(g5_pairs)
                if set(pair) == intended
            )
            baseline_rank = next(
                i + 1 for i, pair in enumerate(numeric_pairs)
                if set(pair) == intended
            )
            records.append({
                "trial": trial,
                "g5_rank": g5_rank,
                "baseline_rank": baseline_rank,
                "hit_first": g5_rank == 1,
            })
        self.assertEqual(len(records), trials)
        self.assertTrue(
            all(1 <= item["g5_rank"] <= 15 and
                1 <= item["baseline_rank"] <= 15 for item in records)
        )
        wins = sum(x["g5_rank"] < x["baseline_rank"] for x in records)
        ties = sum(x["g5_rank"] == x["baseline_rank"] for x in records)
        losses = trials - wins - ties
        summary = {
            "trials": trials,
            "first_pair_hits": sum(x["hit_first"] for x in records),
            "mean_g5_rank": round(statistics.mean(x["g5_rank"] for x in records), 3),
            "mean_numeric_rank": round(statistics.mean(x["baseline_rank"] for x in records), 3),
            "g5_better": wins,
            "tie": ties,
            "g5_worse": losses,
            "first_counterexamples": [
                row for row in records
                if row["g5_rank"] > row["baseline_rank"]
            ][:5],
        }
        print("G5_ACTIVITY_ADVERSARIAL_STUDY", json.dumps(summary, sort_keys=True))
        self.assertEqual(wins + ties + losses, trials)


if __name__ == "__main__":
    unittest.main()
