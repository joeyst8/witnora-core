"""Safety and sequencing tests for the bounded research queue."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts.run_witnora_research_queue import execute_plan, validate_plan


TASKS = [
    "wcrc016_heldout_unit",
    "wcrc017_dense_unit",
    "wcrc017_dense_ganak",
]


class TestResearchQueue(unittest.TestCase):
    def test_manifest_rejects_unsafe_or_duplicate_tasks(self):
        self.assertEqual(validate_plan({"version": 1, "tasks": TASKS}), TASKS)
        for plan in (
            {"version": 1, "tasks": ["rm -rf ."]},
            {"version": 1, "tasks": ["wcrc004_orbit_unit"] * 2},
            {"version": 2, "tasks": TASKS},
            {"version": 1, "tasks": []},
        ):
            with self.assertRaises(ValueError):
                validate_plan(plan)

    def test_immediately_advances_through_all_approved_tasks(self):
        calls = []
        def invoke(command, **kwargs):
            calls.append(command)
            self.assertFalse(kwargs.get("shell", False))
            self.assertLessEqual(kwargs["timeout"], 180)
            return subprocess.CompletedProcess(command, 0, "exact\n", "")
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / "results.json"
            rc = execute_plan(TASKS, report_path=report, invoke=invoke)
            details = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 3)
        self.assertEqual(details["stop_reason"], "QUEUE_COMPLETE")
        self.assertEqual(
            [row["id"] for row in details["results"]], TASKS
        )
        self.assertTrue(all(row["status"] == "PASS"
                            for row in details["results"]))

    def test_failure_stops_without_running_the_next_experiment(self):
        invoke = Mock(return_value=subprocess.CompletedProcess([], 4, "", "bad"))
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / "results.json"
            rc = execute_plan(TASKS, report_path=report, invoke=invoke)
            details = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rc, 1)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(details["stop_reason"], "STOP_ON_FAILURE")
        self.assertEqual(details["results"][0]["status"], "FAIL")

    def test_timeout_stops_and_records_incomplete_not_unsat(self):
        invoke = Mock(side_effect=subprocess.TimeoutExpired(["test"], 1))
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / "results.json"
            rc = execute_plan(TASKS, report_path=report, invoke=invoke)
            details = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rc, 1)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(details["results"][0]["status"], "TIMEOUT")
        self.assertEqual(details["stop_reason"], "STOP_ON_FAILURE")

    def test_task_count_cap(self):
        invoke = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
        with tempfile.TemporaryDirectory() as work:
            report = Path(work) / "results.json"
            rc = execute_plan(
                TASKS, max_tasks=1, report_path=report, invoke=invoke
            )
            details = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(rc, 0)
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(details["stop_reason"], "TASK_CAP")
        self.assertEqual(len(details["results"]), 1)

    def test_limits_cannot_be_removed_by_cli_parameters(self):
        with self.assertRaises(ValueError):
            execute_plan(TASKS, max_tasks=10)
        with self.assertRaises(ValueError):
            execute_plan(TASKS, budget_seconds=3600)


if __name__ == "__main__":
    unittest.main()
