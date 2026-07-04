"""Variable elimination for bounded-primal-treewidth CNF components."""

from __future__ import annotations

from typing import Any

from .certificate import NO_COLLAPSE, StepLogger
from .cnf import CNFFormula, Clause, has_tautology


def _resolve_on_variable(pos_clause: Clause, neg_clause: Clause, var: int) -> Clause | None:
    lits = [lit for lit in pos_clause if lit != var] + [
        lit for lit in neg_clause if lit != -var
    ]
    return Clause.from_literals(lits)


def eliminate_variable(
    formula: CNFFormula,
    var: int,
    width_cap: int,
    logger: StepLogger | None = None,
) -> tuple[str, CNFFormula, dict[str, Any]]:
    pos = [clause for clause in formula.clauses if var in clause]
    neg = [clause for clause in formula.clauses if -var in clause]
    removed = sorted(pos + neg, key=lambda c: c.literals)
    kept = [clause for clause in formula.clauses if var not in clause and -var not in clause]

    resolvents: dict[tuple[int, ...], Clause] = {}
    tautological: list[dict[str, Any]] = []
    generated: list[dict[str, Any]] = []
    max_resolvent_len = 0

    for a in sorted(pos, key=lambda c: c.literals):
        for b in sorted(neg, key=lambda c: c.literals):
            raw_lits = sorted([lit for lit in a if lit != var] + [lit for lit in b if lit != -var])
            if has_tautology(raw_lits):
                tautological.append(
                    {
                        "positive_clause": a.to_list(),
                        "negative_clause": b.to_list(),
                        "resolvent": raw_lits,
                    }
                )
                continue
            resolvent = _resolve_on_variable(a, b, var)
            if resolvent is None:
                tautological.append(
                    {
                        "positive_clause": a.to_list(),
                        "negative_clause": b.to_list(),
                        "resolvent": raw_lits,
                    }
                )
                continue
            max_resolvent_len = max(max_resolvent_len, len(resolvent))
            if len(resolvent) > width_cap:
                details = {
                    "status": NO_COLLAPSE,
                    "eliminated_variable": var,
                    "reason": "resolvent_exceeds_width_cap",
                    "resolvent": resolvent.to_list(),
                    "width_cap": width_cap,
                }
                return NO_COLLAPSE, formula, details
            resolvents[resolvent.literals] = resolvent
            generated.append(
                {
                    "positive_clause": a.to_list(),
                    "negative_clause": b.to_list(),
                    "resolvent": resolvent.to_list(),
                }
            )

    output = CNFFormula(kept + list(resolvents.values()))
    added = [clause.to_list() for clause in sorted(resolvents.values(), key=lambda c: c.literals)]
    details = {
        "status": "OK",
        "eliminated_variable": var,
        "width_cap": width_cap,
        "width_observed": max_resolvent_len,
        "tautological_resolvents_discarded": tautological,
        "generated_resolvents": generated,
        "added_resolvents": added,
    }
    if logger is not None:
        logger.append(
            "VE",
            formula,
            output,
            details=details,
            removed_clauses=[clause.to_list() for clause in removed],
            added_clauses=added,
            reconstruction_data={
                "eliminated_variable": var,
                "removed_clauses": [clause.to_list() for clause in removed],
                "added_resolvents": added,
                "input_formula_hash": formula.formula_hash,
                "output_formula_hash": output.formula_hash,
            },
        )
    return "OK", output, details


def run_variable_elimination(
    formula: CNFFormula,
    order: list[int],
    width_cap: int,
    logger: StepLogger | None = None,
) -> tuple[str, CNFFormula, dict[str, Any]]:
    current = formula
    for var in order:
        status, current, details = eliminate_variable(current, var, width_cap, logger)
        if status != "OK":
            return status, current, details
        if current.contains_empty_clause:
            return "UNSAT", current, {"reason": "empty_clause_after_elimination", "variable": var}
    return "SAT", current, {"reason": "all_variables_eliminated"}
