"""Portable proof-carrying certificate bundle support."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .certificate import (
    CollapsePath,
    CollapseStep,
    NO_COLLAPSE,
    SAT,
    UNSAT,
    UNSAT_LEVEL_2SAT_SCC,
    UNSAT_LEVEL_EXPLICIT_EMPTY,
    UNSAT_LEVEL_NOT_UNSAT,
    XOR_UNSAT_NATIVE,
    proof_trace_class_from_status,
    sat_certification_level,
    unsat_certification_level_from_steps,
)
from .cnf import CNFFormula, formula_satisfied
from .dimacs import export_dimacs, parse_dimacs
from .drat import DRATExport, export_drat_for_path
from .drat_trim import run_drat_trim
from .proof_trace import is_supported_native_unsat_trace, native_unsat_trace
from .reconstruction import reconstruct_assignment
from .verifier import verify_collapse_path
from .xor import XorEquation, XorSystem, verify_xor_assignment

WITNORA_VERSION = "0.9.2"
CERTIFICATE_FORMAT_VERSION = "wcert-1"
VERIFIER_VERSION = "witnora-standalone-verifier-0.9.2"

FORBIDDEN_STATUSES = {"HARD", "UNKNOWN", "PROBABLY_UNSAT", "PROBABLY_HARD"}


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def proof_trace_class(status: str, unsat_level: str = UNSAT_LEVEL_NOT_UNSAT) -> str:
    return proof_trace_class_from_status(status, unsat_level)


def external_proof_status(step_type: str) -> str:
    if step_type == "BCE":
        return "RAT_COMPATIBLE"
    if step_type == "VE":
        return "LRAT_EXPORT_NOT_IMPLEMENTED"
    if step_type in {"PLE", "CD", "TREEWIDTH_SOLVE"}:
        return "NOT_A_CLAUSAL_REFUTATION_STEP"
    return "CHECKED_BY_WITNORA_REPLAY"


def unsat_certification_level(path: CollapsePath) -> str:
    return unsat_certification_level_from_steps(path.status, path.steps)


def _normalise_stats(stats: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in sorted(stats.items()) if key != "time_ms"}


def _result_without_timing(path: CollapsePath) -> dict[str, Any]:
    data = path.to_dict()
    data["stats"] = _normalise_stats(data.get("stats", {}))
    return data


def _collapse_path_payload(path: CollapsePath) -> dict[str, Any]:
    return {
        "proof_trace_class": path.proof_trace_class,
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
        "proof_trace_class": path.proof_trace_class,
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
    drat_export: DRATExport | None = None,
) -> dict[str, str]:
    result = _result_without_timing(path)
    files = {
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
    trace = native_unsat_trace(path)
    if trace is not None:
        files["proof_trace.json"] = stable_json(trace)
    if path.xor_data is not None:
        files["xor_system.json"] = stable_json(path.xor_data.get("xor_system", {}))
        files["xor_trace.json"] = stable_json(path.xor_data.get("xor_trace", {}))
        files["xor_status.json"] = stable_json(path.xor_data.get("xor_status", {}))
    if drat_export is not None:
        files["drat_status.json"] = stable_json(drat_export.status)
        if drat_export.proof_text is not None and drat_export.status.get("drat_export_status") == "EXPORTED":
            files["proof.drat"] = drat_export.proof_text
    return files


def _excerpt(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def _with_drat_trim_result(
    drat_export: DRATExport,
    original_dimacs_text: str,
    drat_trim_path: str | Path | None,
) -> DRATExport:
    if (
        drat_trim_path is None
        or drat_export.proof_text is None
        or drat_export.status.get("drat_export_status") != "EXPORTED"
    ):
        return drat_export

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_path = root / "original.dimacs"
        proof_path = root / "proof.drat"
        original_path.write_text(
            original_dimacs_text if original_dimacs_text.endswith("\n") else original_dimacs_text + "\n",
            encoding="utf-8",
        )
        proof_path.write_text(drat_export.proof_text, encoding="utf-8")
        trim_result = run_drat_trim(original_path, proof_path, drat_trim_path)

    status = dict(drat_export.status)
    status.update(
        {
            "external_checker": trim_result.get("external_checker", "NOT_RUN"),
            "external_checker_path": trim_result.get("external_checker_path"),
            "external_checker_ran": bool(trim_result.get("external_checker_ran", False)),
            "external_checker_verified": bool(trim_result.get("external_checker_verified", False)),
            "external_checker_exit_code": trim_result.get("exit_code"),
            "external_checker_stdout_excerpt": _excerpt(str(trim_result.get("stdout", ""))),
            "external_checker_stderr_excerpt": _excerpt(str(trim_result.get("stderr", ""))),
            "external_checker_timeout": bool(trim_result.get("timeout", False)),
            "external_checker_error": trim_result.get("error"),
        }
    )
    if not status["external_checker_verified"] and status["external_checker_ran"]:
        status["supported_reason"] = (
            status.get("supported_reason")
            or "internal RUP-subset checker verified proof; external checker did not accept"
        )
    return DRATExport(drat_export.proof_text, status)


def _manifest(
    original_formula: CNFFormula,
    path: CollapsePath,
    files: dict[str, str],
    drat_export: DRATExport | None = None,
) -> dict[str, Any]:
    drat_status = drat_export.status if drat_export is not None else {
        "drat_export_status": "NOT_REQUESTED",
    }
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
        "sat_certification_level": path.sat_certification_level,
        "unsat_certification_level": unsat_certification_level(path),
        "proof_trace_class": path.proof_trace_class,
        "external_lrat_frat": False,
        "native_unsat_trace_scope": "END_TO_END_WITH_COLLAPSE_REPLAY",
        "external_drat": bool(drat_status.get("drat_export_status") == "EXPORTED"),
        "drat_export_status": drat_status.get("drat_export_status"),
        "xor_used": path.xor_data is not None,
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
    export_drat: bool = False,
    drat_trim_path: str | Path | None = None,
) -> Path:
    """Write a deterministic .wcert directory or .wcert.json certificate."""

    output = Path(output_path)
    original_text = original_dimacs_text or export_dimacs(original_formula)
    drat_export = export_drat_for_path(original_formula, path) if export_drat else None
    if drat_export is not None:
        drat_export = _with_drat_trim_result(drat_export, original_text, drat_trim_path)
    files = _bundle_files(original_formula, path, original_text, drat_export)
    manifest = _manifest(original_formula, path, files, drat_export)
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
        xor_data=data.get("xor_data"),
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
        proof_trace = (
            json.loads(files["proof_trace.json"])
            if "proof_trace.json" in files
            else None
        )
    except Exception as exc:
        return _fail(str(exc), "json_parse")

    if str(result_data.get("status", "")) in FORBIDDEN_STATUSES:
        return _fail("forbidden status present", "forbidden_status")
    if files.get("certificate_hash.txt", "").strip() != manifest.get("certificate_hash"):
        return _fail("certificate_hash.txt mismatch", "certificate_hash")
    if result_data.get("certificate_hash") != manifest.get("certificate_hash"):
        return _fail("result certificate hash mismatch", "certificate_hash")
    if manifest.get("sat_certification_level") != result_data.get("sat_certification_level"):
        return _fail("SAT certification level mismatch", "certification_metadata")
    if manifest.get("unsat_certification_level") != result_data.get("unsat_certification_level"):
        return _fail("UNSAT certification level mismatch", "certification_metadata")
    if manifest.get("proof_trace_class") != result_data.get("proof_trace_class"):
        return _fail("proof_trace_class manifest mismatch", "certification_metadata")
    if manifest.get("external_lrat_frat") is not False:
        return _fail("external_lrat_frat must remain false in v0.9.2", "proof_trace_classification")
    if manifest.get("verification_levels", {}).get("external_lrat_frat") is not False:
        return _fail("external LRAT/FRAT verification falsely claimed", "proof_trace_classification")
    if manifest.get("native_unsat_trace_scope") != "END_TO_END_WITH_COLLAPSE_REPLAY":
        return _fail("native UNSAT trace scope mismatch", "certification_metadata")

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
    if result_data.get("xor_data") is not None:
        if "xor_system.json" not in files or "xor_trace.json" not in files or "xor_status.json" not in files:
            return _fail("missing XOR certificate files", "xor_certificate")
        if json.loads(files["xor_system.json"]) != result_data["xor_data"].get("xor_system", {}):
            return _fail("xor_system.json differs from result.json", "xor_certificate")
        if json.loads(files["xor_trace.json"]) != result_data["xor_data"].get("xor_trace", {}):
            return _fail("xor_trace.json differs from result.json", "xor_certificate")
        if json.loads(files["xor_status.json"]) != result_data["xor_data"].get("xor_status", {}):
            return _fail("xor_status.json differs from result.json", "xor_certificate")
    elif result_data.get("status") == XOR_UNSAT_NATIVE:
        return _fail("XOR-native UNSAT certificate missing xor_data", "xor_certificate")

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

    if path_obj.xor_data is not None:
        try:
            xor_system_data = path_obj.xor_data.get("xor_system", {})
            xor_system = XorSystem(
                XorEquation(
                    equation.get("variables", []),
                    int(equation.get("rhs", 0)),
                    source=str(equation.get("source", "certificate")),
                    source_clauses=equation.get("source_clauses", []),
                )
                for equation in xor_system_data.get("equations", [])
            )
            xor_status = dict(path_obj.xor_data.get("xor_status", {}))
        except Exception as exc:
            return _fail(f"invalid XOR certificate data: {exc}", "xor_certificate")
        if path_obj.status == SAT and not verify_xor_assignment(
            xor_system,
            path_obj.reconstructed_original_assignment,
        ):
            return _fail("SAT assignment does not satisfy XOR equations", "xor_certificate")
        if path_obj.status == XOR_UNSAT_NATIVE:
            if xor_status.get("xor_status") != "UNSAT":
                return _fail("XOR-native UNSAT missing XOR contradiction status", "xor_certificate")
            if xor_status.get("external_drat") is not False:
                return _fail("XOR-native UNSAT falsely claims external DRAT", "xor_certificate")
            if xor_status.get("drat_claim") != "NOT_EXPORTED":
                return _fail("XOR-native UNSAT falsely claims DRAT export", "xor_certificate")

    expected_unsat_level = unsat_certification_level(path_obj)
    expected_sat_level = sat_certification_level(
        path_obj.status,
        path_obj.original_verification,
    )
    expected_class = path_obj.proof_trace_class
    if result_data.get("sat_certification_level") != expected_sat_level:
        return _fail("SAT certification level mismatch", "certification_metadata")
    if result_data.get("unsat_certification_level") != expected_unsat_level:
        return _fail("UNSAT certification level mismatch", "certification_metadata")
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
    expected_trace = native_unsat_trace(path_obj)
    if proof_trace is not None:
        if not is_supported_native_unsat_trace(proof_trace):
            return _fail("unsupported native proof trace", "proof_trace")
        if proof_trace != expected_trace:
            return _fail("proof_trace.json mismatch", "proof_trace")
        if proof_trace != result_data.get("native_proof_trace"):
            return _fail("result native proof trace mismatch", "proof_trace")
    elif expected_trace is not None:
        return _fail("missing proof_trace.json", "proof_trace")

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
        if expected_unsat_level not in {UNSAT_LEVEL_EXPLICIT_EMPTY, UNSAT_LEVEL_2SAT_SCC}:
            return _fail(
                "UNSAT requires independently checkable contradiction or future LRAT/FRAT proof",
                "unsat_external_certification",
            )
        checks["unsat_contradiction"] = True
    elif path_obj.status == NO_COLLAPSE:
        checks["no_collapse_report"] = True
    elif path_obj.status == XOR_UNSAT_NATIVE:
        checks["xor_native_unsat_not_drat"] = True

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
