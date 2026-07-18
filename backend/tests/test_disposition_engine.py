import unittest
import sys
from datetime import date
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.auth import User
from app.disposition_engine import build_disposition_workspace
from app.routers.disposition import require_disposition_access


class DispositionEngineTests(unittest.TestCase):
    def setUp(self):
        self.lead = {
            "id": "lead-test",
            "address": "901 Ten Mile Rd",
            "parcelNumber": "12059500000240000",
            "county": "Dallas",
            "lotSize": "1.2 acres",
            "stage": "Under Contract",
            "assignmentFee": "12500",
            "notes": "title opened, taxes verified",
        }

    def test_radius_filter_reduces_transaction_count(self):
        near = build_disposition_workspace(self.lead, radius_miles=1, today=date(2026, 7, 17))
        wide = build_disposition_workspace(self.lead, radius_miles=25, today=date(2026, 7, 17))

        self.assertLessEqual(len(near["transactions"]), len(wide["transactions"]))
        self.assertTrue(all(item["distanceMiles"] <= 1 for item in near["transactions"]))

    def test_repeated_buyer_is_grouped_and_scored(self):
        workspace = build_disposition_workspace(self.lead, radius_miles=25, today=date(2026, 7, 17))
        dfw_match = next(
            item for item in workspace["buyerMatches"] if item["buyerName"] == "DFW Land Partners LLC"
        )

        self.assertGreaterEqual(dfw_match["totalVerifiedPurchases"], 3)
        self.assertIn("repeatActivity", dfw_match["scoreBreakdown"])
        self.assertGreater(dfw_match["score"], 60)

    def test_acquisition_user_cannot_access_disposition_workspace(self):
        user = User(username="caller", name="Caller", role="Acquisition")

        with self.assertRaises(HTTPException) as error:
            require_disposition_access(user)

        self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
