"""External review package for Witnora v2.24.

v2.24 packages v2.14 through v2.23 for external review. It is a review and
reproducibility layer, not a solver/operator/theorem upgrade.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import shutil
from typing import Any
import zipfile

from .obstruction_dual import sha256_file, stable_json
from .tc063_theorem_hardening import (
    HARDENED_STATUS,
    TC063_THEOREM_HARDENING_VERIFIED,
    build_hardening_record,
    check_tc063_hardening,
)


PACKAGE_ID = "WITNORA-V2.24-EXTERNAL-REVIEW-PACKAGE"
PACKAGE_VERSION = "v2.24-external-review-package-v2.23"
UNKNOWN_METADATA_NOT_CLAIMED = "UNKNOWN_METADATA_NOT_CLAIMED"
ARTIFACT_NAME = "witnora-core-v2.24-external-review-package-v2.23.zip"

REQUIRED_MARKDOWN = [
    "EXTERNAL_REVIEW_PACKAGE_REPORT.md",
    "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md",
    "TC063_THEOREM_APPENDIX.md",
    "G9_G13_SOUNDNESS_APPENDIX.md",
    "REPRODUCIBILITY_GUIDE.md",
    "REVIEWER_GUIDE_V2_24.md",
    "CLAIM_BOUNDARY_TABLE.md",
    "LIMITATIONS_AND_NONCLAIMS.md",
    "REVIEWER_OBJECTION_RESPONSES.md",
    "RELEASE_HISTORY_V2_14_TO_V2_23.md",
    "CONTRIBUTION_TABLE.md",
    "EVIDENCE_SUMMARY.md",
]

REQUIRED_JSON = [
    "external_review_package_manifest.json",
    "release_manifest_v2_14_to_v2_23.json",
    "evidence_manifest.json",
    "claim_boundary_manifest.json",
    "theorem_candidate_manifest.json",
    "tc063_obligation_manifest.json",
    "reviewer_checklist.json",
    "reproducibility_manifest.json",
    "artifact_sha_manifest.json",
    "package_validation_summary.json",
]

FORBIDDEN_AFFIRMATIVE_FRAGMENTS = [
    "we solved p vs np",
    "p vs np progress is claimed",
    "polynomial-time sat algorithm",
    "all-sat coverage is claimed",
    "hierarchy completeness is claimed",
    "tc-063 is theorem_proven_unqualified",
    "native certificates are external proofs",
    "finite tests replace proof",
    "drat proof claimed",
]


@dataclass(frozen=True)
class ExternalReviewPackageManifest:
    package_id: str
    version: str
    scope: list[str]
    markdown_files: list[str]
    json_files: list[str]
    paper_path: str
    artifact_name: str
    test_command: str
    expected_test_count: int
    verification_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_zip(root: Path, zip_path: str | Path) -> str:
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(root).as_posix())
    return sha256_file(target)


def release_records_v214_to_v223() -> list[dict[str, Any]]:
    return [
        {
            "version": "v2.14",
            "tag": "v2.14-obstruction-dual-certificate",
            "commit": "c2fc1f971ccdc4aca963799f150bdb209d55982d",
            "release": "Obstruction Dual Certificate",
            "source_sha256": UNKNOWN_METADATA_NOT_CLAIMED,
            "artifact_sha256": "B10DAE866A00F155B99FE83BD6B055056835A82E4A274156C11A28712681F97D",
            "tests": "495 OK",
            "core_evidence": "G7 obstruction-dual certificates and missing-operator recommendations.",
        },
        {
            "version": "v2.15",
            "tag": "v2.15-graph-separator-lift",
            "commit": "47622bd686728f92ca018832fad11efd663d14ef",
            "release": "Graph Separator Lift",
            "source_sha256": "852E3C515892F9EA1757D2CE0895AEC6DB5F38EC09EA46330E81AF1EC06BA04D",
            "artifact_sha256": "E60859CEB47C098101E17C0405B28C4F00DA78047E5D1C15F215B20A44AC3267",
            "tests": "513 OK",
            "core_evidence": "G8 separator SAT lift and UNSAT cover certificates.",
        },
        {
            "version": "v2.16",
            "tag": "v2.16-composed-operator-orchestration",
            "commit": "379bfb0c8d990d92169f6c734888c0dafed5b175",
            "release": "Composed Operator Orchestration",
            "source_sha256": "D4C5C458A799827A1B4AE7DD27CB41377708F41390C82D18E0F9070C84AAE2B8",
            "artifact_sha256": "38237671E302A3CCF65AC73279A6820C7565AAC9FB924A6E5F38C9B62598E3BB",
            "tests": "533 OK",
            "core_evidence": "G9 certificate chaining with verified formula handoffs.",
        },
        {
            "version": "v2.17",
            "tag": "v2.17-circuit-projection-lift",
            "commit": "1d5177f7833dce700aa8d38e4add4740f485b2b0",
            "release": "Circuit Projection Lift",
            "source_sha256": "D75711609F08910D50591E6B1BEC7D553A3B1882DB8CAE291E836C5FE2D23C2D",
            "artifact_sha256": "311743336029B862E87F75EE1057A1FEA17870C010A3749456274ADA538CB042",
            "tests": "557 OK",
            "core_evidence": "G10 exact definitional projection and witness lift.",
        },
        {
            "version": "v2.18",
            "tag": "v2.18-proof-motif-generalization-checker",
            "commit": "ada52fe8c1f3c2b7a90486d28e26ab27b39a6d16",
            "release": "Proof Motif Generalization Checker",
            "source_sha256": "5AEC097DB6FC58BD1D7C480FCF162F8C23F95E184EF08FB769C3A55CCB6E2832",
            "artifact_sha256": "5BFA801064BEA3182BF987E849D010CC28F363049F8E310C761DB24FA64CA4FE",
            "tests": "574 OK",
            "core_evidence": "G11 checked generalized proof motifs.",
        },
        {
            "version": "v2.19",
            "tag": "v2.19-self-expanding-collapse-planner",
            "commit": "26493ea6b65013c05a91574f7b340bd8633dfcfd",
            "release": "Self-Expanding Collapse Planner",
            "source_sha256": "F1509FB6F3FD28CFCBA2DEF5E122F184A38336648DA3F5D90F86404CD89FC9B9",
            "artifact_sha256": "0CEAB228C3B5D6385D1C61B8B7AC4D46D0E50D309E2853EF6B2B822875346484",
            "tests": "593 OK",
            "core_evidence": "G12 plan-only certificates and missing-operator hypotheses.",
        },
        {
            "version": "v2.20",
            "tag": "v2.20-planner-guided-execution",
            "commit": "b9307cba7487c060421c8384b844539d96b8f48a",
            "release": "Planner-Guided Execution",
            "source_sha256": "07969B56E9F9BA131FD6299877ACEA90D42391FDF88C3231AC6E2E38AB686900",
            "artifact_sha256": "DA588151B49C2AB88322129A62804EE3E5BDEE85080E11FDC1FE909540F5BDAF",
            "tests": "610 OK",
            "core_evidence": "G13 verified finite plan-execution chains.",
        },
        {
            "version": "v2.21",
            "tag": "v2.21-theoremization-g9-g13-soundness",
            "commit": "d9fc586250c23c2932ebd1595d36ce521b6dff4e",
            "release": "G9-G13 Soundness Theoremization",
            "source_sha256": "DE79621FAD4CFAF836E095C552C3D08063F24503B9B0FAFF384E83F79964EDF1",
            "artifact_sha256": "75F58997D4E4197B83E9DF7B79314C961C1C68CD0B4701A9F9466A7605554A40",
            "tests": "623 OK",
            "core_evidence": "G9-G13 proof sketches and proof obligations.",
        },
        {
            "version": "v2.22",
            "tag": "v2.22-bounded-separator-affine-family-theorem",
            "commit": "e6bbca02a994c7b3dd996b9ff4de809e040647e0",
            "release": "Bounded Separator-Affine Family Theorem",
            "source_sha256": "C06382CA8A8E9217FEC0CC16CBAFBA80140437735DE8E567CD251F290C22E278",
            "artifact_sha256": "AB08AD169D4E315CF87FEF6EA1AA0A80BFB77E12A88CE3876C29DC331D8B0731",
            "tests": "650 OK",
            "core_evidence": "G14 restricted SAF(c,r) theorem attempt.",
        },
        {
            "version": "v2.23",
            "tag": "v2.23-harden-tc063-separator-affine-theorem",
            "commit": "ee944b22de7913990289888a9f4b89123461c2f7",
            "release": "TC-063 Theorem Hardening",
            "source_sha256": "04EEBFF728A914912C5D5B6787E5B7258A95804A970915D97C5E3B5B1F5AF30F",
            "artifact_sha256": "0991062AD8D17E7DD3D6A2001813FD6E4C4F81C3F1F93BF2CB5487761D2F00BC",
            "tests": "669 OK",
            "core_evidence": "TC-063 lemmas, proof obligations, validator, and scaling evidence.",
        },
    ]


def contribution_rows() -> list[dict[str, str]]:
    return [
        {
            "contribution": "Certified collapse-research framework",
            "claim": "Operator hierarchy and native certificate discipline for verifier-to-witness collapse research.",
            "evidence": "G0-G14 modules, tests, and package manifests.",
            "not_claimed": "P vs NP proof or complete SAT algorithm.",
        },
        {
            "contribution": "Obstruction-to-operator loop",
            "claim": "Obstruction fingerprints can promote candidate operators.",
            "evidence": "v2.14 through v2.18.",
            "not_claimed": "All obstructions are covered.",
        },
        {
            "contribution": "Planner-guided finite execution loop",
            "claim": "Finite plan-execution chains can be separately checked.",
            "evidence": "v2.19 and v2.20.",
            "not_claimed": "All plans succeed.",
        },
        {
            "contribution": "G9-G13 soundness backbone",
            "claim": "Formal proof sketches and proof obligations are recorded.",
            "evidence": "v2.21.",
            "not_claimed": "Mechanized theorem proof.",
        },
        {
            "contribution": "TC-063 restricted theorem",
            "claim": "SAF(c,r) theorem with proof obligations.",
            "evidence": "v2.22 and v2.23.",
            "not_claimed": "All-SAT theorem or unqualified theorem-proven status.",
        },
    ]


def claim_boundary_rows() -> list[dict[str, str]]:
    return [
        {"claim": "P vs NP solved", "status": "NOT CLAIMED", "evidence": "Nonclaim language in paper and manifests.", "not_claimed": "P vs NP proof or progress.", "reviewer_note": "Treat P vs NP only as motivation."},
        {"claim": "Polynomial-time SAT", "status": "NOT CLAIMED", "evidence": "Fixed-c caveat for TC-063 only.", "not_claimed": "Arbitrary SAT solver.", "reviewer_note": "Check fixed-parameter wording."},
        {"claim": "All-SAT coverage", "status": "NOT CLAIMED", "evidence": "TC-063 scope is SAF(c,r).", "not_claimed": "All CNFs.", "reviewer_note": "Attack restricted scope."},
        {"claim": "Hierarchy completeness", "status": "NOT CLAIMED", "evidence": "Gap and limitation docs.", "not_claimed": "Complete hierarchy.", "reviewer_note": "Ask whether G0-G14 should be a lattice."},
        {"claim": "TC-063 restricted family theorem", "status": HARDENED_STATUS, "evidence": "v2.23 hardening record.", "not_claimed": "THEOREM_PROVEN_UNQUALIFIED.", "reviewer_note": "Inspect proof obligations."},
        {"claim": "G9-G13 soundness", "status": "FORMAL_PROOF_SKETCH / PROOF_OBLIGATIONS", "evidence": "v2.21 theoremization.", "not_claimed": "Fully mechanized proof.", "reviewer_note": "Audit checker assumptions."},
        {"claim": "Native certificates", "status": "NATIVE_ONLY", "evidence": "Native checkers and claim-boundary tests.", "not_claimed": "External DRAT/LRAT/FRAT proof.", "reviewer_note": "Demand external proof bridge for external proof claims."},
        {"claim": "External DRAT/LRAT/FRAT proof", "status": "NOT CLAIMED", "evidence": "No external bridge in v2.24.", "not_claimed": "DRAT proof unless present.", "reviewer_note": "Native is not external."},
        {"claim": "Finite implementation evidence", "status": "REPRODUCED_TEST_EVIDENCE", "evidence": "Release tests through v2.23.", "not_claimed": "Finite tests substitute proof.", "reviewer_note": "Separate implementation support from theorem proof."},
        {"claim": "Planner execution loop", "status": "FINITE_PLANNER_EXECUTION_VERIFIED", "evidence": "v2.20.", "not_claimed": "All plans succeed.", "reviewer_note": "Inspect mismatch controls."},
    ]


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")).replace("\n", " ") for col in columns) + " |")
    return "\n".join(lines)


def paper_text() -> str:
    return """# Witnora Collapse Hierarchy: External Review Draft

