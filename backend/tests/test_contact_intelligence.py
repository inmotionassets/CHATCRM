import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contact_intelligence import BatchDataContactProvider, ContactIntelligenceService, normalize_phone


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

    def test_batchdata_not_configured_is_clear_and_safe(self):
        provider = BatchDataContactProvider(api_key="")
        snapshot = ContactIntelligenceService(provider_name="batchdata", public_provider=provider).build_snapshot(
            {"id": "lead-no-key", "name": "Owner", "address": "100 Main St Dallas TX"},
            enrich=True,
        )

        self.assertEqual(snapshot.status, "provider_not_configured")
        self.assertFalse(snapshot.paidProviderConfigured)
        self.assertTrue(snapshot.needsPaidSkipTrace)
        self.assertIn("BATCHDATA_API_KEY", snapshot.message)

    def test_batchdata_provider_normalizes_new_phone_email_and_evidence(self):
        def fake_request(payload):
            self.assertIsInstance(payload, list)
            self.assertEqual(payload[0]["owner_name"], "Forge Holdings LLC")
            return {
                "results": [
                    {
                        "owner_name": "Forge Holdings LLC",
                        "property_address": "1234 Forge St Dallas TX",
                        "confidence_score": 0.91,
                        "phones": [
                            {
                                "phone": "+1 (469) 555-0188",
                                "phone_type": "mobile",
                                "confidence": 0.94,
                                "dnc_status": False,
                                "last_verified_date": "2026-08-01",
                            }
                        ],
                        "emails": [{"email": "forge@example.com", "confidence": 0.81}],
                    }
                ]
            }

        provider = BatchDataContactProvider(api_key="test-key", request_json=fake_request)
        snapshot = ContactIntelligenceService(provider_name="batchdata", public_provider=provider).build_snapshot(
            {"id": "lead-new-phone", "name": "Forge Holdings LLC", "address": "1234 Forge St Dallas TX"},
            enrich=True,
        )

        self.assertTrue(snapshot.paidProviderConfigured)
        self.assertEqual(snapshot.status, "enriched")
        self.assertFalse(snapshot.needsPaidSkipTrace)
        self.assertEqual(snapshot.bestContact.normalizedValue, "4695550188")
        self.assertEqual(snapshot.bestContact.provider, "batchdata")
        self.assertEqual(snapshot.bestContact.phoneType, "mobile")
        self.assertGreaterEqual(snapshot.bestContact.ownerNameMatch, 90)
        self.assertTrue(snapshot.enrichmentRunId.startswith("run-"))
        self.assertTrue(any(contact.contactType == "email" for contact in snapshot.contacts))

    def test_batchdata_dnc_phone_is_not_callable(self):
        provider = BatchDataContactProvider(
            api_key="test-key",
            request_json=lambda payload: {
                "results": [
                    {
                        "owner_name": "Forge Holdings LLC",
                        "property_address": "1234 Forge St Dallas TX",
                        "phones": [{"phone": "214-555-0112", "phone_type": "mobile", "dnc_status": True}],
                    }
                ]
            },
        )
        snapshot = ContactIntelligenceService(provider_name="batchdata", public_provider=provider).build_snapshot(
            {"id": "lead-dnc", "name": "Forge Holdings LLC", "address": "1234 Forge St Dallas TX"},
            enrich=True,
        )

        contact = snapshot.contacts[0]
        self.assertTrue(contact.doNotCall)
        self.assertFalse(contact.isCallable)
        self.assertEqual(contact.status, "do_not_call")

    def test_contact_feedback_marks_bad_numbers_down(self):
        single_phone_lead = {**self.lead, "phone": "214-555-0199", "phones": ["214-555-0199"], "email": ""}
        snapshot = ContactIntelligenceService(provider_name="free_public").build_snapshot(single_phone_lead, enrich=True)
        contact_id = snapshot.bestContact.id
        updated = ContactIntelligenceService().apply_feedback(snapshot, contact_id, "wrong_number")

        bad_contact = next(contact for contact in updated.contacts if contact.id == contact_id)
        self.assertTrue(bad_contact.wrongNumber)
        self.assertFalse(bad_contact.isCallable)
        self.assertEqual(bad_contact.status, "wrong_number")
        self.assertTrue(updated.refreshRecommended)

    def test_phone_normalization_handles_country_code(self):
        self.assertEqual(normalize_phone("+1 (972) 555-0101"), "9725550101")


if __name__ == "__main__":
    unittest.main()
