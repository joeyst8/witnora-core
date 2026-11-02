"""Controlled interaction gate: activity, phase saving and bounded restarts.

Static CDCL and four 2x2 activity variants all use the same watched-clause
and first-UIP engine; only polarity memory/restart scheduling are toggled.
"""
from __future__ import annotations

from collections import Counter
from math import ceil
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from scripts.experiment_minisat_first_uip import FirstUIP, pigeonhole
from scripts.experiment_minisat_vsids_ablation import ActivityFirstUIP, random_near_transition
from scripts.experiment_cross_support_propagation import make_case
from scripts.experiment_event_cached_ood import random_three_sat, mixed_random_parities


class ActivityPhaseRestart(ActivityFirstUIP):
    def __init__(self, clauses, *, phase_save=True, restarts=True, first_restart=32):
        if first_restart < 1:
            raise ValueError("restart interval must be positive")
        super().__init__(clauses)
        self.phase_save = phase_save
        self.restarts = restarts
        self.saved = {}
        self.restart_spacing = first_restart
        self.next_restart_at = first_restart

    def backjump(self, target):
        if self.phase_save and target < len(self.trail_lim):
            for lit in self.trail[self.trail_lim[target]:]:
                self.saved[abs(lit)] = lit > 0
        super().backjump(target)

    def branch_literal(self, variable):
        if self.phase_save and not self.saved.get(variable, True):
            self.stats["saved_negative_phases"] += 1
            return -variable
        return variable

    def after_learning(self):
        if not self.restarts or self.stats["conflicts"] < self.next_restart_at:
            return
        if self.trail_lim:
            self.backjump(0)
            # Revisit permanent level-zero assignments for newly attached
            # learned clauses, whose watchers did not exist earlier.
            self.qhead = 0
        self.stats["restarts"] += 1
        self.restart_spacing = ceil(self.restart_spacing * 1.5)
        self.next_restart_at += self.restart_spacing


MODES = ("static", "activity", "phase", "restart", "combined")


def make_solver(clauses, mode):
    if mode == "static":
        return FirstUIP(clauses)
    if mode == "activity":
        return ActivityFirstUIP(clauses)
    if mode == "phase":
        return ActivityPhaseRestart(clauses, phase_save=True, restarts=False)
    if mode == "restart":
        return ActivityPhaseRestart(clauses, phase_save=False, restarts=True)
    if mode == "combined":
        return ActivityPhaseRestart(clauses, phase_save=True, restarts=True)
    raise ValueError("unknown mode")


def benchmark(seeds=12, repeats=5, conflict_budget=2000):
    if seeds < 1 or repeats < 1 or conflict_budget < 1:
        raise ValueError("invalid benchmark budget")
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
        with Minisat22(bootstrap_with=clauses) as oracle:
            expected = oracle.solve()
        timings = {mode: [] for mode in (*MODES, "minisat")}
        counters = {}
        outcomes = {}
        for rep in range(repeats):
            order = MODES[rep % len(MODES):] + MODES[:rep % len(MODES)]
            for mode in order:
                start = perf_counter()
                solver = make_solver(clauses, mode)
                result = solver.solve(conflict_budget=conflict_budget)
                timings[mode].append((perf_counter() - start) * 1000)
                if result is not None and result != expected:
                    raise AssertionError((family, seed, mode, expected, result))
                outcomes[mode] = "UNKNOWN" if result is None else "SOLVED"
                counters[mode] = solver.stats
            start = perf_counter()
            with Minisat22(bootstrap_with=clauses) as oracle:
                if oracle.solve() != expected:
                    raise AssertionError("oracle nondeterminism")
            timings["minisat"].append((perf_counter() - start) * 1000)
        records.append({"family": family, "n": n, "seed": seed,
                        "expected": expected,
                        **{mode + "_status": outcomes[mode] for mode in MODES},
                        **{mode + "_ms": median(times) for mode, times in timings.items()},
                        **{mode + "_" + key: counters[mode][key] for mode in MODES
                           for key in ("decisions", "conflicts", "learned", "restarts", "saved_negative_phases")}})
    all_solved = [r for r in records if all(r[m + "_status"] == "SOLVED" for m in MODES)]
    return {"summary": {"cases": len(records), "all_modes_solved": len(all_solved),
                        "completed_answer_disagreements": 0,
                        **{m + "_unknown": sum(r[m + "_status"] == "UNKNOWN" for r in records) for m in MODES},
                        **{m + "_total_ms_common_solved": round(sum(r[m + "_ms"] for r in all_solved), 4)
                           for m in (*MODES, "minisat")},
                        **{m + "_total_ms_charged": round(sum(r[m + "_ms"] for r in records), 4)
                           for m in (*MODES, "minisat")},
                        **{m + "_faster_than_activity": sum(r[m + "_ms"] < r["activity_ms"] for r in all_solved)
                           for m in ("phase", "restart", "combined")},
                        **{m + "_total_restarts": sum(r[m + "_restarts"] for r in records)
                           for m in ("restart", "combined")}},
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(benchmark()["summary"], indent=2))