## Abstract

Witnora is a certified collapse-research framework for studying verifier-to-witness collapse through operator grammars, native certificates, obstruction fingerprints, planner-guided finite executions, and restricted theorem candidates. Witnora does not claim a proof of P vs NP.

## Introduction

The project studies how SAT verification structure can sometimes be turned into witnesses, certificates, or proof obligations. The current package is designed for external attack and review.

## Problem Framing

The central question is how collapse operators can be stated, checked, composed, planned, and theoremized without overstating their scope.

## Related-Work Positioning

Witnora touches SAT preprocessing, certified SAT solving, structural SAT, affine reasoning, symmetry, cardinality, proof compression, automated theorem search, and AI reasoning evaluation. The contribution is the certificate-backed collapse hierarchy and reviewable obligation structure, not novelty of every individual primitive.

## Collapse Grammar Hierarchy G0-G14

The hierarchy now spans base simplification, XOR, symmetry, cardinality, capacity, affine residue, proof motif compression, obstruction dual certificates, separator lift, composed orchestration, circuit projection, proof motif generalization, collapse planning, planner-guided execution, and the bounded separator-affine theorem layer.

## Obstruction-To-Operator Loop

v2.14 identifies obstruction fingerprints and promotes graph separator, circuit projection, proof motif generalization, and composed orchestration directions.

