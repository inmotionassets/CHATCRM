import json
import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.contact_intelligence import ContactIntelligenceSnapshot, LeadContact
from fastapi import HTTPException
from app.auth import User
from app.routers.contact_intelligence import PropStreamImportRequest, import_propstream_contacts
from app.propstream_import import (
    APPROVAL_PHRASE,
    apply_propstream_import,
    merge_propstream_snapshot,
    preview_propstream_import,
    restore_propstream_before_images,
)


class PropStreamImportTests(unittest.TestCase):
    def existing_contact(self, **updates):
        values = dict(
            id="ci-existing",
            leadId="lead-1",
            contactType="phone",
            value="(214) 555-0199",
            normalizedValue="2145550199",
            source="Imported lead data",
            isCallable=True,
            isTextable=True,
            status="confirmed_owner",
            verifiedOwner=True,
            evidence=["Owner verified in LEGACY"],
        )
        values.update(updates)
        return LeadContact(**values)

    def test_new_candidates_are_unverified_non_callable_and_deduplicated(self):
        snapshot, added = merge_propstream_snapshot(
            "lead-1",
            [
                {"value": "+1 469-555-0101", "phoneType": "Mobile", "publicDnc": False},
                {"value": "(469) 555-0101", "phoneType": "Mobile", "publicDnc": False},
            ],
            owner_name="Owner A",
            property_address="100 Main St, Dallas, TX",
            match_confidence="exact",
            match_evidence=["APN + county + property address"],
            imported_at="2026-10-09T12:00:00+00:00",
        )
        self.assertEqual(added, 1)
        contact = next(c for c in snapshot.contacts if c.normalizedValue == "4695550101")
        self.assertEqual(contact.source, "PropStream")
        self.assertEqual(contact.provider, "PropStream")
        self.assertFalse(contact.verifiedOwner)
        self.assertFalse(contact.isCallable)
        self.assertFalse(contact.isTextable)
        self.assertEqual(contact.phoneType, "Mobile")
        self.assertIn("not cleared", " ".join(contact.evidence))

        again, again_added = merge_propstream_snapshot(
            "lead-1",
            [{"value": "4695550101", "publicDnc": False}],
            snapshot,
            imported_at="2026-10-09T12:00:00+00:00",
        )
        self.assertEqual(again_added, 0)
        self.assertEqual(len(again.contacts), 1)

    def test_existing_lead_phone_is_not_shadowed_but_public_dnc_is_saved(self):
        untouched, added = merge_propstream_snapshot(
            "lead-1", [{"value": "2145550199", "alreadyOnLead": True, "publicDnc": False}]
        )
        self.assertEqual(added, 0)
        self.assertEqual(untouched.contacts, [])

        suppressed, added = merge_propstream_snapshot(
            "lead-1", [{"value": "2145550199", "alreadyOnLead": True, "publicDnc": True}]
        )
        self.assertEqual(added, 1)
        self.assertTrue(suppressed.contacts[0].doNotCall)
        self.assertFalse(suppressed.contacts[0].isCallable)
        self.assertFalse(suppressed.contacts[0].isTextable)
    def test_dnc_and_prior_suppressions_are_sticky(self):
        verified = ContactIntelligenceSnapshot(
            leadId="lead-1",
            contacts=[self.existing_contact()],
        )
        updated, added = merge_propstream_snapshot(
            "lead-1",
            [{"value": "1 (214) 555-0199", "publicDnc": True}],
            verified,
        )
        self.assertEqual(added, 0)
        contact = updated.contacts[0]
        self.assertTrue(contact.verifiedOwner)
        self.assertTrue(contact.doNotCall)
        self.assertTrue(contact.doNotText)
        self.assertFalse(contact.isCallable)
        self.assertFalse(contact.isTextable)

        for flag in ("wrongNumber", "disconnected", "doNotCall", "doNotText"):
            prior = self.existing_contact(**{flag: True})
            result, _ = merge_propstream_snapshot(
                "lead-1", [{"value": "2145550199", "publicDnc": False}],
                ContactIntelligenceSnapshot(leadId="lead-1", contacts=[prior]),
            )
            returned = result.contacts[0]
            if flag != "doNotText":
                self.assertFalse(returned.isCallable, flag)
            self.assertFalse(returned.isTextable, flag)
            self.assertTrue(getattr(returned, flag), flag)

    def test_approval_gate_rejects_missing_or_wrong_phrase(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT)")
        for approved, phrase in ((False, APPROVAL_PHRASE), (True, "yes")):
            with self.assertRaises(ValueError):
                apply_propstream_import(
                    connection, False, [{"leadId": "lead-1", "contacts": []}],
                    approved=approved, approval_phrase=phrase,
                )
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM contact_intelligence_records").fetchone()[0], 0)
        connection.close()

    def test_route_requires_admin_and_explicit_phrase_before_any_write(self):
        body = PropStreamImportRequest(approved=False, imports=[])
        acq = User(username="acq", name="Acq", role="Acquisition")
        admin = User(username="admin", name="Admin", role="Admin")
        with self.assertRaises(HTTPException) as forbidden:
            import_propstream_contacts(body, acq)
        self.assertEqual(forbidden.exception.status_code, 403)
        with self.assertRaises(HTTPException) as approval_required:
            import_propstream_contacts(body, admin)
        self.assertEqual(approval_required.exception.status_code, 400)
    def test_production_dry_run_is_read_only_and_rollback_restores_before_image(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT)")
        original = ContactIntelligenceSnapshot(
            leadId="lead-1",
            contacts=[self.existing_contact()],
        )
        original_payload = original.model_dump_json()
        connection.execute("INSERT INTO contact_intelligence_records VALUES (?, ?, ?)", ("lead-1", original_payload, "before"))
        items = [
            {"leadId": "lead-1", "matchConfidence": "exact", "contacts": [
                {"value": "2145550199", "publicDnc": True},
                {"value": "4695550101", "publicDnc": False},
            ]},
            {"leadId": "lead-2", "matchConfidence": "high_confidence", "contacts": [
                {"value": "4695550102", "publicDnc": False},
            ]},
        ]
        preview = preview_propstream_import(connection, False, items)
        self.assertFalse(preview["productionWrites"])
        self.assertEqual(preview["contactSnapshotRowsToCreate"], 1)
        self.assertEqual(preview["contactSnapshotRowsToUpdate"], 1)
        self.assertEqual(preview["contactRowsToCreate"], 2)
        self.assertEqual(preview["contactRowsToUpdate"], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM contact_intelligence_records").fetchone()[0], 1)

        with connection:
            apply_propstream_import(
                connection, False, items, approved=True,
                approval_phrase=APPROVAL_PHRASE,
            )
        with connection:
            restored = restore_propstream_before_images(
                connection, False, preview["beforeImages"], approved=True,
                approval_phrase="ROLL BACK PROPSTREAM CONTACTS",
                backup_hash=preview["backupHash"],
            )
        self.assertEqual(restored, {"snapshotsRestored": 1, "snapshotsRemoved": 1})
        rows = connection.execute("SELECT lead_id, payload FROM contact_intelligence_records ORDER BY lead_id").fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["lead_id"], "lead-1")
        self.assertEqual(rows[0]["payload"], original_payload)
        connection.close()

    def test_rollback_rejects_an_altered_backup(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT)")
        with self.assertRaises(ValueError):
            restore_propstream_before_images(
                connection, False, [{"leadId": "lead-1", "existed": False, "payload": None}],
                approved=True, approval_phrase="ROLL BACK PROPSTREAM CONTACTS", backup_hash="invalid",
            )
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM contact_intelligence_records").fetchone()[0], 0)
        connection.close()
    def test_batch_write_rolls_back_as_one_transaction(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE contact_intelligence_records (lead_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT)")
        connection.execute("CREATE TRIGGER fail_second BEFORE INSERT ON contact_intelligence_records WHEN NEW.lead_id = 'lead-2' BEGIN SELECT RAISE(ABORT, 'forced test failure'); END")
        items = [
            {"leadId": "lead-1", "contacts": [{"value": "4695550101"}], "matchConfidence": "exact"},
            {"leadId": "lead-2", "contacts": [{"value": "4695550102"}], "matchConfidence": "exact"},
        ]
        with self.assertRaises(sqlite3.IntegrityError):
            with connection:
                apply_propstream_import(
                    connection, False, items, approved=True,
                    approval_phrase=APPROVAL_PHRASE,
                    imported_at="2026-10-09T12:00:00+00:00",
                )
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM contact_intelligence_records").fetchone()[0], 0)
        connection.close()


if __name__ == "__main__":
    unittest.main()
