import json
import re
import sqlite3
from pathlib import Path

from app.routers.imports import decode_csv, extract_csv_leads


DATABASE_PATH = Path("chatcrm.db")
CSV_PATHS = [
    Path(r"C:\Users\vdvon\Downloads\Vacant Lots- Property Export Vacant_Land_Tax_Delinquencies.xlsx.csv"),
    Path(r"C:\Users\vdvon\Downloads\Vacant Lots- Propwire Export - 3112 Properties - Jul 21_ 2024 Full skip.xls.csv"),
]


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def address_match(left: str, right: str) -> bool:
    left_key = normalize(left)
    right_key = normalize(right)
    return bool(left_key and right_key and (left_key == right_key or left_key.startswith(right_key) or right_key.startswith(left_key)))


def merge_phones(*groups) -> list[str]:
    phones: list[str] = []
    seen: set[str] = set()

    for group in groups:
        values = group if isinstance(group, list) else ([group] if group else [])
        for phone in values:
            key = digits(phone)
            if key and key not in seen:
                seen.add(key)
                phones.append(phone)

    return phones


def main() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    rows = connection.execute("SELECT id, payload FROM leads").fetchall()
    leads = [(lead_id, json.loads(payload)) for lead_id, payload in rows]
    imported = []

    for path in CSV_PATHS:
        parsed, _warnings = extract_csv_leads(decode_csv(path.read_bytes()), path.name)
        imported.extend([lead.model_dump() for lead in parsed])

    added = 0
    updated = 0
    added_numbers = 0

    for item in imported:
        match_index = None
        for index, (_lead_id, lead) in enumerate(leads):
            if address_match(lead.get("address", ""), item.get("address", "")):
                match_index = index
                break

        if match_index is None:
            item.update(
                {
                    "id": f"csv-{normalize(item.get('address', ''))}",
                    "stage": "New Lead",
                    "score": item.get("confidence") or 70,
                    "owner": "Import Review",
                    "needsReview": True,
                    "contactStatus": "needs-review",
                    "followUpDate": "",
                    "repairBudget": "",
                    "maxOfferPercent": "70",
                    "assignmentFee": "",
                }
            )
            leads.insert(0, (item["id"], item))
            added += 1
            continue

        lead_id, lead = leads[match_index]
        before = {digits(phone) for phone in (lead.get("phones") or []) + ([lead.get("phone")] if lead.get("phone") else [])}
        phones = merge_phones(lead.get("phones") or [], lead.get("phone"), item.get("phones") or [], item.get("phone"))
        after = {digits(phone) for phone in phones}

        for field in [
            "parcelNumber",
            "county",
            "bedrooms",
            "bathrooms",
            "sqft",
            "yearBuilt",
            "lotSize",
            "estimatedArv",
            "assessedValue",
            "email",
        ]:
            if not lead.get(field) and item.get(field):
                lead[field] = item[field]

        if item.get("name") and item.get("name") != "Unknown Owner":
            lead["name"] = item["name"]

        lead["phones"] = phones
        lead["phone"] = phones[0] if phones else lead.get("phone", "")
        lead["source"] = lead.get("source") or item.get("source")
        leads[match_index] = (lead_id, lead)
        updated += 1
        added_numbers += len(after - before)

    connection.execute("DELETE FROM leads")
    connection.executemany("INSERT INTO leads (id, payload) VALUES (?, ?)", [(lead_id, json.dumps(lead)) for lead_id, lead in leads])
    connection.commit()
    connection.close()

    print(
        {
            "imported_rows": len(imported),
            "added_leads": added,
            "updated_leads": updated,
            "new_total": len(leads),
            "new_numbers_added": added_numbers,
        }
    )


if __name__ == "__main__":
    main()
