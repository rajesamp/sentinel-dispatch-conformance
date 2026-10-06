from copy import deepcopy
import json
from pathlib import Path
import unittest

from experiments.oracle import check_receipt, equal_json, evaluate_receipts
from experiments.scenarios import apply_mutation, generate_cases, manifest


class ScenarioContractTests(unittest.TestCase):
    def test_unique_structural_ids_and_fresh_fixtures(self):
        cases = generate_cases()
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        self.assertTrue(20 <= len(cases) <= 40)
        cases[0]["initial_catalogs"][0]["tools"][0]["description"] = "changed"
        self.assertEqual(generate_cases()[0]["initial_catalogs"][0]["tools"][0]["description"], "Read fixture.")

    def test_partition_composition_labels_disjoint(self):
        cases = generate_cases()
        development = {c["family"] for c in cases if c["split"] == "development"}
        verification = {c["family"] for c in cases if c["split"] == "verification"}
        self.assertFalse(development & verification)
        self.assertTrue(any(c["kind"] == "benign" for c in cases if c["split"] == "verification"))

    def test_explicit_revocation_and_schema(self):
        valid_actions = {"refresh", "begin_refresh", "complete_refresh", "mutate_args",
                         "mutate_source", "reapprove", "execute_again"}
        for case in generate_cases():
            self.assertIn(case["expected_policy"], {"allow", "deny", "allow_once"})
            for op in case["operations"]:
                self.assertIn(op["action"], valid_actions)
                self.assertIn(op["at"], {"after_select", "after_prepare", "after_execute"})
                self.assertIs(type(op["revokes_approval"]), bool)
            if case["expected_policy"] == "deny":
                self.assertTrue(any(op["revokes_approval"] for op in case["operations"]))
            else:
                self.assertIsNotNone(case["expected_receipt"])

    def test_saved_manifest_matches_generator(self):
        path = Path(__file__).parents[1] / "data" / "scenario_manifest.json"
        self.assertEqual(json.loads(path.read_text()), manifest())

    def test_mutation_reaches_nested_caller_value(self):
        value = {"nested": ["before"]}
        apply_mutation(value, ["nested", 0], "after")
        self.assertEqual(value, {"nested": ["after"]})


class IndependentOracleTests(unittest.TestCase):
    def setUp(self):
        self.approval = generate_cases()[0]["expected_receipt"]
        self.receipt = deepcopy(self.approval)

    def test_correct_bytes_and_object_key_order(self):
        self.receipt["request"] = json.dumps(self.receipt["request"]).encode()
        self.assertEqual(check_receipt(self.approval, self.receipt), [])

    def test_identity_argument_and_descriptor_negative_controls(self):
        for field, issue in [("server", "server_mismatch"), ("connection", "connection_mismatch")]:
            bad = deepcopy(self.receipt)
            bad[field] = "wrong"
            self.assertIn(issue, check_receipt(self.approval, bad))
        bad = deepcopy(self.receipt)
        bad["request"]["params"]["arguments"]["path"] = "wrong.txt"
        self.assertIn("request_mismatch", check_receipt(self.approval, bad))
        bad = deepcopy(self.receipt)
        bad["descriptor"]["title"] = "Unapproved title"
        self.assertIn("descriptor_mismatch", check_receipt(self.approval, bad))

    def test_explicit_revocation_does_not_depend_on_content_change(self):
        self.assertIn("dispatch_after_relevant_revocation",
                      check_receipt(self.approval, self.receipt, revoked=True))

    def test_post_enqueue_revocation_not_retroactive(self):
        self.receipt["revoked_at_dispatch"] = False
        result = evaluate_receipts(self.approval, [self.receipt], revoked=True, expected_policy="allow")
        self.assertTrue(result["safe"])

    def test_gate_status_cannot_conceal_receipt_violation(self):
        self.receipt["server"] = "wrong"
        self.receipt["gate_allowed"] = False
        self.assertFalse(evaluate_receipts(self.approval, [self.receipt])["safe"])

    def test_no_dispatch_is_safe_but_not_benign_completion(self):
        result = evaluate_receipts(self.approval, [], expected_policy="allow")
        self.assertTrue(result["safe"])
        self.assertFalse(result["policy_satisfied"])

    def test_replay_and_missing_approval_negative_controls(self):
        self.assertFalse(evaluate_receipts(self.approval, [self.receipt, self.receipt])["safe"])
        self.assertEqual(check_receipt(None, self.receipt), ["dispatch_without_approval"])

    def test_typed_json_and_duplicate_key_rejection(self):
        self.assertFalse(equal_json(True, 1))
        self.assertFalse(equal_json(1, 1.0))
        self.receipt["request"] = b'{"id": 1, "id": 2}'
        self.assertIn("invalid_request_receipt", check_receipt(self.approval, self.receipt))


if __name__ == "__main__":
    unittest.main()
