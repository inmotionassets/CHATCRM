"""Contact-only PropStream import helpers.

Only Contact Intelligence snapshots are written. Lead payloads, call activity,
assignments, buyer data, and agreements remain untouched.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .contact_intelligence import (
    ContactIntelligenceSnapshot,
    LeadContact,
    contact_id,
    format_phone,
    normalize_phone,
    normalize_snapshot,
)

APPROVAL_PHRASE = "IMPORT PROPSTREAM CONTACTS"


def _timestamp(value: str | None = None) -> str:
    return value or datetime.now(timezone.utc).isoformat()


def merge_propstream_snapshot(
    lead_id: str,
    candidates: list[dict[str, Any]],
    existing: ContactIntelligenceSnapshot | None = None,
    *,
    owner_name: str = "",
    property_address: str = "",
    match_confidence: str = "",
    match_evidence: list[str] | None = None,
    imported_at: str | None = None,
) -> tuple[ContactIntelligenceSnapshot, int]:
    """Add/dedupe returned phone candidates while preserving existing flags."""
    timestamp = _timestamp(imported_at)
    base = existing or ContactIntelligenceSnapshot(
        leadId=lead_id,
        ownerName=owner_name,
        propertyAddress=property_address,
        provider="existing_data",
        status="contact_candidates_added",
    )
    contacts = list(base.contacts)
    by_key: dict[str, int] = {}
    for index, contact in enumerate(contacts):
        if contact.contactType == "phone":
            key = normalize_phone(contact.normalizedValue or contact.value)
            if key:
                by_key.setdefault(key, index)

    evidence_base = [
        "Source: PropStream returned property export.",
        f"Property match confidence: {match_confidence or 'manual review'}.",
        *(match_evidence or []),
    ]
    added = 0
    seen_in_batch: set[str] = set()

    for raw in candidates:
        number = normalize_phone(str(raw.get("value") or raw.get("phone") or ""))
        if len(number) != 10 or number in seen_in_batch:
            continue
        seen_in_batch.add(number)
        public_dnc = bool(raw.get("publicDnc"))
        type_value = str(raw.get("phoneType") or "unknown").strip() or "unknown"
        incoming_evidence = [
            *evidence_base,
            f"Public DNC: {'yes' if public_dnc else 'not indicated; not cleared'}.",
        ]

        existing_index = by_key.get(number)
        if existing_index is None and bool(raw.get("alreadyOnLead")) and not public_dnc:
            # Existing lead phones already appear through the base snapshot.
            # Do not shadow their current state with an unverified import copy.
            continue
        if existing_index is not None:
            prior = contacts[existing_index]
            evidence = list(dict.fromkeys([*prior.evidence, *incoming_evidence]))
            restricted = public_dnc or prior.doNotCall or prior.wrongNumber or prior.disconnected
            contacts[existing_index] = prior.model_copy(update={
                "doNotCall": public_dnc or prior.doNotCall,
                "doNotText": public_dnc or prior.wrongNumber or prior.disconnected or prior.doNotText,
                "isCallable": False if restricted else prior.isCallable,
                "isTextable": False if restricted or public_dnc or prior.doNotText else prior.isTextable,
                "status": "do_not_call" if public_dnc else prior.status,
                "evidence": evidence,
                "updatedAt": timestamp,
            })
            continue

        contacts.append(LeadContact(
            id=contact_id(lead_id, "phone", number),
            leadId=lead_id,
            contactType="phone",
            value=format_phone(number),
            displayValue=format_phone(number),
            normalizedValue=number,
            source="PropStream",
            provider="PropStream",
            sourceConfidence=60,
            lineType="unknown",
            phoneType=type_value,
            isCallable=False,
            isTextable=False,
            status="do_not_call" if public_dnc else "needs_review",
            doNotCall=public_dnc,
            doNotText=public_dnc,
            verifiedOwner=False,
            evidence=incoming_evidence,
            updatedAt=timestamp,
        ))
        by_key[number] = len(contacts) - 1
        added += 1

    result = base.model_copy(update={
        "leadId": lead_id,
        "ownerName": base.ownerName or owner_name,
        "propertyAddress": base.propertyAddress or property_address,
        "contacts": contacts,
        "updatedAt": timestamp,
        "message": "PropStream phone candidates added for review; new candidates are not callable or textable.",
    })
    return normalize_snapshot(result), added


def apply_propstream_import(
    connection,
    use_postgres: bool,
    items: list[dict[str, Any]],
    *,
    approved: bool,
    approval_phrase: str,
    imported_at: str | None = None,
) -> dict[str, int]:
    """Apply approved rows in the caller's single database transaction.

    This updates only contact_intelligence_records. The caller's connection
    context owns commit/rollback; no enrichment queue or provider is used.
    """
    if not approved or approval_phrase != APPROVAL_PHRASE:
        raise ValueError("Explicit PropStream contact import approval is required")
    if not items:
        return {"processedLeads": 0, "addedContacts": 0, "updatedContacts": 0}

    placeholder = "%s" if use_postgres else "?"
    select_sql = f"SELECT payload FROM contact_intelligence_records WHERE lead_id = {placeholder}"
    insert_sql = (
        "INSERT INTO contact_intelligence_records (lead_id, payload, updated_at) VALUES (%s, %s, now()) "
        "ON CONFLICT (lead_id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()"
        if use_postgres else
        "INSERT INTO contact_intelligence_records (lead_id, payload, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(lead_id) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP"
    )
    added_total = updated_total = processed = 0
    for item in items:
        lead_id = str(item.get("leadId") or "").strip()
        if not lead_id:
            raise ValueError("Every approved import row must reference an existing lead")
        row = connection.execute(select_sql, (lead_id,)).fetchone()
        if row:
            payload = row[0] if use_postgres else row["payload"]
            existing = ContactIntelligenceSnapshot.model_validate(payload if isinstance(payload, dict) else json.loads(payload))
        else:
            existing = None
        snapshot, added = merge_propstream_snapshot(
            lead_id,
            list(item.get("contacts") or []),
            existing,
            owner_name=str(item.get("ownerName") or ""),
            property_address=str(item.get("propertyAddress") or ""),
            match_confidence=str(item.get("matchConfidence") or ""),
            match_evidence=list(item.get("matchEvidence") or []),
            imported_at=imported_at,
        )
        connection.execute(insert_sql, (lead_id, snapshot.model_dump_json()))
        added_total += added
        updated_total += len(item.get("contacts") or []) - added
        processed += 1
    return {"processedLeads": processed, "addedContacts": added_total, "updatedContacts": updated_total}



def preview_propstream_import(connection, use_postgres: bool, items: list[dict[str, Any]], *, lock_rows: bool = False) -> dict[str, Any]:
    """Read-only dry run with exact snapshot before-images and a content hash."""
    placeholder = "%s" if use_postgres else "?"
    lock_clause = " FOR UPDATE" if use_postgres and lock_rows else ""
    select_sql = f"SELECT payload FROM contact_intelligence_records WHERE lead_id = {placeholder}{lock_clause}"
    backup = []
    snapshot_create = snapshot_update = contact_create = contact_update = contact_unchanged = 0
    for item in items:
        lead_id = str(item.get("leadId") or "").strip()
        if not lead_id:
            raise ValueError("Every dry-run row must reference an existing lead")
        row = connection.execute(select_sql, (lead_id,)).fetchone()
        if row:
            payload = row[0] if use_postgres else row["payload"]
            raw_payload = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, separators=(",", ":"))
            existing = ContactIntelligenceSnapshot.model_validate(payload if isinstance(payload, dict) else json.loads(payload))
            snapshot_update += 1
        else:
            raw_payload = None
            existing = None
            snapshot_create += 1
        backup.append({"leadId": lead_id, "existed": row is not None, "payload": raw_payload})

        current_keys = {
            normalize_phone(contact.normalizedValue or contact.value)
            for contact in (existing.contacts if existing else [])
            if contact.contactType == "phone"
        }
        seen: set[str] = set()
        for raw in item.get("contacts") or []:
            number = normalize_phone(str(raw.get("value") or raw.get("phone") or ""))
            if len(number) != 10 or number in seen:
                continue
            seen.add(number)
            if number in current_keys:
                contact_update += 1
            elif raw.get("alreadyOnLead") and not raw.get("publicDnc"):
                contact_unchanged += 1
            else:
                contact_create += 1

    canonical_plan = json.dumps(
        {"imports": items, "beforeImages": backup},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    import hashlib
    plan_hash = hashlib.sha256(canonical_plan).hexdigest()
    backup_bytes = json.dumps(backup, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    backup_hash = hashlib.sha256(backup_bytes).hexdigest()
    return {
        "planHash": plan_hash,
        "backupHash": backup_hash,
        "importLeads": len(items),
        "contactSnapshotRowsToCreate": snapshot_create,
        "contactSnapshotRowsToUpdate": snapshot_update,
        "contactRowsToCreate": contact_create,
        "contactRowsToUpdate": contact_update,
        "contactRowsUnchanged": contact_unchanged,
        "leadRowsToCreate": 0,
        "leadRowsToUpdate": 0,
        "productionWrites": False,
        "beforeImages": backup,
    }


def restore_propstream_before_images(connection, use_postgres: bool, before_images: list[dict[str, Any]], *, approved: bool, approval_phrase: str, backup_hash: str) -> dict[str, int]:
    """Restore only contact snapshot rows from a saved dry-run before-image."""
    if not approved or approval_phrase != "ROLL BACK PROPSTREAM CONTACTS":
        raise ValueError("Explicit PropStream rollback approval is required")
    backup_bytes = json.dumps(before_images, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    import hashlib
    if hashlib.sha256(backup_bytes).hexdigest() != backup_hash:
        raise ValueError("Rollback backup checksum does not match")
    placeholder = "%s" if use_postgres else "?"
    upsert_sql = (
        "INSERT INTO contact_intelligence_records (lead_id, payload, updated_at) VALUES (%s, %s, now()) "
        "ON CONFLICT (lead_id) DO UPDATE SET payload = EXCLUDED.payload, updated_at = now()"
        if use_postgres else
        "INSERT INTO contact_intelligence_records (lead_id, payload, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP) "
        "ON CONFLICT(lead_id) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP"
    )
    restored = deleted = 0
    seen: set[str] = set()
    for image in before_images:
        lead_id = str(image.get("leadId") or "").strip()
        if not lead_id or lead_id in seen:
            raise ValueError("Rollback before-image contains a missing or duplicate lead id")
        seen.add(lead_id)
        if image.get("existed"):
            payload = image.get("payload")
            if payload is None:
                raise ValueError("Existing snapshot before-image is missing its payload")
            payload = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, separators=(",", ":"))
            connection.execute(upsert_sql, (lead_id, payload))
            restored += 1
        else:
            connection.execute(f"DELETE FROM contact_intelligence_records WHERE lead_id = {placeholder}", (lead_id,))
            deleted += 1
    return {"snapshotsRestored": restored, "snapshotsRemoved": deleted}
