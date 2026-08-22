from __future__ import annotations

import os
import json
import re
from datetime import datetime, timezone
from hashlib import sha1
from typing import Any
from urllib import request
from urllib.parse import quote_plus

from pydantic import BaseModel, Field


BUSINESS_OWNER_PATTERN = re.compile(
    r"\b(llc|l\.l\.c\.|inc|corp|corporation|company|co\.|homes?|builders?|construction|"
    r"development|properties|investments?|realty|land|capital|holdings|partners|ventures|trust)\b",
    re.IGNORECASE,
)


class ContactSourceLink(BaseModel):
    label: str
    url: str
    sourceType: str = "public_search"
    confidence: int = 50
    notes: str = ""


class LeadContact(BaseModel):
    id: str
    leadId: str
    contactType: str = "phone"
    value: str = ""
    displayValue: str = ""
    normalizedValue: str = ""
    source: str = "existing_data"
    sourceUrl: str = ""
    sourceConfidence: int = 0
    provider: str = ""
    matchConfidence: int = 0
    ownerNameMatch: int = 0
    addressMatch: int = 0
    lineType: str = "unknown"
    phoneType: str = "unknown"
    carrier: str = ""
    isMobile: bool = False
    isLandline: bool = False
    isVoip: bool = False
    isCallable: bool = False
    isTextable: bool = False
    isPrimary: bool = False
    priorityRank: int = 99
    status: str = "unverified"
    doNotCall: bool = False
    doNotText: bool = False
    disconnected: bool = False
    wrongNumber: bool = False
    verifiedOwner: bool = False
    lastAttemptedAt: str = ""
    lastResult: str = ""
    lastVerifiedDate: str = ""
    enrichmentRunId: str = ""
    evidence: list[str] = Field(default_factory=list)
    updatedAt: str = ""


class ContactIntelligenceSnapshot(BaseModel):
    leadId: str
    ownerName: str = ""
    propertyAddress: str = ""
    provider: str = "free_public"
    status: str = "not_enriched"
    bestContact: LeadContact | None = None
    contacts: list[LeadContact] = Field(default_factory=list)
    sourceUrls: list[ContactSourceLink] = Field(default_factory=list)
    confidence: int = 0
    needsPaidSkipTrace: bool = False
    paidProviderConfigured: bool = False
    refreshRecommended: bool = False
    enrichmentRunId: str = ""
    message: str = ""
    limitations: list[str] = Field(default_factory=list)
    updatedAt: str = ""


class ContactIntelligenceProvider:
    provider_name = "base"

    def enrich_property_owner(self, lead: Any) -> ContactIntelligenceSnapshot:
        raise NotImplementedError

    def enrich_batch(self, leads: list[Any]) -> list[ContactIntelligenceSnapshot]:
        return [self.enrich_property_owner(lead) for lead in leads]

    def validate_phone(self, phone: str) -> dict[str, Any]:
        digits = normalize_phone(phone)
        is_valid = is_valid_us_phone(digits)
        return {
            "normalized": digits,
            "display": format_phone(digits) if is_valid else phone,
            "isValid": is_valid,
            "lineType": "unknown",
            "carrier": "",
        }

    def normalize_result(self, snapshot: ContactIntelligenceSnapshot) -> ContactIntelligenceSnapshot:
        return normalize_snapshot(snapshot)


