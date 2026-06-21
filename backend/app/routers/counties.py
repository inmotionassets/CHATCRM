import json
from collections import Counter

from fastapi import APIRouter
from pydantic import BaseModel

from ..auth import CurrentUser
from . import buyers as buyer_store
from . import leads as lead_store

router = APIRouter(prefix="/counties", tags=["counties"])


class CountyRecord(BaseModel):
    id: str
    state: str = "Texas"
    market: str = ""
    countyName: str
    cadUrl: str = ""
    gisUrl: str = ""
    taxUrl: str = ""
    parcelUrl: str = ""
    supportsGis: bool = True
    supportsTaxLookup: bool = True
    supportsParcelLookup: bool = True
    isActive: bool = True
    buyerImportRules: list[str] = []
    builderDetectionRules: list[str] = []
    publicContactEnrichment: list[str] = []
    parcelMapping: list[str] = []


class CountyDashboard(BaseModel):
    county: CountyRecord
    leadCount: int = 0
    parcelFound: int = 0
    gisReady: bool = False
    taxReady: bool = False
    buyerMatches: int = 0
    topOwner: str = ""
    topBuyer: str = ""
    avgBuilderScore: int = 0
    landLeadCount: int = 0


COUNTY_REGISTRY = [
    CountyRecord(
        id="tx-dallas",
        market="DFW Core",
        countyName="Dallas County",
        cadUrl="https://www.dallascad.org/",
        gisUrl="https://www.dallascad.org/",
        taxUrl="https://www.dallasact.com/act_webdev/dallas/index.jsp",
        parcelUrl="https://www.dallascad.org/SearchAddr.aspx",
    ),
    CountyRecord(
        id="tx-tarrant",
        market="DFW Core",
        countyName="Tarrant County",
        cadUrl="https://www.tad.org/",
        gisUrl="https://www.tad.org/",
        taxUrl="https://taxonline.tarrantcounty.com/TaxPayer/",
        parcelUrl="https://www.tad.org/property-search/",
    ),
    CountyRecord(
        id="tx-collin",
        market="DFW Core",
        countyName="Collin County",
        cadUrl="https://www.collincad.org/",
        gisUrl="https://www.collincad.org/maps/",
        taxUrl="https://taxpublic.collincountytx.gov/",
        parcelUrl="https://www.collincad.org/propertysearch",
    ),
    CountyRecord(
        id="tx-denton",
        market="DFW Core",
        countyName="Denton County",
        cadUrl="https://www.dentoncad.com/",
        gisUrl="https://www.dentoncad.com/",
        taxUrl="https://taxweb.dentoncounty.gov/",
        parcelUrl="https://www.dentoncad.com/",
    ),
    CountyRecord(
        id="tx-rockwall",
        market="DFW Core",
        countyName="Rockwall County",
        cadUrl="https://www.rockwallcad.com/",
        gisUrl="https://www.rockwallcad.com/",
        taxUrl="https://www.rockwallcountytexas.com/84/Tax-Office",
        parcelUrl="https://www.rockwallcad.com/",
    ),
    CountyRecord(
        id="tx-kaufman",
        market="DFW Core",
        countyName="Kaufman County",
        cadUrl="https://www.kaufman-cad.org/",
        gisUrl="https://www.kaufman-cad.org/",
        taxUrl="https://actweb.acttax.com/act_webdev/kaufman/index.jsp",
        parcelUrl="https://www.kaufman-cad.org/",
    ),
    CountyRecord(
        id="tx-harris",
        market="Houston Market",
        countyName="Harris County",
        cadUrl="https://hcad.org/",
        gisUrl="https://hcad.org/",
        taxUrl="https://www.hctax.net/Property/Overview",
        parcelUrl="https://hcad.org/property-search/",
    ),
    CountyRecord(
        id="tx-fort-bend",
        market="Houston Market",
        countyName="Fort Bend County",
        cadUrl="https://www.fbcad.org/",
        gisUrl="https://www.fbcad.org/",
        taxUrl="https://www.fortbendcountytx.gov/government/departments/tax-assessor-collector",
        parcelUrl="https://www.fbcad.org/property-search/",
    ),
    CountyRecord(
        id="tx-montgomery",
        market="Houston Market",
        countyName="Montgomery County",
        cadUrl="https://mcad-tx.org/",
        gisUrl="https://mcad-tx.org/",
        taxUrl="https://actweb.acttax.com/act_webdev/montgomery/index.jsp",
        parcelUrl="https://mcad-tx.org/property-search/",
    ),
    CountyRecord(
        id="tx-travis",
        market="Austin Market",
        countyName="Travis County",
        cadUrl="https://traviscad.org/",
        gisUrl="https://traviscad.org/",
        taxUrl="https://tax-office.traviscountytx.gov/properties/taxes",
        parcelUrl="https://traviscad.org/property-search/",
    ),
    CountyRecord(
        id="tx-williamson",
        market="Austin Market",
        countyName="Williamson County",
        cadUrl="https://www.wcad.org/",
        gisUrl="https://www.wcad.org/",
        taxUrl="https://tax.wilcotx.gov/",
        parcelUrl="https://www.wcad.org/property-search/",
    ),
    CountyRecord(
        id="tx-bexar",
        market="San Antonio Market",
        countyName="Bexar County",
        cadUrl="https://www.bcad.org/",
        gisUrl="https://www.bcad.org/",
        taxUrl="https://bexar.acttax.com/act_webdev/bexar/index.jsp",
        parcelUrl="https://www.bcad.org/property-search/",
    ),
]


