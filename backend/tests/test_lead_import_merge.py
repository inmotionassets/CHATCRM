import unittest

from app.routers.imports import ParsedLead, merge_csv_leads, normalize_import_address
from app.routers.leads import Lead


class LeadImportMergeTests(unittest.TestCase):
    def parsed(self, **overrides):
        values = {
            "name": "New Owner",
            "address": "100 Main Street Dallas TX 75201",
            "parcelNumber": "00-123-400",
            "county": "Dallas",
            "phones": ["(214) 555-1212"],
            "phone": "(214) 555-1212",
            "email": "owner@example.com",
            "source": "source.csv",
            "confidence": 95,
            "notes": "",
            "lotSize": "5000",
            "assessedValue": "45000",
        }
        values.update(overrides)
        return ParsedLead(**values)

    def test_normalized_address_ignores_zip_state_and_street_spelling(self):
        self.assertEqual(
            normalize_import_address("100 Main Street, Dallas, Texas 75201"),
            normalize_import_address("100 MAIN ST DALLAS TX"),
        )

    def test_merge_preserves_workflow_and_adds_missing_contact_data(self):
        existing = Lead(
            id="lead-1",
            name="Existing Owner",
            address="100 Main St Dallas TX",
            parcelNumber="00123400",
            notes="Seller called back",
            stage="Follow Up",
            contactStatus="follow-up",
            phones=["972-555-0101"],
            phone="972-555-0101",
        )
        changed, added, updated, duplicates = merge_csv_leads([existing], [self.parsed()], "source.csv")
        self.assertEqual((added, updated, duplicates), (0, 1, 1))
        self.assertEqual(len(changed), 1)
        saved = changed[0]
        self.assertEqual(saved.id, existing.id)
        self.assertEqual(saved.notes, "Seller called back")
        self.assertEqual(saved.stage, "Follow Up")
        self.assertEqual(saved.contactStatus, "follow-up")
        self.assertEqual(len(saved.phones), 2)
        self.assertEqual(saved.lotSize, "5000")
        self.assertEqual(saved.assessedValue, "45000")

    def test_duplicate_rows_create_one_new_lead_and_union_phones(self):
        first = self.parsed()
        second = self.parsed(phone="469-555-1212", phones=["469-555-1212"])
        changed, added, updated, duplicates = merge_csv_leads([], [first, second], "source.csv")
        self.assertEqual((added, updated, duplicates), (1, 0, 1))
        self.assertEqual(len(changed), 1)
        self.assertEqual(len(changed[0].phones), 2)
        self.assertEqual(changed[0].parcelNumber, "00-123-400")


if __name__ == "__main__":
    unittest.main()
