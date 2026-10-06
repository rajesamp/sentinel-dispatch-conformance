import json
import unittest

from binding_gate.core import BindingGate, descriptor_bytes, InvalidDefinition


def tool(name="read_file", description="Read a fixture.", **extra):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": {}}, **extra}


class TestCore(unittest.TestCase):
    def test_global_epoch_is_captured_at_selection(self):
        gate = BindingGate(global_epoch=True)
        gate.refresh('a', [tool()], 'a1')
        gate.refresh('b', [tool()], 'b1')
        selected = gate.select('a', 'read_file')
        permit = gate.prepare(selected, {})
        receipts = []
        self.assertTrue(gate.execute(permit, lambda *v: receipts.append(v)).allowed)
        permit = gate.prepare(gate.select('a', 'read_file'), {})
        gate.refresh('b', [tool()], 'b1')
        self.assertFalse(gate.execute(permit, lambda *v: receipts.append(v)).allowed)
        self.assertEqual(len(receipts), 1)

    def setUp(self):
        self.gate = BindingGate()
        self.receipts = []
        self.gate.refresh("trusted", [tool()], "pipe-1")

    def writer(self, server, conn, request, descriptor):
        receipt = (server, conn, json.loads(request), json.loads(descriptor))
        self.receipts.append(receipt)
        return receipt

    def permit(self):
        return self.gate.prepare(self.gate.select("trusted", "read_file"),
                                 {"path": "fixture"})

    def test_copy_freezes_arguments_and_descriptor(self):
        data = tool()
        self.gate.refresh("trusted", [data], "pipe-1")
        selected = self.gate.select("trusted", "read_file")
        args = {"path": "original"}
        token = self.gate.prepare(selected, args)
        args["path"] = "modified"
        data["description"] = "modified"
        self.assertTrue(self.gate.execute(token, self.writer).allowed)
        self.assertEqual(self.receipts[0][2]["params"]["arguments"]["path"], "original")
        self.assertEqual(self.receipts[0][3]["description"], "Read a fixture.")

    def test_full_metadata_change_invalidates(self):
        token = self.permit()
        self.gate.refresh("trusted", [tool(title="New title")], "pipe-1")
        self.assertFalse(self.gate.execute(token, self.writer).allowed)
        self.assertEqual(self.receipts, [])

    def test_irrelevant_churn_and_key_order_preserve(self):
        token = self.permit()
        self.gate.refresh("other", [tool()], "other-pipe")
        self.gate.refresh("trusted", [dict(reversed(list(tool().items())))], "pipe-1")
        self.assertTrue(self.gate.execute(token, self.writer).allowed)

    def test_remove_readd_invalidates_even_identical(self):
        token = self.permit()
        self.gate.refresh("trusted", [], "pipe-1")
        self.gate.refresh("trusted", [tool()], "pipe-1")
        self.assertFalse(self.gate.execute(token, self.writer).allowed)

    def test_connection_rebinding_invalidates(self):
        token = self.permit()
        self.gate.refresh("trusted", [tool()], "pipe-2")
        self.assertFalse(self.gate.execute(token, self.writer).allowed)

    def test_same_name_other_server_is_distinct(self):
        self.gate.refresh("other", [tool()], "other-pipe")
        self.assertTrue(self.gate.execute(self.permit(), self.writer).allowed)
        self.assertEqual(self.receipts[0][0:2], ("trusted", "pipe-1"))

    def test_one_use(self):
        token = self.permit()
        self.assertTrue(self.gate.execute(token, self.writer).allowed)
        self.assertFalse(self.gate.execute(token, self.writer).allowed)
        self.assertEqual(len(self.receipts), 1)

    def test_out_of_order_refresh_and_duplicate_completion(self):
        r1 = self.gate.begin_refresh("trusted")
        r2 = self.gate.begin_refresh("trusted")
        self.assertTrue(self.gate.complete_refresh("trusted", r2, [tool(title="new")],
                                                    "pipe-1").accepted)
        self.assertFalse(self.gate.complete_refresh("trusted", r1, [tool()],
                                                     "pipe-1").accepted)
        self.assertFalse(self.gate.complete_refresh("trusted", r2, [tool()],
                                                     "pipe-1").accepted)
        self.assertEqual(json.loads(self.gate.select("trusted", "read_file").descriptor)["title"],
                         "new")

    def test_bad_catalog_does_not_partially_publish(self):
        token = self.permit()
        result = self.gate.refresh("trusted", [tool("first"), {"name": "invalid"}])
        self.assertFalse(result.accepted)
        self.assertIsNone(self.gate.select("trusted", "first"))
        self.assertIsNone(self.gate.select("trusted", "read_file"))
        self.assertFalse(self.gate.execute(token, self.writer).allowed)

    def test_unknown_and_forged_tokens_deny(self):
        self.assertIsNone(self.gate.select("trusted", "unknown"))
        self.assertFalse(self.gate.execute("unissued-token", self.writer).allowed)

    def test_transport_error_is_not_reported_as_prevented(self):
        def failed(*args):
            raise OSError("fixture transport error")
        result = self.gate.execute(self.permit(), failed)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "transport outcome unknown")

    def test_strict_json_limits_and_shapes(self):
        for schema in (None, [], "object", 4):
            with self.subTest(schema=schema), self.assertRaises(InvalidDefinition):
                descriptor_bytes({"name": "x", "inputSchema": schema})
        bad = tool()
        bad["cycle"] = bad
        with self.assertRaises(InvalidDefinition):
            descriptor_bytes(bad)

    def test_policy_exception_is_fail_closed(self):
        def broken(_):
            raise ValueError("policy error")
        gate = BindingGate(admit=broken)
        self.assertFalse(gate.refresh("s", [tool()]).accepted)
        self.assertIsNone(gate.select("s", "read_file"))


if __name__ == "__main__":
    unittest.main()
