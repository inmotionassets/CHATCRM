import sqlite3
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contact_intelligence import BatchDataContactProvider, ContactIntelligenceService, ContactIntelligenceSnapshot, LeadContact, normalize_phone, summarize_calling_snapshot
from app.routers import contact_intelligence as contact_router
from app.routers.leads import Lead


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

    def test_calling_queue_summary_classifies_all_phone_safety_states(self):
        contacts = [
            LeadContact(id="eligible", leadId="queue-test", value="2145550199", normalizedValue="2145550199", isCallable=True, status="imported", doNotText=True),
            LeadContact(id="review", leadId="queue-test", value="4695550111", normalizedValue="4695550111", isCallable=False, status="needs_review"),
            LeadContact(id="down", leadId="queue-test", value="9725550111", normalizedValue="9725550111", isCallable=False, disconnected=True, status="disconnected"),
            LeadContact(id="blocked", leadId="queue-test", value="8175550111", normalizedValue="8175550111", isCallable=False, doNotCall=True, status="do_not_call"),
            LeadContact(id="email", leadId="queue-test", contactType="email", value="owner@example.com"),
        ]
        summary = summarize_calling_snapshot(ContactIntelligenceSnapshot(leadId="queue-test", contacts=contacts))
        self.assertEqual(summary["status"], "eligible")
        self.assertEqual(summary["numberCounts"], {"eligible": 1, "unreviewed": 1, "disconnected": 1, "suppressed": 1})
        self.assertNotIn("value", summary)

    def test_lead_level_compliance_status_overrides_callable_phone_snapshot(self):
        snapshot = ContactIntelligenceSnapshot(leadId="queue-dnc", contacts=[
            LeadContact(id="n1", leadId="queue-dnc", value="2145550199", normalizedValue="2145550199", isCallable=True, status="imported")
        ])
        summary = summarize_calling_snapshot(snapshot, "do-not-call")
        self.assertEqual(summary["status"], "suppressed")
        self.assertEqual(summary["numberCounts"]["eligible"], 0)
        self.assertEqual(summary["numberCounts"]["suppressed"], 1)

    def test_empty_snapshot_is_explicitly_no_numbers(self):
        summary = summarize_calling_snapshot(ContactIntelligenceSnapshot(leadId="empty"))
        self.assertEqual(summary["status"], "no_numbers")

    def test_calling_queue_endpoint_uses_saved_contact_snapshot_without_returning_phone_values(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT, payload TEXT)")
        saved = ContactIntelligenceSnapshot(leadId="saved-only-lead", contacts=[
            LeadContact(id="saved-phone", leadId="saved-only-lead", value="(214) 555-0199", normalizedValue="2145550199", isCallable=True, status="imported")
        ])
        connection.execute(
            "INSERT INTO contact_intelligence_records (lead_id, payload) VALUES (?, ?)",
            (saved.leadId, saved.model_dump_json()),
        )
        lead = Lead(id="saved-only-lead", name="Owner", address="1 Main St", contactStatus="needs-review")
        request = contact_router.CallingQueueRequest(leadIds=[lead.id])
        with (
            patch.object(contact_router.lead_store, "USE_POSTGRES", False),
            patch.object(contact_router.lead_store, "list_saved_leads", return_value=[lead]),
            patch.object(contact_router, "get_connection", return_value=connection),
            patch.object(contact_router, "real_enrichment_service", return_value=ContactIntelligenceService(provider_name="free_public")),
        ):
            result = contact_router.summarize_calling_queue(request, SimpleNamespace(role="Acquisition"))
        self.assertEqual(result["leadCounts"]["eligible"], 1)
        self.assertEqual(result["numberCounts"]["eligible"], 1)
        self.assertEqual(result["leads"][0]["status"], "eligible")
        self.assertNotIn("2145550199", str(result))

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

    def test_current_snapshot_unions_imports_and_preserves_feedback_without_provider_call(self):
        def forbidden_request(payload):
            self.fail("A read must never call paid enrichment")
        provider = BatchDataContactProvider(api_key="test-only", request_json=forbidden_request)
        service = ContactIntelligenceService(provider_name="batchdata", public_provider=provider)
        lead = {**self.lead, "name": "Domingo Hernandez", "owner": "Import Review"}
        saved = service.build_snapshot(lead)
        saved = service.apply_feedback(saved, saved.bestContact.id, "do_not_call")
        original_dump = saved.model_dump()
        lead["phones"] = ["2145550199", "9725550111", "4695550101", "4695550102", "4695550103"]
        current = service.current_snapshot(lead, saved)
        phones = [c for c in current.contacts if c.contactType == "phone"]
        self.assertEqual(len(phones), 5)
        self.assertTrue(next(c for c in phones if c.normalizedValue == "2145550199").doNotCall)
        self.assertNotEqual(current.bestContact.normalizedValue, "2145550199")
        self.assertEqual(current.ownerName, "Domingo Hernandez")
        self.assertTrue(current.paidProviderConfigured)
        self.assertEqual(saved.model_dump(), original_dump)
        self.assertEqual(provider.build_payload(lead)[0]["owner_name"], "Domingo Hernandez")

    def test_missing_contacts_need_no_paid_request(self):
        provider = BatchDataContactProvider(api_key="", request_json=lambda _: self.fail("No paid request"))
        service = ContactIntelligenceService(provider_name="batchdata", public_provider=provider)
        for name in ["Agustin Jaramillo", "Gilberto Lopez"]:
            snapshot = service.current_snapshot({"id": name, "name": name, "owner": "Import Review"})
            self.assertEqual(snapshot.contacts, [])
            self.assertIsNone(snapshot.bestContact)
            self.assertFalse(snapshot.paidProviderConfigured)

    def test_feedback_can_target_new_import_after_saved_snapshot(self):
        service = ContactIntelligenceService(provider_name="free_public")
        saved = service.build_snapshot(self.lead)
        lead = {**self.lead, "phones": [*self.lead["phones"], "4695550101"]}
        current = service.current_snapshot(lead, saved)
        new_contact = next(c for c in current.contacts if c.normalizedValue == "4695550101")
        updated = service.apply_feedback(current, new_contact.id, "confirmed_owner")
        self.assertEqual(updated.bestContact.id, new_contact.id)
        self.assertTrue(updated.bestContact.verifiedOwner)


if __name__ == "__main__":
    unittest.main()
