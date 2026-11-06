"""Falsifiable exhaustive five-variable study of weighted Walsh LP proof.

This pilot is deliberately small and exploratory. It records exact formulas,
truth-table outcomes, rationally auditable integer weights and whole LP cost.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import random
import statistics
import time

import numpy
import scipy

from scripts.w033_walsh_bound import walsh_bound
from scripts.w034_weighted_walsh import audit_integer_weights,search_integer_certificate


SEED = 340034
REPS = 40
SIZES = (12,16,20,24,32)


def brute_min_violated(nvars, clauses):
    return min(sum(not any(assignment[abs(lit)-1] == (lit > 0)
                           for lit in clause) for clause in clauses)
               for assignment in itertools.product((False,True), repeat=nvars))


def run():
    rng=random.Random(SEED)
    pool=[[a*s[0],b*s[1],c*s[2]]
          for a,b,c in itertools.combinations(range(1,6),3)
          for s in itertools.product((-1,1),repeat=3)]
    rows=[]
    for m in SIZES:
        for rep in range(REPS):
            clauses=rng.sample(pool,m)
            exact_min=brute_min_violated(5,clauses)
            ground_truth="UNSAT" if exact_min>0 else "SAT"
            unweighted=walsh_bound(5,clauses)
            started=time.perf_counter_ns()
            optimized=search_integer_certificate(5,clauses)
            lp_wall_ns=time.perf_counter_ns()-started
            # Never accept the approximate numerical LP alone.
            checked=audit_integer_weights(clauses,5,optimized["weights"])
            if checked["status"]!=optimized["status"]:
                raise RuntimeError("independent exact proof audit differs")
            if ground_truth=="SAT" and (
                    unweighted["status"]=="UNSAT_CERTIFIED" or
                    optimized["status"]=="UNSAT_CERTIFIED"):
                raise RuntimeError("false UNSAT certificate on exhaustively SAT input")
            if optimized["status"]=="UNSAT_CERTIFIED":
                assert min(sum(w for c,w in zip(clauses,optimized["weights"])
                               if not any(a[abs(lit)-1]==(lit>0) for lit in c))
                           for a in itertools.product((False,True),repeat=5))>0
            rows.append({"case_id":f"n5_m{m}_r{rep:02}","nvars":5,"clauses":clauses,
                         "min_violated_by_truth_table":exact_min,
                         "ground_truth":ground_truth,
                         "unweighted_status":unweighted["status"],
                         "weighted_status":optimized["status"],
                         "weights":optimized["weights"],
                         "exact_weighted_bound_numerator":checked["lower_bound_numerator"],
                         "LP_objective":optimized["optimizer_objective"],
                         "LP_wall_ns":lp_wall_ns})
        print("W034",m,"cases completed",REPS,flush=True)
    summary=[]
    for m in SIZES:
        group=[row for row in rows if len(row["clauses"])==m]
        summary.append({"clauses_per_formula":m,"sample_size":len(group),
                        "SAT":sum(row["ground_truth"]=="SAT" for row in group),
                        "UNSAT":sum(row["ground_truth"]=="UNSAT" for row in group),
                        "weighted_certified_UNSAT":sum(row["weighted_status"]=="UNSAT_CERTIFIED" for row in group),
                        "global_unweighted_certified_UNSAT":sum(row["unweighted_status"]=="UNSAT_CERTIFIED" for row in group),
                        "median_LP_wall_ms":statistics.median(row["LP_wall_ns"] for row in group)/1e6})
    report={"study":"W-CROSSDOMAIN-034","phase":"seeded_5_variable_exhaustive_small_pilot",
            "nvars":5,"seed":SEED,"reps_per_clause_size":REPS,"clause_sizes":list(SIZES),
            "source_formula_pool": "all 80 distinct 3-literal sign patterns on five vars",
            "python_numpy":numpy.__version__,"python_scipy":scipy.__version__,
            "protocol":"docs/W_CROSSDOMAIN_034_WEIGHTED_SPECTRAL_PROTOCOL.md",
            "rows":rows,"summary":summary,
            "scope":"small n=5 exploratory; weights exact verified; LP costs not competitive baseline"}
    Path(os.environ["W034_REPORT_PATH"]).write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print("W034_COMPLETE",len(rows),"formulas",flush=True)


if __name__=="__main__":
    run()
