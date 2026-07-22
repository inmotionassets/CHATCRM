import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.outcome_intelligence import (
    LEARNING_MANTRA,
    build_learning_summary,
    build_outcome_record,
    evaluate_recommendation,
)


class OutcomeIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.lead = {
            "id": "lead-learning-test",
            "address": "1234 Forge St",
            "parcelNumber": "000123456789",
            "county": "Dallas",
        }

    def test_recommendation_accuracy_supports_yes_partial_and_no(self):
        self.assertEqual(evaluate_recommendation("DFW Land Partners LLC", "DFW Land Partners", "closed"), "yes")
        self.assertEqual(evaluate_recommendation("DFW Land Partners LLC", "DFW Land Holdings LLC", "closed"), "partial")
        self.assertEqual(evaluate_recommendation("DFW Land Partners LLC", "Texas Dirt Investments", "closed"), "no")

    def test_outcome_record_captures_property_recommendation_actual_result_and_quality(self):
        record = build_outcome_record(
            "outcome-test-1",
            self.lead,
            {
                "recommendedBuyer": "DFW Land Partners LLC",
                "recommendedAction": "Pursue Immediately",
                "originalOpportunityScore": 94,
                "confidence": 92,
                "finalBuyer": "DFW Land Partners",
                "assignmentFee": "18000",
                "daysToClose": "9",
                "purchasePrice": "$62,000",
                "dispositionResult": "closed",
                "sellerOutcome": "seller_closed",
            },
            created_at="2026-07-22T12:00:00+00:00",
        )

        self.assertEqual(record["schemaVersion"], "outcome-intelligence-v1")
        self.assertEqual(record["property"]["address"], "1234 Forge St")
        self.assertEqual(record["recommendation"]["recommendedAction"], "Pursue Immediately")
        self.assertEqual(record["actualResult"]["assignmentFee"], 18000)
        self.assertEqual(record["intelligence"]["recommendationCorrect"], "yes")
        self.assertEqual(record["intelligence"]["assignmentPerformance"], "strong")
        self.assertEqual(record["dataQuality"][0]["level"], "verified")

    def test_learning_summary_measures_before_it_predicts(self):
        records = [
            build_outcome_record(
                "outcome-test-1",
                self.lead,
                {
                    "recommendedBuyer": "DFW Land Partners LLC",
                    "finalBuyer": "DFW Land Partners",
                    "assignmentFee": 18000,
                    "daysToClose": 9,
                    "dispositionResult": "closed",
                    "confidence": 92,
                },
            ),
            build_outcome_record(
                "outcome-test-2",
                self.lead,
                {
                    "recommendedBuyer": "ABC Builders LLC",
                    "finalBuyer": "Texas Dirt Investments",
                    "assignmentFee": 12000,
                    "daysToClose": 15,
                    "dispositionResult": "closed",
                    "confidence": 81,
                },
            ),
        ]

        summary = build_learning_summary(records)

        self.assertEqual(summary["mantra"], LEARNING_MANTRA)
        self.assertEqual(summary["totalOutcomes"], 2)
        self.assertEqual(summary["closedDeals"], 2)
        self.assertEqual(summary["correctRecommendations"], 1)
        self.assertEqual(summary["recommendationAccuracyRate"], 50)
        self.assertEqual(summary["averageDaysToClose"], 12)
        self.assertEqual(summary["averageAssignmentFee"], 15000)
        self.assertIn("Not active", summary["predictionStatus"])

    def test_data_quality_handles_messy_non_closed_outcomes(self):
        record = build_outcome_record(
            "outcome-test-3",
            self.lead,
            {
                "recommendedBuyer": "DFW Land Partners LLC",
                "dispositionResult": "contract_canceled",
                "sellerOutcome": "seller_backed_out",
                "priceChanged": "false",
                "contractReassigned": "true",
            },
        )

        flags = {item["label"] for item in record["dataQuality"]}
        self.assertEqual(record["intelligence"]["outcomeType"], "failed")
        self.assertIn("Contract was reassigned", flags)
        self.assertNotIn("Price changed during disposition", flags)


if __name__ == "__main__":
    unittest.main()