DEFAULT_RULES = {
    "buyerImportRules": ["Owner/company grouping", "Mailing address grouping", "ZIP/county activity"],
    "builderDetectionRules": ["Homes/builders/construction", "Development/communities", "Properties/investments/holdings"],
    "publicContactEnrichment": ["CAD public phone", "Official tax/CAD links", "Public website/contact links only"],
    "parcelMapping": ["APN/account number", "Site address", "GIS parcel ID when available"],
}


def get_connection():
    return lead_store.get_postgres_connection() if lead_store.USE_POSTGRES else lead_store.get_sqlite_connection()


def ensure_county_table(connection) -> None:
    if lead_store.USE_POSTGRES:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS counties (
                id TEXT PRIMARY KEY,
                state TEXT NOT NULL DEFAULT '',
                county_name TEXT NOT NULL DEFAULT '',
                cad_url TEXT NOT NULL DEFAULT '',
                gis_url TEXT NOT NULL DEFAULT '',
                tax_url TEXT NOT NULL DEFAULT '',
                parcel_url TEXT NOT NULL DEFAULT '',
                supports_gis BOOLEAN NOT NULL DEFAULT true,
                supports_tax_lookup BOOLEAN NOT NULL DEFAULT true,
                supports_parcel_lookup BOOLEAN NOT NULL DEFAULT true,
                is_active BOOLEAN NOT NULL DEFAULT true,
                payload TEXT NOT NULL DEFAULT '{}'
            )
            """
        )
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS counties (
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL DEFAULT '',
            county_name TEXT NOT NULL DEFAULT '',
            cad_url TEXT NOT NULL DEFAULT '',
            gis_url TEXT NOT NULL DEFAULT '',
            tax_url TEXT NOT NULL DEFAULT '',
            parcel_url TEXT NOT NULL DEFAULT '',
            supports_gis INTEGER NOT NULL DEFAULT 1,
            supports_tax_lookup INTEGER NOT NULL DEFAULT 1,
            supports_parcel_lookup INTEGER NOT NULL DEFAULT 1,
            is_active INTEGER NOT NULL DEFAULT 1,
            payload TEXT NOT NULL DEFAULT '{}'
        )
        """
    )


