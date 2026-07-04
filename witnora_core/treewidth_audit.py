"""Exact primal-treewidth audit tools for small CNF diagnostics."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
from typing import Any
import zipfile

from .benchmark import max_clause_width
from .certificate import NO_COLLAPSE, SAT, UNSAT
from .cnf import CNFFormula
from .cnfgen_matrix import cnfgen_version
from .dimacs import parse_dimacs
from .primal import Graph, graph_edges, primal_graph
from .public_benchmarks import find_cnfgen_cli
from .runner import solve
from .treewidth import verify_elimination_order

AUDIT_VERSION = "0.9.0"

EXACT_WIDTH_FOUND = "EXACT_WIDTH_FOUND"
NOT_FOUND_UP_TO_MAX_C = "NOT_FOUND_UP_TO_MAX_C"
SKIPPED_TOO_MANY_VARIABLES = "SKIPPED_TOO_MANY_VARIABLES"
TIMEOUT = "TIMEOUT"

SOLVED_AS_EXPECTED = "SOLVED_AS_EXPECTED"
EXPECTED_NO_COLLAPSE_WIDTH_LIMIT = "EXPECTED_NO_COLLAPSE_WIDTH_LIMIT"
VE_ORDER_SEARCH_BUG = "VE_ORDER_SEARCH_BUG"
AUDIT_INCONCLUSIVE = "AUDIT_INCONCLUSIVE"


class AuditTimeout(Exception):
    pass


def _clone_graph(graph: Graph) -> Graph:
    return {var: set(neighs) for var, neighs in graph.items()}


def _canonical_state(graph: Graph) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...]]:
    return tuple(sorted(graph)), tuple(graph_edges(graph))


def _eliminate(graph: Graph, var: int) -> Graph:
    new_graph: Graph = {v: set(neighs) for v, neighs in graph.items() if v != var}
    neighbors = sorted(graph[var])
    for i, a in enumerate(neighbors):
        if a not in new_graph:
            continue
        for b in neighbors[i + 1 :]:
            if b not in new_graph:
                continue
            new_graph[a].add(b)
            new_graph[b].add(a)
    for neighs in new_graph.values():
        neighs.discard(var)
    return new_graph


def bounded_elimination_order_audit(
    graph: Graph,
    width_cap: int,
    *,
    timeout_seconds: float | None = None,
) -> list[int] | None:
    """Search for an elimination order of width at most width_cap.

    This diagnostic search intentionally supports caps beyond the solver's
    v0 route limit. It is for small audit instances only.
    """

    start = time.perf_counter()
    failed: set[tuple[tuple[int, ...], tuple[tuple[int, int], ...]]] = set()

    def check_timeout() -> None:
        if timeout_seconds is not None and time.perf_counter() - start > timeout_seconds:
            raise AuditTimeout()

    def search(current: Graph) -> list[int] | None:
        check_timeout()
        if not current:
            return []
        state = _canonical_state(current)
        if state in failed:
            return None
        min_degree = min(len(neighs) for neighs in current.values())
        if min_degree > width_cap:
            failed.add(state)
            return None
        candidates = [var for var in sorted(current) if len(current[var]) <= width_cap]
        candidates.sort(key=lambda var: (len(current[var]), var))
        for var in candidates:
            next_graph = _eliminate(current, var)
            rest = search(next_graph)
            if rest is not None:
                return [var] + rest
        failed.add(state)
        return None

    order = search(_clone_graph(graph))
    if order is None:
        return None
    verified = verify_elimination_order(graph, order)
    if verified is None or verified > width_cap:
        return None
    return order


def exact_width_audit(
    formula: CNFFormula,
    *,
    instance_name: str,
    max_c: int,
    max_vars: int = 24,
    timeout_seconds: float | None = 30.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    graph = primal_graph(formula)
    base = {
        "instance_name": instance_name,
        "num_vars": formula.num_vars,
        "num_clauses": formula.num_clauses,
        "primal_edges": len(graph_edges(graph)),
        "max_clause_width": max_clause_width(formula),
        "clique_lower_bound": max(0, max_clause_width(formula) - 1),
        "exact_width_found": None,
        "exact_order": [],
        "max_c_tested": max_c,
        "runtime_seconds": 0.0,
    }
    if formula.num_vars > max_vars:
        base.update(
            {
                "status": SKIPPED_TOO_MANY_VARIABLES,
                "skip_reason": "num_vars_exceeds_max_vars",
                "runtime_seconds": round(time.perf_counter() - started, 6),
            }
        )
        return base
    try:
        for c in range(0, max_c + 1):
            remaining_timeout = None
            if timeout_seconds is not None:
                elapsed = time.perf_counter() - started
                remaining_timeout = max(0.001, timeout_seconds - elapsed)
            order = bounded_elimination_order_audit(
                graph,
                c,
                timeout_seconds=remaining_timeout,
            )
            if order is not None:
                width = verify_elimination_order(graph, order)
                base.update(
                    {
                        "status": EXACT_WIDTH_FOUND,
                        "exact_width_found": width,
                        "exact_order": order,
                        "runtime_seconds": round(time.perf_counter() - started, 6),
                    }
                )
                return base
    except AuditTimeout:
        base.update(
            {
                "status": TIMEOUT,
                "runtime_seconds": round(time.perf_counter() - started, 6),
            }
        )
        return base
    base.update(
        {
            "status": NOT_FOUND_UP_TO_MAX_C,
            "runtime_seconds": round(time.perf_counter() - started, 6),
        }
    )
    return base


def compare_solver_to_audit(
    formula: CNFFormula,
    audit: dict[str, Any],
    c: int,
) -> dict[str, Any]:
    result = solve(formula, c)
    exact_width = audit.get("exact_width_found")
    solved = result.status in {SAT, UNSAT}
    exact_within_c = isinstance(exact_width, int) and exact_width <= c
    if solved:
        diagnosis = SOLVED_AS_EXPECTED
    elif exact_within_c:
        diagnosis = VE_ORDER_SEARCH_BUG
    elif audit.get("status") == EXACT_WIDTH_FOUND and isinstance(exact_width, int) and exact_width > c:
        diagnosis = EXPECTED_NO_COLLAPSE_WIDTH_LIMIT
    elif audit.get("status") == NOT_FOUND_UP_TO_MAX_C and int(audit.get("max_c_tested", -1)) >= c:
        diagnosis = EXPECTED_NO_COLLAPSE_WIDTH_LIMIT
    else:
        diagnosis = AUDIT_INCONCLUSIVE
    return {
        "instance_name": audit.get("instance_name", ""),
        "c_parameter": c,
        "witnora_status": result.status,
        "witnora_final_class": result.final_class,
        "witnora_solved": solved,
        "exact_width_found": exact_width,
        "audit_status": audit.get("status", ""),
        "exact_width_leq_c": exact_within_c,
        "diagnosis": diagnosis,
    }


def _run_cnfgen_php(pigeons: int, holes: int, output_path: Path, cnfgen_path: str | None) -> tuple[str, str]:
    cli = find_cnfgen_cli(cnfgen_path)
    if cli is None:
        raise FileNotFoundError("official cnfgen CLI not found")
    command = [cli, "php", str(pigeons), str(holes)]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError(proc.stderr or proc.stdout or "cnfgen php command failed")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(proc.stdout, encoding="utf-8")
    return " ".join(command), proc.stdout


def audit_official_pigeonhole(
    output_dir: str | Path,
    *,
    cnfgen_path: str | None = None,
    instances: list[tuple[int, int]] | None = None,
    max_c_by_instance: dict[str, int] | None = None,
    compare_c_values: list[int] | None = None,
    max_vars: int = 24,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    output = Path(output_dir)
    dimacs_dir = output / "generated_dimacs"
    instances = instances or [(3, 2), (4, 3), (5, 4), (6, 5)]
    max_c_by_instance = max_c_by_instance or {"php_4_3": 8, "php_5_4": 12}
    compare_c_values = compare_c_values or [2, 3, 4]
    audits: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    commands: list[str] = []
    for pigeons, holes in instances:
        name = f"php_{pigeons}_{holes}"
        path = dimacs_dir / f"{name}.cnf"
        command, dimacs_text = _run_cnfgen_php(pigeons, holes, path, cnfgen_path)
        commands.append(command)
        formula = parse_dimacs(dimacs_text)
        audit = exact_width_audit(
            formula,
            instance_name=name,
            max_c=max_c_by_instance.get(name, 8),
            max_vars=max_vars,
            timeout_seconds=timeout_seconds,
        )
        audits.append(audit)
        for c in compare_c_values:
            comparisons.append(compare_solver_to_audit(formula, audit, c))
    return {
        "version": AUDIT_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cnfgen_version": cnfgen_version(cnfgen_path),
        "cnfgen_path": find_cnfgen_cli(cnfgen_path) or "",
        "generation_commands": commands,
        "audits": audits,
        "comparisons": comparisons,
    }


def write_audit_csv(data: dict[str, Any], path: str | Path) -> None:
    columns = [
        "instance_name",
        "num_vars",
        "num_clauses",
        "primal_edges",
        "max_clause_width",
        "clique_lower_bound",
        "exact_width_found",
        "exact_order",
        "max_c_tested",
        "status",
        "runtime_seconds",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in data.get("audits", []):
            out = dict(row)
            out["exact_order"] = " ".join(str(v) for v in row.get("exact_order", []))
            writer.writerow(out)


def audit_report_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Witnora-Core v0.9.0 Exact Treewidth / VE Ordering Audit",
        "",
        "This audit checks whether selected NO_COLLAPSE results are explained by primal treewidth exceeding the tested c values or by a possible VE ordering-search bug.",
        "It is a diagnostic, not a hardness claim and not new solver logic.",
        "",
        f"- CNFgen: {data.get('cnfgen_version', '')}",
        f"- CNFgen path: {data.get('cnfgen_path', '')}",
        "",
        "## Exact Width Audit",
        "",
        "| Instance | Vars | Clauses | Edges | Clique LB | Status | Exact width | Max c tested | Runtime s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in data.get("audits", []):
        lines.append(
            "| {instance_name} | {num_vars} | {num_clauses} | {primal_edges} | {clique_lower_bound} | {status} | {exact_width_found} | {max_c_tested} | {runtime_seconds} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Solver Comparison",
            "",
            "| Instance | c | Witnora status | Final class | Exact width <= c | Diagnosis |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in data.get("comparisons", []):
        lines.append(
            "| {instance_name} | {c_parameter} | {witnora_status} | {witnora_final_class} | {exact_width_leq_c} | {diagnosis} |".format(
                **row
            )
        )
    php43 = next((row for row in data.get("audits", []) if row.get("instance_name") == "php_4_3"), None)
    lines.extend(["", "## php_4_3 Finding", ""])
    if php43 and php43.get("status") == EXACT_WIDTH_FOUND:
        width = php43.get("exact_width_found")
        if isinstance(width, int) and width <= 4:
            lines.append("`php_4_3` has exact width <= 4 in this audit. Any c=4 no-collapse needs VE investigation.")
        else:
            lines.append("`php_4_3` has exact width greater than 4 in this audit, so c=4 no-collapse is expected from the current width route.")
    else:
        lines.append("`php_4_3` was inconclusive in this audit.")
    lines.extend(
        [
            "",
            "Allowed claim: this audit verifies or refutes a specific width hypothesis for small formulas.",
            "Forbidden claims: no hardness claim, no P vs NP claim, no HARD/UNKNOWN status, and no broad solver-performance claim.",
            "",
        ]
    )
    return "\n".join(lines)


def write_audit_artifact(data: dict[str, Any], output_dir: str | Path, *, zip_path: str | Path | None = None) -> str | None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "audit_results.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_csv(data, output / "audit_results.csv")
    (output / "AUDIT_REPORT.md").write_text(audit_report_markdown(data), encoding="utf-8")
    if zip_path is None:
        return None
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        prefix = Path("outputs") / output.name if output.parent.name == "outputs" else Path(output.name)
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, (prefix / path.relative_to(output)).as_posix())
    return str(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit exact primal treewidth for small CNF formulas")
    parser.add_argument("--out-dir", default="outputs/v0.9.0-treewidth-audit")
    parser.add_argument("--cnfgen-path")
    parser.add_argument("--max-vars", type=int, default=24)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--zip", default="witnora-core-v0.9.0-treewidth-audit.zip")
    args = parser.parse_args(argv)
    data = audit_official_pigeonhole(
        args.out_dir,
        cnfgen_path=args.cnfgen_path,
        max_vars=args.max_vars,
        timeout_seconds=args.timeout_seconds,
    )
    write_audit_artifact(data, args.out_dir, zip_path=args.zip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
