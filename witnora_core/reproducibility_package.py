"""External paper and reproducibility package for the collapse hierarchy.

v2.12 packages existing evidence for external review. It does not add a new
operator, alter solver/proof/XOR logic, or promote empirical deltas into
strictness theorems.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .finite_edge_certificate import (
    DEFAULT_EDGE_INSTANCES,
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G1_XOR,
    G2_SYMMETRY_CERTIFIED,
    LOWER_REPLAY_NO_COLLAPSE,
    build_finite_edge_delta_certificate,
)
from .finite_strictness_certificate import (
    DEFAULT_FINITE_INSTANCES,
    FINITE_STRICTNESS_CERTIFIED,
    G0_WIDTH_C,
    G1_XOR_FOR_STRICTNESS,
    build_finite_strictness_certificate,
)
from .strictness_proof import make_zip, sha256_file, stable_json


PACKAGE_VERSION = "v2.12-paper-reproducibility-package"
PACKAGE_ID = "WITNORA-V2.12-PAPER-REPRODUCIBILITY"
NOT_RECORDED = "NOT_RECORDED_IN_THIS_ARTIFACT"
EXPECTED_TEST_COUNT = 463


@dataclass(frozen=True)
class ReproducibilityPackageManifest:
    package_id: str
    version: str
    source_release: dict[str, Any]
    artifact_release: dict[str, Any]
    included_releases: list[dict[str, Any]]
    included_certificates: list[dict[str, Any]]
    included_reports: list[str]
    paper_paths: list[str]
    evidence_tables: list[str]
    reproduction_scripts: list[str]
    claim_boundary_files: list[str]
    sha256_records: dict[str, str]
    test_command: str
    expected_test_count: int
    drat_trim_requirement: str
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceSummaryRecord:
    hierarchy_edge: str
    evidence_type: str
    witness_family: str
    instances: list[str]
    lower_evidence: str
    upper_evidence: str
    certificate_type: str
    checker_status: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimBoundaryRecord:
    claim: str
    allowed_wording: str
    forbidden_wording: str
    reason: str
    affected_sections: list[str]
    tests_guarding_boundary: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def release_records() -> list[dict[str, Any]]:
    return [
        {
            "tag": "v2.0-collapse-theory-lab",
            "commit": "d594134125e0bf2f0db69957268e18bb13f6b15e",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "6FD7726127FE8617D790D170C02570F150C28C4E11F58A0938A152C119FF8253",
            "secondary_artifacts": [
                {
                    "name": "witnora-core-v2.0-operator-frontier.zip",
                    "sha256": "D6479262FB5BD9F0B5CBE2C0DAF15C0685F7DC4D663CC2637BEBE5C185B9FE12",
                }
            ],
        },
        {
            "tag": "v2.1-collapse-theory-frontier",
            "commit": "30984267261412a52e2e19a2a120cdecaab908fd",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "924C555F04A40A83B755A3FD89712091D1E6F8B88FADDCE8145A3569B3D82169",
        },
        {
            "tag": "v2.2-certified-symmetry-collapse",
            "commit": "0430a39e0a4fac3b3c52fc2518d3f44c46200296",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "8BB062FF2ADF08BC2A8FD9088A75A14BAE6D7A78C3844502BD86E8EBB83FEE6F",
        },
        {
            "tag": "v2.3-pigeonhole-cardinality-collapse",
            "commit": "fa26d76226e1ab7edea72943c8aec0710d5ca50b",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "F78767A898923FC0F2071A2E5C5F7ED6F3755AF188FFC1683772E307F22EE40E",
        },
        {
            "tag": "v2.4-operator-genesis",
            "commit": "b9916f7a7c5dafa07883a235510a88356c0749d8",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "7D345AD954FC95E8104840D10FA4A3E6EE7E23D6EC9B41B6EA2A34AD5D4821F8",
        },
        {
            "tag": "v2.5-orbit-capacity-counting",
            "commit": "bedac2a21b3e17a95aa1138fea38a002875034cb",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "9A1C66D9032BF3457FE10DF82CCBEEDAE90D389E2ECB6849C79DC0B442D70876",
        },
        {
            "tag": "v2.6-affine-residue-collapse",
            "commit": "695ae0f805ca63a6abd4f5f07748c5e93e896efd",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "DF8CE21DB1AE50C267FF77584517AC30BBCB64D3E1793682FB6568E26217DD7C",
        },
        {
            "tag": "v2.7-proof-motif-compression",
            "commit": "eab9aebd005cee7ddf55f608f36d698a099e9a4c",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "7F2A7C4656CC60D49D0C93B5F9F364EF703EB7018CC4D90790D6B1656AE22417",
        },
        {
            "tag": "v2.8-collapse-hierarchy-theoremization",
            "commit": "36ad36460fefc506b8bdc43904ba2a914b1988a7",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "68068774A8455EBFBB490697C85176B42698F15AD50EDEE9A680A0BBC300CCAD",
        },
        {
            "tag": "v2.9-restricted-g0-g1-strictness",
            "commit": "083ea0f12d330855f35c6db87abde9e771085855",
            "source_sha256": NOT_RECORDED,
            "artifact_sha256": "DF54400039C7CDCF3C5E44E4D259BA7D9FD2DDA66FDEDC6F1F5C6AB1BA0BAA18",
        },
        {
            "tag": "v2.10-finite-strictness-certificate",
            "commit": "4eabff20f2dd2f6100fe2be586d22593d26ad7b4",
            "source_sha256": "ED4E7EF05F95FEBF2399EE3C857748D8845AEA26F2D8BF0DE751E04926B6FA4D",
            "artifact_sha256": "4603D5F8CE52C3DEC67EE8D33C20ED5EFB34812906D6511F30BC488E14CB3424",
        },
        {
            "tag": "v2.11-finite-edge-delta-g1-g2",
            "commit": "2d53697551ae649eea0274cda4ef129fd928399b",
            "source_sha256": "3DF12122A0264CF4CB070033AC55C89510AFE743B94CC5E5CE29C41C507453E5",
            "artifact_sha256": "9AFB64684B07534F7B844902800E3B4064BB379BD2C93CA98F358C345FD9BB49",
        },
    ]


def evidence_summary_records() -> list[EvidenceSummaryRecord]:
    return [
        EvidenceSummaryRecord(
            hierarchy_edge="G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS",
            evidence_type=FINITE_STRICTNESS_CERTIFIED,
            witness_family="restricted Tseitin/XOR-chain finite witnesses",
            instances=list(DEFAULT_FINITE_INSTANCES),
            lower_evidence="certified width obstruction",
            upper_evidence="G1_XOR upper-bound verified",
            certificate_type="FINITE_STRICTNESS_CERTIFICATE",
            checker_status="FINITE_STRICTNESS_CERTIFICATE_VERIFIED",
            claim_boundary="finite restricted strictness certificate only; not a scalable family theorem",
        ),
        EvidenceSummaryRecord(
            hierarchy_edge="G1_XOR -> G2_SYMMETRY_CERTIFIED",
            evidence_type=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
            witness_family="cycle graph 3-coloring symmetry witnesses",
            instances=list(DEFAULT_EDGE_INSTANCES),
            lower_evidence="bounded replay no-collapse",
            upper_evidence="G2 symmetry certificate verified",
            certificate_type="FINITE_EDGE_DELTA_CERTIFICATE",
            checker_status="FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED",
            claim_boundary="finite empirical edge delta only; lower replay is not a lower-bound proof",
        ),
        EvidenceSummaryRecord(
            hierarchy_edge="G2_SYMMETRY_CERTIFIED -> G3_SYMMETRY_CARDINALITY_CERTIFIED",
            evidence_type="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            witness_family="pigeonhole/cardinality native certificates",
            instances=["php_3_2", "php_4_3", "php_5_4", "php_6_5"],
            lower_evidence="G2 symmetry diagnostic/replay boundary",
            upper_evidence="native pigeonhole counting certificates",
            certificate_type="PIGEONHOLE_NATIVE_COUNTING_CERTIFICATE",
            checker_status="PIGEONHOLE_CERTIFICATE_VERIFIED",
            claim_boundary="empirical operator evidence, not a family theorem",
        ),
        EvidenceSummaryRecord(
            hierarchy_edge="G3_SYMMETRY_CARDINALITY_CERTIFIED -> G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            evidence_type="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            witness_family="local Hall/capacity-deficit assignment formulas",
            instances=["hall_local_3_2", "hall_local_4_3", "hall_local_5_4"],
            lower_evidence="G3 standard pigeonhole recognizer duplicate controls excluded",
            upper_evidence="native orbit-capacity certificates",
            certificate_type="ORBIT_CAPACITY_DEFICIT_CONTRADICTION",
            checker_status="ORBIT_CAPACITY_CERTIFICATE_VERIFIED",
            claim_boundary="local capacity-deficit evidence only; not a complete matching/allocation solver",
        ),
        EvidenceSummaryRecord(
            hierarchy_edge="G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE -> G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
            evidence_type="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            witness_family="exact high-arity GF(2) affine residue encodings",
            instances=["parity_arity_7_unsat", "parity_arity_8_unsat", "parity_arity_9_unsat", "parity_arity_10_unsat"],
            lower_evidence="lower arity-cap affine boundary",
            upper_evidence="native GF(2) elimination certificates",
            certificate_type="AFFINE_RESIDUE_GF2_CERTIFICATE",
            checker_status="AFFINE_RESIDUE_CERTIFICATE_VERIFIED",
            claim_boundary="exact extraction only; no broad modular solver claim",
        ),
        EvidenceSummaryRecord(
            hierarchy_edge="G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE -> G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE",
            evidence_type="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            witness_family="repeated proof motif macro-certificate examples",
            instances=["motif_ladder_4", "motif_ladder_8", "renamed_conflict_motif_8", "motif_chain_with_selectors_8"],
            lower_evidence="G5 semantic operators do not certify proof-motif rows under the package boundary",
            upper_evidence="native macro-proof motif certificates",
            certificate_type="PROOF_MOTIF_COMPRESSION_CERTIFICATE",
            checker_status="PROOF_MOTIF_CERTIFICATE_VERIFIED",
            claim_boundary="proof motif evidence only; no DRAT or proof-system completeness claim",
        ),
    ]


def claim_boundary_records() -> list[ClaimBoundaryRecord]:
    return [
        ClaimBoundaryRecord(
            "P vs NP",
            "P vs NP is a long-range motivation.",
            "Witnora proves P vs NP progress.",
            "The package contains bounded artifacts, not a complexity-theory resolution.",
            ["Abstract", "Relationship to P vs NP", "Non-Claims"],
            ["NO_PNP_CLAIM_PASS", "PAPER_REQUIRED_NONCLAIMS_PASS"],
        ),
        ClaimBoundaryRecord(
            "polynomial-time SAT",
            "This work does not claim a polynomial-time SAT algorithm.",
            "Witnora is a polynomial-time SAT algorithm.",
            "The hierarchy is a bounded research program over selected certificate-backed routes.",
            ["Non-Claims", "Limitations"],
            ["NO_POLYTIME_SAT_CLAIM_PASS"],
        ),
        ClaimBoundaryRecord(
            "hierarchy completeness",
            "The hierarchy is a research program.",
            "The G0-G6 hierarchy is complete.",
            "Gaps and proof obligations remain open.",
            ["Gap Analysis", "Future Work"],
            ["NO_HIERARCHY_COMPLETENESS_CLAIM_PASS"],
        ),
        ClaimBoundaryRecord(
            "full hierarchy strictness",
            "Edges have graded evidence; strictness is claimed only where certificate conditions justify it.",
            "All hierarchy edges are strict theorems.",
            "Only v2.10 has finite strictness with certified lower obstruction.",
            ["Evidence Summary", "Proof Obligations"],
            ["EVIDENCE_SUMMARY_GRADES_PASS"],
        ),
        ClaimBoundaryRecord(
            "full G0_BASE strictness",
            "v2.10 concerns restricted G0_WIDTH_C, not full G0_BASE.",
            "Full G0_BASE strictness is proven.",
            "Full G0 contains additional routes not discharged by the finite width certificate.",
            ["Finite Strictness Certificate"],
            ["FINITE_STRICTNESS_G0_G1_SUMMARY_PASS"],
        ),
        ClaimBoundaryRecord(
            "finite strictness certificate",
            "FINITE_STRICTNESS_CERTIFIED applies to finite restricted G0_WIDTH_C -> G1_XOR witnesses with lower obstruction evidence.",
            "Finite certificates prove scalable family theorems.",
            "The scope is finite and restricted.",
            ["Evidence Summary", "Reproducibility"],
            ["FINITE_STRICTNESS_G0_G1_SUMMARY_PASS", "NO_FALSE_FAMILY_THEOREM_CLAIM_PASS"],
        ),
        ClaimBoundaryRecord(
            "finite empirical edge delta",
            "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED records replayed finite delta evidence.",
            "The empirical edge delta is a strictness theorem.",
            "G1 lower replay is bounded non-acceptance, not obstruction proof.",
            ["Finite Empirical Edge Delta"],
            ["FINITE_EDGE_DELTA_G1_G2_SUMMARY_PASS", "CLAIM_BOUNDARY_FORBIDDEN_WORDING_PASS"],
        ),
        ClaimBoundaryRecord(
            "native certificate vs DRAT",
            "Native certificates are not DRAT proofs unless explicitly exported and checked.",
            "Native certificates are DRAT proofs.",
            "Native checkers and external proof formats have different trust semantics.",
            ["Native Certificate Types", "Non-Claims"],
            ["NATIVE_CERT_NOT_DRAT_PASS"],
        ),
        ClaimBoundaryRecord(
            "generated operator vs theorem",
            "Generated operators are prototypes or candidates unless proof obligations are discharged.",
            "Generated operators are theorems.",
            "Implementation evidence and theorem evidence are separate.",
            ["Operator Genesis", "Proof Obligations"],
            ["CLAIM_BOUNDARY_TABLE_PASS"],
        ),
        ClaimBoundaryRecord(
            "replayed no-collapse vs lower-bound proof",
            "LOWER_REPLAY_NO_COLLAPSE is bounded replay evidence.",
            "Replay no-collapse is a lower-bound proof.",
            "A lower-bound proof requires an independently checked obstruction.",
            ["Finite Empirical Edge Delta"],
            ["CLAIM_BOUNDARY_FORBIDDEN_WORDING_PASS"],
        ),
        ClaimBoundaryRecord(
            "empirical evidence vs family theorem",
            "EMPIRICAL_EVIDENCE_NOT_THEOREM marks bounded evidence and proof obligations.",
            "Empirical evidence is a family theorem.",
            "Scaling and lower-bound obligations remain open.",
            ["Evidence Summary", "Proof Obligations"],
            ["NO_FALSE_FAMILY_THEOREM_CLAIM_PASS"],
        ),
    ]


def external_paper_text() -> str:
    return "\n".join(
        [
            "# Witnora Collapse Hierarchy: Certificate-Backed Operator Discovery for Verifier-to-Witness Collapse",
            "",
            "## Abstract",
            "",
            "Witnora is a certificate-backed collapse hierarchy and operator-discovery program for studying verifier-to-witness collapse. It compares bounded grammars, emits native certificates where implemented, and records proof obligations where evidence remains empirical.",
            "",
            "## Introduction",
            "",
            "The project studies when structured CNF verifier instances admit deterministic, replayable collapse paths to witnesses or proof certificates. The current artifact packages the G0-G6 hierarchy, finite certificates, empirical edge evidence, and reviewer-facing reproduction steps.",
            "",
            "## Motivation: Verifier-to-Witness Collapse",
            "",
            "The long-range motivation is to understand routes from efficiently checkable verifier instances to efficiently discoverable witnesses or certificates. Witnora treats this as an experimental theorem-building program, not as a solved complexity question.",
            "",
            "## Non-Claims",
            "",
            "This work does not prove P vs NP.",
            "This work does not claim a polynomial-time SAT algorithm.",
            "Strictness is only claimed where a finite strictness certificate with lower obstruction evidence is verified.",
            "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED is not a lower-bound proof.",
            "Native certificates are not DRAT proofs unless explicitly exported and checked.",
            "The hierarchy is a research program, not a complete SAT algorithm.",
            "",
            "## Bounded Collapse Classes W_B(G)",
            "",
            "For a bound profile B and grammar G, W_B(G) is the operational set of formulas for which Witnora emits a SAT witness verified against the original CNF, an externally checked proof, or an accepted native certificate whose checker succeeds within configured bounds.",
            "",
            "## Grammar Hierarchy G0-G6",
            "",
            "- G0_BASE: UP, PLE, SUB, BCE, VE, components, 2SAT, bounded treewidth.",
            "- G1_XOR: G0 plus exact bounded XOR extraction and affine elimination.",
            "- G2_SYMMETRY_CERTIFIED: exact automorphism validation and SAT witness reconstruction.",
            "- G3_SYMMETRY_CARDINALITY_CERTIFIED: exact AMO/ALO and pigeonhole counting certificates.",
            "- G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE: local Hall/capacity-deficit native certificates.",
            "- G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE: exact high-arity GF(2) native certificates.",
            "- G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE: native macro-proof motif certificates.",
            "",
            "## Native Certificate Types",
            "",
            "Native certificates include width obstruction records, XOR/GF(2) certificates, symmetry witness reconstruction, pigeonhole counting, orbit-capacity deficits, affine residue traces, and proof-motif macro certificates. Native certificates are checked by Witnora-native checkers and are not DRAT proofs unless explicitly exported and checked.",
            "",
            "## Operator Genesis",
            "",
            "Operator genesis extracts obstruction fingerprints and proposes operator schemas. Generated candidates are not trusted until implemented, checked, tested, red-teamed, and frozen.",
            "",
            "## Finite Strictness Certificate: G0_WIDTH_C -> G1_XOR",
            "",
            "v2.10 records `FINITE_STRICTNESS_CERTIFIED` for finite restricted witnesses: `tseitin_10`, `xor_chain_unsat_n5`, `tseitin_12`, `xor_chain_unsat_n7`, `tseitin_14`, and `xor_chain_unsat_n9`. The lower side has certified width obstruction; the upper side has verified G1 XOR evidence. This is finite and restricted, not a scalable family theorem.",
            "",
            "## Finite Empirical Edge Delta: G1_XOR -> G2_SYMMETRY_CERTIFIED",
            "",
            "v2.11 records `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` for `cycle_4_3color`, `cycle_6_3color`, `cycle_8_3color`, and `cycle_10_3color`. The lower side is bounded replay no-collapse under G1_XOR, not a lower-bound proof. The upper side verifies G2 symmetry SAT witness reconstruction.",
            "",
            "## Empirical Evidence for G2-G6",
            "",
            "G2-G6 evidence includes pigeonhole/cardinality certificates, local Hall/capacity-deficit certificates, high-arity affine residue certificates, and proof motif macro-certificates. These are empirical operator-delta records unless a stricter proof object is explicitly supplied.",
            "",
            "## Proof Obligations",
            "",
            "Open obligations include full G0_BASE non-collapse, scalable family lower bounds, checker soundness writeups, cost-model completeness, and external proof bridges where sound.",
            "",
            "## Gap Analysis",
            "",
            "Open gaps include random 3-SAT, general circuit-SAT, arbitrary PB encodings, non-exact affine patterns, realistic SAT competition instances, and formulas where no confident obstruction fingerprint is found.",
            "",
            "## Relationship to P vs NP",
            "",
            "P vs NP is the long-range motivation. Witnora studies certificate-backed collapse structure that may clarify verifier-to-witness routes, while explicitly avoiding progress claims.",
            "",
            "## Why This Does Not Prove P vs NP",
            "",
            "The current results are bounded, operational, and finite or empirical unless otherwise labeled. They do not establish general lower bounds, hierarchy completeness, or a polynomial-time algorithm for SAT.",
            "",
            "## Reproducibility",
            "",
            "The v2.12 package includes release SHA records, evidence summaries, claim-boundary tables, reproduction steps, validation scripts, and a package manifest. The expected full test command is `python -m unittest discover -s tests -v` with real drat-trim configured when available.",
            "",
            "## Limitations",
            "",
            "Finite certificates do not imply family theorems. Empirical edge deltas do not imply lower bounds. Native certificates do not replace external proof formats unless a bridge is checked against the original CNF.",
            "",
            "## Future Work",
            "",
            "Next work should either submit the package for external review or add another finite edge certificate while preserving the evidence-grade distinction introduced in v2.10 and v2.11.",
            "",
        ]
    )


def evidence_summary_markdown(records: list[EvidenceSummaryRecord]) -> str:
    lines = [
        "# Evidence Summary",
        "",
        "This table separates finite strictness, finite empirical edge deltas, empirical operator evidence, theorem candidates, and proof obligations.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## {record.hierarchy_edge}",
                "",
                f"- Evidence type: `{record.evidence_type}`",
                f"- Witness family: {record.witness_family}",
                f"- Instances: {', '.join(f'`{item}`' for item in record.instances)}",
                f"- Lower evidence: {record.lower_evidence}",
                f"- Upper evidence: {record.upper_evidence}",
                f"- Certificate type: `{record.certificate_type}`",
                f"- Checker status: `{record.checker_status}`",
                f"- Claim boundary: {record.claim_boundary}",
                "",
            ]
        )
    return "\n".join(lines)


def claim_boundary_markdown(records: list[ClaimBoundaryRecord]) -> str:
    lines = [
        "# Claim Boundary Table",
        "",
        "| Claim | Allowed wording | Forbidden wording | Reason | Tests/checks |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            "| {claim} | {allowed} | {forbidden} | {reason} | {tests} |".format(
                claim=record.claim,
                allowed=record.allowed_wording,
                forbidden=record.forbidden_wording,
                reason=record.reason,
                tests=", ".join(f"`{item}`" for item in record.tests_guarding_boundary),
            )
        )
    lines.append("")
    return "\n".join(lines)


def reproduction_steps_text() -> str:
    return "\n".join(
        [
            "# Reproduction Steps",
            "",
            "1. Start from the v2.12 source tree.",
            "2. If real drat-trim is available, set `WITNORA_DRAT_TRIM` to the executable path.",
            "3. Run `python -m unittest discover -s tests -v`.",
            "4. Regenerate v2.10 with `python -m witnora_core.finite_strictness_certificate build --out-root outputs/v2.10-finite-strictness-certificate --strict`.",
            "5. Regenerate v2.11 with `python -m witnora_core.finite_edge_certificate build --edge G1_XOR:G2_SYMMETRY_CERTIFIED --out-root outputs/v2.11-finite-edge-delta-g1-g2 --strict`.",
            "6. Regenerate this package with `python -m witnora_core.reproducibility_package build --out-root outputs/v2.12-paper-reproducibility-package --strict`.",
            "7. Validate it with `python scripts/validate_v2_12_package.py --package-root outputs/v2.12-paper-reproducibility-package`.",
            "",
            "No internet, external API, or marketplace workflow is required.",
            "",
        ]
    )


def external_review_packet_text() -> str:
    return "\n".join(
        [
            "# External Review Packet",
            "",
            "## What Witnora claims",
            "",
            "Witnora is a certificate-backed collapse hierarchy and operator-discovery program for studying verifier-to-witness collapse.",
            "",
            "## What Witnora does not claim",
            "",
            "It does not claim P vs NP progress, a polynomial-time SAT algorithm, hierarchy completeness, scalable family theorems from finite certificates, or peer-review acceptance.",
            "",
            "## How to reproduce",
            "",
            "Run the full unit suite, rebuild v2.10/v2.11 certificates, then run the v2.12 validation script.",
            "",
            "## What to inspect first",
            "",
            "Inspect the evidence summary, claim-boundary table, finite strictness certificate, finite empirical edge-delta certificate, and external paper draft.",
            "",
            "## Known weaknesses",
            "",
            "The G1-to-G2 edge has replay evidence, not lower-bound evidence. Most G2-G6 edges remain empirical. Native certificates are not external DRAT proofs unless bridges are explicitly checked.",
            "",
            "## Requested reviewer questions",
            "",
            "- Are W_B(G) definitions useful?",
            "- Is the finite strictness certificate meaningful?",
            "- Is the empirical edge delta label honest?",
            "- Are native certificates adequate for this research program?",
            "- Which proof obligation should be attacked next?",
            "- Which operator is most novel?",
            "- Is this paper framing acceptable for a workshop?",
            "",
            "## Proof obligations",
            "",
            "Full G0_BASE strictness, scalable family lower bounds, checker soundness notes, and external proof bridges remain open.",
            "",
            "## Future work",
            "",
            "Either submit this package for external feedback or build the next finite edge certificate with the same evidence-grade discipline.",
            "",
        ]
    )


def paper_submission_checklist_text() -> str:
    return "\n".join(
        [
            "# Paper Submission Checklist",
            "",
            "- Confirm all non-claims are present.",
            "- Confirm evidence grades are correct.",
            "- Confirm finite edge delta is not described as strictness theorem.",
            "- Confirm native certificates are not described as DRAT.",
            "- Confirm release SHA manifest is included.",
            "- Confirm reproduction scripts run without network access.",
            "- Confirm no external acceptance or peer-review claim is made.",
            "",
        ]
    )


def package_file_index(root: Path) -> list[dict[str, Any]]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "path": str(path.relative_to(root)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    return files


def release_sha_manifest() -> dict[str, Any]:
    return {
        "version": PACKAGE_VERSION,
        "records": release_records(),
        "missing_hash_marker": NOT_RECORDED,
        "note": "Hashes not recorded in code are explicitly marked rather than invented.",
    }


def build_manifest(root: Path, sha_records: dict[str, str]) -> ReproducibilityPackageManifest:
    finite_strictness = build_finite_strictness_certificate().to_dict()
    finite_edge = build_finite_edge_delta_certificate().to_dict()
    return ReproducibilityPackageManifest(
        package_id=PACKAGE_ID,
        version=PACKAGE_VERSION,
        source_release={"tag": PACKAGE_VERSION, "source_sha256": NOT_RECORDED},
        artifact_release={"name": "witnora-core-v2.12-paper-reproducibility-package.zip", "sha256": NOT_RECORDED},
        included_releases=release_records(),
        included_certificates=[
            {
                "type": finite_strictness["type"],
                "status": finite_strictness["strictness_status"],
                "instances": [record["instance_id"] for record in finite_strictness["instances"]],
            },
            {
                "type": finite_edge["type"],
                "status": finite_edge["evidence_grade"],
                "instances": [record["instance_id"] for record in finite_edge["instances"]],
            },
        ],
        included_reports=[
            "EVIDENCE_SUMMARY.md",
            "CLAIM_BOUNDARY_TABLE.md",
            "EXTERNAL_REVIEW_PACKET.md",
            "PAPER_SUBMISSION_CHECKLIST.md",
        ],
        paper_paths=[
            "paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md",
            "outputs/v2.12-paper-reproducibility-package/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md",
        ],
        evidence_tables=["evidence_summary.json", "EVIDENCE_SUMMARY.md"],
        reproduction_scripts=["scripts/reproduce_v2_12_package.py", "scripts/validate_v2_12_package.py"],
        claim_boundary_files=["claim_boundary_table.json", "CLAIM_BOUNDARY_TABLE.md"],
        sha256_records=sha_records,
        test_command="python -m unittest discover -s tests -v",
        expected_test_count=EXPECTED_TEST_COUNT,
        drat_trim_requirement="Set WITNORA_DRAT_TRIM for real drat-trim smoke tests.",
        verification_status="PACKAGE_GENERATED_VALIDATION_REQUIRED",
    )


def validate_package(root: str | Path) -> dict[str, Any]:
    package_root = Path(root)
    required = [
        "REPRODUCIBILITY_MANIFEST.json",
        "RELEASE_SHA256_MANIFEST.json",
        "EVIDENCE_SUMMARY.md",
        "evidence_summary.json",
        "CLAIM_BOUNDARY_TABLE.md",
        "claim_boundary_table.json",
        "REPRODUCTION_STEPS.md",
        "EXTERNAL_REVIEW_PACKET.md",
        "PAPER_SUBMISSION_CHECKLIST.md",
        "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md",
        "package_file_index.json",
    ]
    errors: list[str] = []
    for name in required:
        if not (package_root / name).is_file():
            errors.append(f"missing required file: {name}")
    paper = (package_root / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md").read_text(encoding="utf-8") if (package_root / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md").is_file() else ""
    required_nonclaims = [
        "This work does not prove P vs NP.",
        "This work does not claim a polynomial-time SAT algorithm.",
        "Strictness is only claimed where a finite strictness certificate with lower obstruction evidence is verified.",
        "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED is not a lower-bound proof.",
        "Native certificates are not DRAT proofs unless explicitly exported and checked.",
        "The hierarchy is a research program, not a complete SAT algorithm.",
    ]
    for phrase in required_nonclaims:
        if phrase not in paper:
            errors.append(f"missing paper non-claim: {phrase}")
    evidence_path = package_root / "evidence_summary.json"
    if evidence_path.is_file():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        grades = {record["hierarchy_edge"]: record["evidence_type"] for record in evidence["evidence_summary"]}
        if grades.get("G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS") != FINITE_STRICTNESS_CERTIFIED:
            errors.append("G0->G1 evidence grade mismatch")
        if grades.get("G1_XOR -> G2_SYMMETRY_CERTIFIED") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
            errors.append("G1->G2 evidence grade mismatch")
    text_blob = ""
    scanned_for_claims = [
        "REPRODUCIBILITY_MANIFEST.json",
        "EVIDENCE_SUMMARY.md",
        "evidence_summary.json",
        "REPRODUCTION_STEPS.md",
        "EXTERNAL_REVIEW_PACKET.md",
        "PAPER_SUBMISSION_CHECKLIST.md",
        "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md",
    ]
    for name in scanned_for_claims:
        path = package_root / name
        if path.is_file():
            text_blob += "\n" + path.read_text(encoding="utf-8")
    forbidden_positive = [
        "Witnora proves P vs NP progress",
        "Witnora is a polynomial-time SAT algorithm",
        "The G0-G6 hierarchy is complete",
        "All hierarchy edges are strict theorems",
        "The empirical edge delta is a strictness theorem",
        "Native certificates are DRAT proofs.",
        "External reviewers accepted this work",
        "peer-reviewed and accepted",
    ]
    for phrase in forbidden_positive:
        if phrase in text_blob:
            errors.append(f"forbidden claim present: {phrase}")
    return {
        "package_root": str(package_root),
        "required_files_checked": required,
        "errors": errors,
        "verification_status": "PASS" if not errors else "FAIL",
    }


def build_reproducibility_package(
    *,
    out_root: str | Path = "outputs/v2.12-paper-reproducibility-package",
    strict: bool = False,
    zip_path: str | Path = "witnora-core-v2.12-paper-reproducibility-package.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    evidence_records = evidence_summary_records()
    claim_records = claim_boundary_records()
    evidence_payload = {"evidence_summary": [record.to_dict() for record in evidence_records]}
    claim_payload = {"claim_boundary_table": [record.to_dict() for record in claim_records]}
    paper_text = external_paper_text()

    _write_json(root / "RELEASE_SHA256_MANIFEST.json", release_sha_manifest())
    _write_json(root / "evidence_summary.json", evidence_payload)
    _write_text(root / "EVIDENCE_SUMMARY.md", evidence_summary_markdown(evidence_records))
    _write_json(root / "claim_boundary_table.json", claim_payload)
    _write_text(root / "CLAIM_BOUNDARY_TABLE.md", claim_boundary_markdown(claim_records))
    _write_text(root / "REPRODUCTION_STEPS.md", reproduction_steps_text())
    _write_text(root / "EXTERNAL_REVIEW_PACKET.md", external_review_packet_text())
    _write_text(root / "PAPER_SUBMISSION_CHECKLIST.md", paper_submission_checklist_text())
    _write_text(root / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md", paper_text)
    _write_text(Path("paper") / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md", paper_text)

    initial_index = package_file_index(root)
    sha_records = {entry["path"]: entry["sha256"] for entry in initial_index}
    manifest = build_manifest(root, sha_records).to_dict()
    _write_json(root / "REPRODUCIBILITY_MANIFEST.json", manifest)
    _write_json(root / "package_file_index.json", {"files": package_file_index(root)})
    validation = validate_package(root)
    _write_json(root / "v2_12_reproducibility_validation.json", validation)
    _write_json(root / "package_file_index.json", {"files": package_file_index(root)})
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "strict": strict,
        "manifest": manifest,
        "evidence_summary": evidence_payload,
        "claim_boundary_table": claim_payload,
        "validation": validation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/validate the v2.12 paper reproducibility package")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out-root", default="outputs/v2.12-paper-reproducibility-package")
    build.add_argument("--strict", action="store_true")
    build.add_argument("--zip", default="witnora-core-v2.12-paper-reproducibility-package.zip")
    validate = sub.add_parser("validate")
    validate.add_argument("--package-root", default="outputs/v2.12-paper-reproducibility-package")
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build_reproducibility_package(out_root=args.out_root, strict=args.strict, zip_path=args.zip)
        print(
            stable_json(
                {
                    "out_root": result["out_root"],
                    "zip": result["zip"],
                    "zip_sha256": result["zip_sha256"],
                    "verification_status": result["validation"]["verification_status"],
                }
            )
        )
        return 0 if result["validation"]["verification_status"] == "PASS" else 1
    if args.command == "validate":
        result = validate_package(args.package_root)
        print(stable_json(result))
        return 0 if result["verification_status"] == "PASS" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
