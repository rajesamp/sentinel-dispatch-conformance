import unittest
from experiments.enumerate_traces import generate, ALPHABET


class EnumerationTests(unittest.TestCase):
    def test_declared_universe_and_unique_words(self):
        data = generate()
        self.assertEqual(len(data["cases"]), 259)
        self.assertEqual(len({c["id"] for c in data["cases"]}), 259)
        for n in range(4):
            self.assertEqual(sum(len(c["operations"]) == n for c in data["cases"]), len(ALPHABET)**n)

    def test_aba_revokes_but_unrelated_and_argument_changes_preserve(self):
        cases = {c["id"]: c for c in generate()["cases"]}
        self.assertEqual(cases["enum-publish_changed__publish_original"]["expected_policy"], "deny")
        self.assertEqual(cases["enum-withdraw__publish_original"]["expected_policy"], "deny")
        safe = cases["enum-unrelated_server__mutate_arguments__publish_original"]
        self.assertEqual(safe["expected_policy"], "allow")
        self.assertEqual(safe["expected_receipt"]["request"]["params"]["arguments"], {"path": "fixture.txt"})

    def test_no_reference_alias_between_cases(self):
        data = generate()
        data["cases"][0]["initial_catalogs"][0]["tools"][0]["name"] = "changed"
        self.assertEqual(data["cases"][1]["initial_catalogs"][0]["tools"][0]["name"], "read_file")


if __name__ == "__main__":
    unittest.main()