## Certified Operators and Native Certificates

Native certificates are checked by Witnora checkers. Native certificates are not DRAT/LRAT/FRAT unless explicitly exported and externally checked.

## Composed Operator Orchestration

G9 composes certified operator steps only when step certificates, formula hashes, handoffs, and witness/proof lifts verify.

## Circuit Projection Lift

G10 projects only exact definitional gate encodings and requires lifted SAT witnesses to satisfy the original CNF.

## Proof Motif Generalization

G11 treats near-motif similarity as diagnostic until every concrete or parametric instantiation verifies.

## Self-Expanding Collapse Planner

G12 produces plan-only certificates. Planner certificates are plan-only unless paired with separate verified execution certificates.

## Planner-Guided Execution Loop

G13 pairs a verified plan with a separate verified execution chain. Matching a plan on finite fixtures does not prove all plans succeed.

## Soundness Theoremization G9-G13

v2.21 records G9-G13 soundness as formal proof sketches and proof obligations, not as mechanized proven theorems.

## TC-063 Bounded Separator-Affine Family Theorem

TC-063 is a restricted theorem with proof obligations over SAF(c,r), not an all-SAT theorem. It depends on fixed separator bound c, supported affine extraction bound r, G5 affine checker soundness, complete separator assignment enumeration, original-CNF SAT witness verification, and complete UNSAT cover verification.

