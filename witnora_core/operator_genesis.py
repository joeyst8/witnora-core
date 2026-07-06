"""Operator Genesis Engine for collapse-theory research.

This module proposes candidate collapse-operator schemas from bounded
obstruction fingerprints. It does not implement those operators and it does
not claim that any generated candidate solves a formula.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
from itertools import combinations
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, Clause
from .dimacs import load_dimacs

GENESIS_VERSION = "2.5"

SYMMETRY_HEAVY = "SYMMETRY_HEAVY"
COUNTING_DEFICIT = "COUNTING_DEFICIT"
AFFINE_HIDDEN = "AFFINE_HIDDEN"
HIGH_ARITY_AFFINE = "HIGH_ARITY_AFFINE"
HIGH_LOCAL_OVERLAP = "HIGH_LOCAL_OVERLAP"
REPEATED_PROOF_MOTIF = "REPEATED_PROOF_MOTIF"
MODULAR_CONSTRAINT_SIGNAL = "MODULAR_CONSTRAINT_SIGNAL"
GRAPH_SEPARATOR_OBSTRUCTION = "GRAPH_SEPARATOR_OBSTRUCTION"
CAPACITY_FLOW_OBSTRUCTION = "CAPACITY_FLOW_OBSTRUCTION"
FIBER_ORBIT_COMPRESSION = "FIBER_ORBIT_COMPRESSION"
PROJECTION_LIFT_SIGNAL = "PROJECTION_LIFT_SIGNAL"
CARDINALITY_INCOMPLETE = "CARDINALITY_INCOMPLETE"
TREEWIDTH_OVER_CAP = "TREEWIDTH_OVER_CAP"
PROOF_EXPORT_BLOWUP = "PROOF_EXPORT_BLOWUP"
NO_CONFIDENT_FINGERPRINT = "NO_CONFIDENT_FINGERPRINT"
UNKNOWN_FINGERPRINT_PATTERN_FORBIDDEN = "UNKNOWN_FINGERPRINT_PATTERN_FORBIDDEN"

GENERATED_CANDIDATE = "GENERATED_CANDIDATE"
PROMOTION_ELIGIBLE = "PROMOTION_ELIGIBLE"
PROTOTYPE_PLANNED = "PROTOTYPE_PLANNED"
REJECTED_UNSAFE = "REJECTED_UNSAFE"
REJECTED_NO_CERTIFICATE_SKETCH = "REJECTED_NO_CERTIFICATE_SKETCH"
REJECTED_NO_TEST_FAMILY = "REJECTED_NO_TEST_FAMILY"

SEEDED_FROM_KNOWN_PATTERN = "SEEDED_FROM_KNOWN_PATTERN"
COMPOSED_FROM_MULTIPLE_FINGERPRINTS = "COMPOSED_FROM_MULTIPLE_FINGERPRINTS"
ABSTRACTION_FROM_PRIOR_OPERATOR = "ABSTRACTION_FROM_PRIOR_OPERATOR"
NOVEL_SCHEMA_HYPOTHESIS = "NOVEL_SCHEMA_HYPOTHESIS"

SAT_WITNESS_RECONSTRUCTION = "SAT_WITNESS_RECONSTRUCTION"
UNSAT_NATIVE_CERTIFICATE = "UNSAT_NATIVE_CERTIFICATE"
DRAT_BRIDGE = "DRAT_BRIDGE"
EQUI_SAT_PRESERVATION = "EQUI_SAT_PRESERVATION"
COUNTING_SOUNDNESS = "COUNTING_SOUNDNESS"
ORBIT_ACTION_VERIFICATION = "ORBIT_ACTION_VERIFICATION"
PROJECTION_LIFT_VERIFICATION = "PROJECTION_LIFT_VERIFICATION"
MODULAR_ARITHMETIC_TRACE = "MODULAR_ARITHMETIC_TRACE"
GRAPH_DECOMPOSITION_TRACE = "GRAPH_DECOMPOSITION_TRACE"
LEMMA_DERIVATION_TRACE = "LEMMA_DERIVATION_TRACE"

SKETCH_ONLY = "SKETCH_ONLY"
CHECKER_NOT_IMPLEMENTED = "CHECKER_NOT_IMPLEMENTED"
CHECKER_PLANNED = "CHECKER_PLANNED"
CHECKER_AVAILABLE = "CHECKER_AVAILABLE"

SAT = "SAT"
UNSAT = "UNSAT"
EQUI_SAT = "EQUI_SAT"
WITNESS_LIFT = "WITNESS_LIFT"
NATIVE_CERT_ONLY = "NATIVE_CERT_ONLY"

SPECULATIVE = "SPECULATIVE"
CONJECTURE = "CONJECTURE"
EMPIRICAL_EVIDENCE = "EMPIRICAL_EVIDENCE"

ORBIT_CAPACITY_STRUCTURE_DETECTED = "ORBIT_CAPACITY_STRUCTURE_DETECTED"
ORBIT_CAPACITY_NATIVE_CERTIFIED = "ORBIT_CAPACITY_NATIVE_CERTIFIED"
ORBIT_CAPACITY_DIAGNOSTIC_ONLY = "ORBIT_CAPACITY_DIAGNOSTIC_ONLY"
ORBIT_CAPACITY_CERTIFICATE_VERIFIED = "ORBIT_CAPACITY_CERTIFICATE_VERIFIED"
ORBIT_CAPACITY_CERTIFICATE_FAILED = "ORBIT_CAPACITY_CERTIFICATE_FAILED"
HALL_DEFICIT_NATIVE_UNSAT = "HALL_DEFICIT_NATIVE_UNSAT"
G4_ORBIT_CAPACITY_NATIVE_CERTIFIED = "G4_ORBIT_CAPACITY_NATIVE_CERTIFIED"
ORBIT_COMPRESSION_EXPANDED_AND_VERIFIED = "ORBIT_COMPRESSION_EXPANDED_AND_VERIFIED"
ORBIT_COMPRESSION_DIAGNOSTIC_ONLY = "ORBIT_COMPRESSION_DIAGNOSTIC_ONLY"
ORBIT_COUNTING_DRAT_NOT_CLAIMED = "ORBIT_COUNTING_DRAT_NOT_CLAIMED"
UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED = "UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED"
DUPLICATE_OF_G3_PIGEONHOLE_PATTERN = "DUPLICATE_OF_G3_PIGEONHOLE_PATTERN"
G4_NO_NEW_DELTA = "G4_NO_NEW_DELTA"


@dataclass(frozen=True)
class ObstructionFingerprint:
    instance_id: str
    family: str
    grammar_failed: str
    public_category_before: str
    fingerprint_types: list[str]
    structural_features: dict[str, Any]
    evidence: dict[str, Any]
    confidence: str
    source_result_paths: list[str]
    recommended_operator_seeds: list[str]
    reproducibility_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CertificateObligation:
    candidate_id: str
    obligation_type: str
    checker_requirements: list[str]
    missing_pieces: list[str]
    independently_checkable: bool
    current_status: str
    no_fake_claim_guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratedOperatorCandidate:
    candidate_id: str
    name: str
    origin_fingerprints: list[str]
    generation_method: str
    status: str
    trigger_signature: list[str]
    intended_transformation: str
    preservation_obligation: str
    certificate_obligation: list[str]
    expected_witness_or_proof_type: str
    families_likely_helped: list[str]
    prior_grammars_expected_to_fail: list[str]
    proposed_new_grammar: str
    failure_modes: list[str]
    safety_risks: list[str]
    minimal_test_instances: list[str]
    promotion_criteria: list[str]
    forbidden_interpretations: list[str]
    novelty_score: float
    evidence_score: float
    risk_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorPromotionRecord:
    candidate_id: str
    from_status: str
    to_status: str
    promotion_allowed: bool
    reasons: list[str]
    missing_requirements: list[str]
    required_tests: list[str]
    claim_boundary: str
    timestamp_or_run_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fingerprint_hash(payload: dict[str, Any]) -> str:
    return _sha256_text(stable_json(payload))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(stable_json(payload), encoding="utf-8", newline="\n")


def make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source))
    digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
    return digest


def _php_formula(pigeons: int, holes: int) -> CNFFormula:
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


def _parity_formula(width: int, rhs: int = 1) -> CNFFormula:
    clauses: list[list[int]] = []
    for mask in range(1 << width):
        parity = bin(mask).count("1") % 2
        if parity == rhs:
            continue
        clause: list[int] = []
        for index in range(width):
            var = index + 1
            bit = (mask >> index) & 1
            clause.append(-var if bit else var)
        clauses.append(clause)
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


def _clique_proxy_formula(size: int) -> CNFFormula:
    clauses: list[list[int]] = []
    for i in range(1, size + 1):
        for j in range(i + 1, size + 1):
            clauses.append([i, j])
            clauses.append([-i, -j])
    return CNFFormula.from_raw_clauses(clauses)


def _subset_sum_toy_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3],
            [4, 5, 6],
            [-1, -4],
            [-2, -5],
            [-3, -6],
            [1, 4, 7],
            [-7, 8],
            [-8, 9],
        ]
    )


def _adversarial_mixed_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3, 4],
            [-1, -2, 3, 4],
            [-1, 2, -3, 4],
            [1, -2, -3, 4],
            [1, 2, -3, -4],
            [-1, 2, 3, -4],
            [5, 6],
            [-5, 7],
            [-6, 7],
            [-7, 8],
        ]
    )


def _near_symmetry_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3],
            [-1, -2],
            [-1, -3],
            [-2, -3],
            [4, 5, 6],
            [-4, -5],
            [-4, -6],
            [-5, -6],
            [6, 7],
        ]
    )


def _random_structured_formula() -> CNFFormula:
    clauses: list[list[int]] = []
    for i in range(1, 9):
        clauses.append([i, (i % 8) + 1])
        if i % 2 == 0:
            clauses.append([-i, ((i + 2) % 8) + 1])
    return CNFFormula.from_raw_clauses(clauses)


def _family_fixtures(families: Iterable[str]) -> list[dict[str, Any]]:
    fixtures: list[dict[str, Any]] = []
    selected = list(families)
    for family in selected:
        normalized = family.replace("_", "-")
        if normalized == "pigeonhole":
            fixtures.append(
                {
                    "instance_id": "php_5_4_frontier",
                    "family": "pigeonhole",
                    "formula": _php_formula(5, 4),
                    "grammar_failed": "G2_SYMMETRY_CERTIFIED",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "parity":
            fixtures.append(
                {
                    "instance_id": "parity_7_over_cap",
                    "family": "parity",
                    "formula": _parity_formula(7),
                    "grammar_failed": "G1_XOR",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "graph-coloring":
            fixtures.append(
                {
                    "instance_id": "cycle_6_3color_frontier",
                    "family": "graph-coloring",
                    "formula": _graph_coloring_formula(6, [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 1)], 3),
                    "grammar_failed": "G2_SYMMETRY_CERTIFIED",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "clique":
            fixtures.append(
                {
                    "instance_id": "clique_proxy_6",
                    "family": "clique",
                    "formula": _clique_proxy_formula(6),
                    "grammar_failed": "G1_XOR",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized in {"independent-set", "independent"}:
            fixtures.append(
                {
                    "instance_id": "independent_set_proxy_6",
                    "family": "independent-set",
                    "formula": _clique_proxy_formula(6),
                    "grammar_failed": "G1_XOR",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "subset-sum":
            fixtures.append(
                {
                    "instance_id": "subset_sum_capacity_toy",
                    "family": "subset-sum",
                    "formula": _subset_sum_toy_formula(),
                    "grammar_failed": "G3_SYMMETRY_CARDINALITY_CERTIFIED",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "adversarial-mixed":
            fixtures.append(
                {
                    "instance_id": "adversarial_mixed_affine_motif",
                    "family": "adversarial-mixed",
                    "formula": _adversarial_mixed_formula(),
                    "grammar_failed": "G1_XOR",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "near-symmetry":
            fixtures.append(
                {
                    "instance_id": "near_symmetry_broken_orbit",
                    "family": "near-symmetry",
                    "formula": _near_symmetry_formula(),
                    "grammar_failed": "G2_SYMMETRY_CERTIFIED",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
        elif normalized == "random-structured":
            fixtures.append(
                {
                    "instance_id": "random_structured_seed_0",
                    "family": "random-structured",
                    "formula": _random_structured_formula(),
                    "grammar_failed": "G1_XOR",
                    "public_category_before": "NO_COLLAPSE_FOUND",
                }
            )
    return fixtures


def _clause_size_distribution(formula: CNFFormula) -> dict[str, int]:
    counts = Counter(len(clause) for clause in formula.clauses)
    return {str(size): counts[size] for size in sorted(counts)}


def _literal_balance(formula: CNFFormula) -> dict[str, int]:
    positive = sum(1 for clause in formula.clauses for lit in clause if lit > 0)
    negative = sum(1 for clause in formula.clauses for lit in clause if lit < 0)
    return {"positive": positive, "negative": negative}


def _occurrence_signatures(formula: CNFFormula) -> dict[int, tuple[int, int, tuple[int, ...]]]:
    clause_sizes_by_var: dict[int, list[int]] = defaultdict(list)
    pos = Counter()
    neg = Counter()
    for clause in formula.clauses:
        for lit in clause:
            var = abs(lit)
            clause_sizes_by_var[var].append(len(clause))
            if lit > 0:
                pos[var] += 1
            else:
                neg[var] += 1
    return {
        var: (pos[var], neg[var], tuple(sorted(clause_sizes_by_var[var])))
        for var in formula.variables
    }


def _orbit_score(formula: CNFFormula) -> dict[str, Any]:
    grouped: dict[tuple[int, int, tuple[int, ...]], list[int]] = defaultdict(list)
    for var, signature in _occurrence_signatures(formula).items():
        grouped[signature].append(var)
    orbits = [vars_ for vars_ in grouped.values() if len(vars_) > 1]
    largest = max((len(vars_) for vars_ in orbits), default=1)
    covered = sum(len(vars_) for vars_ in orbits)
    return {
        "candidate_orbit_count": len(orbits),
        "largest_candidate_orbit": largest,
        "orbit_variable_coverage": covered,
        "candidate_orbits": [vars_ for vars_ in sorted(orbits, key=lambda item: (-len(item), item[0]))[:6]],
    }


def _cardinality_indicators(formula: CNFFormula) -> dict[str, Any]:
    positive_wide = [clause.literals for clause in formula.clauses if len(clause) >= 3 and all(lit > 0 for lit in clause)]
    negative_binary = [clause.literals for clause in formula.clauses if len(clause) == 2 and all(lit < 0 for lit in clause)]
    return {
        "positive_wide_clause_count": len(positive_wide),
        "negative_binary_clause_count": len(negative_binary),
        "alo_like_widths": sorted({len(clause) for clause in positive_wide}),
        "amo_like_pairs": len(negative_binary),
    }


def _variable_overlap_features(formula: CNFFormula) -> dict[str, Any]:
    pair_counts = Counter()
    variable_sets = []
    for clause in formula.clauses:
        variables = tuple(sorted(abs(lit) for lit in clause))
        variable_sets.append(variables)
        for i, first in enumerate(variables):
            for second in variables[i + 1 :]:
                pair_counts[(first, second)] += 1
    motif_counts = Counter(variable_sets)
    return {
        "max_pair_overlap": max(pair_counts.values(), default=0),
        "repeated_variable_set_count": sum(1 for count in motif_counts.values() if count > 1),
        "top_variable_set_multiplicity": max(motif_counts.values(), default=0),
    }


def extract_obstruction_fingerprint(fixture: dict[str, Any]) -> ObstructionFingerprint:
    formula: CNFFormula = fixture["formula"]
    family = fixture["family"]
    orbit = _orbit_score(formula)
    cardinality = _cardinality_indicators(formula)
    overlap = _variable_overlap_features(formula)
    literal_balance = _literal_balance(formula)
    features = {
        "variable_count": formula.num_vars,
        "clause_count": formula.num_clauses,
        "clause_size_distribution": _clause_size_distribution(formula),
        "literal_balance": literal_balance,
        "incidence_orbit_summary": orbit,
        "cardinality_indicators": cardinality,
        "overlap_features": overlap,
        "heuristic_only": True,
    }
    types: list[str] = []
    seeds: list[str] = []
    evidence: dict[str, Any] = {}

    if orbit["largest_candidate_orbit"] >= max(3, formula.num_vars // 3):
        types.append(SYMMETRY_HEAVY)
        evidence[SYMMETRY_HEAVY] = orbit
        seeds.append("ORBIT_COUNTING_COLLAPSE")
    if family == "pigeonhole":
        types.extend([COUNTING_DEFICIT, CAPACITY_FLOW_OBSTRUCTION])
        evidence[COUNTING_DEFICIT] = {"demand": 5, "capacity": 4, "source": "standard php fixture"}
        seeds.extend(["ORBIT_COUNTING_COLLAPSE", "CAPACITY_DEFICIT_COLLAPSE"])
    if family == "subset-sum":
        types.extend([CAPACITY_FLOW_OBSTRUCTION, COUNTING_DEFICIT, MODULAR_CONSTRAINT_SIGNAL])
        evidence[CAPACITY_FLOW_OBSTRUCTION] = {"capacity_rows": 2, "linking_clauses": 4}
        seeds.extend(["CAPACITY_DEFICIT_COLLAPSE", "MODULAR_RESIDUE_COLLAPSE"])
    if family == "parity":
        types.extend([HIGH_ARITY_AFFINE, MODULAR_CONSTRAINT_SIGNAL])
        evidence[HIGH_ARITY_AFFINE] = {"parity_width": 7, "current_exact_xor_cap": 6}
        seeds.append("MODULAR_RESIDUE_COLLAPSE")
    if family in {"graph-coloring", "clique", "independent-set"}:
        types.extend([GRAPH_SEPARATOR_OBSTRUCTION, HIGH_LOCAL_OVERLAP])
        evidence[GRAPH_SEPARATOR_OBSTRUCTION] = {"max_pair_overlap": overlap["max_pair_overlap"]}
        seeds.append("GRAPH_SEPARATOR_LIFT")
    if family == "graph-coloring":
        types.extend([FIBER_ORBIT_COMPRESSION, PROJECTION_LIFT_SIGNAL])
        seeds.append("FIBER_PROJECTION_COLLAPSE")
    if family == "adversarial-mixed":
        types.extend([AFFINE_HIDDEN, REPEATED_PROOF_MOTIF, PROOF_EXPORT_BLOWUP])
        evidence[PROOF_EXPORT_BLOWUP] = {"repeated_variable_sets": overlap["repeated_variable_set_count"]}
        seeds.extend(["PROOF_MOTIF_COMPRESSION", "MODULAR_RESIDUE_COLLAPSE"])
    if family == "near-symmetry":
        types.extend([SYMMETRY_HEAVY, CARDINALITY_INCOMPLETE])
        evidence[CARDINALITY_INCOMPLETE] = {"broken_orbit_variable": 7}
        seeds.append("ORBIT_COUNTING_COLLAPSE")
    if family == "random-structured":
        types = [NO_CONFIDENT_FINGERPRINT]
        evidence[NO_CONFIDENT_FINGERPRINT] = {"reason": "deterministic fixture lacks a dominant structural signal"}

    types = sorted(dict.fromkeys(types))
    seeds = sorted(dict.fromkeys(seeds))
    if not seeds:
        seeds = ["OBSTRUCTION_DUAL_CERTIFICATE"]
    confidence = "HIGH" if len(types) >= 3 else "MEDIUM" if types and types != [NO_CONFIDENT_FINGERPRINT] else "LOW"
    hash_payload = {
        "instance_id": fixture["instance_id"],
        "family": family,
        "fingerprint_types": types,
        "structural_features": features,
        "recommended_operator_seeds": seeds,
    }
    return ObstructionFingerprint(
        instance_id=fixture["instance_id"],
        family=family,
        grammar_failed=fixture["grammar_failed"],
        public_category_before=fixture["public_category_before"],
        fingerprint_types=types,
        structural_features=features,
        evidence=evidence,
        confidence=confidence,
        source_result_paths=[],
        recommended_operator_seeds=seeds,
        reproducibility_hash=_fingerprint_hash(hash_payload),
    )


def extract_fingerprints(families: Iterable[str]) -> list[ObstructionFingerprint]:
    return [extract_obstruction_fingerprint(fixture) for fixture in _family_fixtures(families)]


def _candidate_seed_definitions() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "OG-001",
            "name": "ORBIT_COUNTING_COLLAPSE",
            "trigger_signature": [SYMMETRY_HEAVY, COUNTING_DEFICIT],
            "generation_method": COMPOSED_FROM_MULTIPLE_FINGERPRINTS,
            "intended_transformation": "Group assignment variables into verified orbits, then emit counting certificates over orbit capacities.",
            "preservation_obligation": "Prove orbit action preserves the original CNF and counting constraints are checked against source clauses.",
            "certificate_obligation": [ORBIT_ACTION_VERIFICATION, COUNTING_SOUNDNESS, UNSAT_NATIVE_CERTIFICATE],
            "expected_witness_or_proof_type": NATIVE_CERT_ONLY,
            "families_likely_helped": ["pigeonhole variants", "matching", "scheduling", "allocation"],
            "prior_grammars_expected_to_fail": ["G1_XOR", "G2_SYMMETRY_CERTIFIED"],
            "proposed_new_grammar": "G4_ORBIT_COUNTING_PROTOTYPE",
            "minimal_test_instances": ["php_5_4", "matching_4_3_toy", "allocation_5_4_toy"],
            "novelty_base": 0.62,
        },
        {
            "candidate_id": "OG-002",
            "name": "CAPACITY_DEFICIT_COLLAPSE",
            "trigger_signature": [CAPACITY_FLOW_OBSTRUCTION, COUNTING_DEFICIT],
            "generation_method": SEEDED_FROM_KNOWN_PATTERN,
            "intended_transformation": "Detect demand greater than capacity through exact source constraints and emit Hall-style native deficit certificates.",
            "preservation_obligation": "Verify every demand/capacity inequality from original clauses before any native UNSAT certificate.",
            "certificate_obligation": [COUNTING_SOUNDNESS, UNSAT_NATIVE_CERTIFICATE],
            "expected_witness_or_proof_type": NATIVE_CERT_ONLY,
            "families_likely_helped": ["matching", "scheduling", "resource allocation", "generalized pigeonhole"],
            "prior_grammars_expected_to_fail": ["G1_XOR", "G2_SYMMETRY_CERTIFIED", "G3_SYMMETRY_CARDINALITY_CERTIFIED"],
            "proposed_new_grammar": "G4_CAPACITY_DEFICIT_PROTOTYPE",
            "minimal_test_instances": ["matching_3_2", "machine_scheduling_4_3", "resource_allocation_5_4"],
            "novelty_base": 0.55,
        },
        {
            "candidate_id": "OG-003",
            "name": "FIBER_PROJECTION_COLLAPSE",
            "trigger_signature": [FIBER_ORBIT_COMPRESSION, PROJECTION_LIFT_SIGNAL],
            "generation_method": NOVEL_SCHEMA_HYPOTHESIS,
            "intended_transformation": "Project equivalent fibers to a lower-dimensional representative space and provide a witness lift map.",
            "preservation_obligation": "Prove projection is equi-satisfiable and every projected witness lifts to an original witness.",
            "certificate_obligation": [PROJECTION_LIFT_VERIFICATION, SAT_WITNESS_RECONSTRUCTION, EQUI_SAT_PRESERVATION],
            "expected_witness_or_proof_type": WITNESS_LIFT,
            "families_likely_helped": ["reversible circuits", "equivalence-heavy encodings", "structured SAT"],
            "prior_grammars_expected_to_fail": ["G1_XOR", "G2_SYMMETRY_CERTIFIED"],
            "proposed_new_grammar": "G4_FIBER_PROJECTION_PROTOTYPE",
            "minimal_test_instances": ["cycle_6_3color", "equivalence_fiber_toy", "reversible_mux_toy"],
            "novelty_base": 0.82,
        },
        {
            "candidate_id": "OG-004",
            "name": "PROOF_MOTIF_COMPRESSION",
            "trigger_signature": [REPEATED_PROOF_MOTIF, PROOF_EXPORT_BLOWUP],
            "generation_method": ABSTRACTION_FROM_PRIOR_OPERATOR,
            "intended_transformation": "Identify repeated derivation motifs and propose reusable lemma certificates before DRAT export.",
            "preservation_obligation": "Each lemma must be independently derived or externally checked before reuse.",
            "certificate_obligation": [LEMMA_DERIVATION_TRACE, DRAT_BRIDGE],
            "expected_witness_or_proof_type": UNSAT,
            "families_likely_helped": ["structured UNSAT", "repetitive graph constraints", "induction-like formulas"],
            "prior_grammars_expected_to_fail": ["G1_XOR"],
            "proposed_new_grammar": "G4_PROOF_MOTIF_PROTOTYPE",
            "minimal_test_instances": ["tseitin_20_proof_blowup", "ladder_unsat_toy", "repeated_graph_constraint_toy"],
            "novelty_base": 0.7,
        },
        {
            "candidate_id": "OG-005",
            "name": "MODULAR_RESIDUE_COLLAPSE",
            "trigger_signature": [MODULAR_CONSTRAINT_SIGNAL, HIGH_ARITY_AFFINE],
            "generation_method": ABSTRACTION_FROM_PRIOR_OPERATOR,
            "intended_transformation": "Generalize exact XOR traces to exact modular residue constraints with replayable arithmetic traces.",
            "preservation_obligation": "Every modular constraint must be extracted from exact source clauses or carried as a checked side certificate.",
            "certificate_obligation": [MODULAR_ARITHMETIC_TRACE, EQUI_SAT_PRESERVATION],
            "expected_witness_or_proof_type": NATIVE_CERT_ONLY,
            "families_likely_helped": ["parity over cap", "crypto-like formulas", "modular arithmetic encodings"],
            "prior_grammars_expected_to_fail": ["G1_XOR"],
            "proposed_new_grammar": "G4_MODULAR_RESIDUE_PROTOTYPE",
            "minimal_test_instances": ["parity_12", "mod3_sum_toy", "xor_chain_high_arity"],
            "novelty_base": 0.74,
        },
        {
            "candidate_id": "OG-006",
            "name": "GRAPH_SEPARATOR_LIFT",
            "trigger_signature": [GRAPH_SEPARATOR_OBSTRUCTION, TREEWIDTH_OVER_CAP],
            "generation_method": SEEDED_FROM_KNOWN_PATTERN,
            "intended_transformation": "Use certified separators to decompose formulas and lift witnesses or native proofs across pieces.",
            "preservation_obligation": "Separator decomposition and boundary assignments must be replayable without brute-force arbitrary SAT solving.",
            "certificate_obligation": [GRAPH_DECOMPOSITION_TRACE, SAT_WITNESS_RECONSTRUCTION],
            "expected_witness_or_proof_type": WITNESS_LIFT,
            "families_likely_helped": ["graph coloring", "clique", "independent set", "bounded-separator graphs"],
            "prior_grammars_expected_to_fail": ["G0_BASE", "G1_XOR"],
            "proposed_new_grammar": "G4_GRAPH_SEPARATOR_PROTOTYPE",
            "minimal_test_instances": ["cycle_8_3color", "clique_proxy_6", "separator_grid_toy"],
            "novelty_base": 0.5,
        },
        {
            "candidate_id": "OG-007",
            "name": "OBSTRUCTION_DUAL_CERTIFICATE",
            "trigger_signature": [NO_CONFIDENT_FINGERPRINT, GRAPH_SEPARATOR_OBSTRUCTION, PROOF_EXPORT_BLOWUP],
            "generation_method": NOVEL_SCHEMA_HYPOTHESIS,
            "intended_transformation": "Turn persistent bounded non-collapse evidence into a native obstruction object and theorem-candidate queue.",
            "preservation_obligation": "Obstruction certificates must be scoped to configured grammar/resource bounds and never treated as hardness proofs.",
            "certificate_obligation": [LEMMA_DERIVATION_TRACE, GRAPH_DECOMPOSITION_TRACE],
            "expected_witness_or_proof_type": NATIVE_CERT_ONLY,
            "families_likely_helped": ["failed frontier instances", "proof-complexity candidates"],
            "prior_grammars_expected_to_fail": ["G0_BASE", "G1_XOR", "G2_SYMMETRY_CERTIFIED", "G3_SYMMETRY_CARDINALITY_CERTIFIED"],
            "proposed_new_grammar": "G4_OBSTRUCTION_DUAL_PROTOTYPE",
            "minimal_test_instances": ["random_structured_seed_0", "frontier_noncollapse_set_1"],
            "novelty_base": 0.9,
        },
    ]


def _matching_fingerprint_ids(fingerprints: list[ObstructionFingerprint], triggers: list[str]) -> list[str]:
    trigger_set = set(triggers)
    matches = [
        fingerprint.instance_id
        for fingerprint in fingerprints
        if trigger_set.intersection(fingerprint.fingerprint_types)
    ]
    return sorted(matches)


def _evidence_score(fingerprints: list[ObstructionFingerprint], triggers: list[str]) -> float:
    if not fingerprints:
        return 0.0
    trigger_set = set(triggers)
    matches = sum(1 for fingerprint in fingerprints if trigger_set.intersection(fingerprint.fingerprint_types))
    confidence_bonus = sum(1 for fingerprint in fingerprints if fingerprint.confidence == "HIGH" and trigger_set.intersection(fingerprint.fingerprint_types))
    return round(min(1.0, (matches + 0.5 * confidence_bonus) / max(1, len(fingerprints))), 3)


def _risk_score(seed: dict[str, Any]) -> float:
    obligations = seed["certificate_obligation"]
    base = 0.2 + 0.08 * len(obligations)
    if DRAT_BRIDGE in obligations:
        base += 0.18
    if seed["generation_method"] == NOVEL_SCHEMA_HYPOTHESIS:
        base += 0.12
    return round(min(1.0, base), 3)


def _safety_risks(seed: dict[str, Any]) -> list[str]:
    risks = [
        "Would be unsound if source constraints are inferred from missing clauses.",
        "Must not be reported as implemented before checker support exists.",
    ]
    if ORBIT_ACTION_VERIFICATION in seed["certificate_obligation"]:
        risks.append("Naive orbit merging can lose witnesses unless the group action is verified.")
    if DRAT_BRIDGE in seed["certificate_obligation"]:
        risks.append("DRAT bridge cannot be claimed without external proof checking against original CNF.")
    if MODULAR_ARITHMETIC_TRACE in seed["certificate_obligation"]:
        risks.append("Modular constraints must be exact; heuristic residue signals are not extraction claims.")
    return risks


def generate_operator_candidates(fingerprints: list[ObstructionFingerprint]) -> list[GeneratedOperatorCandidate]:
    candidates: list[GeneratedOperatorCandidate] = []
    for seed in _candidate_seed_definitions():
        evidence = _evidence_score(fingerprints, seed["trigger_signature"])
        risk = _risk_score(seed)
        novelty = round(seed["novelty_base"], 3)
        candidates.append(
            GeneratedOperatorCandidate(
                candidate_id=seed["candidate_id"],
                name=seed["name"],
                origin_fingerprints=_matching_fingerprint_ids(fingerprints, seed["trigger_signature"]),
                generation_method=seed["generation_method"],
                status=GENERATED_CANDIDATE,
                trigger_signature=seed["trigger_signature"],
                intended_transformation=seed["intended_transformation"],
                preservation_obligation=seed["preservation_obligation"],
                certificate_obligation=seed["certificate_obligation"],
                expected_witness_or_proof_type=seed["expected_witness_or_proof_type"],
                families_likely_helped=seed["families_likely_helped"],
                prior_grammars_expected_to_fail=seed["prior_grammars_expected_to_fail"],
                proposed_new_grammar=seed["proposed_new_grammar"],
                failure_modes=[
                    "false structural trigger",
                    "missing independent checker",
                    "certificate blowup",
                    "operator does not change bounded outcome",
                ],
                safety_risks=_safety_risks(seed),
                minimal_test_instances=seed["minimal_test_instances"],
                promotion_criteria=[
                    "trigger signature appears in at least one reproducible fingerprint",
                    "certificate obligation sketch is present",
                    "minimal test family is named",
                    "forbidden interpretations and safety risks are explicit",
                ],
                forbidden_interpretations=[
                    "Generated candidate is not implemented.",
                    "Generated candidate has not solved a formula.",
                    "Generated theorem candidates are not theorem claims.",
                    "No P vs NP progress is claimed.",
                ],
                novelty_score=novelty,
                evidence_score=evidence,
                risk_score=risk,
            )
        )
    return sorted(candidates, key=lambda item: (-(item.evidence_score + item.novelty_score - item.risk_score), item.candidate_id))


def certificate_obligations_for(candidate: GeneratedOperatorCandidate) -> list[CertificateObligation]:
    obligations: list[CertificateObligation] = []
    for obligation_type in candidate.certificate_obligation:
        requirements = {
            SAT_WITNESS_RECONSTRUCTION: ["reconstruct assignment", "verify lifted witness against original CNF"],
            UNSAT_NATIVE_CERTIFICATE: ["define native contradiction object", "replay source-clause obligations"],
            DRAT_BRIDGE: ["export proof.drat", "verify with external checker against original CNF"],
            EQUI_SAT_PRESERVATION: ["prove forward and backward satisfiability preservation"],
            COUNTING_SOUNDNESS: ["derive demand/capacity facts from original clauses", "check arithmetic contradiction"],
            ORBIT_ACTION_VERIFICATION: ["verify generators preserve clauses", "recompute orbit partition"],
            PROJECTION_LIFT_VERIFICATION: ["record projection map", "verify lift map on witnesses"],
            MODULAR_ARITHMETIC_TRACE: ["record modular rows", "replay arithmetic trace"],
            GRAPH_DECOMPOSITION_TRACE: ["record separator bags", "verify boundary consistency"],
            LEMMA_DERIVATION_TRACE: ["record lemma source", "replay derivation or mark checker missing"],
        }[obligation_type]
        obligations.append(
            CertificateObligation(
                candidate_id=candidate.candidate_id,
                obligation_type=obligation_type,
                checker_requirements=requirements,
                missing_pieces=["operator implementation", "independent checker", "red-team tests"],
                independently_checkable=obligation_type not in {DRAT_BRIDGE},
                current_status=SKETCH_ONLY,
                no_fake_claim_guardrails=[
                    "Do not mark candidate implemented.",
                    "Do not mark formula solved.",
                    "Do not claim DRAT without external verification.",
                    "Do not promote theorem-candidate to theorem.",
                ],
            )
        )
    return obligations


def build_certificate_obligation_matrix(candidates: Iterable[GeneratedOperatorCandidate]) -> list[CertificateObligation]:
    matrix: list[CertificateObligation] = []
    for candidate in candidates:
        matrix.extend(certificate_obligations_for(candidate))
    return matrix


def evaluate_promotion(candidate: GeneratedOperatorCandidate, run_id: str = "") -> OperatorPromotionRecord:
    missing: list[str] = []
    if not candidate.trigger_signature:
        missing.append("trigger_signature")
    if not candidate.intended_transformation:
        missing.append("intended_transformation")
    if not candidate.certificate_obligation:
        missing.append("certificate_obligation")
    if not candidate.minimal_test_instances:
        missing.append("minimal_test_instances")
    if not candidate.safety_risks:
        missing.append("safety_risks")
    if not candidate.forbidden_interpretations:
        missing.append("forbidden_interpretations")
    unsafe = any("UNSAFE" in risk.upper() or "NO_PRESERVATION" in risk.upper() for risk in candidate.safety_risks)
    if unsafe:
        return OperatorPromotionRecord(
            candidate_id=candidate.candidate_id,
            from_status=candidate.status,
            to_status=REJECTED_UNSAFE,
            promotion_allowed=False,
            reasons=["Safety risks indicate an unsound or unchecked preservation path."],
            missing_requirements=missing,
            required_tests=candidate.minimal_test_instances,
            claim_boundary="Rejected candidates are not implemented and are not solver results.",
            timestamp_or_run_id=run_id or datetime.now(timezone.utc).isoformat(),
        )
    if "certificate_obligation" in missing:
        to_status = REJECTED_NO_CERTIFICATE_SKETCH
    elif "minimal_test_instances" in missing:
        to_status = REJECTED_NO_TEST_FAMILY
    else:
        to_status = PROMOTION_ELIGIBLE
    return OperatorPromotionRecord(
        candidate_id=candidate.candidate_id,
        from_status=candidate.status,
        to_status=to_status,
        promotion_allowed=not missing,
        reasons=[
            "Promotion means eligible for prototype planning only; no implemented or certified claim is made.",
            "Certificate sketch, trigger signature, risks, and test family are recorded.",
        ]
        if not missing
        else ["Promotion blocked by missing requirements."],
        missing_requirements=missing,
        required_tests=candidate.minimal_test_instances,
        claim_boundary="Generated candidates are schemas, not implemented operators or theorem claims.",
        timestamp_or_run_id=run_id or datetime.now(timezone.utc).isoformat(),
    )


def build_promotion_queue(candidates: Iterable[GeneratedOperatorCandidate], run_id: str) -> list[OperatorPromotionRecord]:
    return [evaluate_promotion(candidate, run_id) for candidate in candidates]


def build_theorem_candidate_queue(candidates: Iterable[GeneratedOperatorCandidate]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for candidate in candidates:
        status = CONJECTURE if candidate.evidence_score >= 0.5 else SPECULATIVE
        queue.append(
            {
                "theorem_id": f"TQ-{candidate.candidate_id.split('-')[-1]}",
                "candidate_operator": candidate.name,
                "bounded_strictness_statement": (
                    f"There may exist a bounded profile B where instances showing {', '.join(candidate.trigger_signature)} "
                    f"enter W_B({candidate.proposed_new_grammar}) but remain outside the prior bounded grammars."
                ),
                "expected_witness_family": candidate.families_likely_helped,
                "prior_grammar_expected_to_fail": candidate.prior_grammars_expected_to_fail,
                "new_grammar_expected_to_succeed": candidate.proposed_new_grammar,
                "proof_obligations": candidate.certificate_obligation,
                "current_status": status,
                "forbidden_interpretations": [
                    "Not a theorem.",
                    "No lower bound against prior grammars is proved.",
                    "No implemented operator or solved instance is claimed.",
                    "No P vs NP progress is claimed.",
                ],
            }
        )
    return queue


def operator_schema_language() -> dict[str, Any]:
    return {
        "schema_version": GENESIS_VERSION,
        "required_fields": [
            "name",
            "trigger_signature",
            "intended_transformation",
            "preserved_property",
            "certificate_obligation",
            "independent_checker_requirement",
            "expected_delta",
            "target_families",
            "minimal_test_instances",
            "safety_risks",
            "forbidden_interpretations",
            "promotion_criteria",
            "theorem_candidate_generated",
        ],
        "preserved_property_values": [SAT, UNSAT, EQUI_SAT, WITNESS_LIFT, NATIVE_CERT_ONLY],
        "candidate_status_values": [
            GENERATED_CANDIDATE,
            PROMOTION_ELIGIBLE,
            PROTOTYPE_PLANNED,
            REJECTED_UNSAFE,
            REJECTED_NO_CERTIFICATE_SKETCH,
            REJECTED_NO_TEST_FAMILY,
        ],
        "fingerprint_values": [
            SYMMETRY_HEAVY,
            COUNTING_DEFICIT,
            AFFINE_HIDDEN,
            HIGH_ARITY_AFFINE,
            HIGH_LOCAL_OVERLAP,
            REPEATED_PROOF_MOTIF,
            MODULAR_CONSTRAINT_SIGNAL,
            GRAPH_SEPARATOR_OBSTRUCTION,
            CAPACITY_FLOW_OBSTRUCTION,
            FIBER_ORBIT_COMPRESSION,
            PROJECTION_LIFT_SIGNAL,
            CARDINALITY_INCOMPLETE,
            TREEWIDTH_OVER_CAP,
            PROOF_EXPORT_BLOWUP,
            NO_CONFIDENT_FINGERPRINT,
        ],
        "claim_boundary": "Operator schemas are proposals until implemented, checked, tested, red-teamed, and frozen.",
    }


def _rank_summary(candidates: Iterable[GeneratedOperatorCandidate]) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        combined = round(candidate.evidence_score + candidate.novelty_score - candidate.risk_score, 3)
        rows.append(
            {
                "candidate_id": candidate.candidate_id,
                "name": candidate.name,
                "novelty_score": candidate.novelty_score,
                "evidence_score": candidate.evidence_score,
                "risk_score": candidate.risk_score,
                "combined_priority_score": combined,
                "status": candidate.status,
            }
        )
    return sorted(rows, key=lambda row: (-row["combined_priority_score"], row["candidate_id"]))


def operator_genesis_report(
    fingerprints: list[ObstructionFingerprint],
    candidates: list[GeneratedOperatorCandidate],
    obligations: list[CertificateObligation],
    promotions: list[OperatorPromotionRecord],
    theorem_queue: list[dict[str, Any]],
) -> str:
    lines = [
        "# Operator Genesis Report",
        "",
        "## Executive Summary",
        "",
        "v2.4 generates candidate operator schemas. It does not claim that generated candidates are implemented, certified, or theorem-proven.",
        "",
        "## Why v2.4 Exists After G1/G2/G3",
        "",
        "G1_XOR, G2_SYMMETRY_CERTIFIED, and G3_SYMMETRY_CARDINALITY_CERTIFIED showed that new operators can change bounded collapse outcomes when their certificates are explicit. v2.4 turns remaining obstruction fingerprints into a promotion queue for the next operator leap.",
        "",
        "## Obstruction Fingerprint Definitions",
        "",
        "Fingerprints are deterministic structural summaries. They are heuristic unless a later checker discharges the associated certificate obligations.",
        "",
    ]
    for name in operator_schema_language()["fingerprint_values"]:
        lines.append(f"- `{name}`")
    lines.extend(["", "## Fingerprint Extraction Results", ""])
    for fingerprint in fingerprints:
        lines.append(
            f"- `{fingerprint.instance_id}` ({fingerprint.family}): {', '.join(fingerprint.fingerprint_types)}; confidence `{fingerprint.confidence}`"
        )
    lines.extend(["", "## Generated Operator Candidates", ""])
    for row in _rank_summary(candidates):
        lines.append(
            f"- `{row['candidate_id']}` `{row['name']}`: status `{row['status']}`, novelty {row['novelty_score']}, evidence {row['evidence_score']}, risk {row['risk_score']}"
        )
    lines.extend(
        [
            "",
            "## Novelty vs Seeded-Known-Pattern Distinction",
            "",
            "Candidates record whether they are seeded from known patterns, composed from multiple fingerprints, abstractions from prior operators, or novel schema hypotheses. Novelty is tracked separately from evidence.",
            "",
            "## Certificate Obligation Matrix",
            "",
        ]
    )
    by_candidate: dict[str, list[str]] = defaultdict(list)
    for obligation in obligations:
        by_candidate[obligation.candidate_id].append(obligation.obligation_type)
    for candidate_id, obligation_types in sorted(by_candidate.items()):
        lines.append(f"- `{candidate_id}`: {', '.join(obligation_types)}")
    lines.extend(["", "## Promotion Queue", ""])
    for record in promotions:
        lines.append(
            f"- `{record.candidate_id}`: `{record.from_status}` -> `{record.to_status}`; allowed={record.promotion_allowed}"
        )
    lines.extend(["", "## Theorem Candidate Queue", ""])
    for item in theorem_queue:
        lines.append(f"- `{item['theorem_id']}` for `{item['candidate_operator']}`: `{item['current_status']}`")
    lines.extend(
        [
            "",
            "## What Is Not Implemented",
            "",
            "No generated candidate is implemented in v2.4. No generated candidate is a solver route. No generated candidate is trusted as a working collapse operator.",
            "",
            "## What Is Not Proven",
            "",
            "No generated theorem candidate is labeled as a theorem. No lower bound against a prior grammar is proved.",
            "",
            "## What Remains Forbidden",
            "",
            "- no P vs NP progress claim",
            "- no polynomial-time SAT claim",
            "- no fake DRAT claim",
            "- no fake certificate claim",
            "- no generated operator solved-claim",
            "- no HARD or UNKNOWN status claims",
            "",
            "## First True Novel-Operator Breakthrough Criteria",
            "",
            "A future generated operator becomes a real operator only after implementation, independent checker support, test-family evidence, claim-boundary review, and a frozen artifact.",
            "",
            "## v2.5 Recommendation",
            "",
            "Prototype the highest-ranked candidate with a narrow checker-first plan. The current ranking favors candidates with strong fingerprints and explicit certificate sketches, not speculative solving claims.",
            "",
        ]
    )
    return "\n".join(lines)


def run_operator_genesis(
    *,
    families: Iterable[str],
    out_root: str | Path,
    strict: bool = False,
    zip_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    run_id = f"operator-genesis-{GENESIS_VERSION}"
    fingerprints = extract_fingerprints(families)
    candidates = generate_operator_candidates(fingerprints)
    obligations = build_certificate_obligation_matrix(candidates)
    promotions = build_promotion_queue(candidates, run_id)
    theorem_queue = build_theorem_candidate_queue(candidates)
    schema = operator_schema_language()
    ranking = _rank_summary(candidates)
    payloads = {
        "obstruction_fingerprints.json": [item.to_dict() for item in fingerprints],
        "generated_operator_candidates.json": [item.to_dict() for item in candidates],
        "operator_promotion_queue.json": [item.to_dict() for item in promotions],
        "certificate_obligation_matrix.json": [item.to_dict() for item in obligations],
        "theorem_candidate_queue.json": theorem_queue,
        "operator_schema_language.json": schema,
        "candidate_operator_rankings.json": ranking,
        "manifest.json": {
            "version": GENESIS_VERSION,
            "families": list(families),
            "strict": strict,
            "candidate_count": len(candidates),
            "fingerprint_count": len(fingerprints),
            "claim_boundary": "generated schemas only; no implemented operator or theorem claim",
        },
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    report = operator_genesis_report(fingerprints, candidates, obligations, promotions, theorem_queue)
    (root / "OPERATOR_GENESIS_REPORT.md").write_text(report, encoding="utf-8", newline="\n")
    zip_digest = ""
    if zip_path:
        zip_digest = make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": zip_digest,
        "obstruction_fingerprints": payloads["obstruction_fingerprints.json"],
        "generated_operator_candidates": payloads["generated_operator_candidates.json"],
        "operator_promotion_queue": payloads["operator_promotion_queue.json"],
        "certificate_obligation_matrix": payloads["certificate_obligation_matrix.json"],
        "theorem_candidate_queue": theorem_queue,
        "candidate_operator_rankings": ranking,
        "operator_schema_language": schema,
    }


@dataclass(frozen=True)
class OrbitCapacityInstance:
    instance_id: str
    items: tuple[str, ...]
    resources: tuple[str, ...]
    allowed_resources: dict[str, tuple[str, ...]]
    resource_capacities: dict[str, int]
    assignment_variables: dict[tuple[str, str], int]
    formula: CNFFormula
    family: str = "orbit-capacity"
    duplicate_of_g3: bool = False
    sat_control: bool = False
    incomplete_structure: bool = False
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "items": list(self.items),
            "resources": list(self.resources),
            "allowed_resources": {item: list(resources) for item, resources in self.allowed_resources.items()},
            "resource_capacities": dict(self.resource_capacities),
            "assignment_variables": [
                {"item": item, "resource": resource, "variable": variable}
                for (item, resource), variable in sorted(self.assignment_variables.items())
            ],
            "formula_hash": self.formula.formula_hash,
            "duplicate_of_g3": self.duplicate_of_g3,
            "sat_control": self.sat_control,
            "incomplete_structure": self.incomplete_structure,
            "description": self.description,
        }


@dataclass(frozen=True)
class OrbitCapacityCertificate:
    type: str
    instance_id: str
    formula_hash: str
    assignment_variables: list[dict[str, Any]]
    demand_subset: list[str]
    neighborhood_resources: list[str]
    resource_capacities: dict[str, int]
    alo_clause_ids_by_item: dict[str, int]
    amo_clause_ids_by_resource: dict[str, list[int]]
    capacity_constraint_ids_by_resource: dict[str, list[int]]
    demand_count: int
    capacity_count: int
    contradiction: bool
    hall_deficit: bool
    orbit_summary: dict[str, Any]
    orbit_compression_used: bool
    orbit_expanded_and_verified: bool
    checker_status: str
    status: str
    public_category: str
    certification_level: str
    drat_claim: str
    claim_boundary: str
    g3_duplicate_control: bool
    g4_delta_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normal_clause_key(literals: Iterable[int]) -> tuple[int, ...]:
    return Clause(literals).literals


def _clause_id_map(formula: CNFFormula) -> dict[tuple[int, ...], int]:
    return {clause.literals: idx for idx, clause in enumerate(formula.clauses, start=1)}


def _assignment_var(item_index: int, resource_index: int, resource_count: int) -> int:
    return (item_index - 1) * resource_count + resource_index


def _build_assignment_formula(
    *,
    items: Iterable[str],
    resources: Iterable[str],
    allowed_resources: dict[str, Iterable[str]],
    resource_capacities: dict[str, int],
    omit_alo_items: Iterable[str] = (),
    omit_capacity_clauses: Iterable[tuple[str, tuple[str, ...]]] = (),
) -> tuple[CNFFormula, dict[tuple[str, str], int]]:
    item_list = tuple(items)
    resource_list = tuple(resources)
    resource_index = {resource: idx + 1 for idx, resource in enumerate(resource_list)}
    assignment_variables: dict[tuple[str, str], int] = {}
    for item_idx, item in enumerate(item_list, start=1):
        for resource in allowed_resources[item]:
            assignment_variables[(item, resource)] = _assignment_var(item_idx, resource_index[resource], len(resource_list))

    clauses: list[list[int]] = []
    omitted_alo = set(omit_alo_items)
    omitted_capacity = {(resource, tuple(sorted(items_))) for resource, items_ in omit_capacity_clauses}
    for item in item_list:
        if item in omitted_alo:
            continue
        clauses.append([assignment_variables[(item, resource)] for resource in allowed_resources[item]])

    for resource in resource_list:
        users = [item for item in item_list if resource in allowed_resources[item]]
        cap = int(resource_capacities.get(resource, 1))
        if cap < 1:
            raise ValueError(f"resource capacity must be positive: {resource}")
        for limited_group in combinations(users, cap + 1):
            key = (resource, tuple(sorted(limited_group)))
            if key in omitted_capacity:
                continue
            clauses.append([-assignment_variables[(item, resource)] for item in limited_group])
    return CNFFormula.from_raw_clauses(clauses), assignment_variables


def make_orbit_capacity_instance(instance_id: str) -> OrbitCapacityInstance:
    specs: dict[str, dict[str, Any]] = {
        "complete_match_3_2": {
            "items": ("i1", "i2", "i3"),
            "resources": ("r1", "r2"),
            "allowed": {"i1": ("r1", "r2"), "i2": ("r1", "r2"), "i3": ("r1", "r2")},
            "capacities": {"r1": 1, "r2": 1},
            "duplicate": True,
            "description": "Complete assignment deficit equivalent to the standard G3 pigeonhole pattern.",
        },
        "complete_match_4_3": {
            "items": ("i1", "i2", "i3", "i4"),
            "resources": ("r1", "r2", "r3"),
            "allowed": {f"i{i}": ("r1", "r2", "r3") for i in range(1, 5)},
            "capacities": {"r1": 1, "r2": 1, "r3": 1},
            "duplicate": True,
            "description": "Complete assignment deficit equivalent to the standard G3 pigeonhole pattern.",
        },
        "hall_local_3_2": {
            "items": ("a", "b", "c"),
            "resources": ("r1", "r2", "r3"),
            "allowed": {"a": ("r1", "r2"), "b": ("r1", "r2"), "c": ("r1", "r2")},
            "capacities": {"r1": 1, "r2": 1, "r3": 1},
            "description": "Local Hall deficit: three items are confined to two unit-capacity resources.",
        },
        "hall_local_4_3": {
            "items": ("a", "b", "c", "d"),
            "resources": ("r1", "r2", "r3"),
            "allowed": {"a": ("r1", "r2"), "b": ("r1", "r2"), "c": ("r1", "r2"), "d": ("r3",)},
            "capacities": {"r1": 1, "r2": 1, "r3": 1},
            "description": "Balanced globally but unsat by local Hall deficit on {a,b,c}.",
        },
        "hall_local_5_4": {
            "items": ("a", "b", "c", "d", "e"),
            "resources": ("r1", "r2", "r3", "r4"),
            "allowed": {"a": ("r1", "r2"), "b": ("r1", "r2"), "c": ("r1", "r2"), "d": ("r3",), "e": ("r4",)},
            "capacities": {"r1": 1, "r2": 1, "r3": 1, "r4": 1},
            "description": "Five-item local Hall deficit with a balanced-looking global resource count.",
        },
        "allocation_capacity_5_4_local_deficit": {
            "items": ("a", "b", "c", "d", "e"),
            "resources": ("r1", "r2", "r3"),
            "allowed": {"a": ("r1", "r2"), "b": ("r1", "r2"), "c": ("r1", "r2"), "d": ("r1", "r2"), "e": ("r1", "r2")},
            "capacities": {"r1": 2, "r2": 2, "r3": 3},
            "description": "Five demands are trapped in two resources of total capacity four.",
        },
        "scheduling_slot_capacity_local_deficit": {
            "items": ("t1", "t2", "t3", "t4", "t5", "t6"),
            "resources": ("slot1", "slot2", "slot3"),
            "allowed": {
                "t1": ("slot1", "slot2"),
                "t2": ("slot1", "slot2"),
                "t3": ("slot1", "slot2"),
                "t4": ("slot1", "slot2"),
                "t5": ("slot1", "slot2"),
                "t6": ("slot3",),
            },
            "capacities": {"slot1": 2, "slot2": 2, "slot3": 2},
            "description": "Scheduling-style local capacity deficit.",
        },
        "capacity_deficit_5_over_4": {
            "items": ("t1", "t2", "t3", "t4", "t5"),
            "resources": ("s1", "s2"),
            "allowed": {f"t{i}": ("s1", "s2") for i in range(1, 6)},
            "capacities": {"s1": 2, "s2": 2},
            "description": "Capacity greater than one with five tasks over total capacity four.",
        },
        "capacity_deficit_7_over_6": {
            "items": ("t1", "t2", "t3", "t4", "t5", "t6", "t7"),
            "resources": ("s1", "s2", "s3"),
            "allowed": {
                "t1": ("s1", "s2"),
                "t2": ("s1", "s2"),
                "t3": ("s1", "s2"),
                "t4": ("s1", "s2"),
                "t5": ("s1", "s2"),
                "t6": ("s3",),
                "t7": ("s3",),
            },
            "capacities": {"s1": 2, "s2": 2, "s3": 2},
            "description": "Capacity greater than one with a five-task local deficit inside a seven-task instance.",
        },
        "hall_balanced_3_3_sat_control": {
            "items": ("a", "b", "c"),
            "resources": ("r1", "r2", "r3"),
            "allowed": {"a": ("r1",), "b": ("r2",), "c": ("r3",)},
            "capacities": {"r1": 1, "r2": 1, "r3": 1},
            "sat_control": True,
            "description": "Balanced satisfiable control with no Hall deficit.",
        },
        "capacity_balanced_4_4_no_contradiction": {
            "items": ("t1", "t2", "t3", "t4"),
            "resources": ("s1", "s2"),
            "allowed": {f"t{i}": ("s1", "s2") for i in range(1, 5)},
            "capacities": {"s1": 2, "s2": 2},
            "sat_control": True,
            "description": "Capacity control with demand equal to available capacity.",
        },
        "incomplete_capacity_structure_reject": {
            "items": ("a", "b", "c"),
            "resources": ("r1", "r2"),
            "allowed": {"a": ("r1", "r2"), "b": ("r1", "r2"), "c": ("r1", "r2")},
            "capacities": {"r1": 1, "r2": 1},
            "omit_capacity": [("r1", ("a", "b"))],
            "incomplete": True,
            "description": "Deficit-shaped instance with a missing AMO clause; checker must reject.",
        },
    }
    if instance_id not in specs:
        raise ValueError(f"unsupported orbit-capacity instance id: {instance_id}")
    spec = specs[instance_id]
    formula, assignment_variables = _build_assignment_formula(
        items=spec["items"],
        resources=spec["resources"],
        allowed_resources=spec["allowed"],
        resource_capacities=spec["capacities"],
        omit_alo_items=spec.get("omit_alo", ()),
        omit_capacity_clauses=spec.get("omit_capacity", ()),
    )
    return OrbitCapacityInstance(
        instance_id=instance_id,
        items=tuple(spec["items"]),
        resources=tuple(spec["resources"]),
        allowed_resources={item: tuple(resources) for item, resources in spec["allowed"].items()},
        resource_capacities={resource: int(capacity) for resource, capacity in spec["capacities"].items()},
        assignment_variables=assignment_variables,
        formula=formula,
        duplicate_of_g3=bool(spec.get("duplicate", False)),
        sat_control=bool(spec.get("sat_control", False)),
        incomplete_structure=bool(spec.get("incomplete", False)),
        description=str(spec.get("description", "")),
    )


def _all_orbit_capacity_instance_ids() -> list[str]:
    return [
        "hall_local_3_2",
        "hall_local_4_3",
        "hall_local_5_4",
        "allocation_capacity_5_4_local_deficit",
        "scheduling_slot_capacity_local_deficit",
        "capacity_deficit_5_over_4",
        "capacity_deficit_7_over_6",
        "complete_match_3_2",
        "complete_match_4_3",
        "hall_balanced_3_3_sat_control",
        "capacity_balanced_4_4_no_contradiction",
        "incomplete_capacity_structure_reject",
    ]


def find_hall_deficit(instance: OrbitCapacityInstance, *, max_subset_size: int = 6) -> dict[str, Any]:
    for size in range(1, min(max_subset_size, len(instance.items)) + 1):
        for subset in combinations(instance.items, size):
            neighborhood = sorted({resource for item in subset for resource in instance.allowed_resources[item]})
            demand = len(subset)
            capacity = sum(instance.resource_capacities[resource] for resource in neighborhood)
            if demand > capacity:
                return {
                    "status": HALL_DEFICIT_NATIVE_UNSAT,
                    "demand_subset": list(subset),
                    "neighborhood_resources": neighborhood,
                    "demand_count": demand,
                    "capacity_count": capacity,
                    "search_nodes_expanded": sum(1 for prior_size in range(1, size) for _ in combinations(instance.items, prior_size))
                    + 1,
                    "max_subset_size": max_subset_size,
                }
    return {
        "status": ORBIT_CAPACITY_DIAGNOSTIC_ONLY,
        "demand_subset": [],
        "neighborhood_resources": [],
        "demand_count": 0,
        "capacity_count": 0,
        "search_nodes_expanded": sum(1 for size in range(1, min(max_subset_size, len(instance.items)) + 1) for _ in combinations(instance.items, size)),
        "max_subset_size": max_subset_size,
    }


def _orbit_capacity_orbit_summary(instance: OrbitCapacityInstance, demand_subset: Iterable[str]) -> dict[str, Any]:
    item_groups: dict[tuple[tuple[str, ...], int], list[str]] = defaultdict(list)
    for item in instance.items:
        resources = tuple(instance.allowed_resources[item])
        cap_sum = sum(instance.resource_capacities[resource] for resource in resources)
        item_groups[(resources, cap_sum)].append(item)
    resource_groups: dict[tuple[int, tuple[str, ...]], list[str]] = defaultdict(list)
    for resource in instance.resources:
        users = tuple(item for item in instance.items if resource in instance.allowed_resources[item])
        resource_groups[(instance.resource_capacities[resource], users)].append(resource)
    demand_set = set(demand_subset)
    return {
        "item_orbits_by_neighborhood": [group for group in sorted(item_groups.values(), key=lambda group: (-len(group), group[0]))],
        "resource_orbits_by_capacity_and_users": [group for group in sorted(resource_groups.values(), key=lambda group: (-len(group), group[0]))],
        "demand_subset_orbit_coverage": sorted(demand_set),
        "heuristic_orbit_summary_only": True,
    }


def _ids_for_orbit_capacity_constraints(
    formula: CNFFormula,
    instance: OrbitCapacityInstance,
    *,
    demand_subset: Iterable[str],
) -> tuple[dict[str, int], dict[str, list[int]], dict[str, list[int]]]:
    clause_ids = _clause_id_map(formula)
    alo_ids: dict[str, int] = {}
    for item in demand_subset:
        clause = _normal_clause_key(instance.assignment_variables[(item, resource)] for resource in instance.allowed_resources[item])
        if clause in clause_ids:
            alo_ids[item] = clause_ids[clause]

    amo_ids: dict[str, list[int]] = {}
    cap_ids: dict[str, list[int]] = {}
    for resource in instance.resources:
        users = [item for item in instance.items if resource in instance.allowed_resources[item]]
        cap = instance.resource_capacities[resource]
        ids: list[int] = []
        for limited_group in combinations(users, cap + 1):
            clause = _normal_clause_key(-instance.assignment_variables[(item, resource)] for item in limited_group)
            if clause in clause_ids:
                ids.append(clause_ids[clause])
        if ids:
            cap_ids[resource] = sorted(ids)
        if cap == 1 and ids:
            amo_ids[resource] = sorted(ids)
    return alo_ids, amo_ids, cap_ids


def build_orbit_capacity_certificate(
    instance: OrbitCapacityInstance,
    *,
    max_subset_size: int = 6,
    use_orbit_compression: bool = True,
) -> OrbitCapacityCertificate:
    deficit = find_hall_deficit(instance, max_subset_size=max_subset_size)
    demand_subset = list(deficit["demand_subset"])
    neighborhood = list(deficit["neighborhood_resources"])
    alo_ids, amo_ids, cap_ids = _ids_for_orbit_capacity_constraints(instance.formula, instance, demand_subset=demand_subset)
    assignment_records = [
        {"item": item, "resource": resource, "variable": variable}
        for (item, resource), variable in sorted(instance.assignment_variables.items())
    ]
    orbit_summary = _orbit_capacity_orbit_summary(instance, demand_subset)
    compression_used = use_orbit_compression and any(len(group) > 1 for group in orbit_summary["item_orbits_by_neighborhood"])
    status = ORBIT_CAPACITY_CERTIFICATE_FAILED
    checker_status = ORBIT_CAPACITY_CERTIFICATE_FAILED
    public_category = "NO_COLLAPSE_FOUND"
    certification_level = "NOT_CERTIFIED"
    notes = "No Hall/capacity deficit certificate was emitted."
    if demand_subset and deficit["demand_count"] > deficit["capacity_count"]:
        status = HALL_DEFICIT_NATIVE_UNSAT
        checker_status = "NOT_RUN"
        public_category = UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED
        certification_level = ORBIT_CAPACITY_NATIVE_CERTIFIED
        notes = "Native Hall/capacity-deficit contradiction candidate; checker must expand all evidence against the original CNF."

    cert = OrbitCapacityCertificate(
        type="ORBIT_CAPACITY_DEFICIT_CONTRADICTION",
        instance_id=instance.instance_id,
        formula_hash=instance.formula.formula_hash,
        assignment_variables=assignment_records,
        demand_subset=demand_subset,
        neighborhood_resources=neighborhood,
        resource_capacities={resource: int(instance.resource_capacities[resource]) for resource in sorted(instance.resource_capacities)},
        alo_clause_ids_by_item=alo_ids,
        amo_clause_ids_by_resource=amo_ids,
        capacity_constraint_ids_by_resource=cap_ids,
        demand_count=int(deficit["demand_count"]),
        capacity_count=int(deficit["capacity_count"]),
        contradiction=bool(deficit["demand_count"] > deficit["capacity_count"]),
        hall_deficit=bool(demand_subset and deficit["demand_count"] > deficit["capacity_count"]),
        orbit_summary=orbit_summary,
        orbit_compression_used=compression_used,
        orbit_expanded_and_verified=compression_used,
        checker_status=checker_status,
        status=status,
        public_category=public_category,
        certification_level=certification_level,
        drat_claim=ORBIT_COUNTING_DRAT_NOT_CLAIMED,
        claim_boundary="native capacity-deficit certificate only; no DRAT proof claimed",
        g3_duplicate_control=instance.duplicate_of_g3,
        g4_delta_status=DUPLICATE_OF_G3_PIGEONHOLE_PATTERN if instance.duplicate_of_g3 else "PENDING_CHECK",
        notes=notes,
    )
    check = check_orbit_capacity_certificate(instance.formula, cert)
    data = cert.to_dict()
    data["checker_status"] = check["status"]
    data["orbit_expanded_and_verified"] = check["status"] == ORBIT_CAPACITY_CERTIFICATE_VERIFIED
    if check["status"] == ORBIT_CAPACITY_CERTIFICATE_VERIFIED:
        data["status"] = HALL_DEFICIT_NATIVE_UNSAT
        data["public_category"] = UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED
        data["certification_level"] = ORBIT_CAPACITY_NATIVE_CERTIFIED
        data["g4_delta_status"] = DUPLICATE_OF_G3_PIGEONHOLE_PATTERN if instance.duplicate_of_g3 else G4_ORBIT_CAPACITY_NATIVE_CERTIFIED
        data["notes"] = (
            "Orbit compression helps discover and compress the deficit; the UNSAT certificate is verified by expanding "
            "the orbit/capacity evidence against the original CNF."
        )
    else:
        data["status"] = ORBIT_CAPACITY_CERTIFICATE_FAILED if demand_subset else ORBIT_CAPACITY_DIAGNOSTIC_ONLY
        data["public_category"] = "NO_COLLAPSE_FOUND"
        data["certification_level"] = "NOT_CERTIFIED"
        data["g4_delta_status"] = G4_NO_NEW_DELTA
        data["notes"] = "No native G4 collapse is claimed because the Hall/capacity certificate obligations did not verify."
    return OrbitCapacityCertificate(**data)


def _certificate_assignment_maps(data: dict[str, Any]) -> tuple[dict[tuple[str, str], int], dict[str, tuple[str, ...]], tuple[str, ...], tuple[str, ...]]:
    assignment: dict[tuple[str, str], int] = {}
    items: set[str] = set()
    resources: set[str] = set()
    for record in data.get("assignment_variables", []):
        item = str(record["item"])
        resource = str(record["resource"])
        variable = int(record["variable"])
        key = (item, resource)
        if key in assignment:
            raise ValueError(f"duplicate assignment variable for {key}")
        assignment[key] = variable
        items.add(item)
        resources.add(resource)
    allowed: dict[str, list[str]] = defaultdict(list)
    for item, resource in sorted(assignment):
        allowed[item].append(resource)
    return assignment, {item: tuple(resources_) for item, resources_ in allowed.items()}, tuple(sorted(items)), tuple(sorted(resources))


def check_orbit_capacity_certificate(formula: CNFFormula, certificate: OrbitCapacityCertificate | dict[str, Any]) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, OrbitCapacityCertificate) else dict(certificate)
    errors: list[str] = []
    if str(data.get("formula_hash", "")).lower() != formula.formula_hash.lower():
        errors.append("FORMULA_HASH_MISMATCH")
    if data.get("drat_claim") != ORBIT_COUNTING_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_CLAIM")
    try:
        assignment, allowed, items, resources = _certificate_assignment_maps(data)
    except (KeyError, TypeError, ValueError) as exc:
        assignment, allowed, items, resources = {}, {}, (), ()
        errors.append(f"ASSIGNMENT_VARIABLE_MAPPING_INVALID:{exc}")

    clause_ids = _clause_id_map(formula)
    clause_by_id = {idx: clause for clause, idx in clause_ids.items()}
    seen_vars = list(assignment.values())
    if len(seen_vars) != len(set(seen_vars)):
        errors.append("ASSIGNMENT_VARIABLE_IDS_NOT_UNIQUE")
    if any(variable not in formula.variables for variable in seen_vars):
        errors.append("ASSIGNMENT_VARIABLE_NOT_IN_FORMULA")

    demand_subset = [str(item) for item in data.get("demand_subset", [])]
    resource_capacities = {str(resource): int(capacity) for resource, capacity in data.get("resource_capacities", {}).items()}
    if any(item not in allowed for item in demand_subset):
        errors.append("DEMAND_SUBSET_ITEM_NOT_IN_ASSIGNMENT_GRID")
    for resource, capacity in resource_capacities.items():
        if capacity < 1:
            errors.append(f"INVALID_CAPACITY:{resource}")
    neighborhood = sorted({resource for item in demand_subset for resource in allowed.get(item, ())})
    if neighborhood != sorted(map(str, data.get("neighborhood_resources", []))):
        errors.append("NEIGHBORHOOD_RESOURCES_MISMATCH")

    alo_ids_by_item = {str(item): int(clause_id) for item, clause_id in data.get("alo_clause_ids_by_item", {}).items()}
    for item in demand_subset:
        expected = _normal_clause_key(assignment[(item, resource)] for resource in allowed.get(item, ()))
        if expected not in clause_ids:
            errors.append(f"ALO_CLAUSE_MISSING:{item}")
        elif alo_ids_by_item.get(item) != clause_ids[expected] or clause_by_id.get(alo_ids_by_item.get(item)) != expected:
            errors.append(f"ALO_CLAUSE_ID_MISMATCH:{item}")

    capacity_ids_by_resource = {
        str(resource): [int(clause_id) for clause_id in ids]
        for resource, ids in data.get("capacity_constraint_ids_by_resource", {}).items()
    }
    for resource in neighborhood:
        if resource not in resource_capacities:
            errors.append(f"CAPACITY_MISSING:{resource}")
            continue
        users = [item for item in items if (item, resource) in assignment]
        cap = resource_capacities[resource]
        expected_ids: list[int] = []
        for limited_group in combinations(users, cap + 1):
            expected = _normal_clause_key(-assignment[(item, resource)] for item in limited_group)
            if expected not in clause_ids:
                errors.append(f"CAPACITY_CLAUSE_MISSING:{resource}:{','.join(limited_group)}")
            else:
                expected_ids.append(clause_ids[expected])
        if sorted(capacity_ids_by_resource.get(resource, [])) != sorted(expected_ids):
            errors.append(f"CAPACITY_CLAUSE_IDS_MISMATCH:{resource}")

    demand_count = len(demand_subset)
    capacity_count = sum(resource_capacities.get(resource, 0) for resource in neighborhood)
    if int(data.get("demand_count", -1)) != demand_count:
        errors.append("DEMAND_COUNT_MISMATCH")
    if int(data.get("capacity_count", -1)) != capacity_count:
        errors.append("CAPACITY_COUNT_MISMATCH")
    if not (demand_count > capacity_count):
        errors.append("NO_HALL_CAPACITY_DEFICIT")
    if data.get("contradiction") is not True or data.get("hall_deficit") is not True:
        errors.append("CONTRADICTION_FLAG_MISSING")
    if data.get("orbit_compression_used") and data.get("orbit_expanded_and_verified") is not True:
        errors.append("ORBIT_COMPRESSION_NOT_EXPANDED")
    if "DRAT" in str(data.get("public_category", "")):
        errors.append("PUBLIC_CATEGORY_FAKE_DRAT")

    status = ORBIT_CAPACITY_CERTIFICATE_VERIFIED if not errors else ORBIT_CAPACITY_CERTIFICATE_FAILED
    return {
        "status": status,
        "checker_status": status,
        "errors": errors,
        "demand_count": demand_count,
        "capacity_count": capacity_count,
        "neighborhood_resources": neighborhood,
        "claim_boundary": "Native Hall/capacity-deficit certificate only; no DRAT proof and no full matching/allocation solver claim.",
    }


def orbit_capacity_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Orbit Capacity Collapse Report",
        "",
        "## Executive Summary",
        "",
        "v2.5 promotes the v2.4-generated ORBIT_COUNTING_COLLAPSE candidate into G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE. It certifies local Hall/capacity deficits for exact generated assignment CNFs. It does not claim a full matching solver, allocation solver, DRAT proof, strictness theorem, or P vs NP progress.",
        "",
        "## Core Distinction From G3",
        "",
        "G3 recognizes standard pigeonhole-style global deficits. G4 searches for a local subset S whose allowed resource neighborhood N(S) has total capacity smaller than |S|. Complete matching examples that duplicate the G3 pigeonhole pattern are marked as duplicate controls, not novel G4 deltas.",
        "",
        "## Target Instances",
        "",
        "| instance | G3 baseline | G4 status | public category | demand | capacity | delta |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['g3_result']}` | `{row['g4_status']}` | `{row['public_category']}` | {row['demand_count']} | {row['capacity_count']} | `{row['g4_delta_status']}` |"
        )
    lines.extend(
        [
            "",
            "## Orbit Compression",
            "",
            "Orbit compression is used only as a discovery/display aid. A trusted native UNSAT row requires the checker to expand the demand subset, neighborhood, ALO clauses, and capacity clauses against the original CNF.",
            "",
            "## Operator Delta Summary",
            "",
            stable_json(delta),
            "## Theorem Candidate Boundary",
            "",
            "G4 bounded delta evidence is empirical evidence, not a theorem. The Hall/capacity certificate has a formal proof-sketch shape for the provided subset S, but no lower-bound theorem against G3 is claimed.",
            "",
            "## Forbidden Claims",
            "",
            "- no P vs NP progress claim",
            "- no polynomial-time SAT claim",
            "- no full matching/allocation solver claim",
            "- no DRAT verification claim",
            "- no G4 strictness theorem claim",
            "- no HARD or UNKNOWN statuses",
            "",
        ]
    )
    return "\n".join(lines)


def run_orbit_capacity_lab(
    *,
    instances: Iterable[str],
    out_root: str | Path,
    strict: bool = False,
    zip_path: str | Path | None = None,
    max_subset_size: int = 6,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cert_root = root / "certificates"
    cnf_root = root / "original_cnf"
    cert_root.mkdir(parents=True, exist_ok=True)
    cnf_root.mkdir(parents=True, exist_ok=True)

    selected_ids = list(instances)
    rows: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    checker_rows: list[dict[str, Any]] = []
    for instance_id in selected_ids:
        instance = make_orbit_capacity_instance(instance_id)
        deficit = find_hall_deficit(instance, max_subset_size=max_subset_size)
        certificate = build_orbit_capacity_certificate(instance, max_subset_size=max_subset_size)
        check = check_orbit_capacity_certificate(instance.formula, certificate)
        cert_path = cert_root / f"{instance_id}_orbit_capacity_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        cert_path.write_text(stable_json(certificate.to_dict()), encoding="utf-8", newline="\n")
        cnf_path.write_text(instance.formula.canonical_dimacs(), encoding="utf-8", newline="\n")
        g3_result = DUPLICATE_OF_G3_PIGEONHOLE_PATTERN if instance.duplicate_of_g3 else "CARDINALITY_DIAGNOSTIC_ONLY"
        if instance.sat_control:
            g3_result = "NO_COLLAPSE_FOUND"
        novel_delta = (
            check["status"] == ORBIT_CAPACITY_CERTIFICATE_VERIFIED
            and not instance.duplicate_of_g3
            and not instance.sat_control
            and not instance.incomplete_structure
        )
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "g3_result": g3_result,
            "g4_grammar": "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            "g4_status": certificate.status,
            "public_category": certificate.public_category,
            "certification_level": certificate.certification_level,
            "checker_status": check["status"],
            "demand_subset": certificate.demand_subset,
            "neighborhood_resources": certificate.neighborhood_resources,
            "demand_count": certificate.demand_count,
            "capacity_count": certificate.capacity_count,
            "g3_duplicate_control": instance.duplicate_of_g3,
            "sat_control": instance.sat_control,
            "incomplete_structure": instance.incomplete_structure,
            "g4_delta_status": certificate.g4_delta_status,
            "novel_g4_delta": novel_delta,
            "drat_claim": certificate.drat_claim,
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
            "orbit_expanded_and_verified": certificate.orbit_expanded_and_verified,
        }
        rows.append(row)
        certificates.append(certificate.to_dict())
        traces.append({"instance_id": instance_id, "deficit_trace": deficit, "instance": instance.to_dict()})
        checker_rows.append({"instance_id": instance_id, **check})

    local_certified = [row for row in rows if row["novel_g4_delta"]]
    duplicate_controls = [row for row in rows if row["g3_duplicate_control"]]
    balanced_controls = [row for row in rows if row["sat_control"]]
    delta = {
        "operator_added": "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
        "promoted_candidate": "ORBIT_COUNTING_COLLAPSE",
        "instances_total": len(rows),
        "native_certified": sum(1 for row in rows if row["checker_status"] == ORBIT_CAPACITY_CERTIFICATE_VERIFIED),
        "novel_local_hall_deltas": len(local_certified),
        "duplicate_g3_controls": len(duplicate_controls),
        "balanced_controls_without_contradiction": sum(1 for row in balanced_controls if row["public_category"] == "NO_COLLAPSE_FOUND"),
        "fake_drat_claims": sum(1 for row in rows if row["drat_claim"] != ORBIT_COUNTING_DRAT_NOT_CLAIMED),
        "strictness_status": "EMPIRICAL_EVIDENCE_NOT_THEOREM",
        "claim_boundary": "G4 native Hall/capacity-deficit evidence only; no full matching/allocation solver claim and no DRAT claim.",
    }
    theorem_queue = [
        {
            "id": "TC-012",
            "name": "Hall/Capacity Native Certification Candidate",
            "status": "FORMAL_PROOF_SKETCH",
            "statement": "For exact assignment CNFs with ALO demand constraints and exact capacity constraints, a provided subset S with |S| > capacity(N(S)) yields a native UNSAT certificate checkable against the original CNF.",
            "forbidden_interpretations": ["not a full matching solver", "not a DRAT proof", "not P vs NP progress"],
        },
        {
            "id": "TC-013",
            "name": "G4 Orbit-Capacity Strictness Candidate",
            "status": "EMPIRICAL_EVIDENCE_NOT_THEOREM",
            "statement": "Local Hall-deficit formulas are certified by G4 while G3's standard pigeonhole/cardinality recognizer does not count them as its standard complete-grid pattern.",
            "forbidden_interpretations": ["not a strictness theorem", "no lower bound against G3 is proved"],
        },
        {
            "id": "TC-014",
            "name": "Operator Genesis Success Candidate",
            "status": "EMPIRICAL_EVIDENCE",
            "statement": "The v2.4-generated ORBIT_COUNTING_COLLAPSE candidate was promoted to a v2.5 prototype with native certificate checks and bounded operator-delta evidence.",
            "forbidden_interpretations": ["generated operator is not a theorem", "not a broad solver claim"],
        },
    ]

    payloads = {
        "orbit_capacity_certificates.json": {"certificates": certificates},
        "hall_deficit_detection_trace.json": {"traces": traces},
        "orbit_capacity_checker_summary.json": {"checks": checker_rows},
        "g4_operator_delta_summary.json": delta,
        "theorem_candidates.json": {"theorem_candidates": theorem_queue},
        "manifest.json": {
            "version": "2.5",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "instances": selected_ids,
            "strict": strict,
            "claim_boundary": "native Hall/capacity-deficit certificates only; no DRAT or P vs NP claim",
        },
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    _write_orbit_capacity_csv(root / "orbit_capacity_structure_summary.csv", rows)
    (root / "ORBIT_CAPACITY_COLLAPSE_REPORT.md").write_text(orbit_capacity_report(rows, delta), encoding="utf-8", newline="\n")
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "orbit_capacity_certificates": certificates,
        "orbit_capacity_rows": rows,
        "hall_deficit_detection_trace": traces,
        "orbit_capacity_checker_summary": checker_rows,
        "g4_operator_delta_summary": delta,
        "theorem_candidates": theorem_queue,
    }


def _write_orbit_capacity_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    headers = [
        "instance_id",
        "g3_result",
        "g4_status",
        "public_category",
        "checker_status",
        "demand_count",
        "capacity_count",
        "g3_duplicate_control",
        "g4_delta_status",
        "novel_g4_delta",
    ]
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(header, "")).replace(",", ";") for header in headers))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora Operator Genesis Engine")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--families",
        nargs="+",
        default=["pigeonhole", "parity", "graph-coloring", "clique", "subset-sum", "adversarial-mixed", "random-structured"],
    )
    run_parser.add_argument("--out-root", default="outputs/v2.4-operator-genesis")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--zip", default="witnora-core-v2.4-operator-genesis.zip")
    orbit_parser = sub.add_parser("run-orbit-capacity-lab")
    orbit_parser.add_argument(
        "--instances",
        nargs="+",
        default=[
            "hall_local_3_2",
            "hall_local_4_3",
            "hall_local_5_4",
            "complete_match_3_2",
            "complete_match_4_3",
            "hall_balanced_3_3_sat_control",
            "capacity_balanced_4_4_no_contradiction",
        ],
    )
    orbit_parser.add_argument("--out-root", default="outputs/v2.5-orbit-capacity-counting")
    orbit_parser.add_argument("--strict", action="store_true")
    orbit_parser.add_argument("--max-subset-size", type=int, default=6)
    orbit_parser.add_argument("--zip", default="witnora-core-v2.5-orbit-capacity-counting.zip")
    check_orbit_parser = sub.add_parser("check-orbit-capacity-cert")
    check_orbit_parser.add_argument("--cnf", required=True)
    check_orbit_parser.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_operator_genesis(families=args.families, out_root=args.out_root, strict=args.strict, zip_path=args.zip)
        print(
            stable_json(
                {
                    "out_root": args.out_root,
                    "zip": args.zip,
                    "zip_sha256": result["zip_sha256"],
                    "summary": {
                        "fingerprint_count": len(result["obstruction_fingerprints"]),
                        "candidate_count": len(result["generated_operator_candidates"]),
                    },
                }
            )
        )
        return 0
    if args.command == "run-orbit-capacity-lab":
        result = run_orbit_capacity_lab(
            instances=args.instances,
            out_root=args.out_root,
            strict=args.strict,
            zip_path=args.zip,
            max_subset_size=args.max_subset_size,
        )
        print(
            stable_json(
                {
                    "out_root": args.out_root,
                    "zip": args.zip,
                    "zip_sha256": result["zip_sha256"],
                    "summary": result["g4_operator_delta_summary"],
                }
            )
        )
        return 0
    if args.command == "check-orbit-capacity-cert":
        formula = load_dimacs(args.cnf)
        data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        print(stable_json(check_orbit_capacity_certificate(formula, data)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
