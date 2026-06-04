from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path
from re import sub
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from ..auth import CurrentUser

router = APIRouter(prefix="/agreements", tags=["agreements"])

CONTRACTS_PATH = Path(__file__).resolve().parents[2] / "contracts"
CONTRACTS_PATH.mkdir(exist_ok=True)


class AgreementDraft(BaseModel):
    seller_name: str
    property_address: str
    parcel_number: str = ""
    purchase_price: Decimal
    earnest_money: Decimal = Decimal("100.00")
    agreement_date: str = ""
    closing_date: str = ""
    buyer_name: str = "Virgo Davis"
    buyer_vesting: str = "and/or assigns"
    title_company: str = ""
    additional_terms: str = ""


@router.post("/generate")
def generate_agreement(draft: AgreementDraft, current_user: CurrentUser):
    file_name = build_file_name(draft.property_address)
    file_path = CONTRACTS_PATH / file_name
    build_pdf(file_path, draft)
    return {
        "file_name": file_name,
        "download_url": f"/agreements/files/{file_name}",
    }


@router.get("/files/{file_name}")
def download_agreement(file_name: str):
    safe_name = Path(file_name).name
    file_path = CONTRACTS_PATH / safe_name
    return FileResponse(file_path, media_type="application/pdf", filename=safe_name)


def build_file_name(address: str) -> str:
    safe_address = sub(r"[^A-Za-z0-9]+", "-", address).strip("-")[:64] or "property"
    return f"purchase-agreement-draft-{safe_address}-{uuid4().hex[:8]}.pdf"


def build_pdf(file_path: Path, draft: AgreementDraft) -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DraftTitle",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#18212f"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="DraftNotice",
            parent=styles["BodyText"],
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#9a3412"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="AgreementBody",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
        )
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    story = [
        Paragraph("REAL ESTATE PURCHASE AGREEMENT DRAFT", styles["DraftTitle"]),
        Spacer(1, 6),
        Paragraph(
            "DRAFT TEMPLATE FOR REVIEW. This generated document is not legal advice. "
            "Have an attorney or qualified real-estate professional confirm the correct form and terms before signing.",
            styles["DraftNotice"],
        ),
        Spacer(1, 14),
    ]

    agreement_date = draft.agreement_date or date.today().isoformat()
    data = [
        ["Agreement Date", agreement_date],
        ["Seller", draft.seller_name],
        ["Buyer", f"{draft.buyer_name} {draft.buyer_vesting}".strip()],
        ["Property Address", draft.property_address],
        ["Parcel / APN", draft.parcel_number or "To be confirmed"],
        ["Purchase Price", money(draft.purchase_price)],
        ["Earnest Money", money(draft.earnest_money)],
        ["Closing Date", draft.closing_date or "To be agreed"],
        ["Title Company / Closing Agent", draft.title_company or "To be selected"],
    ]
    table = Table(data, colWidths=[1.75 * inch, 5.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef8f5")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#176f5f")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd8d0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([table, Spacer(1, 14)])

    body = [
        "<b>1. Property.</b> Seller agrees to sell and Buyer agrees to purchase the property identified above, "
        "together with improvements and fixtures, subject to confirmation of the legal description and parcel information.",
        "<b>2. Purchase Price.</b> The purchase price and earnest-money amount are stated above. "
        "Payment method, escrow handling, and any financing terms must be confirmed before execution.",
        "<b>3. Closing.</b> Closing is targeted for the date stated above, subject to title review, mutually agreed closing instructions, and applicable addenda.",
        "<b>4. Assignment.</b> Buyer vesting is stated above. The parties should confirm any assignment rights, restrictions, disclosures, and required addenda with a qualified professional.",
        "<b>5. Condition and Due Diligence.</b> Inspection rights, option periods, access, condition, disclosures, taxes, prorations, and title objections must be completed in the appropriate state-specific contract form or addenda.",
        "<b>6. Additional Terms.</b> " + escape(draft.additional_terms or "None entered."),
    ]

    for paragraph in body:
        story.extend([Paragraph(paragraph, styles["AgreementBody"]), Spacer(1, 8)])

    story.extend(
        [
            Spacer(1, 12),
            signature_table("Seller Signature", "Date", "Buyer Signature", "Date"),
            Spacer(1, 26),
            Paragraph(
                f"Generated by ChatCRM on {datetime.now().strftime('%Y-%m-%d %H:%M')}. "
                "Use an attorney-approved or state-required contract form for execution.",
                styles["DraftNotice"],
            ),
        ]
    )
    document.build(story)


def signature_table(*labels: str) -> Table:
    table = Table([["", "", "", ""], list(labels)], colWidths=[2.3 * inch, 0.9 * inch, 2.3 * inch, 0.9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 1), (-1, 1), 0.6, colors.HexColor("#64748b")),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#475569")),
                ("TOPPADDING", (0, 1), (-1, 1), 5),
            ]
        )
    )
    return table


def money(value: Decimal) -> str:
    return f"${value:,.2f}"
