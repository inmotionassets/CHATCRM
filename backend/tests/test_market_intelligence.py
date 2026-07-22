import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market_intelligence import MarketIntelligenceFilters, MarketIntelligenceService


class MarketIntelligenceServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = MarketIntelligenceService()
        self.lead = {
            "id": "lead-market-test",
            "address": "1234 Forge St",
            "parcelNumber": "000001",
            "county": "Dallas",
            "lotSize": "1.2 acres",
            "stage": "Under Contract",
            "assignmentFee": "15000",
            "notes": "title opened and taxes verified",
        }

    def test_snapshot_returns_stable_market_intelligence_contract(self):
        snapshot = self.service.build_snapshot(
            self.lead,
            filters=MarketIntelligenceFilters(radius_miles=25),
            provider_name="mock",
        )

        self.assertEqual(snapshot["marketIntelligence"]["engine"], "Market Intelligence Engine")
        self.assertIn("Transaction Engine", snapshot["marketIntelligence"]["modules"])
        self.assertIn("Buyer Intelligence", snapshot["marketIntelligence"]["modules"])
        self.assertIn("Opportunity Scoring", snapshot["marketIntelligence"]["modules"])
        self.assertIn("Market Intelligence Map", snapshot["marketIntelligence"]["modules"])
        self.assertIn("buyerFootprints", snapshot)
        self.assertIn("dealIntelligenceSummary", snapshot)
        self.assertGreater(len(snapshot["buyerMatches"]), 0)

    def test_opportunity_score_is_explainable(self):
        snapshot = self.service.build_snapshot(
            self.lead,
            filters=MarketIntelligenceFilters(radius_miles=25),
            provider_name="mock",
        )
        opportunity = snapshot["marketIntelligence"]["opportunityScore"]

        self.assertGreaterEqual(opportunity["score"], 0)
        self.assertLessEqual(opportunity["score"], 100)
        self.assertTrue(opportunity["grade"])
        self.assertGreaterEqual(len(opportunity["reasons"]), 5)
        self.assertTrue(all("label" in reason and "points" in reason and "detail" in reason for reason in opportunity["reasons"]))

    def test_map_snapshot_has_marker_rules_layers_and_timeline(self):
        snapshot = self.service.build_snapshot(
            self.lead,
            filters=MarketIntelligenceFilters(radius_miles=25, sold_within_days=180),
            provider_name="mock",
        )
        map_snapshot = snapshot["marketIntelligence"]["map"]
        marker_types = {item["type"] for item in map_snapshot["markerLegend"]}
        transaction_marker_types = {item["marketMarkerType"] for item in snapshot["transactions"]}

        self.assertEqual(map_snapshot["subjectMarker"]["type"], "subject_property")
        self.assertEqual(map_snapshot["timeline"]["selectedDays"], 180)
        self.assertIn("builder_purchase", marker_types)
        self.assertIn("repeat_buyer", marker_types)
        self.assertIn("unknown_estimated", marker_types)
        self.assertTrue(transaction_marker_types & {"cash_purchase", "builder_purchase", "repeat_buyer", "recorded_sale"})
        self.assertTrue(map_snapshot["futureLayers"])
        self.assertTrue(all(not item["available"] for item in map_snapshot["futureLayers"]))

    def test_buyer_highlight_summaries_are_ready_for_map_mode(self):
        snapshot = self.service.build_snapshot(
            self.lead,
            filters=MarketIntelligenceFilters(radius_miles=25),
            provider_name="mock",
        )
        highlights = snapshot["marketIntelligence"]["map"]["buyerHighlights"]
        first_highlight = next(iter(highlights.values()))

        self.assertIn("verifiedPurchases", first_highlight)
        self.assertIn("purchasesWithin", first_highlight)
        self.assertIn("1", first_highlight["purchasesWithin"])
        self.assertIn("3", first_highlight["purchasesWithin"])
        self.assertIn("10", first_highlight["purchasesWithin"])
        self.assertIn("buyingTrend", first_highlight)

    def test_empty_csv_provider_falls_back_without_breaking_snapshot(self):
        snapshot = self.service.build_snapshot(
            self.lead,
            filters=MarketIntelligenceFilters(radius_miles=5),
            provider_name="county",
        )

        self.assertEqual(snapshot["source"]["provider"], "county")
        self.assertTrue(snapshot["source"]["errors"])
        self.assertGreater(len(snapshot["transactions"]), 0)
        self.assertIn("mock fallback", snapshot["source"]["sourceName"])


if __name__ == "__main__":
    unittest.main()