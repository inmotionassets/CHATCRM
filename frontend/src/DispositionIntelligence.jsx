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
const propertyTypeOptions = [
  { label: "All Types", value: "" },
  { label: "Vacant Land", value: "vacant land" },
  { label: "Residential Lot", value: "residential lot" },
  { label: "Commercial", value: "commercial" },
  { label: "Builder Lots", value: "builder lots" }
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
  const [mapFilters, setMapFilters] = React.useState({
    propertyType: "",
    builderOnly: false,
    repeatBuyers: false,
    entityPurchases: false
  });
  const [workspace, setWorkspace] = React.useState(null);
  const [selectedSaleId, setSelectedSaleId] = React.useState("");
  const [selectedBuyerKey, setSelectedBuyerKey] = React.useState("");
  const [selectedIntelReason, setSelectedIntelReason] = React.useState(null);
  const [message, setMessage] = React.useState("Loading Disposition Intelligence...");
  const [sourceMessage, setSourceMessage] = React.useState("");
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [isUploading, setIsUploading] = React.useState(false);
  const csvInputRef = React.useRef(null);

  const selectedLead = dealOptions.find((lead) => lead.id === selectedLeadId) || dealOptions[0] || null;
  const visibleTransactions = React.useMemo(
    () => filterTransactionsForMap(workspace?.transactions || [], mapFilters, selectedBuyerKey),
    [workspace?.transactions, mapFilters, selectedBuyerKey]
  );
  const selectedSale =
    visibleTransactions.find((transaction) => transaction.id === selectedSaleId) ||
    workspace?.transactions?.find((transaction) => transaction.id === selectedSaleId) ||
    visibleTransactions[0] ||
    workspace?.transactions?.[0] ||
    null;
  const selectedBuyerFootprint =
    workspace?.buyerFootprints?.[selectedBuyerKey] ||
    workspace?.buyerFootprints?.[normalizeBuyerKey(selectedSale?.buyerName)] ||
    null;
  const marketMap = workspace?.marketIntelligence?.map || {};

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

      setMessage("Loading market intelligence...");
      try {
        const result = await fetchDispositionWorkspace(selectedLead.id, filters, authToken);
        if (cancelled) return;
        setWorkspace(result);
        setSelectedSaleId(result.transactions?.[0]?.id || "");
        setSelectedBuyerKey("");
        setSelectedIntelReason(result.marketIntelligence?.opportunityScore?.reasons?.[0] || null);
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

  function updateMapFilter(field, value) {
    setMapFilters((current) => ({ ...current, [field]: value }));
  }

  function clearBuyerHighlight() {
    setSelectedBuyerKey("");
  }

  async function reloadWorkspace(nextMessage = "Loading market intelligence...", nextFilters = filters) {
    if (!authToken || !selectedLead?.id) return;
    setMessage(nextMessage);
    const result = await fetchDispositionWorkspace(selectedLead.id, nextFilters, authToken);
    setWorkspace(result);
    setSelectedSaleId(result.transactions?.[0]?.id || "");
    setSelectedBuyerKey("");
    setSelectedIntelReason(result.marketIntelligence?.opportunityScore?.reasons?.[0] || null);
    setMessage("");
  }

  async function handleRefresh() {
    if (!selectedLead?.id || isRefreshing) return;
    setIsRefreshing(true);
    setSourceMessage("");
    try {
      const result = await refreshDispositionWorkspace(selectedLead.id, filters, authToken);
      setSourceMessage(`Refreshed ${result.transactionCount || 0} records from ${result.sourceName || result.provider}.`);
      await reloadWorkspace("Refreshing market intelligence...");
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
      await reloadWorkspace("Loading imported market intelligence...", csvFilters);
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
    <div className="panel wide-panel disposition-workspace market-intelligence-workspace">
      <div className="panel-header disposition-header">
        <div>
          <p className="eyebrow">LEGACY Market Intelligence</p>
          <h2>Market Intelligence Map</h2>
          <p className="subtle-copy">Open the market first: who is most likely to buy this property, and why?</p>
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
          <MarketIntelligencePanel
            intelligence={workspace.marketIntelligence}
            onSelectReason={setSelectedIntelReason}
            selectedReason={selectedIntelReason}
          />

          <section className="market-map-layout">
            <BuyerActivityMap
              filters={workspace.filters}
              mapFilters={mapFilters}
              mapSnapshot={marketMap}
              onClearBuyerHighlight={clearBuyerHighlight}
              onSelectBuyer={setSelectedBuyerKey}
              onSelectSale={setSelectedSaleId}
              onUpdateFilter={updateFilter}
              onUpdateMapFilter={updateMapFilter}
              selectedBuyerFootprint={selectedBuyerFootprint}
              selectedBuyerKey={selectedBuyerKey}
              selectedSale={selectedSale}
              subject={workspace.subject}
              transactions={visibleTransactions}
            />
            <aside className="market-side-rail">
              <RankedBuyerMatches
                matches={workspace.buyerMatches}
                onSelectBuyer={setSelectedBuyerKey}
                onSelectReason={setSelectedIntelReason}
                selectedBuyerKey={selectedBuyerKey}
              />
              <BuyerFootprintDrawer footprint={selectedBuyerFootprint} highlight={marketMap.buyerHighlights?.[selectedBuyerKey]} />
            </aside>
          </section>

          <DealIntelligenceCards items={workspace.dealIntelligenceSummary || []} />

          <section className="disposition-support-grid">
            <SubjectPropertyPanel readiness={workspace.readiness} subject={workspace.subject} />
            <DispositionOverview overview={workspace.overview} />
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

function MarketIntelligencePanel({ intelligence, onSelectReason, selectedReason }) {
  const opportunity = intelligence?.opportunityScore;
  if (!opportunity) return null;
  const activeReason = selectedReason || opportunity.reasons?.[0];
  return (
    <section className="market-intelligence-panel premium-intelligence-panel">
      <div className="opportunity-score-block">
        <p className="eyebrow">Opportunity</p>
        <strong>{opportunity.score}</strong>
        <span>{opportunity.grade}</span>
      </div>
      <div className="market-summary-block">
        <h3>What LEGACY knows</h3>
        <p>{intelligence.summary}</p>
        <div className="opportunity-reason-list clickable-reasons">
          {(opportunity.reasons || []).slice(0, 6).map((reason) => (
            <button
              className={activeReason?.label === reason.label ? "active" : ""}
              key={reason.label}
              onClick={() => onSelectReason?.(reason)}
              type="button"
            >
              {reason.label} +{reason.points}
            </button>
          ))}
        </div>
      </div>
      {activeReason ? (
        <div className="reason-evidence-panel">
          <span>Evidence</span>
          <strong>{activeReason.label}</strong>
          <p>{activeReason.detail}</p>
        </div>
      ) : null}
    </section>
  );
}

function DealIntelligenceCards({ items }) {
  if (!items?.length) return null;
  return (
    <div className="deal-intelligence-grid intelligence-card-grid">
      {items.map((item) => (
        <article className="deal-intelligence-card evidence-card" key={item.label}>
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
    <section className="disposition-panel overview-panel">
      <div>
        <p className="eyebrow">Market Totals</p>
        <h3>Snapshot Metrics</h3>
      </div>
      <div className="disposition-overview-grid">
        {items.map(([label, value]) => (
          <article className="stat compact-stat" key={label}>
            <p>{label}</p>
            <strong>{value}</strong>
          </article>
        ))}
      </div>
    </section>
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

function BuyerActivityMap({
  filters,
  mapFilters,
  mapSnapshot,
  onClearBuyerHighlight,
  onSelectBuyer,
  onSelectSale,
  onUpdateFilter,
  onUpdateMapFilter,
  selectedBuyerFootprint,
  selectedBuyerKey,
  selectedSale,
  subject,
  transactions
}) {
  const markerRecords = transactions.map((transaction) => ({
    transaction,
    position: markerPosition(transaction, subject, filters.radiusMiles)
  }));
  const connectorRecords = selectedBuyerKey
    ? markerRecords
        .filter((record) => normalizeBuyerKey(record.transaction.buyerName) === selectedBuyerKey)
        .sort((a, b) => String(a.transaction.saleDate || "").localeCompare(String(b.transaction.saleDate || "")))
    : [];
  const highlight = selectedBuyerKey ? mapSnapshot?.buyerHighlights?.[selectedBuyerKey] : null;

  return (
    <section className="disposition-panel activity-map-panel market-map-panel">
      <div className="map-heading market-map-heading">
        <div>
          <p className="eyebrow">Market Intelligence Map</p>
          <h3>{transactions.length} visible market signals</h3>
        </div>
        <small>{filters.radiusMiles} mile radius / {filters.soldWithinDays} days</small>
      </div>

      <MarketMapControls
        filters={filters}
        mapFilters={mapFilters}
        mapSnapshot={mapSnapshot}
        onUpdateFilter={onUpdateFilter}
        onUpdateMapFilter={onUpdateMapFilter}
      />

      {selectedBuyerKey ? (
        <div className="buyer-highlight-strip">
          <div>
            <span>Buyer Highlight Mode</span>
            <strong>{highlight?.buyerName || selectedBuyerFootprint?.entityName || selectedBuyerKey}</strong>
          </div>
          <button onClick={onClearBuyerHighlight} type="button">Show Full Market</button>
        </div>
      ) : null}

      <div className="buyer-activity-map premium-market-map" aria-label="Market intelligence map">
        <div className="map-grid-lines" />
        <div className="market-map-rings">
          <span className="ring ring-one" />
          <span className="ring ring-two" />
          <span className="ring ring-three" />
        </div>
        <svg aria-hidden="true" className="footprint-line-layer" focusable="false">
          {connectorRecords.slice(1).map((record, index) => {
            const previous = connectorRecords[index];
            return (
              <line
                key={`${previous.transaction.id}-${record.transaction.id}`}
                x1={`${previous.position.left}%`}
                x2={`${record.position.left}%`}
                y1={`${previous.position.top}%`}
                y2={`${record.position.top}%`}
              />
            );
          })}
        </svg>
        <button className="map-marker subject-marker" style={{ left: "50%", top: "50%" }} type="button">
          Deal
        </button>
        <div className="map-center-card">
          <span>Under Contract</span>
          <strong>{subject.address}</strong>
        </div>
        {markerRecords.map(({ transaction, position }) => {
          const markerType = mapMarkerType(transaction);
          return (
            <button
              className={`map-marker ${markerClass(markerType)} ${selectedSale?.id === transaction.id ? "active" : ""}`}
              key={transaction.id}
              onClick={() => {
                onSelectSale(transaction.id);
                onSelectBuyer?.(normalizeBuyerKey(transaction.buyerName));
              }}
              style={{ left: `${position.left}%`, top: `${position.top}%` }}
              title={`${transaction.buyerName || "Unknown buyer"} / ${formatMoney(transaction.salePrice)}`}
              type="button"
            >
              {markerLabel(markerType)}
            </button>
          );
        })}
      </div>

      <MapLegend legend={mapSnapshot?.markerLegend || []} />
      <FutureLayerStrip layers={mapSnapshot?.futureLayers || []} />

      {selectedSale ? (
        <SaleMarkerDrawer sale={selectedSale} onSelectBuyer={onSelectBuyer} />
      ) : (
        <div className="mini-empty"><p>No nearby sales found for these filters.</p></div>
      )}
    </section>
  );
}

function MarketMapControls({ filters, mapFilters, mapSnapshot, onUpdateFilter, onUpdateMapFilter }) {
  const timeline = mapSnapshot?.timeline || {};
  return (
    <div className="market-map-controls">
      <div className="segmented-filter">
        <span>Radius</span>
        <div>
          {radiusOptions.map((radius) => (
            <button
              className={filters.radiusMiles === radius ? "active" : ""}
              key={radius}
              onClick={() => onUpdateFilter("radiusMiles", radius)}
              type="button"
            >
              {radius}
            </button>
          ))}
        </div>
      </div>

      <div className="timeline-control">
        <div>
          <span>Timeline</span>
          <strong>{filters.soldWithinDays} days</strong>
        </div>
        <input
          aria-label="Transaction timeline"
          max={soldDateOptions.length - 1}
          min="0"
          onChange={(event) => onUpdateFilter("soldWithinDays", soldDateOptions[Number(event.target.value)] || 365)}
          step="1"
          type="range"
          value={Math.max(0, soldDateOptions.indexOf(filters.soldWithinDays))}
        />
        <small>{timeline.visibleTransactionCount || 0} records / newest {formatShortDate(timeline.newestSaleDate)}</small>
      </div>

      <label>
        Property Type
        <select value={mapFilters.propertyType} onChange={(event) => onUpdateMapFilter("propertyType", event.target.value)}>
          {propertyTypeOptions.map((option) => (
            <option key={option.value || "all"} value={option.value}>{option.label}</option>
          ))}
        </select>
      </label>

      <div className="map-toggle-group">
        <label>
          <input checked={filters.cashOnly} onChange={(event) => onUpdateFilter("cashOnly", event.target.checked)} type="checkbox" />
          Cash Only
        </label>
        <label>
          <input checked={mapFilters.builderOnly} onChange={(event) => onUpdateMapFilter("builderOnly", event.target.checked)} type="checkbox" />
          Builder Only
        </label>
        <label>
          <input checked={mapFilters.repeatBuyers} onChange={(event) => onUpdateMapFilter("repeatBuyers", event.target.checked)} type="checkbox" />
          Repeat Buyers
        </label>
        <label>
          <input checked={mapFilters.entityPurchases} onChange={(event) => onUpdateMapFilter("entityPurchases", event.target.checked)} type="checkbox" />
          Entity Purchases
        </label>
      </div>
    </div>
  );
}

function MapLegend({ legend }) {
  const fallback = [
    { type: "recorded_sale", label: "Recorded Sale" },
    { type: "cash_purchase", label: "Cash Purchase" },
    { type: "builder_purchase", label: "Builder Purchase" },
    { type: "repeat_buyer", label: "Repeat Buyer" },
    { type: "unknown_estimated", label: "Unknown / Estimated" }
  ];
  return (
    <div className="map-legend premium-map-legend">
      {(legend.length ? legend : fallback).map((item) => (
        <span key={item.type}><i className={`legend-dot ${legendClass(item.type)}`} />{item.label}</span>
      ))}
    </div>
  );
}

function FutureLayerStrip({ layers }) {
  if (!layers.length) return null;
  return (
    <div className="future-layer-strip">
      <span>Future Layers</span>
      {layers.map((layer) => (
        <button disabled key={layer.type} type="button">{layer.label}</button>
      ))}
    </div>
  );
}

function SaleMarkerDrawer({ sale, onSelectBuyer }) {
  const buyerKey = normalizeBuyerKey(sale.buyerName);
  return (
    <article className="sale-drawer market-sale-drawer">
      <div className="sale-drawer-header">
        <div>
          <p className="eyebrow">Transaction Evidence</p>
          <h3>{sale.address}</h3>
          <p>Sold {formatMoney(sale.salePrice)} on {formatShortDate(sale.saleDate)}</p>
        </div>
        <span className={`source-badge ${mapMarkerType(sale)}`}>{humanizeLabel(mapMarkerType(sale))}</span>
      </div>
      <div className="source-badge-row evidence-tags">
        {saleSourceBadges(sale).map((badge) => <span className="source-badge" key={badge}>{badge}</span>)}
        {(sale.evidenceTags || []).map((tag) => <span className="source-badge" key={tag}>{tag}</span>)}
      </div>
      <div className="subject-detail-grid sale-detail-grid">
        <DispositionMetric label="Sale Date" value={formatShortDate(sale.saleDate)} />
        <DispositionMetric label="Sale Price" value={formatMoney(sale.salePrice)} />
        <DispositionMetric label="Distance" value={`${sale.distanceMiles} mi`} />
        <DispositionMetric label="Lot Size" value={`${sale.acreage || "Unknown"} acres`} />
        <DispositionMetric label="Price/Acre" value={formatMoney(sale.pricePerAcre)} />
        <DispositionMetric label="Buyer Name" value={sale.buyerName || "Unknown"} />
        <DispositionMetric label="Buyer Entity" value={sale.buyerEntity || sale.buyerName || "Unknown"} />
        <DispositionMetric label="Source" value={sale.sourceName || sale.source || "Unknown"} />
        <DispositionMetric label="Confidence" value={`${sale.confidence || 0}%`} />
        <DispositionMetric label="Property Type" value={sale.propertyType || "Unknown"} />
      </div>
      <p className="subtle-copy">{sale.buyerMailingAddress || "Buyer mailing address missing"}</p>
      <p className="subtle-copy">{sale.sourceLastRefreshed ? `Source refreshed ${formatTimestamp(sale.sourceLastRefreshed)}` : "Source refresh date missing"}</p>
      <div className="sale-actions">
        <button onClick={() => onSelectBuyer?.(buyerKey)} type="button">View Buyer</button>
        <button onClick={() => onSelectBuyer?.(buyerKey)} type="button">Highlight Holdings</button>
        <button type="button">Match To Deal</button>
        <button disabled type="button">Skip Trace</button>
      </div>
    </article>
  );
}

function RankedBuyerMatches({ matches, onSelectBuyer, onSelectReason, selectedBuyerKey }) {
  return (
    <section className="disposition-panel ranked-buyers-panel">
      <div>
        <p className="eyebrow">Buyer Prediction</p>
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
              <div className="reason-list clickable-reasons compact-reasons">
                {(match.reasons || []).slice(0, 5).map((reason) => (
                  <button
                    key={reason}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelectReason?.({ label: match.buyerName, points: match.score, detail: reason });
                    }}
                    type="button"
                  >
                    {reason}
                  </button>
                ))}
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

function BuyerFootprintDrawer({ footprint, highlight }) {
  if (!footprint) {
    return (
      <section className="disposition-panel buyer-footprint-drawer">
        <p className="eyebrow">Buyer Footprint</p>
        <div className="mini-empty"><p>Select a ranked buyer to see their verified footprint.</p></div>
      </section>
    );
  }

  return (
    <section className="disposition-panel buyer-footprint-drawer market-footprint-drawer">
      <div>
        <p className="eyebrow">Buyer Highlight</p>
        <h3>{footprint.entityName}</h3>
        <small>{footprint.sourceConfidence || 0}% source confidence</small>
      </div>

      <div className="footprint-stat-grid">
        <DispositionMetric label="Verified Purchases" value={highlight?.verifiedPurchases ?? footprint.verifiedPurchaseCount} />
        <DispositionMetric label="Within 1 Mile" value={highlight?.purchasesWithin?.["1"] ?? footprint.purchasesByRadius?.["1"] ?? 0} />
        <DispositionMetric label="Within 3 Miles" value={highlight?.purchasesWithin?.["3"] ?? footprint.purchasesByRadius?.["3"] ?? 0} />
        <DispositionMetric label="Within 5 Miles" value={highlight?.purchasesWithin?.["5"] ?? footprint.purchasesByRadius?.["5"] ?? 0} />
        <DispositionMetric label="Within 10 Miles" value={highlight?.purchasesWithin?.["10"] ?? footprint.purchasesByRadius?.["10"] ?? 0} />
        <DispositionMetric label="Avg Purchase" value={formatMoney(highlight?.averagePurchase ?? footprint.averagePurchasePrice)} />
        <DispositionMetric label="Avg Acreage" value={highlight?.averageAcreage ?? footprint.averageAcreage ?? 0} />
        <DispositionMetric label="Avg Price/Acre" value={formatMoney(highlight?.averagePricePerAcre ?? footprint.averagePricePerAcre)} />
        <DispositionMetric label="Latest Purchase" value={formatShortDate(highlight?.latestPurchase || footprint.latestPurchaseDate)} />
        <DispositionMetric label="Buying Trend" value={trendLabel(highlight?.buyingTrend || footprint.activityTrend)} />
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

function filterTransactionsForMap(transactions = [], mapFilters = {}, selectedBuyerKey = "") {
  return transactions.filter((transaction) => {
    const buyerKey = normalizeBuyerKey(transaction.buyerName);
    const markerType = mapMarkerType(transaction);
    const propertyType = String(transaction.propertyType || "").toLowerCase();
    const buyerType = String(transaction.buyerType || "").toLowerCase();

    if (selectedBuyerKey && buyerKey !== selectedBuyerKey) return false;
    if (mapFilters.propertyType === "builder lots" && buyerType !== "builder" && !propertyType.includes("lot")) return false;
    if (mapFilters.propertyType && mapFilters.propertyType !== "builder lots" && !propertyType.includes(mapFilters.propertyType)) return false;
    if (mapFilters.builderOnly && markerType !== "builder_purchase" && buyerType !== "builder") return false;
    if (mapFilters.repeatBuyers && markerType !== "repeat_buyer") return false;
    if (mapFilters.entityPurchases && !isEntityBuyer(transaction.buyerName)) return false;
    return true;
  });
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

function mapMarkerType(transaction = {}) {
  const legacyType = transaction.marketMarkerType || transaction.markerType || "recorded_sale";
  return {
    standard: "recorded_sale",
    cash: "cash_purchase",
    builder: "builder_purchase",
    repeat: "repeat_buyer",
    issue: "unknown_estimated"
  }[legacyType] || legacyType;
}

function markerClass(type) {
  return {
    recorded_sale: "recorded-marker",
    cash_purchase: "cash-marker",
    builder_purchase: "builder-marker",
    repeat_buyer: "repeat-marker",
    unknown_estimated: "unknown-marker"
  }[type] || "recorded-marker";
}

function markerLabel(type) {
  return {
    recorded_sale: "S",
    cash_purchase: "$",
    builder_purchase: "B",
    repeat_buyer: "R",
    unknown_estimated: "?"
  }[type] || "S";
}

function legendClass(type) {
  return {
    recorded_sale: "standard",
    cash_purchase: "cash",
    builder_purchase: "builder",
    repeat_buyer: "repeat",
    unknown_estimated: "unknown"
  }[type] || "standard";
}

function isEntityBuyer(value = "") {
  return /\b(llc|inc|corp|company|co|holdings|partners|development|investments|properties|homes|builders)\b/i.test(String(value));
}

function trendLabel(trend = {}) {
  const recent = Number(trend["90"] || 0);
  const annual = Number(trend["365"] || 0);
  if (recent >= 3) return "Increasing";
  if (recent >= 1) return "Active";
  if (annual >= 1) return "Cooling";
  return "Unknown";
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
  if (mapMarkerType(sale) === "repeat_buyer") badges.push("Verified repeat buyer");
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
    .replace(/_/g, " ")
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (char) => char.toUpperCase());
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
