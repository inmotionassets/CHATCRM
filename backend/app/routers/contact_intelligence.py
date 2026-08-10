from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..auth import CurrentUser
from ..contact_intelligence import (
    ContactSourceLink,
    ContactIntelligenceService,
    ContactIntelligenceSnapshot,
    extract_lead_emails,
    extract_lead_phones,
    normalize_phone,
)
from . import leads as lead_store


router = APIRouter(prefix="/contact-intelligence", tags=["contact-intelligence"])
TEST_BATCH_LIMIT = 10


class ContactFeedbackRequest(BaseModel):
    leadId: str
    feedbackType: str
    notes: str = ""


class ContactBatchRequest(BaseModel):
    leadIds: list[str] = Field(default_factory=list)


class ContactEntitySnapshotRequest(BaseModel):
    entityType: str = "entity"
    entityId: str = ""
    entityName: str = ""
    company: str = ""
    phone: str = ""
    phones: list[str] = Field(default_factory=list)
    email: str = ""
    website: str = ""
    contactFormUrl: str = ""
    linkedinUrl: str = ""
    facebookUrl: str = ""
    mailingAddress: str = ""
    registeredAgent: str = ""
    address: str = ""
    county: str = ""
    source: str = ""
    sourceUrls: list[str] = Field(default_factory=list)


