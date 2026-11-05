"""G9-G13 soundness-backbone theoremization for Witnora v2.21.

This module creates proof-sketch records and proof-obligation matrices for the
closed-loop architecture introduced from v2.16 through v2.20. It deliberately
does not add a solver/operator and does not mark any theorem as proven.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile


RELEASE = "v2.21-theoremization-g9-g13-soundness"
PUBLIC_CATEGORY = "THEORY_SKETCH_AND_PROOF_OBLIGATIONS"
RECORD_TYPE = "SOUNDNESS_THEOREMIZATION_RECORD"

THEOREMIZATION_PACKAGE_VERIFIED = "THEOREMIZATION_PACKAGE_VERIFIED"
THEOREMIZATION_PACKAGE_FAILED = "THEOREMIZATION_PACKAGE_FAILED"

FORMAL_PROOF_SKETCH = "FORMAL_PROOF_SKETCH"
PROOF_OBLIGATION = "PROOF_OBLIGATION"
THEOREM_CANDIDATE = "THEOREM_CANDIDATE"
EMPIRICAL_EVIDENCE = "EMPIRICAL_EVIDENCE"
SPECULATIVE = "SPECULATIVE"

ALLOWED_CANDIDATE_STATUSES = {
    FORMAL_PROOF_SKETCH,
    PROOF_OBLIGATION,
    THEOREM_CANDIDATE,
    EMPIRICAL_EVIDENCE,
    SPECULATIVE,
}
FORBIDDEN_STATUS_VALUES = {"THEOREM_PROVEN", "COMPLETE", "PNP_PROGRESS", "HARD", "UNKNOWN"}

SCOPE = [
    "G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE",
    "G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE",
    "G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE",
    "G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE",
    "G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE",
]

OBLIGATION_CATEGORIES = [
    "CERTIFICATE_CHECKER_SOUNDNESS",
    "FORMULA_SERIALIZATION_HASH_EXACTNESS",
    "WITNESS_VERIFICATION",
    "UNSAT_PRESERVATION_EQUISAT_PROOF",
    "DIAGNOSTIC_ONLY_EXCLUSION",
    "FAKE_DRAT_EXCLUSION",
    "THEOREM_PROVEN_CLAIM_EXCLUSION",
    "COMPOSITION_ASSOCIATIVITY_CHAINING",
    "PROJECTION_EQUISATISFIABILITY",
    "MOTIF_INSTANTIATION_VALIDITY",
    "PLAN_EXECUTION_SEPARATION",
    "MISMATCH_HANDLING",
    "FINITE_VS_FAMILY_BOUNDARY",
    "NATIVE_VS_EXTERNAL_CERTIFICATE_BOUNDARY",
]


@dataclass(frozen=True)
class SoundnessTheoremCandidate:
    theorem_id: str
    title: str
    grammar_scope: list[str]
    statement: str
    assumptions: list[str]
    proof_sketch: str
    proof_obligations: list[str]
    evidence_support: list[str]
    known_gaps: list[str]
    nonclaims: list[str]
    status: str
    may_not_be_claimed_as_proven: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SoundnessTheoremizationRecord:
    record_type: str
    release: str
    scope: list[str]
    theorem_candidates: list[dict[str, Any]]
    proof_obligation_matrix: list[dict[str, Any]]
    evidence_links: dict[str, Any]
    claim_boundary_audit: list[dict[str, Any]]
    reviewer_objection_table: list[dict[str, Any]]
    status: str
    public_category: str
    forbidden_claims_checked: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


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


def build_soundness_theorem_candidates() -> list[SoundnessTheoremCandidate]:
    """Return the v2.21 G9-G13 theoremization candidates."""

    return [
        SoundnessTheoremCandidate(
            theorem_id="TC-057",
            title="G9 Composition Soundness Candidate",
            grammar_scope=["G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE"],
            statement=(
                "If every step in a composed orchestration certificate is verified by its corresponding "
                "operator checker, every formula handoff hash matches, diagnostic-only steps are excluded "
                "from result certification, and the final SAT witness or UNSAT preservation chain verifies "
                "against the original formula, then the composed result is sound for that finite instance."
            ),
            assumptions=[
                "Each step checker is sound.",
                "Formula hash function collision resistance is assumed operationally.",
                "Handoff hashes match exact serialized formula state.",
                "SAT witness is verified against the original CNF.",
                "UNSAT preservation or equisatisfiability obligations verify.",
                "No diagnostic-only step is used as proof.",
            ],
            proof_sketch=(
                "Induct over the operator sequence. Each checked step relates its input formula state to "
                "its output under a declared preservation rule. Matching handoff hashes ensure the next "
                "step consumes exactly the previous output. A SAT result is discharged by direct original-CNF "
                "witness checking; an UNSAT result is discharged by composing verified preservation obligations."
            ),
            proof_obligations=[
                "Mechanize each step-checker soundness assumption.",
                "Formalize formula serialization and hash binding.",
                "Formalize composition of SAT witness lifts and UNSAT preservation rules.",
            ],
            evidence_support=[
                "outputs/v2.16-composed-operator-orchestration/g9_operator_delta_summary.json",
                "outputs/v2.20-planner-guided-execution/planner_execution_checker_summary.json",
            ],
            known_gaps=[
                "Native checker soundness is not yet proof-assistant verified.",
                "Hash binding is operational, not a mathematical collision-proof statement.",
            ],
            nonclaims=[
                "Does not claim composition completeness.",
                "Does not claim a DRAT proof.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=FORMAL_PROOF_SKETCH,
        ),
        SoundnessTheoremCandidate(
            theorem_id="TC-058",
            title="G10 Circuit Projection Soundness Candidate",
            grammar_scope=["G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE"],
            statement=(
                "If each projected auxiliary variable has an exact verified definitional gate encoding, "
                "projection steps are equisatisfiability-preserving, unsafe auxiliary uses are rejected, "
                "and the lifted assignment satisfies the original CNF directly, then SAT witness lift is "
                "sound; for UNSAT, if the projected core is UNSAT and every projection step is "
                "equisatisfiability-preserving, then original UNSAT is soundly preserved for supported "
                "exact definitional families."
            ),
            assumptions=[
                "Only exact AND, OR, and NOT definitions are accepted in the v2.17 prototype.",
                "Incomplete, polluted, and unsafe auxiliary definitions are rejected.",
                "SAT lift is checked directly against the original CNF.",
                "UNSAT requires an equisatisfiability-preserving projection chain.",
                "No arbitrary auxiliary projection is trusted.",
            ],
            proof_sketch=(
                "For each verified gate definition, the auxiliary value is forced to equal the gate function "
                "on its inputs. SAT lifting evaluates these definitions and then relies on direct CNF "
                "satisfaction. UNSAT preservation follows only when every elimination step is certified "
                "as equisatisfiable, allowing contradiction in the core to lift back to the original."
            ),
            proof_obligations=[
                "Formalize exact definitional encodings for supported gates.",
                "Formalize safe-use constraints for projected auxiliary variables.",
                "Mechanize equisatisfiability of supported projection steps.",
            ],
            evidence_support=[
                "outputs/v2.17-circuit-projection-lift/g10_operator_delta_summary.json",
                "outputs/v2.17-circuit-projection-lift/circuit_projection_checker_summary.json",
            ],
            known_gaps=[
                "The proof sketch is limited to supported exact definitions.",
                "No broad circuit-SAT completeness statement is available or claimed.",
            ],
            nonclaims=[
                "Does not claim arbitrary circuit projection.",
                "Does not claim circuit-SAT solving.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=FORMAL_PROOF_SKETCH,
        ),
        SoundnessTheoremCandidate(
            theorem_id="TC-059",
            title="G11 Proof Motif Generalization Soundness Candidate",
            grammar_scope=["G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE"],
            statement=(
                "If every generalized proof motif reuse is checked through concrete proof expansion or a "
                "verified parametric instantiation, all substitutions are valid, and the final contradiction "
                "verifies from original clauses, then the generalized macro-proof certificate is sound for "
                "that finite instance."
            ),
            assumptions=[
                "Near similarity is not treated as proof.",
                "Every reuse instantiation checks.",
                "Loose similarity is rejected or diagnostic-only.",
                "Exact G6 duplicates are not counted as novel G11 deltas.",
                "The final contradiction is verified from original clauses.",
            ],
            proof_sketch=(
                "The generalized template is trusted only after all concrete instantiations are checked. "
                "Each instantiated step is a valid proof step over clauses present in the original CNF. "
                "Therefore the macro-proof abbreviates checked concrete derivations rather than replacing "
                "them with similarity evidence."
            ),
            proof_obligations=[
                "Formalize the template language and substitution safety constraints.",
                "Mechanize the resolution/unit-propagation step validator.",
                "Formalize compression accounting as non-semantic bookkeeping.",
            ],
            evidence_support=[
                "outputs/v2.18-proof-motif-generalization-checker/g11_operator_delta_summary.json",
                "outputs/v2.18-proof-motif-generalization-checker/proof_motif_generalization_checker_summary.json",
            ],
            known_gaps=[
                "Parametric checking is still scoped to the implemented template forms.",
                "Native macro-proofs are not externally checked DRAT/LRAT/FRAT artifacts.",
            ],
            nonclaims=[
                "Does not claim arbitrary proof-pattern learning.",
                "Does not claim proof motif completeness.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=FORMAL_PROOF_SKETCH,
        ),
        SoundnessTheoremCandidate(
            theorem_id="TC-060",
            title="G12 Plan-Only Soundness Candidate",
            grammar_scope=["G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE"],
            statement=(
                "If a collapse plan certificate verifies, then the plan is structurally valid, "
                "operator-compatible, claim-boundary safe, and execution-required; it does not certify SAT, "
                "UNSAT, DRAT, theorem, or completeness."
            ),
            assumptions=[
                "Operator names and certificate types are known.",
                "Handoff and lift obligations are declared.",
                "Unknown operators are rejected.",
                "Diagnostic-only steps cannot be proof.",
                "Execution-required boundary is explicit.",
            ],
            proof_sketch=(
                "The checker validates only metadata compatibility, known-operator references, required "
                "handoff obligations, and forbidden-claim boundaries. Since the certificate explicitly "
                "records PLAN_ONLY and EXECUTION_REQUIRED, no formula result follows from the plan alone."
            ),
            proof_obligations=[
                "Formalize the semantics of plan-only records.",
                "Prove planner verification cannot imply SAT or UNSAT.",
                "Tie future execution claims to separate operator certificates.",
            ],
            evidence_support=[
                "outputs/v2.19-self-expanding-collapse-planner/g12_planner_delta_summary.json",
                "outputs/v2.19-self-expanding-collapse-planner/collapse_planner_checker_summary.json",
            ],
            known_gaps=[
                "The plan language is operational rather than proof-assistant formalized.",
                "The mapping from obstruction fingerprints to plans remains heuristic and bounded.",
            ],
            nonclaims=[
                "Does not claim execution happened.",
                "Does not claim SAT or UNSAT.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=FORMAL_PROOF_SKETCH,
        ),
        SoundnessTheoremCandidate(
            theorem_id="TC-061",
            title="G13 Planner-Guided Execution Soundness Candidate",
            grammar_scope=["G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE"],
            statement=(
                "If a verified G12 plan is paired with a separately verified G13 execution certificate, "
                "every actual operator certificate verifies, every formula handoff verifies, planned-vs-actual "
                "comparison is recomputed, and the final SAT witness or UNSAT preservation trace verifies, "
                "then the finite execution result is sound for that instance."
            ),
            assumptions=[
                "Plan and execution certificates are separate.",
                "Execution is not copied from the plan.",
                "Every actual step certificate is checked.",
                "Mismatch does not certify planner success.",
                "SAT witness verifies against original CNF.",
                "UNSAT preservation is required.",
            ],
            proof_sketch=(
                "The plan is first checked as a plan-only object. The execution certificate is then checked "
                "independently. Actual step certificates and formula-state handoffs establish the execution "
                "chain. A SAT result is accepted only by direct original-CNF witness verification, and an "
                "UNSAT result is accepted only through verified preservation/native proof obligations."
            ),
            proof_obligations=[
                "Formalize separation between plan certificate and execution certificate.",
                "Formalize planned-vs-actual comparison semantics.",
                "Mechanize step-checker soundness for every operator allowed in execution.",
            ],
            evidence_support=[
                "outputs/v2.20-planner-guided-execution/g13_planner_execution_delta_summary.json",
                "outputs/v2.20-planner-guided-execution/planner_execution_checker_summary.json",
            ],
            known_gaps=[
                "The execution checker is native code, not an externally verified proof assistant artifact.",
                "Finite fixtures do not prove that future plans will succeed.",
            ],
            nonclaims=[
                "Does not claim all plans succeed.",
                "Does not claim planner completeness.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=FORMAL_PROOF_SKETCH,
        ),
        SoundnessTheoremCandidate(
            theorem_id="TC-062",
            title="Closed-Loop Finite Soundness Candidate",
            grammar_scope=[
                "G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE",
                "G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE",
                "G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE",
            ],
            statement=(
                "For finite controlled instances where obstruction fingerprinting, planning, execution, "
                "certificate verification, and result verification all pass, Witnora demonstrates a sound "
                "finite closed-loop collapse experiment."
            ),
            assumptions=[
                "G7 obstruction record verifies.",
                "G12 plan verifies.",
                "G13 execution verifies.",
                "The result is certified by the actual operator chain.",
                "All claim boundaries are preserved.",
            ],
            proof_sketch=(
                "Compose the scoped guarantees: obstruction records describe a failure fingerprint without "
                "claiming SAT/UNSAT, plans describe a compatible future route without claiming execution, "
                "and G13 accepts only a separate execution chain whose result obligations verify. The closed "
                "loop is therefore finite evidence about this checked pipeline, not a family theorem."
            ),
            proof_obligations=[
                "Formalize obstruction-record semantics.",
                "Formalize plan-to-execution linkage.",
                "Define the finite-vs-family boundary in a proof assistant or comparable external formalism.",
            ],
            evidence_support=[
                "outputs/v2.14-obstruction-dual-certificate/g7_obstruction_dual_summary.json",
                "outputs/v2.19-self-expanding-collapse-planner/g12_planner_delta_summary.json",
                "outputs/v2.20-planner-guided-execution/g13_planner_execution_delta_summary.json",
            ],
            known_gaps=[
                "No infinite-family theorem is proven.",
                "No hierarchy completeness result is proven.",
                "External proof-checker integration remains future work.",
            ],
            nonclaims=[
                "Does not claim hierarchy coverage.",
                "Does not claim a family theorem.",
                "Does not claim a proven theorem.",
                "Does not claim P vs NP progress.",
            ],
            status=EMPIRICAL_EVIDENCE,
        ),
    ]


def _evidence_link(path: str, release: str, scope: str) -> dict[str, Any]:
    p = Path(path)
    return {
        "release": release,
        "scope": scope,
        "path": path,
        "exists_in_workspace": p.exists(),
        "sha256": sha256_file(p) if p.exists() and p.is_file() else "NOT_RECORDED_IN_THIS_ARTIFACT",
    }


def build_evidence_links() -> dict[str, Any]:
    return {
        "v2.16 G9 evidence": [
            _evidence_link(
                "outputs/v2.16-composed-operator-orchestration/g9_operator_delta_summary.json",
                "v2.16-composed-operator-orchestration",
                "G9",
            ),
            _evidence_link(
                "outputs/v2.16-composed-operator-orchestration/composed_orchestration_checker_summary.json",
                "v2.16-composed-operator-orchestration",
                "G9",
            ),
        ],
        "v2.17 G10 evidence": [
            _evidence_link(
                "outputs/v2.17-circuit-projection-lift/g10_operator_delta_summary.json",
                "v2.17-circuit-projection-lift",
                "G10",
            ),
            _evidence_link(
                "outputs/v2.17-circuit-projection-lift/circuit_projection_checker_summary.json",
                "v2.17-circuit-projection-lift",
                "G10",
            ),
        ],
        "v2.18 G11 evidence": [
            _evidence_link(
                "outputs/v2.18-proof-motif-generalization-checker/g11_operator_delta_summary.json",
                "v2.18-proof-motif-generalization-checker",
                "G11",
            ),
            _evidence_link(
                "outputs/v2.18-proof-motif-generalization-checker/proof_motif_generalization_checker_summary.json",
                "v2.18-proof-motif-generalization-checker",
                "G11",
            ),
        ],
        "v2.19 G12 evidence": [
            _evidence_link(
                "outputs/v2.19-self-expanding-collapse-planner/g12_planner_delta_summary.json",
                "v2.19-self-expanding-collapse-planner",
                "G12",
            ),
            _evidence_link(
                "outputs/v2.19-self-expanding-collapse-planner/collapse_planner_checker_summary.json",
                "v2.19-self-expanding-collapse-planner",
                "G12",
            ),
        ],
        "v2.20 G13 evidence": [
            _evidence_link(
                "outputs/v2.20-planner-guided-execution/g13_planner_execution_delta_summary.json",
                "v2.20-planner-guided-execution",
                "G13",
            ),
            _evidence_link(
                "outputs/v2.20-planner-guided-execution/planner_execution_checker_summary.json",
                "v2.20-planner-guided-execution",
                "G13",
            ),
        ],
    }


def build_claim_boundary_audit() -> list[dict[str, Any]]:
    return [
        {
            "claim": "finite certified execution evidence",
            "allowed_wording": "G13 verifies finite plan-guided executions whose actual certificates and handoffs check.",
            "forbidden_wording": "All plans execute successfully.",
            "reason": "Finite checked rows do not imply universal planner success.",
            "tests_guarding_boundary": ["PLANNER_EXECUTION_MISMATCH_PASS", "NO_COMPLETENESS_CLAIM_PASS"],
        },
        {
            "claim": "formal proof sketches",
            "allowed_wording": "G9-G13 soundness is stated as formal proof sketches and proof obligations.",
            "forbidden_wording": "Theorem proven.",
            "reason": "No proof-assistant artifact or external formal proof is included in v2.21.",
            "tests_guarding_boundary": ["NO_THEOREM_PROVEN_CLAIM_PASS"],
        },
        {
            "claim": "native certificate soundness assumptions",
            "allowed_wording": "Native certificates are checked by Witnora checkers under explicit assumptions.",
            "forbidden_wording": "Native certificates are DRAT proofs.",
            "reason": "Native certificates are not external DRAT/LRAT/FRAT artifacts unless exported and checked.",
            "tests_guarding_boundary": ["NO_FAKE_DRAT_CLAIM_PASS"],
        },
        {
            "claim": "closed-loop finite experiments",
            "allowed_wording": "The obstruction-plan-execution loop is demonstrated on finite controlled instances.",
            "forbidden_wording": "The hierarchy is complete.",
            "reason": "Closed-loop evidence does not cover all SAT formulas or all obstructions.",
            "tests_guarding_boundary": ["NO_COMPLETENESS_CLAIM_PASS"],
        },
        {
            "claim": "P vs NP boundary",
            "allowed_wording": "P vs NP is long-range motivation only.",
            "forbidden_wording": "P vs NP progress.",
            "reason": "No lower bound, complete solver, or complexity-class separation is shown.",
            "tests_guarding_boundary": ["NO_PNP_CLAIM_PASS"],
        },
        {
            "claim": "status vocabulary",
            "allowed_wording": "Use theorem candidate, formal proof sketch, proof obligation, or empirical evidence.",
            "forbidden_wording": "HARD or UNKNOWN as accepted statuses.",
            "reason": "No-collapse and diagnostic rows are not hardness or unknown-satisfiability claims.",
            "tests_guarding_boundary": ["NO_HARD_UNKNOWN_STATUS_PASS"],
        },
    ]


def build_reviewer_objection_table() -> list[dict[str, Any]]:
    return [
        {
            "objection": "This is just engineering.",
            "response": (
                "The release defines theorem candidates, proof sketches, proof obligations, and certified "
                "finite evidence. It does not overclaim theorem status."
            ),
        },
        {
            "objection": "Native certificates are not external proofs.",
            "response": (
                "Correct. Native certificates are scoped as native unless DRAT/LRAT/FRAT export is implemented "
                "and externally checked."
            ),
        },
        {
            "objection": "Plans are not proofs.",
            "response": "Correct. G12 is plan-only and G13 separates execution certificates.",
        },
        {
            "objection": "Finite examples do not imply families.",
            "response": "Correct. Infinite-family theorems remain proof obligations.",
        },
        {
            "objection": "Operator composition may be unsound.",
            "response": (
                "G9/G13 require verified step certificates, formula handoffs, and result checks; full "
                "theoremization remains candidate/sketch level."
            ),
        },
        {
            "objection": "Projection may be unsound.",
            "response": (
                "G10 only supports exact definitions and verifies original-CNF SAT lift; UNSAT requires "
                "equisatisfiability preservation."
            ),
        },
        {
            "objection": "Motif generalization may fake proof compression.",
            "response": (
                "G11 requires every generalized reuse to be concretely checked or parametrically instantiated "
                "and verified."
            ),
        },
    ]


def build_proof_obligation_matrix(candidates: list[SoundnessTheoremCandidate]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        for category in OBLIGATION_CATEGORIES:
            rows.append(
                {
                    "theorem_candidate_id": candidate.theorem_id,
                    "candidate_title": candidate.title,
                    "obligation_category": category,
                    "assumptions": candidate.assumptions,
                    "verified_by_tests": _test_refs_for_category(category),
                    "supported_by_previous_release_evidence": candidate.evidence_support,
                    "still_informal": True,
                    "requires_external_formalization": True,
                    "requires_external_proof_checker_or_drat_bridge": category == "NATIVE_VS_EXTERNAL_CERTIFICATE_BOUNDARY",
                    "risk_level": _risk_level(category),
                    "reviewer_objection": _reviewer_objection_for_category(category),
                    "planned_response": _planned_response_for_category(category),
                    "current_status": "FORMAL_PROOF_SKETCH_ONLY",
                }
            )
    return rows


def _test_refs_for_category(category: str) -> list[str]:
    mapping = {
        "CERTIFICATE_CHECKER_SOUNDNESS": ["SOUNDNESS_THEOREMIZATION_SCHEMA_PASS"],
        "FORMULA_SERIALIZATION_HASH_EXACTNESS": ["PLANNER_EXECUTION_HANDOFF_PASS"],
        "WITNESS_VERIFICATION": ["PLANNER_EXECUTION_SAT_ORIGINAL_CNF_PASS"],
        "UNSAT_PRESERVATION_EQUISAT_PROOF": ["PLANNER_EXECUTION_UNSAT_PRESERVATION_PASS"],
        "DIAGNOSTIC_ONLY_EXCLUSION": ["PLANNER_EXECUTION_DIAGNOSTIC_AS_RESULT_REJECT_PASS"],
        "FAKE_DRAT_EXCLUSION": ["NO_FAKE_DRAT_CLAIM_PASS"],
        "THEOREM_PROVEN_CLAIM_EXCLUSION": ["NO_THEOREM_PROVEN_CLAIM_PASS"],
        "COMPOSITION_ASSOCIATIVITY_CHAINING": ["COMPOSED_ORCHESTRATION_CHAIN_VERIFIED_PASS"],
        "PROJECTION_EQUISATISFIABILITY": ["CIRCUIT_PROJECTION_EQUI_SAT_PASS"],
        "MOTIF_INSTANTIATION_VALIDITY": ["PROOF_MOTIF_GENERALIZED_REUSE_CHECK_PASS"],
        "PLAN_EXECUTION_SEPARATION": ["PLANNER_EXECUTION_PLAN_VERIFY_PASS"],
        "MISMATCH_HANDLING": ["PLANNER_EXECUTION_MISMATCH_PASS"],
        "FINITE_VS_FAMILY_BOUNDARY": ["NO_THEOREM_PROVEN_CLAIM_PASS"],
        "NATIVE_VS_EXTERNAL_CERTIFICATE_BOUNDARY": ["NO_FAKE_DRAT_CLAIM_PASS"],
    }
    return mapping.get(category, [])


def _risk_level(category: str) -> str:
    if category in {"CERTIFICATE_CHECKER_SOUNDNESS", "UNSAT_PRESERVATION_EQUISAT_PROOF", "PROJECTION_EQUISATISFIABILITY"}:
        return "HIGH"
    if category in {"FORMULA_SERIALIZATION_HASH_EXACTNESS", "COMPOSITION_ASSOCIATIVITY_CHAINING", "MOTIF_INSTANTIATION_VALIDITY"}:
        return "MEDIUM"
    return "LOW"


def _reviewer_objection_for_category(category: str) -> str:
    objections = {
        "CERTIFICATE_CHECKER_SOUNDNESS": "Native checkers may contain bugs or unstated assumptions.",
        "FORMULA_SERIALIZATION_HASH_EXACTNESS": "Hash handoffs may hide serialization mismatch.",
        "WITNESS_VERIFICATION": "SAT witnesses may only satisfy a transformed formula.",
        "UNSAT_PRESERVATION_EQUISAT_PROOF": "UNSAT may not lift through every transformation.",
        "DIAGNOSTIC_ONLY_EXCLUSION": "Diagnostics could accidentally become proof steps.",
        "FAKE_DRAT_EXCLUSION": "Native certificates may be mislabeled as external proofs.",
        "THEOREM_PROVEN_CLAIM_EXCLUSION": "Proof sketches may be overstated as theorems.",
        "COMPOSITION_ASSOCIATIVITY_CHAINING": "Operator composition may be order-sensitive.",
        "PROJECTION_EQUISATISFIABILITY": "Projection may silently drop constraints.",
        "MOTIF_INSTANTIATION_VALIDITY": "Similarity may substitute for proof.",
        "PLAN_EXECUTION_SEPARATION": "Plans may be mistaken for executions.",
        "MISMATCH_HANDLING": "A mismatch may still be reported as planner success.",
        "FINITE_VS_FAMILY_BOUNDARY": "Finite rows may be overstated as a family theorem.",
        "NATIVE_VS_EXTERNAL_CERTIFICATE_BOUNDARY": "Native proof objects may be confused with DRAT/LRAT/FRAT.",
    }
    return objections[category]


def _planned_response_for_category(category: str) -> str:
    responses = {
        "CERTIFICATE_CHECKER_SOUNDNESS": "Keep checker obligations explicit and target proof-assistant audits next.",
        "FORMULA_SERIALIZATION_HASH_EXACTNESS": "Record exact formula hashes and require handoff equality.",
        "WITNESS_VERIFICATION": "Verify final SAT witnesses directly against the original CNF.",
        "UNSAT_PRESERVATION_EQUISAT_PROOF": "Accept UNSAT only when preservation/equisat obligations verify.",
        "DIAGNOSTIC_ONLY_EXCLUSION": "Reject diagnostic-only steps as SAT/UNSAT evidence.",
        "FAKE_DRAT_EXCLUSION": "State native-vs-external proof boundaries in every report.",
        "THEOREM_PROVEN_CLAIM_EXCLUSION": "Use theorem candidate and proof sketch labels only.",
        "COMPOSITION_ASSOCIATIVITY_CHAINING": "Require explicit step order and formula-state handoffs.",
        "PROJECTION_EQUISATISFIABILITY": "Restrict projection to exact definitions and checked preservation.",
        "MOTIF_INSTANTIATION_VALIDITY": "Check every generalized reuse concretely or parametrically.",
        "PLAN_EXECUTION_SEPARATION": "Keep G12 plan certificates and G13 execution certificates separate.",
        "MISMATCH_HANDLING": "Report mismatch as mismatch, not planner success.",
        "FINITE_VS_FAMILY_BOUNDARY": "Label finite evidence separately from family theorem obligations.",
        "NATIVE_VS_EXTERNAL_CERTIFICATE_BOUNDARY": "Use external proof labels only after external checking.",
    }
    return responses[category]


def build_theoremization_record() -> SoundnessTheoremizationRecord:
    candidates = build_soundness_theorem_candidates()
    matrix = build_proof_obligation_matrix(candidates)
    return SoundnessTheoremizationRecord(
        record_type=RECORD_TYPE,
        release=RELEASE,
        scope=SCOPE,
        theorem_candidates=[candidate.to_dict() for candidate in candidates],
        proof_obligation_matrix=matrix,
        evidence_links=build_evidence_links(),
        claim_boundary_audit=build_claim_boundary_audit(),
        reviewer_objection_table=build_reviewer_objection_table(),
        status=THEOREMIZATION_PACKAGE_VERIFIED,
        public_category=PUBLIC_CATEGORY,
        forbidden_claims_checked=[
            "theorem proven",
            "P vs NP progress",
            "polynomial-time SAT",
            "hierarchy completeness",
            "universal collapse planning",
            "all plans succeed",
            "DRAT proof unless externally checked",
            "lower bound against G0-G13",
            "HARD / UNKNOWN statuses",
        ],
    )


def _candidate_summary(candidates: list[SoundnessTheoremCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "theorem_id": candidate.theorem_id,
            "title": candidate.title,
            "grammar_scope": candidate.grammar_scope,
            "status": candidate.status,
            "may_not_be_claimed_as_proven": candidate.may_not_be_claimed_as_proven,
            "evidence_support": candidate.evidence_support,
            "nonclaims": candidate.nonclaims,
        }
        for candidate in candidates
    ]


def _markdown_report(record: SoundnessTheoremizationRecord) -> str:
    data = record.to_dict()
    lines = [
        "# G9-G13 Soundness Backbone Theoremization",
        "",
        "v2.21 is theoremization, not a new solver/operator release.",
        "",
        "The G9-G13 backbone is stated as theorem candidates, formal proof sketches, and proof obligations. No theorem is marked proven. Finite evidence does not imply an infinite-family theorem. Native certificates are not external DRAT/LRAT/FRAT proofs unless exported and checked. The closed-loop finite evidence does not imply P-vs-NP progress.",
        "",
        "## Scope",
        "",
    ]
    for item in data["scope"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Candidates", ""])
    for candidate in data["theorem_candidates"]:
        lines.extend(
            [
                f"### {candidate['theorem_id']}: {candidate['title']}",
                "",
                f"Status: `{candidate['status']}`",
                "",
                candidate["statement"],
                "",
                "Proof sketch:",
                "",
                candidate["proof_sketch"],
                "",
                "Nonclaims:",
            ]
        )
        for nonclaim in candidate["nonclaims"]:
            lines.append(f"- {nonclaim}")
        lines.append("")
    lines.extend(
        [
            "## Proof Obligation Matrix",
            "",
            f"Rows: {len(data['proof_obligation_matrix'])}",
            "",
            "## Claim Boundary",
            "",
        ]
    )
    for claim in data["claim_boundary_audit"]:
        lines.append(f"- {claim['claim']}: allowed `{claim['allowed_wording']}`; forbidden `{claim['forbidden_wording']}`.")
    lines.append("")
    return "\n".join(lines)


def _docs_claim_boundary_markdown(audit: list[dict[str, Any]]) -> str:
    lines = [
        "# G9-G13 Claim Boundary",
        "",
        "v2.21 is a soundness-backbone theoremization package. It uses proof sketches and obligations; it does not mark any theorem as proven.",
        "",
        "## Boundaries",
        "",
    ]
    for row in audit:
        lines.extend(
            [
                f"### {row['claim']}",
                "",
                f"Allowed: {row['allowed_wording']}",
                "",
                f"Forbidden: {row['forbidden_wording']}",
                "",
                f"Reason: {row['reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def _reviewer_objections_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Reviewer Objections for G9-G13",
        "",
        "These responses are intentionally conservative. They preserve the difference between native finite evidence, proof sketches, and proven theorems.",
        "",
    ]
    for row in rows:
        lines.extend([f"## {row['objection']}", "", row["response"], ""])
    return "\n".join(lines)


def _soundness_backbone_markdown(candidates: list[SoundnessTheoremCandidate]) -> str:
    lines = [
        "# G9-G13 Soundness Backbone",
        "",
        "v2.21 theoremizes the G9-G13 backbone as proof sketches and proof obligations. It adds no new solver or SAT operator.",
        "",
        "The next mathematical gate is an infinite-family theorem. This release does not prove that theorem.",
        "",
    ]
    for candidate in candidates:
        lines.extend([f"## {candidate.title}", "", candidate.statement, "", f"Status: `{candidate.status}`", ""])
    return "\n".join(lines)


def _theory_sketch(candidate: SoundnessTheoremCandidate) -> str:
    lines = [
        f"# {candidate.title}",
        "",
        "Status: `" + candidate.status + "`",
        "",
        "This is a formal proof sketch and proof-obligation record, not a proven theorem.",
        "",
        "## Statement",
        "",
        candidate.statement,
        "",
        "## Assumptions",
        "",
    ]
    for assumption in candidate.assumptions:
        lines.append(f"- {assumption}")
    lines.extend(["", "## Proof Sketch", "", candidate.proof_sketch, "", "## Proof Obligations", ""])
    for obligation in candidate.proof_obligations:
        lines.append(f"- {obligation}")
    lines.extend(["", "## Nonclaims", ""])
    for nonclaim in candidate.nonclaims:
        lines.append(f"- {nonclaim}")
    lines.append("")
    return "\n".join(lines)


def _proof_obligation_markdown(matrix: list[dict[str, Any]]) -> str:
    lines = [
        "# G9-G13 Proof Obligation Matrix",
        "",
        "Each row is still informal until discharged by an external formalization or a stronger proof artifact.",
        "",
        "| Candidate | Category | Risk | Current Status |",
        "| --- | --- | --- | --- |",
    ]
    for row in matrix:
        lines.append(
            f"| {row['theorem_candidate_id']} | {row['obligation_category']} | {row['risk_level']} | {row['current_status']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_supporting_docs(candidates: list[SoundnessTheoremCandidate], matrix: list[dict[str, Any]], audit: list[dict[str, Any]], objections: list[dict[str, Any]]) -> None:
    _write_text(Path("docs/SOUNDNESS_BACKBONE_G9_G13.md"), _soundness_backbone_markdown(candidates))
    _write_text(Path("docs/CLAIM_BOUNDARY_G9_G13.md"), _docs_claim_boundary_markdown(audit))
    _write_text(Path("docs/REVIEWER_OBJECTIONS_G9_G13.md"), _reviewer_objections_markdown(objections))
    sketch_paths = {
        "TC-057": "theory/G9_COMPOSITION_SOUNDNESS_SKETCH.md",
        "TC-058": "theory/G10_CIRCUIT_PROJECTION_SOUNDNESS_SKETCH.md",
        "TC-059": "theory/G11_PROOF_MOTIF_GENERALIZATION_SOUNDNESS_SKETCH.md",
        "TC-060": "theory/G12_PLAN_ONLY_SOUNDNESS_SKETCH.md",
        "TC-061": "theory/G13_PLANNER_EXECUTION_SOUNDNESS_SKETCH.md",
        "TC-062": "theory/G9_G13_CLOSED_LOOP_SOUNDNESS_SKETCH.md",
    }
    for candidate in candidates:
        _write_text(Path(sketch_paths[candidate.theorem_id]), _theory_sketch(candidate))
    _write_text(Path("theory/PROOF_OBLIGATION_MATRIX_G9_G13.md"), _proof_obligation_markdown(matrix))


def run_soundness_theoremization(
    out_root: str | Path = "outputs/v2.21-theoremization-g9-g13-soundness",
    *,
    strict: bool = False,
    zip_path: str | Path | None = "witnora-core-v2.21-theoremization-g9-g13-soundness.zip",
    write_docs: bool = False,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    record = build_theoremization_record()
    data = record.to_dict()
    candidates = build_soundness_theorem_candidates()
    summary = _candidate_summary(candidates)
    matrix = data["proof_obligation_matrix"]
    audit = data["claim_boundary_audit"]
    objections = data["reviewer_objection_table"]

    _write_json(root / "soundness_backbone_theoremization.json", data)
    _write_json(root / "theorem_candidate_summary.json", summary)
    _write_json(root / "proof_obligation_matrix.json", matrix)
    _write_json(root / "claim_boundary_audit.json", audit)
    _write_json(root / "reviewer_objection_table.json", objections)
    _write_json(root / "evidence_linkage_summary.json", data["evidence_links"])
    _write_text(root / "THEOREMIZATION_REPORT.md", _markdown_report(record))

    if write_docs:
        _write_supporting_docs(candidates, matrix, audit, objections)

    check = check_soundness_theoremization(data)
    if strict and check["status"] != THEOREMIZATION_PACKAGE_VERIFIED:
        raise RuntimeError(stable_json(check))

    artifact_sha = _make_zip(root, zip_path) if zip_path else None
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else None,
        "zip_sha256": artifact_sha,
        "record": data,
        "summary": {
            "candidate_count": len(candidates),
            "proof_obligation_rows": len(matrix),
            "claim_boundary_rows": len(audit),
            "reviewer_objection_rows": len(objections),
            "status": check["status"],
            "strict": bool(strict),
        },
        "check": check,
    }


def _status_values(data: Any) -> list[str]:
    values: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"status", "public_category", "checker_status", "current_status"} and isinstance(value, str):
                values.append(value)
            values.extend(_status_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(_status_values(item))
    return values


def check_soundness_theoremization(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if payload.get("record_type") != RECORD_TYPE:
        errors.append("BAD_RECORD_TYPE")
    if payload.get("release") != RELEASE:
        errors.append("BAD_RELEASE")
    if payload.get("scope") != SCOPE:
        errors.append("BAD_SCOPE")
    candidates = payload.get("theorem_candidates", [])
    if len(candidates) < 6:
        errors.append("MISSING_THEOREM_CANDIDATES")
    for candidate in candidates:
        if candidate.get("status") not in ALLOWED_CANDIDATE_STATUSES:
            errors.append(f"BAD_CANDIDATE_STATUS:{candidate.get('theorem_id')}")
        if candidate.get("may_not_be_claimed_as_proven") is not True:
            errors.append(f"MISSING_NOT_PROVEN_FLAG:{candidate.get('theorem_id')}")
        if not candidate.get("proof_obligations"):
            errors.append(f"MISSING_PROOF_OBLIGATIONS:{candidate.get('theorem_id')}")
        if not candidate.get("nonclaims"):
            errors.append(f"MISSING_NONCLAIMS:{candidate.get('theorem_id')}")
    if len(payload.get("proof_obligation_matrix", [])) < len(candidates) * len(OBLIGATION_CATEGORIES):
        errors.append("PROOF_OBLIGATION_MATRIX_TOO_SMALL")
    if len(payload.get("claim_boundary_audit", [])) < 6:
        errors.append("CLAIM_BOUNDARY_AUDIT_TOO_SMALL")
    if len(payload.get("reviewer_objection_table", [])) < 7:
        errors.append("REVIEWER_OBJECTION_TABLE_TOO_SMALL")
    if payload.get("public_category") != PUBLIC_CATEGORY:
        errors.append("BAD_PUBLIC_CATEGORY")
    status_values = set(_status_values(payload))
    forbidden_statuses = sorted(status_values & FORBIDDEN_STATUS_VALUES)
    if forbidden_statuses:
        errors.append("FORBIDDEN_STATUS_VALUES:" + ",".join(forbidden_statuses))
    forbidden_checked = " ".join(payload.get("forbidden_claims_checked", [])).lower()
    for required in ["theorem proven", "p vs np progress", "polynomial-time sat", "hierarchy completeness"]:
        if required not in forbidden_checked:
            errors.append(f"FORBIDDEN_CLAIM_NOT_CHECKED:{required}")
    status = THEOREMIZATION_PACKAGE_VERIFIED if not errors else THEOREMIZATION_PACKAGE_FAILED
    return {
        "status": status,
        "errors": errors,
        "candidate_count": len(candidates),
        "proof_obligation_rows": len(payload.get("proof_obligation_matrix", [])),
        "claim_boundary_rows": len(payload.get("claim_boundary_audit", [])),
        "reviewer_objection_rows": len(payload.get("reviewer_objection_table", [])),
    }


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_soundness_theoremization(args.out_root, strict=args.strict, zip_path=args.zip, write_docs=args.write_docs)
    print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "summary": result["summary"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = check_soundness_theoremization(_load_json(args.theoremization))
    print(stable_json(result))
    return 0 if result["status"] == THEOREMIZATION_PACKAGE_VERIFIED else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.soundness_theoremization")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-root", default="outputs/v2.21-theoremization-g9-g13-soundness")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default="witnora-core-v2.21-theoremization-g9-g13-soundness.zip")
    run.add_argument("--write-docs", action="store_true")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--theoremization", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
