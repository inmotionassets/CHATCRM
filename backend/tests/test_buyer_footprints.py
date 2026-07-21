import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.buyer_footprints import (
    alias_confidence,
    build_buyer_footprints,
    build_deal_intelligence_summary,
    normalize_entity_name,
)
from app.market_intelligence import MarketIntelligenceFilters, MarketIntelligenceService
from app.disposition_providers import normalize_provider_transaction, prepare_persisted_transaction_for_subject


SUBJECT = {
    "leadId": "lead-footprint",
    "address": "1234 Forge St, Dallas, TX",
    "coordinates": {"lat": 32.7767, "lng": -96.7970},
    "acreage": 1.0,
    "propertyType": "Vacant Land",
    "targetAssignmentPrice": 65000,
}


def transaction(**overrides):
    base = {
        "id": "tx-1",
        "address": "1300 Forge Street, Dallas, TX 75201",
        "apn": "000001",
        "saleDate": "2026-06-20",
        "salePrice": 72000,
        "acreage": 1.2,
        "pricePerAcre": 60000,
        "propertyType": "Vacant Land",
        "cashSale": True,
        "buyerName": "ABC Builders LLC",
        "buyerMailingAddress": "100 Main St, Dallas, TX 75201",
        "buyerType": "builder",
        "coordinates": {"lat": 32.778, "lng": -96.796},
        "distanceMiles": 0.2,
        "confidence": 92,
        "dataQuality": "verified",
        "verified": True,
    }
    base.update(overrides)
    return base


class BuyerFootprintTests(unittest.TestCase):
    def test_entity_name_normalization_groups_llc_variations(self):
        self.assertEqual(normalize_entity_name("ABC Builders LLC"), "abc builders")
        self.assertEqual(normalize_entity_name("A.B.C. Builders, L.L.C."), "abc builders")
        self.assertEqual(normalize_entity_name("ABC BUILDERS"), "abc builders")

    def test_alias_confidence_blocks_false_positive_merges(self):
        strong = alias_confidence("A.B.C. Builders, L.L.C.", "ABC Builders LLC")
        weak = alias_confidence("ABC Capital LLC", "ABC Builders LLC")

        self.assertGreaterEqual(strong["confidence"], 90)
        self.assertLess(weak["confidence"], 90)
        self.assertIn("not merged", weak["reason"].lower())

    def test_same_street_radius_and_corridor_evidence(self):
        transactions = [
            transaction(id="tx-1", address="1300 Forge Street, Dallas, TX", distanceMiles=0.2),
            transaction(id="tx-2", address="1420 Forge St, Dallas, TX", distanceMiles=0.7, saleDate="2026-05-15"),
            transaction(id="tx-3", address="1500 Forge St, Dallas, TX", distanceMiles=0.9, saleDate="2026-04-10"),
        ]

        footprints = build_buyer_footprints(transactions, SUBJECT)
        footprint = footprints["abc builders"]

        self.assertEqual(footprint["purchasesByRadius"]["1"], 3)
        self.assertTrue(any(signal["label"] == "Same-street buyer" for signal in footprint["streetLevelSignals"]))
        self.assertTrue(any("corridor" in signal["label"].lower() for signal in footprint["corridorSignals"]))
        self.assertIn("Possible land assembler", footprint["intentSignals"])

    def test_market_snapshot_includes_footprints_and_deal_summary(self):
        lead = {
            "id": "lead-test",
            "address": "1234 Forge St",
            "parcelNumber": "000001",
            "county": "Dallas",
            "lotSize": "1 acres",
            "stage": "Under Contract",
        }
        service = MarketIntelligenceService()
        workspace = service.build_snapshot(lead, filters=MarketIntelligenceFilters(radius_miles=25), provider_name="mock")

        self.assertIn("buyerFootprints", workspace)
        self.assertIn("dealIntelligenceSummary", workspace)
        self.assertIn("marketIntelligence", workspace)
        self.assertTrue(workspace["buyerFootprints"])

    def test_csv_provider_transactions_feed_footprint_engine(self):
        provider_transaction = normalize_provider_transaction(
            {
                "source_record_id": "CSV-001",
                "apn": "00000481291000000",
                "address": "1300 Forge Street, Dallas, TX 75201",
                "latitude": "32.778",
                "longitude": "-96.796",
                "sale_date": "2026-06-20",
                "sale_price": "72000",
                "acreage": "1.2",
                "buyer_name": "A.B.C. Builders, L.L.C.",
                "property_type": "Vacant Land",
                "financing_type": "Cash",
            },
            provider="csv",
            source_name="Dallas County CSV Import",
        )
        prepared = prepare_persisted_transaction_for_subject(provider_transaction, SUBJECT)
        footprints = build_buyer_footprints([prepared], SUBJECT)

        self.assertIn("abc builders", footprints)
        self.assertEqual(footprints["abc builders"]["verifiedPurchaseCount"], 1)

    def test_deal_summary_identifies_strongest_match(self):
        footprints = build_buyer_footprints([transaction()], SUBJECT)
        summary = build_deal_intelligence_summary(
            footprints,
            [{"buyerName": "ABC Builders LLC", "score": 91}],
            [transaction()],
        )

        strongest = next(item for item in summary if item["label"] == "Strongest buyer match")
        self.assertEqual(strongest["value"], "91%")


if __name__ == "__main__":
    unittest.main()