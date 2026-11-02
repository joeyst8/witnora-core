"""MiniSat-informed (not MiniSat-derived) propagation A/B with matched DPLL.

Compare full repeated clause scans with persistent two-watched literals.
Both use one occurrence-based branching order, binary DFS, unit propagation,
no learning, restarts, or parity deductions. Correctness vs native MiniSat22.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from random import Random
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from scripts.experiment_cross_support_propagation import make_case
from scripts.experiment_event_cached_ood import random_three_sat, mixed_random_parities


class TrailDPLL:
    def __init__(self, clauses, watched):
        self.clauses = tuple(tuple(c) for c in clauses)
        self.watched = watched
        self.values = {}
        self.trail = []
        self.qhead = 0
        self.stats = Counter()
        counts = Counter(abs(lit) for c in self.clauses for lit in c)
        self.order = sorted(counts, key=lambda v: (-counts[v], v))
        self.watches = defaultdict(list)
        self.pairs = []
        if watched:
            for ci, c in enumerate(self.clauses):
                if len(c) >= 2:
                    self.pairs.append([0, 1])
                    self.watches[c[0]].append(ci)
                    self.watches[c[1]].append(ci)
                else:
                    self.pairs.append(None)

    def lit_value(self, lit):
        value = self.values.get(abs(lit))
        return None if value is None else value == (lit > 0)

    def enqueue(self, lit):
        v, value = abs(lit), lit > 0
        existing = self.values.get(v)
        if existing is not None:
            return existing == value
        self.values[v] = value
        self.trail.append(lit)
        self.stats["implications"] += 1
        return True

    def propagate_scan(self):
        # Entire active CNF is scanned after each batch of implications.
        while True:
            length = len(self.trail)
            for clause in self.clauses:
                self.stats["clause_visits"] += 1
                satisfied = False
                undefs = []
                for lit in clause:
                    self.stats["literal_visits"] += 1
                    value = self.lit_value(lit)
                    if value is True:
                        satisfied = True
                        break
                    if value is None:
                        undefs.append(lit)
                if satisfied:
                    continue
                if not undefs:
                    return False
                if len(undefs) == 1 and not self.enqueue(undefs[0]):
                    return False
            if len(self.trail) == length:
                return True

    def propagate_watch(self):
        while self.qhead < len(self.trail):
            falsified = -self.trail[self.qhead]
            self.qhead += 1
            watch_list = self.watches[falsified]
            idx = 0
            while idx < len(watch_list):
                ci = watch_list[idx]
                clause = self.clauses[ci]
                p0, p1 = self.pairs[ci]
                if clause[p0] == falsified:
                    changed = 0
                    other = p1
                else:
                    if clause[p1] != falsified:
                        raise AssertionError("stale watcher")
                    changed = 1
                    other = p0
                self.stats["clause_visits"] += 1
                self.stats["literal_visits"] += 1
                other_lit = clause[other]
                if self.lit_value(other_lit) is True:
                    idx += 1
                    continue
                replacement = None
                for k, lit in enumerate(clause):
                    if k in (p0, p1):
                        continue
                    self.stats["literal_visits"] += 1
                    if self.lit_value(lit) is not False:
                        replacement = k
                        break
                if replacement is not None:
                    self.pairs[ci][changed] = replacement
                    watch_list[idx] = watch_list[-1]
                    watch_list.pop()
                    self.watches[clause[replacement]].append(ci)
                    continue
                other_value = self.lit_value(other_lit)
                if other_value is False:
                    return False
                if other_value is None and not self.enqueue(other_lit):
                    return False
                idx += 1
        return True

    def propagate(self):
        return self.propagate_watch() if self.watched else self.propagate_scan()

    def undo(self, trail_size):
        for lit in self.trail[trail_size:]:
            del self.values[abs(lit)]
        del self.trail[trail_size:]
        self.qhead = min(self.qhead, trail_size)

    def search(self):
        self.stats["nodes"] += 1
        if not self.propagate():
            self.stats["conflicts"] += 1
            return False
        var = next((v for v in self.order if v not in self.values), None)
        if var is None:
            return True
        self.stats["decisions"] += 1
        for lit in (var, -var):
            checkpoint = len(self.trail)
            if self.enqueue(lit) and self.search():
                return True
            self.undo(checkpoint)
        return False

    def run(self):
        if any(not c for c in self.clauses):
            return False
        for clause in self.clauses:
            if len(clause) == 1 and not self.enqueue(clause[0]):
                return False
        return self.search()


def benchmark(seeds=12, repeats=7):
    if seeds < 1 or repeats < 1:
        raise ValueError("seeds and repeats must be positive")
    cases = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("conflict", "imply", "sat", "random"):
                cases.append(("cross_" + kind, n, seed, make_case(n, seed, kind)))
    for seed in range(seeds):
        cases += [("ood_3sat", 0, seed, random_three_sat(seed)),
                  ("ood_parity", 0, seed, mixed_random_parities(seed))]
    records = []
    for family, n, seed, formula in cases:
        clauses = formula.to_clause_lists()
        with Minisat22(bootstrap_with=clauses) as oracle:
            truth = oracle.solve()
        times = {"scan": [], "watch": [], "minisat": []}
        data = {}
        for rep in range(repeats):
            for mode in (("scan", "watch") if rep % 2 == 0 else ("watch", "scan")):
                start = perf_counter()
                solver = TrailDPLL(clauses, watched=(mode == "watch"))
                result = solver.run()
                times[mode].append((perf_counter() - start) * 1000)
                if result != truth:
                    raise AssertionError((family, n, seed, mode, result, truth))
                data[mode] = solver.stats
            start = perf_counter()
            with Minisat22(bootstrap_with=clauses) as native:
                if native.solve() != truth:
                    raise AssertionError("native inconsistency")
            times["minisat"].append((perf_counter() - start) * 1000)
        if data["scan"]["decisions"] != data["watch"]["decisions"]:
            raise AssertionError((family, seed, "different search trees", data))
        records.append({"family": family, "n": n, "seed": seed,
                        "truth": truth,
                        **{mode + "_ms": median(ts) for mode, ts in times.items()},
                        **{mode + "_" + key: data[mode][key]
                           for mode in ("scan", "watch")
                           for key in ("nodes", "decisions", "conflicts", "clause_visits", "literal_visits")}})
    return {"summary": {"cases": len(records), "truth_agreement": True,
                        "identical_search_decisions": True,
                        "watch_time_wins": sum(r["watch_ms"] < r["scan_ms"] for r in records),
                        "watch_clause_visit_wins": sum(r["watch_clause_visits"] < r["scan_clause_visits"] for r in records),
                        **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in records), 4)
                           for mode in ("scan", "watch", "minisat")},
                        **{mode + "_clause_visits": sum(r[mode + "_clause_visits"] for r in records)
                           for mode in ("scan", "watch")}},
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(benchmark()["summary"], indent=2))
