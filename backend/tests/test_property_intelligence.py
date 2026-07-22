import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market_intelligence import MarketIntelligenceFilters, MarketIntelligenceService


class PropertyIntelligenceSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.service = MarketIntelligenceService()
        self.lead = {
            "id": "lead-property-test",
            "name": "Forge Holdings LLC",
            "address": "1234 Forge St",
            "parcelNumber": "000123456789",
            "county": "Dallas",
            "lotSize": "1.2 acres",
            "stage": "Hot Lead",
            "email": "seller@example.com",
            "assignmentFee": "17500",
        }
        self.parcel = {
            "leadId": "lead-property-test",
            "address": "1234 Forge St",
            "apn": "000123456789",
            "county": "Dallas",
            "acreage": "1.2",
            "zoning": "Residential",
            "utilityAvailability": "Street utilities nearby",
            "floodZone": "No",
            "taxDelinquencyStatus": "Needs Review",
        }

    def test_property_snapshot_starts_from_address_and_subject_property(self):
        snapshot = self.service.build_property_snapshot(
            self.lead,
            self.parcel,
            filters=MarketIntelligenceFilters(radius_miles=25),
            provider_name="mock",
        )

        self.assertEqual(snapshot["engine"], "LEGACY Property Intelligence")
        self.assertEqual(snapshot["version"], "property-intelligence-workspace-v1")
        self.assertEqual(snapshot["addressTrigger"], "1234 Forge St")
        self.assertEqual(snapshot["subjectProperty"]["apn"], "000123456789")
        self.assertEqual(snapshot["subjectProperty"]["county"], "Dallas")
        self.assertIn("coordinates", snapshot["subjectProperty"])

    def test_property_snapshot_includes_parcel_outline_and_map_contract(self):
        snapshot = self.service.build_property_snapshot(
            self.lead,
            self.parcel,
            filters=MarketIntelligenceFilters(radius_miles=10),
            provider_name="mock",
        )
        subject_parcel = snapshot["marketIntelligence"]["map"]["subjectParcel"]

        self.assertEqual(subject_parcel["boundaryType"], "estimated")
        self.assertEqual(len(subject_parcel["boundary"]), 4)
        self.assertEqual(snapshot["marketIntelligence"]["map"]["subjectMarker"]["color"], "gold")
        self.assertTrue(snapshot["transactions"])

    def test_property_snapshot_explains_narrative_and_buyers(self):
        snapshot = self.service.build_property_snapshot(
            self.lead,
            self.parcel,
            filters=MarketIntelligenceFilters(radius_miles=25),
            provider_name="mock",
        )
        narrative = snapshot["marketIntelligence"]["narrative"]
        buyers = snapshot["marketIntelligence"]["mostProbableBuyers"]

        self.assertGreaterEqual(len(narrative), 4)
        self.assertTrue(all(item.get("sentence") and item.get("evidence") is not None for item in narrative))
        self.assertGreater(len(buyers), 0)
        self.assertTrue(all("score" in buyer and "reasons" in buyer for buyer in buyers))

    def test_contact_intelligence_is_provider_ready_without_fake_private_data(self):
        snapshot = self.service.build_property_snapshot(self.lead, self.parcel, provider_name="mock")
        contact = snapshot["contactIntelligence"]

        self.assertEqual(contact["status"], "public-data-ready")
        self.assertEqual(contact["email"], "seller@example.com")
        self.assertIn("Licensed skip trace", contact["futureProviders"])
        self.assertEqual(contact["businessPhone"], "")


if __name__ == "__main__":
    unittest.main()