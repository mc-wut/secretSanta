import unittest
import copy
from secretSanta import (
    PERMANENT_EXCLUSIONS,
    build_exclusions,
    assign,
    validate_exclusions
)

# ---------------------
# TEST FIXTURES
# ---------------------

PARTICIPANTS = {
    "matt": {},
    "stacy": {},
    "ruthie": {},
    "bob": {},
    "eddie": {},
    "maggie": {},
    "tom": {}
}

BASE_DATA = {
    "participants": PARTICIPANTS,
    "history": {
        "2021": {
            "matt": "stacy",
            "stacy": "ruthie",
            "ruthie": "bob",
            "bob": "eddie",
            "eddie": "maggie",
            "maggie": "tom",
            "tom": "matt"
        },
        "2022": {
            "matt": "ruthie",
            "stacy": "bob",
            "ruthie": "eddie",
            "bob": "maggie",
            "eddie": "tom",
            "maggie": "matt",
            "tom": "stacy"
        },
        "2023": {
            "matt": "bob",
            "stacy": "eddie",
            "ruthie": "maggie",
            "bob": "tom",
            "eddie": "matt",
            "maggie": "stacy",
            "tom": "ruthie"
        },
        "2024": {
            "matt": "eddie",
            "stacy": "maggie",
            "ruthie": "tom",
            "bob": "matt",
            "eddie": "stacy",
            "maggie": "ruthie",
            "tom": "bob"
        }
    },
    "assignments": {}
}

# ---------------------
# TESTS
# ---------------------

class TestSecretSanta(unittest.TestCase):

    def setUp(self):
        # deep copy so tests don't mutate shared state
        self.data = copy.deepcopy(BASE_DATA)
        self.ids, self.exclusions = build_exclusions(self.data)

    def test_everyone_gets_someone(self):
        assignments = assign(self.ids, self.exclusions)
        self.assertEqual(set(assignments.keys()), set(self.ids))

    def test_everyone_is_unique_receiver(self):
        assignments = assign(self.ids, self.exclusions)
        receivers = set(assignments.values())
        self.assertEqual(len(receivers), len(self.ids))

    def test_no_self_assignments(self):
        assignments = assign(self.ids, self.exclusions)
        for giver, receiver in assignments.items():
            self.assertNotEqual(giver, receiver)

    def test_respects_exclusion_window(self):
        assignments = assign(self.ids, self.exclusions)
        for giver, receiver in assignments.items():
            self.assertNotIn(receiver, self.exclusions[giver])

    def test_permanent_exclusion_example(self):
        # simulate spouses
        self.exclusions["matt"].add("stacy")
        self.exclusions["stacy"].add("matt")

        assignments = assign(self.ids, self.exclusions)
        self.assertNotEqual(assignments["matt"], "stacy")
        self.assertNotEqual(assignments["stacy"], "matt")

    def test_validate_exclusions_passes(self):
        # should not raise
        validate_exclusions(self.ids, self.exclusions)

    def test_validate_exclusions_fails_when_overconstrained(self):
        # matt can give to nobody
        self.exclusions["matt"] = set(self.ids)

        with self.assertRaises(RuntimeError):
            validate_exclusions(self.ids, self.exclusions)

    def test_multiple_runs_still_valid(self):
        # randomness should never break invariants
        for _ in range(50):
            assignments = assign(self.ids, self.exclusions)

            self.assertEqual(len(assignments), len(self.ids))
            self.assertEqual(len(set(assignments.values())), len(self.ids))

            for g, r in assignments.items():
                self.assertNotEqual(g, r)
                self.assertNotIn(r, self.exclusions[g])

    def test_forecast_next_3_years(self):
        data = copy.deepcopy(BASE_DATA)
        forecast_history = copy.deepcopy(data["history"])
        current_year = 2025
        forecast_years = 3

        print("\n--- Forecasting next 3 years of Secret Santa assignments ---")
        for offset in range(forecast_years):
            year = str(current_year + offset)

            # Build exclusions (rolling window)
            temp_data = {"participants": data["participants"], "history": forecast_history}
            ids, exclusions = build_exclusions(temp_data)

            # Add permanent exclusions
            for giver, banned in PERMANENT_EXCLUSIONS.items():
                exclusions[giver].update(banned)

            validate_exclusions(ids, exclusions)

            # Assign
            assignments = assign(ids, exclusions)
            forecast_history[year] = assignments

            # Print results
            print(f"\nYear {year}:")
            for giver in sorted(assignments.keys()):
                print(f"  {giver} -> {assignments[giver]}")

if __name__ == "__main__":
    unittest.main()
