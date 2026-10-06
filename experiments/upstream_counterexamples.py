"""Measure narrowly scoped upstream behavior with inert metadata and no tool calls.

Execution reads the vendored package, performs in-memory checks, and emits JSON
to stdout. It never invokes an MCP tool, makes network requests, or writes files.
Predicted outcomes are paired with observations, not reported as attack recall.
The scheduler hook in the race case only waits; a separate actor updates the
shared catalogue dictionary. Host-dependent cases are labelled accordingly.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import threading
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PROJECT_ROOT / "vendor" / "sentinel-tpd"
COMMIT = "5ce5d56e57a0acd092435fca5d89b78d0b39ee7b"
SOURCE_URL = f"https://github.com/rajesamp/sentinel-tpd/blob/{COMMIT}/"
EXPECTED_BLOBS = {
    "__init__.py": "bec2fd11829ae6efcba718302718974689fc29e6",
    "audit.py": "4bf4815668b67f45923a2c46a96974cbad72af15",
    "registry.py": "27225015688724ac202c87cb0094a8912b96028a",
    "scanner.py": "578ddae22791784f3334bfdf973d6579a8c082ac",
    "signals.py": "03888a86823c2fd75058009999f519abd5483d0d",
}
MARKER = "<IMPORTANT>test marker</IMPORTANT>"


def _verify_sources() -> dict[str, dict[str, str]]:
    result = {}
    for filename, expected in EXPECTED_BLOBS.items():
        path = VENDOR_ROOT / "sentinel_tpd" / filename
        data = path.read_bytes()
        git_blob = hashlib.sha1(
            f"blob {len(data)}\0".encode("ascii") + data
        ).hexdigest()
        if git_blob != expected:
            raise RuntimeError(f"Vendored source differs from pinned commit: {filename}")
        result[filename] = {
            "git_blob_sha1": git_blob,
            "sha256": hashlib.sha256(data).hexdigest(),
            "url": SOURCE_URL + "sentinel_tpd/" + filename,
        }
    return result


SOURCE_PROVENANCE = _verify_sources()
_PACKAGE_NAME = "_sentinel_tpd_baseline_5ce5d56e"
if _PACKAGE_NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        _PACKAGE_NAME,
        VENDOR_ROOT / "sentinel_tpd" / "__init__.py",
        submodule_search_locations=[str(VENDOR_ROOT / "sentinel_tpd")],
    )
    if _spec is None or _spec.loader is None:
        raise RuntimeError("Cannot load pinned upstream package")
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_PACKAGE_NAME] = _module
    _spec.loader.exec_module(_module)
_upstream = sys.modules[_PACKAGE_NAME]
if Path(_upstream.__file__).resolve() != (VENDOR_ROOT / "sentinel_tpd" / "__init__.py").resolve():
    raise RuntimeError("Unexpected package source in baseline module namespace")

AuditChain = _upstream.AuditChain
ToolRegistry = _upstream.ToolRegistry
fingerprint = _upstream.fingerprint
scan_tool_metadata = _upstream.scan_tool_metadata


def clean_tool(description: str = "Return a value.") -> dict[str, Any]:
    return {
        "name": "lookup",
        "description": description,
        "inputSchema": {"type": "object"},
    }


def _record(
    case_id: str,
    family: str,
    role: str,
    support_class: str,
    precondition: str,
    observed: dict[str, bool],
    expected: dict[str, bool],
    interpretation: str,
    refs: list[str],
) -> dict[str, Any]:
    if set(observed) != set(expected):
        raise ValueError(f"Mismatched observation keys for {case_id}")
    if any(type(value) is not bool for value in [*observed.values(), *expected.values()]):
        raise TypeError("Observation and expectation values must be actual booleans")
    return {
        "case_id": case_id,
        "family": family,
        "role": role,
        "support_class": support_class,
        "precondition": precondition,
        "observed": observed,
        "expected": expected,
        "matches_expected": observed == expected,
        "interpretation": interpretation,
        "source_refs": [SOURCE_URL + ref for ref in refs],
    }


def malformed_schema_records() -> list[dict[str, Any]]:
    variants = [
        ("null", None),
        ("string", "not a schema object"),
        ("number", 17),
        ("list", ["object"]),
        ("missing", None),
    ]
    records = []
    for label, schema in variants:
        tool = clean_tool()
        if label == "missing":
            del tool["inputSchema"]
        else:
            tool["inputSchema"] = schema
        registry = ToolRegistry()
        scan = scan_tool_metadata(tool)
        registered = registry.register(tool)
        checked = registry.check_invocation(tool)
        observed = {
            "scan_allowed": scan.allowed,
            "registration_allowed": registered.allowed,
            "invocation_allowed": checked.allowed,
        }
        records.append(_record(
            "malformed_schema_" + label, "schema_validation", "counterexample",
            "direct_claim",
            "Raw tool dictionaries reach the library without upstream MCP schema validation.",
            observed, dict.fromkeys(observed, True),
            "Admission contradicts documented malformed-schema denial. This does not establish that an MCP SDK accepts the input or that harmful execution occurs.",
            ["sentinel_tpd/scanner.py#L8-L9", "sentinel_tpd/scanner.py#L61-L87", "sentinel_tpd/scanner.py#L110-L162"],
        ))
    return records


def stale_registration_record() -> dict[str, Any]:
    registry = ToolRegistry()
    old = clean_tool()
    replacement = clean_tool(MARKER)
    initial = registry.register(old)
    denied = registry.register(replacement)
    retained = registry.is_registered(old["name"])
    old_check = registry.check_invocation(old)
    new_check = registry.check_invocation(replacement)
    return _record(
        "denied_reregistration_retains_old_snapshot", "replacement_policy",
        "conditional_observation", "host_precondition",
        "Host uses register for replacement and defines denial as revoking earlier admission.",
        {
            "initial_allowed": initial.allowed,
            "replacement_allowed": denied.allowed,
            "old_entry_retained": retained,
            "old_snapshot_allowed": old_check.allowed,
            "current_poisoned_snapshot_allowed": new_check.allowed,
            "quarantined_after_current_check": registry.is_quarantined(old["name"]),
        },
        {
            "initial_allowed": True, "replacement_allowed": False,
            "old_entry_retained": True, "old_snapshot_allowed": True,
            "current_poisoned_snapshot_allowed": False,
            "quarantined_after_current_check": True,
        },
        "Old admission persists, but the changed poisoned descriptor is denied. Retaining the last good snapshot can be legitimate under another replacement policy.",
        ["sentinel_tpd/registry.py#L54-L61", "sentinel_tpd/registry.py#L82-L114"],
    )


def projection_records() -> list[dict[str, Any]]:
    def set_title(tool: dict[str, Any], value: str) -> None:
        tool["title"] = value

    def set_annotation_title(tool: dict[str, Any], value: str) -> None:
        tool["annotations"] = {"title": value}

    def set_output_description(tool: dict[str, Any], value: str) -> None:
        tool["outputSchema"] = {
            "type": "object",
            "properties": {"value": {"type": "string", "description": value}},
        }

    setters: list[tuple[str, Callable[[dict[str, Any], str], None]]] = [
        ("title", set_title),
        ("annotations_title", set_annotation_title),
        ("output_schema_description", set_output_description),
    ]
    records = []
    for label, setter in setters:
        original = clean_tool()
        setter(original, "Value lookup")
        changed = copy.deepcopy(original)
        setter(changed, MARKER)
        registry = ToolRegistry()
        admitted = registry.register(original)
        observed = {
            "original_allowed": admitted.allowed,
            "changed_scan_allowed": scan_tool_metadata(changed).allowed,
            "fingerprint_unchanged": fingerprint(original) == fingerprint(changed),
            "changed_invocation_allowed": registry.check_invocation(changed).allowed,
        }
        records.append(_record(
            "omitted_field_" + label, "descriptor_projection", "scope_observation",
            "scope_extension",
            f"The host consumes {label}; other tool fields are unchanged.",
            observed, dict.fromkeys(observed, True),
            "This field is outside the baseline's explicitly documented fingerprint projection. Relevance depends on the host exposing or trusting it.",
            ["sentinel_tpd/scanner.py#L61-L87", "sentinel_tpd/scanner.py#L96-L107", "README.md#L97-L98"],
        ))
    return records


class _SchedulingAudit(AuditChain):
    """Test-only pause after scanning. It does not modify any descriptor."""

    def __init__(self, scanned: threading.Barrier, updated: threading.Barrier) -> None:
        super().__init__()
        self.scanned = scanned
        self.updated = updated
        self.pause_next_registration = True

    def append(self, event: str, payload: dict[str, Any]) -> dict[str, Any]:
        if event == "TOOL_REGISTERED" and self.pause_next_registration:
            self.pause_next_registration = False
            self.scanned.wait(timeout=5)
            self.updated.wait(timeout=5)
        return super().append(event, payload)


def registration_interleaving_record(copy_snapshot: bool = False) -> dict[str, Any]:
    catalogue = clean_tool()
    submitted = copy.deepcopy(catalogue) if copy_snapshot else catalogue
    scanned = threading.Barrier(2)
    updated = threading.Barrier(2)
    registry = ToolRegistry(audit=_SchedulingAudit(scanned, updated))
    actor_errors: list[BaseException] = []

    def catalogue_update_actor() -> None:
        try:
            scanned.wait(timeout=5)
            # Only this separate actor mutates the untrusted catalogue object.
            catalogue["description"] = MARKER
            updated.wait(timeout=5)
        except BaseException as exc:
            actor_errors.append(exc)

    actor = threading.Thread(target=catalogue_update_actor, name="catalogue-update")
    actor.start()
    try:
        verdict = registry.register(submitted)
    except BaseException:
        scanned.abort()
        updated.abort()
        raise
    finally:
        actor.join(timeout=6)
    if actor.is_alive():
        scanned.abort()
        updated.abort()
        raise RuntimeError("Catalogue actor did not complete")
    if actor_errors:
        raise RuntimeError("Catalogue actor failed") from actor_errors[0]
    observed = {
        "registration_allowed": verdict.allowed,
        "catalogue_was_mutated": catalogue["description"] == MARKER,
        "fresh_scan_of_current_allowed": scan_tool_metadata(catalogue).allowed,
        "current_invocation_allowed": registry.check_invocation(catalogue).allowed,
    }
    expected = {
        "registration_allowed": True,
        "catalogue_was_mutated": True,
        "fresh_scan_of_current_allowed": False,
        "current_invocation_allowed": not copy_snapshot,
    }
    return _record(
        "registration_race_copied_snapshot" if copy_snapshot else "registration_scan_fingerprint_interleaving",
        "registration_snapshot", "mitigation_control" if copy_snapshot else "conditional_counterexample",
        "host_precondition",
        "A host catalogue update can interleave with registration on a shared dictionary. The audit hook only schedules; a separate actor updates metadata.",
        observed, expected,
        "A defensive descriptor copy before registration prevents this interleaving from admitting unscanned content. The changed current descriptor is denied."
        if copy_snapshot else
        "The clean scan verdict precedes fingerprinting of mutated content. This conditional race assumes shared mutable host state; baseline thread safety is not promised.",
        ["sentinel_tpd/registry.py#L54-L61", "sentinel_tpd/registry.py#L90-L114"],
    )


def identity_records() -> list[dict[str, Any]]:
    a = clean_tool("Return a value from A.")
    b = clean_tool("Return a value from B.")
    shared = ToolRegistry()
    admitted_a = shared.register(a)
    admitted_b = shared.register(b)
    b_before = shared.check_invocation(b)
    a_after = shared.check_invocation(a)
    b_after = shared.check_invocation(b)
    collision = _record(
        "shared_registry_same_name_collision", "server_identity", "conditional_observation",
        "host_precondition", "One unnamespaced registry is shared across two distinct trusted server connections.",
        {
            "a_registered": admitted_a.allowed, "b_registered": admitted_b.allowed,
            "b_before_a_check_allowed": b_before.allowed,
            "a_after_overwrite_allowed": a_after.allowed,
            "b_after_a_check_allowed": b_after.allowed,
        },
        {
            "a_registered": True, "b_registered": True,
            "b_before_a_check_allowed": True, "a_after_overwrite_allowed": False,
            "b_after_a_check_allowed": False,
        },
        "The adapter couples two servers' fingerprints and quarantine, causing an availability collision. It does not demonstrate malicious dispatch.",
        ["sentinel_tpd/registry.py#L47-L60", "sentinel_tpd/registry.py#L75-L114"],
    )
    per_server = {"A": ToolRegistry(), "B": ToolRegistry()}
    snapshots = {"A": copy.deepcopy(a), "B": copy.deepcopy(b)}
    allowed = {}
    for origin in ("A", "B"):
        allowed[origin + "_registered"] = per_server[origin].register(snapshots[origin]).allowed
    for origin in ("A", "B"):
        allowed[origin + "_invocation_allowed"] = per_server[origin].check_invocation(
            copy.deepcopy(snapshots[origin])
        ).allowed
    separated = _record(
        "per_server_copied_snapshot_adapter", "server_identity", "mitigation_control",
        "host_precondition", "Trusted host selects a distinct registry per connection and copies each descriptor.",
        allowed, dict.fromkeys(allowed, True),
        "A simple host adapter preserves both same-name tools. This is a fair strengthened baseline control, not new detection functionality.",
        ["README.md#L83-L84", "sentinel_tpd/registry.py#L41-L60"],
    )
    return [collision, separated]


def positive_control_records() -> list[dict[str, Any]]:
    records = []
    registry = ToolRegistry()
    clean = clean_tool()
    registered = registry.register(clean)
    records.append(_record(
        "benign_registration_and_call", "ordinary_controls", "positive_control", "direct_claim",
        "Valid benign descriptor in a single-server sequential use.",
        {"registration_allowed": registered.allowed, "invocation_allowed": registry.check_invocation(clean).allowed},
        {"registration_allowed": True, "invocation_allowed": True},
        "Ordinary valid use succeeds.", ["sentinel_tpd/registry.py#L54-L61", "sentinel_tpd/registry.py#L112-L114"],
    ))
    registry = ToolRegistry()
    poisoned = clean_tool(MARKER)
    registered = registry.register(poisoned)
    records.append(_record(
        "known_poisoning_pattern_denied", "ordinary_controls", "positive_control", "direct_claim",
        "The controlled denial marker is in the covered description field.",
        {"registration_allowed": registered.allowed, "invocation_allowed": registry.check_invocation(poisoned).allowed},
        {"registration_allowed": False, "invocation_allowed": False},
        "A known pattern is denied normally.", ["sentinel_tpd/signals.py#L49-L59", "sentinel_tpd/registry.py#L82-L88"],
    ))
    registry = ToolRegistry()
    records.append(_record(
        "unknown_tool_denied", "ordinary_controls", "positive_control", "direct_claim",
        "The otherwise clean tool was never registered.",
        {"invocation_allowed": registry.check_invocation(clean_tool()).allowed},
        {"invocation_allowed": False}, "Default denial for an unknown name works.",
        ["sentinel_tpd/registry.py#L82-L88"],
    ))
    registry = ToolRegistry()
    original = clean_tool()
    registry.register(original)
    changed = clean_tool(MARKER)
    changed_check = registry.check_invocation(changed)
    quarantined = registry.is_quarantined(original["name"])
    refreshed = registry.rescan_on_refresh([copy.deepcopy(original)])
    records.append(_record(
        "covered_mutation_denied_then_clean_refresh_recovers", "ordinary_controls", "positive_control", "direct_claim",
        "Covered metadata changes before check; subsequent refresh advertises a clean descriptor.",
        {
            "mutated_invocation_allowed": changed_check.allowed,
            "quarantined_after_mutation": quarantined,
            "clean_refresh_allowed": refreshed[0].allowed,
            "quarantined_after_clean_refresh": registry.is_quarantined(original["name"]),
            "clean_invocation_allowed_after_refresh": registry.check_invocation(original).allowed,
        },
        {
            "mutated_invocation_allowed": False, "quarantined_after_mutation": True,
            "clean_refresh_allowed": True, "quarantined_after_clean_refresh": False,
            "clean_invocation_allowed_after_refresh": True,
        },
        "Mutation denial and clean recovery are intended behavior. Recovery is not a bypass.",
        ["sentinel_tpd/registry.py#L90-L114", "sentinel_tpd/registry.py#L118-L136", "tests/test_sentinel_tpd.py#L101-L120"],
    ))
    registry = ToolRegistry()
    registry.register(original)
    registry.check_invocation(changed)
    denied_refresh = registry.rescan_on_refresh([changed])
    records.append(_record(
        "poisoned_refresh_keeps_quarantine", "ordinary_controls", "positive_control", "direct_claim",
        "An already quarantined tool is refreshed with the still-poisoned descriptor.",
        {
            "refresh_allowed": denied_refresh[0].allowed,
            "still_quarantined": registry.is_quarantined(original["name"]),
            "invocation_allowed": registry.check_invocation(changed).allowed,
        },
        {"refresh_allowed": False, "still_quarantined": True, "invocation_allowed": False},
        "Poisoned refresh does not clear quarantine.", ["sentinel_tpd/registry.py#L118-L136"],
    ))
    return records


def run_counterexamples() -> dict[str, Any]:
    records = [
        *positive_control_records(),
        *malformed_schema_records(),
        stale_registration_record(),
        *projection_records(),
        registration_interleaving_record(False),
        registration_interleaving_record(True),
        *identity_records(),
    ]
    ids = [record["case_id"] for record in records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate case identifier")
    return {
        "schema_version": 1,
        "experiment": "upstream_source_contract_reproductions",
        "provenance": {
            "repository": "rajesamp/sentinel-tpd", "commit": COMMIT,
            "package_version": _upstream.__version__,
            "source_files": SOURCE_PROVENANCE,
            "python": platform.python_version(),
            "protocol_reference": "https://modelcontextprotocol.io/specification/2025-11-25/server/tools",
        },
        "measurement_boundary": "In-memory source/API observations; no real MCP transport, model, tool execution, harm outcome, or performance claim.",
        "records_are_not_independent_attack_families": True,
        "all_expected_observations": all(record["matches_expected"] for record in records),
        "records": records,
    }


def main() -> int:
    result = run_counterexamples()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_expected_observations"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
