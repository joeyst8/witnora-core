"""Experimental first-UIP CDCL vs watched-literal DPLL, not production.

Own Python implementation of the standard CDCL algorithm studied in
MiniSat. Uses watched clauses, a reversible trail with implication reasons,
first-UIP resolution, non-chronological backjumping. No restarts, VSIDS,
or clause database deletion. Does not emit a certified UNSAT proof.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from statistics import median
from time import perf_counter

from pysat.solvers import Minisat22

from scripts.experiment_minisat_watch_reverse_engineering import TrailDPLL
from scripts.experiment_cross_support_propagation import make_case
from scripts.experiment_event_cached_ood import random_three_sat, mixed_random_parities


class FirstUIP:
    def __init__(self, clauses):
        self.original = tuple(tuple(c) for c in clauses)
        self.clauses = []
        self.watches = defaultdict(list)
        self.pairs = []
        self.values = {}
        self.level = {}
        self.reason = {}
        self.trail = []
        self.trail_lim = []
        self.qhead = 0
        self.stats = Counter()
        self.learned = []
        counts = Counter(abs(l) for c in self.original for l in c)
        self.order = sorted(counts, key=lambda v: (-counts[v], v))

    def literal_value(self, lit):
        val = self.values.get(abs(lit))
        return None if val is None else (val == (lit > 0))

    def enqueue(self, lit, reason=None):
        v = abs(lit)
        val = lit > 0
        old = self.values.get(v)
        if old is not None:
            return old == val
        self.values[v] = val
        self.reason[v] = reason
        self.level[v] = len(self.trail_lim)
        self.trail.append(lit)
        return True

    def attach(self, clause):
        ci = len(self.clauses)
        clause = tuple(clause)
        self.clauses.append(clause)
        if len(clause) > 1:
            self.pairs.append([0, 1])
            self.watches[clause[0]].append(ci)
            self.watches[clause[1]].append(ci)
        else:
            self.pairs.append(None)
        return ci

    def propagate(self):
        while self.qhead < len(self.trail):
            falsified = -self.trail[self.qhead]
            self.qhead += 1
            watches = self.watches[falsified]
            i = 0
            while i < len(watches):
                ci = watches[i]
                clause = self.clauses[ci]
                first, second = self.pairs[ci]
                if clause[first] == falsified:
                    updated, other = 0, second
                elif clause[second] == falsified:
                    updated, other = 1, first
                else:
                    raise AssertionError("inconsistent watched literal")
                self.stats["clause_visits"] += 1
                other_lit = clause[other]
                if self.literal_value(other_lit) is True:
                    i += 1
                    continue
                replacement = next((k for k, lit in enumerate(clause)
                                    if k not in (first, second)
                                    and self.literal_value(lit) is not False), None)
                if replacement is not None:
                    self.pairs[ci][updated] = replacement
                    watches[i] = watches[-1]
                    watches.pop()
                    self.watches[clause[replacement]].append(ci)
                    continue
                if self.literal_value(other_lit) is False:
                    return ci
                if not self.enqueue(other_lit, reason=ci):
                    return ci
                i += 1
        return None

    def analyze(self, conflict):
        """Standard first-UIP implication-graph resolution, no minimization."""
        learnt = [0]
        seen = set()
        pending = 0
        trail_index = len(self.trail) - 1
        pivot_lit = None
        current_clause = self.clauses[conflict]
        while True:
            for lit in current_clause:
                v = abs(lit)
                if v == abs(pivot_lit or 0) or v in seen or self.level[v] == 0:
                    continue
                seen.add(v)
                self.note_conflict_var(v)
                if self.level[v] == len(self.trail_lim):
                    pending += 1
                else:
                    learnt.append(lit)
            while abs(self.trail[trail_index]) not in seen:
                trail_index -= 1
            pivot_lit = self.trail[trail_index]
            trail_index -= 1
            seen.remove(abs(pivot_lit))
            pending -= 1
            if pending == 0:
                learnt[0] = -pivot_lit
                break
            reason = self.reason[abs(pivot_lit)]
            if reason is None:
                raise AssertionError("first-UIP trace encountered unexplained variable")
            current_clause = self.clauses[reason]
        if len({abs(l) for l in learnt}) != len(learnt):
            raise AssertionError("duplicate variable in learnt clause")
        backlevel = max((self.level[abs(l)] for l in learnt[1:]), default=0)
        return tuple(learnt), backlevel

    def note_conflict_var(self, variable):
        """Hook for activity-based branching; fixed-order baseline does nothing."""

    def finish_conflict(self):
        """Hook for activity decay; no-op in fixed-order baseline."""

    def pick_branch(self):
        return next((v for v in self.order if v not in self.values), None)

    def backjump(self, target):
        if target >= len(self.trail_lim):
            return
        cut = self.trail_lim[target]
        for lit in self.trail[cut:]:
            v = abs(lit)
            del self.values[v]
            del self.level[v]
            del self.reason[v]
        del self.trail[cut:]
        del self.trail_lim[target:]
        self.qhead = min(self.qhead, len(self.trail))

    def solve(self, conflict_budget=None):
        if any(not c for c in self.original):
            return False
        for clause in self.original:
            ci = self.attach(clause)
            if len(clause) == 1 and not self.enqueue(clause[0], reason=ci):
                return False
        while True:
            self.stats["nodes"] += 1
            conflict = self.propagate()
            if conflict is not None:
                self.stats["conflicts"] += 1
                if not self.trail_lim:
                    return False
                if conflict_budget is not None and self.stats["conflicts"] >= conflict_budget:
                    self.stats["budget_exhausted"] += 1
                    return None
                learnt, backlevel = self.analyze(conflict)
                self.finish_conflict()
                oldlevel = len(self.trail_lim)
                self.backjump(backlevel)
                self.stats["backjump_levels"] += oldlevel - backlevel
                if any(self.literal_value(lit) is not False for lit in learnt[1:]):
                    raise AssertionError("learned clause is not asserting after backjump")
                ci = self.attach(learnt)
                self.learned.append(learnt)
                self.stats["learned"] += 1
                if not self.enqueue(learnt[0], reason=ci):
                    raise AssertionError("learned asserting clause contradicts backjump")
            else:
                var = self.pick_branch()
                if var is None:
                    return True
                self.stats["decisions"] += 1
                self.trail_lim.append(len(self.trail))
                if not self.enqueue(var):
                    raise AssertionError("branch variable previously assigned")


def pigeonhole(pigeons, holes):
    clauses = []
    var = lambda pigeon, hole: pigeon * holes + hole + 1
    for pigeon in range(pigeons):
        clauses.append(tuple(var(pigeon, hole) for hole in range(holes)))
        for h in range(holes):
            for k in range(h + 1, holes):
                clauses.append((-var(pigeon, h), -var(pigeon, k)))
    for hole in range(holes):
        for i in range(pigeons):
            for j in range(i + 1, pigeons):
                clauses.append((-var(i, hole), -var(j, hole)))
    return clauses


def benchmark(seeds=12, repeats=5):
    cases = []
    for n in (16, 32):
        for seed in range(seeds):
            for kind in ("conflict", "imply", "sat", "random"):
                cases.append(("cross_" + kind, n, seed, make_case(n, seed, kind).to_clause_lists()))
    for seed in range(seeds):
        cases.extend([("ood_3sat", 0, seed, random_three_sat(seed).to_clause_lists()),
                      ("ood_parity", 0, seed, mixed_random_parities(seed).to_clause_lists())])
    for holes in (3, 4, 5, 6, 7):
        cases.append(("pigeonhole", holes + 1, holes, pigeonhole(holes + 1, holes)))
    records = []
    for family, n, seed, clauses in cases:
        with Minisat22(bootstrap_with=clauses) as native:
            truth = native.solve()
        trials = {"dpll": [], "cdcl": [], "minisat": []}
        stats = {}
        for rep in range(repeats):
            for mode in (("dpll", "cdcl") if rep % 2 == 0 else ("cdcl", "dpll")):
                begin = perf_counter()
                solver = TrailDPLL(clauses, watched=True) if mode == "dpll" else FirstUIP(clauses)
                result = solver.run() if mode == "dpll" else solver.solve()
                elapsed = (perf_counter() - begin) * 1000
                if result != truth:
                    raise AssertionError((family, seed, mode, truth, result))
                trials[mode].append(elapsed)
                stats[mode] = solver.stats
            begin = perf_counter()
            with Minisat22(bootstrap_with=clauses) as native:
                if native.solve() != truth:
                    raise AssertionError("native solver disagreement")
            trials["minisat"].append((perf_counter() - begin) * 1000)
        records.append({"family": family, "n": n, "seed": seed, "sat": truth,
                        **{mode + "_ms": median(ts) for mode, ts in trials.items()},
                        **{mode + "_" + key: stats[mode][key]
                           for mode in ("dpll", "cdcl")
                           for key in ("decisions", "conflicts", "clause_visits", "learned")}})
    return {"summary": {"cases": len(records), "all_answers_agree": True,
                        "cdcl_time_wins": sum(r["cdcl_ms"] < r["dpll_ms"] for r in records),
                        "cdcl_decision_wins": sum(r["cdcl_decisions"] < r["dpll_decisions"] for r in records),
                        "learned_clauses": sum(r["cdcl_learned"] for r in records),
                        **{mode + "_total_ms": round(sum(r[mode + "_ms"] for r in records), 4)
                           for mode in ("dpll", "cdcl", "minisat")}},
            "records": records}


if __name__ == "__main__":
    import json
    print(json.dumps(benchmark()["summary"], indent=2))
