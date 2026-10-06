"""Independent post-development challenges, not an untouched statistical holdout.

Only inert local fixtures are used. Callback misuse tests document trusted-host
assumptions; they must not be counted as server-reachable vulnerabilities.
"""
from copy import deepcopy
from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest

from binding_gate.core import BindingGate, InvalidDefinition, descriptor_bytes
from experiments.adapters import SnapshotAdapter
from experiments.enumerate_traces import generate
from experiments.oracle import check_receipt


ROOT = Path(__file__).resolve().parents[1]


def descriptor(name="read_file", **extra):
    return {"name": name, "description": "Read a local fixture.",
            "inputSchema": {"type": "object", "properties": {}}, **extra}


def strong_arms():
    return [BindingGate(), SnapshotAdapter("revoke")]


class AdversarialReviewTests(unittest.TestCase):
    def ready(self, arm):
        self.assertTrue(arm.refresh("host-a", [descriptor()], "connection-a").accepted)
        selected = arm.select("host-a", "read_file")
        token = arm.prepare(selected, {"path": "approved.txt"})
        self.assertIsNotNone(token)
        return selected, token

    def test_unissued_cross_instance_and_wrong_type_tokens_cannot_enqueue(self):
        first, second = BindingGate(), BindingGate()
        _, first_token = self.ready(first)
        self.ready(second)
        receipts = []
        for token in [first_token, "0" * 32, None, 0, [], {}]:
            self.assertFalse(second.execute(token, lambda *a: receipts.append(a)).allowed)
        self.assertEqual(receipts, [])

    def test_selection_field_tampering_does_not_create_a_permit(self):
        arm = BindingGate()
        selected, _ = self.ready(arm)
        changed = [replace(selected, server="host-b"),
                   replace(selected, name="unregistered"),
                   replace(selected, connection="connection-b"),
                   replace(selected, descriptor=descriptor_bytes(descriptor(title="changed"))),
                   replace(selected, generation=selected.generation + 1)]
        for view in changed:
            with self.subTest(view=view):
                self.assertIsNone(arm.prepare(view, {}))

    def test_prepare_is_trusted_authorization_not_user_intent_authentication(self):
        arm = BindingGate()
        selected, _ = self.ready(arm)
        # A trusted caller can copy Selection and ask to approve any plain JSON
        # arguments. This intentionally documents the boundary, not an exploit.
        token = arm.prepare(replace(selected), {"path": "another-approved-operation.txt"})
        self.assertIsNotNone(token)

    def test_concurrent_replay_enqueues_at_most_once(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                receipts, statuses = [], []
                barrier = threading.Barrier(9)
                def execute():
                    barrier.wait(timeout=3)
                    statuses.append(arm.execute(token, lambda *a: receipts.append(a)).allowed)
                workers = [threading.Thread(target=execute, daemon=True) for _ in range(8)]
                for worker in workers:
                    worker.start()
                barrier.wait(timeout=3)
                for worker in workers:
                    worker.join(timeout=3)
                    self.assertFalse(worker.is_alive())
                self.assertEqual(len(receipts), 1)
                self.assertEqual(sum(statuses), 1)

    def test_refresh_contender_cannot_publish_between_validation_and_enqueue(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                entered, release = threading.Event(), threading.Event()
                attempted, published = threading.Event(), threading.Event()
                events, errors = [], []
                def writer(*unused):
                    entered.set()
                    if not release.wait(3):
                        raise TimeoutError("test failed to release writer")
                    events.append("enqueue")
                def execute():
                    try:
                        arm.execute(token, writer)
                    except BaseException as exc:
                        errors.append(exc)
                def refresh():
                    attempted.set()
                    try:
                        arm.refresh("host-a", [descriptor(title="new")], "connection-a")
                        events.append("publication")
                        published.set()
                    except BaseException as exc:
                        errors.append(exc)
                worker = threading.Thread(target=execute, daemon=True)
                updater = threading.Thread(target=refresh, daemon=True)
                worker.start()
                try:
                    self.assertTrue(entered.wait(3))
                    updater.start()
                    self.assertTrue(attempted.wait(3))
                    self.assertFalse(published.wait(0.05))
                    lock = arm._lock if isinstance(arm, BindingGate) else arm.lock
                    self.assertTrue(lock.locked())
                finally:
                    release.set()
                    worker.join(timeout=3)
                    if updater.ident is not None:
                        updater.join(timeout=3)
                self.assertFalse(worker.is_alive())
                self.assertFalse(updater.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(events, ["enqueue", "publication"])

    def test_revocation_published_before_enqueue_blocks_both_strong_arms(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                arm.refresh("host-a", [descriptor(title="changed")], "connection-a")
                receipts = []
                self.assertFalse(arm.execute(token, lambda *a: receipts.append(a)).allowed)
                self.assertEqual(receipts, [])

    def test_restored_bytes_do_not_restore_revoked_approval(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                original, token = self.ready(arm)
                arm.refresh("host-a", [], "connection-a")
                arm.refresh("host-a", [descriptor()], "connection-a")
                self.assertIsNone(arm.prepare(original, {}))
                self.assertFalse(arm.execute(token, lambda *a: self.fail("revoked enqueue")).allowed)

    def test_full_hash_control_exposes_aba_limitation(self):
        arm = SnapshotAdapter("full_hash")
        _, token = self.ready(arm)
        arm.refresh("host-a", [], "connection-a")
        arm.refresh("host-a", [descriptor()], "connection-a")
        receipts = []
        self.assertTrue(arm.execute(token, lambda *a: receipts.append(a)).allowed)
        self.assertEqual(len(receipts), 1)

    def test_stale_malformed_completion_cannot_withdraw_latest_snapshot(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                older = arm.begin_refresh("host-a")
                newer = arm.begin_refresh("host-a")
                self.assertTrue(arm.complete_refresh("host-a", newer, [descriptor()], "connection-a").accepted)
                self.assertFalse(arm.complete_refresh("host-a", older, [{"name": "broken"}], "connection-a").accepted)
                receipts = []
                self.assertTrue(arm.execute(token, lambda *a: receipts.append(a)).allowed)
                self.assertEqual(len(receipts), 1)

    def test_failed_latest_refresh_withdraws_whole_server_and_preserves_other(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                arm.refresh("host-b", [descriptor()], "connection-b")
                other_token = arm.prepare(arm.select("host-b", "read_file"), {})
                result = arm.refresh("host-a", [descriptor("first"), descriptor("first")], "connection-a")
                self.assertFalse(result.accepted)
                self.assertIsNone(arm.select("host-a", "first"))
                self.assertIsNone(arm.select("host-a", "read_file"))
                self.assertFalse(arm.execute(token, lambda *a: self.fail("partial enqueue")).allowed)
                self.assertTrue(arm.execute(other_token, lambda *a: None).allowed)

    def test_partial_staging_not_visible_during_scanner_callback(self):
        paused, release = threading.Event(), threading.Event()
        def admit(data):
            if data["name"] == "second":
                paused.set()
                if not release.wait(3):
                    raise TimeoutError("test staging timeout")
            return True
        arm = BindingGate(admit=admit)
        original, token = self.ready(arm)
        results = []
        worker = threading.Thread(target=lambda: results.append(arm.refresh(
            "host-a", [descriptor("first"), descriptor("second")], "connection-a")), daemon=True)
        worker.start()
        try:
            self.assertTrue(paused.wait(3))
            self.assertIsNone(arm.select("host-a", "first"))
            self.assertEqual(arm.select("host-a", "read_file"), original)
            # Revocation becomes effective on completed publication, not when a
            # speculative scan begins. This is an explicit contract boundary.
            self.assertTrue(arm.execute(token, lambda *a: None).allowed)
        finally:
            release.set()
            worker.join(timeout=3)
        self.assertFalse(worker.is_alive())
        self.assertTrue(results[0].accepted)
        self.assertIsNone(arm.select("host-a", "read_file"))

    def test_callback_cannot_change_publication_name_away_from_frozen_descriptor(self):
        def mutate(data):
            data["name"] = "changed_by_host_callback"
            return True
        arm = BindingGate(admit=mutate)
        result = arm.refresh("host-a", [descriptor()], "connection-a")
        if result.accepted:
            for name in ("read_file", "changed_by_host_callback"):
                selected = arm.select("host-a", name)
                if selected is None:
                    continue
                self.assertEqual(selected.name, json.loads(selected.descriptor)["name"])
                token = arm.prepare(selected, {})
                receipts = []
                self.assertTrue(arm.execute(token, lambda *a: receipts.append(a)).allowed)
                self.assertEqual(json.loads(receipts[0][2])["params"]["name"],
                                 json.loads(receipts[0][3])["name"])

    def test_raw_duplicate_key_catalogue_is_not_a_supported_gate_input(self):
        arm = BindingGate()
        self.assertFalse(arm.refresh("host-a", b'[{"name":"a","name":"b"}]').accepted)
        # Once another component parses duplicate keys into a dict, their
        # presence is unrecoverable; transport parsing must reject them first.

    def test_nonfinite_surrogate_custom_and_cyclic_inputs_rejected(self):
        bad_values = [float("inf"), float("nan"), "\ud800", object()]
        cyclic = {}
        cyclic["cycle"] = cyclic
        bad_values.append(cyclic)
        for value in bad_values:
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(InvalidDefinition):
                    descriptor_bytes(descriptor(_meta={"value": value}))

    def test_oracle_rejects_overflowed_number_and_nonunicode_scalar(self):
        for raw in (b'{"n":1e999}', b'{"s":"\\ud800"}'):
            with self.subTest(raw=raw):
                approval = {"server": "a", "connection": "c", "descriptor": raw, "request": {}}
                self.assertIn("invalid_descriptor_receipt", check_receipt(approval, deepcopy(approval)))

    def test_signed_zero_exposes_conservative_gate_invalidation(self):
        approval = {"server": "a", "connection": "c", "descriptor": {"n": -0.0}, "request": {}}
        receipt = deepcopy(approval)
        receipt["descriptor"]["n"] = 0.0
        # The coordinator selected structured numeric equality for the safety
        # oracle. Canonical-byte guards conservatively invalidate this equivalent
        # numeric value; report the missed completion, not an oracle bypass.
        self.assertEqual(check_receipt(approval, receipt), [])
        self.assertNotEqual(descriptor_bytes(descriptor(_meta={"n": -0.0})),
                            descriptor_bytes(descriptor(_meta={"n": 0.0})))
        for arm in strong_arms():
            arm.refresh("host-a", [descriptor(_meta={"n": -0.0})], "connection-a")
            token = arm.prepare(arm.select("host-a", "read_file"), {})
            arm.refresh("host-a", [descriptor(_meta={"n": 0.0})], "connection-a")
            self.assertFalse(arm.execute(token, lambda *a: self.fail("unexpected enqueue")).allowed)

    def test_finite_model_labels_match_independent_event_membership_rule(self):
        cases = generate()["cases"]
        counts = {"allow": 0, "deny": 0}
        # Independently derive the absorbing revocation predicate directly from
        # the six-symbol contract, not from generator state or returned labels.
        for case in cases:
            word = case["id"].removeprefix("enum-").split("__")
            expected = "deny" if set(word) & {"publish_changed", "withdraw", "reconnect"} else "allow"
            self.assertEqual(case["expected_policy"], expected)
            counts[expected] += 1
        self.assertEqual(counts, {"allow": 40, "deny": 219})

    def test_both_strong_arms_meet_all_259_finite_traces_in_independent_driver(self):
        for factory in (BindingGate, lambda: SnapshotAdapter("revoke")):
            completions = 0
            for case in generate()["cases"]:
                arm = factory()
                initial = case["initial_catalogs"][0]
                arm.refresh(initial["server"], initial["tools"], initial["connection"])
                view = arm.select("server-a", "read_file")
                args = deepcopy(case["arguments"])
                approval = {"server": "server-a", "connection": "c1",
                            "descriptor": deepcopy(initial["tools"][0]),
                            "request": {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                        "params": {"name": "read_file", "arguments": deepcopy(args)}}}
                token = arm.prepare(view, args)
                self.assertIsNotNone(token)
                for op in case["operations"]:
                    if op["action"] == "refresh":
                        arm.refresh(op["server"], op["tools"], op["connection"])
                    else:
                        self.assertEqual(op["action"], "mutate_args")
                        self.assertEqual(op["path"], ["path"])
                        args["path"] = op["value"]
                receipts = []
                def sink(server, connection, request, descriptor_raw):
                    receipts.append({"server": server, "connection": connection,
                                     "request": request, "descriptor": descriptor_raw})
                arm.execute(token, sink)
                word = case["id"].removeprefix("enum-").split("__")
                revoked = bool(set(word) & {"publish_changed", "withdraw", "reconnect"})
                with self.subTest(arm=type(arm).__name__, trace=case["id"]):
                    self.assertEqual(len(receipts), 0 if revoked else 1)
                    for receipt in receipts:
                        self.assertEqual(check_receipt(approval, receipt, revoked=revoked), [])
                completions += len(receipts)
            self.assertEqual(completions, 40)

    def test_writer_failure_after_enqueue_is_unknown_and_token_remains_consumed(self):
        for arm in strong_arms():
            with self.subTest(arm=type(arm).__name__):
                _, token = self.ready(arm)
                receipts = []
                def partial(*values):
                    receipts.append(values)
                    raise OSError("synthetic acknowledgement loss")
                result = arm.execute(token, partial)
                self.assertEqual(result.reason, "transport outcome unknown")
                self.assertEqual(len(receipts), 1)
                self.assertFalse(arm.execute(token, partial).allowed)
                self.assertEqual(len(receipts), 1)

    def test_writer_reentry_is_an_explicit_unsupported_host_contract(self):
        # The API documents non-reentrant trusted writers. Isolate the deliberate
        # violation in a disposable subprocess; no deadlocked process is retained.
        code = '''
from binding_gate.core import BindingGate
g = BindingGate()
g.refresh("a", [{"name": "x", "inputSchema": {"type": "object"}}])
t = g.prepare(g.select("a", "x"), {})
g.execute(t, lambda *unused: g.select("a", "x"))
'''
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        with self.assertRaises(subprocess.TimeoutExpired):
            subprocess.run([sys.executable, "-c", code], env=env, cwd=ROOT,
                           check=True, capture_output=True, timeout=0.5)


if __name__ == "__main__":
    unittest.main()