## Experiments / Finite Evidence

Finite evidence supports implementation behavior but does not substitute for a family proof.

## Reproducibility

The v2.24 package includes release manifests, SHA records, tests, and reproduction instructions for external review.

## Claim Boundaries

No P vs NP proof, P vs NP progress, polynomial-time SAT, all-SAT coverage, hierarchy completeness, fake DRAT claim, or unqualified theorem-proven claim is made.

## Limitations

Native checkers are not proof-assistant verified. TC-063 has proof obligations. Several claims are finite evidence or proof sketches. The current hierarchy may need a lattice formalization.

## Future Work

External formalization of TC-063, G5 checker soundness, DRAT/LRAT/FRAT bridges, broader benchmark pressure, and proof-assistant integration are natural next steps.

## Appendix Pointers

See `TC063_THEOREM_APPENDIX.md`, `G9_G13_SOUNDNESS_APPENDIX.md`, `CLAIM_BOUNDARY_TABLE.md`, and `REPRODUCIBILITY_GUIDE.md`.
"""


def tc063_appendix(record: dict[str, Any]) -> str:
    lemmas = record["lemmas"]
    obligations = record["proof_obligation_matrix"]
    return "\n".join(
        [
            "# TC-063 Theorem Appendix",
            "",
            "TC-063 is not THEOREM_PROVEN_UNQUALIFIED.",
            f"TC-063 status: {HARDENED_STATUS}.",
            "",
            "## Formal SAF(c,r) Definition",
            "",
            "SAF(c,r) contains CNFs with a separator S of size at most fixed c such that every assignment to S leaves independent exact affine residual components accepted by G5 under supported affine bound r.",
            "",
            "## Theorem Statement",
            "",
            "For every F in SAF(c,r), fixed-c separator enumeration, complete separator-assignment enumeration, G5 residual affine checks, SAT witness lifting, and UNSAT assignment covers produce native certificates checkable by Witnora.",
            "",
            "## Fixed-c Polynomiality Caveat",
            "",
            "Polynomiality is only for fixed c and supported r. The exponential dependence on c is explicit through 2^c separator assignments and O(n^c) separator search.",
            "",
            "## Lemmas",
            "",
            "\n".join(f"- {lemma['lemma_name']}: {lemma['status']}" for lemma in lemmas),
            "",
            "## 32 Proof Obligations",
            "",
            "\n".join(f"- {row['obligation_id']}: {row['obligation']}" for row in obligations),
            "",
            "## Dependency Matrix",
            "",
            "\n".join(f"- {row['dependency']}: {row['status']}" for row in record["dependency_matrix"]),
            "",
            "## Structural SAF Validator Summary",
            "",
            f"Valid fixture: {record['structural_validator_summary']['valid_fixture']['validation_status']}. Non-affine control: {record['structural_validator_summary']['invalid_fixture']['validation_status']}.",
            "",
            "## Scaling Evidence Summary",
            "",
            f"{record['scaling_evidence_summary']['passed']}/{record['scaling_evidence_summary']['total']} scaling rows verified for n=64 and n=128. Scaling evidence is implementation support only.",
            "",
            "## Native Certificate Boundary",
            "",
            "Native certificates are not external DRAT/LRAT/FRAT proofs unless exported and externally checked.",
            "",
            "## Nonclaims",
            "",
            "- No P vs NP proof or progress.",
            "- No all-SAT theorem.",
            "- No hierarchy completeness.",
            "- No unqualified theorem-proven claim.",
            "- Finite tests do not substitute proof.",
            "",
        ]
    )


def g9_g13_appendix() -> str:
    return """# G9-G13 Soundness Appendix

