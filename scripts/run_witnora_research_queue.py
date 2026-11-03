"""Bounded completion-driven Witnora research queue.

One approved experiment starts immediately after the previous experiment
finishes. No schedules, self-dispatch, auto-commits, paid API calls, or
open-ended loops. The manifest names ONLY audited task IDs; it cannot
provide arbitrary shell commands.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "research" / "witnora_research_queue.json"
DEFAULT_REPORT = ROOT / "artifacts" / "witnora_research_queue_report.json"

# Fixed, reviewed modules. Manifest entries are identifiers, not commands.
ALLOWED_TASKS = {
    "wcrc005_symmetry_falsification":
        ("-m", "scripts.benchmark_crc_symmetry_stress"),
    "wcrc005_defect_unit":
        ("-m", "unittest", "tests.test_crc_defect_oracle", "-v"),
    "wcrc005_defect_ganak":
        ("-m", "scripts.benchmark_crc_defect"),
    "wcrc004_orbit_unit":
        ("-m", "unittest", "tests.test_crc_orbit_oracle", "-v"),
    "wcrc004_orbit_benchmark":
        ("-m", "scripts.benchmark_crc_orbit"),
    "wcrc003_highcount_control":
        ("-m", "scripts.benchmark_crc_highcount",
         "--max-states", "30000", "--seconds", "2.5", "--repeats", "1"),
}
MAX_TASKS = 5
MAX_BUDGET_SECONDS = 900
PER_TASK_TIMEOUT_SECONDS = 180


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_plan(data: object) -> list[str]:
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("expected research queue manifest version 1")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a nonempty list")
    if not all(isinstance(t, str) and t in ALLOWED_TASKS for t in tasks):
        raise ValueError("all tasks must be reviewed ALLOWED_TASKS identifiers")
    if len(set(tasks)) != len(tasks):
        raise ValueError("duplicate tasks are prohibited")
    return tasks


def execute_plan(
    task_ids: list[str], *, max_tasks: int = 3,
    budget_seconds: int = 480, report_path: Path = DEFAULT_REPORT,
    invoke=subprocess.run, clock=time.monotonic,
) -> int:
    if not 1 <= max_tasks <= MAX_TASKS:
        raise ValueError(f"max_tasks must be in 1..{MAX_TASKS}")
    if not 1 <= budget_seconds <= MAX_BUDGET_SECONDS:
        raise ValueError(f"budget_seconds must be in 1..{MAX_BUDGET_SECONDS}")
    if not task_ids or any(task not in ALLOWED_TASKS for task in task_ids):
        raise ValueError("task plan contains an unreviewed or empty task")
    report = {
        "schema": 1, "started_utc": utc_now(),
        "configured_tasks": task_ids,
        "task_cap": max_tasks, "budget_seconds": budget_seconds,
        "per_task_timeout_seconds": PER_TASK_TIMEOUT_SECONDS,
        "results": [], "stop_reason": None,
    }
    started = clock()
    reason = "QUEUE_COMPLETE"
    for task_id in task_ids:
        if len(report["results"]) >= max_tasks:
            reason = "TASK_CAP"
            break
        remaining = budget_seconds - (clock() - started)
        if remaining < 1:
            reason = "TOTAL_BUDGET_EXHAUSTED"
            break
        timeout = min(PER_TASK_TIMEOUT_SECONDS, max(1, int(remaining)))
        command = [sys.executable, *ALLOWED_TASKS[task_id]]
        print(f"[queue] START {task_id}, deadline {timeout}s", flush=True)
        task_started = clock()
        outcome = "PASS"
        code = 0
        try:
            finished = invoke(
                command, cwd=str(ROOT), capture_output=True,
                text=True, check=False, timeout=timeout,
                env=os.environ.copy(),
            )
            code = finished.returncode
            if finished.stdout:
                print(finished.stdout[-10000:], flush=True)
            if finished.stderr:
                print(finished.stderr[-10000:], file=sys.stderr, flush=True)
            if code != 0:
                outcome = "FAIL"
        except subprocess.TimeoutExpired:
            outcome, code = "TIMEOUT", None
        except OSError as error:
            outcome, code = f"ERROR:{type(error).__name__}", None
        elapsed = round(clock() - task_started, 3)
        report["results"].append({
            "id": task_id, "status": outcome,
            "elapsed_seconds": elapsed, "exit_code": code,
        })
        print(f"[queue] FINISH {task_id}: {outcome} ({elapsed}s)", flush=True)
        if outcome != "PASS":
            reason = "STOP_ON_FAILURE"
            break
    report["stop_reason"] = reason
    report["finished_utc"] = utc_now()
    report["elapsed_seconds"] = round(clock() - started, 3)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(f"[queue] {reason}; report: {report_path}", flush=True)
    return 1 if reason in ("STOP_ON_FAILURE", "TOTAL_BUDGET_EXHAUSTED") else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--max-tasks", type=int, default=3)
    parser.add_argument("--budget-seconds", type=int, default=480)
    parser.add_argument("--dry-run", action="store_true")
    options = parser.parse_args()
    if not 1 <= options.max_tasks <= MAX_TASKS:
        parser.error(f"--max-tasks must be in 1..{MAX_TASKS}")
    if not 1 <= options.budget_seconds <= MAX_BUDGET_SECONDS:
        parser.error(f"--budget-seconds must be in 1..{MAX_BUDGET_SECONDS}")
    tasks = validate_plan(json.loads(options.plan.read_text(encoding="utf-8")))
    if options.dry_run:
        print(json.dumps({
            "dry_run": True, "selected": tasks[:options.max_tasks],
            "queued_after_cap": tasks[options.max_tasks:],
            "budget_seconds": options.budget_seconds,
        }, sort_keys=True))
        return 0
    return execute_plan(
        tasks, max_tasks=options.max_tasks,
        budget_seconds=options.budget_seconds, report_path=options.report,
    )


if __name__ == "__main__":
    raise SystemExit(main())
