"""Tests for SENTINEL-TPD. Runnable via `python -m unittest` or `pytest`."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sentinel_tpd import (  # noqa: E402
    AuditChain,
    ToolRegistry,
    fingerprint,
    scan_tool_metadata,
)
from tests.fixtures.poisoned_tools import (  # noqa: E402
    ALL_POISONED,
    BENIGN_CALCULATOR,
    BENIGN_WEATHER,
    POISONED_EXFIL,
    POISONED_IMPERATIVE_TAG,
    POISONED_PARAM_SENSITIVE_PATH,
    RUGPULL_AFTER,
    RUGPULL_BEFORE,
)


class TestScanner(unittest.TestCase):
    def test_benign_tools_allowed(self) -> None:
        for tool in (BENIGN_WEATHER, BENIGN_CALCULATOR):
            v = scan_tool_metadata(tool)
            self.assertTrue(v.allowed, f"{tool['name']} wrongly denied: {v}")
            self.assertEqual(v.max_severity, 0)

    def test_every_poisoned_fixture_denied(self) -> None:
        for tool in ALL_POISONED:
            v = scan_tool_metadata(tool)
            self.assertFalse(
                v.allowed, f"{tool['name']} wrongly ALLOWED: {v.to_dict()}"
            )
            self.assertGreaterEqual(v.max_severity, 3)

    def test_imperative_tag_is_m4(self) -> None:
        v = scan_tool_metadata(POISONED_IMPERATIVE_TAG)
        self.assertEqual(v.max_severity, 4)
        self.assertIn("TPD-IMPERATIVE-TAG", {f.signal_id for f in v.findings})

    def test_exfil_destination_is_m4(self) -> None:
        v = scan_tool_metadata(POISONED_EXFIL)
        self.assertEqual(v.max_severity, 4)
        self.assertIn("TPD-EXFIL-DEST", {f.signal_id for f in v.findings})

    def test_nested_parameter_description_is_scanned(self) -> None:
        v = scan_tool_metadata(POISONED_PARAM_SENSITIVE_PATH)
        self.assertFalse(v.allowed)
        hit_paths = {f.field_path for f in v.findings}
        self.assertTrue(
            any("inputSchema" in p for p in hit_paths),
            f"expected a schema-level hit, got {hit_paths}",
        )

    def test_fail_closed_on_malformed_metadata(self) -> None:
        for bad in (None, "not-a-dict", 42, {"description": "no name"}):
            v = scan_tool_metadata(bad)
            self.assertFalse(v.allowed)
            self.assertEqual(v.max_severity, 4)

    def test_verdict_serializes(self) -> None:
        v = scan_tool_metadata(POISONED_IMPERATIVE_TAG)
        blob = json.dumps(v.to_dict())
        self.assertIn("TPD-IMPERATIVE-TAG", blob)


class TestRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.reg = ToolRegistry()

    def test_clean_tool_registers_and_invokes(self) -> None:
        v = self.reg.register(BENIGN_WEATHER)
        self.assertTrue(v.allowed)
        self.assertTrue(self.reg.is_registered("get_weather"))
        d = self.reg.check_invocation(BENIGN_WEATHER)
        self.assertTrue(d.allowed)

    def test_poisoned_tool_never_registers(self) -> None:
        v = self.reg.register(POISONED_IMPERATIVE_TAG)
        self.assertFalse(v.allowed)
        self.assertFalse(self.reg.is_registered("add_numbers"))
        d = self.reg.check_invocation(POISONED_IMPERATIVE_TAG)
        self.assertFalse(d.allowed)
        self.assertIn("never registered", d.reason)

    def test_unregistered_tool_default_denied(self) -> None:
        d = self.reg.check_invocation(BENIGN_CALCULATOR)
        self.assertFalse(d.allowed)
        self.assertIn("default-deny", d.reason)

    def test_rug_pull_detected_and_quarantined(self) -> None:
        self.assertTrue(self.reg.register(RUGPULL_BEFORE).allowed)
        self.assertTrue(self.reg.check_invocation(RUGPULL_BEFORE).allowed)
        # Metadata mutates between registration and this call:
        d = self.reg.check_invocation(RUGPULL_AFTER)
        self.assertFalse(d.allowed)
        self.assertIn("rug pull", d.reason)
        self.assertTrue(self.reg.is_quarantined("fetch_url"))
        # Even the ORIGINAL clean metadata is now denied until re-registered:
        d2 = self.reg.check_invocation(RUGPULL_BEFORE)
        self.assertFalse(d2.allowed)
        self.assertIn("quarantined", d2.reason)

    def test_refresh_rescans_and_lifts_quarantine_on_clean_scan(self) -> None:
        self.reg.register(RUGPULL_BEFORE)
        self.reg.check_invocation(RUGPULL_AFTER)  # triggers quarantine
        verdicts = self.reg.rescan_on_refresh([RUGPULL_BEFORE, BENIGN_WEATHER])
        self.assertTrue(all(v.allowed for v in verdicts))
        self.assertFalse(self.reg.is_quarantined("fetch_url"))
        self.assertTrue(self.reg.check_invocation(RUGPULL_BEFORE).allowed)

    def test_fingerprint_stable_under_key_order(self) -> None:
        reordered = dict(reversed(list(BENIGN_WEATHER.items())))
        self.assertEqual(fingerprint(BENIGN_WEATHER), fingerprint(reordered))

    def test_registry_writes_audit_events(self) -> None:
        self.reg.register(BENIGN_WEATHER)
        self.reg.register(POISONED_IMPERATIVE_TAG)
        events = [e["event"] for e in self.reg.audit.entries]
        self.assertIn("TOOL_REGISTERED", events)
        self.assertIn("TOOL_DENIED", events)
        ok, detail = self.reg.audit.verify()
        self.assertTrue(ok, detail)


class TestAuditChain(unittest.TestCase):
    def test_chain_verifies_when_untouched(self) -> None:
        chain = AuditChain()
        for i in range(5):
            chain.append("EVENT", {"i": i})
        ok, detail = chain.verify()
        self.assertTrue(ok, detail)
        self.assertEqual(len(chain), 5)

    def test_tampering_breaks_chain(self) -> None:
        chain = AuditChain()
        for i in range(5):
            chain.append("EVENT", {"i": i})
        chain.entries  # copy accessor — mutate internals directly instead:
        chain._entries[2]["payload"]["i"] = 999  # simulate tamper
        ok, detail = chain.verify()
        self.assertFalse(ok)
        self.assertIn("seq 2", detail)

    def test_jsonl_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "audit.jsonl"
            chain = AuditChain(path)
            chain.append("A", {"x": 1})
            chain.append("B", {"y": 2})
            head = chain.head
            reloaded = AuditChain(path)
            ok, detail = reloaded.verify()
            self.assertTrue(ok, detail)
            self.assertEqual(reloaded.head, head)
            self.assertEqual(len(reloaded), 2)


if __name__ == "__main__":
    unittest.main()
