"""Check measured source-contract examples and their benign counter-controls."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from experiments import upstream_counterexamples as upstream


class TestUpstreamCounterexamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = upstream.run_counterexamples()
        cls.records = {item["case_id"]: item for item in cls.report["records"]}

    def test_pinned_provenance_and_json_roundtrip(self) -> None:
        report = json.loads(json.dumps(self.report))
        self.assertEqual(report["provenance"]["commit"], upstream.COMMIT)
        for filename, blob in upstream.EXPECTED_BLOBS.items():
            self.assertEqual(report["provenance"]["source_files"][filename]["git_blob_sha1"], blob)

    def test_malformed_schemas_are_observed_as_admitted(self) -> None:
        for label in ("null", "string", "number", "list", "missing"):
            with self.subTest(schema=label):
                record = self.records["malformed_schema_" + label]
                self.assertEqual(record["support_class"], "direct_claim")
                self.assertTrue(record["observed"]["scan_allowed"])
                self.assertTrue(record["observed"]["registration_allowed"])
                self.assertTrue(record["observed"]["invocation_allowed"])

    def test_denied_replacement_does_not_allow_current_poisoned_descriptor(self) -> None:
        observed = self.records["denied_reregistration_retains_old_snapshot"]["observed"]
        self.assertFalse(observed["replacement_allowed"])
        self.assertTrue(observed["old_entry_retained"])
        self.assertTrue(observed["old_snapshot_allowed"])
        self.assertFalse(observed["current_poisoned_snapshot_allowed"])
        self.assertTrue(observed["quarantined_after_current_check"])

    def test_projection_cases_are_explicit_scope_extensions(self) -> None:
        for label in ("title", "annotations_title", "output_schema_description"):
            with self.subTest(field=label):
                record = self.records["omitted_field_" + label]
                self.assertEqual(record["support_class"], "scope_extension")
                self.assertTrue(record["observed"]["fingerprint_unchanged"])
                self.assertTrue(record["observed"]["changed_scan_allowed"])
                self.assertTrue(record["observed"]["changed_invocation_allowed"])

    def test_controlled_interleaving_admits_content_that_fresh_scan_denies(self) -> None:
        record = self.records["registration_scan_fingerprint_interleaving"]
        observed = record["observed"]
        self.assertEqual(record["support_class"], "host_precondition")
        self.assertTrue(observed["registration_allowed"])
        self.assertTrue(observed["catalogue_was_mutated"])
        self.assertFalse(observed["fresh_scan_of_current_allowed"])
        self.assertTrue(observed["current_invocation_allowed"])

    def test_copy_before_registration_prevents_shared_reference_race(self) -> None:
        observed = self.records["registration_race_copied_snapshot"]["observed"]
        self.assertTrue(observed["registration_allowed"])
        self.assertTrue(observed["catalogue_was_mutated"])
        self.assertFalse(observed["fresh_scan_of_current_allowed"])
        self.assertFalse(observed["current_invocation_allowed"])

    def test_shared_registry_collision_and_per_server_adapter_control(self) -> None:
        collision = self.records["shared_registry_same_name_collision"]["observed"]
        self.assertTrue(collision["b_before_a_check_allowed"])
        self.assertFalse(collision["a_after_overwrite_allowed"])
        self.assertFalse(collision["b_after_a_check_allowed"])
        adapter = self.records["per_server_copied_snapshot_adapter"]["observed"]
        self.assertTrue(adapter["A_invocation_allowed"])
        self.assertTrue(adapter["B_invocation_allowed"])

    def test_benign_allowed_known_poison_and_unknown_denied(self) -> None:
        self.assertTrue(self.records["benign_registration_and_call"]["observed"]["invocation_allowed"])
        self.assertFalse(self.records["known_poisoning_pattern_denied"]["observed"]["registration_allowed"])
        self.assertFalse(self.records["known_poisoning_pattern_denied"]["observed"]["invocation_allowed"])
        self.assertFalse(self.records["unknown_tool_denied"]["observed"]["invocation_allowed"])

    def test_clean_refresh_is_intended_recovery(self) -> None:
        record = self.records["covered_mutation_denied_then_clean_refresh_recovers"]
        observed = record["observed"]
        self.assertEqual(record["role"], "positive_control")
        self.assertFalse(observed["mutated_invocation_allowed"])
        self.assertTrue(observed["quarantined_after_mutation"])
        self.assertTrue(observed["clean_refresh_allowed"])
        self.assertFalse(observed["quarantined_after_clean_refresh"])
        self.assertTrue(observed["clean_invocation_allowed_after_refresh"])

    def test_poisoned_refresh_keeps_quarantine(self) -> None:
        observed = self.records["poisoned_refresh_keeps_quarantine"]["observed"]
        self.assertFalse(observed["refresh_allowed"])
        self.assertTrue(observed["still_quarantined"])
        self.assertFalse(observed["invocation_allowed"])

    def test_export_expectations_match_without_claiming_attack_recall(self) -> None:
        self.assertTrue(self.report["all_expected_observations"])
        self.assertTrue(self.report["records_are_not_independent_attack_families"])
        for record in self.report["records"]:
            with self.subTest(case=record["case_id"]):
                self.assertTrue(record["matches_expected"])
                self.assertEqual(set(record["observed"]), set(record["expected"]))
                self.assertTrue(all(type(value) is bool for value in record["observed"].values()))
                self.assertIn(record["support_class"], {"direct_claim", "scope_extension", "host_precondition"})


if __name__ == "__main__":
    unittest.main()
