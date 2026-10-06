"""Regenerate descriptive tables from an immutable offline run's raw records."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _object_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def summarize_trials(rows: list[dict]) -> dict:
    completed = [r for r in rows if r["status"] == "completed"]
    benign = [r for r in rows if r["kind"] == "benign"]
    ordinary = [r for r in benign if not r["reapproval_attempts"]]
    recovery = [r for r in benign if r["reapproval_attempts"]]
    violations = Counter(v["issue"] for r in rows for v in r["outcome"]["violations"])
    return {
        "trials": len(rows), "completed_trials": len(completed),
        "execution_failures": len(rows) - len(completed),
        "actual_dispatch_receipts": sum(r["outcome"]["dispatch_count"] for r in rows),
        "violating_receipts": sum(len({v["receipt_index"] for v in r["outcome"]["violations"]}) for r in rows),
        "trials_with_invariant_violations": sum(not r["outcome"]["safe"] for r in rows),
        "safe_completed_trials": sum(r["outcome"]["safe"] for r in completed),
        "safe_dispatch_trials": sum(r["outcome"]["safe"] and r["outcome"]["dispatch_count"] > 0 for r in completed),
        "safe_rejection_trials": sum(r["outcome"]["safe"] and r["outcome"]["dispatch_count"] == 0 for r in completed),
        "policy_satisfied_trials": sum(r["outcome"]["policy_satisfied"] for r in completed),
        "fully_satisfied_trials": sum(r["fully_satisfied"] for r in completed),
        "challenge_trials": sum(r["kind"] == "challenge" for r in rows),
        "challenge_safe_completed_trials": sum(r["kind"] == "challenge" and r["outcome"]["safe"] for r in completed),
        "benign_trials": len(benign),
        "benign_without_reapproval_trials": len(ordinary),
        "benign_first_pass_completed": sum(r["benign_first_pass_completed"] is True for r in benign),
        "benign_with_reapproval_trials": len(recovery),
        "benign_reapproval_completed": sum(r["benign_final_completed"] is True for r in recovery),
        "benign_final_completed": sum(r["benign_final_completed"] is True for r in benign),
        "violations_by_invariant": dict(sorted(violations.items())),
        "cases": [r["case_id"] for r in rows],
    }


def _quantiles(values: list[float]) -> dict:
    if not values:
        return {"p50": None, "p95": None, "minimum": None, "maximum": None}
    values = sorted(values)
    return {"p50": statistics.median(values), "p95": values[math.ceil(0.95 * len(values)) - 1],
            "minimum": values[0], "maximum": values[-1]}


def build_summary(run_dir: Path) -> dict:
    metadata = json.loads((run_dir / "metadata.json").read_text())
    completion = json.loads((run_dir / "completion.json").read_text())
    # Protect reproduction from stale or edited raw records.
    for name, expected in completion["output_sha256"].items():
        if _sha(run_dir / name) != expected:
            raise ValueError("run artifact hash mismatch: " + name)
    trials = _read_rows(run_dir / "trials.jsonl")
    timings = _read_rows(run_dir / "timings.jsonl")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    for field, value in (("scenario_sha256", manifest), ("code_sha256", metadata["code_files"]),
                         ("environment_sha256", metadata["environment"])):
        if _object_sha(value) != metadata["provenance"][field]:
            raise ValueError("underlying provenance digest mismatch: " + field)
    if completion["source_unchanged"] and completion["ending_code_sha256"] != metadata["provenance"]["code_sha256"]:
        raise ValueError("ending source digest disagrees with unchanged-source declaration")
    selected = {c["id"]: c for c in manifest["cases"] if c["split"] in metadata["splits"]}
    if (len(manifest["cases"]) != metadata["manifest_case_count"]
            or len({c["id"] for c in manifest["cases"]}) != len(manifest["cases"])
            or len(selected) != metadata["selected_case_count"]
            or len(set(metadata["methods"])) != len(metadata["methods"])):
        raise ValueError("manifest selection counts or method uniqueness disagree")
    expected_keys = {(case_id, method) for case_id in selected for method in metadata["methods"]}
    if len(expected_keys) != metadata["expected_trial_count"]:
        raise ValueError("expected trial count differs from selected manifest cross methods")
    seen = set()
    for row in trials + timings:
        if row.get("provenance") != metadata["provenance"] or row.get("run_id") != metadata["run_id"]:
            raise ValueError("record provenance mismatch")
        if row["record_type"] == "trial":
            key = row["case_id"], row["method"]
            if key in seen:
                raise ValueError("duplicate trial record")
            if key not in expected_keys:
                raise ValueError("trial does not belong to selected manifest and methods")
            case = selected[row["case_id"]]
            if row["case_sha256"] != _object_sha(case):
                raise ValueError("trial case hash differs from manifest")
            if any(row[field] != case[field] for field in ("family", "split", "kind", "expected_policy")):
                raise ValueError("trial labels differ from manifest")
            seen.add(key)
    if len(trials) != completion["trial_count"]:
        raise ValueError("completion count differs from raw trial count")
    if completion["status"] == "completed" and seen != expected_keys:
        raise ValueError("completed run lacks exact selected manifest cross methods coverage")
    by_method = {method: summarize_trials([r for r in trials if r["method"] == method])
                 for method in metadata["methods"]}
    by_split = {split: {method: summarize_trials([r for r in trials if r["method"] == method and r["split"] == split])
                       for method in metadata["methods"]} for split in metadata["splits"]}
    by_family = {family: {method: summarize_trials([r for r in trials if r["method"] == method and r["family"] == family])
                         for method in metadata["methods"]} for family in metadata["families"]}
    grouped = defaultdict(list)
    for row in timings:
        if row["phase"] == "measured":
            grouped[row["operation"], row["method"]].append(row)
    timing_summary = {}
    for (operation, method), values in sorted(grouped.items()):
        completed = [r for r in values if r["status"] == "completed"]
        timing_summary.setdefault(operation, {})[method] = {
            "measured_batch_samples": len(values), "successful_batch_samples": len(completed),
            "execution_failures": len(values) - len(completed),
            "timed_operations": sum(r["batch_size"] for r in completed),
            "ns_per_operation": _quantiles([r["ns_per_operation"] for r in completed]),
            "empty_harness_ns_per_operation": _quantiles([r["empty_harness_ns_per_operation"]
                                                           for r in completed if "empty_harness_ns_per_operation" in r]),
            "paired_harness_adjusted_ns_per_operation": _quantiles([r["paired_harness_adjusted_ns_per_operation"]
                                                                     for r in completed if "paired_harness_adjusted_ns_per_operation" in r]),
        }
    return {"schema_version": 1, "run_id": metadata["run_id"], "label": metadata["label"],
            "provenance": metadata["provenance"], "run_status": completion["status"],
            "source_unchanged": completion["source_unchanged"], "scope": metadata["scope"],
            "manifest_case_count": metadata["manifest_case_count"], "selected_case_count": metadata["selected_case_count"],
            "unique_families": len(metadata["families"]), "expected_trials": metadata["expected_trial_count"],
            "actual_trials": len(trials), "by_method": by_method, "by_split": by_split,
            "by_family": by_family, "timing": timing_summary,
            "quantile_definition": "p50 is sample median; p95 is nearest-rank ceil(0.95*n); samples are batch means",
            "completion_boundary": "synchronous local transport sink enqueue, not remote execution",
            "verification_disclosure": metadata["verification_disclosure"],
            "limitations": ["Designed cases are not independent attack samples; no scenario confidence intervals.",
                            "Timing is one sequential local process session; no timing confidence intervals.",
                            "No memory, network, LLM behavior, detector accuracy or production scalability measurement.",
                            "Reapproval cases run the declared fresh-approval path; no automatic retries are invented.",
                            "First-pass denominator excludes authored reapproval cases; final benign denominator includes them."]}


def _fraction(n: int, d: int) -> str:
    return f"{n}/{d}" if d else "—"


def markdown_report(summary: dict) -> str:
    lines = [f"# Offline run {summary['run_id']}", "",
             f"Run label: `{summary['label']}`. Status: **{summary['run_status']}**. "
             f"Source unchanged during run: `{summary['source_unchanged']}`.", "",
             f"{summary['selected_case_count']} selected cases from {summary['manifest_case_count']} manifest cases; "
             f"{summary['unique_families']} selected family labels; {summary['actual_trials']}/{summary['expected_trials']} expected arm-case executions.",
             "", summary["scope"], "", summary["verification_disclosure"] + ".", "",
             "Completion below means enqueue into the local sink. A safe rejection is distinct from a completed approved operation.", ""]
    for split, methods in [("All selected cases", summary["by_method"]), *summary["by_split"].items()]:
        lines += [f"## {split}", "",
                  "| Method | Failed executions | Unsafe traces | Unsafe receipts / receipts | Policy met | Fully met | Benign first pass | Benign final |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for method, data in methods.items():
            lines.append(f"| {method} | {data['execution_failures']}/{data['trials']} | "
                         f"{data['trials_with_invariant_violations']}/{data['trials']} | "
                         f"{_fraction(data['violating_receipts'], data['actual_dispatch_receipts'])} | "
                         f"{data['policy_satisfied_trials']}/{data['trials']} | "
                         f"{data['fully_satisfied_trials']}/{data['trials']} | "
                         f"{_fraction(data['benign_first_pass_completed'], data['benign_without_reapproval_trials'])} | "
                         f"{_fraction(data['benign_final_completed'], data['benign_trials'])} |")
        lines.append("")
    lines += ["First-pass denominator includes benign cases without a declared reapproval. Final benign completion includes authored recovery paths. Execution failures are retained and are never credited as prevention.",
              "", "## Local timing", "", summary["quantile_definition"] + ".", "",
              "Values include the Python batch-loop/call cost and use microseconds per operation. No subtraction is applied here; paired empty-harness and un-clamped adjusted values remain in JSON and raw samples.", "",
              "| Operation | Method | Batch samples | Timed operations | p50 µs | p95 µs |",
              "|---|---|---:|---:|---:|---:|"]
    for operation, methods in summary["timing"].items():
        for method, data in methods.items():
            q = data["ns_per_operation"]
            p50 = "—" if q["p50"] is None else f"{q['p50'] / 1000:.3f}"
            p95 = "—" if q["p95"] is None else f"{q['p95'] / 1000:.3f}"
            lines.append(f"| {operation} | {method} | {data['successful_batch_samples']}/{data['measured_batch_samples']} | "
                         f"{data['timed_operations']} | {p50} | {p95} |")
    lines += ["", "## Interpretation limits", ""] + ["- " + x for x in summary["limitations"]]
    lines += ["", "Raw evidence: `trials.jsonl`, `timings.jsonl`, `manifest.json`, `metadata.json`, and `completion.json`. "
              "All records carry scenario, source-tree, and environment hashes. Transport bytes use explicit base64 envelopes.", ""]
    return "\n".join(lines)


def latex_tables(summary: dict) -> str:
    def esc(value):
        return str(value).replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("%", r"\%").replace("&", r"\&").replace("#", r"\#")
    lines = ["% Generated from raw run evidence; do not edit numerical cells.",
             "% Run: " + summary["run_id"], r"\begin{tabular}{lrrrrrr}",
             r"Method & Trials & Unsafe & Receipts & Policy & Benign first & Benign final \\", r"\hline"]
    for method, d in summary["by_method"].items():
        first = f"{d['benign_first_pass_completed']}/{d['benign_without_reapproval_trials']}"
        final = f"{d['benign_final_completed']}/{d['benign_trials']}"
        lines.append(f"{esc(method)} & {d['trials']} & {d['trials_with_invariant_violations']} & "
                     f"{d['actual_dispatch_receipts']} & {d['policy_satisfied_trials']} & {first} & {final} " + r"\\")
    lines += [r"\end{tabular}", "", r"\begin{tabular}{llrr}",
              r"Operation & Method & p50 ($\mu$s) & p95 ($\mu$s) \\", r"\hline"]
    for operation, methods in summary["timing"].items():
        for method, d in methods.items():
            q = d["ns_per_operation"]
            if q["p50"] is not None:
                lines.append(f"{esc(operation)} & {esc(method)} & {q['p50']/1000:.3f} & {q['p95']/1000:.3f} " + r"\\")
    return "\n".join(lines + [r"\end{tabular}", ""])


def write_report(run_dir: Path, output: Path | None = None) -> dict:
    run_dir = Path(run_dir)
    output = run_dir if output is None else Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / name for name in ("summary.json", "summary.md", "tables.tex")]
    if any(p.exists() for p in paths):
        raise FileExistsError("report files already exist; use a fresh --output directory")
    summary = build_summary(run_dir)
    texts = [json.dumps(summary, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
             markdown_report(summary), latex_tables(summary)]
    for path, value in zip(paths, texts):
        with path.open("x", encoding="utf-8") as stream:
            stream.write(value)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="fresh report destination")
    args = parser.parse_args()
    write_report(args.run_dir, args.output)
    print(str(args.output.resolve()))


if __name__ == "__main__":
    main()
