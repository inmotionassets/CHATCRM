import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import disposition_providers as providers
from app.routers import leads as lead_store


SAMPLE_CSV = """source_record_id,parcel_id,address,latitude,longitude,sale_date,sale_price,acreage,deed_type,financing_type,buyer_name,seller_name,buyer_mailing_address,property_type,zoning,confidence
DCAD-001,00000481291000000,"1214 Cedar Crest Blvd, Dallas, TX",32.7832,-96.7891,2026-06-24,72000,1.25,Warranty Deed,Cash,DFW Land Partners LLC,Sample Seller,"325 N Saint Paul St, Dallas, TX",Vacant Land,R-7.5,92
DCAD-002,00000783114000000,"1881 Oak Gate Ln, Dallas, TX",32.7954,-96.8062,2026-05-18,81000,1.70,Warranty Deed,Conventional,Lone Star Custom Homes LLC,Sample Seller,"4301 Alpha Rd, Dallas, TX",Residential Lot,R-10,88
"""


class DispositionProviderTests(unittest.TestCase):
    def setUp(self):
        self.old_database_path = lead_store.DATABASE_PATH
        self.old_use_postgres = lead_store.USE_POSTGRES
        self.temp_dir = tempfile.TemporaryDirectory()
        lead_store.DATABASE_PATH = Path(self.temp_dir.name) / "chatcrm-test.db"
        lead_store.USE_POSTGRES = False

    def tearDown(self):
        lead_store.DATABASE_PATH = self.old_database_path
        lead_store.USE_POSTGRES = self.old_use_postgres
        self.temp_dir.cleanup()

    def test_csv_row_normalizes_into_standard_transaction_schema(self):
        transaction = providers.normalize_provider_transaction(
            {
                "Record ID": "DCAD-003",
                "APN": "00000319045000000",
                "Property Address": "901 Prairie Bend Rd, Dallas, TX",
                "Sale Date": "04/26/2026",
                "Sale Price": "$54,500",
                "Acres": "0.95",
                "Buyer": "Texas Dirt Investments LLC",
                "Cash Sale": "yes",
            },
            provider="csv",
            source_name="Dallas County CSV Import",
        )

        self.assertEqual(transaction["source"], "csv")
        self.assertEqual(transaction["sourceRecordId"], "DCAD-003")
        self.assertEqual(transaction["saleDate"], "2026-04-26")
        self.assertEqual(transaction["salePrice"], 54500)
        self.assertEqual(transaction["buyerType"], "investor")
        self.assertTrue(transaction["cashSale"])
        self.assertIn(transaction["dataQuality"], {"estimated", "verified"})

    def test_import_csv_persists_transactions_and_prevents_duplicates(self):
        first_result = providers.import_csv_transactions(SAMPLE_CSV, source_name="Dallas County CSV Import")
        second_result = providers.import_csv_transactions(SAMPLE_CSV, source_name="Dallas County CSV Import")

        self.assertEqual(first_result["importedCount"], 2)
        self.assertEqual(second_result["updatedCount"], 2)

        with providers.get_connection() as connection:
            providers.ensure_disposition_tables(connection)
            count = connection.execute("SELECT COUNT(*) AS total FROM disposition_transactions").fetchone()["total"]
            buyers = connection.execute("SELECT COUNT(*) AS total FROM buyer_entities").fetchone()["total"]

        self.assertEqual(count, 2)
        self.assertEqual(buyers, 2)

    def test_missing_coordinates_are_estimated_and_marked_for_review(self):
        transaction = providers.normalize_provider_transaction(
            {
                "source_record_id": "NO-COORDS",
                "apn": "00000999999000000",
                "address": "500 Missing Point Dr, Dallas, TX",
                "sale_date": "2026-03-01",
                "sale_price": "69000",
                "acreage": "1.4",
                "buyer_name": "Metro Infill Builders LLC",
            },
            provider="csv",
            source_name="Dallas County CSV Import",
        )
        prepared = providers.prepare_persisted_transaction_for_subject(
            transaction,
            {"coordinates": {"lat": 32.7767, "lng": -96.7970}},
        )

        self.assertEqual(prepared["dataQuality"], "estimated")
        self.assertTrue(prepared["estimated"])
        self.assertGreater(prepared["distanceMiles"], 0)


if __name__ == "__main__":
    unittest.main()