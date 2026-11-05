#!/bin/sh
set -eu

required_input() {
  name="$1"
  value="$2"
  if [ -z "$value" ]; then
    echo "WITNORA_DOCKER_ACTION_INPUT_MISSING: $name is required." >&2
    exit 2
  fi
}

source_zip="${INPUT_SOURCE_ZIP:-}"
diagnostic_zip="${INPUT_DIAGNOSTIC_ZIP:-}"
manifest="${INPUT_MANIFEST:-}"
depth="${INPUT_DEPTH:-metadata}"
select_policy="${INPUT_SELECT:-largest}"
select_instance="${INPUT_SELECT_INSTANCE:-}"
rerun_drat_trim="${INPUT_RERUN_DRAT_TRIM:-false}"
drat_trim="${INPUT_DRAT_TRIM:-}"
max_replay_proofs="${INPUT_MAX_REPLAY_PROOFS:-1}"
replay_timeout_seconds="${INPUT_REPLAY_TIMEOUT_SECONDS:-120}"
fail_on="${INPUT_FAIL_ON:-hash_mismatch,overclaim,missing_file}"
fail_on_risk_flags="${INPUT_FAIL_ON_RISK_FLAGS:-}"
fail_on_verdict="${INPUT_FAIL_ON_VERDICT:-}"
out_dir="${INPUT_OUT_DIR:-witnora-verify-out}"
upload_artifacts="${INPUT_UPLOAD_ARTIFACTS:-false}"

required_input "source-zip" "$source_zip"
required_input "diagnostic-zip" "$diagnostic_zip"
required_input "manifest" "$manifest"

echo "Witnora Verify Docker action"
echo "Verification depth: $depth"
echo "Selection policy: $select_policy"
echo "Witnora Verify did not rerun the solver, regenerate CNFgen instances, regenerate DRAT proofs, or rerun the full benchmark diagnostic."

if [ "$upload_artifacts" = "true" ]; then
  echo "upload-artifacts was requested, but Docker actions cannot invoke actions/upload-artifact internally. Upload '$out_dir' in a later workflow step."
fi

set -- \
  --source-zip "$source_zip" \
  --diagnostic-zip "$diagnostic_zip" \
  --manifest "$manifest" \
  --depth "$depth" \
  --select "$select_policy" \
  --select-instance "$select_instance" \
  --max-replay-proofs "$max_replay_proofs" \
  --replay-timeout-seconds "$replay_timeout_seconds" \
  --fail-on "$fail_on" \
  --fail-on-risk-flags "$fail_on_risk_flags" \
  --fail-on-verdict "$fail_on_verdict" \
  --out-dir "$out_dir"

if [ "$rerun_drat_trim" = "true" ]; then
  set -- "$@" --rerun-drat-trim
fi

if [ -n "$drat_trim" ]; then
  set -- "$@" --drat-trim "$drat_trim"
fi

exec python -m witnora_core.ci "$@"
