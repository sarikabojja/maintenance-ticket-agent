import unittest
from backend.triage import analyze_ticket

class TriageTests(unittest.TestCase):
    def test_known_tickets(self):
        cases = [
            ("Inverter 4 tripping repeatedly after noon, high temperature alarm visible", "inverter_thermal", "high"),
            ("Gearbox vibration has increased for turbine WTG-12 with abnormal noise", "gearbox_vibration", "critical"),
            ("Inspection checklist pending for spillway gate maintenance", "inspection_compliance", "medium"),
            ("SCADA data missing for block 3 for last two hours", "data_gap", "medium"),
            ("Blade pitch error after high wind gust event", "pitch_system", "high"),
            ("Curtailment instruction not reflected in generation dashboard", "grid_curtailment", "medium"),
        ]
        for text, category, severity in cases:
            with self.subTest(text=text):
                result = analyze_ticket(text)
                self.assertEqual(result["category"], category)
                self.assertEqual(result["severity"], severity)

    def test_unknown_ticket_requests_review(self):
        result = analyze_ticket("Unfamiliar hydraulic pressure fluctuation")
        self.assertEqual(result["category"], "needs_review")
        self.assertTrue(result["requires_human_review"])

if __name__ == "__main__":
    unittest.main()