## G9 Composed Orchestration

Soundness sketch: every operator step must have a verified certificate, matching input/output formula hashes, declared preservation, and verified final witness/proof obligations.

## G10 Circuit Projection Lift

Soundness sketch: only exact definitional gates may be projected; SAT lifts are checked against the original CNF; UNSAT preservation requires equisatisfiability obligations.

## G11 Proof Motif Generalization

Soundness sketch: near similarity is not proof. Every generalized reuse must be checked through concrete expansion or verified parametric instantiation.

## G12 Plan-Only Soundness

Soundness sketch: a plan certificate proves structural compatibility and claim-boundary safety only. It does not certify SAT, UNSAT, DRAT, theorem, or completeness.

## G13 Planner-Guided Execution

Soundness sketch: a verified plan must be paired with a separate verified execution certificate. Actual step certificates, handoffs, and final result obligations are checked independently.

## Closed-Loop Finite Evidence

The demonstrated loop is obstruction -> plan -> execution -> checked certificates -> verified result on finite fixtures only.

## Boundaries

These are proof sketches and proof obligations. Native certificates remain native-only. Finite evidence is not a family theorem. No P-vs-NP claim is made.
"""


def reviewer_guide_text() -> str:
    return """# Reviewer Guide v2.24

## What to Inspect First

Read the external review draft, TC-063 appendix, G9-G13 appendix, claim-boundary table, and evidence manifest.

## How to Reproduce Tests

Set `WITNORA_DRAT_TRIM` to a real `drat-trim.exe`, then run `python -m unittest discover -s tests -v`.

## Where TC-063 Lives

Inspect `TC063_THEOREM_APPENDIX.md`, `tc063_obligation_manifest.json`, and `theory/TC063_BOUNDED_SEPARATOR_AFFINE_HARDENED_THEOREM.md`.

## Where Proof Obligations Live

Read `tc063_obligation_manifest.json`, `G9_G13_SOUNDNESS_APPENDIX.md`, and the theory lemma files.

## What Claims Are Not Made

No P vs NP proof, no P vs NP progress, no all-SAT coverage, no hierarchy completeness, no polynomial-time arbitrary SAT claim, no fake DRAT claim, and no unqualified theorem-proven claim.

## How to Verify Archives and SHAs

Compare release entries in `artifact_sha_manifest.json` and `evidence_manifest.json` against local source and artifact zips.

## How to Inspect Native Certificates

Inspect native checker modules and their tests. Native means Witnora-checkable, not external DRAT/LRAT/FRAT.

## How to Attack the Framework

Attack G5 affine soundness, separator decomposition, UNSAT cover, native certificate boundary, finite-vs-family boundary, and claim-boundary wording.

## How to Audit Claim Boundaries

Read `CLAIM_BOUNDARY_TABLE.md` and `claim_boundary_manifest.json`, then compare against the paper draft and appendices.

## Known Limitations

