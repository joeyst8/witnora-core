"""Self-expanding collapse planner certificates.

v2.19 is a planning layer over the existing G0-G11 operator hierarchy. A plan
is not execution, not SAT/UNSAT evidence, not DRAT, not a proof, and not a
theorem. The checker accepts only structurally valid, claim-boundary-safe plans
that explicitly require future certified operator execution.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula
from .dimacs import load_dimacs
from .obstruction_dual import (
    CIRCUIT_PROJECTION_SIGNAL,
    COMPOSED_OBSTRUCTION,
    GRAPH_SEPARATOR_OBSTRUCTION,
    NEAR_AFFINE_NOT_EXACT,
    NEAR_CARDINALITY_INCOMPLETE,
    NO_CONFIDENT_FINGERPRINT,
    PROOF_MOTIF_NEAR_MISS,
    sha256_file,
    stable_json,
)


VERSION = "2.19"

G12_GRAMMAR = "G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE"

COLLAPSE_PLANNER_OBSTRUCTION_LOADED = "COLLAPSE_PLANNER_OBSTRUCTION_LOADED"
COLLAPSE_PLANNER_OPERATOR_PORTFOLIO_LOADED = "COLLAPSE_PLANNER_OPERATOR_PORTFOLIO_LOADED"
COLLAPSE_PLANNER_PLAN_PROPOSED = "COLLAPSE_PLANNER_PLAN_PROPOSED"
COLLAPSE_PLANNER_PLAN_VERIFIED = "COLLAPSE_PLANNER_PLAN_VERIFIED"
COLLAPSE_PLANNER_PLAN_REJECTED = "COLLAPSE_PLANNER_PLAN_REJECTED"
COLLAPSE_PLANNER_MISSING_OPERATOR_HYPOTHESIS_CREATED = "COLLAPSE_PLANNER_MISSING_OPERATOR_HYPOTHESIS_CREATED"
COLLAPSE_PLANNER_EXECUTION_REQUIRED = "COLLAPSE_PLANNER_EXECUTION_REQUIRED"
COLLAPSE_PLANNER_DIAGNOSTIC_ONLY = "COLLAPSE_PLANNER_DIAGNOSTIC_ONLY"
COLLAPSE_PLANNER_NO_SAT_UNSAT_CLAIM = "COLLAPSE_PLANNER_NO_SAT_UNSAT_CLAIM"
G12_COLLAPSE_PLAN_NATIVE_CERTIFIED = "G12_COLLAPSE_PLAN_NATIVE_CERTIFIED"

FINITE_PLANNER_CERTIFICATE_VERIFIED = "FINITE_PLANNER_CERTIFICATE_VERIFIED"

OPERATOR_SEQUENCE_PLAN = "OPERATOR_SEQUENCE_PLAN"
MISSING_OPERATOR_HYPOTHESIS_PLAN = "MISSING_OPERATOR_HYPOTHESIS_PLAN"
REVIEW_OR_THEOREMIZATION_PLAN = "REVIEW_OR_THEOREMIZATION_PLAN"

SAT_WITNESS = "SAT_WITNESS"
UNSAT_PRESERVATION = "UNSAT_PRESERVATION"
EQUI_SAT = "EQUI_SAT"
NATIVE_ONLY = "NATIVE_ONLY"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

PLAN_ONLY = "PLAN_ONLY"
EXECUTION_REQUIRED = "EXECUTION_REQUIRED"

DRAT_NOT_CLAIMED = "COLLAPSE_PLANNER_DRAT_NOT_CLAIMED"

RECOGNIZED_FINGERPRINTS = {
    COMPOSED_OBSTRUCTION,
    CIRCUIT_PROJECTION_SIGNAL,
    PROOF_MOTIF_NEAR_MISS,
    GRAPH_SEPARATOR_OBSTRUCTION,
    NEAR_AFFINE_NOT_EXACT,
    NEAR_CARDINALITY_INCOMPLETE,
    NO_CONFIDENT_FINGERPRINT,
}

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "planner solves sat",
    "planner proves sat",
    "planner proves unsat",
    "drat verified",
    "theorem proven",
    "hierarchy completeness",
    "p vs np progress",
    "polynomial-time sat",
    "universal collapse planning",
    "all obstructions covered",
}


@dataclass(frozen=True)
class PlannerInstance:
    instance_id: str
    obstruction_fingerprint: str
    structural_features: dict[str, Any]
    formula: CNFFormula
    family: str
    description: str
    control_kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "formula_hash": self.formula.formula_hash,
            "obstruction_fingerprint": self.obstruction_fingerprint,
            "structural_features": self.structural_features,
            "description": self.description,
            "control_kind": self.control_kind,
        }


@dataclass(frozen=True)
class OperatorPortfolioItem:
    operator_name: str
    grammar_id: str
    certificate_type: str
    supports_sat_lift: bool
    supports_unsat_preservation: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CollapsePlanCertificate:
    type: str
    instance_id: str
    formula_hash: str
    formula_summary: dict[str, Any]
    source_obstruction_record: dict[str, Any]
    planner_version: str
    operator_portfolio_hash: str
    available_operators: list[dict[str, Any]]
    proposed_plans: list[dict[str, Any]]
    selected_plan_id: str
    plan_selection_rationale: str
    missing_operator_hypotheses: list[dict[str, Any]]
    execution_requirements: list[str]
    expected_certificate_chain: list[dict[str, Any]]
    expected_lift_obligations: list[str]
    expected_failure_modes: list[str]
    evidence_grade: str
    drat_claim: str
    claimed_result: str
    status_audit: list[str]
    execution_status: str
    status: str
    claim_boundary: str
    checker_status: str
    public_category: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data), encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _sha256_payload(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def _make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return sha256_file(target)


def _formula_summary(formula: CNFFormula, features: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "formula_hash": formula.formula_hash,
        "variable_count": formula.num_vars,
        "clause_count": formula.num_clauses,
        "structural_features": dict(features or {}),
    }


def operator_portfolio() -> list[OperatorPortfolioItem]:
    return [
        OperatorPortfolioItem("EXACT_XOR", "G1_XOR", "XOR_NATIVE_OR_DRAT_CERTIFICATE", True, True, "XOR certificate required; no planner execution claim."),
        OperatorPortfolioItem("SYMMETRY_CERTIFIED", "G2_SYMMETRY_CERTIFIED", "SYMMETRY_CERTIFICATE", True, False, "Witness reconstruction must verify original CNF."),
        OperatorPortfolioItem("PIGEONHOLE_CARDINALITY", "G3_SYMMETRY_CARDINALITY_CERTIFIED", "PIGEONHOLE_COUNTING_CERTIFICATE", False, True, "Native counting certificate only."),
        OperatorPortfolioItem("ORBIT_CAPACITY_COUNTING", "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "ORBIT_CAPACITY_CERTIFICATE", False, True, "Native Hall/capacity certificate only."),
        OperatorPortfolioItem("HIGH_ARITY_AFFINE_RESIDUE", "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "AFFINE_RESIDUE_GF2_CERTIFICATE", True, True, "Exact affine extraction only."),
        OperatorPortfolioItem("PROOF_MOTIF_COMPRESSION", "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE", "PROOF_MOTIF_COMPRESSION_CERTIFICATE", False, True, "Every exact motif reuse must verify."),
        OperatorPortfolioItem("GRAPH_SEPARATOR_LIFT", "G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "GRAPH_SEPARATOR_LIFT_CERTIFICATE", True, True, "Separator assignments and cover obligations must verify."),
        OperatorPortfolioItem("COMPOSED_OPERATOR_ORCHESTRATION", "G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE", "COMPOSED_ORCHESTRATION_CERTIFICATE", True, True, "Every formula handoff and step certificate must verify."),
        OperatorPortfolioItem("CIRCUIT_PROJECTION_LIFT", "G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE", "CIRCUIT_PROJECTION_LIFT_CERTIFICATE", True, True, "Exact definitional projection only."),
        OperatorPortfolioItem("PROOF_MOTIF_GENERALIZATION_CHECKER", "G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE", "PROOF_MOTIF_GENERALIZATION_CERTIFICATE", False, True, "Every generalized reuse must expand and verify."),
    ]


def _portfolio_dict() -> dict[str, dict[str, Any]]:
    return {item.operator_name: item.to_dict() for item in operator_portfolio()}


def _portfolio_hash(items: list[dict[str, Any]]) -> str:
    return _sha256_payload(items)


def _operator_step(
    *,
    step_id: str,
    operator_name: str,
    expected_input_features: list[str],
    expected_output_features: list[str],
    preservation_required: str,
    handoff_requirements: list[str] | None = None,
    lift_requirements: list[str] | None = None,
) -> dict[str, Any]:
    portfolio = _portfolio_dict()
    item = portfolio[operator_name]
    return {
        "step_id": step_id,
        "operator_name": operator_name,
        "grammar_id": item["grammar_id"],
        "expected_input_features": expected_input_features,
        "expected_output_features": expected_output_features,
        "expected_certificate_type": item["certificate_type"],
        "preservation_required": preservation_required,
        "handoff_requirements": handoff_requirements
        or [
            "input formula hash must match prior step output",
            "output formula hash must be recorded before next step",
            "claim boundary must be propagated",
        ],
        "lift_requirements": lift_requirements
        or [
            "future execution certificate must define witness/proof lift",
            "final result must be checked against original CNF or preserved by native certificates",
        ],
        "claim_boundary": item["claim_boundary"],
    }


def make_planner_instance(instance_id: str) -> PlannerInstance:
    specs: dict[str, dict[str, Any]] = {
        "composed_obstruction_plan": {
            "fingerprint": COMPOSED_OBSTRUCTION,
            "features": {"subsignals": ["circuit", "affine", "separator", "near_motif"], "planner_target": "orchestration"},
            "clauses": [[1, 2], [-1, 3], [-2, -3]],
            "family": "composed-obstruction",
            "description": "Composed obstruction row requiring an orchestration plan.",
        },
        "circuit_projection_plan": {
            "fingerprint": CIRCUIT_PROJECTION_SIGNAL,
            "features": {"projected_core_signal": "affine", "has_definitional_gates": True},
            "clauses": [[1, 2], [-1, 3], [-3, 4]],
            "family": "circuit-projection",
            "description": "Projection should be planned before affine residue reasoning.",
        },
        "proof_motif_near_plan": {
            "fingerprint": PROOF_MOTIF_NEAR_MISS,
            "features": {"near_motif_sites": 5, "non_identical_reuse": True},
            "clauses": [[1, 2, 3], [-1], [-2], [-3]],
            "family": "proof-motif-near",
            "description": "Near proof motifs require the G11 checker.",
        },
        "graph_separator_plan": {
            "fingerprint": GRAPH_SEPARATOR_OBSTRUCTION,
            "features": {"component_signals": ["affine", "capacity", "near_motif"], "separator_size": 2},
            "clauses": [[1, 2], [-1, 3], [-2, 4], [-3, -4]],
            "family": "graph-separator",
            "description": "Separator plan with component-level subplans.",
        },
        "near_affine_missing_operator_plan": {
            "fingerprint": NEAR_AFFINE_NOT_EXACT,
            "features": {"near_affine_rows": 4, "exact_extraction_failed": True},
            "clauses": [[1, 2, 3], [-1, -2], [2, -3]],
            "family": "near-affine",
            "description": "Near-affine row where current exact operators should not overclaim.",
        },
        "near_cardinality_missing_operator_plan": {
            "fingerprint": NEAR_CARDINALITY_INCOMPLETE,
            "features": {"alo_present": True, "amo_incomplete": True},
            "clauses": [[1, 2], [-1, -3], [-2, -4]],
            "family": "near-cardinality",
            "description": "Incomplete cardinality row requiring a missing PB/certificate hypothesis.",
        },
        "no_confident_fingerprint_plan": {
            "fingerprint": NO_CONFIDENT_FINGERPRINT,
            "features": {"confidence": "low", "next_step": "vocabulary_expansion"},
            "clauses": [[1, -2, 3], [-1, 4], [-3, -4]],
            "family": "no-confident-fingerprint",
            "description": "No confident fingerprint; planner should emit review/vocabulary plan.",
        },
        "fake_execution_claim_reject": {"base": "composed_obstruction_plan", "control": "fake_execution"},
        "fake_sat_unsat_claim_reject": {"base": "circuit_projection_plan", "control": "fake_sat_unsat"},
        "fake_drat_claim_reject": {"base": "proof_motif_near_plan", "control": "fake_drat"},
        "unknown_operator_reject": {"base": "composed_obstruction_plan", "control": "unknown_operator"},
        "missing_certificate_type_reject": {"base": "circuit_projection_plan", "control": "missing_certificate_type"},
        "missing_handoff_requirement_reject": {"base": "graph_separator_plan", "control": "missing_handoff"},
        "missing_unsat_preservation_requirement_reject": {"base": "graph_separator_plan", "control": "missing_unsat_preservation"},
        "diagnostic_step_as_proof_reject": {"base": "no_confident_fingerprint_plan", "control": "diagnostic_as_proof"},
        "hard_unknown_status_reject": {"base": "near_affine_missing_operator_plan", "control": "hard_unknown_status"},
        "tamper_reject": {"base": "proof_motif_near_plan", "control": "tamper"},
    }
    if instance_id not in specs:
        raise ValueError(f"unsupported planner instance id: {instance_id}")
    spec = specs[instance_id]
    if "base" in spec:
        base = make_planner_instance(str(spec["base"]))
        return PlannerInstance(
            instance_id=instance_id,
            obstruction_fingerprint=base.obstruction_fingerprint,
            structural_features=base.structural_features,
            formula=base.formula,
            family=base.family,
            description=f"Negative control derived from {base.instance_id}.",
            control_kind=str(spec["control"]),
        )
    return PlannerInstance(
        instance_id=instance_id,
        obstruction_fingerprint=str(spec["fingerprint"]),
        structural_features=dict(spec["features"]),
        formula=CNFFormula.from_raw_clauses(spec["clauses"]),
        family=str(spec["family"]),
        description=str(spec["description"]),
    )


def _source_obstruction_record(instance: PlannerInstance) -> dict[str, Any]:
    trace = {
        "features": instance.structural_features,
        "bounded_replay_scope": "G0_G11_DIAGNOSTIC_REPLAY_ONLY",
        "no_lower_bound_claim": True,
    }
    return {
        "obstruction_id": f"obs_{instance.instance_id}",
        "obstruction_fingerprint": instance.obstruction_fingerprint,
        "source_module": "witnora_core.obstruction_dual",
        "evidence_hash": _sha256_payload(trace),
        "diagnostic_trace": trace,
    }


def _missing_operator(name: str, obstruction: str, certificate_type: str, controls: list[str]) -> dict[str, Any]:
    return {
        "proposed_operator_name": name,
        "obstruction_addressed": obstruction,
        "expected_certificate_type": certificate_type,
        "minimal_soundness_obligations": [
            "define exact accepted input structure",
            "define native certificate schema",
            "define independent checker",
            "reject incomplete or polluted evidence",
            "separate planning from execution",
        ],
        "required_negative_controls": controls,
    }


def _plan_for_instance(instance: PlannerInstance) -> dict[str, Any]:
    fp = instance.obstruction_fingerprint
    features = instance.structural_features
    if fp == COMPOSED_OBSTRUCTION:
        steps = [
            _operator_step(step_id="s1", operator_name="CIRCUIT_PROJECTION_LIFT", expected_input_features=["definitional circuit front-end"], expected_output_features=["projected core"], preservation_required=EQUI_SAT),
            _operator_step(step_id="s2", operator_name="HIGH_ARITY_AFFINE_RESIDUE", expected_input_features=["affine core"], expected_output_features=["native affine certificate candidate"], preservation_required=UNSAT_PRESERVATION),
            _operator_step(step_id="s3", operator_name="GRAPH_SEPARATOR_LIFT", expected_input_features=["separator signal"], expected_output_features=["component certificate plan"], preservation_required=EQUI_SAT),
            _operator_step(step_id="s4", operator_name="PROOF_MOTIF_GENERALIZATION_CHECKER", expected_input_features=["near motif component"], expected_output_features=["generalized macro-proof candidate"], preservation_required=UNSAT_PRESERVATION),
            _operator_step(step_id="s5", operator_name="COMPOSED_OPERATOR_ORCHESTRATION", expected_input_features=["checked substep certificates"], expected_output_features=["future composed certificate"], preservation_required=NATIVE_ONLY),
        ]
        return {
            "plan_id": "plan_composed_orchestration",
            "plan_type": OPERATOR_SEQUENCE_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": steps,
            "missing_operator_hypothesis": None,
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "MEDIUM_DIAGNOSTIC_ONLY",
            "rationale": "Composed obstruction requires a future G9 certificate chain with checked substep certificates.",
            "forbidden_claims": ["no execution claim", "no SAT/UNSAT claim", "no DRAT claim", "no theorem claim"],
        }
    if fp == CIRCUIT_PROJECTION_SIGNAL:
        downstream = "HIGH_ARITY_AFFINE_RESIDUE"
        if features.get("projected_core_signal") == "capacity":
            downstream = "ORBIT_CAPACITY_COUNTING"
        steps = [
            _operator_step(step_id="s1", operator_name="CIRCUIT_PROJECTION_LIFT", expected_input_features=["exact definitional gates"], expected_output_features=["projected core"], preservation_required=EQUI_SAT),
            _operator_step(step_id="s2", operator_name=downstream, expected_input_features=[str(features.get("projected_core_signal", "core signal"))], expected_output_features=["downstream native certificate candidate"], preservation_required=UNSAT_PRESERVATION),
        ]
        return {
            "plan_id": "plan_circuit_projection_then_core",
            "plan_type": OPERATOR_SEQUENCE_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": steps,
            "missing_operator_hypothesis": None,
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "HIGH_DIAGNOSTIC_ONLY",
            "rationale": "Exact projection should be attempted before native core reasoning.",
            "forbidden_claims": ["no execution claim", "no SAT/UNSAT claim", "no DRAT claim", "no theorem claim"],
        }
    if fp == PROOF_MOTIF_NEAR_MISS:
        return {
            "plan_id": "plan_proof_motif_generalization",
            "plan_type": OPERATOR_SEQUENCE_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": [
                _operator_step(step_id="s1", operator_name="PROOF_MOTIF_GENERALIZATION_CHECKER", expected_input_features=["near motif sites", "non-identical reuse"], expected_output_features=["generalized template certificate candidate"], preservation_required=UNSAT_PRESERVATION)
            ],
            "missing_operator_hypothesis": None,
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "HIGH_DIAGNOSTIC_ONLY",
            "rationale": "G11 is the promoted checker for near-motif rows; exact G6 is tried first only on duplicate exact motifs.",
            "forbidden_claims": ["no proof claim until G11 certificate verifies", "no DRAT claim", "no theorem claim"],
        }
    if fp == GRAPH_SEPARATOR_OBSTRUCTION:
        return {
            "plan_id": "plan_separator_with_component_subplans",
            "plan_type": OPERATOR_SEQUENCE_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": [
                _operator_step(step_id="s1", operator_name="GRAPH_SEPARATOR_LIFT", expected_input_features=["small separator"], expected_output_features=["conditioned components"], preservation_required=EQUI_SAT),
                _operator_step(step_id="s2", operator_name="HIGH_ARITY_AFFINE_RESIDUE", expected_input_features=["affine component"], expected_output_features=["component affine certificate candidate"], preservation_required=UNSAT_PRESERVATION),
                _operator_step(step_id="s3", operator_name="ORBIT_CAPACITY_COUNTING", expected_input_features=["capacity component"], expected_output_features=["component capacity certificate candidate"], preservation_required=UNSAT_PRESERVATION),
                _operator_step(step_id="s4", operator_name="PROOF_MOTIF_GENERALIZATION_CHECKER", expected_input_features=["near motif component"], expected_output_features=["component macro-proof candidate"], preservation_required=UNSAT_PRESERVATION),
            ],
            "missing_operator_hypothesis": None,
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "MEDIUM_DIAGNOSTIC_ONLY",
            "rationale": "Separator decomposition requires future component certificates and separator lift obligations.",
            "forbidden_claims": ["no separator execution claim", "no SAT/UNSAT claim", "no theorem claim"],
        }
    if fp == NEAR_AFFINE_NOT_EXACT:
        return {
            "plan_id": "plan_missing_robust_affine_completion",
            "plan_type": MISSING_OPERATOR_HYPOTHESIS_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": [],
            "missing_operator_hypothesis": _missing_operator(
                "ROBUST_AFFINE_COMPLETION_OR_REJECTION",
                fp,
                "ROBUST_AFFINE_COMPLETION_CERTIFICATE",
                ["incomplete affine reject", "polluted affine reject", "false completion reject"],
            ),
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "MEDIUM_DIAGNOSTIC_ONLY",
            "rationale": "Existing exact affine operators should not accept near-affine evidence without a new checker.",
            "forbidden_claims": ["missing operator is not implemented", "no SAT/UNSAT claim", "no theorem claim"],
        }
    if fp == NEAR_CARDINALITY_INCOMPLETE:
        return {
            "plan_id": "plan_missing_cardinality_completion",
            "plan_type": MISSING_OPERATOR_HYPOTHESIS_PLAN,
            "triggering_fingerprints": [fp],
            "operator_sequence": [],
            "missing_operator_hypothesis": _missing_operator(
                "CARDINALITY_COMPLETION_OR_PB_CERTIFICATE",
                fp,
                "CARDINALITY_COMPLETION_OR_PB_CERTIFICATE",
                ["missing AMO reject", "polluted PB reject", "wrong capacity reject"],
            ),
            "expected_execution_result": EXECUTION_REQUIRED,
            "plan_confidence": "MEDIUM_DIAGNOSTIC_ONLY",
            "rationale": "Incomplete cardinality evidence needs a future PB/certification operator rather than a fake collapse.",
            "forbidden_claims": ["missing operator is not implemented", "no SAT/UNSAT claim", "no theorem claim"],
        }
    return {
        "plan_id": "plan_fingerprint_vocabulary_review",
        "plan_type": REVIEW_OR_THEOREMIZATION_PLAN,
        "triggering_fingerprints": [NO_CONFIDENT_FINGERPRINT],
        "operator_sequence": [],
        "missing_operator_hypothesis": _missing_operator(
            "FINGERPRINT_VOCABULARY_EXPANSION",
            NO_CONFIDENT_FINGERPRINT,
            "FINGERPRINT_REVIEW_CERTIFICATE",
            ["low-confidence fingerprint reject", "unsupported feature reject"],
        ),
        "expected_execution_result": EXECUTION_REQUIRED,
        "plan_confidence": "LOW_DIAGNOSTIC_ONLY",
        "rationale": "No confident fingerprint exists; expand vocabulary or review theoremization gaps before execution.",
        "forbidden_claims": ["no operator execution claim", "no SAT/UNSAT claim", "no theorem claim"],
    }


def build_collapse_plan_certificate(instance: PlannerInstance) -> CollapsePlanCertificate:
    portfolio = [item.to_dict() for item in operator_portfolio()]
    selected = _plan_for_instance(instance)
    proposed = [selected]
    hypotheses = [selected["missing_operator_hypothesis"]] if selected.get("missing_operator_hypothesis") else []
    certificate_chain = [
        {
            "step_id": step["step_id"],
            "operator_name": step["operator_name"],
            "expected_certificate_type": step["expected_certificate_type"],
            "execution_status": EXECUTION_REQUIRED,
        }
        for step in selected.get("operator_sequence", [])
    ]
    if selected["plan_type"] == MISSING_OPERATOR_HYPOTHESIS_PLAN or selected["plan_type"] == REVIEW_OR_THEOREMIZATION_PLAN:
        certificate_chain.append(
            {
                "step_id": "future_operator",
                "operator_name": selected["missing_operator_hypothesis"]["proposed_operator_name"],
                "expected_certificate_type": selected["missing_operator_hypothesis"]["expected_certificate_type"],
                "execution_status": EXECUTION_REQUIRED,
            }
        )
    cert = CollapsePlanCertificate(
        type="COLLAPSE_PLAN_CERTIFICATE",
        instance_id=instance.instance_id,
        formula_hash=instance.formula.formula_hash,
        formula_summary=_formula_summary(instance.formula, instance.structural_features),
        source_obstruction_record=_source_obstruction_record(instance),
        planner_version=VERSION,
        operator_portfolio_hash=_portfolio_hash(portfolio),
        available_operators=portfolio,
        proposed_plans=proposed,
        selected_plan_id=str(selected["plan_id"]),
        plan_selection_rationale=str(selected["rationale"]),
        missing_operator_hypotheses=hypotheses,
        execution_requirements=[
            COLLAPSE_PLANNER_EXECUTION_REQUIRED,
            "future operator certificates must be produced and checked before any SAT/UNSAT result is claimed",
        ],
        expected_certificate_chain=certificate_chain,
        expected_lift_obligations=[
            "SAT witness lift obligations must be supplied by future execution if SAT is claimed later",
            "UNSAT preservation obligations must be supplied by future execution if UNSAT is claimed later",
            "diagnostic-only steps cannot be used as proof",
        ],
        expected_failure_modes=[
            "operator preconditions not met",
            "certificate checker rejects a future step",
            "formula handoff missing or mismatched",
            "missing operator remains unimplemented",
        ],
        evidence_grade=FINITE_PLANNER_CERTIFICATE_VERIFIED,
        drat_claim=DRAT_NOT_CLAIMED,
        claimed_result="PLAN_ONLY_NO_RESULT",
        status_audit=[
            COLLAPSE_PLANNER_NO_SAT_UNSAT_CLAIM,
            COLLAPSE_PLANNER_EXECUTION_REQUIRED,
        ],
        execution_status=EXECUTION_REQUIRED,
        status=COLLAPSE_PLANNER_PLAN_PROPOSED,
        claim_boundary="Plan certificate only; execution required; no SAT/UNSAT, no DRAT, no theorem, no completeness, and no P-vs-NP claim.",
        checker_status="NOT_RUN",
        public_category=G12_COLLAPSE_PLAN_NATIVE_CERTIFIED,
    )
    data = cert.to_dict()
    data = _apply_control_tamper(instance, data)
    check = check_collapse_plan_certificate(instance.formula, data)
    data["checker_status"] = check["status"]
    data["status"] = check["status"]
    if check["status"] != COLLAPSE_PLANNER_PLAN_VERIFIED:
        data["public_category"] = COLLAPSE_PLANNER_PLAN_REJECTED
    return CollapsePlanCertificate(**data)


def _apply_control_tamper(instance: PlannerInstance, data: dict[str, Any]) -> dict[str, Any]:
    kind = instance.control_kind
    if not kind:
        return data
    if kind == "fake_execution":
        data["execution_status"] = "EXECUTED"
    elif kind == "fake_sat_unsat":
        data["claimed_result"] = "SAT"
        data["public_category"] = "SAT_COLLAPSE_PLANNER_FAKE"
    elif kind == "fake_drat":
        data["drat_claim"] = "DRAT_VERIFIED"
    elif kind == "unknown_operator":
        data["proposed_plans"][0]["operator_sequence"][0]["operator_name"] = "UNRECOGNIZED_OPERATOR"
    elif kind == "missing_certificate_type":
        data["proposed_plans"][0]["operator_sequence"][0]["expected_certificate_type"] = ""
    elif kind == "missing_handoff":
        data["proposed_plans"][0]["operator_sequence"][0]["handoff_requirements"] = []
    elif kind == "missing_unsat_preservation":
        for step in data["proposed_plans"][0].get("operator_sequence", []):
            if step.get("preservation_required") == UNSAT_PRESERVATION:
                step["lift_requirements"] = []
                break
    elif kind == "diagnostic_as_proof":
        data["proposed_plans"][0]["plan_type"] = OPERATOR_SEQUENCE_PLAN
        data["proposed_plans"][0]["operator_sequence"] = [
            _operator_step(
                step_id="s1",
                operator_name="PROOF_MOTIF_GENERALIZATION_CHECKER",
                expected_input_features=["diagnostic-only signal"],
                expected_output_features=["none"],
                preservation_required=DIAGNOSTIC_ONLY,
            )
        ]
    elif kind == "hard_unknown_status":
        data["status_audit"] = ["UNKNOWN"]
    elif kind == "tamper":
        data["formula_hash"] = "0" * 64
    return data


def _known_operator_by_name(portfolio: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("operator_name")): item for item in portfolio}


def _scan_for_forbidden_status(data: Any, errors: list[str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "obstruction_fingerprint" and value == NO_CONFIDENT_FINGERPRINT:
                continue
            _scan_for_forbidden_status(value, errors)
    elif isinstance(data, list):
        for item in data:
            _scan_for_forbidden_status(item, errors)
    elif isinstance(data, str) and data in FORBIDDEN_STATUS_VALUES:
        errors.append(f"FORBIDDEN_STATUS:{data}")


def check_collapse_plan_certificate(formula: CNFFormula, certificate: CollapsePlanCertificate | dict[str, Any]) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, CollapsePlanCertificate) else dict(certificate)
    errors: list[str] = []
    if data.get("type") != "COLLAPSE_PLAN_CERTIFICATE":
        errors.append("CERTIFICATE_TYPE_MISMATCH")
    if str(data.get("formula_hash", "")).lower() != formula.formula_hash.lower():
        errors.append("FORMULA_HASH_MISMATCH")
    if data.get("formula_summary", {}).get("formula_hash") != formula.formula_hash:
        errors.append("FORMULA_SUMMARY_HASH_MISMATCH")
    source = data.get("source_obstruction_record", {})
    fingerprint = source.get("obstruction_fingerprint")
    if fingerprint not in RECOGNIZED_FINGERPRINTS:
        errors.append("OBSTRUCTION_FINGERPRINT_UNRECOGNIZED")
    if not source.get("evidence_hash"):
        errors.append("OBSTRUCTION_EVIDENCE_HASH_MISSING")
    portfolio = data.get("available_operators", [])
    if _portfolio_hash(portfolio) != data.get("operator_portfolio_hash"):
        errors.append("OPERATOR_PORTFOLIO_HASH_MISMATCH")
    known = _known_operator_by_name(portfolio)
    canonical = _portfolio_dict()
    for operator_name, item in known.items():
        if operator_name not in canonical:
            errors.append(f"OPERATOR_NOT_IN_CANONICAL_PORTFOLIO:{operator_name}")
        elif item.get("grammar_id") != canonical[operator_name]["grammar_id"]:
            errors.append(f"OPERATOR_GRAMMAR_MISMATCH:{operator_name}")
        if not item.get("certificate_type"):
            errors.append(f"OPERATOR_CERTIFICATE_TYPE_MISSING:{operator_name}")
    plans = data.get("proposed_plans", [])
    if not plans:
        errors.append("NO_PLAN_PROPOSED")
    selected_plan = None
    for plan in plans:
        if plan.get("plan_id") == data.get("selected_plan_id"):
            selected_plan = plan
    if selected_plan is None:
        errors.append("SELECTED_PLAN_NOT_FOUND")
    for plan in plans:
        plan_type = plan.get("plan_type")
        if plan_type not in {OPERATOR_SEQUENCE_PLAN, MISSING_OPERATOR_HYPOTHESIS_PLAN, REVIEW_OR_THEOREMIZATION_PLAN}:
            errors.append(f"PLAN_TYPE_INVALID:{plan.get('plan_id')}")
        if plan.get("expected_execution_result") != EXECUTION_REQUIRED:
            errors.append(f"EXECUTION_REQUIRED_NOT_DECLARED:{plan.get('plan_id')}")
        if not plan.get("forbidden_claims"):
            errors.append(f"FORBIDDEN_CLAIMS_NOT_LISTED:{plan.get('plan_id')}")
        sequence = plan.get("operator_sequence", [])
        if plan_type == OPERATOR_SEQUENCE_PLAN and not sequence:
            errors.append(f"SEQUENCE_PLAN_EMPTY:{plan.get('plan_id')}")
        for idx, step in enumerate(sequence):
            operator_name = step.get("operator_name")
            if operator_name not in known:
                errors.append(f"UNKNOWN_OPERATOR:{operator_name}")
                continue
            if step.get("grammar_id") != known[operator_name].get("grammar_id"):
                errors.append(f"STEP_GRAMMAR_MISMATCH:{operator_name}")
            if not step.get("expected_certificate_type"):
                errors.append(f"STEP_CERTIFICATE_TYPE_MISSING:{step.get('step_id')}")
            if step.get("expected_certificate_type") != known[operator_name].get("certificate_type"):
                errors.append(f"STEP_CERTIFICATE_TYPE_MISMATCH:{step.get('step_id')}")
            preservation = step.get("preservation_required")
            if preservation == DIAGNOSTIC_ONLY:
                errors.append(f"DIAGNOSTIC_STEP_AS_PROOF:{step.get('step_id')}")
            if preservation not in {SAT_WITNESS, UNSAT_PRESERVATION, EQUI_SAT, NATIVE_ONLY, DIAGNOSTIC_ONLY}:
                errors.append(f"PRESERVATION_REQUIREMENT_INVALID:{step.get('step_id')}")
            if idx > 0 and not step.get("handoff_requirements"):
                errors.append(f"HANDOFF_REQUIREMENT_MISSING:{step.get('step_id')}")
            if not step.get("handoff_requirements"):
                errors.append(f"HANDOFF_REQUIREMENT_MISSING:{step.get('step_id')}")
            if preservation in {SAT_WITNESS, UNSAT_PRESERVATION, EQUI_SAT} and not step.get("lift_requirements"):
                errors.append(f"LIFT_OR_PRESERVATION_REQUIREMENT_MISSING:{step.get('step_id')}")
        if plan_type in {MISSING_OPERATOR_HYPOTHESIS_PLAN, REVIEW_OR_THEOREMIZATION_PLAN}:
            hypothesis = plan.get("missing_operator_hypothesis")
            if not hypothesis:
                errors.append(f"MISSING_OPERATOR_HYPOTHESIS_ABSENT:{plan.get('plan_id')}")
            else:
                if not hypothesis.get("expected_certificate_type"):
                    errors.append("MISSING_OPERATOR_CERTIFICATE_TYPE_MISSING")
                if not hypothesis.get("minimal_soundness_obligations"):
                    errors.append("MISSING_OPERATOR_SOUNDNESS_OBLIGATIONS_MISSING")
                if not hypothesis.get("required_negative_controls"):
                    errors.append("MISSING_OPERATOR_NEGATIVE_CONTROLS_MISSING")
    if data.get("execution_status") != EXECUTION_REQUIRED:
        errors.append("FAKE_EXECUTION_CLAIM")
    if COLLAPSE_PLANNER_EXECUTION_REQUIRED not in data.get("execution_requirements", []):
        errors.append("EXECUTION_REQUIREMENT_TOP_LEVEL_MISSING")
    if data.get("drat_claim") != DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_CLAIM")
    if data.get("evidence_grade") != FINITE_PLANNER_CERTIFICATE_VERIFIED:
        errors.append("EVIDENCE_GRADE_INVALID")
    public_category = str(data.get("public_category", ""))
    if public_category.startswith("SAT_") or public_category.startswith("UNSAT_"):
        errors.append("FAKE_SAT_UNSAT_PUBLIC_CATEGORY")
    if data.get("claimed_result") in {"SAT", "UNSAT"}:
        errors.append("FAKE_SAT_UNSAT_CLAIM")
    if data.get("solver_result") in {"SAT", "UNSAT"}:
        errors.append("FAKE_SOLVER_RESULT_CLAIM")
    payload_text = stable_json(data).lower()
    for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
        if fragment in payload_text:
            errors.append(f"FORBIDDEN_CLAIM_FRAGMENT:{fragment}")
    _scan_for_forbidden_status(data, errors)
    status = COLLAPSE_PLANNER_PLAN_VERIFIED if not errors else COLLAPSE_PLANNER_PLAN_REJECTED
    return {
        "status": status,
        "checker_status": status,
        "errors": errors,
        "selected_plan_id": data.get("selected_plan_id"),
        "plan_count": len(plans),
        "evidence_grade": data.get("evidence_grade"),
        "execution_required": data.get("execution_status") == EXECUTION_REQUIRED,
        "claim_boundary": "Planner certificate only; future certified operator execution is required before any SAT/UNSAT/proof claim.",
    }


def collapse_planner_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Self-Expanding Collapse Planner Report",
        "",
        "## Executive Summary",
        "",
        "v2.19 adds G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE. G12 maps obstruction fingerprints to structurally valid plans, missing-operator hypotheses, or review/theoremization plans. A plan is not execution, not SAT/UNSAT evidence, not DRAT, not a proof, and not a theorem.",
        "",
        "## Planned Rows",
        "",
        "| instance | fingerprint | selected plan | type | checker | evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['obstruction_fingerprint']}` | `{row['selected_plan_id']}` | `{row['selected_plan_type']}` | `{row['checker_status']}` | `{row['evidence_grade']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The planner verifies structural compatibility and claim-boundary safety only. Execution requires later operator certificates. Diagnostic-only steps cannot be proof, and missing operators remain hypotheses.",
            "",
            "## Planner Delta Summary",
            "",
            stable_json(delta),
            "## Forbidden Claims",
            "",
            "- no planner SAT/UNSAT claim",
            "- no execution claim",
            "- no DRAT claim",
            "- no theorem or strictness theorem claim",
            "- no completeness claim",
            "- no P vs NP progress claim",
            "- no HARD or UNKNOWN statuses",
            "",
        ]
    )
    return "\n".join(lines)


def run_collapse_planner_lab(
    *,
    instances: Iterable[str],
    out_root: str | Path,
    strict: bool = False,
    zip_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cert_root = root / "certificates"
    cnf_root = root / "original_cnf"
    cert_root.mkdir(parents=True, exist_ok=True)
    cnf_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    checker_summary: list[dict[str, Any]] = []
    obstruction_mapping: list[dict[str, Any]] = []
    selected_plans: list[dict[str, Any]] = []
    missing_hypotheses: list[dict[str, Any]] = []
    for instance_id in instances:
        instance = make_planner_instance(instance_id)
        cert = build_collapse_plan_certificate(instance)
        check = check_collapse_plan_certificate(instance.formula, cert)
        cert_path = cert_root / f"{instance_id}_collapse_plan_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        _write_json(cert_path, cert.to_dict())
        _write_text(cnf_path, instance.formula.canonical_dimacs())
        selected = next(plan for plan in cert.proposed_plans if plan["plan_id"] == cert.selected_plan_id)
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "control_kind": instance.control_kind,
            "obstruction_fingerprint": instance.obstruction_fingerprint,
            "selected_plan_id": cert.selected_plan_id,
            "selected_plan_type": selected["plan_type"],
            "checker_status": check["status"],
            "evidence_grade": cert.evidence_grade,
            "execution_status": cert.execution_status,
            "public_category": cert.public_category,
            "valid_planner_delta": check["status"] == COLLAPSE_PLANNER_PLAN_VERIFIED and instance.control_kind is None,
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
        }
        rows.append(row)
        certificates.append(cert.to_dict())
        checker_summary.append({**check, "instance_id": instance_id})
        obstruction_mapping.append(
            {
                "instance_id": instance_id,
                "obstruction_fingerprint": instance.obstruction_fingerprint,
                "selected_plan_id": cert.selected_plan_id,
                "selected_plan_type": selected["plan_type"],
                "checker_status": check["status"],
            }
        )
        selected_plans.append({"instance_id": instance_id, "selected_plan": selected})
        if cert.missing_operator_hypotheses:
            missing_hypotheses.extend({"instance_id": instance_id, **hypothesis} for hypothesis in cert.missing_operator_hypotheses)

    portfolio = [item.to_dict() for item in operator_portfolio()]
    delta = {
        "operator_added": G12_GRAMMAR,
        "instances_total": len(rows),
        "plans_verified": sum(1 for row in rows if row["checker_status"] == COLLAPSE_PLANNER_PLAN_VERIFIED),
        "planner_delta_count": sum(1 for row in rows if row["valid_planner_delta"]),
        "rejected_negative_controls": sum(1 for row in rows if row["control_kind"] and row["checker_status"] == COLLAPSE_PLANNER_PLAN_REJECTED),
        "operator_sequence_plans": sum(1 for row in rows if row["selected_plan_type"] == OPERATOR_SEQUENCE_PLAN and row["checker_status"] == COLLAPSE_PLANNER_PLAN_VERIFIED),
        "missing_operator_plans": sum(1 for row in rows if row["selected_plan_type"] == MISSING_OPERATOR_HYPOTHESIS_PLAN and row["checker_status"] == COLLAPSE_PLANNER_PLAN_VERIFIED),
        "review_plans": sum(1 for row in rows if row["selected_plan_type"] == REVIEW_OR_THEOREMIZATION_PLAN and row["checker_status"] == COLLAPSE_PLANNER_PLAN_VERIFIED),
        "evidence_grade": FINITE_PLANNER_CERTIFICATE_VERIFIED,
        "execution_required": True,
        "sat_unsat_claims": 0,
        "drat_claims": 0,
        "strict": strict,
        "claim_boundary": "Planner certificate only; no execution, SAT/UNSAT, DRAT, theorem, completeness, lower-bound, or P-vs-NP claim.",
    }
    _write_json(root / "collapse_plan_certificates.json", certificates)
    _write_json(root / "collapse_planner_checker_summary.json", checker_summary)
    _write_json(root / "obstruction_to_plan_mapping.json", obstruction_mapping)
    _write_json(root / "operator_portfolio_summary.json", {"operator_portfolio_hash": _portfolio_hash(portfolio), "available_operators": portfolio})
    _write_json(root / "selected_plan_summary.json", selected_plans)
    _write_json(root / "missing_operator_hypotheses.json", missing_hypotheses)
    _write_json(root / "g12_planner_delta_summary.json", delta)
    _write_text(root / "COLLAPSE_PLANNER_REPORT.md", collapse_planner_report(rows, delta))
    zip_sha = None
    if zip_path is not None:
        zip_sha = _make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "rows": rows,
        "collapse_plan_certificates": certificates,
        "collapse_planner_checker_summary": checker_summary,
        "obstruction_to_plan_mapping": obstruction_mapping,
        "operator_portfolio_summary": {"operator_portfolio_hash": _portfolio_hash(portfolio), "available_operators": portfolio},
        "selected_plan_summary": selected_plans,
        "missing_operator_hypotheses": missing_hypotheses,
        "g12_planner_delta_summary": delta,
        "artifact_zip": str(zip_path) if zip_path is not None else None,
        "artifact_sha256": zip_sha,
    }


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_collapse_planner_lab(
        instances=args.instances,
        out_root=args.out_root,
        strict=args.strict,
        zip_path=args.zip,
    )
    print(stable_json({"out_root": result["out_root"], "artifact_zip": result["artifact_zip"], "artifact_sha256": result["artifact_sha256"], "delta": result["g12_planner_delta_summary"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    formula = load_dimacs(args.cnf)
    data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
    result = check_collapse_plan_certificate(formula, data)
    print(stable_json(result))
    return 0 if result["status"] == COLLAPSE_PLANNER_PLAN_VERIFIED else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.collapse_planner")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--instances", nargs="+", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--cnf", required=True)
    check.add_argument("--certificate", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
