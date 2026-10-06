from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from experiments.adapters import METHODS, NaiveAdapter
from experiments.report_results import build_summary, summarize_trials, write_report
from experiments.run_study import (InvalidScenario, benchmark, run_case, run_study,
                                   validate_manifest, validate_case)
from experiments.scenarios import generate_cases, manifest, refresh, tool


def development_case(identifier="dev-normal"):
    return next(c for c in generate_cases() if c["id"] == identifier)


class ReplayTests(unittest.TestCase):
    def test_all_development_cases_execute_for_all_methods(self):
        cases = [c for c in generate_cases() if c["split"] == "development"]
        self.assertEqual(len(cases), 24)
        for case in cases:
            for method in METHODS:
                with self.subTest(case=case["id"], method=method):
                    result = run_case(case, method)
                    self.assertEqual(result["status"], "completed", result["failure"])

    def test_argument_copy_is_approved_before_mutation(self):
        case = development_case("dev-mutable-arguments")
        original = deepcopy(case)
        for method in ("naive_host", "snapshot_revocation"):
            result = run_case(case, method)
            approval = result["approvals"][0]
            self.assertEqual(json.loads(approval["request_bytes"])["params"]["arguments"], case["arguments"])
            self.assertEqual(result["outcome"]["safe"], method != "naive_host")
        self.assertEqual(case, original)

    def test_source_dictionary_is_not_repaired_by_harness(self):
        result = run_case(development_case("dev-source-copy"), "naive_host")
        self.assertEqual(result["outcome"]["dispatch_count"], 1)
        self.assertIn("descriptor_mismatch", [v["issue"] for v in result["outcome"]["violations"]])
        self.assertEqual(json.loads(result["approvals"][0]["descriptor_bytes"])["description"], "Read fixture.")

    def test_revocation_captured_at_enqueue_not_end(self):
        case = development_case()
        case["operations"] = [refresh([tool(description="Changed after dispatch.")],
                                       at="after_execute", revokes=True)]
        result = run_case(case, "binding_gate")
        self.assertTrue(result["fully_satisfied"])
        self.assertFalse(result["receipts"][0]["revoked_at_dispatch"])
        self.assertTrue(result["events"][-1]["revoked"])

    def test_aba_revocation_is_independent_of_restored_bytes(self):
        result = run_case(development_case("dev-description-aba"), "snapshot_hash")
        self.assertFalse(result["outcome"]["safe"])
        self.assertIn("dispatch_after_relevant_revocation", [v["issue"] for v in result["outcome"]["violations"]])

    def test_reapproval_replaces_record_and_resets_revocation(self):
        result = run_case(development_case("dev-clean-recovery"), "binding_gate")
        self.assertTrue(result["benign_final_completed"])
        self.assertFalse(result["benign_first_pass_completed"])
        self.assertEqual(len(result["approvals"]), 2)
        self.assertNotEqual(result["approvals"][0], result["approvals"][1])
        self.assertEqual(result["receipts"][0]["approval"], result["approvals"][1])
        self.assertFalse(result["receipts"][0]["revoked_at_dispatch"])

    def test_safe_rejection_is_not_benign_completion(self):
        result = run_case(development_case("dev-identical-refresh"), "global_epoch")
        self.assertTrue(result["outcome"]["safe"])
        self.assertFalse(result["benign_final_completed"])
        self.assertFalse(result["outcome"]["policy_satisfied"])

    def test_replay_reuses_consumed_token(self):
        result = run_case(development_case("dev-single-use"), "binding_gate")
        self.assertEqual(result["outcome"]["dispatch_count"], 1)
        calls = [x for x in result["events"] if x["action"] == "execute_returned"]
        self.assertEqual([x["allowed"] for x in calls], [True, False])
        self.assertTrue(calls[1]["replay"])

    def test_sink_truth_survives_bad_gate_return(self):
        class LyingAdapter(NaiveAdapter):
            def execute(self, token, writer):
                super().execute(token, lambda s, c, r, d: writer("wrong-server", c, r, d))
                from types import SimpleNamespace
                return SimpleNamespace(allowed=False, reason="denied", receipt=None)
        with patch.dict(METHODS, {"lying_test": LyingAdapter}):
            result = run_case(development_case(), "lying_test")
        self.assertFalse(result["outcome"]["safe"])
        self.assertEqual(result["outcome"]["dispatch_count"], 1)

    def test_execution_exception_is_retained_and_not_credited(self):
        class BrokenAdapter(NaiveAdapter):
            def execute(self, token, writer):
                raise RuntimeError("intentional harness failure")
        with patch.dict(METHODS, {"broken_test": BrokenAdapter}):
            result = run_case(development_case(), "broken_test")
        self.assertEqual(result["status"], "execution_error")
        self.assertFalse(result["fully_satisfied"])
        self.assertIn("intentional harness failure", result["failure"]["message"])
        self.assertEqual(summarize_trials([result])["safe_completed_trials"], 0)
        class BrokenConstructor:
            def __init__(self):
                raise RuntimeError("constructor failed")
        with patch.dict(METHODS, {"broken_test": BrokenConstructor}):
            result = run_case(development_case(), "broken_test")
        self.assertEqual(result["status"], "execution_error")
        self.assertEqual(result["failure"]["message"], "constructor failed")

    def test_malformed_scenarios_fail_loudly(self):
        bad = development_case()
        bad["operations"] = [{"at": "invented", "action": "refresh", "revokes_approval": False}]
        with self.assertRaises(InvalidScenario):
            validate_case(bad)
        bad = development_case("dev-mutable-arguments")
        bad["operations"][0]["path"] = ["missing", "child"]
        self.assertEqual(run_case(bad, "binding_gate")["status"], "invalid_scenario")
        duplicate = manifest()
        duplicate["cases"].append(deepcopy(duplicate["cases"][0]))
        with self.assertRaises(InvalidScenario):
            validate_manifest(duplicate)