Native checkers are not proof-assistant verified. TC-063 has proof obligations. Finite tests support implementation only. The hierarchy may need a lattice formalization.
"""


def reproducibility_guide_text() -> str:
    return """# Reproducibility Guide

## Environment Assumptions

Run from a clean source extraction with Python available.

## Set WITNORA_DRAT_TRIM

`$env:WITNORA_DRAT_TRIM='C:\\Users\\maham\\AppData\\Local\\Temp\\witnora-drat-trim-real\\drat-trim\\drat-trim.exe'`

## Run Full Tests

`python -m unittest discover -s tests -v`

## Run v2.22/v2.23 Tests

`python -m unittest tests.test_separator_affine_family_theorem tests.test_tc063_theorem_hardening_schema -v`

## Regenerate v2.24 Package

`python -m witnora_core.external_review_package_v224 run --out-root outputs/v2.24-external-review-package-v2.23 --strict`

## Outputs Generated

The package writes markdown and JSON manifests under `outputs/v2.24-external-review-package-v2.23/`.

## Source Archive Exclusions

Generated outputs, generated artifacts, and untracked standalone directories are excluded from source archives.

## Verify SHA256

Use `Get-FileHash -Algorithm SHA256 <path>` on Windows PowerShell.

## What Failures Mean

Test failures invalidate the package until reviewed. Validation failures usually indicate a missing file, forbidden claim, or stale manifest.
"""


def limitations_text() -> str:
    return """# Limitations and Nonclaims

- Witnora does not claim a proof of P vs NP.
- Witnora does not claim P vs NP progress.
- Witnora does not claim polynomial-time SAT.
- Witnora does not claim all-SAT coverage.
- Witnora does not claim hierarchy completeness.
- TC-063 is restricted to SAF(c,r) and remains `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`.
- Native certificates are not DRAT/LRAT/FRAT unless exported and externally checked.
- Finite tests support implementation behavior but do not substitute for proof.
- Native checkers are not proof-assistant verified.
"""


def reviewer_objections_text() -> str:
    return """# Reviewer Objection Responses

## This is not a P vs NP proof.

Correct. The package frames Witnora as a certified collapse-research framework, not a P vs NP proof.

## TC-063 is not fully proven.

Correct. TC-063 is `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`.

## Native certificates are not external proofs.

Correct. Native certificates are not DRAT/LRAT/FRAT unless externally exported and checked.

## Finite tests do not prove a family theorem.

Correct. Finite evidence supports implementation behavior only.

## Checker assumptions matter.

Correct. G5 affine soundness and native checker soundness are explicit dependencies.
"""


def release_history_text(records: list[dict[str, Any]]) -> str:
    lines = ["# Release History v2.14 to v2.23", ""]
    for record in records:
        lines.append(f"- {record['version']} `{record['tag']}`: {record['release']} ({record['tests']})")
    lines.append("")
    return "\n".join(lines)


def evidence_summary_text(records: list[dict[str, Any]]) -> str:
    lines = ["# Evidence Summary", "", "This package summarizes reproducible finite evidence and theorem-obligation artifacts. It does not claim P vs NP progress.", ""]
    for record in records:
        lines.append(f"## {record['version']} {record['release']}")
        lines.append("")
        lines.append(record["core_evidence"])
        lines.append("")
    return "\n".join(lines)


def contribution_table_text() -> str:
    return "# Contribution Table\n\n" + _markdown_table(contribution_rows(), ["contribution", "claim", "evidence", "not_claimed"]) + "\n"


def claim_boundary_table_text() -> str:
    return "# Claim Boundary Table\n\n" + _markdown_table(claim_boundary_rows(), ["claim", "status", "evidence", "not_claimed", "reviewer_note"]) + "\n"


def package_report_text(check: dict[str, Any]) -> str:
    return f"""# External Review Package Report

Package: `{PACKAGE_VERSION}`

Validation status: `{check['verification_status']}`

This package presents Witnora as a certified collapse-research framework with one restricted infinite-family theorem candidate and proof obligations.

