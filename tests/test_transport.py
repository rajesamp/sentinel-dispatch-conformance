import base64
import json
import os
import sys
import unittest

from integration.check_transport import LocalConnection, run_checks


@unittest.skipUnless(os.name == "posix", "subprocess fixture uses POSIX pipe selectors")
class ProcessBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_checks()
        cls.cases = {c["case"]: c for c in cls.result["cases"]}

    def test_all_six_checks_pass_with_actual_reaped_children(self):
        self.assertEqual(self.result["case_count"], 6)
        for case in self.result["cases"]:
            with self.subTest(case=case["case"]):
                self.assertEqual(case["status"], "passed", case["failure"])
                self.assertEqual(len(case["processes"]), 2)
                self.assertTrue(all(c["clean_exit"] and c["returncode"] == 0 for c in case["processes"]))

    def test_normal_and_mutated_calls_arrive_as_exact_original_bytes(self):
        original = (b'{"id":1,"jsonrpc":"2.0","method":"tools/call","params":'
                    b'{"arguments":{"options":{"fields":["name","size"]},"path":"fixture.txt"},'
                    b'"name":"read_file"}}')
        case = self.cases["normal_and_mutated_arguments"]
        self.assertEqual(len(case["receipts"]), 2)
        for receipt in case["receipts"]:
            body = receipt["response"]["result"]["structuredContent"]
            self.assertEqual(base64.b64decode(body["received_payload_base64"], validate=True), original)
            self.assertEqual(body["received_object"], json.loads(original))
        self.assertEqual([p["audit"]["frames_received"] for p in case["processes"]], [2, 0])

    def test_identical_named_requests_reach_distinct_selected_processes(self):
        case = self.cases["same_name_routing"]
        a, b = case["receipts"]
        self.assertEqual(a["sent_payload_base64"], b["sent_payload_base64"])
        self.assertNotEqual(a["trusted_process_pid"], b["trusted_process_pid"])
        self.assertEqual([a["trusted_server"], b["trusted_server"]], ["server-a", "server-b"])
        self.assertEqual([p["audit"]["frames_received"] for p in case["processes"]], [1, 1])

    def test_descriptor_and_connection_revocation_send_zero_frames(self):
        for name in ("descriptor_replacement", "connection_replacement"):
            with self.subTest(case=name):
                case = self.cases[name]
                self.assertEqual(case["writer_calls"], 0)
                self.assertEqual(case["receipts"], [])
                self.assertEqual([p["audit"]["frames_received"] for p in case["processes"]], [0, 0])
                self.assertEqual([e["reason"] for e in case["events"] if e["action"] == "execute"], ["binding changed"])

    def test_consumed_permit_does_not_create_second_frame(self):
        case = self.cases["single_use"]
        self.assertEqual([e["allowed"] for e in case["events"] if e["action"] == "execute"], [True, False])
        self.assertEqual(case["writer_calls"], 1)
        self.assertEqual([p["audit"]["frames_received"] for p in case["processes"]], [1, 0])

    def test_reapproval_uses_new_process_and_new_authorized_arguments(self):
        case = self.cases["legitimate_reapproval"]
        self.assertEqual([p["audit"]["frames_received"] for p in case["processes"]], [0, 1])
        receipt = case["receipts"][0]
        self.assertEqual(receipt["trusted_connection"], "c2")
        self.assertEqual(receipt["response"]["result"]["structuredContent"]["received_object"]["params"]["arguments"],
                         {"path": "authorized-new.txt"})

    def test_unsupported_method_is_inert_and_counted_as_received_frame(self):
        child = LocalConnection("test-server", "test-connection")
        try:
            receipt = child.send(b'{"jsonrpc":"2.0","id":5,"method":"unsupported"}')
            self.assertEqual(receipt["response"]["error"]["code"], -32601)
        finally:
            lifecycle = child.finish()
        self.assertTrue(lifecycle["clean_exit"])
        self.assertEqual(lifecycle["audit"]["frames_received"], 1)
        self.assertEqual(lifecycle["audit"]["supported_calls_received"], 0)

    def test_silent_child_times_out_and_is_reaped(self):
        child = LocalConnection("test-server", "silent-connection", timeout=0.2,
                                command=[sys.executable, "-I", "-u", "-c", "import time; time.sleep(60)"])
        try:
            with self.assertRaises(TimeoutError):
                child.send(b'{"jsonrpc":"2.0","id":1,"method":"tools/call"}')
        finally:
            lifecycle = child.finish()
        self.assertIsNotNone(child.process.poll())
        self.assertFalse(lifecycle["clean_exit"])
        self.assertIsNone(lifecycle["audit"])

    def test_early_child_exit_is_failure_not_zero_dispatch_protection(self):
        child = LocalConnection("test-server", "closed-connection", timeout=0.5,
                                command=[sys.executable, "-I", "-u", "-c", "pass"])
        try:
            with self.assertRaises((EOFError, BrokenPipeError)):
                child.send(b'{"jsonrpc":"2.0","id":1,"method":"tools/call"}')
        finally:
            lifecycle = child.finish()
        self.assertIsNotNone(child.process.poll())
        self.assertFalse(lifecycle["clean_exit"])


if __name__ == "__main__":
    unittest.main()
