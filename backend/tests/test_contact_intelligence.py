import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contact_intelligence import ContactIntelligenceService, normalize_phone


class ContactIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.lead = {
            "id": "lead-contact-test",
            "name": "Forge Holdings LLC",
            "address": "1234 Forge St Dallas TX",
            "county": "Dallas",
            "phone": "(214) 555-0199, 972-555-0111",
            "phones": ["214-555-0199"],
            "email": "owner@example.com",
        }

    def test_free_contact_intelligence_ranks_existing_numbers(self):
        snapshot = ContactIntelligenceService(provider_name="free_public").build_snapshot(self.lead, enrich=True)

        self.assertEqual(snapshot.leadId, "lead-contact-test")
        self.assertEqual(snapshot.bestContact.normalizedValue, "2145550199")
        self.assertEqual(snapshot.bestContact.source, "Imported lead data")
        self.assertTrue(snapshot.bestContact.isCallable)
        self.assertGreaterEqual(snapshot.confidence, 70)
        self.assertFalse(snapshot.needsPaidSkipTrace)

    def test_free_contact_intelligence_does_not_fake_private_phones(self):
        lead = {
            "id": "lead-no-phone",
            "name": "DFW Land Partners LLC",
            "address": "901 Ten Mile Rd Dallas TX",
            "county": "Dallas",
        }
        snapshot = ContactIntelligenceService(provider_name="free_public").build_snapshot(lead, enrich=True)

        self.assertEqual(snapshot.contacts, [])
        self.assertTrue(snapshot.needsPaidSkipTrace)
        self.assertIn("private owner cell phones", " ".join(snapshot.limitations))
        self.assertTrue(any(source.label == "Dallas County Tax Office" for source in snapshot.sourceUrls))

    def test_contact_feedback_marks_bad_numbers_down(self):
        snapshot = ContactIntelligenceService(provider_name="free_public").build_snapshot(self.lead, enrich=True)
        contact_id = snapshot.bestContact.id
        updated = ContactIntelligenceService().apply_feedback(snapshot, contact_id, "wrong_number")

        bad_contact = next(contact for contact in updated.contacts if contact.id == contact_id)
        self.assertTrue(bad_contact.wrongNumber)
        self.assertFalse(bad_contact.isCallable)
        self.assertEqual(bad_contact.status, "wrong_number")

    def test_phone_normalization_handles_country_code(self):
        self.assertEqual(normalize_phone("+1 (972) 555-0101"), "9725550101")


if __name__ == "__main__":
    unittest.main()
