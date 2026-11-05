"""W024 independent audit: recompute source CNFs and moments, not Rust labels.

The 64 generated pairs are deliberate isomorphic relabelings, not independent
benchmark draws. Python is used ONLY for differential verification of Rust.
"""
import collections
import json
import os
import subprocess
import unittest

TRIPLES = ((1, 2, 3), (1, 4, 5), (2, 4, 6), (3, 5, 6), (7, 8, 9))
SAT_RHS = (0, 0, 0, 0, 1)
UNSAT_RHS = (0, 0, 0, 1, 0)


def next_rand(state):
    state ^= (state << 13) & 0xFFFFFFFF
    state ^= state >> 17
    state ^= (state << 5) & 0xFFFFFFFF
    return state & 0xFFFFFFFF


def shuffle(items, state):
    items = list(items)
    for i in range(len(items) - 1, 0, -1):
        state = next_rand(state)
        j = state % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items, state


def encode(triples, rhs):
    clauses = []
    for triple, b in zip(triples, rhs):
        for pattern in range(8):
            if pattern.bit_count() % 2 != b:
                clauses.append([(-v if (pattern >> j) & 1 else v) for j, v in enumerate(triple)])
    return clauses


def reconstruct_pair(index):
    state = (0xD24F0240 ^ (((index + 1) * 0x9E3779B9) & 0xFFFFFFFF)) & 0xFFFFFFFF
    seed = state
    mapping, state = shuffle(range(1, 10), state)
    triples = [tuple(mapping[v - 1] for v in group) for group in TRIPLES]
    positions, _ = shuffle(range(20), state)
    return seed, [encode(triples, SAT_RHS)[i] for i in positions], [encode(triples, UNSAT_RHS)[i] for i in positions]


def source_stats(clauses):
    positive = [0] * 9
    negative = [0] * 9
    neg_hist = [0] * 4
    support = collections.Counter()
    gram = [[0] * 9 for _ in range(9)]
    for clause in clauses:
        assert len(clause) == 3
        key = tuple(sorted(abs(lit) for lit in clause))
        assert len(set(key)) == 3
        support[key] += 1
        neg_hist[sum(lit < 0 for lit in clause)] += 1
        for a in clause:
            (positive if a > 0 else negative)[abs(a) - 1] += 1
            for b in clause:
                gram[abs(a) - 1][abs(b) - 1] += 1 if (a > 0) == (b > 0) else -1
    return (tuple(positive), tuple(negative), tuple(neg_hist), tuple(sorted(support.items())),
            tuple(tuple(row) for row in gram))


def model_count(clauses):
    return sum(all(any(((assignment >> (abs(lit) - 1)) & 1) == (lit > 0)
                           for lit in clause) for clause in clauses)
               for assignment in range(512))


def recover_from_source(clauses):
    groups = collections.defaultdict(list)
    for clause in clauses:
        key = tuple(sorted(abs(l) for l in clause))
        signs = tuple(1 if next(l for l in clause if abs(l) == var) > 0 else -1 for var in key)
        groups[key].append(signs)
    assert len(groups) == 5
    rows, moments = [], {}
    for key, sign_rows in sorted(groups.items()):
        assert len(sign_rows) == len(set(sign_rows)) == 4
        products = [a * b * c for a, b, c in sign_rows]
        assert len(set(products)) == 1
        moments[key] = sum(products)
        mask = sum(1 << (v - 1) for v in key)
        rows.append((key, mask, int(products[0] > 0)))

    # Independent exhaustive linear-algebra consistency check (16 bit masks).
    consistent = any(all(((assignment & mask).bit_count() & 1) == rhs
                         for _, mask, rhs in rows) for assignment in range(512))
    witnesses = []
    for bits in range(1, 1 << 5):
        mask = 0
        rhs = 0
        selected = []
        for i, (key, rowmask, rowrhs) in enumerate(rows):
            if (bits >> i) & 1:
                mask ^= rowmask
                rhs ^= rowrhs
                selected.append(key)
        if mask == 0 and rhs == 1:
            witnesses.append(selected)
    assert consistent == (len(witnesses) == 0)
    return consistent, moments, witnesses


class MomentBarrierIndependentTests(unittest.TestCase):
    def test_every_pair_and_all_preregistered_controls(self):
        path = os.environ.get("WITNORA_RUST_MOMENT_BIN")
        self.assertTrue(path and os.path.isfile(path), "set WITNORA_RUST_MOMENT_BIN")
        completed = subprocess.run([path, "--json"], capture_output=True, text=True, check=True)
        report = json.loads(completed.stdout)
        self.assertEqual(report["study"], "W-CROSSDOMAIN-024")
        self.assertEqual(report["case_count"], 64)
        self.assertEqual(len(report["cases"]), 64)
        self.assertEqual(report["controls_with_full_clauses"], [0, 1, 31, 63])
        controls = {0, 1, 31, 63}
        for i, case in enumerate(report["cases"]):
            with self.subTest(case=i):
                seed, sat, unsat = reconstruct_pair(i)
                self.assertEqual(case["index"], i)
                self.assertEqual(case["seed"], seed)
                self.assertEqual((len(sat), len(unsat)), (20, 20))
                s, u = source_stats(sat), source_stats(unsat)
                self.assertEqual(s, u)
                self.assertEqual(s[2], (1, 12, 3, 4))
                self.assertEqual(len(s[3]), 5)
                self.assertEqual(s[0], s[1])
                for a in range(9):
                    for b in range(9):
                        self.assertEqual(s[4][a][b], s[0][a] + s[1][a] if a == b else 0)
                sat_count, unsat_count = model_count(sat), model_count(unsat)
                self.assertEqual((sat_count, unsat_count), (32, 0))
                self.assertEqual((case["models_sat"], case["models_unsat"]), (32, 0))
                sat_consistent, sat_moments, sat_witnesses = recover_from_source(sat)
                unsat_consistent, unsat_moments, unsat_witnesses = recover_from_source(unsat)
                self.assertTrue(sat_consistent)
                self.assertFalse(unsat_consistent)
                self.assertFalse(sat_witnesses)
                self.assertTrue(unsat_witnesses)
                self.assertEqual(sorted(sat_moments.values()), sorted(unsat_moments.values()))
                self.assertNotEqual(sat_moments, unsat_moments)
                self.assertTrue(case["all_first_second_order_stats_match"])
                self.assertTrue(case["pairwise_normalized_gram_is_identity_over_three"])
                self.assertTrue(case["aggregate_third_order_histograms_match"])
                self.assertTrue(case["triple_indexed_third_moments_differ"])
                self.assertTrue(case["xor_recovers_sat"])
                self.assertTrue(case["xor_recovers_unsat"])
                witness = [tuple(x) for x in case["unsat_xor_witness_triplets"]]
                self.assertIn(witness, unsat_witnesses)
                if i in controls:
                    self.assertEqual(case["independent_control"]["sat_clauses"], sat)
                    self.assertEqual(case["independent_control"]["unsat_clauses"], unsat)
                else:
                    self.assertNotIn("independent_control", case)


if __name__ == "__main__":
    unittest.main()