def seed_counties(connection) -> None:
    ensure_county_table(connection)
    placeholder = "%s" if lead_store.USE_POSTGRES else "?"
    count = connection.execute(f"SELECT COUNT(*) FROM counties WHERE state = {placeholder}", ("Texas",)).fetchone()[0]
    if count:
        return

    for county in COUNTY_REGISTRY:
        record = county.model_copy(update=DEFAULT_RULES)
        values = (
            record.id,
            record.state,
            record.countyName,
            record.cadUrl,
            record.gisUrl,
            record.taxUrl,
            record.parcelUrl,
            record.supportsGis,
            record.supportsTaxLookup,
            record.supportsParcelLookup,
            record.isActive,
            record.model_dump_json(),
        )
        if lead_store.USE_POSTGRES:
            connection.execute(
                """
                INSERT INTO counties (
                    id, state, county_name, cad_url, gis_url, tax_url, parcel_url,
                    supports_gis, supports_tax_lookup, supports_parcel_lookup, is_active, payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                values,
            )
        else:
            connection.execute(
                """
                INSERT OR IGNORE INTO counties (
                    id, state, county_name, cad_url, gis_url, tax_url, parcel_url,
                    supports_gis, supports_tax_lookup, supports_parcel_lookup, is_active, payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )


def list_counties() -> list[CountyRecord]:
    with get_connection() as connection:
        seed_counties(connection)
        rows = connection.execute("SELECT payload FROM counties ORDER BY state, county_name").fetchall()

    counties = [CountyRecord.model_validate(lead_store.parse_saved_payload(row[0])) for row in rows]
    registry_order = {county.id: index for index, county in enumerate(COUNTY_REGISTRY)}
    return sorted(counties, key=lambda county: registry_order.get(county.id, 999))


def market_sort(market: str) -> int:
    order = ["DFW Core", "Houston Market", "Austin Market", "San Antonio Market"]
    return order.index(market) if market in order else 99


def normalize_county_name(value: str = "") -> str:
    return value.lower().replace("county", "").strip()


def county_dashboards() -> list[CountyDashboard]:
    counties = list_counties()
    leads = lead_store.list_saved_leads()
    buyers = buyer_store.list_saved_buyers()
    lead_counts = Counter(normalize_county_name(lead.county) for lead in leads)
    parcel_counts = Counter(normalize_county_name(lead.county) for lead in leads if lead.parcelNumber)
    land_counts = Counter(
        normalize_county_name(lead.county)
        for lead in leads
        if any(term in f"{lead.source} {lead.notes} {lead.lotSize}".lower() for term in ["land", "lot", "vacant"])
    )

    dashboards: list[CountyDashboard] = []
    for county in counties:
        key = normalize_county_name(county.countyName)
        county_buyers = [
            buyer
            for buyer in buyers
            if key in {normalize_county_name(item) for item in buyer.counties}
            or (key == "dallas" and (not buyer.counties or "Dallas" in buyer.counties))
        ]
        scores = [buyer.builderScore for buyer in county_buyers if buyer.builderScore]
        top_buyer = max(county_buyers, key=lambda buyer: buyer.builderScore, default=None)
        top_owner = next((lead.name for lead in leads if normalize_county_name(lead.county) == key and lead.name), "")
        dashboards.append(
            CountyDashboard(
                county=county,
                leadCount=lead_counts[key],
                parcelFound=parcel_counts[key],
                gisReady=county.supportsGis,
                taxReady=county.supportsTaxLookup,
                buyerMatches=len(county_buyers),
                topOwner=top_owner,
                topBuyer=(top_buyer.company or top_buyer.name) if top_buyer else "",
                avgBuilderScore=round(sum(scores) / len(scores)) if scores else 0,
                landLeadCount=land_counts[key],
            )
        )

    return dashboards


@router.get("", response_model=list[CountyRecord])
def get_counties(current_user: CurrentUser):
    return list_counties()


@router.get("/dashboard", response_model=list[CountyDashboard])
def get_county_dashboard(current_user: CurrentUser):
    return county_dashboards()
