"""v2.13 paper hardening and reviewer-defense package.

This module only packages and validates reviewer-facing documentation. It does
not add an operator, change solver behavior, change proof export, or alter XOR
logic/evidence grades.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .finite_edge_certificate import FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED
from .finite_strictness_certificate import FINITE_STRICTNESS_CERTIFIED
from .reproducibility_package import (
    claim_boundary_markdown,
    claim_boundary_records,
    evidence_summary_records,
    external_paper_text,
)
from .strictness_proof import make_zip, sha256_file, stable_json


PACKAGE_VERSION = "v2.13-paper-hardening-reviewer-defense"
PACKAGE_ID = "WITNORA-V2.13-PAPER-HARDENING-REVIEWER-DEFENSE"
EXPECTED_TEST_COUNT = 485


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def contribution_table_text() -> str:
    return "\n".join(
        [
            "# Contribution Table",
            "",
            "| Contribution | What is claimed | Evidence type | What is not claimed |",
            "| --- | --- | --- | --- |",
            "| Bounded collapse hierarchy G0-G6 | Operational sequence for bounded collapse grammars | Research program / empirical evidence | Complete SAT algorithm or complete hierarchy |",
            "| Native certificate taxonomy | Certificate objects with native checkers | Checker-backed artifacts | Native certificates as DRAT unless exported and checked |",
            "| Operator Genesis Engine | Candidate operator schemas from obstruction fingerprints | Generated candidates / proof obligations | Fully autonomous theorem discovery |",
            "| Generated operators G4/G5/G6 | Three generated candidates promoted to prototypes | Empirical operator evidence | General matching, modular arithmetic, or proof-compression completeness |",
            "| Finite strictness certificate G0_WIDTH_C -> G1_XOR | Finite restricted certificate with lower obstruction evidence | FINITE_STRICTNESS_CERTIFIED | Full G0_BASE or scalable family theorem |",
            "| Finite empirical edge-delta certificate G1_XOR -> G2_SYMMETRY_CERTIFIED | Finite replayed edge delta with upper witness verification | FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED | Lower-bound proof or strictness theorem |",
            "| Proof-obligation matrix | Explicit theorem-promotion obligations | Formal proof obligations | Obligations discharged by listing them |",
            "| Reproducibility package | External review packet and replay scripts | Package validation | Peer-review acceptance |",
            "| Claim-boundary table | Allowed and forbidden wording with test guards | Validation guards | Elimination of all future review risk |",
            "",
        ]
    )


def reviewer_objection_table_text() -> str:
    return "\n".join(
        [
            "# Reviewer Objection Table",
            "",
            "| Objection | Response |",
            "| --- | --- |",
            "| This does not prove P vs NP. | Correct. P vs NP is only motivation. No P vs NP progress is claimed. |",
            "| This is finite evidence, not a family theorem. | Correct. v2.10 is finite strictness certification; family theorem remains a proof obligation. |",
            "| Empirical edge deltas are not lower bounds. | Correct. v2.11 explicitly labels them FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED. |",
            "| Native certificates are not DRAT. | Correct. Native certificates are independently checked by Witnora checkers; DRAT is only claimed when exported and externally checked. |",
            "| Some operators are known ideas. | Correct. Witnora's novelty is the certificate-backed hierarchy, operator-genesis loop, evidence grading, and proof-obligation structure. |",
            "| The hierarchy may be a lattice, not a line. | Correct. The current line is an operational sequence; partial-order/lattice formalization is future work. |",
            "| The system is synthetic/crafted. | Partly correct. Current families are controlled witnesses for operator behavior; broader benchmarks are a future gap. |",
            "| Why no external peer review yet? | v2.13 prepares the artifact for external review; no peer-review acceptance is claimed. |",
            "",
        ]
    )


def limitations_and_nonclaims_text() -> str:
    return "\n".join(
        [
            "# Limitations and Non-Claims",
            "",
            "- No P vs NP progress is claimed.",
            "- No polynomial-time SAT algorithm is claimed.",
            "- No hierarchy completeness is claimed.",
            "- No family theorem follows from finite certificates.",
            "- Empirical edge deltas are not strictness theorems.",
            "- Native certificates are not DRAT unless exported and checked against the original CNF.",
            "- The current hierarchy is operational and may later become a partial order or lattice.",
            "- Many instances are controlled or synthetic witnesses for operator behavior.",
            "- Broader external benchmarks remain future work.",
            "- Native checkers are not formally verified proof-assistant artifacts.",
            "- v2.13 does not add a new operator.",
            "- v2.13 does not change solver logic, proof-export logic, or XOR-solving logic.",
            "- v2.13 does not claim external acceptance or peer review.",
            "",
        ]
    )


def reviewer_guide_text() -> str:
    return "\n".join(
        [
            "# Reviewer Guide",
            "",
            "## What to read first",
            "",
            "Read the external paper draft, then the contribution table, evidence summary, claim-boundary appendix, and reviewer objection table.",
            "",
            "## What to reproduce first",
            "",
            "Run the full unit suite, validate the v2.12 package, then validate the v2.13 hardening package.",
            "",
            "## How to run validation",
            "",
            "`python scripts/validate_v2_13_paper_package.py --package-root outputs/v2.13-paper-hardening-reviewer-defense`",
            "",
            "## How to inspect v2.10 finite strictness certificate",
            "",
            "Inspect the G0_WIDTH_C -> G1_XOR evidence row. Confirm `FINITE_STRICTNESS_CERTIFIED` appears only where certified lower obstruction evidence exists.",
            "",
            "## How to inspect v2.11 finite empirical edge delta",
            "",
            "Inspect the G1_XOR -> G2_SYMMETRY_CERTIFIED row. Confirm lower replay is bounded non-acceptance, not a lower-bound proof.",
            "",
            "## How to inspect evidence grades",
            "",
            "Check `EVIDENCE_SUMMARY.md` and verify v2.10 remains `FINITE_STRICTNESS_CERTIFIED` while v2.11 remains `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`.",
            "",
            "## How to inspect claim boundaries",
            "",
            "Read `CLAIM_BOUNDARY_APPENDIX.md` and compare allowed wording, forbidden wording, reason, and validation guard.",
            "",
            "## What Witnora claims",
            "",
            "Witnora claims a certificate-backed collapse hierarchy and operator-discovery program with finite certificates, empirical edge deltas, native certificates, and explicit proof obligations.",
            "",
            "## What Witnora does not claim",
            "",
            "It does not claim P vs NP progress, polynomial-time SAT, hierarchy completeness, peer-review acceptance, or family theorems from finite certificates.",
            "",
            "## Known weaknesses",
            "",
            "Current witnesses are often controlled. Native checkers are not proof-assistant verified. Several hierarchy edges remain empirical rather than theorem-proven. The current chain may later need a lattice formalization.",
            "",
            "## Suggested reviewer questions",
            "",
            "- Are W_B(G) definitions useful?",
            "- Is finite strictness certification meaningful?",
            "- Is the empirical edge-delta label honest?",
            "- Are native certificates adequate for this research program?",
            "- Which proof obligation should be attacked next?",
            "- Which operator is most novel?",
            "- Should the hierarchy be a lattice instead of a chain?",
            "- Is the paper framing acceptable as a workshop/system/research-program paper?",
            "",
        ]
    )


def external_review_packet_text() -> str:
    return "\n".join(
        [
            "# External Review Packet",
            "",
            "## One-page summary",
            "",
            "Witnora is a certificate-backed collapse hierarchy and operator-discovery program for studying verifier-to-witness collapse. v2.13 hardens the external paper and reviewer package without adding operators or changing evidence grades.",
            "",
            "## Contribution table",
            "",
            "See `CONTRIBUTION_TABLE.md` for the claim/evidence/non-claim split.",
            "",
            "## Claim-boundary summary",
            "",
            "The package separates finite strictness, empirical edge deltas, empirical operator evidence, theorem candidates, and proof obligations.",
            "",
            "## Artifact checklist",
            "",
            "- External paper draft",
            "- Reviewer guide",
            "- Contribution table",
            "- Reviewer objection table",
            "- Limitations and non-claims",
            "- Claim-boundary appendix",
            "- v2.13 validation JSON",
            "",
            "## Reproduction command",
            "",
            "`python -m unittest discover -s tests -v`",
            "",
            "## Expected test count",
            "",
            f"{EXPECTED_TEST_COUNT}",
            "",
            "## Expected validation status",
            "",
            "`PASS`",
            "",
            "## Known limitations",
            "",
            "Finite certificates remain finite. Empirical edge deltas are not lower bounds. Native certificates are not DRAT unless exported and checked. No external acceptance or peer review is claimed.",
            "",
            "## What feedback is requested",
            "",
            "Feedback is requested on the usefulness of W_B(G), finite certificates, empirical edge-delta wording, native certificates, proof obligations, and whether the hierarchy should be formalized as a lattice.",
            "",
            "## Suggested order of inspection",
            "",
            "1. Paper non-claims",
            "2. Contribution table",
            "3. Evidence grades",
            "4. v2.10 finite strictness row",
            "5. v2.11 finite empirical edge-delta row",
            "6. Claim-boundary appendix",
            "7. Reproduction and validation scripts",
            "",
        ]
    )


def paper_hardening_summary_text() -> str:
    return "\n".join(
        [
            "# Paper Hardening Summary",
            "",
            "v2.13 strengthens the external paper/reproducibility package with related work positioning, contribution and objection tables, explicit limitations, a reviewer guide, an artifact inspection order, and validation tests.",
            "",
            "It does not add a new operator, change solver logic, change proof-export logic, change XOR-solving logic, or change evidence grades.",
            "",
        ]
    )


def claim_boundary_appendix_text() -> str:
    return "# Claim-Boundary Appendix\n\n" + claim_boundary_markdown(claim_boundary_records()).split("\n", 2)[-1]


def validate_paper_hardening_package(root: str | Path) -> dict[str, Any]:
    package_root = Path(root)
    required = [
        "REVIEWER_GUIDE.md",
        "EXTERNAL_REVIEW_PACKET.md",
        "PAPER_HARDENING_SUMMARY.md",
        "CONTRIBUTION_TABLE.md",
        "REVIEWER_OBJECTION_TABLE.md",
        "LIMITATIONS_AND_NONCLAIMS.md",
        "CLAIM_BOUNDARY_APPENDIX.md",
        "v2_13_validation.json",
    ]
    errors: list[str] = []
    for name in required:
        if not (package_root / name).is_file():
            errors.append(f"missing required v2.13 file: {name}")

    paper_path = Path("paper") / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md"
    paper = paper_path.read_text(encoding="utf-8") if paper_path.is_file() else ""
    for section in [
        "## Related Work",
        "## Contribution Table",
        "## Reviewer Objection Table",
        "## Limitations",
        "## Claim-Boundary Appendix",
    ]:
        if section not in paper:
            errors.append(f"paper missing section: {section}")

    required_nonclaims = [
        "This work does not prove P vs NP.",
        "This work does not claim a polynomial-time SAT algorithm.",
        "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED is not a lower-bound proof.",
        "Native certificates are not DRAT proofs unless explicitly exported and checked.",
        "The hierarchy is a research program, not a complete SAT algorithm.",
    ]
    for phrase in required_nonclaims:
        if phrase not in paper:
            errors.append(f"paper missing non-claim: {phrase}")

    grades = {record.hierarchy_edge: record.evidence_type for record in evidence_summary_records()}
    if grades.get("G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS") != FINITE_STRICTNESS_CERTIFIED:
        errors.append("v2.10 evidence grade changed")
    if grades.get("G1_XOR -> G2_SYMMETRY_CERTIFIED") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
        errors.append("v2.11 evidence grade changed")

    paper_claim_scan = paper.split("## Reviewer Objection Table", 1)[0]
    safe_scan = "\n".join(
        [
            paper_claim_scan,
            (package_root / "EXTERNAL_REVIEW_PACKET.md").read_text(encoding="utf-8")
            if (package_root / "EXTERNAL_REVIEW_PACKET.md").is_file()
            else "",
            (package_root / "PAPER_HARDENING_SUMMARY.md").read_text(encoding="utf-8")
            if (package_root / "PAPER_HARDENING_SUMMARY.md").is_file()
            else "",
        ]
    )
    forbidden_positive = [
        "v2.13 adds G7",
        "v2.13 adds a new operator",
        "Witnora proves P vs NP progress",
        "Witnora is a polynomial-time SAT algorithm",
        "The G0-G6 hierarchy is complete",
        "The empirical edge delta is a strictness theorem",
        "Native certificates are DRAT proofs.",
        "External reviewers accepted this work",
        "peer-review acceptance is claimed",
        "peer-reviewed and accepted",
    ]
    for phrase in forbidden_positive:
        if phrase in safe_scan:
            errors.append(f"forbidden positive claim present: {phrase}")

    return {
        "package_id": PACKAGE_ID,
        "version": PACKAGE_VERSION,
        "package_root": str(package_root),
        "required_files_checked": required,
        "evidence_grades": grades,
        "no_new_operator": True,
        "solver_logic_changed": False,
        "proof_export_logic_changed": False,
        "xor_logic_changed": False,
        "errors": errors,
        "verification_status": "PASS" if not errors else "FAIL",
    }


def build_paper_hardening_package(
    *,
    out_root: str | Path = "outputs/v2.13-paper-hardening-reviewer-defense",
    zip_path: str | Path = "witnora-core-v2.13-paper-hardening-reviewer-defense.zip",
    strict: bool = False,
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    _write_text(Path("paper") / "WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md", external_paper_text())
    _write_text(root / "REVIEWER_GUIDE.md", reviewer_guide_text())
    _write_text(root / "EXTERNAL_REVIEW_PACKET.md", external_review_packet_text())
    _write_text(root / "PAPER_HARDENING_SUMMARY.md", paper_hardening_summary_text())
    _write_text(root / "CONTRIBUTION_TABLE.md", contribution_table_text())
    _write_text(root / "REVIEWER_OBJECTION_TABLE.md", reviewer_objection_table_text())
    _write_text(root / "LIMITATIONS_AND_NONCLAIMS.md", limitations_and_nonclaims_text())
    _write_text(root / "CLAIM_BOUNDARY_APPENDIX.md", claim_boundary_appendix_text())
    _write_json(root / "v2_13_validation.json", {"verification_status": "PENDING"})
    validation = validate_paper_hardening_package(root)
    _write_json(root / "v2_13_validation.json", validation)
    file_index = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            file_index.append({"path": str(path.relative_to(root)).replace("\\", "/"), "sha256": sha256_file(path)})
    _write_json(root / "package_file_index.json", {"files": file_index})
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "validation": validation,
        "strict": strict,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/validate the v2.13 paper hardening package")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out-root", default="outputs/v2.13-paper-hardening-reviewer-defense")
    build.add_argument("--zip", default="witnora-core-v2.13-paper-hardening-reviewer-defense.zip")
    build.add_argument("--strict", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--package-root", default="outputs/v2.13-paper-hardening-reviewer-defense")
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build_paper_hardening_package(out_root=args.out_root, zip_path=args.zip, strict=args.strict)
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
        result = validate_paper_hardening_package(args.package_root)
        print(stable_json(result))
        return 0 if result["verification_status"] == "PASS" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