class ContactBatchResult(BaseModel):
    provider: str
    providerConfigured: bool
    requestedCount: int
    processedCount: int
    matchedCount: int
    partialCount: int
    unmatchedCount: int
    failedCount: int
    maxBatch: int = TEST_BATCH_LIMIT
    message: str = ""
    results: list[dict[str, Any]] = Field(default_factory=list)


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_contact_intelligence_table(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_intelligence_records (
                lead_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        connection.execute(
            """
            ALTER TABLE contact_intelligence_records
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_enrichment_queue (
                lead_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                reason TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_intelligence_records (
            lead_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_enrichment_queue (
            lead_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'pending',
            reason TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_saved_snapshot(lead_id: str) -> ContactIntelligenceSnapshot | None:
    with get_connection() as connection:
        ensure_contact_intelligence_table(connection)
        if lead_store.USE_POSTGRES:
            row = connection.execute(
                "SELECT payload FROM contact_intelligence_records WHERE lead_id = %s",
                (lead_id,),
            ).fetchone()
        else:
            row = connection.execute(
                "SELECT payload FROM contact_intelligence_records WHERE lead_id = ?",
                (lead_id,),
            ).fetchone()

    if not row:
        return None

    payload = row[0] if lead_store.USE_POSTGRES else row["payload"]
    return ContactIntelligenceSnapshot.model_validate(lead_store.parse_saved_payload(payload))


def save_snapshot(snapshot: ContactIntelligenceSnapshot) -> ContactIntelligenceSnapshot:
    with get_connection() as connection:
        ensure_contact_intelligence_table(connection)
        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO contact_intelligence_records (lead_id, payload, updated_at)
                VALUES (%s, %s, now())
                ON CONFLICT (lead_id) DO UPDATE SET
                    payload = EXCLUDED.payload,
                    updated_at = now()
                """,
                (snapshot.leadId, snapshot.model_dump_json()),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO contact_intelligence_records (lead_id, payload, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (snapshot.leadId, snapshot.model_dump_json()),
            )

    queue_if_needed(snapshot.leadId, snapshot)
    return snapshot


def upsert_queue(lead_id: str, status: str, reason: str) -> None:
    with get_connection() as connection:
        ensure_contact_intelligence_table(connection)
        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO contact_enrichment_queue (lead_id, status, reason, updated_at)
                VALUES (%s, %s, %s, now())
                ON CONFLICT (lead_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    reason = EXCLUDED.reason,
                    updated_at = now()
                """,
                (lead_id, status, reason),
            )
        else:
            connection.execute(
                """
                INSERT OR REPLACE INTO contact_enrichment_queue (lead_id, status, reason, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (lead_id, status, reason),
            )


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def require_entity_contact_access(entity_type: str, current_user: CurrentUser) -> None:
    protected_types = {"buyer", "builder", "developer", "llc", "business", "entity"}
    if entity_type.lower() in protected_types and current_user.role not in {"Admin", "Disposition"}:
        raise HTTPException(status_code=403, detail="Buyer Contact Intelligence is protected for leadership.")


def require_lead(lead_id: str):
    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def contact_entity_payload(request: ContactEntitySnapshotRequest) -> dict[str, Any]:
    entity_type = (request.entityType or "entity").strip().lower()
    entity_name = (
        request.entityName
        or request.company
        or request.registeredAgent
        or request.mailingAddress
        or "Unknown Entity"
    ).strip()
    entity_id = (request.entityId or f"{entity_type}:{entity_name}").strip()
    phones = [phone for phone in [request.phone, *request.phones] if str(phone).strip()]
    address = (request.address or request.mailingAddress).strip()

    return {
        "id": entity_id,
        "name": entity_name,
        "owner": entity_name,
        "address": address,
        "mailingAddress": request.mailingAddress,
        "phone": phones[0] if phones else "",
        "phones": phones,
        "email": request.email,
        "website": request.website,
        "county": request.county,
        "source": request.source,
        "entityType": entity_type,
        "registeredAgent": request.registeredAgent,
    }


def entity_source_links(request: ContactEntitySnapshotRequest) -> list[ContactSourceLink]:
    links: list[ContactSourceLink] = []
    for label, url, source_type in [
        ("Company website", request.website, "public_business_record"),
        ("Contact form", request.contactFormUrl, "public_business_contact"),
        ("LinkedIn company page", request.linkedinUrl, "public_social_profile"),
        ("Facebook business page", request.facebookUrl, "public_social_profile"),
    ]:
        clean_url = str(url or "").strip()
        if clean_url:
            links.append(ContactSourceLink(label=label, url=clean_url, sourceType=source_type, confidence=70))

    for index, url in enumerate(request.sourceUrls, start=1):
        clean_url = str(url or "").strip()
        if clean_url:
            links.append(
                ContactSourceLink(
                    label=f"Imported source {index}",
                    url=clean_url,
                    sourceType="imported_source",
                    confidence=60,
                )
            )
    return links


def merge_source_links(existing: list[ContactSourceLink], extra: list[ContactSourceLink]) -> list[ContactSourceLink]:
    seen: set[str] = set()
    merged: list[ContactSourceLink] = []
    for link in [*existing, *extra]:
        key = link.url.lower()
        if not link.url or key in seen:
            continue
        seen.add(key)
        merged.append(link)
    return merged


def real_enrichment_service() -> ContactIntelligenceService:
    provider_name = (os.getenv("CONTACT_INTELLIGENCE_PROVIDER") or "batchdata").strip().lower()
    return ContactIntelligenceService(provider_name=provider_name)


def queue_if_needed(lead_id: str, snapshot: ContactIntelligenceSnapshot | None = None) -> tuple[bool, str]:
    lead = lead_store.get_saved_lead(lead_id)
    if not lead:
        return False, "lead_missing"
    needs_queue, reason = lead_needs_enrichment(lead, snapshot)
    if needs_queue:
        upsert_queue(lead_id, "pending", reason)
    return needs_queue, reason


def lead_needs_enrichment(lead, snapshot: ContactIntelligenceSnapshot | None = None) -> tuple[bool, str]:
    lead_data = lead.model_dump() if hasattr(lead, "model_dump") else dict(lead)
    if not extract_lead_phones(lead_data):
        return True, "missing_contact"

    if snapshot:
        phone_contacts = [contact for contact in snapshot.contacts if contact.contactType == "phone"]
        if phone_contacts and all(contact.wrongNumber or contact.disconnected or contact.doNotCall for contact in phone_contacts):
            return True, "refresh_recommended"
        if snapshot.refreshRecommended:
            return True, "refresh_recommended"

    return False, ""


def attach_snapshot_contacts_to_lead(lead, snapshot: ContactIntelligenceSnapshot) -> tuple[int, int]:
    lead_data = lead.model_dump() if hasattr(lead, "model_dump") else dict(lead)
    existing_phones = extract_lead_phones(lead_data)
    existing_phone_keys = {normalize_phone(phone) for phone in existing_phones}
    new_phones: list[str] = []

    for contact in snapshot.contacts:
        if contact.contactType != "phone":
            continue
        if contact.doNotCall or contact.wrongNumber or contact.disconnected or not contact.isCallable:
            continue
        key = normalize_phone(contact.normalizedValue or contact.value)
        if key and key not in existing_phone_keys:
            existing_phone_keys.add(key)
            new_phones.append(contact.displayValue or contact.value)

    existing_emails = extract_lead_emails(lead_data)
    existing_email_keys = {email.lower() for email in existing_emails}
    new_emails: list[str] = []
    for contact in snapshot.contacts:
        if contact.contactType != "email":
            continue
        email = (contact.normalizedValue or contact.value).strip().lower()
        if email and email not in existing_email_keys:
            existing_email_keys.add(email)
            new_emails.append(email)

    updates: dict[str, object] = {}
    if new_phones:
        merged_phones = [*existing_phones, *new_phones]
        updates["phones"] = merged_phones
        updates["phone"] = merged_phones[0]
    if new_emails:
        merged_emails = [*existing_emails, *new_emails]
        updates["email"] = ", ".join(merged_emails)

    if updates:
        lead_store.update_lead_payload(lead.id, updates)

    return len(new_phones), len(new_emails)


def process_enrichment(lead_id: str, service: ContactIntelligenceService) -> dict[str, Any]:
    lead = require_lead(lead_id)
    snapshot = service.build_snapshot(lead, enrich=True)
    added_phones, added_emails = attach_snapshot_contacts_to_lead(lead, snapshot)
    saved_snapshot = save_snapshot(snapshot)

    if saved_snapshot.status in {"failed", "provider_not_configured"}:
        outcome = "failed"
    elif added_phones or any(contact.contactType == "phone" and contact.provider for contact in saved_snapshot.contacts):
        outcome = "matched"
    elif saved_snapshot.contacts:
        outcome = "partial"
    else:
        outcome = "unmatched"

    upsert_queue(lead_id, "completed" if outcome in {"matched", "partial"} else "pending", outcome)
    return {
        "leadId": lead_id,
        "outcome": outcome,
        "addedPhones": added_phones,
        "addedEmails": added_emails,
        "status": saved_snapshot.status,
        "message": saved_snapshot.message,
        "snapshot": saved_snapshot,
    }


def build_batch_result(service: ContactIntelligenceService, requested_count: int, results: list[dict[str, Any]], message: str = "") -> ContactBatchResult:
    return ContactBatchResult(
        provider=service.provider_name,
        providerConfigured=service.provider_configured(),
        requestedCount=requested_count,
        processedCount=len(results),
        matchedCount=sum(1 for result in results if result["outcome"] == "matched"),
        partialCount=sum(1 for result in results if result["outcome"] == "partial"),
        unmatchedCount=sum(1 for result in results if result["outcome"] == "unmatched"),
        failedCount=sum(1 for result in results if result["outcome"] == "failed"),
        message=message,
        results=results,
    )


def eligible_missing_leads() -> list[str]:
    eligible: list[str] = []
    for lead in lead_store.list_saved_leads():
        saved_snapshot = get_saved_snapshot(lead.id)
        needs_queue, reason = lead_needs_enrichment(lead, saved_snapshot)
        if needs_queue:
            upsert_queue(lead.id, "pending", reason)
            eligible.append(lead.id)
    return eligible


@router.get("/leads/{lead_id}", response_model=ContactIntelligenceSnapshot)
def get_lead_contact_intelligence(lead_id: str, current_user: CurrentUser):
    saved_snapshot = get_saved_snapshot(lead_id)
    if saved_snapshot:
        queue_if_needed(lead_id, saved_snapshot)
        return saved_snapshot

    lead = require_lead(lead_id)
    snapshot = ContactIntelligenceService().build_snapshot(lead, enrich=False)
    return save_snapshot(snapshot)


@router.post("/entities/snapshot", response_model=ContactIntelligenceSnapshot)
def get_entity_contact_intelligence(request: ContactEntitySnapshotRequest, current_user: CurrentUser):
    entity_type = (request.entityType or "entity").strip().lower()
    require_entity_contact_access(entity_type, current_user)

    payload = contact_entity_payload(request)
    snapshot = ContactIntelligenceService().build_snapshot(payload, enrich=False)
    source_links = merge_source_links(snapshot.sourceUrls, entity_source_links(request))
    has_contacts = bool(snapshot.contacts)
    message = (
        "Existing Contact Intelligence is ready for this entity."
        if has_contacts
        else "No verified contact is saved yet. Public research paths are ready; licensed enrichment is still required for private phones."
    )

    return snapshot.model_copy(
        update={
            "leadId": payload["id"],
            "ownerName": payload["owner"],
            "propertyAddress": payload["address"],
            "provider": "contact_intelligence",
            "sourceUrls": source_links,
            "needsPaidSkipTrace": not has_contacts,
            "message": message,
        }
    )


@router.post("/leads/{lead_id}/enrich", response_model=ContactIntelligenceSnapshot)
def enrich_lead_contact_intelligence(lead_id: str, current_user: CurrentUser):
    require_admin(current_user)
    service = real_enrichment_service()
    result = process_enrichment(lead_id, service)
    return result["snapshot"]


@router.post("/contacts/{contact_id}/feedback", response_model=ContactIntelligenceSnapshot)
def record_contact_feedback(contact_id: str, request: ContactFeedbackRequest, current_user: CurrentUser):
    lead = require_lead(request.leadId)
    saved_snapshot = get_saved_snapshot(request.leadId)
    if not saved_snapshot:
        saved_snapshot = ContactIntelligenceService().build_snapshot(lead, enrich=False)

    snapshot = ContactIntelligenceService().apply_feedback(
        saved_snapshot,
        contact_id,
        request.feedbackType,
        request.notes,
    )
    return save_snapshot(snapshot)


@router.get("/queue/estimate")
def estimate_contact_enrichment_queue(current_user: CurrentUser, mode: str = Query("missing")):
    require_admin(current_user)
    service = real_enrichment_service()
    eligible = eligible_missing_leads() if mode in {"missing", "refresh"} else []
    return {
        "mode": mode,
        "eligibleCount": len(eligible),
        "maxBatch": TEST_BATCH_LIMIT,
        "provider": service.provider_name,
        "providerConfigured": service.provider_configured(),
        "autoEnrichmentEnabled": os.getenv("CONTACT_AUTO_ENRICHMENT_ENABLED", "false").lower() == "true",
        "message": "Paid enrichment provider not configured." if not service.provider_configured() else "Ready for a 10-lead test batch.",
    }


@router.post("/enrich-missing", response_model=ContactBatchResult)
def enrich_missing_contacts(current_user: CurrentUser):
    require_admin(current_user)
    service = real_enrichment_service()
    eligible = eligible_missing_leads()
    if not service.provider_configured():
        return build_batch_result(service, len(eligible), [], "Paid enrichment provider not configured.")

    lead_ids = eligible[:TEST_BATCH_LIMIT]
    results = [process_enrichment(lead_id, service) for lead_id in lead_ids]
    return build_batch_result(service, len(eligible), results, f"Processed {len(results)} of {len(eligible)} eligible leads.")


@router.post("/enrich-selected", response_model=ContactBatchResult)
def enrich_selected_contacts(request: ContactBatchRequest, current_user: CurrentUser):
    require_admin(current_user)
    service = real_enrichment_service()
    lead_ids = [lead_id for lead_id in dict.fromkeys(request.leadIds) if lead_id]
    if len(lead_ids) > TEST_BATCH_LIMIT:
        raise HTTPException(status_code=400, detail=f"Run at most {TEST_BATCH_LIMIT} leads during the test batch")

    if not service.provider_configured():
        return build_batch_result(service, len(lead_ids), [], "Paid enrichment provider not configured.")

    results = [process_enrichment(lead_id, service) for lead_id in lead_ids]
    return build_batch_result(service, len(lead_ids), results, f"Processed {len(results)} selected leads.")