class EvidenceAndTimingTests(unittest.TestCase):
    def test_seeded_paired_timing_and_warmup_records(self):
        rows = []
        benchmark(methods=["snapshot_revocation", "binding_gate"], seed=17,
                  warmups=1, repeats=2, batch_size=2, emit=rows.append)
        self.assertEqual(len(rows), (5 * 2 + 1) * 3)
        self.assertTrue(all(r["status"] == "completed" for r in rows))
        self.assertEqual(sum(r["phase"] == "warmup" for r in rows), 11)
        measured = [r for r in rows if r["phase"] == "measured" and r["operation"] != "scanner_only"]
        for row in measured:
            self.assertEqual(row["ns_per_operation"], row["elapsed_ns"] / 2)
            pair = [r for r in measured if r["pair_id"] == row["pair_id"]]
            self.assertEqual(len(pair), 2)
            self.assertEqual(pair[0]["method_order"], pair[1]["method_order"])
        rerun = []
        benchmark(methods=["snapshot_revocation", "binding_gate"], seed=17,
                  warmups=1, repeats=2, batch_size=2, emit=rerun.append)
        self.assertEqual([r.get("method_order") for r in rows], [r.get("method_order") for r in rerun])

    def test_evidence_reproduces_reports_and_never_overwrites(self):
        suite = manifest()
        suite["cases"] = [development_case(), development_case("dev-mutable-arguments")]
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory) / "run"
            result = run_study(run, suite=suite, methods=["naive_host", "binding_gate"], timing=False,
                               manifest_source=str(Path(__file__).resolve().parents[1] / "data/scenario_manifest.json"))
            self.assertEqual(result["status"], "completed")
            metadata = json.loads((run / "metadata.json").read_text())
            self.assertEqual(metadata["manifest_source"], "data/scenario_manifest.json")
            self.assertNotIn("/", metadata["environment"]["executable"])
            self.assertEqual(metadata["environment"]["upstream_import"], "vendor/sentinel-tpd/sentinel_tpd")
            summary = build_summary(run)
            self.assertEqual(summary["actual_trials"], 4)
            self.assertEqual(summary["by_method"]["naive_host"]["trials_with_invariant_violations"], 1)
            self.assertEqual(summary, json.loads((run / "summary.json").read_text()))
            reproduced = write_report(run, Path(directory) / "reproduced")
            self.assertEqual(summary, reproduced)
            self.assertEqual((run / "tables.tex").read_bytes(), (Path(directory) / "reproduced/tables.tex").read_bytes())
            with self.assertRaises(FileExistsError):
                run_study(run, suite=suite, timing=False)
            with self.assertRaises(FileExistsError):
                write_report(run)
            raw = (run / "trials.jsonl").read_text()
            self.assertIn('"encoding": "base64"', raw)
            (run / "trials.jsonl").write_text(raw + "\n")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                build_summary(run)

    def test_report_checks_coverage_and_embedded_provenance(self):
        suite = manifest()
        suite["cases"] = [development_case()]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            run_study(source, suite=suite, methods=["naive_host", "binding_gate"], timing=False)
            for defect in ("missing_trial", "case_hash", "environment", "code_map"):
                with self.subTest(defect=defect):
                    run = Path(directory) / defect
                    shutil.copytree(source, run)
                    completion = json.loads((run / "completion.json").read_text())
                    if defect in {"missing_trial", "case_hash"}:
                        rows = [json.loads(line) for line in (run / "trials.jsonl").read_text().splitlines()]
                        if defect == "missing_trial":
                            rows.pop()
                            completion["trial_count"] = len(rows)
                        else:
                            rows[0]["case_sha256"] = "0" * 64
                        (run / "trials.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
                    else:
                        metadata = json.loads((run / "metadata.json").read_text())
                        if defect == "environment":
                            metadata["environment"]["cpu_count"] = -1
                        else:
                            metadata["code_files"]["src/binding_gate/core.py"] = "0" * 64
                        (run / "metadata.json").write_text(json.dumps(metadata))
                    # Even coherent outer file hashes cannot conceal semantic
                    # coverage or embedded provenance inconsistencies.
                    completion["output_sha256"] = {name: hashlib.sha256((run / name).read_bytes()).hexdigest()
                                                   for name in completion["output_sha256"]}
                    (run / "completion.json").write_text(json.dumps(completion))
                    with self.assertRaises(ValueError):
                        build_summary(run)


if __name__ == "__main__":
    unittest.main()
