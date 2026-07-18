import React from "react";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8001"
    : "https://chatcrm.onrender.com");

const radiusOptions = [1, 3, 5, 10, 25];
const soldDateOptions = [30, 90, 180, 365];
const buyerTypeOptions = [
  { label: "All Buyers", value: "" },
  { label: "Builders", value: "builder" },
  { label: "Investors", value: "investor" },
  { label: "Developers", value: "developer" }
];

export function DispositionIntelligenceView({ authToken, currentUser, leads }) {
  const dealOptions = React.useMemo(() => getDispositionLeadOptions(leads), [leads]);
  const [selectedLeadId, setSelectedLeadId] = React.useState("");
  const [filters, setFilters] = React.useState({
    radiusMiles: 5,
    soldWithinDays: 365,
    vacantLandOnly: false,
    cashOnly: false,
    buyerType: "",
    provider: ""
  });
  const [workspace, setWorkspace] = React.useState(null);
  const [selectedSaleId, setSelectedSaleId] = React.useState("");
  const [selectedBuyerKey, setSelectedBuyerKey] = React.useState("");
  const [message, setMessage] = React.useState("Loading Disposition Intelligence...");
  const [sourceMessage, setSourceMessage] = React.useState("");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const csvInputRef = React.useRef(null);

  const selectedLead = dealOptions.find((lead) => lead.id === selectedLeadId) || dealOptions[0] || null;
  const selectedSale =
    workspace?.transactions?.find((transaction) => transaction.id === selectedSaleId) ||
    workspace?.transactions?.[0] ||
    null;
  const selectedBuyerFootprint =
    workspace?.buyerFootprints?.[selectedBuyerKey] ||
    workspace?.buyerFootprints?.[normalizeBuyerKey(selectedSale?.buyerName)] ||
    null;

  React.useEffect(() => {
    if (!selectedLeadId && dealOptions[0]?.id) {
      setSelectedLeadId(dealOptions[0].id);
    }
  }, [dealOptions, selectedLeadId]);

  React.useEffect(() => {
    let cancelled = false;

    async function loadWorkspace() {
      if (!authToken || !selectedLead?.id) {
        setWorkspace(null);
        setMessage("Move a lead to Offer, Under Contract, or Closed to activate Disposition Intelligence.");
        return;
      }

      setMessage("Loading buyer activity...");
      try {
        const result = await fetchDispositionWorkspace(selectedLead.id, filters, authToken);
        if (cancelled) return;
        setWorkspace(result);
        setSelectedSaleId(result.transactions?.[0]?.id || "");
        setSelectedBuyerKey(result.buyerMatches?.[0]?.normalizedBuyerName || "");
        setMessage("");
      } catch (error) {
        if (!cancelled) {
          setWorkspace(null);
          setMessage(error.message || "Could not load Disposition Intelligence yet.");
        }
      }
    }

    loadWorkspace();
    return () => {
      cancelled = true;
    };
  }, [
    authToken,
    selectedLead?.id,
    filters.radiusMiles,
    filters.soldWithinDays,
    filters.vacantLandOnly,
    filters.cashOnly,
    filters.buyerType,
    filters.provider
  ]);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  async function reloadWorkspace(nextMessage = "Loading buyer activity...", nextFilters = filters) {
    if (!authToken || !selectedLead?.id) return;
    setMessage(nextMessage);
    const result = await fetchDispositionWorkspace(selectedLead.id, nextFilters, authToken);
    setWorkspace(result);
    setSelectedSaleId(result.transactions?.[0]?.id || "");
    setSelectedBuyerKey(result.buyerMatches?.[0]?.normalizedBuyerName || "");
    setMessage("");
  }

  async function handleRefresh() {
    if (!selectedLead?.id || isRefreshing) return;
    setIsRefreshing(true);
    setSourceMessage("");
    try {
      const result = await refreshDispositionWorkspace(selectedLead.id, filters, authToken);
      setSourceMessage(`Refreshed ${result.transactionCount || 0} records from ${result.sourceName || result.provider}.`);
      await reloadWorkspace("Refreshing buyer activity...");
    } catch (error) {
      setSourceMessage(error.message || "Could not refresh buyer activity yet.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handleCsvUpload(event) {
    const file = event.target.files?.[0];
    if (!file || isUploading) return;
    setIsUploading(true);
    setSourceMessage("");
    try {
      const result = await importDispositionCsv(file, authToken);
      const csvFilters = { ...filters, provider: "csv" };
      setFilters(csvFilters);
      setSourceMessage(`Imported ${result.importedCount || 0} new records, updated ${result.updatedCount || 0}, flagged ${result.duplicateCount || 0} duplicates.`);
      await reloadWorkspace("Loading imported buyer activity...", csvFilters);
    } catch (error) {
      setSourceMessage(error.message || "Could not import that CSV yet.");
    } finally {
      setIsUploading(false);
      event.target.value = "";
    }
  }

  if (!["Admin", "Disposition"].includes(currentUser?.role)) {
    return (
      <div className="panel wide-panel disposition-workspace">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Disposition Intelligence</p>
            <h2>Leadership Workspace</h2>
          </div>
        </div>
        <div className="mini-empty">
          <p>Buyer names, pricing strategy, and disposition actions are protected for leadership.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="panel wide-panel disposition-workspace">
      <div className="panel-header disposition-header">
        <div>
          <p className="eyebrow">Disposition Intelligence</p>
          <h2>Buyer Activity Map</h2>
          <p className="subtle-copy">Rank buyers by what they have actually purchased near the subject property.</p>
        </div>
        <div className="disposition-controls">
          <label>
            Deal
            <select value={selectedLead?.id || ""} onChange={(event) => setSelectedLeadId(event.target.value)}>
              {dealOptions.map((lead) => (
                <option key={lead.id} value={lead.id}>
                  {lead.address || lead.name || "Unnamed Deal"}
                </option>
              ))}
            </select>
          </label>
          <label>
            Radius
            <select value={filters.radiusMiles} onChange={(event) => updateFilter("radiusMiles", Number(event.target.value))}>
              {radiusOptions.map((radius) => (
                <option key={radius} value={radius}>{radius} mi</option>
              ))}
            </select>
          </label>
          <label>
            Sold Within
            <select value={filters.soldWithinDays} onChange={(event) => updateFilter("soldWithinDays", Number(event.target.value))}>
              {soldDateOptions.map((days) => (
                <option key={days} value={days}>{days} days</option>
              ))}
            </select>
          </label>
          <button className="disposition-tool-button" disabled={!selectedLead?.id || isRefreshing} onClick={handleRefresh} type="button">
            {isRefreshing ? "Refreshing" : "Refresh Activity"}
          </button>
          <button className="disposition-tool-button primary" disabled={isUploading} onClick={() => csvInputRef.current?.click()} type="button">
            {isUploading ? "Uploading" : "Upload CSV"}
          </button>
          <input accept=".csv" className="hidden-file-input" onChange={handleCsvUpload} ref={csvInputRef} type="file" />
        </div>
      </div>

      {message ? <p className="parcel-message">{message}</p> : null}
      {sourceMessage ? <p className="parcel-message soft-message">{sourceMessage}</p> : null}

      {workspace ? (
        <>
          <SourceStatusPanel source={workspace.source} />
          <DispositionOverview overview={workspace.overview} />
          <DealIntelligenceCards items={workspace.dealIntelligenceSummary || []} />

          <div className="disposition-filter-row">
            <label>
              <input
                checked={filters.vacantLandOnly}
                onChange={(event) => updateFilter("vacantLandOnly", event.target.checked)}
                type="checkbox"
              />
              Vacant land
            </label>
            <label>
              <input
                checked={filters.cashOnly}
                onChange={(event) => updateFilter("cashOnly", event.target.checked)}
                type="checkbox"
              />
              Cash sales
            </label>
            <label>
              Buyer Type
              <select value={filters.buyerType} onChange={(event) => updateFilter("buyerType", event.target.value)}>
                {buyerTypeOptions.map((option) => (
                  <option key={option.value || "all"} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
          </div>

          <section className="disposition-grid-layout">
            <SubjectPropertyPanel readiness={workspace.readiness} subject={workspace.subject} />
            <BuyerActivityMap
              filters={workspace.filters}
              onSelectBuyer={setSelectedBuyerKey}
              onSelectSale={setSelectedSaleId}
              selectedBuyerKey={selectedBuyerKey}
              selectedSale={selectedSale}
              subject={workspace.subject}
              transactions={workspace.transactions}
            />
            <div className="buyer-footprint-column">
              <RankedBuyerMatches matches={workspace.buyerMatches} onSelectBuyer={setSelectedBuyerKey} selectedBuyerKey={selectedBuyerKey} />
              <BuyerFootprintDrawer footprint={selectedBuyerFootprint} />
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

function SourceStatusPanel({ source }) {
  if (!source) return null;
  return (
    <section className="source-status-panel">
      <div>
        <p className="eyebrow">Data Source</p>
        <strong>{source.sourceName || "Mock buyer activity"}</strong>
        <small>{source.lastRefreshAt ? `Last refreshed ${formatTimestamp(source.lastRefreshAt)}` : "Waiting for first refresh"}</small>
      </div>
      <span className={`source-badge ${source.provider || "mock"}`}>{source.provider || "mock"}</span>
      {(source.errors || []).length ? (
        <div className="source-errors">
          {source.errors.map((error) => <span key={error}>{error}</span>)}
        </div>
      ) : null}
    </section>
  );
}

function DealIntelligenceCards({ items }) {
  if (!items?.length) return null;
  return (
    <div className="deal-intelligence-grid">
      {items.map((item) => (
        <article className="deal-intelligence-card" key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          <p>{item.detail}</p>
        </article>
      ))}
    </div>
  );
}

function DispositionOverview({ overview }) {
  const items = [
    ["Nearby Buyers", overview.verifiedNearbyBuyers],
    ["High Matches", overview.highMatchBuyers],
    ["Active Builders", overview.activeBuilders],
    ["Similar Sales", overview.recentSimilarSales],
    ["Avg Price/Acre", formatMoney(overview.averagePricePerAcre)],
    ["Projected Spread", formatMoney(overview.estimatedAssignmentSpread)]
  ];

  return (
    <div className="disposition-overview-grid">
      {items.map(([label, value]) => (
        <article className="stat compact-stat" key={label}>
          <p>{label}</p>
          <strong>{value}</strong>
        </article>
      ))}
    </div>
  );
}

function SubjectPropertyPanel({ readiness, subject }) {
  return (
    <section className="disposition-panel subject-panel">
      <div>
        <p className="eyebrow">Subject Property</p>
        <h3>{subject.address}</h3>
        <small>{subject.county || "County needed"} / {subject.propertyType || "Property type needed"}</small>
      </div>

      <div className="subject-detail-grid">
        <DispositionMetric label="APN" value={subject.apn || "Missing"} />
        <DispositionMetric label="Acreage" value={subject.acreage || "Missing"} />
        <DispositionMetric label="Contract" value={formatMoney(subject.contractPrice)} />
        <DispositionMetric label="Target" value={formatMoney(subject.targetAssignmentPrice)} />
        <DispositionMetric label="Spread" value={formatMoney(subject.projectedSpread)} />
        <DispositionMetric label="Utilities" value={subject.utilities || "Unknown"} />
      </div>

      <div className="readiness-list">
        <p className="eyebrow">Deal Readiness</p>
        {readiness.map((item) => (
          <span className={item.complete ? "ready" : ""} key={item.label}>
            <span className={`status-dot ${item.complete ? "green" : "orange"}`} />
            {item.label}
          </span>
        ))}
      </div>
    </section>
  );
}

function BuyerActivityMap({ filters, onSelectBuyer, onSelectSale, selectedBuyerKey, selectedSale, subject, transactions }) {
  return (
    <section className="disposition-panel activity-map-panel">
      <div className="map-heading">
        <div>
          <p className="eyebrow">Buyer Activity Map</p>
          <h3>{transactions.length} nearby sale markers</h3>
        </div>
        <small>{filters.radiusMiles} mile radius / {filters.soldWithinDays} days</small>
      </div>

      <div className="buyer-activity-map" aria-label="Mock buyer activity map">
        <div className="map-grid-lines" />
        <button className="map-marker subject-marker" style={{ left: "50%", top: "50%" }} type="button">
          Subject
        </button>
        {transactions.map((transaction) => {
          const position = markerPosition(transaction, subject, filters.radiusMiles);
          return (
            <button
              className={`map-marker ${markerClass(transaction.markerType)} ${selectedSale?.id === transaction.id ? "active" : ""} ${selectedBuyerKey && normalizeBuyerKey(transaction.buyerName) === selectedBuyerKey ? "footprint-active" : ""} ${selectedBuyerKey && normalizeBuyerKey(transaction.buyerName) !== selectedBuyerKey ? "footprint-dim" : ""}`}
              key={transaction.id}
              onClick={() => {
                onSelectSale(transaction.id);
                onSelectBuyer?.(normalizeBuyerKey(transaction.buyerName));
              }}
              style={{ left: `${position.left}%`, top: `${position.top}%` }}
              type="button"
            >
              {markerLabel(transaction.markerType)}
            </button>
          );
        })}
      </div>

      <div className="map-legend">
        <span><i className="legend-dot standard" />Recorded sale</span>
        <span><i className="legend-dot cash" />Cash investor</span>
        <span><i className="legend-dot builder" />Builder</span>
        <span><i className="legend-dot repeat" />Repeat buyer</span>
        <span><i className="legend-dot issue" />Estimated / review</span>
      </div>

      {selectedSale ? <SaleMarkerDrawer sale={selectedSale} /> : <div className="mini-empty"><p>No nearby sales found for these filters.</p></div>}
    </section>
  );
}

function SaleMarkerDrawer({ sale }) {
  return (
    <article className="sale-drawer">
      <div>
        <h3>{sale.address}</h3>
        <p>Sold {formatMoney(sale.salePrice)} on {formatShortDate(sale.saleDate)}</p>
      </div>
      <div className="source-badge-row">
        {saleSourceBadges(sale).map((badge) => <span className="source-badge" key={badge}>{badge}</span>)}
      </div>
      <div className="subject-detail-grid">
        <DispositionMetric label="Lot Size" value={`${sale.acreage || "Unknown"} acres`} />
        <DispositionMetric label="Price/Acre" value={formatMoney(sale.pricePerAcre)} />
        <DispositionMetric label="Distance" value={`${sale.distanceMiles} mi`} />
        <DispositionMetric label="Buyer" value={sale.buyerName} />
        <DispositionMetric label="Source" value={sale.sourceName || sale.source || "Unknown"} />
        <DispositionMetric label="Quality" value={`${humanizeLabel(sale.dataQuality || "estimated")} / ${sale.confidence || 0}%`} />
        <DispositionMetric label="Deed" value={sale.deedType || "Unknown"} />
        <DispositionMetric label="Financing" value={sale.financingType || "Unknown"} />
      </div>
      <p className="subtle-copy">{sale.buyerMailingAddress || "Buyer mailing address missing"}</p>
      <p className="subtle-copy">{sale.sourceLastRefreshed ? `Source refreshed ${formatTimestamp(sale.sourceLastRefreshed)}` : "Source refresh date missing"}</p>
      <div className="sale-actions">
        <button type="button">Add Buyer</button>
        <button type="button">View Buyer Profile</button>
        <button type="button">Match to Deal</button>
      </div>
    </article>
  );
}

function RankedBuyerMatches({ matches, onSelectBuyer, selectedBuyerKey }) {
  return (
    <section className="disposition-panel ranked-buyers-panel">
      <div>
        <p className="eyebrow">Ranked Buyers</p>
        <h3>Best Buyers For This Deal</h3>
      </div>
      {matches.length ? (
        <div className="ranked-buyer-list">
          {matches.slice(0, 6).map((match, index) => (
            <article
              className={`ranked-buyer-card ${selectedBuyerKey === match.normalizedBuyerName ? "active" : ""}`}
              key={match.normalizedBuyerName}
              onClick={() => onSelectBuyer?.(match.normalizedBuyerName)}
            >
              <div className="ranked-buyer-top">
                <strong>{index + 1}. {match.buyerName}</strong>
                <span>{match.score}% Match</span>
              </div>
              <p>{match.nearbyPurchases} nearby purchases / {match.totalVerifiedPurchases} verified total</p>
              <small>Average purchase {formatMoney(match.averagePurchasePrice)} / {match.averageAcreage} acres</small>
              <div className="score-breakdown">
                {Object.entries(match.scoreBreakdown || {}).map(([label, value]) => (
                  <span key={label}>{humanizeLabel(label)} {value}</span>
                ))}
              </div>
              <div className="reason-list">
                {(match.reasons || []).slice(0, 4).map((reason) => <span key={reason}>{reason}</span>)}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="mini-empty"><p>No ranked buyers found for these filters.</p></div>
      )}
    </section>
  );
}

function BuyerFootprintDrawer({ footprint }) {
  if (!footprint) {
    return (
      <section className="disposition-panel buyer-footprint-drawer">
        <p className="eyebrow">Buyer Footprint</p>
        <div className="mini-empty"><p>Select a ranked buyer to see their footprint.</p></div>
      </section>
    );
  }

  return (
    <section className="disposition-panel buyer-footprint-drawer">
      <div>
        <p className="eyebrow">Buyer Footprint</p>
        <h3>{footprint.entityName}</h3>
        <small>{footprint.sourceConfidence || 0}% source confidence</small>
      </div>

      <div className="footprint-stat-grid">
        <DispositionMetric label="Verified Buys" value={footprint.verifiedPurchaseCount} />
        <DispositionMetric label="Within 1 Mile" value={footprint.purchasesByRadius?.["1"] || 0} />
        <DispositionMetric label="Within 5 Miles" value={footprint.purchasesByRadius?.["5"] || 0} />
        <DispositionMetric label="Cash %" value={`${footprint.cashPurchasePercentage || 0}%`} />
        <DispositionMetric label="Avg Price" value={formatMoney(footprint.averagePurchasePrice)} />
        <DispositionMetric label="Avg Acreage" value={footprint.averageAcreage || 0} />
      </div>

      <div className="footprint-chip-group">
        {(footprint.intentSignals || []).map((signal) => <span key={signal}>{signal}</span>)}
      </div>

      <div className="footprint-section">
        <strong>Why this buyer matters</strong>
        <p>{footprint.matchExplanation}</p>
      </div>

      <div className="footprint-section">
        <strong>Corridor Evidence</strong>
        {(footprint.corridorSignals || []).length ? (
          footprint.corridorSignals.map((signal) => (
            <p key={signal.label}>{signal.label}: {signal.detail}</p>
          ))
        ) : (
          <p>No corridor signal yet.</p>
        )}
      </div>

      <div className="footprint-section">
        <strong>Aliases</strong>
        {(footprint.aliases || []).slice(0, 4).map((alias) => (
          <p key={alias.alias}>{alias.alias} / {alias.confidence}% / {alias.reason}</p>
        ))}
      </div>

      <div className="sale-actions">
        <button type="button">Add to Outreach</button>
        <button type="button">Match to Deal</button>
        <button type="button">Exclude from Deal</button>
      </div>
    </section>
  );
}

function DispositionMetric({ label, value }) {
  return (
    <div className="disposition-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

async function refreshDispositionWorkspace(leadId, filters, token) {
  const params = new URLSearchParams({
    radiusMiles: String(filters.radiusMiles || 5),
    soldWithinDays: String(filters.soldWithinDays || 365),
    vacantLandOnly: String(Boolean(filters.vacantLandOnly)),
    cashOnly: String(Boolean(filters.cashOnly))
  });

  if (filters.buyerType) {
    params.append("buyerType", filters.buyerType);
  }
  if (filters.provider) {
    params.append("provider", filters.provider);
  }

  const response = await fetch(`${apiBaseUrl}/disposition/workspace/${encodeURIComponent(leadId)}/refresh?${params}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (!response.ok) {
    throw new Error("Could not refresh buyer activity.");
  }

  return response.json();
}

async function importDispositionCsv(file, token) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("source_name", "Dallas County CSV Import");

  const response = await fetch(`${apiBaseUrl}/disposition/transactions/import-csv`, {
    body: formData,
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (!response.ok) {
    throw new Error("Could not import the transaction CSV.");
  }

  return response.json();
}

async function fetchDispositionWorkspace(leadId, filters, token) {
  const params = new URLSearchParams({
    radiusMiles: String(filters.radiusMiles || 5),
    soldWithinDays: String(filters.soldWithinDays || 365),
    vacantLandOnly: String(Boolean(filters.vacantLandOnly)),
    cashOnly: String(Boolean(filters.cashOnly))
  });

  if (filters.buyerType) {
    params.append("buyerType", filters.buyerType);
  }
  if (filters.provider) {
    params.append("provider", filters.provider);
  }

  const response = await fetch(`${apiBaseUrl}/disposition/workspace/${encodeURIComponent(leadId)}?${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });

  if (response.status === 403) {
    throw new Error("Disposition Intelligence is protected for leadership.");
  }
  if (!response.ok) {
    throw new Error("Disposition Intelligence is not ready yet.");
  }

  return response.json();
}

function getDispositionLeadOptions(leads = []) {
  const preferred = leads.filter((lead) => isDispositionReadyLead(lead));
  return preferred.length ? preferred : leads.slice(0, 12);
}

function isDispositionReadyLead(lead = {}) {
  const text = `${lead.stage || ""} ${lead.contactStatus || ""} ${lead.notes || ""}`.toLowerCase();
  return ["offer", "contract", "closed", "hot", "confirmed"].some((signal) => text.includes(signal));
}

function markerPosition(transaction, subject, radiusMiles) {
  const subjectLat = Number(subject?.coordinates?.lat) || 0;
  const subjectLng = Number(subject?.coordinates?.lng) || 0;
  const markerLat = Number(transaction?.coordinates?.lat) || subjectLat;
  const markerLng = Number(transaction?.coordinates?.lng) || subjectLng;
  const milesNorth = (markerLat - subjectLat) * 69;
  const milesEast = (markerLng - subjectLng) * Math.cos((subjectLat * Math.PI) / 180) * 69;
  const scale = Math.max(Number(radiusMiles) || 5, 1);
  return {
    left: clamp(50 + (milesEast / scale) * 43, 7, 93),
    top: clamp(50 - (milesNorth / scale) * 43, 7, 93)
  };
}

function normalizeBuyerKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[.,]/g, "")
    .replace(/\b(llc|l l c|inc|company|co|ltd|lp|llp)\b/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function markerClass(type) {
  return {
    builder: "builder-marker",
    cash: "cash-marker",
    repeat: "repeat-marker",
    issue: "issue-marker"
  }[type] || "standard-marker";
}

function markerLabel(type) {
  return {
    builder: "B",
    cash: "$",
    repeat: "R",
    issue: "!"
  }[type] || "S";
}

function formatMoney(value) {
  const numberValue = Number(value) || 0;
  return new Intl.NumberFormat("en-US", {
    currency: "USD",
    maximumFractionDigits: 0,
    style: "currency"
  }).format(numberValue);
}

function saleSourceBadges(sale = {}) {
  const badges = [];
  if (sale.verified) badges.push("Recorded sale");
  if (sale.estimated) badges.push("Estimated sale");
  if (sale.dataQuality === "incomplete") badges.push("Incomplete record");
  if (sale.buyerMailingAddress && !Number(sale.salePrice)) badges.push("Buyer mailing record");
  if (sale.buyerType === "builder" && !sale.verified) badges.push("Inferred builder");
  if (sale.markerType === "repeat") badges.push("Verified repeat buyer");
  return [...new Set(badges.length ? badges : ["Source needs review"])];
}

function formatShortDate(value) {
  if (!value) return "date missing";
  const date = new Date(`${value}T12:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function formatTimestamp(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function humanizeLabel(value) {
  return String(value || "")
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (char) => char.toUpperCase());
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