It is not a P vs NP proof, not all-SAT coverage, not hierarchy completeness, and not an external DRAT/LRAT/FRAT proof package.
"""


def build_json_payloads() -> dict[str, Any]:
    hardening = build_hardening_record().to_dict()
    releases = release_records_v214_to_v223()
    claims = claim_boundary_rows()
    return {
        "release_manifest": {"releases": releases},
        "evidence_manifest": {"releases": releases, "core_scope": "v2.14 through v2.23 external review evidence"},
        "claim_boundary_manifest": {"rows": claims},
        "theorem_candidate_manifest": {
            "tc063": {
                "id": "TC-063",
                "status": HARDENED_STATUS,
                "scope": "SAF(c,r)",
                "not_claimed": ["P vs NP", "all SAT", "hierarchy completeness", "THEOREM_PROVEN_UNQUALIFIED"],
            },
            "g9_g13": "FORMAL_PROOF_SKETCH / PROOF_OBLIGATIONS",
        },
        "tc063_obligation_manifest": {
            "lemmas": hardening["lemmas"],
            "proof_obligations": hardening["proof_obligation_matrix"],
            "dependency_matrix": hardening["dependency_matrix"],
            "structural_validator_summary": hardening["structural_validator_summary"],
            "scaling_evidence_summary": hardening["scaling_evidence_summary"],
        },
        "reviewer_checklist": {
            "items": [
                "Inspect TC-063 proof obligations.",
                "Attack G5 affine soundness dependency.",
                "Audit separator decomposition and UNSAT cover.",
                "Verify native-vs-external certificate boundary.",
                "Check finite-vs-family wording.",
            ]
        },
        "reproducibility_manifest": {
            "test_command": "python -m unittest discover -s tests -v",
            "drat_trim_env": "WITNORA_DRAT_TRIM",
            "expected_tests": 679,
            "package_command": "python -m witnora_core.external_review_package_v224 run --out-root outputs/v2.24-external-review-package-v2.23 --strict",
        },
        "artifact_sha_manifest": {
            record["tag"]: {
                "source_sha256": record["source_sha256"],
                "artifact_sha256": record["artifact_sha256"],
                "commit": record["commit"],
            }
            for record in releases
        },
    }


def _scan_forbidden_text(text: str) -> list[str]:
    lower = text.lower()
    return [fragment for fragment in FORBIDDEN_AFFIRMATIVE_FRAGMENTS if fragment in lower]


def check_external_review_package(package_root: str | Path) -> dict[str, Any]:
    root = Path(package_root)
    errors: list[str] = []
    for name in REQUIRED_MARKDOWN:
        if not (root / name).exists():
            errors.append(f"MISSING_MARKDOWN:{name}")
    for name in REQUIRED_JSON:
        if not (root / name).exists():
            errors.append(f"MISSING_JSON:{name}")
    combined_text = "\n".join((root / name).read_text(encoding="utf-8") for name in REQUIRED_MARKDOWN if (root / name).exists())
    for fragment in _scan_forbidden_text(combined_text):
        errors.append("FORBIDDEN_CLAIM:" + fragment.upper().replace(" ", "_"))
    tc_text = (root / "TC063_THEOREM_APPENDIX.md").read_text(encoding="utf-8") if (root / "TC063_THEOREM_APPENDIX.md").exists() else ""
    for required in ["SAF(c,r)", "TC-063 status: RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS", "TC-063 is not THEOREM_PROVEN_UNQUALIFIED"]:
        if required not in tc_text:
            errors.append("TC063_APPENDIX_MISSING:" + required)
    if tc_text.count("- TC063-L") < 8 and "Separator Decomposition" not in tc_text:
        errors.append("TC063_LEMMAS_MISSING")
    try:
        obligations = json.loads((root / "tc063_obligation_manifest.json").read_text(encoding="utf-8"))
        if len(obligations.get("proof_obligations", [])) != 32:
            errors.append("TC063_OBLIGATION_COUNT_MISMATCH")
    except FileNotFoundError:
        pass
    claim_text = (root / "CLAIM_BOUNDARY_TABLE.md").read_text(encoding="utf-8") if (root / "CLAIM_BOUNDARY_TABLE.md").exists() else ""
    for required in ["P vs NP solved", "Polynomial-time SAT", "All-SAT coverage", "Hierarchy completeness", "TC-063 restricted family theorem"]:
        if required not in claim_text:
            errors.append("CLAIM_BOUNDARY_ROW_MISSING:" + required)
    try:
        evidence = json.loads((root / "evidence_manifest.json").read_text(encoding="utf-8"))
        versions = {row["version"] for row in evidence.get("releases", [])}
        if not all(f"v2.{n}" in versions for n in range(15, 24)):
            errors.append("EVIDENCE_MANIFEST_RELEASE_RANGE_INCOMPLETE")
    except FileNotFoundError:
        pass
    status_values: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"status", "verification_status", "checker_status", "validation_status"} and isinstance(item, str):
                    status_values.append(item)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for name in REQUIRED_JSON:
        path = root / name
        if path.exists():
            walk(json.loads(path.read_text(encoding="utf-8")))
    bad_statuses = sorted(set(status_values) & {"HARD", "UNKNOWN"})
    if bad_statuses:
        errors.append("FORBIDDEN_STATUS:" + ",".join(bad_statuses))
    verification_status = "PASS" if not errors else "FAIL"
    return {"verification_status": verification_status, "errors": errors, "required_markdown": REQUIRED_MARKDOWN, "required_json": REQUIRED_JSON}


def run_external_review_package(
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = ARTIFACT_NAME,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    paper_path = Path("paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md")
    hardening = build_hardening_record().to_dict()
    releases = release_records_v214_to_v223()
    payloads = build_json_payloads()

    _write_text(paper_path, paper_text())
    markdown_payloads = {
        "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md": paper_text(),
        "TC063_THEOREM_APPENDIX.md": tc063_appendix(hardening),
        "G9_G13_SOUNDNESS_APPENDIX.md": g9_g13_appendix(),
        "REPRODUCIBILITY_GUIDE.md": reproducibility_guide_text(),
        "REVIEWER_GUIDE_V2_24.md": reviewer_guide_text(),
        "CLAIM_BOUNDARY_TABLE.md": claim_boundary_table_text(),
        "LIMITATIONS_AND_NONCLAIMS.md": limitations_text(),
        "REVIEWER_OBJECTION_RESPONSES.md": reviewer_objections_text(),
        "RELEASE_HISTORY_V2_14_TO_V2_23.md": release_history_text(releases),
        "CONTRIBUTION_TABLE.md": contribution_table_text(),
        "EVIDENCE_SUMMARY.md": evidence_summary_text(releases),
    }
    for name, text in markdown_payloads.items():
        _write_text(root / name, text)

    manifest = ExternalReviewPackageManifest(
        package_id=PACKAGE_ID,
        version=PACKAGE_VERSION,
        scope=[record["tag"] for record in releases],
        markdown_files=REQUIRED_MARKDOWN,
        json_files=REQUIRED_JSON,
        paper_path=str(paper_path),
        artifact_name=str(zip_path) if zip_path else "",
        test_command="python -m unittest discover -s tests -v",
        expected_test_count=679,
        verification_status="PENDING",
    ).to_dict()
    _write_json(root / "external_review_package_manifest.json", manifest)
    _write_json(root / "release_manifest_v2_14_to_v2_23.json", payloads["release_manifest"])
    _write_json(root / "evidence_manifest.json", payloads["evidence_manifest"])
    _write_json(root / "claim_boundary_manifest.json", payloads["claim_boundary_manifest"])
    _write_json(root / "theorem_candidate_manifest.json", payloads["theorem_candidate_manifest"])
    _write_json(root / "tc063_obligation_manifest.json", payloads["tc063_obligation_manifest"])
    _write_json(root / "reviewer_checklist.json", payloads["reviewer_checklist"])
    _write_json(root / "reproducibility_manifest.json", payloads["reproducibility_manifest"])
    _write_json(root / "artifact_sha_manifest.json", payloads["artifact_sha_manifest"])
    _write_json(root / "package_validation_summary.json", {"verification_status": "PENDING", "errors": []})
    _write_text(
        root / "EXTERNAL_REVIEW_PACKAGE_REPORT.md",
        "# External Review Package Report\n\nValidation status: `PENDING`.\n",
    )

    check = check_external_review_package(root)
    _write_json(root / "package_validation_summary.json", check)
    _write_text(root / "EXTERNAL_REVIEW_PACKAGE_REPORT.md", package_report_text(check))
    manifest["verification_status"] = check["verification_status"]
    _write_json(root / "external_review_package_manifest.json", manifest)

    if strict and check["verification_status"] != "PASS":
        raise RuntimeError("external review package validation failed: " + ";".join(check["errors"]))
    digest = _make_zip(root, zip_path) if zip_path else ""
    return {"out_root": str(root), "zip": str(zip_path) if zip_path else "", "zip_sha256": digest, "validation": check, "manifest": manifest}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_external_review_package(args.out_root, strict=args.strict, zip_path=args.zip)
    print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "validation": result["validation"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    result = check_external_review_package(args.package_root)
    print(stable_json(result))
    return 0 if result["verification_status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.external_review_package_v224")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--out-root", default="outputs/v2.24-external-review-package-v2.23")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default=ARTIFACT_NAME)
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--package-root", required=True)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