class ExistingDataProvider(ContactIntelligenceProvider):
    provider_name = "existing_data"

    def enrich_property_owner(self, lead: Any) -> ContactIntelligenceSnapshot:
        lead_data = lead_to_dict(lead)
        lead_id = str(lead_data.get("id") or "")
        timestamp = current_timestamp()
        contacts: list[LeadContact] = []

        for index, phone in enumerate(extract_lead_phones(lead_data), start=1):
            validation = self.validate_phone(phone)
            digits = validation["normalized"]
            if not digits:
                continue

            is_valid = bool(validation["isValid"])
            contacts.append(
                LeadContact(
                    id=contact_id(lead_id, "phone", digits),
                    leadId=lead_id,
                    contactType="phone",
                    value=validation["display"],
                    displayValue=validation["display"],
                    normalizedValue=digits,
                    source="Imported lead data",
                    sourceConfidence=78 if is_valid else 35,
                    lineType=validation["lineType"],
                    carrier=validation["carrier"],
                    isCallable=is_valid,
                    isTextable=is_valid,
                    isPrimary=index == 1,
                    priorityRank=index,
                    status="imported" if is_valid else "needs_review",
                    evidence=[
                        "Number came from the uploaded lead data.",
                        "Free Contact Intelligence has not verified owner match or carrier.",
                    ],
                    updatedAt=timestamp,
                )
            )

        for index, email in enumerate(extract_lead_emails(lead_data), start=1):
            contacts.append(
                LeadContact(
                    id=contact_id(lead_id, "email", email.lower()),
                    leadId=lead_id,
                    contactType="email",
                    value=email,
                    displayValue=email,
                    normalizedValue=email.lower(),
                    source="Imported lead data",
                    sourceConfidence=70,
                    isPrimary=not contacts and index == 1,
                    priorityRank=50 + index,
                    status="imported",
                    evidence=[
                        "Email came from the uploaded lead data.",
                        "Free Contact Intelligence has not verified inbox ownership.",
                    ],
                    updatedAt=timestamp,
                )
            )

        snapshot = ContactIntelligenceSnapshot(
            leadId=lead_id,
            ownerName=owner_name(lead_data),
            propertyAddress=str(lead_data.get("address") or ""),
            provider=self.provider_name,
            status="existing_contacts_ready" if contacts else "no_existing_contacts",
            contacts=contacts,
            message="Existing/imported contact data is ready." if contacts else "No imported phone or email was found.",
            updatedAt=timestamp,
        )
        return normalize_snapshot(snapshot)


class FreePublicProvider(ContactIntelligenceProvider):
    provider_name = "free_public"

    def enrich_property_owner(self, lead: Any) -> ContactIntelligenceSnapshot:
        lead_data = lead_to_dict(lead)
        lead_id = str(lead_data.get("id") or "")
        sources = build_public_source_links(lead_data)
        has_business_owner = bool(BUSINESS_OWNER_PATTERN.search(owner_name(lead_data)))

        message = (
            "Free public sources are prepared. New private owner phones usually require a licensed skip-trace provider."
        )
        if has_business_owner:
            message = (
                "Free public business/entity searches are prepared. Public business phones may exist, but private owner cells usually require paid skip trace."
            )

        return ContactIntelligenceSnapshot(
            leadId=lead_id,
            ownerName=owner_name(lead_data),
            propertyAddress=str(lead_data.get("address") or ""),
            provider=self.provider_name,
            status="public_sources_ready",
            contacts=[],
            sourceUrls=sources,
            needsPaidSkipTrace=True,
            message=message,
            limitations=free_limitations(),
            updatedAt=current_timestamp(),
        )


class MockContactProvider(ContactIntelligenceProvider):
    provider_name = "mock"

    def enrich_property_owner(self, lead: Any) -> ContactIntelligenceSnapshot:
        lead_data = lead_to_dict(lead)
        lead_id = str(lead_data.get("id") or "")
        return ContactIntelligenceSnapshot(
            leadId=lead_id,
            ownerName=owner_name(lead_data),
            propertyAddress=str(lead_data.get("address") or ""),
            provider=self.provider_name,
            status="mock_ready",
            sourceUrls=build_public_source_links(lead_data),
            needsPaidSkipTrace=True,
            message="Mock provider ready. It does not create fake private phone numbers.",
            limitations=free_limitations(),
            updatedAt=current_timestamp(),
        )


