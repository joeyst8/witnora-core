"""Collapse grammar comparison and operator-frontier diagnostics.

This module is a research harness, not a new SAT solver. It composes existing
certified Witnora routes to compare bounded collapse grammars and record where
adding an operator changes an observed, certificate-checkable outcome.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, Iterable
import zipfile

from .certificate import NO_COLLAPSE, XOR_UNSAT_NATIVE
from .cnf import CNFFormula
from .families import make_blocked_clique_collapse_family
from .proof import export_certificate_bundle
from .public_benchmarks import (
    ERROR,
    NO_COLLAPSE_FOUND,
    SAT_ASSIGNMENT_VERIFIED,
    TIMEOUT,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    UNSAT_XOR_NATIVE_ONLY,
    find_cnfgen_cli,
)
from .runner import solve, solve_with_xor
from .xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns

THEORY_VERSION = "2.0"
OPERATOR_STUB_NOT_EXECUTED = "OPERATOR_STUB_NOT_EXECUTED"

PUBLIC_CATEGORIES = [
    SAT_ASSIGNMENT_VERIFIED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    UNSAT_XOR_NATIVE_ONLY,
    UNSAT_NOT_EXTERNALLY_VERIFIED,
    NO_COLLAPSE_FOUND,
    OPERATOR_STUB_NOT_EXECUTED,
    TIMEOUT,
    ERROR,
]


@dataclass(frozen=True)
class CollapseOperator:
    name: str
    enabled: bool
    description: str
    certificate_supported: bool
    external_proof_supported: bool
    deterministic: bool
    resource_bounds: dict[str, Any] = field(default_factory=dict)
    stub: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CollapseGrammar:
    name: str
    operators: tuple[str, ...]
    terminal_classes: tuple[str, ...]
    max_c: int
    xor_max_k: int
    proof_policy: dict[str, Any]
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoryInstance:
    instance_id: str
    family: str
    formula: CNFFormula
    source: str
    notes: str = ""
    generation_command: str = ""


@dataclass(frozen=True)
class CollapseResult:
    instance_id: str
    family: str
    grammar: str
    status: str
    public_category: str
    collapse_path_found: bool
    discovery_route: str
    certification_level: str
    proof_status: str
    runtime: float
    detected_structures: dict[str, Any]
    blocked_reason: str
    artifact_paths: dict[str, str]
    formula_hash: str
    num_vars: int
    num_clauses: int
    step_types: list[str] = field(default_factory=list)
    c_parameter: int = 0
    source: str = ""
    notes: str = ""
    generation_command: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrictnessWitness:
    family: str
    instance: str
    base_grammar: str
    extended_grammar: str
    added_operator: str
    base_result: str
    extended_result: str
    certification_level: str
    evidence: list[dict[str, Any]]
    scope: str = "bounded configured grammar/resource comparison"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorDelta:
    operator_added: str
    families_helped: list[str]
    instances_changed: int
    externally_verified_delta: int
    native_only_delta: int
    no_collapse_delta: int
    failure_modes: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return sha256_file(target)


def collapse_operators() -> dict[str, CollapseOperator]:
    return {
        "UP": CollapseOperator("UP", True, "Unit propagation.", True, False, True),
        "PLE": CollapseOperator("PLE", True, "Pure literal elimination.", True, False, True),
        "SUB": CollapseOperator("SUB", True, "Deterministic subsumption deletion.", True, False, True),
        "BCE": CollapseOperator("BCE", True, "Blocked clause elimination.", True, False, True),
        "COMPONENTS": CollapseOperator("COMPONENTS", True, "Connected-component decomposition.", True, False, True),
        "VE": CollapseOperator("VE", True, "Bounded variable elimination.", True, False, True, {"max_c": 2}),
        "TWO_SAT": CollapseOperator("TWO_SAT", True, "2-SAT SCC terminal class.", True, False, True),
        "TREEWIDTH": CollapseOperator("TREEWIDTH", True, "Bounded primal-treewidth terminal class.", True, False, True, {"max_c": 2}),
        "EXACT_XOR": CollapseOperator("EXACT_XOR", True, "Exact full-CNF XOR extraction up to max_k.", True, False, True, {"max_k": 6}),
        "SPARSE_MIN_FILL_XOR": CollapseOperator("SPARSE_MIN_FILL_XOR", True, "Deterministic sparse/min-fill XOR elimination.", True, False, True),
        "XOR_DRAT_BRIDGE": CollapseOperator("XOR_DRAT_BRIDGE", True, "Bounded XOR-to-DRAT export when externally checked.", True, True, True),
        "HORN_PROTOTYPE": CollapseOperator("HORN_PROTOTYPE", False, "Horn operator placeholder.", False, False, True, stub=True),
        "CARDINALITY_PROTOTYPE": CollapseOperator("CARDINALITY_PROTOTYPE", False, "Small cardinality operator placeholder.", False, False, True, stub=True),
        "BACKDOOR_DIAGNOSTIC": CollapseOperator("BACKDOOR_DIAGNOSTIC", False, "Bounded backdoor-search diagnostic placeholder.", False, False, True, stub=True),
    }


def grammar_profiles() -> dict[str, CollapseGrammar]:
    base_ops = ("UP", "PLE", "SUB", "BCE", "VE", "COMPONENTS", "TWO_SAT", "TREEWIDTH")
    g1_ops = (*base_ops, "EXACT_XOR", "SPARSE_MIN_FILL_XOR", "XOR_DRAT_BRIDGE")
    terminals = ("SAT_ASSIGNMENT", "UNSAT_CONFLICT", "2SAT", "TREEWIDTH_LEQ_C", "NO_COLLAPSE_FOUND")
    xor_policy = {
        "xor_drat": True,
        "xor_elim_order": "sparse-min-fill",
        "max_row_width": 10,
        "max_proof_clauses": 100000,
        "max_proof_bytes": 10_000_000,
        "timeout_seconds": 300.0,
    }
    return {
        "G0_BASE": CollapseGrammar(
            "G0_BASE",
            base_ops,
            terminals,
            2,
            0,
            {"external_proof": "base DRAT only where already supported"},
            "UP, PLE, SUB, BCE, components, 2SAT, VE, and bounded treewidth under configured cap.",
        ),
        "G1_XOR": CollapseGrammar(
            "G1_XOR",
            g1_ops,
            (*terminals, "XOR_AFFINE"),
            2,
            6,
            xor_policy,
            "G0_BASE plus exact CNF XOR extraction and deterministic sparse/min-fill affine reasoning.",
        ),
        "G2_HORN_PROTOTYPE": CollapseGrammar(
            "G2_HORN_PROTOTYPE",
            (*g1_ops, "HORN_PROTOTYPE"),
            (*terminals, "XOR_AFFINE", "HORN_SAT"),
            2,
            6,
            {"operator_status": OPERATOR_STUB_NOT_EXECUTED},
            "Honest Horn placeholder; no Horn operator is executed in v2.0.",
        ),
        "G3_CARDINALITY_PROTOTYPE": CollapseGrammar(
            "G3_CARDINALITY_PROTOTYPE",
            (*g1_ops, "CARDINALITY_PROTOTYPE"),
            (*terminals, "XOR_AFFINE", "CARDINALITY"),
            2,
            6,
            {"operator_status": OPERATOR_STUB_NOT_EXECUTED},
            "Honest small-cardinality placeholder; no cardinality operator is executed in v2.0.",
        ),
        "G4_BACKDOOR_DIAGNOSTIC": CollapseGrammar(
            "G4_BACKDOOR_DIAGNOSTIC",
            (*g1_ops, "BACKDOOR_DIAGNOSTIC"),
            (*terminals, "XOR_AFFINE", "BACKDOOR_DIAGNOSTIC"),
            2,
            6,
            {"operator_status": OPERATOR_STUB_NOT_EXECUTED, "search_cap": "not executed"},
            "Backdoor diagnostic placeholder; no bounded backdoor search is executed in v2.0.",
        ),
    }


def _xor_formula(equations: Iterable[tuple[Iterable[int], int]]) -> CNFFormula:
    clauses: list[tuple[int, ...]] = []
    for variables, rhs in equations:
        clauses.extend(canonical_xor_cnf_clauses(tuple(variables), int(rhs)))
    return CNFFormula.from_raw_clauses(clauses)


def _pigeonhole_formula(pigeons: int, holes: int) -> CNFFormula:
    def var(pigeon: int, hole: int) -> int:
        return (pigeon - 1) * holes + hole

    clauses: list[list[int]] = []
    for pigeon in range(1, pigeons + 1):
        clauses.append([var(pigeon, hole) for hole in range(1, holes + 1)])
    for hole in range(1, holes + 1):
        for first in range(1, pigeons + 1):
            for second in range(first + 1, pigeons + 1):
                clauses.append([-var(first, hole), -var(second, hole)])
    return CNFFormula.from_raw_clauses(clauses)


def _run_cnfgen_tseitin(cnfgen: str, n: int, out_root: Path | None) -> TheoryInstance | None:
    command = [cnfgen, "--seed", str(n), "tseitin", str(n)]
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    if out_root is not None:
        dimacs = out_root / "generated_dimacs" / f"tseitin_{n}.cnf"
        dimacs.parent.mkdir(parents=True, exist_ok=True)
        dimacs.write_text(proc.stdout, encoding="utf-8", newline="\n")
        source = str(dimacs)
    else:
        source = "official_cnfgen_stdout"
    from .dimacs import parse_dimacs

    return TheoryInstance(
        f"tseitin_{n}",
        "tseitin",
        parse_dimacs(proc.stdout),
        source,
        "official CNFgen Tseitin instance generated for bounded theory lab",
        " ".join(command),
    )


def build_family_instances(
    families: Iterable[str],
    *,
    out_root: str | Path | None = None,
    cnfgen_path: str | Path | None = None,
    prefer_official_tseitin: bool = True,
) -> list[TheoryInstance]:
    root = Path(out_root) if out_root is not None else None
    instances: list[TheoryInstance] = []
    for family in list(families):
        if family == "tseitin":
            official = None
            cnfgen = find_cnfgen_cli(cnfgen_path) if prefer_official_tseitin else None
            if cnfgen is not None:
                official = _run_cnfgen_tseitin(cnfgen, 10, root)
            instances.append(
                official
                if official is not None
                else TheoryInstance(
                    "tseitin_fixture_4",
                    "tseitin",
                    _xor_formula([((1, 2, 3), 0), ((1, 2, 4), 0), ((3, 4), 1)]),
                    "built_in_tseitin_structural_fixture",
                    "fallback exact-XOR Tseitin-style contradiction; not official CNFgen output",
                )
            )
        elif family == "pigeonhole":
            for pigeons in range(3, 11):
                holes = pigeons - 1
                instances.append(
                    TheoryInstance(
                        f"php_{pigeons}_{holes}",
                        "pigeonhole",
                        _pigeonhole_formula(pigeons, holes),
                        "built_in_pigeonhole",
                        "deterministic pigeonhole CNF fixture",
                    )
                )
        elif family == "parity":
            instances.extend(
                [
                    TheoryInstance("parity_4_exact", "parity", _xor_formula([((1, 2, 3, 4), 1)]), "built_in_exact_xor", "small exact parity equation within max_k"),
                    TheoryInstance("parity_7_over_cap", "parity", _xor_formula([((1, 2, 3, 4, 5, 6, 7), 1)]), "built_in_exact_xor", "single parity equation over the default exact-XOR cap"),
                ]
            )
        elif family == "blocked-clique":
            instances.append(
                TheoryInstance("blocked_clique_n6", "blocked-clique", make_blocked_clique_collapse_family(6), "built_in_blocked_clique", "BCE strictness family from earlier Witnora diagnostics")
            )
        elif family == "xor-chain":
            instances.append(
                TheoryInstance(
                    "xor_chain_unsat_n5",
                    "xor-chain",
                    _xor_formula([((1, 2, 3, 4), 0), ((1, 2, 3, 5), 0), ((4, 5), 1)]),
                    "built_in_exact_xor_chain",
                    "contradictory exact XOR chain requiring affine reasoning under cap 2",
                )
            )
        elif family == "adversarial-mixed":
            incomplete = sorted(canonical_xor_cnf_clauses((1, 2, 3, 4), 0))[:-1]
            instances.append(
                TheoryInstance("near_xor_incomplete_k4", "adversarial-mixed", CNFFormula.from_raw_clauses(incomplete + [(1, 2, 3, 4, 5)]), "built_in_adversarial_near_xor", "incomplete XOR-looking pattern; detector must not claim exact XOR")
            )
            instances.append(
                TheoryInstance("xor_extra_clause_safe_k4", "adversarial-mixed", CNFFormula.from_raw_clauses(list(canonical_xor_cnf_clauses((1, 2, 3, 4), 0)) + [(1,)]), "built_in_adversarial_extra_clause", "exact XOR pattern plus extra clause; source clauses are retained")
            )
        elif family == "horn":
            instances.append(
                TheoryInstance("horn_stub_fixture", "horn", CNFFormula.from_raw_clauses([[-1, 2], [-2, 3], [-3]]), "built_in_horn_fixture", "Horn fixture used only to show the v2.0 Horn operator remains a stub")
            )
        elif family == "cardinality":
            instances.append(
                TheoryInstance("exactly_one_stub_fixture", "cardinality", CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3], [-2, -3]]), "built_in_cardinality_fixture", "small exactly-one fixture; cardinality operator is a stub in v2.0")
            )
        else:
            raise ValueError(f"unsupported theory family: {family}")
    return instances


def _detected_structures(formula: CNFFormula, xor_max_k: int) -> dict[str, Any]:
    detected = None if xor_max_k <= 0 else detect_cnf_xor_patterns(formula, max_k=xor_max_k)
    skipped = [
        item
        for item in (detected.diagnostics if detected is not None else ())
        if item.get("reason") == "XOR_PATTERN_SKIPPED_MAX_K"
    ]
    positive_counts = [sum(1 for lit in clause.literals if lit > 0) for clause in formula.clauses]
    horn_clauses = sum(1 for count in positive_counts if count <= 1)
    binary_negative = sum(1 for clause in formula.clauses if len(clause) == 2 and all(lit < 0 for lit in clause))
    return {
        "detected_xor_equations": len(detected.equations) if detected is not None else 0,
        "max_detected_xor_arity": max((len(eq.variables) for eq in detected.equations), default=0)
        if detected is not None
        else 0,
        "xor_skipped_over_max_k": len(skipped),
        "horn_clause_ratio": round(horn_clauses / formula.num_clauses, 6) if formula.num_clauses else 0.0,
        "binary_negative_clause_count": binary_negative,
        "max_clause_width": max((len(clause) for clause in formula.clauses), default=0),
    }


def _stub_result(instance: TheoryInstance, grammar: CollapseGrammar, started: float) -> CollapseResult:
    return CollapseResult(
        instance.instance_id,
        instance.family,
        grammar.name,
        OPERATOR_STUB_NOT_EXECUTED,
        OPERATOR_STUB_NOT_EXECUTED,
        False,
        "OPERATOR_STUB_NOT_EXECUTED",
        "NOT_EXTERNALLY_VERIFIED",
        OPERATOR_STUB_NOT_EXECUTED,
        round(time.perf_counter() - started, 6),
        _detected_structures(instance.formula, grammar.xor_max_k),
        "OPERATOR_STUB_NOT_EXECUTED",
        {},
        instance.formula.formula_hash,
        instance.formula.num_vars,
        instance.formula.num_clauses,
        [],
        grammar.max_c,
        instance.source,
        instance.notes,
        instance.generation_command,
    )


def run_instance(
    instance: TheoryInstance,
    grammar: CollapseGrammar,
    *,
    out_root: str | Path | None = None,
    strict: bool = False,
    drat_trim_path: str | Path | None = None,
) -> CollapseResult:
    started = time.perf_counter()
    if any(op.endswith("_PROTOTYPE") or op == "BACKDOOR_DIAGNOSTIC" for op in grammar.operators):
        return _stub_result(instance, grammar, started)

    if grammar.name == "G1_XOR":
        path = solve_with_xor(instance.formula, c=grammar.max_c, detect_cnf_xor=True, detect_xor_max_k=grammar.xor_max_k)
    else:
        path = solve(instance.formula, c=grammar.max_c)

    artifact_paths: dict[str, str] = {}
    proof_status = "NOT_REQUESTED"
    if strict and grammar.name == "G1_XOR" and path.status == XOR_UNSAT_NATIVE and drat_trim_path is not None and out_root is not None:
        policy = grammar.proof_policy
        cert = Path(out_root) / "certs" / grammar.name / f"{instance.instance_id}.wcert"
        export_certificate_bundle(
            instance.formula,
            path,
            cert,
            original_dimacs_text=instance.formula.canonical_dimacs(),
            export_drat=True,
            export_xor_drat=True,
            drat_trim_path=drat_trim_path,
            xor_drat_max_row_width=int(policy.get("max_row_width", 10)),
            xor_drat_max_proof_clauses=int(policy.get("max_proof_clauses", 100000)),
            xor_drat_max_proof_bytes=int(policy.get("max_proof_bytes", 10_000_000)),
            xor_drat_timeout_seconds=float(policy.get("timeout_seconds", 300.0)),
            xor_elim_order=str(policy.get("xor_elim_order", "sparse-min-fill")),
        )
        artifact_paths["certificate"] = str(cert)
        if (cert / "proof.drat").exists():
            artifact_paths["proof_drat"] = str(cert / "proof.drat")
        status_path = cert / "xor_drat_status.json"
        if status_path.exists():
            proof_status = json.loads(status_path.read_text(encoding="utf-8")).get("xor_drat_status", "RECORDED")

    public_category = path.public_category
    collapse_path_found = public_category in {SAT_ASSIGNMENT_VERIFIED, UNSAT_DRAT_EXPORTED_VERIFIED, UNSAT_XOR_NATIVE_ONLY, UNSAT_NOT_EXTERNALLY_VERIFIED}
    blocked_reason = "NO_COLLAPSE_UNDER_CONFIGURED_GRAMMAR_BOUNDS" if path.status == NO_COLLAPSE else ""
    return CollapseResult(
        instance.instance_id,
        instance.family,
        grammar.name,
        path.logical_status,
        public_category,
        collapse_path_found,
        path.discovery_route,
        path.public_certification_level,
        proof_status,
        round(time.perf_counter() - started, 6),
        _detected_structures(instance.formula, grammar.xor_max_k),
        blocked_reason,
        artifact_paths,
        instance.formula.formula_hash,
        instance.formula.num_vars,
        instance.formula.num_clauses,
        [step.type for step in path.steps],
        grammar.max_c,
        instance.source,
        instance.notes,
        instance.generation_command,
    )


def _result_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row["family"]), str(row["instance_id"])


def strictness_witnesses(results: list[CollapseResult]) -> list[StrictnessWitness]:
    rows = [result.to_dict() for result in results]
    by_key_grammar = {(_result_key(row), row["grammar"]): row for row in rows}
    witnesses: list[StrictnessWitness] = []
    for key in sorted({_result_key(row) for row in rows}):
        base = by_key_grammar.get((key, "G0_BASE"))
        extended = by_key_grammar.get((key, "G1_XOR"))
        if base and extended and base["public_category"] == NO_COLLAPSE_FOUND and extended["public_category"] != NO_COLLAPSE_FOUND:
            witnesses.append(
                StrictnessWitness(
                    family=extended["family"],
                    instance=extended["instance_id"],
                    base_grammar="G0_BASE",
                    extended_grammar="G1_XOR",
                    added_operator="XOR_AFFINE",
                    base_result=base["public_category"],
                    extended_result=extended["public_category"],
                    certification_level=extended["certification_level"],
                    evidence=[{"formula_hash": extended["formula_hash"], "detected_structures": extended["detected_structures"], "proof_status": extended["proof_status"], "artifact_paths": extended["artifact_paths"]}],
                )
            )
        if base and base["family"] == "blocked-clique" and base["public_category"] == SAT_ASSIGNMENT_VERIFIED:
            witnesses.append(
                StrictnessWitness(
                    family=base["family"],
                    instance=base["instance_id"],
                    base_grammar="TREEWIDTH_ONLY_C1_DIAGNOSTIC",
                    extended_grammar="G0_BASE",
                    added_operator="BCE",
                    base_result="NO_COLLAPSE_FOUND_BY_WIDTH_SIGNAL",
                    extended_result=base["public_category"],
                    certification_level=base["certification_level"],
                    evidence=[{"formula_hash": base["formula_hash"], "step_types": base["step_types"], "scope_note": "BCE witness is a diagnostic comparison against a treewidth-only subgrammar, not a G0-vs-G1 XOR delta."}],
                )
            )
    return witnesses


def operator_delta_summary(results: list[CollapseResult]) -> list[OperatorDelta]:
    rows = [result.to_dict() for result in results]
    by_key_grammar = {(_result_key(row), row["grammar"]): row for row in rows}
    helped: set[str] = set()
    changed = external = native = no_collapse_delta = 0
    failure_modes: dict[str, int] = {}
    for key in sorted({_result_key(row) for row in rows}):
        base = by_key_grammar.get((key, "G0_BASE"))
        extended = by_key_grammar.get((key, "G1_XOR"))
        if not base or not extended:
            continue
        if base["public_category"] == extended["public_category"]:
            if extended["public_category"] == NO_COLLAPSE_FOUND:
                failure_modes[extended["family"]] = failure_modes.get(extended["family"], 0) + 1
            continue
        changed += 1
        helped.add(str(extended["family"]))
        if base["public_category"] == NO_COLLAPSE_FOUND and extended["public_category"] != NO_COLLAPSE_FOUND:
            no_collapse_delta += 1
        if extended["public_category"] == UNSAT_DRAT_EXPORTED_VERIFIED:
            external += 1
        if extended["public_category"] == UNSAT_XOR_NATIVE_ONLY:
            native += 1
    return [OperatorDelta("XOR_AFFINE", sorted(helped), changed, external, native, no_collapse_delta, failure_modes)]


def _category_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {category: 0 for category in PUBLIC_CATEGORIES}
    for row in rows:
        category = str(row.get("public_category", ERROR))
        counts[category] = counts.get(category, 0) + 1
    return counts


def per_family_summary(results: list[CollapseResult]) -> list[dict[str, Any]]:
    rows = [result.to_dict() for result in results]
    output: list[dict[str, Any]] = []
    for family in sorted({row["family"] for row in rows}):
        for grammar in sorted({row["grammar"] for row in rows if row["family"] == family}):
            group = [row for row in rows if row["family"] == family and row["grammar"] == grammar]
            output.append({"family": family, "grammar": grammar, "total": len(group), **_category_counts(group)})
    return output


def noncollapse_summary(results: list[CollapseResult]) -> dict[str, Any]:
    rows = [result.to_dict() for result in results]
    failures = [
        {"family": row["family"], "instance_id": row["instance_id"], "grammar": row["grammar"], "blocked_reason": row["blocked_reason"], "detected_structures": row["detected_structures"]}
        for row in rows
        if row["public_category"] == NO_COLLAPSE_FOUND
    ]
    return {
        "total_no_collapse": len(failures),
        "by_family": {family: sum(1 for item in failures if item["family"] == family) for family in sorted({item["family"] for item in failures})},
        "failures": failures,
    }


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def strictness_markdown(witnesses: list[StrictnessWitness]) -> str:
    lines = ["# Strictness Witnesses", "", "## Definition", "", "A strictness witness is bounded evidence that a formula family does not collapse under one configured grammar/resource bound but does collapse under an extended grammar. The evidence is not a lower bound against all algorithms.", "", "## G0_BASE vs G1_XOR Examples", ""]
    lines.extend(_markdown_table(["family", "instance", "base", "extended", "operator", "base_result", "extended_result", "certification"], [[w.family, w.instance, w.base_grammar, w.extended_grammar, w.added_operator, w.base_result, w.extended_result, w.certification_level] for w in witnesses]))
    lines.extend(["", "## Tseitin Strictness Evidence", "", "Tseitin rows in this lab are counted as strictness evidence only when G0_BASE reports NO_COLLAPSE_FOUND under the configured cap and G1_XOR records an exact-XOR collapse path.", "", "## Blocked-Clique BCE Strictness Evidence", "", "Blocked-clique evidence compares a treewidth-only diagnostic subgrammar against G0_BASE with BCE. It is not presented as a G0-vs-G1 XOR delta.", "", "## XOR-Chain Evidence", "", "The XOR-chain fixtures are exact full-CNF encodings whose affine contradiction is certificate-checkable.", "", "## Failed or Inconclusive Candidates", "", "Rows that remain NO_COLLAPSE_FOUND are preserved in noncollapse_summary.json for operator-frontier analysis.", "", "## What This Does Not Prove", "", "These witnesses do not prove P vs NP progress, do not establish a general lower bound, and do not solve SAT in general.", "", "## P vs NP Relevance", "", "The relevance is methodological: the lab studies verifier-to-witness collapse routes with replayable evidence. It makes no P vs NP claim.", ""])
    return "\n".join(lines)


def theory_report(results: list[CollapseResult], witnesses: list[StrictnessWitness], deltas: list[OperatorDelta], grammars: dict[str, CollapseGrammar]) -> str:
    rows = [result.to_dict() for result in results]
    lines = ["# Collapse Theory Lab Report", "", "## Definitions", "", "- Collapse Grammar G: a finite set of deterministic, replayable transformations and terminal tractable classes.", "- Collapse Class W(G): formulas that collapse under G within configured resource bounds.", "- Strictness Witness: bounded evidence that G fails under a configured bound while G plus an operator succeeds with certificate-checkable evidence.", "- Operator Delta: changed public outcomes between G and G plus an operator.", "", "## Grammar Profiles", ""]
    for grammar in grammars.values():
        lines.append(f"- {grammar.name}: {grammar.description}")
    lines.extend(["", "## Formula Families", ""])
    for family in sorted({row["family"] for row in rows}):
        lines.append(f"- {family}")
    lines.extend(["", "## G0 vs G1 Results", ""])
    lines.extend(_markdown_table(["family", "instance", "grammar", "category", "detected_xor", "proof_status"], [[row["family"], row["instance_id"], row["grammar"], row["public_category"], row["detected_structures"].get("detected_xor_equations", 0), row["proof_status"]] for row in rows if row["grammar"] in {"G0_BASE", "G1_XOR"}]))
    lines.extend(["", "## Strictness Witnesses", ""])
    lines.extend(_markdown_table(["family", "instance", "operator", "base_result", "extended_result"], [[w.family, w.instance, w.added_operator, w.base_result, w.extended_result] for w in witnesses]))
    lines.extend(["", "## Operator Delta Summary", ""])
    for delta in deltas:
        lines.append(f"- {delta.operator_added}: changed={delta.instances_changed}, externally_verified_delta={delta.externally_verified_delta}, native_only_delta={delta.native_only_delta}, families_helped={delta.families_helped}")
    lines.extend(["", "## What This Does Not Prove", "", "This lab does not claim P vs NP progress, general SAT solving, broad XOR extraction, CryptoMiniSat-style extraction, or lower bounds against all algorithms.", "", "## P vs NP Relevance", "", "Witnora v2.0 provides a certificate-backed experimental framework for studying when verifier instances admit deterministic collapse paths to witnesses or proofs. That is research scaffolding, not a P vs NP result.", "", "## Barriers and Limitations", "", "- Exact XOR extraction remains bounded by max_k.", "- Horn, cardinality, and backdoor operators are honest stubs unless future releases implement them.", "- NO_COLLAPSE_FOUND means no collapse under the configured grammar/resource bound.", "- External DRAT certification is counted only when exported proof evidence verifies.", ""])
    return "\n".join(lines)


def run_theory_experiment(
    *,
    grammars: Iterable[str],
    families: Iterable[str],
    out_root: str | Path,
    drat_trim_path: str | Path | None = None,
    strict: bool = False,
    prefer_official_tseitin: bool = True,
    cnfgen_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    profiles = grammar_profiles()
    selected_grammars = [profiles[name] for name in grammars]
    instances = build_family_instances(families, out_root=root, cnfgen_path=cnfgen_path, prefer_official_tseitin=prefer_official_tseitin)
    results = [run_instance(instance, grammar, out_root=root, strict=strict, drat_trim_path=drat_trim_path) for grammar in selected_grammars for instance in instances]
    witnesses = strictness_witnesses(results)
    deltas = operator_delta_summary(results)
    result_rows = [result.to_dict() for result in results]
    witness_rows = [witness.to_dict() for witness in witnesses]
    delta_rows = [delta.to_dict() for delta in deltas]
    noncollapse = noncollapse_summary(results)
    files = {
        "grammar_profiles.json": {name: grammar.to_dict() for name, grammar in profiles.items()},
        "collapse_operators.json": {name: operator.to_dict() for name, operator in collapse_operators().items()},
        "strictness_witnesses.json": {"witnesses": witness_rows},
        "operator_delta_summary.json": {"deltas": delta_rows},
        "noncollapse_summary.json": noncollapse,
        "manifest.json": {"version": THEORY_VERSION, "created_utc": datetime.now(timezone.utc).isoformat(), "grammars": list(grammars), "families": list(families), "strict": strict, "drat_trim_path": str(drat_trim_path or "")},
    }
    for name, payload in files.items():
        (root / name).write_text(stable_json(payload), encoding="utf-8", newline="\n")
    write_csv(root / "per_instance_results.csv", result_rows)
    write_csv(root / "per_family_results.csv", per_family_summary(results))
    (root / "STRICTNESS_WITNESSES.md").write_text(strictness_markdown(witnesses), encoding="utf-8", newline="\n")
    (root / "COLLAPSE_THEORY_REPORT.md").write_text(theory_report(results, witnesses, deltas, {grammar.name: grammar for grammar in selected_grammars}), encoding="utf-8", newline="\n")
    return {"out_root": str(root), "results": result_rows, "strictness_witnesses": witness_rows, "operator_delta_summary": delta_rows, "noncollapse_summary": noncollapse}


def _recommendations_for_failure(row: dict[str, Any], candidates: list[str]) -> list[dict[str, Any]]:
    structures = row.get("detected_structures", {})
    recommendations: list[dict[str, Any]] = []
    if "cardinality" in candidates and row.get("family") == "pigeonhole":
        recommendations.append({"candidate_operator": "cardinality", "reason": "pigeonhole formulas expose exactly-one / at-most-one structure not currently represented as a certified operator", "needed_for_certification": "exact cardinality extraction, witness reconstruction, and proof logging"})
    if "horn" in candidates and float(structures.get("horn_clause_ratio", 0.0)) > 0.8:
        recommendations.append({"candidate_operator": "horn", "reason": "high Horn-clause ratio suggests a Horn terminal class could be useful", "needed_for_certification": "Horn detection, deterministic Horn-SAT replay trace, and assignment reconstruction"})
    if "backdoor" in candidates:
        recommendations.append({"candidate_operator": "backdoor", "reason": "instance remains outside current grammar; a bounded backdoor diagnostic may identify small routes to existing terminal classes", "needed_for_certification": "strict cap, deterministic branching trace, and no arbitrary brute-force SAT fallback"})
    if structures.get("xor_skipped_over_max_k", 0):
        recommendations.append({"candidate_operator": "higher_arity_exact_xor_future", "reason": "clause groups exceeded the configured exact-XOR max_k; this is a diagnostic signal, not a detection claim", "needed_for_certification": "larger exact full-CNF extraction caps with proof-size controls"})
    return recommendations


def frontier_report(failures: list[dict[str, Any]], recommendations: list[dict[str, Any]]) -> str:
    lines = ["# Operator Frontier Report", "", "This report lists formulas that remain NO_COLLAPSE_FOUND under the selected base grammar and suggests candidate operators for future certified work. It does not claim those operators solve the instances.", "", "## Frontier Failures", ""]
    lines.extend(_markdown_table(["family", "instance", "grammar", "blocked_reason"], [[row["family"], row["instance_id"], row["grammar"], row["blocked_reason"]] for row in failures]))
    lines.extend(["", "## Candidate Operator Recommendations", ""])
    lines.extend(_markdown_table(["family", "instance", "candidate", "reason"], [[row["family"], row["instance_id"], item["candidate_operator"], item["reason"]] for row in failures for item in _recommendations_for_failure(row, ["horn", "cardinality", "backdoor"])]))
    lines.extend(["", "## Boundary", "", "Recommendations are planning signals. They do not prove P vs NP progress, general SAT solving, or broad extraction capability.", ""])
    return "\n".join(lines)


def run_frontier_search(
    *,
    base_grammar: str,
    candidate_operators: Iterable[str],
    families: Iterable[str],
    out_root: str | Path,
    prefer_official_tseitin: bool = False,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    result = run_theory_experiment(grammars=[base_grammar], families=families, out_root=root / "_base_run", strict=False, prefer_official_tseitin=prefer_official_tseitin)
    rows = list(result["results"])
    failures = [row for row in rows if row["public_category"] == NO_COLLAPSE_FOUND]
    candidates = list(candidate_operators)
    recommendations = [{"family": row["family"], "instance_id": row["instance_id"], "base_grammar": row["grammar"], "recommendations": _recommendations_for_failure(row, candidates)} for row in failures]
    (root / "frontier_failures.json").write_text(stable_json({"failures": failures}), encoding="utf-8", newline="\n")
    (root / "candidate_operator_recommendations.json").write_text(stable_json({"recommendations": recommendations}), encoding="utf-8", newline="\n")
    (root / "OPERATOR_FRONTIER_REPORT.md").write_text(frontier_report(failures, recommendations), encoding="utf-8", newline="\n")
    return {"out_root": str(root), "frontier_failures": failures, "candidate_operator_recommendations": recommendations}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora Collapse Theory Lab")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--grammars", nargs="+", default=["G0_BASE", "G1_XOR"])
    run_parser.add_argument("--families", nargs="+", default=["tseitin", "pigeonhole", "parity", "blocked-clique", "xor-chain", "adversarial-mixed"])
    run_parser.add_argument("--out-root", default="outputs/v2.0-collapse-theory-lab")
    run_parser.add_argument("--drat-trim")
    run_parser.add_argument("--cnfgen-path")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--no-official-tseitin", action="store_true")
    run_parser.add_argument("--zip", default="witnora-core-v2.0-collapse-theory-lab.zip")

    strict_parser = sub.add_parser("run-strictness")
    strict_parser.add_argument("--grammars", nargs="+", default=["G0_BASE", "G1_XOR"])
    strict_parser.add_argument("--families", nargs="+", default=["tseitin", "blocked-clique", "xor-chain"])
    strict_parser.add_argument("--out-root", default="outputs/v2.0-collapse-theory-lab")
    strict_parser.add_argument("--drat-trim")
    strict_parser.add_argument("--cnfgen-path")
    strict_parser.add_argument("--strict", action="store_true")
    strict_parser.add_argument("--no-official-tseitin", action="store_true")
    strict_parser.add_argument("--zip", default="witnora-core-v2.0-collapse-theory-lab.zip")

    frontier_parser = sub.add_parser("search-frontier")
    frontier_parser.add_argument("--base-grammar", default="G1_XOR")
    frontier_parser.add_argument("--candidate-operators", nargs="+", default=["horn", "cardinality", "backdoor"])
    frontier_parser.add_argument("--families", nargs="+", default=["parity", "pigeonhole", "adversarial-mixed"])
    frontier_parser.add_argument("--out-root", default="outputs/v2.0-operator-frontier")
    frontier_parser.add_argument("--zip", default="witnora-core-v2.0-operator-frontier.zip")
    args = parser.parse_args(argv)

    if args.command in {"run", "run-strictness"}:
        result = run_theory_experiment(grammars=args.grammars, families=args.families, out_root=args.out_root, drat_trim_path=args.drat_trim, strict=args.strict, cnfgen_path=args.cnfgen_path, prefer_official_tseitin=not args.no_official_tseitin)
        digest = make_zip(args.out_root, args.zip)
        print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"result_count": len(result["results"]), "witness_count": len(result["strictness_witnesses"])}}))
        return 0

    result = run_frontier_search(base_grammar=args.base_grammar, candidate_operators=args.candidate_operators, families=args.families, out_root=args.out_root)
    digest = make_zip(args.out_root, args.zip)
    print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"failure_count": len(result["frontier_failures"])}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
