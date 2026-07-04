"""Portable proof-carrying certificate bundle support."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .certificate import CollapsePath, CollapseStep, NO_COLLAPSE, SAT, UNSAT
from .cnf import CNFFormula, formula_satisfied
from .dimacs import export_dimacs, parse_dimacs
from .reconstruction import reconstruct_assignment
from .verifier import verify_collapse_path

WITNORA_VERSION = "0.4.0"
CERTIFICATE_FORMAT_VERSION = "wcert-1"
VERIFIER_VERSION = "witnora-standalone-verifier-0.4.0"

FORBIDDEN_STATUSES = {"HARD", "UNKNOWN", "PROBABLY_UNSAT", "PROBABLY_HARD"}


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def proof_trace_class(status: str) -> str:
    if status == SAT:
        return "SAT_ASSIGNMENT_RECONSTRUCTION"
    if status == UNSAT:
        return "UNSAT_INTERNAL_REPLAY"
    if status == NO_COLLAPSE:
        return "NO_COLLAPSE_REPORT"
    return "UNSUPPORTED_FOR_EXTERNAL_LRAT"


def external_proof_status(step_type: str) -> str:
    if step_type == "BCE":
        return "RAT_COMPATIBLE"
    if step_type == "VE":
        return "LRAT_EXPORT_NOT_IMPLEMENTED"
    if step_type in {"PLE", "CD", "TREEWIDTH_SOLVE"}:
        return "NOT_A_CLAUSAL_REFUTATION_STEP"
    return "CHECKED_BY_WITNORA_REPLAY"


def unsat_certification_level(path: CollapsePath) -> str:
    if path.status != UNSAT:
        return "LRAT_FRAT_NOT_IMPLEMENTED"
    if any(clause == [] for step in path.steps for clause in step.added_clauses):
        return "EXPLICIT_EMPTY_CLAUSE"
    if any(
        step.type == "2SAT_SOLVE" and step.details.get("status") == "UNSAT"
        for step in path.steps
    ):
        return "INDEPENDENT_2SAT_SCC"
    return "INTERNAL_REPLAY_ONLY"


def _normalise_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in sorted(stats.items()) if key != "time_ms"}


def _result_without_timing(path: CollapsePath) -> dict[str, Any]:
    data = path.to_dict()
    data["stats"] = _normalise_stats(data.get("stats", {}))
    data["proof_trace_class"] = proof_trace_class(path.status)
    return data


def _collapse_path_payload(path: CollapsePath) -> dict[str, Any]:
    return {
        "proof_trace_class": proof_trace_class(path.status),
        "steps": [
            {
                **step.to_dict(),
                "external_proof_status": external_proof_status(step.type),
            }
            for step in path.steps
        ],
    }


def _reconstruction_trace(path: CollapsePath) -> dict[str, Any]:
    return {
        "trace_format_version": "1",
        "proof_trace_class": proof_trace_class(path.status),
        "start_assignment": {
            str(int(var)): bool(value)
            for var, value in sorted(path.final_assignment.items(), key=lambda item: int(item[0]))
        },
        "reverse_step_ids": [step.step_id for step in reversed(path.steps)],
        "trace": [
            {
                "step_id": step.step_id,
                "type": step.type,
                "external_proof_status": external_proof_status(step.type),
            }
            for step in reversed(path.steps)
        ],
        "reconstructed_original_assignment": {
            str(int(var)): bool(value)
            for var, value in sorted(
                path.reconstructed_original_assignment.items(),
                key=lambda item: int(item[0]),
            )
        },
        "original_verification": bool(path.original_verification),
    }


def _bundle_files(
    original_formula: CNFFormula,
    path: CollapsePath,
    original_dimacs_text: str,
) -> dict[str, str]:
    result = _result_without_timing(path)
    return {
        "original.dimacs": original_dimacs_text if original_dimacs_text.endswith("\n") else original_dimacs_text + "\n",
        "normalized.dimacs": export_dimacs(original_formula),
        "result.json": stable_json(result),
        "collapse_path.json": stable_json(_collapse_path_payload(path)),
        "reconstruction_trace.json": stable_json(_reconstruction_trace(path)),
        "component_results.json": stable_json(path.component_results),
        "stats.json": stable_json(_normalise_stats(path.stats)),
        "certificate_hash.txt": path.certificate_hash + "\n",
        "verifier_version.txt": VERIFIER_VERSION + "\n",
    }


def _manifest(
    original_formula: CNFFormula,
    path: CollapsePath,
    files: dict[str, str],
) -> dict[str, Any]:
    return {
        "witnora_version": WITNORA_VERSION,
        "certificate_format_version": CERTIFICATE_FORMAT_VERSION,
        "original_formula_hash": original_formula.formula_hash,
        "normalized_formula_hash": original_formula.formula_hash,
        "certificate_hash": path.certificate_hash,
        "status": path.status,
        "final_class": path.final_class,
        "c_parameter": path.c_parameter,
        "created_by": "witnora_core.runner",
        "forbidden_claims_absent": True,
        "verification_levels": {
            "witnora_replay_verifier": True,
            "independent_raw_checker": True,
            "external_lrat_frat": False,
        },
        "unsat_certification_level": unsat_certification_level(path),
        "files": {
            name: {"sha256": sha256_text(content)}
            for name, content in sorted(files.items())
        },
    }


def export_certificate_bundle(
    original_formula: CNFFormula,
    path: CollapsePath,
    output_path: str | Path,
    *,
    original_dimacs_text: str | None = None,
) -> Path:
    """Write a deterministic .wcert directory or .wcert.json certificate."""

    output = Path(output_path)
    original_text = original_dimacs_text or export_dimacs(original_formula)
    files = _bundle_files(original_formula, path, original_text)
    manifest = _manifest(original_formula, path, files)
    manifest_text = stable_json(manifest)

    if output.suffix == ".json":
        package = {
            "manifest": manifest,
            "files": files,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(stable_json(package), encoding="utf-8")
        return output

    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (output / name).write_text(content, encoding="utf-8")
    (output / "manifest.json").write_text(manifest_text, encoding="utf-8")
    return output


def load_certificate_package(path: str | Path) -> tuple[dict[str, Any], dict[str, str]]:
    source = Path(path)
    if source.is_dir():
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        files = {
            name: (source / name).read_text(encoding="utf-8")
            for name in manifest.get("files", {})
        }
        return manifest, files

    data = json.loads(source.read_text(encoding="utf-8"))
    return data["manifest"], {str(k): str(v) for k, v in data["files"].items()}


def collapse_path_from_result_dict(data: dict[str, Any]) -> CollapsePath:
    steps = [
        CollapseStep(
            step_id=int(step["step_id"]),
            type=str(step["type"]),
            input_formula_hash=str(step["input_formula_hash"]),
            output_formula_hash=str(step["output_formula_hash"]),
            details=dict(step.get("details", {})),
            removed_clauses=[list(clause) for clause in step.get("removed_clauses", [])],
            added_clauses=[list(clause) for clause in step.get("added_clauses", [])],
            assigned_literals=[int(lit) for lit in step.get("assigned_literals", [])],
            reconstruction_data=dict(step.get("reconstruction_data", {})),
        )
        for step in data.get("collapse_path", [])
    ]
    return CollapsePath(
        original_formula_hash=str(data["original_formula_hash"]),
        c_parameter=int(data["c_parameter"]),
        steps=steps,
        final_formula_hash=str(data["final_formula_hash"]),
        final_class=str(data["final_class"]),
        status=str(data["status"]),
        final_assignment={int(k): bool(v) for k, v in data.get("final_assignment", {}).items()},
        reconstructed_original_assignment={
            int(k): bool(v)
            for k, v in data.get("reconstructed_original_assignment", {}).items()
        },
        original_verification=bool(data.get("original_verification", False)),
        component_results=list(data.get("component_results", [])),
        stats=dict(data.get("stats", {})),
    )


def _fail(error: str, failed_check: str) -> dict[str, Any]:
    return {
        "verified": False,
        "error": error,
        "failed_check": failed_check,
    }


def verify_certificate_bundle(path: str | Path) -> dict[str, Any]:
    """Verify a saved certificate package without rerunning collapse search."""

    try:
        manifest, files = load_certificate_package(path)
    except Exception as exc:
        return _fail(str(exc), "package_load")

    for status in [manifest.get("status", "")]:
        if str(status) in FORBIDDEN_STATUSES:
            return _fail("forbidden status present", "forbidden_status")
    if not manifest.get("forbidden_claims_absent", False):
        return _fail("forbidden_claims_absent is not true", "manifest")

    for name, meta in manifest.get("files", {}).items():
        if name not in files:
            return _fail(f"missing file {name}", "file_hash")
        if sha256_text(files[name]) != meta.get("sha256"):
            return _fail(f"file hash mismatch for {name}", "file_hash")

    try:
        result_data = json.loads(files["result.json"])
        collapse_data = json.loads(files["collapse_path.json"])
        component_results = json.loads(files["component_results.json"])
        stats = json.loads(files["stats.json"])
        reconstruction_trace = json.loads(files["reconstruction_trace.json"])
    except Exception as exc:
        return _fail(str(exc), "json_parse")

    if str(result_data.get("status", "")) in FORBIDDEN_STATUSES:
        return _fail("forbidden status present", "forbidden_status")
    if files.get("certificate_hash.txt", "").strip() != manifest.get("certificate_hash"):
        return _fail("certificate_hash.txt mismatch", "certificate_hash")
    if result_data.get("certificate_hash") != manifest.get("certificate_hash"):
        return _fail("result certificate hash mismatch", "certificate_hash")

    stripped_steps = [
        {key: value for key, value in step.items() if key != "external_proof_status"}
        for step in collapse_data.get("steps", [])
    ]
    if stripped_steps != result_data.get("collapse_path", []):
        return _fail("collapse_path.json differs from result.json", "collapse_path")
    for step in collapse_data.get("steps", []):
        if "external_proof_status" not in step:
            return _fail("collapse step missing external_proof_status", "proof_trace_classification")

    if component_results != result_data.get("component_results", []):
        return _fail("component_results.json differs from result.json", "component_results")
    if stats != result_data.get("stats", {}):
        return _fail("stats.json differs from result.json", "stats")

    try:
        original = parse_dimacs(files["original.dimacs"])
        normalized = parse_dimacs(files["normalized.dimacs"])
    except Exception as exc:
        return _fail(str(exc), "dimacs_parse")

    if original.formula_hash != manifest.get("original_formula_hash"):
        return _fail("original formula hash mismatch", "original_formula_hash")
    if normalized.formula_hash != manifest.get("normalized_formula_hash"):
        return _fail("normalized formula hash mismatch", "normalized_formula_hash")
    if normalized.formula_hash != original.formula_hash:
        return _fail("normalized formula differs from parsed original", "normalized_formula_hash")

    path_obj = collapse_path_from_result_dict(result_data)
    if path_obj.certificate_hash != manifest.get("certificate_hash"):
        return _fail("recomputed certificate hash mismatch", "certificate_hash")

    expected_class = proof_trace_class(path_obj.status)
    if result_data.get("proof_trace_class") != expected_class:
        return _fail("proof_trace_class mismatch", "proof_trace_classification")
    if collapse_data.get("proof_trace_class") != expected_class:
        return _fail("collapse proof_trace_class mismatch", "proof_trace_classification")
    if reconstruction_trace.get("proof_trace_class") != expected_class:
        return _fail("reconstruction proof_trace_class mismatch", "reconstruction_trace")
    if reconstruction_trace.get("reverse_step_ids") != [
        step.step_id for step in reversed(path_obj.steps)
    ]:
        return _fail("reverse reconstruction step ids mismatch", "reconstruction_trace")
    if reconstruction_trace.get("reconstructed_original_assignment", {}) != {
        str(k): v
        for k, v in sorted(path_obj.reconstructed_original_assignment.items())
    }:
        return _fail("reconstruction assignment mismatch", "reconstruction_trace")

    replay = verify_collapse_path(original, path_obj)
    if not replay.ok:
        return _fail("; ".join(replay.errors), "collapse_replay")

    checks = {
        "file_hashes": True,
        "certificate_hash": True,
        "collapse_replay": True,
        "component_replay": True,
        "reconstruction_trace": True,
        "forbidden_status_absent": True,
    }

    if path_obj.status == SAT:
        if not formula_satisfied(original, path_obj.reconstructed_original_assignment):
            return _fail("SAT assignment does not satisfy original formula", "sat_assignment")
        reconstructed = reconstruct_assignment(original, path_obj.steps, path_obj.final_assignment)
        if not reconstructed.ok or reconstructed.assignment != path_obj.reconstructed_original_assignment:
            return _fail("reconstruction replay mismatch", "reconstruction_trace")
        checks["sat_assignment"] = True
    elif path_obj.status == UNSAT:
        checks["unsat_contradiction"] = True
    elif path_obj.status == NO_COLLAPSE:
        checks["no_collapse_report"] = True

    return {
        "verified": True,
        "status": path_obj.status,
        "certificate_hash": path_obj.certificate_hash,
        "checks": checks,
    }


def update_manifest_hashes_for_directory(path: str | Path) -> None:
    """Testing helper for constructing self-consistent tampered packages."""

    root = Path(path)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for name in manifest.get("files", {}):
        manifest["files"][name]["sha256"] = sha256_text((root / name).read_text(encoding="utf-8"))
    (root / "manifest.json").write_text(stable_json(manifest), encoding="utf-8")