class BatchDataContactProvider(ContactIntelligenceProvider):
    provider_name = "batchdata"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        endpoint: str | None = None,
        request_json: Any | None = None,
    ):
        self.api_key = (api_key if api_key is not None else os.getenv("BATCHDATA_API_KEY", "")).strip()
        self.base_url = (base_url or os.getenv("BATCHDATA_BASE_URL") or "https://api.batchdata.io").rstrip("/")
        self.endpoint = endpoint or os.getenv("BATCHDATA_SKIPTRACE_ENDPOINT") or "/skiptrace/bulk"
        self.full_url = os.getenv("BATCHDATA_SKIPTRACE_URL", "").strip()
        self.payload_style = (os.getenv("BATCHDATA_PAYLOAD_STYLE") or "array").strip().lower()
        self.request_json = request_json or self._post_json

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def enrich_property_owner(self, lead: Any) -> ContactIntelligenceSnapshot:
        lead_data = lead_to_dict(lead)
        lead_id = str(lead_data.get("id") or "")
        timestamp = current_timestamp()
        run_id = provider_run_id(lead_id, self.provider_name, timestamp)

        if not self.is_configured():
            return ContactIntelligenceSnapshot(
                leadId=lead_id,
                ownerName=owner_name(lead_data),
                propertyAddress=str(lead_data.get("address") or ""),
                provider=self.provider_name,
                status="provider_not_configured",
                sourceUrls=build_public_source_links(lead_data),
                needsPaidSkipTrace=True,
                paidProviderConfigured=False,
                enrichmentRunId=run_id,
                message="Paid enrichment provider not configured. Add BATCHDATA_API_KEY on the backend to enable real skip tracing.",
                limitations=free_limitations(),
                updatedAt=timestamp,
            )

        try:
            raw_result = self.request_json(self.build_payload(lead_data))
        except Exception as exc:
            return ContactIntelligenceSnapshot(
                leadId=lead_id,
                ownerName=owner_name(lead_data),
                propertyAddress=str(lead_data.get("address") or ""),
                provider=self.provider_name,
                status="failed",
                sourceUrls=build_public_source_links(lead_data),
                needsPaidSkipTrace=True,
                paidProviderConfigured=True,
                enrichmentRunId=run_id,
                message=f"BatchData enrichment failed: {str(exc)[:160]}",
                updatedAt=timestamp,
            )

        contacts = self.contacts_from_response(raw_result, lead_data, lead_id, run_id, timestamp)
        return ContactIntelligenceSnapshot(
            leadId=lead_id,
            ownerName=owner_name(lead_data),
            propertyAddress=str(lead_data.get("address") or ""),
            provider=self.provider_name,
            status="enriched" if contacts else "unmatched",
            contacts=contacts,
            sourceUrls=build_public_source_links(lead_data),
            needsPaidSkipTrace=not bool(contacts),
            paidProviderConfigured=True,
            enrichmentRunId=run_id,
            message="BatchData enrichment completed." if contacts else "BatchData returned no new contacts for this lead.",
            updatedAt=timestamp,
        )

    def build_payload(self, lead_data: dict[str, Any]) -> Any:
        record = build_enrichment_record(lead_data)
        if self.payload_style == "properties":
            return {"properties": [record]}
        return [record]

    def contacts_from_response(
        self,
        raw_result: Any,
        lead_data: dict[str, Any],
        lead_id: str,
        run_id: str,
        timestamp: str,
    ) -> list[LeadContact]:
        items = extract_provider_result_items(raw_result)
        contacts: list[LeadContact] = []
        owner_match = 0
        address_match = 0

        for item_index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            owner_match = max(owner_match, simple_match_score(owner_name(lead_data), coalesce(item, ["owner_name", "ownerName", "name"])))
            address_match = max(address_match, simple_match_score(str(lead_data.get("address") or ""), coalesce(item, ["address", "property_address", "propertyAddress"])))
            provider_confidence = score_to_int(coalesce(item, ["confidence_score", "confidence", "matchConfidence", "match_score"]))

            for phone_index, phone_data in enumerate(extract_provider_phone_entries(item), start=1):
                digits = normalize_phone(phone_data.get("value", ""))
                if not is_valid_us_phone(digits):
                    continue

                phone_type = str(phone_data.get("phoneType") or phone_data.get("lineType") or "unknown").lower()
                dnc = boolish(phone_data.get("dnc")) or boolish(phone_data.get("dnc_status")) or boolish(phone_data.get("doNotCall"))
                confidence = max(score_to_int(phone_data.get("confidence")), provider_confidence, 72)
                contacts.append(
                    LeadContact(
                        id=contact_id(lead_id, "phone", digits),
                        leadId=lead_id,
                        contactType="phone",
                        value=format_phone(digits),
                        displayValue=format_phone(digits),
                        normalizedValue=digits,
                        source="BatchData",
                        sourceConfidence=confidence,
                        provider=self.provider_name,
                        matchConfidence=confidence,
                        ownerNameMatch=owner_match,
                        addressMatch=address_match,
                        lineType=phone_type or "unknown",
                        phoneType=phone_type or "unknown",
                        carrier=str(phone_data.get("carrier") or ""),
                        isMobile=phone_type in {"mobile", "wireless", "cell"},
                        isLandline=phone_type in {"landline", "fixed"},
                        isVoip=phone_type == "voip",
                        isCallable=not dnc,
                        isTextable=(phone_type in {"mobile", "wireless", "cell", "unknown"}) and not dnc,
                        priorityRank=item_index * 10 + phone_index,
                        status="do_not_call" if dnc else "enriched",
                        doNotCall=dnc,
                        doNotText=dnc,
                        lastVerifiedDate=str(phone_data.get("lastVerifiedDate") or phone_data.get("last_verified_date") or timestamp),
                        enrichmentRunId=run_id,
                        evidence=[
                            "Returned by licensed BatchData enrichment.",
                            f"Owner match: {owner_match}%.",
                            f"Address match: {address_match}%.",
                        ],
                        updatedAt=timestamp,
                    )
                )

            for email_index, email_data in enumerate(extract_provider_email_entries(item), start=1):
                email = str(email_data.get("value") or "").strip().lower()
                if "@" not in email:
                    continue
                confidence = max(score_to_int(email_data.get("confidence")), provider_confidence, 65)
                contacts.append(
                    LeadContact(
                        id=contact_id(lead_id, "email", email),
                        leadId=lead_id,
                        contactType="email",
                        value=email,
                        displayValue=email,
                        normalizedValue=email,
                        source="BatchData",
                        sourceConfidence=confidence,
                        provider=self.provider_name,
                        matchConfidence=confidence,
                        ownerNameMatch=owner_match,
                        addressMatch=address_match,
                        isCallable=False,
                        isTextable=False,
                        priorityRank=60 + item_index * 10 + email_index,
                        status="enriched",
                        lastVerifiedDate=str(email_data.get("lastVerifiedDate") or email_data.get("last_verified_date") or timestamp),
                        enrichmentRunId=run_id,
                        evidence=[
                            "Returned by licensed BatchData enrichment.",
                            f"Owner match: {owner_match}%.",
                            f"Address match: {address_match}%.",
                        ],
                        updatedAt=timestamp,
                    )
                )

        return contacts

    def _post_json(self, payload: Any) -> Any:
        body = json.dumps(payload).encode("utf-8")
        api_request = request.Request(
            self.endpoint_url(),
            data=body,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(api_request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def endpoint_url(self) -> str:
        if self.full_url:
            return self.full_url
        return f"{self.base_url}/{self.endpoint.lstrip('/')}"

class ContactIntelligenceService:
    def __init__(self, provider_name: str | None = None, public_provider: ContactIntelligenceProvider | None = None):
        self.provider_name = (provider_name or os.getenv("CONTACT_INTELLIGENCE_PROVIDER") or "free_public").strip().lower()
        self.existing_provider = ExistingDataProvider()
        self.public_provider = public_provider or self._provider_for_name(self.provider_name)

    def provider_configured(self) -> bool:
        return bool(getattr(self.public_provider, "is_configured", lambda: self.provider_name in {"free_public", "mock"})())

    def build_snapshot(self, lead: Any, enrich: bool = False) -> ContactIntelligenceSnapshot:
        existing_snapshot = self.existing_provider.enrich_property_owner(lead)
        provider_snapshot = self.public_provider.enrich_property_owner(lead) if enrich else ContactIntelligenceSnapshot(
            leadId=existing_snapshot.leadId,
            ownerName=existing_snapshot.ownerName,
            propertyAddress=existing_snapshot.propertyAddress,
            provider=self.provider_name,
            updatedAt=current_timestamp(),
        )

        merged = merge_snapshots(existing_snapshot, provider_snapshot)
        if not enrich and merged.sourceUrls == []:
            merged.sourceUrls = build_public_source_links(lead_to_dict(lead))

        return normalize_snapshot(merged)

    def apply_feedback(
        self,
        snapshot: ContactIntelligenceSnapshot,
        contact_id_value: str,
        feedback_type: str,
        notes: str = "",
    ) -> ContactIntelligenceSnapshot:
        feedback = feedback_type.strip().lower().replace("-", "_")
        timestamp = current_timestamp()
        updated_contacts: list[LeadContact] = []

        for contact in snapshot.contacts:
            if contact.id != contact_id_value:
                updated_contacts.append(contact)
                continue

            updates: dict[str, Any] = {"updatedAt": timestamp, "lastResult": feedback_type}
            if feedback in {"confirmed", "confirmed_owner", "owner_confirmed"}:
                updates.update(
                    {
                        "verifiedOwner": True,
                        "status": "confirmed_owner",
                        "sourceConfidence": max(contact.sourceConfidence, 92),
                        "evidence": [*contact.evidence, "Team confirmed this contact belongs to the owner."],
                    }
                )
            elif feedback in {"wrong_number", "not_owner"}:
                updates.update(
                    {
                        "wrongNumber": True,
                        "isCallable": False,
                        "isTextable": False,
                        "status": "wrong_number",
                        "sourceConfidence": min(contact.sourceConfidence, 20),
                        "evidence": [*contact.evidence, "Team marked this as the wrong number."],
                    }
                )
            elif feedback == "disconnected":
                updates.update(
                    {
                        "disconnected": True,
                        "isCallable": False,
                        "isTextable": False,
                        "status": "disconnected",
                        "sourceConfidence": min(contact.sourceConfidence, 25),
                        "evidence": [*contact.evidence, "Team marked this contact as disconnected."],
                    }
                )
            elif feedback in {"do_not_call", "dnc"}:
                updates.update(
                    {
                        "doNotCall": True,
                        "isCallable": False,
                        "status": "do_not_call",
                        "evidence": [*contact.evidence, "Team marked this contact as do not call."],
                    }
                )
            elif feedback in {"do_not_text", "dnt"}:
                updates.update(
                    {
                        "doNotText": True,
                        "isTextable": False,
                        "status": "do_not_text",
                        "evidence": [*contact.evidence, "Team marked this contact as do not text."],
                    }
                )
            elif feedback in {"attempted", "called", "voicemail", "no_answer"}:
                updates.update({"lastAttemptedAt": timestamp, "status": feedback})

            if notes:
                updates["evidence"] = [*updates.get("evidence", contact.evidence), notes]

            updated_contacts.append(contact.model_copy(update=updates))

        phone_contacts = [contact for contact in updated_contacts if contact.contactType == "phone"]
        refresh_recommended = bool(phone_contacts) and not any(
            contact.isCallable and not contact.doNotCall and not contact.wrongNumber and not contact.disconnected
            for contact in phone_contacts
        )
        return normalize_snapshot(
            snapshot.model_copy(update={"contacts": updated_contacts, "refreshRecommended": refresh_recommended, "updatedAt": timestamp})
        )

    def _provider_for_name(self, provider_name: str) -> ContactIntelligenceProvider:
        if provider_name == "batchdata":
            return BatchDataContactProvider()
        if provider_name == "mock":
            return MockContactProvider()
        return FreePublicProvider()


def build_enrichment_record(lead_data: dict[str, Any]) -> dict[str, Any]:
    city, state, zip_code = extract_address_parts(lead_data)
    address = str(lead_data.get("address") or "").strip()
    return {
        "owner_name": owner_name(lead_data),
        "property_address": address,
        "address": address,
        "mailing_address": str(lead_data.get("mailingAddress") or lead_data.get("mailing_address") or ""),
        "apn": str(lead_data.get("parcelNumber") or lead_data.get("apn") or ""),
        "parcel_id": str(lead_data.get("parcelNumber") or lead_data.get("apn") or ""),
        "city": city,
        "state": state or "TX",
        "zip_code": zip_code,
        "county": str(lead_data.get("county") or ""),
    }


def extract_address_parts(lead_data: dict[str, Any]) -> tuple[str, str, str]:
    address = str(lead_data.get("address") or "")
    city = str(lead_data.get("city") or "").strip()
    state = str(lead_data.get("state") or "").strip()
    zip_code = str(lead_data.get("zip") or lead_data.get("zipCode") or lead_data.get("postalCode") or "").strip()

    if not zip_code:
        match = re.search(r"\b\d{5}(?:-\d{4})?\b", address)
        if match:
            zip_code = match.group(0)[:5]
    if not state and re.search(r"\bTX\b|\bTexas\b", address, re.IGNORECASE):
        state = "TX"
    if not city:
        compact = re.sub(r"\bTX\b|\bTexas\b|\b\d{5}(?:-\d{4})?\b", "", address, flags=re.IGNORECASE).strip(" ,")
        pieces = [piece.strip() for piece in compact.split(",") if piece.strip()]
        if len(pieces) >= 2:
            city = pieces[-1]
    return city, state, zip_code


def provider_run_id(lead_id: str, provider_name: str, timestamp: str) -> str:
    digest = sha1(f"{lead_id}:{provider_name}:{timestamp}".encode("utf-8")).hexdigest()[:12]
    return f"run-{digest}"


def extract_provider_result_items(raw_result: Any) -> list[dict[str, Any]]:
    if isinstance(raw_result, list):
        return [item for item in raw_result if isinstance(item, dict)]
    if not isinstance(raw_result, dict):
        return []

    for key in ["results", "data", "records", "properties", "matches"]:
        value = raw_result.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = extract_provider_result_items(value)
            if nested:
                return nested

    return [raw_result]


def extract_provider_phone_entries(item: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for key in [
        "phones",
        "phone_numbers",
        "phoneNumbers",
        "mobilePhones",
        "landlinePhones",
        "mobile_phone",
        "landline_phone",
        "phone_number",
        "phone",
    ]:
        value = item.get(key)
        if value is None:
            continue
        entries.extend(normalize_provider_contact_entries(value, key))
    return entries


def extract_provider_email_entries(item: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for key in ["emails", "email_addresses", "emailAddresses", "email"]:
        value = item.get(key)
        if value is None:
            continue
        entries.extend(normalize_provider_contact_entries(value, key))
    return entries


def normalize_provider_contact_entries(value: Any, field_name: str) -> list[dict[str, Any]]:
    if isinstance(value, list):
        entries: list[dict[str, Any]] = []
        for item in value:
            entries.extend(normalize_provider_contact_entries(item, field_name))
        return entries
    if isinstance(value, dict):
        contact_value = coalesce(value, ["value", "phone", "phoneNumber", "phone_number", "number", "email", "emailAddress"])
        if not contact_value:
            return []
        return [
            {
                **value,
                "value": contact_value,
                "phoneType": coalesce(value, ["phoneType", "phone_type", "lineType", "line_type", "type"]) or inferred_phone_type(field_name),
                "lineType": coalesce(value, ["lineType", "line_type", "phoneType", "phone_type", "type"]) or inferred_phone_type(field_name),
                "confidence": coalesce(value, ["confidence", "confidence_score", "score"]),
            }
        ]
    text_value = str(value or "").strip()
    return [{"value": text_value, "phoneType": inferred_phone_type(field_name), "lineType": inferred_phone_type(field_name)}] if text_value else []


def inferred_phone_type(field_name: str) -> str:
    lower = field_name.lower()
    if "mobile" in lower:
        return "mobile"
    if "landline" in lower:
        return "landline"
    return "unknown"


def coalesce(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", []):
            return value
    return ""


def score_to_int(value: Any) -> int:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0
    if score <= 1:
        score *= 100
    return max(0, min(100, int(round(score))))


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "dnc", "do_not_call"}


def simple_match_score(expected: str, returned: Any) -> int:
    expected_tokens = set(re.findall(r"[a-z0-9]+", str(expected or "").lower()))
    returned_tokens = set(re.findall(r"[a-z0-9]+", str(returned or "").lower()))
    if not expected_tokens or not returned_tokens:
        return 0
    overlap = expected_tokens.intersection(returned_tokens)
    return int(round((len(overlap) / max(len(expected_tokens), 1)) * 100))

def merge_snapshots(
    existing_snapshot: ContactIntelligenceSnapshot,
    provider_snapshot: ContactIntelligenceSnapshot,
) -> ContactIntelligenceSnapshot:
    contacts_by_key: dict[str, LeadContact] = {}
    for contact in [*existing_snapshot.contacts, *provider_snapshot.contacts]:
        key = f"{contact.contactType}:{contact.normalizedValue or contact.value}".lower()
        current = contacts_by_key.get(key)
        if not current or contact.sourceConfidence > current.sourceConfidence:
            contacts_by_key[key] = contact

    source_urls = dedupe_source_links([*existing_snapshot.sourceUrls, *provider_snapshot.sourceUrls])
    contacts = list(contacts_by_key.values())
    phone_contacts = [contact for contact in contacts if contact.contactType == "phone"]
    has_callable = any(
        contact.isCallable and not contact.doNotCall and not contact.wrongNumber and not contact.disconnected
        for contact in phone_contacts
    )
    all_phone_contacts_bad = bool(phone_contacts) and not has_callable
    if provider_snapshot.status in {"enriched", "provider_not_configured", "failed", "unmatched"}:
        status = provider_snapshot.status
    else:
        status = "ready" if has_callable else provider_snapshot.status or existing_snapshot.status
    needs_paid = (provider_snapshot.needsPaidSkipTrace or not has_callable) and not has_callable
    paid_configured = provider_snapshot.paidProviderConfigured or existing_snapshot.paidProviderConfigured
    refresh_recommended = all_phone_contacts_bad or provider_snapshot.refreshRecommended or existing_snapshot.refreshRecommended

    if provider_snapshot.status == "provider_not_configured":
        message = provider_snapshot.message
    elif has_callable and provider_snapshot.status == "enriched":
        message = "New provider contacts were added and ranked. Use feedback buttons to teach Contact Intelligence."
    elif has_callable:
        message = "Best existing/imported number is ready. Use feedback buttons to teach Contact Intelligence."
    elif refresh_recommended:
        message = "Every known number is unusable. Refresh enrichment is recommended."
    elif contacts:
        message = "Only partial contact data is available. A licensed skip trace may be needed for better phone coverage."
    else:
        message = provider_snapshot.message or "No contact data found. Paid skip trace is likely needed."

    return ContactIntelligenceSnapshot(
        leadId=existing_snapshot.leadId or provider_snapshot.leadId,
        ownerName=existing_snapshot.ownerName or provider_snapshot.ownerName,
        propertyAddress=existing_snapshot.propertyAddress or provider_snapshot.propertyAddress,
        provider=provider_snapshot.provider or existing_snapshot.provider,
        status=status,
        contacts=contacts,
        sourceUrls=source_urls,
        needsPaidSkipTrace=needs_paid,
        paidProviderConfigured=paid_configured,
        refreshRecommended=refresh_recommended,
        enrichmentRunId=provider_snapshot.enrichmentRunId or existing_snapshot.enrichmentRunId,
        message=message,
        limitations=free_limitations() if needs_paid or not has_callable else [],
        updatedAt=current_timestamp(),
    )


def normalize_snapshot(snapshot: ContactIntelligenceSnapshot) -> ContactIntelligenceSnapshot:
    contacts = sorted(snapshot.contacts, key=contact_sort_key)
    normalized_contacts: list[LeadContact] = []
    for index, contact in enumerate(contacts, start=1):
        normalized_contacts.append(contact.model_copy(update={"priorityRank": index, "isPrimary": index == 1}))

    best_contact = next(
        (
            contact
            for contact in normalized_contacts
            if contact.contactType == "phone"
            and contact.isCallable
            and not contact.doNotCall
            and not contact.wrongNumber
            and not contact.disconnected
        ),
        normalized_contacts[0] if normalized_contacts else None,
    )
    confidence = best_contact.sourceConfidence if best_contact else 0
    return snapshot.model_copy(update={"contacts": normalized_contacts, "bestContact": best_contact, "confidence": confidence})


def contact_sort_key(contact: LeadContact) -> tuple[int, int, str]:
    penalty = 0
    if contact.wrongNumber or contact.disconnected or contact.doNotCall:
        penalty += 100
    if contact.contactType != "phone":
        penalty += 25
    confidence_sort = 100 - int(contact.sourceConfidence or 0)
    return (penalty + confidence_sort, contact.priorityRank, contact.normalizedValue or contact.value)


def lead_to_dict(lead: Any) -> dict[str, Any]:
    if isinstance(lead, dict):
        return lead
    if hasattr(lead, "model_dump"):
        return lead.model_dump()
    if hasattr(lead, "dict"):
        return lead.dict()
    return {}


def owner_name(lead_data: dict[str, Any]) -> str:
    return str(lead_data.get("name") or lead_data.get("owner") or "").strip()


def extract_lead_phones(lead_data: dict[str, Any]) -> list[str]:
    values: list[str] = []
    phones = lead_data.get("phones")
    if isinstance(phones, list):
        values.extend(str(phone) for phone in phones)
    if lead_data.get("phone"):
        values.extend(re.split(r"[\n,;|]+", str(lead_data.get("phone"))))

    seen: set[str] = set()
    clean_values: list[str] = []
    for value in values:
        digits = normalize_phone(value)
        if not digits or digits in seen:
            continue
        seen.add(digits)
        clean_values.append(value.strip())
    return clean_values


def extract_lead_emails(lead_data: dict[str, Any]) -> list[str]:
    raw_email = str(lead_data.get("email") or "")
    values = re.split(r"[\s,;|]+", raw_email)
    seen: set[str] = set()
    emails: list[str] = []
    for value in values:
        email = value.strip()
        if not email or "@" not in email:
            continue
        key = email.lower()
        if key in seen:
            continue
        seen.add(key)
        emails.append(email)
    return emails


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def is_valid_us_phone(digits: str) -> bool:
    if len(digits) != 10:
        return False
    if digits[0] in {"0", "1"} or digits[3] in {"0", "1"}:
        return False
    if len(set(digits)) <= 2:
        return False
    return True


def format_phone(digits: str) -> str:
    if len(digits) != 10:
        return digits
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"


def contact_id(lead_id: str, contact_type: str, normalized_value: str) -> str:
    digest = sha1(f"{lead_id}:{contact_type}:{normalized_value}".encode("utf-8")).hexdigest()[:14]
    return f"ci-{digest}"


def build_public_source_links(lead_data: dict[str, Any]) -> list[ContactSourceLink]:
    owner = owner_name(lead_data)
    address = str(lead_data.get("address") or "").strip()
    county = str(lead_data.get("county") or "").lower()
    query_parts = [part for part in [owner, address, "phone email"] if part]
    links: list[ContactSourceLink] = []

    if query_parts:
        links.append(
            ContactSourceLink(
                label="Public business/contact search",
                url=f"https://www.google.com/search?q={quote_plus(' '.join(query_parts))}",
                notes="Manual public search path. LEGACY does not scrape Google results.",
            )
        )

    if owner and BUSINESS_OWNER_PATTERN.search(owner):
        links.append(
            ContactSourceLink(
                label="Texas Comptroller taxable entity search",
                url="https://comptroller.texas.gov/taxes/franchise/account-status/search.php",
                sourceType="public_business_record",
                confidence=65,
                notes="Useful for public entity status and registered business details.",
            )
        )

    if "dallas" in county or "dallas" in address.lower():
        links.append(
            ContactSourceLink(
                label="Dallas County Tax Office",
                url="https://www.dallasact.com/act_webdev/dallas/index.jsp",
                sourceType="public_tax_record",
                confidence=65,
                notes="Public tax lookup for property/account research.",
            )
        )

    if address:
        links.append(
            ContactSourceLink(
                label="Address public record search",
                url=f"https://www.google.com/search?q={quote_plus(address + ' owner phone')}",
                notes="Manual public record search path. Avoid restricted or login-only sources.",
            )
        )

    return dedupe_source_links(links)


def dedupe_source_links(links: list[ContactSourceLink]) -> list[ContactSourceLink]:
    seen: set[str] = set()
    clean_links: list[ContactSourceLink] = []
    for link in links:
        key = link.url.lower()
        if not link.url or key in seen:
            continue
        seen.add(key)
        clean_links.append(link)
    return clean_links


def free_limitations() -> list[str]:
    return [
        "Free/public sources do not reliably provide private owner cell phones.",
        "Do not bypass logins, CAPTCHAs, or restricted databases.",
        "Use a licensed skip-trace provider later for deeper phone/email coverage.",
    ]


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
