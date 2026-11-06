"""Tiny transparent reference DPLL with exact source-clause scan counts.

This is a correctness/cost comparator for 5-variable inputs, not Kissat or
an optimized production SAT engine. Its clause scanning is explicit.
"""

from __future__ import annotations


def solve(clauses: list[list[int]]):
    stats={"nodes":0,"decisions":0,"unit_assignments":0,"clause_scans":0}

    def dpll(partial):
        stats["nodes"]+=1
        while True:
            units=[]
            all_satisfied=True
            first_open=None
            for clause in clauses:
                stats["clause_scans"]+=1
                available=[]
                satisfied=False
                for lit in clause:
                    assigned=partial.get(abs(lit))
                    if assigned is None:
                        available.append(lit)
                    elif assigned==(lit>0):
                        satisfied=True
                        break
                if satisfied:
                    continue
                all_satisfied=False
                if not available:
                    return None
                if first_open is None:
                    first_open=available[0]
                if len(available)==1:
                    units.append(available[0])
            if all_satisfied:
                return partial
            if not units:
                break
            changed=False
            for lit in units:
                idx=abs(lit)
                value=(lit>0)
                if idx in partial and partial[idx]!=value:
                    return None
                if idx not in partial:
                    partial[idx]=value
                    stats["unit_assignments"]+=1
                    changed=True
            if not changed:
                raise RuntimeError("unit propagation failed to progress")
        idx=abs(first_open)
        stats["decisions"]+=1
        for value in (True,False):
            copy=dict(partial)
            copy[idx]=value
            solution=dpll(copy)
            if solution is not None:
                return solution
        return None

    answer=dpll({})
    return {"verdict":"SAT" if answer is not None else "UNSAT",
            "assignment":answer, **stats}
