"""Reusable verification-report and trust-card helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from .claim_boundary import scan_text_for_claim_boundary
from .proof import verify_certificate_bundle

VERDICT_VERIFIED = "VERIFIED"
VERDICT_PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
VERDICT_NOT_VERIFIED = "NOT_VERIFIED"
VERDICT_OVERCLAIM = "OVERCLAIM"
VERDICT_ARTIFACT_INTEGRITY_VERIFIED = "ARTIFACT_INTEGRITY_VERIFIED"

CERT_RELEASE_ARTIFACT_INTEGRITY_VERIFIED = "RELEASE_ARTIFACT_INTEGRITY_VERIFIED"
DEPTH_METADATA_HASH_CHECKS_ONLY = "metadata_hash_checks_only"
CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN = "heuristic_text_scan"

CLAIM_SCANNER_LIMITATION_TEXT = (
    "The claim-boundary scanner is a heuristic text safety net, not a proof of "
    "absence of overclaims. It can miss paraphrases, ambiguous wording, or "
    "context-sensitive claims. A human audit is still required before public release."
)

ARTIFACT_INTEGRITY_SCOPE_TEXT = (
    "The artifact hashes match the manifest, required files are present, and the "
    "claim-boundary scanner found no affirmative forbidden claims. This is a "
    "metadata and artifact-integrity check. It does not rerun the scientific "
    "proofs, rerun drat-trim on all proofs, or rerun the benchmark diagnostic."
)

DEFAULT_METADATA_ONLY_RISK_FLAGS = [
    "METADATA_ONLY",
    "DRAT_TRIM_NOT_RERUN",
    "INDEPENDENT_CHECKER_NOT_RERUN",
    "CLAIM_SCAN_HEURISTIC_ONLY",
]

DEFAULT_ALLOWED_CLAIMS = [
    "Witnora reports only scoped certification levels supported by evidence.",
    "Externally verified UNSAT requires an accepted proof artifact and checker record.",
    "Native-only results are separated from externally verified results.",
]

DEFAULT_FORBIDDEN_CLAIMS = [
    "parity support",
    "broad XOR extraction",
    "CryptoMiniSat-style extraction",
    "competitive SAT solving",
    "industrial benchmark performance",
    "full DRAT/RAT/LRAT/FRAT support",
    "P vs NP progress",
    "HARD or UNKNOWN status claims",
]


@dataclass
class VerificationReport:
    claim: str
    logical_status: str
    discovery_route: str
    certification_level: str
    public_category: str
    evidence_files: list[str] = field(default_factory=list)
    external_checkers: list[str] = field(default_factory=list)
    checker_results: list[dict[str, Any]] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    reproducibility_status: str = "NOT_ASSESSED"
    verification_depth: str = DEPTH_METADATA_HASH_CHECKS_ONLY
    evidence_checked: list[dict[str, Any]] = field(default_factory=list)
    checks_performed: list[dict[str, Any]] = field(default_factory=list)
    claim_scan_depth: str = CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN
    last_verification_timestamp: str = ""
    allowed_claims: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_CLAIMS))
    forbidden_claims: list[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN_CLAIMS))
    risk_flags: list[str] = field(default_factory=list)
    verdict: str = VERDICT_NOT_VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "logical_status": self.logical_status,
            "discovery_route": self.discovery_route,
            "certification_level": self.certification_level,
            "public_category": self.public_category,
            "evidence_files": self.evidence_files,
            "external_checkers": self.external_checkers,
            "checker_results": self.checker_results,
            "artifact_hashes": self.artifact_hashes,
            "reproducibility_status": self.reproducibility_status,
            "verification_depth": self.verification_depth,
            "evidence_checked": self.evidence_checked,
            "checks_performed": self.checks_performed,
            "claim_scan_depth": self.claim_scan_depth,
            "last_verification_timestamp": self.last_verification_timestamp,
            "allowed_claims": self.allowed_claims,
            "forbidden_claims": self.forbidden_claims,
            "risk_flags": self.risk_flags,
            "verdict": self.verdict,
        }


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_verification_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Witnora Verification Report",
        "",
        "## Claim Being Audited",
        "",
        str(report.get("claim", "")),
        "",
        "## Evidence Provided",
        "",
    ]
    for item in report.get("evidence_files", []):
        lines.append(f"- `{item}`")
    if not report.get("evidence_files"):
        lines.append("- none")
    lines.extend(["", "## Verification Depth", "", f"`{report.get('verification_depth', '')}`"])
    if report.get("verification_depth") == DEPTH_METADATA_HASH_CHECKS_ONLY:
        lines.extend(["", ARTIFACT_INTEGRITY_SCOPE_TEXT])
    lines.extend(["", "## Checks Performed", ""])
    checks_performed = report.get("checks_performed", [])
    if checks_performed:
        for check in checks_performed:
            lines.append(
                f"- `{check.get('name', '')}`: {str(check.get('status', '')).lower()} "
                f"(depth: `{check.get('depth', '')}`)"
            )
    else:
        lines.append("- none recorded")
    lines.extend(["", "## Checker Results", ""])
    for result in report.get("checker_results", []):
        name = result.get("checker", result.get("check", "checker"))
        passed = result.get("passed", result.get("verified", False))
        lines.append(f"- `{name}`: {'pass' if passed else 'fail'}")
    lines.extend(["", "## Evidence Checked", ""])
    evidence_checked = report.get("evidence_checked", [])
    if evidence_checked:
        for item in evidence_checked:
            lines.append(
                f"- `{item.get('path', '')}` ({item.get('kind', '')}): {item.get('status', '')}; "
                f"expected `{item.get('sha256_expected', '')}`, actual `{item.get('sha256_actual', '')}`"
            )
    else:
        lines.append("- none recorded")
    lines.extend(["", "## External Verification", ""])
    for checker in report.get("external_checkers", []):
        lines.append(f"- `{checker}`")
    if not report.get("external_checkers"):
        lines.append("- none recorded")
    lines.extend(
        [
            "",
            "## Claim Boundary Scanner Limitation",
            "",
            CLAIM_SCANNER_LIMITATION_TEXT,
            "",
            f"claim_scan_depth: `{report.get('claim_scan_depth', '')}`",
        ]
    )
    lines.extend(["", "## Artifact Hashes", ""])
    for name, digest in sorted(report.get("artifact_hashes", {}).items()):
        lines.append(f"- `{name}`: `{digest}`")
    lines.extend(["", "## Certification Level", "", f"`{report.get('certification_level', '')}`"])
    lines.extend(["", "## Allowed Claims", ""])
    for claim in report.get("allowed_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Forbidden Claims", ""])
    for claim in report.get("forbidden_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Risk Flags", ""])
    for flag in report.get("risk_flags", []):
        lines.append(f"- {flag}")
    if not report.get("risk_flags"):
        lines.append("- none")
    lines.extend(["", "## Last Verification Timestamp", "", str(report.get("last_verification_timestamp", ""))])
    lines.extend(["", "## Final Verdict", "", f"`{report.get('verdict', '')}`", ""])
    return "\n".join(lines)


def write_report_files(report: dict[str, Any], json_path: str | Path, markdown_path: str | Path) -> None:
    Path(json_path).write_text(stable_json(report), encoding="utf-8")
    Path(markdown_path).write_text(render_verification_report_markdown(report), encoding="utf-8")


def verification_report_for_certificate(path: str | Path) -> dict[str, Any]:
    cert_path = Path(path)
    checker_result = verify_certificate_bundle(cert_path)
    verified = bool(checker_result.get("verified", False))
    risk_flags: list[str] = []
    if not verified:
        risk_flags.append(str(checker_result.get("failed_check", "certificate_verification_failed")))
    result = VerificationReport(
        claim="Witnora certificate bundle is internally consistent and independently replay-checkable.",
        logical_status=str(checker_result.get("status", "NOT_VERIFIED")),
        discovery_route="CERTIFICATE_BUNDLE_CHECK",
        certification_level="CERTIFICATE_BUNDLE_VERIFIED" if verified else "NOT_VERIFIED",
        public_category="CERTIFICATE_VERIFIED" if verified else "CERTIFICATE_NOT_VERIFIED",
        evidence_files=[str(cert_path)],
        external_checkers=[],
        checker_results=[{"checker": "witnora_certificate_bundle_verifier", **checker_result}],
        artifact_hashes={str(cert_path): sha256_file(cert_path)} if cert_path.is_file() else {},
        reproducibility_status="CERTIFICATE_REPLAYED" if verified else "CERTIFICATE_REPLAY_FAILED",
        verification_depth="partial_replay",
        checks_performed=[
            {
                "name": "certificate_bundle_replay",
                "status": "PASS" if verified else "FAIL",
                "depth": "partial_replay",
            }
        ],
        last_verification_timestamp=utc_timestamp(),
        risk_flags=risk_flags,
        verdict=VERDICT_VERIFIED if verified else VERDICT_NOT_VERIFIED,
    )
    return result.to_dict()


def parse_manifest_hash_table(text: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    row_pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`?([A-Fa-f0-9]{64})`?\s*\|", re.MULTILINE)
    for match in row_pattern.finditer(text):
        hashes[match.group(1)] = match.group(2).upper()
    return hashes


def _manifest_lookup(path: Path, manifest_hashes: dict[str, str]) -> str | None:
    candidates = [str(path), path.name, str(path).replace("\\", "/")]
    for candidate in candidates:
        if candidate in manifest_hashes:
            return manifest_hashes[candidate]
    return None


def _evidence_status(path: Path, kind: str, expected: str | None) -> dict[str, Any]:
    exists = path.is_file()
    actual = sha256_file(path) if exists else None
    if not exists:
        status = "MISSING"
    elif expected is None:
        status = "MATCH"
        expected = actual
    elif actual == expected:
        status = "MATCH"
    else:
        status = "MISMATCH"
    return {
        "path": str(path),
        "kind": kind,
        "sha256_expected": expected,
        "sha256_actual": actual,
        "status": status,
    }


def verification_report_for_release(
    *,
    source_zip: str | Path,
    diagnostic_zip: str | Path,
    manifest: str | Path,
) -> dict[str, Any]:
    source_path = Path(source_zip)
    diagnostic_path = Path(diagnostic_zip)
    manifest_path = Path(manifest)
    evidence = [str(source_path), str(diagnostic_path), str(manifest_path)]
    artifact_hashes = {str(path): sha256_file(path) for path in [source_path, diagnostic_path, manifest_path] if path.is_file()}
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_hashes = parse_manifest_hash_table(manifest_text)

    checker_results: list[dict[str, Any]] = []
    checks_performed: list[dict[str, Any]] = []
    risk_flags: list[str] = list(DEFAULT_METADATA_ONLY_RISK_FLAGS)
    evidence_checked: list[dict[str, Any]] = []
    for path in [source_path, diagnostic_path]:
        expected = _manifest_lookup(path, manifest_hashes)
        evidence_item = _evidence_status(
            path,
            "source_archive" if path == source_path else "diagnostic_artifact",
            expected,
        )
        evidence_checked.append(evidence_item)
        check_name = "source_archive_sha256" if path == source_path else "diagnostic_artifact_sha256"
        if expected is None:
            risk_flags.append("UNVERIFIED_CLAIM")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "error": "not listed in manifest"})
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        elif evidence_item["status"] == "MISSING":
            risk_flags.append("MISSING_FILE")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "expected": expected, "error": "missing file"})
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        elif evidence_item["status"] == "MISMATCH":
            risk_flags.append("HASH_MISMATCH")
            checker_results.append(
                {
                    "checker": "sha256_manifest_match",
                    "path": str(path),
                    "passed": False,
                    "expected": expected,
                    "actual": evidence_item["sha256_actual"],
                }
            )
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        else:
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": True, "sha256": evidence_item["sha256_actual"]})
            checks_performed.append({"name": check_name, "status": "PASS", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})

    evidence_checked.append(_evidence_status(manifest_path, "manifest", None))
    checks_performed.append({"name": "manifest_file_present", "status": "PASS", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})

    claim_scan = scan_text_for_claim_boundary(manifest_text)
    checker_results.append({"checker": "claim_boundary_scan", "passed": bool(claim_scan.get("passed")), "details": claim_scan})
    checks_performed.append(
        {
            "name": "claim_boundary_scan",
            "status": "PASS" if claim_scan.get("passed") else "FAIL",
            "depth": CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN,
        }
    )
    if not claim_scan.get("passed"):
        risk_flags.append("UNVERIFIED_CLAIM")

    all_hash_checks_passed = all(
        result.get("passed") is True
        for result in checker_results
        if result.get("checker") == "sha256_manifest_match"
    )
    claim_scan_passed = bool(claim_scan.get("passed"))
    if not all_hash_checks_passed:
        verdict = VERDICT_PARTIALLY_VERIFIED
        reproducibility = "ARTIFACTS_HASHED_WITH_MANIFEST_GAPS"
        certification_level = "RELEASE_ARTIFACT_INTEGRITY_PARTIAL"
    elif not claim_scan_passed:
        verdict = VERDICT_OVERCLAIM
        reproducibility = "CLAIM_BOUNDARY_FAILED"
        certification_level = "RELEASE_ARTIFACT_INTEGRITY_OVERCLAIM"
    else:
        verdict = VERDICT_ARTIFACT_INTEGRITY_VERIFIED
        reproducibility = "SOURCE_AND_DIAGNOSTIC_HASHES_VERIFIED"
        certification_level = CERT_RELEASE_ARTIFACT_INTEGRITY_VERIFIED

    return VerificationReport(
        claim=(
            "Witnora-Core release package supports the scoped public preprint claim "
            "with source, diagnostic artifact, manifest hashes, and recorded external-check evidence."
        ),
        logical_status="RELEASE_ARTIFACT_AUDIT",
        discovery_route="RELEASE_MANIFEST_AND_HASH_CHECK",
        certification_level=certification_level,
        public_category="PUBLIC_RELEASE_VERIFICATION",
        evidence_files=evidence,
        external_checkers=[],
        checker_results=checker_results,
        artifact_hashes=artifact_hashes,
        reproducibility_status=reproducibility,
        verification_depth=DEPTH_METADATA_HASH_CHECKS_ONLY,
        evidence_checked=evidence_checked,
        checks_performed=checks_performed,
        claim_scan_depth=CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN,
        last_verification_timestamp=utc_timestamp(),
        risk_flags=risk_flags,
        verdict=verdict,
    ).to_dict()


def trust_card_from_report(report: dict[str, Any], *, project: str = "Witnora-Core") -> dict[str, Any]:
    verdict = str(report.get("verdict", "NOT_VERIFIED"))
    if verdict == VERDICT_ARTIFACT_INTEGRITY_VERIFIED:
        trust_verdict = "VERIFIED_ARTIFACT_INTEGRITY_WITH_SCOPE_LIMITS"
    elif verdict == VERDICT_VERIFIED:
        trust_verdict = "VERIFIED_WITH_SCOPE_LIMITS"
    elif verdict == VERDICT_PARTIALLY_VERIFIED:
        trust_verdict = "PARTIALLY_VERIFIED_WITH_RISK_FLAGS"
    elif verdict == VERDICT_OVERCLAIM:
        trust_verdict = "OVERCLAIM_DETECTED"
    else:
        trust_verdict = "NOT_VERIFIED"
    verified_by = list(report.get("external_checkers", []))
    verified_by.extend(check.get("name", "check") for check in report.get("checks_performed", []))
    verified_by.extend(result.get("checker", "checker") for result in report.get("checker_results", []))
    return {
        "project": project,
        "claim": report.get("claim", ""),
        "verified_by": verified_by,
        "certification_level": report.get("certification_level", ""),
        "verification_depth": report.get("verification_depth", DEPTH_METADATA_HASH_CHECKS_ONLY),
        "not_claimed": report.get("forbidden_claims", []),
        "reproducibility": report.get("reproducibility_status", ""),
        "risk_flags": report.get("risk_flags", []),
        "verdict": trust_verdict,
    }


def render_trust_card_markdown(card: dict[str, Any]) -> str:
    lines = [
        "# Witnora Trust Card",
        "",
        f"**Project:** {card.get('project', '')}",
        "",
        "This trust card verifies artifact integrity and scope boundaries only. "
        "It does not rerun the scientific proof pipeline.",
        "",
        "## Claim",
        "",
        str(card.get("claim", "")),
        "",
        "## Verified By",
        "",
    ]
    for item in card.get("verified_by", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Certification Level", "", f"`{card.get('certification_level', '')}`"])
    lines.extend(["", "## Verification Depth", "", f"`{card.get('verification_depth', '')}`"])
    lines.extend(["", "## Not Claimed", ""])
    for item in card.get("not_claimed", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Risk Flags", ""])
    for item in card.get("risk_flags", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Reproducibility", "", str(card.get("reproducibility", ""))])
    lines.extend(["", "## Verdict", "", f"`{card.get('verdict', '')}`", ""])
    return "\n".join(lines)
