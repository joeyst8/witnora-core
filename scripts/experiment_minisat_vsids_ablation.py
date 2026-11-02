"""MiniSat-inspired activity-based branching, isolated from first-UIP CDCL.

The same watched-literal conflict-learning engine with either original static
occurrence order or a conflict-bumped, decaying activity priority. No heap,
phase saving, restarts, or database reduction in either variant.
"""
from __future__ import annotations

from random import Random
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula

from scripts.experiment_minisat_first_uip import FirstUIP, pigeonhole
from scripts.experiment_cross_support_propagation import make_case
from scripts.experiment_event_cached_ood import random_three_sat, mixed_random_parities


class ActivityFirstUIP(FirstUIP):
    def __init__(self, clauses, decay=0.95):
        if not 0 < decay < 1:
            raise ValueError("decay must lie strictly between 0 and 1")
        super().__init__(clauses)
        self.activity = {v: 0.0 for v in self.order}
        self.var_increment = 1.0
        self.decay = decay
        self.priorities = {v: i for i, v in enumerate(self.order)}

    def note_conflict_var(self, variable):
        self.activity[variable] += self.var_increment
        self.stats["activity_bumps"] += 1
        if self.activity[variable] > 1e100:
            for v in self.activity:
                self.activity[v] *= 1e-100
            self.var_increment *= 1e-100

    def finish_conflict(self):
        self.var_increment /= self.decay

    def pick_branch(self):
        remaining = (v for v in self.order if v not in self.values)
        return min(remaining,
                   key=lambda v: (-self.activity[v], self.priorities[v]),
                   default=None)


def random_near_transition(seed, n=24, ratio=4.25):
    rng = Random(620000 + seed + 101 * n)
    clauses = []
    for _ in range(round(n * ratio)):
        support = rng.sample(range(1, n + 1), 3)
        clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
    return CNFFormula.from_raw_clauses(clauses)


def benchmark(seeds=12, repeats=7, conflict_budget=2000):
    if seeds < 1 or repeats < 1:
        raise ValueError("seeds and repeats must be positive")
    cases = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("conflict", "imply", "sat", "random"):
                cases.append(("cross_" + kind, n, seed, make_case(n, seed, kind).to_clause_lists()))
    for seed in range(seeds):
        cases += [("ood_3sat", 0, seed, random_three_sat(seed).to_clause_lists()),
                  ("ood_parity", 0, seed, mixed_random_parities(seed).to_clause_lists()),
                  ("transition_3sat", 24, seed, random_near_transition(seed).to_clause_lists())]
    for holes in (3, 4, 5, 6, 7):
        cases.append(("pigeonhole", holes + 1, holes, pigeonhole(holes + 1, holes)))
    records = []
    for family, n, seed, clauses in cases:
        with Minisat22(bootstrap_with=clauses) as native:
            expected = native.solve()
        timings = {mode: [] for mode in ("static", "activity", "minisat")}
        counters = {}
        outcomes = {}
        for rep in range(repeats):
            for mode in (("static", "activity") if rep % 2 == 0 else ("activity", "static")):
                start = perf_counter()
                solver = FirstUIP(clauses) if mode == "static" else ActivityFirstUIP(clauses)
                result = solver.solve(conflict_budget=conflict_budget)
                timings[mode].append((perf_counter() - start) * 1000)
                if result is not None and result != expected:
                    raise AssertionError((family, n, seed, mode, result, expected))
                outcomes[mode] = result
                counters[mode] = solver.stats
            start = perf_counter()
            with Minisat22(bootstrap_with=clauses) as oracle:
                if oracle.solve() != expected:
                    raise AssertionError("native solver mismatch")
            timings["minisat"].append((perf_counter() - start) * 1000)
        records.append({"family": family, "n": n, "seed": seed,
                        "expected": expected,
                        "static_status": "UNKNOWN" if outcomes["static"] is None else "SOLVED",
                        "activity_status": "UNKNOWN" if outcomes["activity"] is None else "SOLVED",
                        **{mode + "_ms": median(vals) for mode, vals in timings.items()},
                        **{mode + "_" + counter: counters[mode][counter]
                           for mode in ("static", "activity")
                           for counter in ("decisions", "conflicts", "learned", "clause_visits", "activity_bumps")}})
    both = [r for r in records if r["static_status"] == "SOLVED" and
            r["activity_status"] == "SOLVED"]
    return {"summary": {"cases": len(records), "solved_both": len(both),
                        "static_unknown": sum(r["static_status"] == "UNKNOWN" for r in records),
                        "activity_unknown": sum(r["activity_status"] == "UNKNOWN" for r in records),
                        "all_completed_answers_agree": True,
                        "activity_time_wins": sum(r["activity_ms"] < r["static_ms"] for r in both),
                        "activity_decision_wins": sum(r["activity_decisions"] < r["static_decisions"] for r in both),
                        "activity_decision_losses": sum(r["activity_decisions"] > r["static_decisions"] for r in both),
                        "activity_total_bumps": sum(r["activity_activity_bumps"] for r in records),
                        **{mode + "_total_ms_solved_both": round(sum(r[mode + "_ms"] for r in both), 4)
                           for mode in ("static", "activity", "minisat")},
                        **{mode + "_total_ms_including_budgeted": round(sum(r[mode + "_ms"] for r in records), 4)
                           for mode in ("static", "activity", "minisat")}},
            "by_family": [{"family": family,
                           "count": sum(r["family"] == family for r in records),
                           **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in records
                                                             if r["family"] == family), 4)
                              for mode in ("static", "activity", "minisat")},
                           "decision_wins": sum(r["family"] == family
                                                and r["activity_decisions"] < r["static_decisions"]
                                                for r in records)}
                          for family in sorted({r["family"] for r in records})],
            "records": records}


if __name__ == "__main__":
    import json
    report = benchmark()
    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["by_family"], indent=2))
