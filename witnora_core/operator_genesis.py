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
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, Clause

GENESIS_VERSION = "2.4"

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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
