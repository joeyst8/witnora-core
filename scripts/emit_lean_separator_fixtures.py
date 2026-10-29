"""Emit Lean claims for independent finite CNF-branch checking.

Python serializes the original formula and its actual G14-conditioned
components. Lean independently checks equivalence by exhaustive evaluation.
This bounded regression test is not a proof about every Python execution.
"""
from pathlib import Path
from witnora_core.separator_affine_family_theorem import (
    _all_assignments, _component_dicts, _condition_by_separator,
    make_separator_affine_instance, build_separator_affine_certificate,
    check_separator_affine_certificate, SAT_CERTIFIED, UNSAT_CERTIFIED,
)

CASES = ("saf_sat_chain_2", "saf_unsat_cover_2", "saf_balanced_sat_2")

def lean_bool(value):
    return "true" if value else "false"

def lean_cnf(formula):
    rows = []
    for clause in formula.to_clause_lists():
        lits = [f"({abs(lit)}, {lean_bool(lit > 0)})" for lit in clause]
        rows.append("[" + ", ".join(lits) + "]")
    return "[" + ", ".join(rows) + "]"

def main():
    out = [
        "import Witnora.Concrete",
        "import Witnora.Verdict",
        "",
        "/- Actual G14 Python conditioning outputs; independent Lean claims. -/",
        "namespace Witnora.Generated",
    ]
    count = 0
    for name in CASES:
        instance = make_separator_affine_instance(name)
        n = max(instance.formula.variables, default=0)
        if n > 10:
            raise RuntimeError("bounded fixture too large")
        cert = build_separator_affine_certificate(instance)
        check = check_separator_affine_certificate(instance.formula, cert)
        if check["checker_status"] != "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED":
            raise RuntimeError(f"{name}: Python certificate rejected")
        if cert.final_result == SAT_CERTIFIED:
            predicate = "isSat"
        elif cert.final_result == UNSAT_CERTIFIED:
            predicate = "isUnsat"
        else:
            raise RuntimeError(f"{name}: no certified result")
        out.append(
            f"example : Witnora.Concrete.{predicate} {n} "
            f"{lean_cnf(instance.formula)} = true := by decide"
        )
        claimed_sat = lean_bool(cert.final_result == SAT_CERTIFIED)
        out.append(
            f"example : Witnora.Verdict.accepts {n} "
            f"{lean_cnf(instance.formula)} {claimed_sat} = true := by decide"
        )
        comps = _component_dicts(instance.formula, instance.separator_variables)
        for a in _all_assignments(instance.separator_variables):
            _, parts, errors = _condition_by_separator(instance.formula, a, comps)
            if errors:
                raise RuntimeError(f"{name}: unexpected conditioning errors {errors}")
            fixed = "[" + ", ".join(
                f"({v}, {lean_bool(a[v])})" for v in sorted(a)
            ) + "]"
            component_list = "[" + ", ".join(
                lean_cnf(parts[c["component_id"]]) for c in comps
            ) + "]"
            out.append(
                f"example : Witnora.Concrete.checkBranch {n} "
                f"{lean_cnf(instance.formula)} {fixed} {component_list} = true := by decide"
            )
            if name == "saf_sat_chain_2" and not any(a.values()):
                out.append(
                    f"example : Witnora.Concrete.checkBranch {n} "
                    f"{lean_cnf(instance.formula)} {fixed} [] = false := by decide"
                )
            count += 1
    out.extend(["", "end Witnora.Generated", ""])
    target = Path("formal/Witnora/Generated.lean")
    target.write_text("\n".join(out), encoding="utf-8")
    print(f"Emitted {count} Lean checks to {target}")

if __name__ == "__main__":
    main()
