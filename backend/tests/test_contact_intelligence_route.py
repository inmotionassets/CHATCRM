from unittest import TestCase
from unittest.mock import patch

from app.contact_intelligence import ContactIntelligenceService
from app.routers import contact_intelligence as contact_routes


class ContactIntelligenceRouteTests(TestCase):
    def setUp(self):
        self.lead = {
            "id": "lead-route-test",
            "name": "Domingo Hernandez",
            "owner": "Import Review",
            "address": "100 Main St Dallas TX",
            "phones": ["4696288298", "2145551234"],
        }

    def test_saved_snapshot_read_failure_still_returns_imported_contacts(self):
        service = ContactIntelligenceService(provider_name="free_public")
        with (
            patch.object(contact_routes, "require_lead", return_value=self.lead),
            patch.object(contact_routes, "get_saved_snapshot", side_effect=RuntimeError("saved payload failure")),
            patch.object(contact_routes, "real_enrichment_service", return_value=service),
        ):
            snapshot = contact_routes.get_lead_contact_intelligence(self.lead["id"], current_user=None)

        self.assertEqual(snapshot.ownerName, "Domingo Hernandez")
        self.assertEqual(len([contact for contact in snapshot.contacts if contact.contactType == "phone"]), 2)

    def test_snapshot_build_failure_uses_safe_imported_contact_fallback(self):
        class BrokenService:
            def current_snapshot(self, lead, saved):
                raise RuntimeError("snapshot merge failure")

            def provider_configured(self):
                return False

        with (
            patch.object(contact_routes, "require_lead", return_value=self.lead),
            patch.object(contact_routes, "get_saved_snapshot", return_value=None),
            patch.object(contact_routes, "real_enrichment_service", return_value=BrokenService()),
        ):
            snapshot = contact_routes.get_lead_contact_intelligence(self.lead["id"], current_user=None)

        self.assertEqual(snapshot.status, "existing_contacts_ready")
        self.assertEqual(snapshot.message, "Existing/imported contacts loaded in safe mode.")
        self.assertEqual(len([contact for contact in snapshot.contacts if contact.contactType == "phone"]), 2)

    def test_snapshot_build_failure_preserves_saved_feedback(self):
        saved = ContactIntelligenceService(provider_name="free_public").build_snapshot(self.lead, enrich=False)
        blocked_id = saved.bestContact.id
        saved = ContactIntelligenceService().apply_feedback(saved, blocked_id, "do_not_call")

        class BrokenService:
            def current_snapshot(self, lead, current_saved):
                raise RuntimeError("snapshot merge failure")

            def provider_configured(self):
                return False

        with (
            patch.object(contact_routes, "require_lead", return_value=self.lead),
            patch.object(contact_routes, "get_saved_snapshot", return_value=saved),
            patch.object(contact_routes, "real_enrichment_service", return_value=BrokenService()),
        ):
            snapshot = contact_routes.get_lead_contact_intelligence(self.lead["id"], current_user=None)

        blocked = next(contact for contact in snapshot.contacts if contact.id == blocked_id)
        self.assertTrue(blocked.doNotCall)
