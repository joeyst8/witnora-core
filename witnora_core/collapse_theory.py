"""Collapse grammar comparison and operator-frontier diagnostics.

This module is a research harness, not a new SAT solver. It composes existing
certified Witnora routes to compare bounded collapse grammars and record where
adding an operator changes an observed, certificate-checkable outcome.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
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
from .theorem_candidates import initial_theorem_candidates, theorem_candidates_markdown
from .xor import canonical_xor_cnf_clauses, detect_cnf_xor_patterns

THEORY_VERSION = "2.1"
OPERATOR_STUB_NOT_EXECUTED = "OPERATOR_STUB_NOT_EXECUTED"

WITHIN_BOUNDS = "WITHIN_BOUNDS"
EXCEEDED_WIDTH_BOUND = "EXCEEDED_WIDTH_BOUND"
EXCEEDED_TIME_BOUND = "EXCEEDED_TIME_BOUND"
EXCEEDED_PROOF_SIZE_BOUND = "EXCEEDED_PROOF_SIZE_BOUND"
EXCEEDED_SEARCH_BOUND = "EXCEEDED_SEARCH_BOUND"
OPERATOR_NOT_APPLICABLE = "OPERATOR_NOT_APPLICABLE"

OBSTRUCTION_TREEWIDTH_OVER_CAP = "TREEWIDTH_OVER_CAP"
OBSTRUCTION_XOR_ARITY_OVER_CAP = "XOR_ARITY_OVER_CAP"
OBSTRUCTION_NO_EXACT_XOR_PATTERN = "NO_EXACT_XOR_PATTERN"
OBSTRUCTION_SYMMETRY_NO_QUOTIENT = "SYMMETRY_DETECTED_NO_CERTIFIED_QUOTIENT"
OBSTRUCTION_CARDINALITY_UNSUPPORTED = "CARDINALITY_STRUCTURE_UNSUPPORTED"
OBSTRUCTION_HORN_UNSUPPORTED = "HORN_STRUCTURE_UNSUPPORTED"
OBSTRUCTION_PROOF_EXPORT_BLOWUP = "PROOF_EXPORT_BLOWUP"
OBSTRUCTION_SEARCH_BOUND_EXCEEDED = "SEARCH_BOUND_EXCEEDED"
OBSTRUCTION_OPERATOR_STUB = "OPERATOR_STUB"

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
class BoundProfile:
    name: str
    max_c: int
    xor_max_k: int
    max_runtime_seconds: float
    max_proof_clauses: int
    max_search_nodes: int
    max_operator_depth: int
    max_orbit_generators: int
    max_symmetry_group_size_estimate: int
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CollapseCost:
    path_length: int
    operator_applications: dict[str, int]
    peak_formula_size: int
    peak_clause_count: int
    peak_variable_count: int
    peak_width: int
    proof_clause_count: int
    proof_bytes: int
    runtime_seconds: float
    external_verification_runtime_seconds: float
    certificate_size_bytes: int
    search_nodes_expanded: int
    resource_bound_profile: str

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
    collapse_cost: CollapseCost
    bounded_cost_status: str
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


@dataclass(frozen=True)
class CollapseObstruction:
    instance_id: str
    family: str
    grammar: str
    obstruction_type: str
    evidence: dict[str, Any]
    suggested_operator: str
    confidence: str
    certifiable_next_step: str

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
        "SYNTACTIC_ORBIT_DIAGNOSTIC": CollapseOperator(
            "SYNTACTIC_ORBIT_DIAGNOSTIC",
            True,
            "Deterministic variable-signature orbit diagnostic. It is not full graph automorphism detection and does not certify a quotient collapse.",
            True,
            False,
            True,
            {"max_orbit_generators": 12, "max_symmetry_group_size_estimate": 100000},
        ),
        "HORN_PROTOTYPE": CollapseOperator("HORN_PROTOTYPE", False, "Horn operator placeholder.", False, False, True, stub=True),
        "CARDINALITY_PROTOTYPE": CollapseOperator("CARDINALITY_PROTOTYPE", False, "Small cardinality operator placeholder.", False, False, True, stub=True),
        "BACKDOOR_DIAGNOSTIC": CollapseOperator("BACKDOOR_DIAGNOSTIC", False, "Bounded backdoor-search diagnostic placeholder.", False, False, True, stub=True),
    }


def bound_profiles() -> dict[str, BoundProfile]:
    return {
        "B_V21_DEFAULT": BoundProfile(
            "B_V21_DEFAULT",
            max_c=2,
            xor_max_k=6,
            max_runtime_seconds=300.0,
            max_proof_clauses=100000,
            max_search_nodes=10000,
            max_operator_depth=64,
            max_orbit_generators=12,
            max_symmetry_group_size_estimate=100000,
            description="Default bounded theory-lab profile for v2.1 experiments.",
        ),
        "B_V21_SYMMETRY_DIAGNOSTIC": BoundProfile(
            "B_V21_SYMMETRY_DIAGNOSTIC",
            max_c=2,
            xor_max_k=6,
            max_runtime_seconds=120.0,
            max_proof_clauses=0,
            max_search_nodes=0,
            max_operator_depth=0,
            max_orbit_generators=12,
            max_symmetry_group_size_estimate=100000,
            description="Diagnostic-only profile for syntactic orbit evidence; no quotient collapse is certified.",
        ),
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
        "G2_SYMMETRY_PROTOTYPE": CollapseGrammar(
            "G2_SYMMETRY_PROTOTYPE",
            (*g1_ops, "SYNTACTIC_ORBIT_DIAGNOSTIC"),
            (*terminals, "XOR_AFFINE", "SYMMETRY_DIAGNOSTIC"),
            2,
            6,
            {**xor_policy, "operator_status": "DIAGNOSTIC_ONLY"},
            "G1_XOR plus deterministic syntactic orbit diagnostics. v2.1 records symmetry signals but does not certify orbit quotient collapse.",
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


def _graph_coloring_formula(vertices: int, edges: Iterable[tuple[int, int]], colors: int) -> CNFFormula:
    def var(vertex: int, color: int) -> int:
        return (vertex - 1) * colors + color

    clauses: list[list[int]] = []
    for vertex in range(1, vertices + 1):
        clauses.append([var(vertex, color) for color in range(1, colors + 1)])
        for first in range(1, colors + 1):
            for second in range(first + 1, colors + 1):
                clauses.append([-var(vertex, first), -var(vertex, second)])
    for u, v in edges:
        for color in range(1, colors + 1):
            clauses.append([-var(u, color), -var(v, color)])
    return CNFFormula.from_raw_clauses(clauses)


def _cycle_edges(vertices: int) -> list[tuple[int, int]]:
    return [(idx, idx + 1) for idx in range(1, vertices)] + [(vertices, 1)]


def _complete_edges(vertices: int) -> list[tuple[int, int]]:
    return [(u, v) for u in range(1, vertices + 1) for v in range(u + 1, vertices + 1)]


def _symmetric_toy_formula(groups: int = 4) -> CNFFormula:
    clauses: list[list[int]] = []
    variables = list(range(1, groups + 1))
    clauses.append(variables)
    for first in variables:
        for second in variables:
            if first < second:
                clauses.append([-first, -second])
    return CNFFormula.from_raw_clauses(clauses)


def _near_symmetric_toy_formula(groups: int = 4) -> CNFFormula:
    clauses = [list(clause.literals) for clause in _symmetric_toy_formula(groups).clauses]
    clauses.append([groups])
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
                    TheoryInstance("parity_7_over_cap", "parity", _xor_formula([((1, 2, 3, 4, 5, 6, 7), 0), ((1, 2, 3, 4, 5, 6, 7), 1)]), "built_in_exact_xor", "contradictory exact parity pair over the default exact-XOR cap"),
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
        elif family == "graph-coloring":
            instances.extend(
                [
                    TheoryInstance("cycle_6_3color", "graph-coloring", _graph_coloring_formula(6, _cycle_edges(6), 3), "built_in_graph_coloring", "symmetric 3-coloring encoding for a cycle graph"),
                    TheoryInstance("complete_4_3color", "graph-coloring", _graph_coloring_formula(4, _complete_edges(4), 3), "built_in_graph_coloring", "small complete graph coloring encoding with color/vertex symmetry"),
                ]
            )
        elif family == "clique":
            instances.append(
                TheoryInstance("complete_graph_independent_set_5", "clique", _graph_coloring_formula(5, _complete_edges(5), 2), "built_in_symmetric_clique_proxy", "small symmetric graph formula used as clique/independent-set battlefield proxy")
            )
        elif family == "symmetric-toy":
            instances.append(
                TheoryInstance("symmetric_exactly_one_4", "symmetric-toy", _symmetric_toy_formula(4), "built_in_symmetric_toy", "obvious interchangeable variables for orbit diagnostics")
            )
        elif family == "adversarial-near-symmetry":
            instances.append(
                TheoryInstance("near_symmetric_exactly_one_4", "adversarial-near-symmetry", _near_symmetric_toy_formula(4), "built_in_near_symmetric_toy", "one variable is intentionally distinguished; orbit diagnostic must not merge it")
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


def _factorial_cap(size: int, cap: int) -> int:
    value = 1
    for item in range(2, size + 1):
        value *= item
        if value > cap:
            return cap
    return value


def syntactic_orbit_diagnostic(formula: CNFFormula, *, max_group_size_estimate: int = 100000) -> dict[str, Any]:
    """Group variables by deterministic syntactic signatures.

    This is a diagnostic signal only. Equal signatures are candidate orbits, not
    a certified automorphism group and not a quotient-collapse proof.
    """

    signatures: dict[int, tuple[Any, ...]] = {}
    clause_memberships: dict[int, list[tuple[int, int, tuple[int, ...]]]] = defaultdict(list)
    for clause in formula.clauses:
        abs_vars = tuple(sorted(abs(lit) for lit in clause.literals))
        for lit in clause.literals:
            sign = 1 if lit > 0 else -1
            clause_memberships[abs(lit)].append((sign, len(clause), abs_vars))

    for variable in range(1, formula.num_vars + 1):
        memberships = clause_memberships.get(variable, [])
        pos_count = sum(1 for sign, _, _ in memberships if sign > 0)
        neg_count = sum(1 for sign, _, _ in memberships if sign < 0)
        signed_widths = Counter((sign, width) for sign, width, _ in memberships)
        co_occurrence = Counter()
        for _, _, abs_vars in memberships:
            for other in abs_vars:
                if other != variable:
                    co_occurrence[other] += 1
        co_degree_histogram = Counter(co_occurrence.values())
        signatures[variable] = (
            pos_count,
            neg_count,
            tuple(sorted(signed_widths.items())),
            tuple(sorted(co_degree_histogram.items())),
            sum(co_occurrence.values()),
        )

    groups: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    for variable, signature in signatures.items():
        groups[signature].append(variable)
    orbit_groups = [sorted(group) for group in groups.values()]
    orbit_groups.sort(key=lambda group: (-len(group), group))
    nontrivial = [group for group in orbit_groups if len(group) > 1]
    estimate = 1
    for group in nontrivial:
        estimate *= _factorial_cap(len(group), max_group_size_estimate)
        if estimate > max_group_size_estimate:
            estimate = max_group_size_estimate
            break
    signature_hashes = []
    for group in nontrivial[:12]:
        signature = signatures[group[0]]
        signature_hashes.append(
            {
                "variables": group,
                "signature_hash": hashlib.sha256(stable_json(signature).encode("utf-8")).hexdigest().upper()[:16],
            }
        )
    return {
        "diagnostic": "SYNTACTIC_ORBIT_DIAGNOSTIC",
        "is_full_automorphism_detection": False,
        "certified_quotient_collapse": False,
        "orbit_count": len(orbit_groups),
        "nontrivial_orbit_count": len(nontrivial),
        "largest_orbit_size": max((len(group) for group in orbit_groups), default=0),
        "candidate_orbits": signature_hashes,
        "symmetry_score": round(sum(len(group) for group in nontrivial) / max(1, formula.num_vars), 6),
        "symmetry_group_size_estimate_capped": estimate,
        "scope": "diagnostic candidate orbit grouping; no certified quotient transformation",
    }


def _cardinality_signal(formula: CNFFormula) -> dict[str, Any]:
    positive_wide = sum(1 for clause in formula.clauses if len(clause) > 1 and all(lit > 0 for lit in clause.literals))
    negative_binary = sum(1 for clause in formula.clauses if len(clause) == 2 and all(lit < 0 for lit in clause.literals))
    return {
        "positive_wide_clause_count": positive_wide,
        "negative_binary_clause_count": negative_binary,
        "at_most_one_signal": negative_binary > 0,
        "exactly_one_like_signal": positive_wide > 0 and negative_binary > 0,
    }


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
    orbit = syntactic_orbit_diagnostic(formula)
    return {
        "detected_xor_equations": len(detected.equations) if detected is not None else 0,
        "max_detected_xor_arity": max((len(eq.variables) for eq in detected.equations), default=0)
        if detected is not None
        else 0,
        "xor_skipped_over_max_k": len(skipped),
        "horn_clause_ratio": round(horn_clauses / formula.num_clauses, 6) if formula.num_clauses else 0.0,
        "binary_negative_clause_count": binary_negative,
        "max_clause_width": max((len(clause) for clause in formula.clauses), default=0),
        "cardinality_signal": _cardinality_signal(formula),
        "symmetry_orbit": orbit,
    }


def _directory_size(path: str | Path) -> int:
    root = Path(path)
    if not root.exists():
        return 0
    if root.is_file():
        return root.stat().st_size
    return sum(item.stat().st_size for item in root.rglob("*") if item.is_file())


def _proof_stats(artifact_paths: dict[str, str]) -> tuple[int, int, float]:
    proof = artifact_paths.get("proof_drat")
    if not proof or not Path(proof).exists():
        return 0, 0, 0.0
    proof_path = Path(proof)
    try:
        clause_count = sum(1 for line in proof_path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
    except OSError:
        clause_count = 0
    runtime = 0.0
    status_path = proof_path.parent / "xor_drat_status.json"
    if status_path.exists():
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
            runtime = float(status.get("drat_trim_runtime_seconds") or 0.0)
        except (OSError, ValueError, TypeError):
            runtime = 0.0
    return clause_count, proof_path.stat().st_size, runtime


def _collapse_cost(
    formula: CNFFormula,
    *,
    runtime: float,
    step_types: list[str],
    artifact_paths: dict[str, str],
    resource_bound_profile: str = "B_V21_DEFAULT",
) -> CollapseCost:
    proof_clause_count, proof_bytes, external_runtime = _proof_stats(artifact_paths)
    operator_counts = dict(sorted(Counter(step_types).items()))
    return CollapseCost(
        path_length=len(step_types),
        operator_applications=operator_counts,
        peak_formula_size=formula.num_clauses + formula.num_vars,
        peak_clause_count=formula.num_clauses,
        peak_variable_count=formula.num_vars,
        peak_width=max((len(clause) for clause in formula.clauses), default=0),
        proof_clause_count=proof_clause_count,
        proof_bytes=proof_bytes,
        runtime_seconds=runtime,
        external_verification_runtime_seconds=external_runtime,
        certificate_size_bytes=_directory_size(artifact_paths.get("certificate", "")) if artifact_paths.get("certificate") else 0,
        search_nodes_expanded=0,
        resource_bound_profile=resource_bound_profile,
    )


def _bounded_cost_status(cost: CollapseCost, grammar: CollapseGrammar, public_category: str) -> str:
    profile = bound_profiles()["B_V21_DEFAULT"]
    if public_category == OPERATOR_STUB_NOT_EXECUTED:
        return OPERATOR_STUB_NOT_EXECUTED
    if cost.runtime_seconds > profile.max_runtime_seconds:
        return EXCEEDED_TIME_BOUND
    if cost.proof_clause_count and cost.proof_clause_count > profile.max_proof_clauses:
        return EXCEEDED_PROOF_SIZE_BOUND
    if cost.search_nodes_expanded > profile.max_search_nodes:
        return EXCEEDED_SEARCH_BOUND
    if public_category == NO_COLLAPSE_FOUND and grammar.name == "G0_BASE" and cost.peak_width > grammar.max_c:
        return EXCEEDED_WIDTH_BOUND
    if public_category == NO_COLLAPSE_FOUND:
        return OPERATOR_NOT_APPLICABLE
    return WITHIN_BOUNDS


def _stub_result(instance: TheoryInstance, grammar: CollapseGrammar, started: float) -> CollapseResult:
    runtime = round(time.perf_counter() - started, 6)
    cost = _collapse_cost(instance.formula, runtime=runtime, step_types=[], artifact_paths={})
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
        runtime,
        _detected_structures(instance.formula, grammar.xor_max_k),
        "OPERATOR_STUB_NOT_EXECUTED",
        {},
        cost,
        OPERATOR_STUB_NOT_EXECUTED,
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

    if grammar.name in {"G1_XOR", "G2_SYMMETRY_PROTOTYPE"}:
        path = solve_with_xor(instance.formula, c=grammar.max_c, detect_cnf_xor=True, detect_xor_max_k=grammar.xor_max_k)
    else:
        path = solve(instance.formula, c=grammar.max_c)

    artifact_paths: dict[str, str] = {}
    proof_status = "NOT_REQUESTED"
    if strict and grammar.name in {"G1_XOR", "G2_SYMMETRY_PROTOTYPE"} and path.status == XOR_UNSAT_NATIVE and drat_trim_path is not None and out_root is not None:
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
    runtime = round(time.perf_counter() - started, 6)
    step_types = [step.type for step in path.steps]
    cost = _collapse_cost(instance.formula, runtime=runtime, step_types=step_types, artifact_paths=artifact_paths)
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
        runtime,
        _detected_structures(instance.formula, grammar.xor_max_k),
        blocked_reason,
        artifact_paths,
        cost,
        _bounded_cost_status(cost, grammar, public_category),
        instance.formula.formula_hash,
        instance.formula.num_vars,
        instance.formula.num_clauses,
        step_types,
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


def obstruction_records(results: list[CollapseResult]) -> list[CollapseObstruction]:
    records: list[CollapseObstruction] = []
    for result in results:
        row = result.to_dict()
        structures = row.get("detected_structures", {})
        orbit = structures.get("symmetry_orbit", {})
        cardinality = structures.get("cardinality_signal", {})
        cost = row.get("collapse_cost", {})
        is_noncollapse = row["public_category"] == NO_COLLAPSE_FOUND
        is_stub = row["public_category"] == OPERATOR_STUB_NOT_EXECUTED
        if is_stub:
            records.append(
                CollapseObstruction(
                    row["instance_id"],
                    row["family"],
                    row["grammar"],
                    OBSTRUCTION_OPERATOR_STUB,
                    {"public_category": row["public_category"], "operators_not_executed": row["step_types"]},
                    "IMPLEMENT_OPERATOR_WITH_CERTIFICATE",
                    "HIGH",
                    "Implement the operator only with replayable trace and certificate semantics.",
                )
            )
            continue
        if not is_noncollapse:
            continue
        if structures.get("xor_skipped_over_max_k", 0):
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_XOR_ARITY_OVER_CAP, structures, "HIGHER_ARITY_XOR", "MEDIUM", "Raise exact-XOR cap only with proof-size controls and exact full-encoding checks.")
            )
        if row["family"] in {"pigeonhole", "graph-coloring", "clique", "symmetric-toy"} and orbit.get("largest_orbit_size", 0) >= 3:
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_SYMMETRY_NO_QUOTIENT, orbit, "SYMMETRY_ORBIT", "HIGH", "Define a sound quotient or symmetry-breaking rule with witness/proof reconstruction.")
            )
        if row["family"] == "pigeonhole" and cardinality.get("exactly_one_like_signal"):
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_CARDINALITY_UNSUPPORTED, cardinality, "CARDINALITY_PB", "HIGH", "Implement exact at-most-one/exactly-one detection with reconstruction and proof boundaries.")
            )
        if float(structures.get("horn_clause_ratio", 0.0)) > 0.8:
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_HORN_UNSUPPORTED, {"horn_clause_ratio": structures.get("horn_clause_ratio")}, "HORN_RENAMABLE", "MEDIUM", "Implement Horn or renamable-Horn detection with deterministic replay.")
            )
        if int(cost.get("peak_width", 0)) > int(row.get("c_parameter", 0)):
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_TREEWIDTH_OVER_CAP, {"peak_width": cost.get("peak_width"), "cap": row.get("c_parameter")}, "GRAPH_DECOMPOSITION", "MEDIUM", "Investigate decomposition operators beyond the current width cap.")
            )
        if not any(record.instance_id == row["instance_id"] and record.grammar == row["grammar"] for record in records):
            records.append(
                CollapseObstruction(row["instance_id"], row["family"], row["grammar"], OBSTRUCTION_NO_EXACT_XOR_PATTERN, structures, "OPERATOR_DISCOVERY_REQUIRED", "LOW", "Collect more structural signatures before proposing a certified operator.")
            )
    return records


def obstruction_report(records: list[CollapseObstruction]) -> str:
    lines = [
        "# Collapse Obstruction Report",
        "",
        "Obstructions are bounded diagnostic records. They explain why a configured grammar did not find a collapse route; they are not hardness claims.",
        "",
    ]
    rows = [[r.family, r.instance_id, r.grammar, r.obstruction_type, r.suggested_operator, r.confidence] for r in records]
    lines.extend(_markdown_table(["family", "instance", "grammar", "obstruction", "suggested_operator", "confidence"], rows))
    lines.extend(["", "## Boundary", "", "A recorded obstruction does not prove that all algorithms fail. It only guides the next certificate-backed operator experiment.", ""])
    return "\n".join(lines)


def _operator_name_from_obstruction(obstruction: CollapseObstruction) -> str:
    mapping = {
        OBSTRUCTION_SYMMETRY_NO_QUOTIENT: "SYMMETRY_ORBIT",
        OBSTRUCTION_XOR_ARITY_OVER_CAP: "HIGHER_ARITY_XOR",
        OBSTRUCTION_CARDINALITY_UNSUPPORTED: "CARDINALITY_PB",
        OBSTRUCTION_HORN_UNSUPPORTED: "HORN_RENAMABLE",
        OBSTRUCTION_TREEWIDTH_OVER_CAP: "GRAPH_DECOMPOSITION",
        OBSTRUCTION_SEARCH_BOUND_EXCEEDED: "BACKDOOR_TO_TRACTABLE",
    }
    return mapping.get(obstruction.obstruction_type, obstruction.suggested_operator)


def rank_candidate_operators(records: list[CollapseObstruction]) -> list[dict[str, Any]]:
    scores: dict[str, dict[str, Any]] = {}
    weights = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    for record in records:
        candidate = _operator_name_from_obstruction(record)
        item = scores.setdefault(candidate, {"candidate_operator": candidate, "score": 0, "evidence_count": 0, "families": set(), "obstruction_types": Counter()})
        item["score"] += weights.get(record.confidence, 1)
        item["evidence_count"] += 1
        item["families"].add(record.family)
        item["obstruction_types"][record.obstruction_type] += 1
    rankings = []
    for item in scores.values():
        rankings.append(
            {
                "candidate_operator": item["candidate_operator"],
                "score": item["score"],
                "evidence_count": item["evidence_count"],
                "families": sorted(item["families"]),
                "obstruction_types": dict(sorted(item["obstruction_types"].items())),
                "claim_boundary": "evidence-based heuristic ranking, not a theorem",
            }
        )
    rankings.sort(key=lambda row: (-row["score"], row["candidate_operator"]))
    return rankings


def operator_discovery_report(failures: list[dict[str, Any]], records: list[CollapseObstruction], rankings: list[dict[str, Any]]) -> str:
    lines = [
        "# Operator Discovery Report",
        "",
        "This report ranks candidate collapse operators from bounded obstruction evidence. Ranking is heuristic, not a theorem, and does not prove a theorem.",
        "",
        "## Non-Collapse Inputs",
        "",
    ]
    lines.extend(_markdown_table(["family", "instance", "grammar", "category"], [[row["family"], row["instance_id"], row["grammar"], row["public_category"]] for row in failures]))
    lines.extend(["", "## Candidate Operator Rankings", ""])
    lines.extend(_markdown_table(["rank", "candidate", "score", "families", "obstructions"], [[idx + 1, row["candidate_operator"], row["score"], ", ".join(row["families"]), ", ".join(row["obstruction_types"].keys())] for idx, row in enumerate(rankings)]))
    lines.extend(["", "## What This Does Not Prove", "", "The discovery engine does not prove P vs NP progress, does not establish general SAT capability, and does not certify that a recommended operator will collapse the listed families.", ""])
    return "\n".join(lines)


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
    lines.extend(["", "## Tseitin Strictness Evidence", "", "Tseitin rows in this lab are counted as strictness evidence only when G0_BASE reports NO_COLLAPSE_FOUND under the configured cap and G1_XOR records an exact-XOR collapse path.", "", "## Blocked-Clique BCE Strictness Evidence", "", "Blocked-clique evidence compares a treewidth-only diagnostic subgrammar against G0_BASE with BCE. It is not presented as a G0-vs-G1 XOR delta.", "", "## XOR-Chain Evidence", "", "The XOR-chain fixtures are exact full-CNF encodings whose affine contradiction is certificate-checkable.", "", "## Failed or Inconclusive Candidates", "", "Rows that remain NO_COLLAPSE_FOUND are preserved in noncollapse_summary.json for operator-frontier analysis.", "", "## What This Does Not Prove", "", "These witnesses do not prove P vs NP progress, do not establish a lower-bound theorem, and do not establish general SAT capability.", "", "## P vs NP Relevance", "", "The relevance is methodological: the lab studies verifier-to-witness collapse routes with replayable evidence. It makes no P vs NP claim.", ""])
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
    lines.extend(["", "## What This Does Not Prove", "", "This lab does not claim P vs NP progress, general SAT capability, broad XOR extraction, CryptoMiniSat-style extraction, or lower-bound theorems against all algorithms.", "", "## P vs NP Relevance", "", "Witnora v2.0 provides a certificate-backed experimental framework for studying when verifier instances admit deterministic collapse paths to witnesses or proofs. That is research scaffolding, not a P vs NP result.", "", "## Barriers and Limitations", "", "- Exact XOR extraction remains bounded by max_k.", "- Horn, cardinality, and backdoor operators are honest stubs unless future releases implement them.", "- NO_COLLAPSE_FOUND means no collapse under the configured grammar/resource bound.", "- External DRAT certification is counted only when exported proof evidence verifies.", ""])
    return "\n".join(lines)


def collapse_cost_summary(results: list[CollapseResult]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        data = result.to_dict()
        cost = data["collapse_cost"]
        rows.append(
            {
                "family": data["family"],
                "instance_id": data["instance_id"],
                "grammar": data["grammar"],
                "public_category": data["public_category"],
                "bounded_cost_status": data["bounded_cost_status"],
                "path_length": cost["path_length"],
                "peak_clause_count": cost["peak_clause_count"],
                "peak_variable_count": cost["peak_variable_count"],
                "peak_width": cost["peak_width"],
                "proof_clause_count": cost["proof_clause_count"],
                "proof_bytes": cost["proof_bytes"],
                "runtime_seconds": cost["runtime_seconds"],
                "certificate_size_bytes": cost["certificate_size_bytes"],
            }
        )
    return rows


def symmetry_orbit_diagnostics(results: list[CollapseResult]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        data = result.to_dict()
        orbit = data["detected_structures"].get("symmetry_orbit", {})
        if orbit.get("largest_orbit_size", 0) > 1:
            rows.append(
                {
                    "family": data["family"],
                    "instance_id": data["instance_id"],
                    "grammar": data["grammar"],
                    "public_category": data["public_category"],
                    "largest_orbit_size": orbit.get("largest_orbit_size", 0),
                    "nontrivial_orbit_count": orbit.get("nontrivial_orbit_count", 0),
                    "symmetry_score": orbit.get("symmetry_score", 0.0),
                    "certified_quotient_collapse": orbit.get("certified_quotient_collapse", False),
                    "candidate_orbits": orbit.get("candidate_orbits", []),
                }
            )
    return rows


def theorem_candidates_outputs(out_root: str | Path) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    candidates = initial_theorem_candidates()
    payload = {"theorem_candidates": [candidate.to_dict() for candidate in candidates]}
    (root / "theorem_candidates.json").write_text(stable_json(payload), encoding="utf-8", newline="\n")
    (root / "THEOREM_CANDIDATES.md").write_text(theorem_candidates_markdown(candidates), encoding="utf-8", newline="\n")
    return payload


def collapse_theory_frontier_report(
    *,
    results: list[CollapseResult],
    witnesses: list[StrictnessWitness],
    records: list[CollapseObstruction],
    rankings: list[dict[str, Any]],
) -> str:
    rows = [result.to_dict() for result in results]
    symmetry_rows = symmetry_orbit_diagnostics(results)
    lines = [
        "# Collapse Theory Frontier Report",
        "",
        "## Executive Summary",
        "",
        "v2.1 extends the collapse lab with bounded cost accounting, theorem-candidate records, obstruction records, syntactic orbit diagnostics, and operator-discovery rankings. Symmetry is diagnostic-only in this release unless an already-existing grammar route provides the certified result.",
        "",
        "## Bound Profile Definition",
        "",
    ]
    for profile in bound_profiles().values():
        lines.append(f"- `{profile.name}`: max_c={profile.max_c}, xor_max_k={profile.xor_max_k}, max_runtime_seconds={profile.max_runtime_seconds}, max_orbit_generators={profile.max_orbit_generators}")
    lines.extend(
        [
            "",
            "## W_B(G) Bounded Collapse Class",
            "",
            "`W_B(G)` is the set of formulas that collapse under grammar `G` within bound profile `B` and emit a valid certificate/proof when required. Current non-collapse is bounded non-collapse under configured grammar/resource bounds, not a proof of hardness.",
            "",
            "## Collapse Cost Model",
            "",
        ]
    )
    lines.extend(_markdown_table(["family", "instance", "grammar", "category", "bounded_status", "peak_width"], [[row["family"], row["instance_id"], row["grammar"], row["public_category"], row["bounded_cost_status"], row["collapse_cost"]["peak_width"]] for row in rows[:24]]))
    lines.extend(["", "## Strictness Witnesses Carried from v2.0", ""])
    lines.extend(_markdown_table(["family", "instance", "operator", "base_result", "extended_result"], [[w.family, w.instance, w.added_operator, w.base_result, w.extended_result] for w in witnesses]))
    lines.extend(["", "## New Obstruction Records", ""])
    lines.extend(_markdown_table(["family", "instance", "obstruction", "suggested_operator", "confidence"], [[r.family, r.instance_id, r.obstruction_type, r.suggested_operator, r.confidence] for r in records[:32]]))
    lines.extend(["", "## Symmetry/Orbit Diagnostics", ""])
    lines.extend(_markdown_table(["family", "instance", "largest_orbit", "score", "certified_quotient"], [[row["family"], row["instance_id"], row["largest_orbit_size"], row["symmetry_score"], row["certified_quotient_collapse"]] for row in symmetry_rows[:24]]))
    lines.extend(["", "## Pigeonhole Battlefield Analysis", "", "Pigeonhole rows expose large syntactic candidate orbits and cardinality-like structure. v2.1 records this as evidence for future `SYMMETRY_ORBIT` and `CARDINALITY_PB` operators; it does not claim symmetry has collapsed pigeonhole.", "", "## Graph-Coloring Battlefield Analysis", "", "Small graph-coloring encodings show repeated color/vertex signatures. The current diagnostic records orbit signals only; no quotient or symmetry-breaking certificate is claimed.", "", "## Operator Discovery Rankings", ""])
    lines.extend(_markdown_table(["rank", "candidate", "score", "families"], [[idx + 1, row["candidate_operator"], row["score"], ", ".join(row["families"])] for idx, row in enumerate(rankings)]))
    lines.extend(["", "## Theorem Candidates", "", "The theorem-candidate registry labels current statements as conjectures or empirical evidence and lists proof obligations before any theorem status could be claimed.", "", "## What This Does Not Prove", "", "This release does not claim P vs NP progress, general SAT capability, broad XOR extraction, full automorphism detection, a finished operator hierarchy, or lower-bound theorems against all algorithms.", "", "## Route to P vs NP: Bold but Clearly Conjectural", "", "The research program is to discover deterministic, certificate-checkable operators that turn verifier obstructions into witnesses or proofs. The route is conjectural and evidence-driven, not a claimed complexity-theory result.", "", "## Next Leap Recommendation", "", "The strongest next operator target is `SYMMETRY_ORBIT`, followed closely by `CARDINALITY_PB` for pigeonhole-style structure and `HIGHER_ARITY_XOR` for parity-over-cap rows.", ""])
    return "\n".join(lines)


def run_collapse_theory_frontier(
    *,
    grammars: Iterable[str],
    families: Iterable[str],
    out_root: str | Path,
    drat_trim_path: str | Path | None = None,
    strict: bool = False,
    prefer_official_tseitin: bool = False,
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
    records = obstruction_records(results)
    rankings = rank_candidate_operators(records)
    candidates = initial_theorem_candidates()
    result_rows = [result.to_dict() for result in results]
    files = {
        "bound_profiles.json": {name: profile.to_dict() for name, profile in bound_profiles().items()},
        "grammar_profiles_v21.json": {name: grammar.to_dict() for name, grammar in profiles.items()},
        "strictness_witnesses_v21.json": {"witnesses": [witness.to_dict() for witness in witnesses]},
        "obstruction_records.json": {"obstructions": [record.to_dict() for record in records]},
        "theorem_candidates.json": {"theorem_candidates": [candidate.to_dict() for candidate in candidates]},
        "symmetry_orbit_diagnostics.json": {"diagnostics": symmetry_orbit_diagnostics(results)},
        "operator_discovery_results.json": {"noncollapse_results": [row for row in result_rows if row["public_category"] == NO_COLLAPSE_FOUND], "obstruction_count": len(records)},
        "candidate_operator_rankings.json": {"rankings": rankings},
        "manifest.json": {"version": THEORY_VERSION, "created_utc": datetime.now(timezone.utc).isoformat(), "grammars": list(grammars), "families": list(families), "strict": strict},
    }
    for name, payload in files.items():
        (root / name).write_text(stable_json(payload), encoding="utf-8", newline="\n")
    write_csv(root / "per_instance_results.csv", result_rows)
    write_csv(root / "collapse_cost_summary.csv", collapse_cost_summary(results))
    (root / "COLLAPSE_THEORY_FRONTIER_REPORT.md").write_text(collapse_theory_frontier_report(results=results, witnesses=witnesses, records=records, rankings=rankings), encoding="utf-8", newline="\n")
    return {
        "out_root": str(root),
        "results": result_rows,
        "strictness_witnesses": [witness.to_dict() for witness in witnesses],
        "obstruction_records": [record.to_dict() for record in records],
        "candidate_operator_rankings": rankings,
        "symmetry_orbit_diagnostics": symmetry_orbit_diagnostics(results),
    }


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
    lines.extend(["", "## Boundary", "", "Recommendations are planning signals. They do not prove P vs NP progress, general SAT capability, or broad extraction capability.", ""])
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


def run_operator_discovery(
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
    profiles = grammar_profiles()
    grammar = profiles[base_grammar]
    instances = build_family_instances(families, out_root=root, prefer_official_tseitin=prefer_official_tseitin)
    results = [run_instance(instance, grammar, out_root=root, strict=False) for instance in instances]
    rows = [result.to_dict() for result in results]
    failures = [row for row in rows if row["public_category"] == NO_COLLAPSE_FOUND]
    records = obstruction_records(results)
    candidates = set(candidate_operators)
    filtered = [
        record
        for record in records
        if (
            ("symmetry" in candidates and record.suggested_operator == "SYMMETRY_ORBIT")
            or ("cardinality" in candidates and record.suggested_operator == "CARDINALITY_PB")
            or ("horn" in candidates and record.suggested_operator == "HORN_RENAMABLE")
            or ("backdoor" in candidates and record.suggested_operator == "BACKDOOR_TO_TRACTABLE")
            or ("xor" in candidates and record.suggested_operator == "HIGHER_ARITY_XOR")
            or ("graph" in candidates and record.suggested_operator == "GRAPH_DECOMPOSITION")
            or not candidates
        )
    ]
    if not filtered:
        filtered = records
    rankings = rank_candidate_operators(filtered)
    payloads = {
        "operator_discovery_results.json": {
            "base_grammar": base_grammar,
            "families": list(families),
            "noncollapse_results": failures,
            "obstruction_records": [record.to_dict() for record in filtered],
            "claim_boundary": "evidence-based heuristic ranking, not a theorem",
        },
        "candidate_operator_rankings.json": {"rankings": rankings},
    }
    for name, payload in payloads.items():
        (root / name).write_text(stable_json(payload), encoding="utf-8", newline="\n")
    (root / "OPERATOR_DISCOVERY_REPORT.md").write_text(operator_discovery_report(failures, filtered, rankings), encoding="utf-8", newline="\n")
    return {"out_root": str(root), "operator_discovery_results": payloads["operator_discovery_results.json"], "candidate_operator_rankings": rankings}


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

    discover_parser = sub.add_parser("discover-operators")
    discover_parser.add_argument("--base-grammar", default="G1_XOR")
    discover_parser.add_argument("--candidate-operators", nargs="+", default=["symmetry", "cardinality", "xor", "horn", "backdoor", "graph"])
    discover_parser.add_argument("--families", nargs="+", default=["pigeonhole", "parity", "graph-coloring", "clique", "adversarial-mixed"])
    discover_parser.add_argument("--out-root", default="outputs/v2.1-operator-discovery")
    discover_parser.add_argument("--zip", default="")

    frontier_lab_parser = sub.add_parser("run-frontier-lab")
    frontier_lab_parser.add_argument("--grammars", nargs="+", default=["G0_BASE", "G1_XOR", "G2_SYMMETRY_PROTOTYPE"])
    frontier_lab_parser.add_argument("--families", nargs="+", default=["tseitin", "pigeonhole", "parity", "blocked-clique", "xor-chain", "adversarial-mixed", "graph-coloring", "clique", "symmetric-toy", "adversarial-near-symmetry"])
    frontier_lab_parser.add_argument("--out-root", default="outputs/v2.1-collapse-theory-frontier")
    frontier_lab_parser.add_argument("--drat-trim")
    frontier_lab_parser.add_argument("--cnfgen-path")
    frontier_lab_parser.add_argument("--strict", action="store_true")
    frontier_lab_parser.add_argument("--official-tseitin", action="store_true")
    frontier_lab_parser.add_argument("--zip", default="witnora-core-v2.1-collapse-theory-frontier.zip")
    args = parser.parse_args(argv)

    if args.command in {"run", "run-strictness"}:
        result = run_theory_experiment(grammars=args.grammars, families=args.families, out_root=args.out_root, drat_trim_path=args.drat_trim, strict=args.strict, cnfgen_path=args.cnfgen_path, prefer_official_tseitin=not args.no_official_tseitin)
        digest = make_zip(args.out_root, args.zip)
        print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"result_count": len(result["results"]), "witness_count": len(result["strictness_witnesses"])}}))
        return 0

    if args.command == "search-frontier":
        result = run_frontier_search(base_grammar=args.base_grammar, candidate_operators=args.candidate_operators, families=args.families, out_root=args.out_root)
        digest = make_zip(args.out_root, args.zip)
        print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"failure_count": len(result["frontier_failures"])}}))
        return 0

    if args.command == "discover-operators":
        result = run_operator_discovery(base_grammar=args.base_grammar, candidate_operators=args.candidate_operators, families=args.families, out_root=args.out_root)
        digest = make_zip(args.out_root, args.zip) if args.zip else ""
        print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"candidate_count": len(result["candidate_operator_rankings"])}}))
        return 0

    result = run_collapse_theory_frontier(grammars=args.grammars, families=args.families, out_root=args.out_root, drat_trim_path=args.drat_trim, strict=args.strict, cnfgen_path=args.cnfgen_path, prefer_official_tseitin=args.official_tseitin)
    digest = make_zip(args.out_root, args.zip)
    print(stable_json({"out_root": args.out_root, "zip": args.zip, "zip_sha256": digest, "summary": {"result_count": len(result["results"]), "obstruction_count": len(result["obstruction_records"]), "candidate_count": len(result["candidate_operator_rankings"])}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
