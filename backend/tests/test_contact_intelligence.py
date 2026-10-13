import sqlite3
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
from fastapi import HTTPException

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
            LeadContact(id="eligible", leadId="queue-test", value="2145550199", normalizedValue="2145550199", isCallable=True, verifiedOwner=True, sourceQualityReviewed=True, status="confirmed_owner", doNotText=True),
            LeadContact(id="review", leadId="queue-test", value="4695550111", normalizedValue="4695550111", isCallable=False, status="needs_review"),
            LeadContact(id="down", leadId="queue-test", value="9725550111", normalizedValue="9725550111", isCallable=False, disconnected=True, status="disconnected"),
            LeadContact(id="blocked", leadId="queue-test", value="8175550111", normalizedValue="8175550111", isCallable=False, doNotCall=True, status="do_not_call"),
            LeadContact(id="opted-out", leadId="queue-test", value="4695550101", normalizedValue="4695550101", optedOut=True, status="opted_out"),
            LeadContact(id="litigation", leadId="queue-test", value="4695550102", normalizedValue="4695550102", litigationHold=True, status="litigation_hold"),
            LeadContact(id="email", leadId="queue-test", contactType="email", value="owner@example.com"),
        ]
        summary = summarize_calling_snapshot(ContactIntelligenceSnapshot(leadId="queue-test", contacts=contacts))
        self.assertEqual(summary["status"], "eligible")
        self.assertEqual(summary["numberCounts"], {"eligible": 2, "unreviewed": 0, "disconnected": 1, "suppressed": 3})
        self.assertNotIn("value", summary)

    def test_lead_level_compliance_status_overrides_callable_phone_snapshot(self):
        snapshot = ContactIntelligenceSnapshot(leadId="queue-dnc", contacts=[
            LeadContact(id="n1", leadId="queue-dnc", value="2145550199", normalizedValue="2145550199", isCallable=True, verifiedOwner=True, sourceQualityReviewed=True, status="confirmed_owner")
        ])
        summary = summarize_calling_snapshot(snapshot, "do-not-call")
        self.assertEqual(summary["status"], "suppressed")
        self.assertEqual(summary["numberCounts"]["eligible"], 0)
        self.assertEqual(summary["numberCounts"]["suppressed"], 1)

    def test_empty_snapshot_is_explicitly_no_numbers(self):
        summary = summarize_calling_snapshot(ContactIntelligenceSnapshot(leadId="empty"))
        self.assertEqual(summary["status"], "no_numbers")

    def test_calling_queue_returns_numbers_only_when_display_payload_is_requested(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT, payload TEXT)")
        saved = ContactIntelligenceSnapshot(leadId="saved-only-lead", contacts=[
            LeadContact(id="saved-phone", leadId="saved-only-lead", value="(214) 555-0199", normalizedValue="2145550199", isCallable=True, verifiedOwner=True, sourceQualityReviewed=True, status="confirmed_owner")
        ])
        connection.execute(
            "INSERT INTO contact_intelligence_records (lead_id, payload) VALUES (?, ?)",
            (saved.leadId, saved.model_dump_json()),
        )
        lead = Lead(id="saved-only-lead", name="Owner", address="1 Main St", contactStatus="needs-review")
        request = contact_router.CallingQueueRequest(leadIds=[lead.id])
        with (
            patch.object(contact_router.lead_store, "USE_POSTGRES", False),
            patch.object(contact_router.lead_store, "list_saved_leads_by_ids", return_value=[lead]),
            patch.object(contact_router, "get_connection", return_value=connection),
            patch.object(contact_router, "real_enrichment_service", return_value=ContactIntelligenceService(provider_name="free_public")),
        ):
            result = contact_router.summarize_calling_queue(request, SimpleNamespace(role="Acquisition"))
        self.assertEqual(result["leadCounts"]["eligible"], 1)
        self.assertEqual(result["numberCounts"]["eligible"], 1)
        self.assertEqual(result["leads"][0]["status"], "eligible")
        self.assertNotIn("2145550199", str(result))

        display_request = contact_router.CallingQueueRequest(leadIds=[lead.id], includePhoneNumbers=True)
        with (
            patch.object(contact_router.lead_store, "USE_POSTGRES", False),
            patch.object(contact_router.lead_store, "list_saved_leads_by_ids", return_value=[lead]),
            patch.object(contact_router, "get_connection", return_value=connection),
            patch.object(contact_router, "real_enrichment_service", return_value=ContactIntelligenceService(provider_name="free_public")),
        ):
            display_result = contact_router.summarize_calling_queue(display_request, SimpleNamespace(role="Acquisition"))
        self.assertEqual(display_result["leads"][0]["phoneNumbers"], [{"value": "(214) 555-0199", "status": "eligible"}])

    def test_batch_calling_queue_applies_suppressions_with_one_phone_lookup(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("""
            CREATE TABLE contact_phone_suppressions (
                phone TEXT PRIMARY KEY, do_not_call INTEGER, do_not_text INTEGER,
                disconnected INTEGER, wrong_number INTEGER
            )
        """)
        connection.executemany(
            "INSERT INTO contact_phone_suppressions VALUES (?, ?, ?, ?, ?)",
            [("2145550199", 1, 0, 0, 0), ("4695550111", 0, 1, 0, 0)],
        )
        statements = []
        connection.set_trace_callback(statements.append)
        snapshots = [
            ContactIntelligenceSnapshot(leadId="one", contacts=[LeadContact(
                id="one-phone", leadId="one", value="2145550199", normalizedValue="2145550199",
                isCallable=True, isTextable=True, verifiedOwner=True, sourceQualityReviewed=True,
                status="confirmed_owner",
            )]),
            ContactIntelligenceSnapshot(leadId="two", contacts=[LeadContact(
                id="two-phone", leadId="two", value="4695550111", normalizedValue="4695550111",
                isCallable=True, isTextable=True, verifiedOwner=True, sourceQualityReviewed=True,
                status="confirmed_owner",
            )]),
        ]

        with patch.object(contact_router.lead_store, "USE_POSTGRES", False):
            restricted = contact_router.apply_registered_phone_suppressions_batch(connection, snapshots)

        self.assertEqual(restricted[0].contacts[0].status, "do_not_call")
        self.assertFalse(restricted[0].contacts[0].isCallable)
        self.assertEqual(restricted[1].contacts[0].status, "do_not_text")
        self.assertTrue(restricted[1].contacts[0].isCallable)
        self.assertFalse(restricted[1].contacts[0].isTextable)
        suppression_lookups = [sql for sql in statements if "from contact_phone_suppressions where phone in" in sql.lower()]
        self.assertEqual(len(suppression_lookups), 1)

    def test_review_to_calling_queue_promotes_only_the_reviewed_test_number(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT PRIMARY KEY, payload TEXT, updated_at TEXT)")
        lead = Lead(
            id="workflow-safe-test", name="Test Owner", address="1 Test St Dallas TX",
            phone="2145550114", phones=["2145550114"], contactStatus="needs-review",
        )
        candidate = LeadContact(
            id="workflow-safe-phone", leadId=lead.id, value="2145550114",
            normalizedValue="2145550114", source="PropStream", isCallable=False,
            isTextable=False, status="needs_review", sourceConfidence=None,
        )
        service = ContactIntelligenceService(provider_name="free_public")
        pending = ContactIntelligenceSnapshot(leadId=lead.id, contacts=[candidate])
        connection.execute(
            "INSERT INTO contact_intelligence_records VALUES (?, ?, CURRENT_TIMESTAMP)",
            (lead.id, pending.model_dump_json()),
        )

        with (
            patch.object(contact_router.lead_store, "USE_POSTGRES", False),
            patch.object(contact_router.lead_store, "list_saved_leads_by_ids", return_value=[lead]),
            patch.object(contact_router, "get_connection", return_value=connection),
            patch.object(contact_router, "real_enrichment_service", return_value=service),
        ):
            live_snapshot = service.current_snapshot(lead, pending)
            self.assertEqual(live_snapshot.bestContact.id, candidate.id)
            self.assertFalse(live_snapshot.needsPaidSkipTrace)
            self.assertFalse(live_snapshot.refreshRecommended)
            before = contact_router.summarize_calling_queue(
                contact_router.CallingQueueRequest(leadIds=[lead.id]), SimpleNamespace(role="Acquisition"),
            )
            reviewed = service.apply_feedback(pending, candidate.id, "confirmed_owner")
            connection.execute(
                "UPDATE contact_intelligence_records SET payload = ? WHERE lead_id = ?",
                (reviewed.model_dump_json(), lead.id),
            )
            after = contact_router.summarize_calling_queue(
                contact_router.CallingQueueRequest(leadIds=[lead.id]), SimpleNamespace(role="Acquisition"),
            )

        self.assertEqual(before["numberCounts"]["unreviewed"], 0)
        self.assertEqual(before["numberCounts"]["eligible"], 1)
        self.assertEqual(before["leads"][0]["status"], "eligible")
        self.assertEqual(after["numberCounts"]["eligible"], 1)
        self.assertEqual(after["leadCounts"]["eligible"], 1)
        self.assertNotIn("2145550114", str(after))

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

    def test_reviewed_owner_becomes_call_ready_without_inventing_confidence_or_text_consent(self):
        imported = LeadContact(
            id="propstream-phone", leadId="review", value="214-555-0199",
            normalizedValue="2145550199", source="PropStream", status="needs_review",
            sourceConfidence=None, isCallable=False, isTextable=False,
        )
        snapshot = ContactIntelligenceSnapshot(leadId="review", contacts=[imported])
        reviewed = ContactIntelligenceService().apply_feedback(snapshot, imported.id, "confirmed_owner")
        contact = reviewed.contacts[0]
        self.assertTrue(contact.verifiedOwner)
        self.assertTrue(contact.sourceQualityReviewed)
        self.assertEqual(contact.status, "confirmed_owner")
        self.assertTrue(contact.isCallable)
        self.assertFalse(contact.isTextable)
        self.assertIsNone(contact.sourceConfidence)
        called = ContactIntelligenceService().apply_feedback(reviewed, imported.id, "no_answer").contacts[0]
        self.assertEqual(called.status, "confirmed_owner")
        self.assertTrue(called.isCallable)
        self.assertTrue(called.lastAttemptedAt)

    def test_owner_review_cannot_clear_sticky_or_litigation_restrictions(self):
        for values in (
            {"doNotCall": True, "status": "do_not_call"},
            {"status": "public_dnc"},
            {"wrongNumber": True, "status": "wrong_number"},
            {"disconnected": True, "status": "disconnected"},
            {"status": "litigation_hold"},
            {"optedOut": True, "status": "opted_out"},
            {"doNotContact": True, "status": "do_not_contact"},
        ):
            with self.subTest(values=values):
                contact = LeadContact(
                    id="restricted", leadId="review", value="2145550199",
                    normalizedValue="2145550199", isCallable=False, **values,
                )
                reviewed = ContactIntelligenceService().apply_feedback(
                    ContactIntelligenceSnapshot(leadId="review", contacts=[contact]),
                    contact.id,
                    "confirmed_owner",
                ).contacts[0]
                self.assertFalse(reviewed.isCallable)
                self.assertEqual(reviewed.status, values["status"])

    def test_missing_source_score_is_not_zero_and_zero_remains_a_real_score(self):
        missing = LeadContact(id="a", leadId="l", value="2145550199")
        zero = LeadContact(id="b", leadId="l", value="2145550100", sourceConfidence=0)
        self.assertIsNone(missing.sourceConfidence)
        self.assertEqual(zero.sourceConfidence, 0)

    def test_review_endpoint_requires_acquisition_access_and_source_review_attestation(self):
        request = contact_router.ContactFeedbackRequest(leadId="safe-test", feedbackType="confirmed_owner")
        with self.assertRaises(HTTPException) as denied:
            contact_router.record_contact_feedback("contact", request, SimpleNamespace(role="Disposition"))
        self.assertEqual(denied.exception.status_code, 403)

        with self.assertRaises(HTTPException) as missing_attestation:
            contact_router.record_contact_feedback("contact", request, SimpleNamespace(role="Acquisition"))
        self.assertEqual(missing_attestation.exception.status_code, 400)

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
        reviewed = next(c for c in updated.contacts if c.id == new_contact.id)
        self.assertTrue(reviewed.verifiedOwner)
        self.assertTrue(reviewed.isCallable)
        self.assertEqual(reviewed.sourceConfidence, new_contact.sourceConfidence)


if __name__ == "__main__":
    unittest.main()
