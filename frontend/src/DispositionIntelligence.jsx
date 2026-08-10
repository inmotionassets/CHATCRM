import React from "react";

const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8001"
    : "https://chatcrm.onrender.com");
const googleMapsEmbedApiKey = import.meta.env.VITE_GOOGLE_MAPS_EMBED_API_KEY || import.meta.env.VITE_GOOGLE_MAPS_API_KEY || "";

const radiusOptions = [1, 3, 5, 10, 25];
const soldDateOptions = [30, 90, 180, 365, 1095];
const baseMapModes = [
  { label: "Road", value: "road" },
  { label: "Satellite", value: "satellite" },
  { label: "Hybrid", value: "hybrid" },
  { label: "Street", value: "street" }
];
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
    soldWithinDays: 180,
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
  const [mapMode, setMapMode] = React.useState("road");
  const [layerVisibility, setLayerVisibility] = React.useState({
    subjectParcel: true,
    parcelBoundaries: false,
    recordedSales: true,
    cashPurchases: true,
    builders: true,
    repeatBuyers: true,
    flood: false,
    zoning: false,
    utilities: false,
    permits: false,
    construction: false,
    ownershipChanges: false
  });
  const [workspace, setWorkspace] = React.useState(null);
  const [selectedSaleId, setSelectedSaleId] = React.useState("");
  const [selectedBuyerKey, setSelectedBuyerKey] = React.useState("");
  const [selectedIntelReason, setSelectedIntelReason] = React.useState(null);
  const [message, setMessage] = React.useState("Loading Disposition Intelligence...");
  const [sourceMessage, setSourceMessage] = React.useState("");
  const [contactMessage, setContactMessage] = React.useState("");
  const [buyerContactSnapshot, setBuyerContactSnapshot] = React.useState(null);
  const [buyerProfileOpen, setBuyerProfileOpen] = React.useState(false);
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
  const selectedBuyerMatch = React.useMemo(() => {
    const buyerKey = selectedBuyerKey || normalizeBuyerKey(selectedSale?.buyerName);
    return (workspace?.buyerMatches || []).find((match) => match.normalizedBuyerName === buyerKey) || null;
  }, [workspace?.buyerMatches, selectedBuyerKey, selectedSale?.buyerName]);
  const buyerContactEntity = React.useMemo(
    () => buildBuyerContactEntity(selectedBuyerMatch, selectedSale, selectedBuyerFootprint, selectedBuyerKey),
    [selectedBuyerMatch, selectedSale, selectedBuyerFootprint, selectedBuyerKey]
  );
  const buyerContactKey = buyerContactEntity?.cacheKey || "";
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

  React.useEffect(() => {
    let cancelled = false;

    async function loadBuyerContactIntelligence() {
      if (!authToken || !buyerContactEntity?.entityName) {
        setBuyerContactSnapshot(null);
        setContactMessage("");
        return;
      }

      setContactMessage("Loading Contact Intelligence...");
      try {
        const snapshot = await fetchContactEntitySnapshot(buyerContactEntity, authToken);
        if (cancelled) return;
        setBuyerContactSnapshot(snapshot);
        setContactMessage("");
      } catch (error) {
        if (!cancelled) {
          setBuyerContactSnapshot(null);
          setContactMessage(error.message || "Contact Intelligence is not ready for this buyer yet.");
        }
      }
    }

    loadBuyerContactIntelligence();
    return () => {
      cancelled = true;
    };
  }, [authToken, buyerContactKey]);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function updateMapFilter(field, value) {
    setMapFilters((current) => ({ ...current, [field]: value }));
  }

  function toggleMapLayer(layerId, available = true) {
    if (!available) return;
    setLayerVisibility((current) => ({ ...current, [layerId]: !current[layerId] }));
  }

  function clearBuyerHighlight() {
    setSelectedBuyerKey("");
    setBuyerProfileOpen(false);
  }

  function openBuyerProfile(buyerKey = selectedBuyerKey) {
    const cleanBuyerKey = buyerKey || normalizeBuyerKey(selectedSale?.buyerName);
    if (!cleanBuyerKey) return;
    setSelectedBuyerKey(cleanBuyerKey);
    setBuyerProfileOpen(true);
  }

  function closeBuyerProfile() {
    setBuyerProfileOpen(false);
  }

  async function refreshBuyerContactProfile() {
    if (!authToken || !buyerContactEntity?.entityName) return;
    setContactMessage("Refreshing Contact Intelligence...");
    try {
      const snapshot = await fetchContactEntitySnapshot(buyerContactEntity, authToken);
      setBuyerContactSnapshot(snapshot);
      setContactMessage("Contact profile refreshed.");
    } catch (error) {
      setContactMessage(error.message || "Could not refresh Contact Intelligence yet.");
    }
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
              layerVisibility={layerVisibility}
              mapFilters={mapFilters}
              mapMode={mapMode}
              mapSnapshot={marketMap}
              onClearBuyerHighlight={clearBuyerHighlight}
              onOpenBuyerProfile={openBuyerProfile}
              onSelectBuyer={setSelectedBuyerKey}
              onSelectSale={setSelectedSaleId}
              onToggleLayer={toggleMapLayer}
              onUpdateFilter={updateFilter}
              onUpdateMapFilter={updateMapFilter}
              onUpdateMapMode={setMapMode}
              selectedBuyerFootprint={selectedBuyerFootprint}
              selectedBuyerKey={selectedBuyerKey}
              selectedSale={selectedSale}
              subject={workspace.subject}
              transactions={visibleTransactions}
            />
            <aside className="market-side-rail">
              <RankedBuyerMatches
                matches={workspace.buyerMatches}
                onOpenBuyerProfile={openBuyerProfile}
                onSelectBuyer={setSelectedBuyerKey}
                onSelectReason={setSelectedIntelReason}
                selectedBuyerKey={selectedBuyerKey}
              />
              <BuyerContactIntelligencePanel
                entity={buyerContactEntity}
                message={contactMessage}
                onOpenProfile={() => openBuyerProfile()}
                onRefresh={refreshBuyerContactProfile}
                snapshot={buyerContactSnapshot}
              />
              <BuyerFootprintDrawer footprint={selectedBuyerFootprint} highlight={marketMap.buyerHighlights?.[selectedBuyerKey]} />
            </aside>
          </section>

          <DealIntelligenceCards items={workspace.dealIntelligenceSummary || []} />

          <section className="disposition-support-grid">
            <SubjectPropertyPanel dealStatus={selectedLead?.stage || "New Lead"} readiness={workspace.readiness} subject={workspace.subject} />
            <DispositionOverview overview={workspace.overview} />
          </section>
        </>
      ) : null}

      {buyerProfileOpen ? (
        <BuyerProfileDrawer
          contactMessage={contactMessage}
          entity={buyerContactEntity}
          footprint={selectedBuyerFootprint}
          match={selectedBuyerMatch}
          onClose={closeBuyerProfile}
          onRefresh={refreshBuyerContactProfile}
          sale={selectedSale}
          snapshot={buyerContactSnapshot}
        />
      ) : null}
    </div>
  );
}

export function LeadLegacyMarketMap({ authToken, lead, onSelectBuyer, selectedBuyerKey = "" }) {
  const [filters, setFilters] = React.useState({
    radiusMiles: 5,
    soldWithinDays: 180,
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
  const [mapMode, setMapMode] = React.useState("road");
  const [layerVisibility, setLayerVisibility] = React.useState({
    subjectParcel: true,
    parcelBoundaries: false,
    recordedSales: true,
    cashPurchases: true,
    builders: true,
    repeatBuyers: true,
    flood: false,
    zoning: false,
    utilities: false,
    permits: false,
    construction: false,
    ownershipChanges: false
  });
  const [workspace, setWorkspace] = React.useState(null);
  const [selectedSaleId, setSelectedSaleId] = React.useState("");
  const [internalBuyerKey, setInternalBuyerKey] = React.useState("");
  const [message, setMessage] = React.useState("Loading LEGACY market map...");
  const [contactMessage, setContactMessage] = React.useState("");
  const [buyerContactSnapshot, setBuyerContactSnapshot] = React.useState(null);
  const [buyerProfileOpen, setBuyerProfileOpen] = React.useState(false);

  const activeBuyerKey = selectedBuyerKey || internalBuyerKey;
  const visibleTransactions = React.useMemo(
    () => filterTransactionsForMap(workspace?.transactions || [], mapFilters, activeBuyerKey),
    [workspace?.transactions, mapFilters, activeBuyerKey]
  );
  const selectedSale =
    visibleTransactions.find((transaction) => transaction.id === selectedSaleId) ||
    workspace?.transactions?.find((transaction) => transaction.id === selectedSaleId) ||
    visibleTransactions[0] ||
    workspace?.transactions?.[0] ||
    null;
  const selectedBuyerFootprint =
    workspace?.buyerFootprints?.[activeBuyerKey] ||
    workspace?.buyerFootprints?.[normalizeBuyerKey(selectedSale?.buyerName)] ||
    null;
  const selectedBuyerMatch = React.useMemo(() => {
    const buyerKey = activeBuyerKey || normalizeBuyerKey(selectedSale?.buyerName);
    return (workspace?.buyerMatches || []).find((match) => match.normalizedBuyerName === buyerKey) || null;
  }, [workspace?.buyerMatches, activeBuyerKey, selectedSale?.buyerName]);
  const buyerContactEntity = React.useMemo(
    () => buildBuyerContactEntity(selectedBuyerMatch, selectedSale, selectedBuyerFootprint, activeBuyerKey),
    [selectedBuyerMatch, selectedSale, selectedBuyerFootprint, activeBuyerKey]
  );
  const buyerContactKey = buyerContactEntity?.cacheKey || "";
  const marketMap = workspace?.marketIntelligence?.map || {};

  React.useEffect(() => {
    let cancelled = false;

    async function loadWorkspace() {
      if (!authToken || !lead?.id) {
        setWorkspace(null);
        setMessage("Open a saved lead to load the LEGACY market map.");
        return;
      }

      setMessage("Loading LEGACY market map...");
      try {
        const result = await fetchDispositionWorkspace(lead.id, filters, authToken);
        if (cancelled) return;
        setWorkspace(result);
        setSelectedSaleId(result.transactions?.[0]?.id || "");
        setInternalBuyerKey("");
        setBuyerProfileOpen(false);
        setMessage("");
      } catch (error) {
        if (!cancelled) {
          setWorkspace(null);
          setMessage(error.message || "Could not load the LEGACY market map yet.");
        }
      }
    }

    loadWorkspace();
    return () => {
      cancelled = true;
    };
  }, [
    authToken,
    lead?.id,
    filters.radiusMiles,
    filters.soldWithinDays,
    filters.vacantLandOnly,
    filters.cashOnly,
    filters.buyerType,
    filters.provider
  ]);

  React.useEffect(() => {
    let cancelled = false;

    async function loadBuyerContactIntelligence() {
      if (!authToken || !buyerContactEntity?.entityName) {
        setBuyerContactSnapshot(null);
        setContactMessage("");
        return;
      }

      setContactMessage("Loading Contact Intelligence...");
      try {
        const snapshot = await fetchContactEntitySnapshot(buyerContactEntity, authToken);
        if (cancelled) return;
        setBuyerContactSnapshot(snapshot);
        setContactMessage("");
      } catch (error) {
        if (!cancelled) {
          setBuyerContactSnapshot(null);
          setContactMessage(error.message || "Contact Intelligence is not ready for this buyer yet.");
        }
      }
    }

    loadBuyerContactIntelligence();
    return () => {
      cancelled = true;
    };
  }, [authToken, buyerContactKey]);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function updateMapFilter(field, value) {
    setMapFilters((current) => ({ ...current, [field]: value }));
  }

  function toggleMapLayer(layerId, available = true) {
    if (!available) return;
    setLayerVisibility((current) => ({ ...current, [layerId]: !current[layerId] }));
  }

  function selectBuyerKey(buyerKey = "") {
    setInternalBuyerKey(buyerKey);
    onSelectBuyer?.(buyerKey);
  }

  function clearBuyerHighlight() {
    selectBuyerKey("");
    setBuyerProfileOpen(false);
  }

  function openBuyerProfile(buyerKey = activeBuyerKey) {
    const cleanBuyerKey = buyerKey || normalizeBuyerKey(selectedSale?.buyerName);
    if (!cleanBuyerKey) return;
    selectBuyerKey(cleanBuyerKey);
    setBuyerProfileOpen(true);
  }

  async function refreshBuyerContactProfile() {
    if (!authToken || !buyerContactEntity?.entityName) return;
    setContactMessage("Refreshing Contact Intelligence...");
    try {
      const snapshot = await fetchContactEntitySnapshot(buyerContactEntity, authToken);
      setBuyerContactSnapshot(snapshot);
      setContactMessage("Contact profile refreshed.");
    } catch (error) {
      setContactMessage(error.message || "Could not refresh Contact Intelligence yet.");
    }
  }

  return (
    <section className="lead-legacy-market-map">
      {message ? <p className="parcel-message">{message}</p> : null}
      {workspace ? (
        <BuyerActivityMap
          filters={workspace.filters || filters}
          layerVisibility={layerVisibility}
          mapFilters={mapFilters}
          mapMode={mapMode}
          mapSnapshot={marketMap}
          onClearBuyerHighlight={clearBuyerHighlight}
          onOpenBuyerProfile={openBuyerProfile}
          onSelectBuyer={selectBuyerKey}
          onSelectSale={setSelectedSaleId}
          onToggleLayer={toggleMapLayer}
          onUpdateFilter={updateFilter}
          onUpdateMapFilter={updateMapFilter}
          onUpdateMapMode={setMapMode}
          selectedBuyerFootprint={selectedBuyerFootprint}
          selectedBuyerKey={activeBuyerKey}
          selectedSale={selectedSale}
          subject={workspace.subject || { address: lead?.address }}
          transactions={visibleTransactions}
        />
      ) : null}
      {buyerProfileOpen ? (
        <BuyerProfileDrawer
          contactMessage={contactMessage}
          entity={buyerContactEntity}
          footprint={selectedBuyerFootprint}
          match={selectedBuyerMatch}
          onClose={() => setBuyerProfileOpen(false)}
          onRefresh={refreshBuyerContactProfile}
          sale={selectedSale}
          snapshot={buyerContactSnapshot}
        />
      ) : null}
    </section>
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

function SubjectPropertyPanel({ dealStatus = "New Lead", readiness, subject }) {
  const isContractedDeal = isActiveContractStatus(dealStatus);
  const contractValue = isContractedDeal ? formatMoney(subject.contractPrice) : "Not under contract";
  const targetValue = isContractedDeal ? formatMoney(subject.targetAssignmentPrice) : "Set after contract";
  const assignmentValue = isContractedDeal ? formatMoney(subject.projectedSpread) : "Pending";

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
        <DispositionMetric label="Contract Price" value={contractValue} />
        <DispositionMetric label="Buyer Target" value={targetValue} />
        <DispositionMetric label="Est. Assignment Fee" value={assignmentValue} />
        <DispositionMetric label="Deal Status" value={dealStatus || "New Lead"} />
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
  layerVisibility,
  mapFilters,
  mapMode,
  mapSnapshot,
  onClearBuyerHighlight,
  onOpenBuyerProfile,
  onSelectBuyer,
  onSelectSale,
  onToggleLayer,
  onUpdateFilter,
  onUpdateMapFilter,
  onUpdateMapMode,
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
  const visibleMarkerRecords = markerRecords.filter(({ transaction }) => isTransactionLayerVisible(transaction, layerVisibility));
  const connectorRecords = selectedBuyerKey
    ? visibleMarkerRecords
        .filter((record) => normalizeBuyerKey(record.transaction.buyerName) === selectedBuyerKey)
        .sort((a, b) => String(a.transaction.saleDate || "").localeCompare(String(b.transaction.saleDate || "")))
    : [];
  const highlight = selectedBuyerKey ? mapSnapshot?.buyerHighlights?.[selectedBuyerKey] : null;
  const subjectParcel = mapSnapshot?.subjectParcel || {};
  const roadIntelligence = mapSnapshot?.roadIntelligence || {};
  const marketActivity = mapSnapshot?.marketActivitySummary || {};

  return (
    <section className="disposition-panel activity-map-panel market-map-panel">
      <div className="map-heading market-map-heading">
        <div>
          <p className="eyebrow">Market Intelligence Map</p>
          <h3>{visibleMarkerRecords.length} recently purchased parcels</h3>
        </div>
        <small>{filters.radiusMiles} mile radius / {formatTimelineLabel(filters.soldWithinDays)}</small>
      </div>

      <MarketMapControls
        filters={filters}
        layerControls={mapSnapshot?.layerControls || []}
        layerVisibility={layerVisibility}
        mapFilters={mapFilters}
        mapMode={mapMode}
        mapSnapshot={mapSnapshot}
        onToggleLayer={onToggleLayer}
        onUpdateFilter={onUpdateFilter}
        onUpdateMapFilter={onUpdateMapFilter}
        onUpdateMapMode={onUpdateMapMode}
      />

      <MapTruthStrip activity={marketActivity} dataProvenance={mapSnapshot?.dataProvenance} subject={subject} subjectParcel={subjectParcel} />
      <RoadIntelligenceCard road={roadIntelligence} />

      {selectedBuyerKey ? (
        <div className="buyer-highlight-strip">
          <div>
            <span>Buyer Highlight Mode</span>
            <strong>{highlight?.buyerName || selectedBuyerFootprint?.entityName || selectedBuyerKey}</strong>
          </div>
          <button onClick={onClearBuyerHighlight} type="button">Show Full Market</button>
        </div>
      ) : null}

      <div className={`buyer-activity-map premium-market-map map-mode-${mapMode} ${googleMapsEmbedApiKey ? "has-google-basemap" : "no-google-basemap"}`} aria-label="Market intelligence map">
        <GoogleBaseMapLayer mapMode={mapMode} selectedSale={selectedSale} subject={subject} />
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
        {layerVisibility.subjectParcel ? (
          <button className="map-marker subject-marker" style={{ left: "50%", top: "50%" }} type="button">
            Deal
          </button>
        ) : null}
        <div className="map-center-card">
          <span>{subjectParcel.boundaryType === "verified" ? "Verified Parcel" : "Subject Marker"}</span>
          <strong>{subject.address}</strong>
          <small>{subjectParcel.message || "Verified parcel boundary unavailable."}</small>
        </div>
        {visibleMarkerRecords.map(({ transaction, position }) => {
          const markerType = mapMarkerType(transaction);
          return (
            <button
              className={`map-marker ${markerClass(markerType)} ${purchaseAgeClass(transaction)} ${selectedSale?.id === transaction.id ? "active" : ""}`}
              key={transaction.id}
              onClick={() => {
                onSelectSale(transaction.id);
                onSelectBuyer?.(normalizeBuyerKey(transaction.buyerName));
              }}
              style={{ left: `${position.left}%`, top: `${position.top}%`, "--marker-opacity": transaction.visualOpacity ?? 1 }}
              title={`${transaction.buyerName || "Unknown buyer"} / ${formatMoney(transaction.salePrice)} / ${transaction.purchaseAgeLabel || "age unknown"}`}
              type="button"
            >
              {markerLabel(markerType)}
            </button>
          );
        })}
      </div>

      <MapLegend legend={mapSnapshot?.markerLegend || []} />
      <PurchaseAgeLegend items={mapSnapshot?.purchaseAgeLegend || []} />
      <FutureLayerStrip layers={mapSnapshot?.futureLayers || []} />

      {selectedSale ? (
        <SaleMarkerDrawer
          onOpenBuyerProfile={onOpenBuyerProfile}
          onSelectBuyer={onSelectBuyer}
          onViewStreet={(sale) => {
            onSelectSale(sale.id);
            onUpdateMapMode("street");
          }}
          sale={selectedSale}
        />
      ) : (
        <div className="mini-empty"><p>No nearby sales found for these filters.</p></div>
      )}
    </section>
  );
}

function MarketMapControls({
  filters,
  layerControls,
  layerVisibility,
  mapFilters,
  mapMode,
  mapSnapshot,
  onToggleLayer,
  onUpdateFilter,
  onUpdateMapFilter,
  onUpdateMapMode
}) {
  const timeline = mapSnapshot?.timeline || {};
  return (
    <div className="market-map-controls upgraded-map-controls">
      <div className="segmented-filter base-map-mode-control">
        <span>Base Map</span>
        <div>
          {baseMapModes.map((mode) => (
            <button
              className={mapMode === mode.value ? "active" : ""}
              key={mode.value}
              onClick={() => onUpdateMapMode(mode.value)}
              type="button"
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

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
          <span>Recently Purchased</span>
          <strong>{formatTimelineLabel(filters.soldWithinDays)}</strong>
        </div>
        <input
          aria-label="Transaction timeline"
          max={soldDateOptions.length - 1}
          min="0"
          onChange={(event) => onUpdateFilter("soldWithinDays", soldDateOptions[Number(event.target.value)] || 180)}
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

      <LayerControlMenu controls={layerControls} layerVisibility={layerVisibility} onToggleLayer={onToggleLayer} />
    </div>
  );
}

function LayerControlMenu({ controls, layerVisibility, onToggleLayer }) {
  if (!controls?.length) return null;
  return (
    <div className="layer-control-menu">
      <span>Layers</span>
      {controls.map((group) => (
        <div className="layer-control-group" key={group.group}>
          <strong>{group.group}</strong>
          {(group.layers || []).map((layer) => (
            <button
              className={`${layer.available ? "" : "disabled"} ${layerVisibility[layer.id] ? "active" : ""}`}
              disabled={!layer.available}
              key={layer.id}
              onClick={() => onToggleLayer(layer.id, layer.available)}
              type="button"
            >
              <i />
              {layer.label}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

function MapTruthStrip({ activity, dataProvenance, subject, subjectParcel }) {
  return (
    <div className="map-truth-strip">
      <div>
        <span>Primary Layer</span>
        <strong>Recently Purchased</strong>
        <p>{activity?.summary || "Load market activity to see recent buyers around this property."}</p>
      </div>
      <div>
        <span>Subject Parcel</span>
        <strong>{subjectParcel?.boundaryType === "verified" ? "Verified boundary" : "Marker only"}</strong>
        <p>{subjectParcel?.message || "Verified parcel boundary unavailable."}</p>
      </div>
      <div>
        <span>Location Source</span>
        <strong>{humanizeLabel(subject?.coordinateSource || "address_seed_estimate")}</strong>
        <p>{subject?.coordinateSource === "lead_record" ? "Coordinates came from lead/provider data." : "Google can map the address; overlay precision improves after verified coordinates/GIS."}</p>
      </div>
      <div>
        <span>Provider</span>
        <strong>{dataProvenance?.sourceName || "Source pending"}</strong>
        <p>{dataProvenance?.truthStandard || "Every insight should keep its source visible."}</p>
      </div>
    </div>
  );
}

function RoadIntelligenceCard({ road }) {
  if (!road) return null;
  return (
    <div className="road-intelligence-card">
      <div>
        <p className="eyebrow">Road Intelligence</p>
        <h4>{road.roadName || "Road needs review"}</h4>
        <small>{road.warning}</small>
      </div>
      <div className="road-intelligence-grid">
        <DispositionMetric label="Road Type" value={road.roadType || "Unknown"} />
        <DispositionMetric label="Paved" value={road.pavedStatus || "Needs Verification"} />
        <DispositionMetric label="Public / Private" value={road.publicPrivate || "Needs Verification"} />
        <DispositionMetric label="Frontage" value={road.estimatedFrontage || "Needs Verification"} />
        <DispositionMetric label="Visual Access" value={road.visualRoadAccess || "Review Street View"} />
        <DispositionMetric label="Legal Access" value={road.legalAccess || "Needs Verification"} />
      </div>
    </div>
  );
}

function GoogleBaseMapLayer({ mapMode, selectedSale, subject }) {
  if (!googleMapsEmbedApiKey) {
    return (
      <div className="map-basemap-placeholder">
        <strong>Google basemap needs key</strong>
        <span>Add VITE_GOOGLE_MAPS_API_KEY to unlock road, satellite, hybrid, and Street View inside this map.</span>
      </div>
    );
  }

  const target = mapMode === "street" && selectedSale?.address ? selectedSale : subject;
  const src = buildDispositionGoogleMapEmbedUrl(target, mapMode);
  return <iframe className="google-basemap-frame" loading="lazy" referrerPolicy="no-referrer-when-downgrade" src={src} title={`${mapMode} map for ${target?.address || subject?.address || "property"}`} />;
}

function PurchaseAgeLegend({ items }) {
  if (!items?.length) return null;
  return (
    <div className="purchase-age-legend">
      <span>Purchase Age</span>
      {items.map((item) => (
        <small className={`age-${item.bucket}`} key={item.bucket}>{item.label}: {item.intensity}</small>
      ))}
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

function SaleMarkerDrawer({ sale, onOpenBuyerProfile, onSelectBuyer, onViewStreet }) {
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
        <DispositionMetric label="Age" value={sale.purchaseAgeLabel || "Unknown"} />
        <DispositionMetric label="Record Type" value={sale.transactionKind || "Recorded Sale"} />
      </div>
      <p className="subtle-copy">{sale.buyerMailingAddress || "Buyer mailing address missing"}</p>
      <p className="subtle-copy">{sale.parcelOverlay?.message || "Parcel geometry is available only when a provider supplies verified boundaries."}</p>
      <TransactionProvenance provenance={sale.dataProvenance} />
      <div className="sale-actions">
        <button onClick={() => onOpenBuyerProfile?.(buyerKey)} type="button">View Buyer Profile</button>
        <button onClick={() => onSelectBuyer?.(buyerKey)} type="button">Highlight Holdings</button>
        <button type="button">Match To Deal</button>
        <button onClick={() => onOpenBuyerProfile?.(buyerKey)} type="button">Contact Intelligence</button>
        <button onClick={() => onViewStreet?.(sale)} type="button">View Street</button>
        {sale.dataProvenance?.sourceUrl ? (
          <a href={safeExternalUrl(sale.dataProvenance.sourceUrl)} rel="noreferrer" target="_blank">Open Transaction Evidence</a>
        ) : (
          <button disabled type="button">Evidence Link Pending</button>
        )}
      </div>
    </article>
  );
}

function TransactionProvenance({ provenance = {} }) {
  return (
    <details className="transaction-provenance">
      <summary>Why do we believe this?</summary>
      <div className="transaction-provenance-grid">
        <DispositionMetric label="Provider" value={provenance.provider || "Unknown"} />
        <DispositionMetric label="Source" value={provenance.sourceName || "Unknown"} />
        <DispositionMetric label="Record ID" value={provenance.sourceRecordId || "Missing"} />
        <DispositionMetric label="APN" value={provenance.apn || "Missing"} />
        <DispositionMetric label="Verified" value={humanizeLabel(provenance.verificationStatus || "estimated")} />
        <DispositionMetric label="Geometry" value={humanizeLabel(provenance.geometrySource || "missing")} />
      </div>
    </details>
  );
}

function RankedBuyerMatches({ matches, onOpenBuyerProfile, onSelectBuyer, onSelectReason, selectedBuyerKey }) {
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
              <div className="ranked-buyer-actions">
                <button
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpenBuyerProfile?.(match.normalizedBuyerName);
                  }}
                  type="button"
                >
                  Open Profile
                </button>
                <button
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectBuyer?.(match.normalizedBuyerName);
                  }}
                  type="button"
                >
                  Highlight
                </button>
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

function BuyerContactIntelligencePanel({ entity, message, onOpenProfile, onRefresh, snapshot }) {
  const contacts = Array.isArray(snapshot?.contacts) ? snapshot.contacts : [];
  const phones = contacts.filter((contact) => contact.contactType === "phone");
  const emails = contacts.filter((contact) => contact.contactType === "email");
  const bestContact = snapshot?.bestContact || contacts[0] || null;
  const health = getContactHealth(snapshot, entity);
  const sourceUrls = Array.isArray(snapshot?.sourceUrls) ? snapshot.sourceUrls : [];
  const websiteUrl = safeExternalUrl(entity?.website);
  const callHref = bestContact?.contactType === "phone" ? `tel:${normalizePhoneDigits(bestContact.normalizedValue || bestContact.value)}` : "";
  const emailHref = bestContact?.contactType === "email" ? `mailto:${bestContact.normalizedValue || bestContact.value}` : "";

  return (
    <section className="disposition-panel contact-intelligence-panel">
      <div className="contact-intelligence-heading">
        <div>
          <p className="eyebrow">Contact Intelligence</p>
          <h3>{entity?.entityName || "Select a buyer"}</h3>
          <small>Shared LEGACY contact engine for buyers, builders, LLCs, and sellers.</small>
        </div>
        <div className={`contact-health-pill ${health.level}`}>
          <strong>{health.score}%</strong>
          <span>Health</span>
        </div>
      </div>

      {entity?.entityName ? (
        <>
          <div className="contact-best-card">
            <span>Best Contact</span>
            <strong>{bestContact ? formatContactValue(bestContact) : "No verified contact saved"}</strong>
            <p>{bestContact ? `${humanizeLabel(bestContact.status || "unverified")} / ${bestContact.source || "Source needed"}` : snapshot?.message || message || "Public research paths are ready."}</p>
          </div>

          <div className="contact-health-grid">
            <DispositionMetric label="Phones" value={phones.length || "None"} />
            <DispositionMetric label="Emails" value={emails.length || "None"} />
            <DispositionMetric label="Sources" value={sourceUrls.length || "Pending"} />
            <DispositionMetric label="Status" value={contactHealthLabel(health)} />
          </div>

          <div className="contact-chip-list">
            {contacts.slice(0, 5).map((contact) => (
              <span className={contact.verifiedOwner ? "verified" : ""} key={contact.id || contact.value}>
                {formatContactValue(contact)}
              </span>
            ))}
            {!contacts.length ? <span className="needs-source">Needs enrichment</span> : null}
          </div>

          <div className="contact-actions-row">
            <a className={!callHref ? "disabled" : ""} href={callHref || undefined}>Call</a>
            <a className={!emailHref ? "disabled" : ""} href={emailHref || undefined}>Email</a>
            <a className={!websiteUrl ? "disabled" : ""} href={websiteUrl || undefined} rel="noreferrer" target="_blank">Website</a>
            <button onClick={onOpenProfile} type="button">Open Profile</button>
            <button onClick={onRefresh} type="button">Refresh</button>
          </div>

          <div className="contact-source-list">
            <strong>Evidence Sources</strong>
            {sourceUrls.slice(0, 4).map((source) => (
              <a href={safeExternalUrl(source.url)} key={source.url} rel="noreferrer" target="_blank">
                {source.label || "Public source"}
                <span>{source.confidence || 0}%</span>
              </a>
            ))}
            {!sourceUrls.length ? <p>No public source links attached yet.</p> : null}
          </div>

          {snapshot?.needsPaidSkipTrace ? (
            <p className="contact-limitation">Private mobile/email discovery still needs a licensed provider. LEGACY will not fake missing numbers.</p>
          ) : null}
        </>
      ) : (
        <div className="mini-empty"><p>Select a buyer or transaction to view Contact Intelligence.</p></div>
      )}
    </section>
  );
}

function BuyerProfileDrawer({ contactMessage, entity, footprint, match, onClose, onRefresh, sale, snapshot }) {
  const contacts = Array.isArray(snapshot?.contacts) ? snapshot.contacts : [];
  const phones = contacts.filter((contact) => contact.contactType === "phone");
  const emails = contacts.filter((contact) => contact.contactType === "email");
  const bestContact = snapshot?.bestContact || contacts[0] || null;
  const health = getContactHealth(snapshot, entity);
  const callHref = bestContact?.contactType === "phone" ? `tel:${normalizePhoneDigits(bestContact.normalizedValue || bestContact.value)}` : "";
  const textHref = bestContact?.contactType === "phone" ? `sms:${normalizePhoneDigits(bestContact.normalizedValue || bestContact.value)}` : "";
  const emailHref = bestContact?.contactType === "email" ? `mailto:${bestContact.normalizedValue || bestContact.value}` : "";
  const websiteUrl = safeExternalUrl(entity?.website);
  const copyText = [
    entity?.entityName,
    bestContact ? `Best Contact: ${formatContactValue(bestContact)}` : "Best Contact: Not saved",
    entity?.mailingAddress ? `Mailing: ${entity.mailingAddress}` : "",
    websiteUrl ? `Website: ${websiteUrl}` : ""
  ].filter(Boolean).join("\n");

  return (
    <div className="buyer-profile-backdrop" role="dialog" aria-modal="true" aria-label="Buyer contact profile">
      <aside className="buyer-profile-drawer">
        <header className="buyer-profile-header">
          <div>
            <p className="eyebrow">Buyer Profile</p>
            <h2>{entity?.entityName || "Buyer"}</h2>
            <p>{match?.buyerType || sale?.buyerType || entity?.entityType || "buyer"} / {match?.totalVerifiedPurchases || footprint?.verifiedPurchaseCount || 0} verified purchases</p>
          </div>
          <button className="buyer-profile-close" onClick={onClose} type="button">Close</button>
        </header>

        <section className="buyer-profile-hero">
          <div className={`contact-health-pill ${health.level}`}>
            <strong>{health.score}%</strong>
            <span>Contact Health</span>
          </div>
          <div className="buyer-profile-best-contact">
            <span>Best Contact</span>
            <strong>{bestContact ? formatContactValue(bestContact) : "No verified contact saved"}</strong>
            <p>{bestContact ? `${humanizeLabel(bestContact.status)} / ${bestContact.source}` : snapshot?.message || "Needs enrichment before outreach."}</p>
          </div>
        </section>

        <div className="buyer-profile-actions">
          <a className={!callHref ? "disabled" : ""} href={callHref || undefined}>Call</a>
          <a className={!textHref ? "disabled" : ""} href={textHref || undefined}>Text</a>
          <a className={!emailHref ? "disabled" : ""} href={emailHref || undefined}>Email</a>
          <button onClick={() => copyText && navigator.clipboard?.writeText(copyText)} type="button">Copy</button>
          <a className={!websiteUrl ? "disabled" : ""} href={websiteUrl || undefined} rel="noreferrer" target="_blank">Open Website</a>
          <button onClick={onRefresh} type="button">Refresh Contact</button>
        </div>

        <section className="buyer-profile-grid">
          <DispositionMetric label="Phones" value={phones.length || "None"} />
          <DispositionMetric label="Emails" value={emails.length || "None"} />
          <DispositionMetric label="Confidence" value={`${snapshot?.confidence || health.score || 0}%`} />
          <DispositionMetric label="Last Verified" value={bestContact?.lastVerifiedDate || snapshot?.updatedAt ? formatTimestamp(bestContact?.lastVerifiedDate || snapshot?.updatedAt) : "Not verified"} />
          <DispositionMetric label="Registered Agent" value={entity?.registeredAgent || "Missing"} />
          <DispositionMetric label="Mailing Address" value={entity?.mailingAddress || "Missing"} />
          <DispositionMetric label="Latest Purchase" value={formatShortDate(match?.latestPurchaseDate || footprint?.latestPurchaseDate || sale?.saleDate)} />
          <DispositionMetric label="Avg Purchase" value={formatMoney(match?.averagePurchasePrice || footprint?.averagePurchasePrice || sale?.salePrice)} />
        </section>

        <section className="buyer-profile-section">
          <h3>Verified Contacts</h3>
          <div className="buyer-profile-contact-list">
            {contacts.length ? contacts.map((contact) => (
              <article key={contact.id || contact.value}>
                <strong>{formatContactValue(contact)}</strong>
                <span>{humanizeLabel(contact.contactType)} / {humanizeLabel(contact.status)} / {contact.sourceConfidence || 0}%</span>
                <small>{contact.source || "Source needed"}</small>
              </article>
            )) : <p>No saved buyer phone or email yet. Use enrichment/provider data before outreach.</p>}
          </div>
        </section>

        <section className="buyer-profile-section">
          <h3>Relationship Memory</h3>
          <div className="buyer-profile-timeline">
            {buildBuyerRelationshipTimeline(match, footprint, sale, snapshot).map((item) => (
              <p key={`${item.label}-${item.detail}`}><b>{item.label}</b>{item.detail}</p>
            ))}
          </div>
        </section>

        <section className="buyer-profile-section">
          <h3>Evidence</h3>
          <p>{footprint?.matchExplanation || match?.reasons?.[0] || "Buyer profile opened from Disposition market evidence."}</p>
          {contactMessage ? <small>{contactMessage}</small> : null}
        </section>
      </aside>
    </div>
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

async function fetchContactEntitySnapshot(entity, token) {
  const response = await fetch(`${apiBaseUrl}/contact-intelligence/entities/snapshot`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(entity)
  });

  if (response.status === 403) {
    throw new Error("Buyer Contact Intelligence is protected for leadership.");
  }
  if (!response.ok) {
    throw new Error("Contact Intelligence is not ready yet.");
  }

  return sanitizeContactSnapshot(await response.json());
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

function isActiveContractStatus(status = "") {
  const cleanStatus = String(status || "").toLowerCase();
  return cleanStatus.includes("contract") || cleanStatus.includes("closing") || cleanStatus.includes("closed") || cleanStatus.includes("funded");
}

function buildBuyerRelationshipTimeline(match, footprint, sale, snapshot) {
  const timeline = [];
  if (sale?.saleDate) {
    timeline.push({ label: formatShortDate(sale.saleDate), detail: `Purchased ${sale.address || "nearby parcel"} for ${formatMoney(sale.salePrice)}.` });
  }
  if (match?.latestPurchaseDate && match.latestPurchaseDate !== sale?.saleDate) {
    timeline.push({ label: formatShortDate(match.latestPurchaseDate), detail: "Latest verified nearby purchase." });
  }
  if (footprint?.verifiedPurchaseCount || match?.totalVerifiedPurchases) {
    timeline.push({ label: "Buyer Activity", detail: `${footprint?.verifiedPurchaseCount || match?.totalVerifiedPurchases} verified purchases connected to this buyer.` });
  }
  if (snapshot?.updatedAt) {
    timeline.push({ label: formatTimestamp(snapshot.updatedAt), detail: "Contact Intelligence snapshot refreshed." });
  }
  if (!timeline.length) {
    timeline.push({ label: "No history yet", detail: "Calls, offers, assignments, and responses will build this profile over time." });
  }
  return timeline;
}

function buildBuyerContactEntity(match, sale, footprint, selectedBuyerKey) {
  const entityName = match?.buyerName || footprint?.entityName || sale?.buyerEntity || sale?.buyerName || "";
  if (!entityName) return null;
  const entityId = match?.normalizedBuyerName || selectedBuyerKey || normalizeBuyerKey(entityName) || sale?.id || entityName;
  const mailingAddress = match?.buyerMailingAddress || sale?.buyerMailingAddress || footprint?.mailingAddress || "";
  const sourceUrls = [
    sale?.sourceUrl,
    sale?.rawSourceMetadata?.sourceUrl,
    sale?.rawSourceMetadata?.url,
    ...(Array.isArray(footprint?.sourceUrls) ? footprint.sourceUrls : [])
  ].filter(Boolean);

  return {
    cacheKey: `${entityId}:${sale?.id || "market"}:${mailingAddress}`,
    entityType: match?.buyerType || sale?.buyerType || "buyer",
    entityId,
    entityName,
    company: entityName,
    mailingAddress,
    address: mailingAddress || sale?.address || "",
    county: sale?.county || "Dallas",
    source: sale?.sourceName || sale?.source || "Disposition Intelligence",
    website: footprint?.website || match?.website || "",
    contactFormUrl: footprint?.contactFormUrl || "",
    linkedinUrl: footprint?.linkedinUrl || "",
    facebookUrl: footprint?.facebookUrl || "",
    phone: match?.phone || footprint?.phone || sale?.phone || "",
    phones: [...new Set([...(match?.phones || []), ...(footprint?.phones || [])].filter(Boolean))],
    email: match?.email || footprint?.email || "",
    registeredAgent: footprint?.registeredAgent || "",
    sourceUrls
  };
}

function sanitizeContactSnapshot(snapshot = {}) {
  const contacts = Array.isArray(snapshot.contacts) ? snapshot.contacts.map(sanitizeContactRecord).filter(Boolean) : [];
  const bestId = String(snapshot.bestContact?.id || "");
  const bestContact = contacts.find((contact) => contact.id === bestId) || (snapshot.bestContact ? sanitizeContactRecord(snapshot.bestContact) : contacts[0] || null);
  return {
    ...snapshot,
    contacts,
    bestContact,
    sourceUrls: Array.isArray(snapshot.sourceUrls) ? snapshot.sourceUrls.filter((source) => source?.url) : [],
    confidence: Number(snapshot.confidence) || 0,
    needsPaidSkipTrace: Boolean(snapshot.needsPaidSkipTrace),
    message: String(snapshot.message || "")
  };
}

function sanitizeContactRecord(contact = {}) {
  const value = String(contact.displayValue || contact.value || contact.normalizedValue || "").trim();
  if (!value) return null;
  return {
    id: String(contact.id || value),
    contactType: String(contact.contactType || "phone"),
    value,
    displayValue: value,
    normalizedValue: String(contact.normalizedValue || value),
    source: String(contact.source || "Unknown source"),
    sourceConfidence: Number(contact.sourceConfidence) || 0,
    status: String(contact.status || "unverified"),
    verifiedOwner: Boolean(contact.verifiedOwner),
    isCallable: Boolean(contact.isCallable),
    isTextable: Boolean(contact.isTextable),
    doNotCall: Boolean(contact.doNotCall),
    doNotText: Boolean(contact.doNotText),
    wrongNumber: Boolean(contact.wrongNumber),
    disconnected: Boolean(contact.disconnected)
  };
}

function getContactHealth(snapshot, entity) {
  const contacts = Array.isArray(snapshot?.contacts) ? snapshot.contacts : [];
  const bestContact = snapshot?.bestContact || contacts[0] || null;
  let score = 0;

  if (bestContact?.verifiedOwner) score = Math.max(bestContact.sourceConfidence || 0, 92);
  else if (bestContact?.isCallable || bestContact?.contactType === "email") score = Math.max(bestContact.sourceConfidence || 0, 68);
  else if (contacts.length) score = Math.max(bestContact?.sourceConfidence || 0, 45);
  else if (entity?.website || entity?.email) score = 46;
  else if ((snapshot?.sourceUrls || []).length) score = 32;
  else if (entity?.entityName) score = 18;

  const cleanScore = clamp(score, 0, 100);
  return {
    score: cleanScore,
    level: cleanScore >= 80 ? "strong" : cleanScore >= 50 ? "usable" : cleanScore >= 25 ? "weak" : "missing"
  };
}

function contactHealthLabel(health) {
  return {
    strong: "Strong",
    usable: "Usable",
    weak: "Weak",
    missing: "Missing"
  }[health?.level] || "Missing";
}

function formatContactValue(contact = {}) {
  if (contact.contactType === "phone") {
    return formatPhoneNumber(contact.displayValue || contact.value || contact.normalizedValue);
  }
  return contact.displayValue || contact.value || "Unknown";
}

function normalizePhoneDigits(value = "") {
  return String(value || "").replace(/[^\d+]/g, "");
}

function formatPhoneNumber(value = "") {
  const digits = normalizePhoneDigits(value).replace(/^1/, "");
  if (digits.length !== 10) return value;
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
}

function safeExternalUrl(url = "") {
  const cleanUrl = String(url || "").trim();
  if (!cleanUrl) return "";
  return /^https?:\/\//i.test(cleanUrl) ? cleanUrl : `https://${cleanUrl}`;
}

function isTransactionLayerVisible(transaction = {}, layerVisibility = {}) {
  const markerType = mapMarkerType(transaction);
  if (markerType === "cash_purchase") return layerVisibility.cashPurchases !== false;
  if (markerType === "builder_purchase") return layerVisibility.builders !== false;
  if (markerType === "repeat_buyer") return layerVisibility.repeatBuyers !== false;
  if (markerType === "unknown_estimated") return layerVisibility.recordedSales !== false;
  return layerVisibility.recordedSales !== false;
}

function purchaseAgeClass(transaction = {}) {
  const bucket = transaction.purchaseAgeBucket || "missing";
  return `purchase-age-${bucket}`;
}

function formatTimelineLabel(days) {
  const cleanDays = Number(days) || 180;
  if (cleanDays >= 1095) return "3 years";
  if (cleanDays >= 365) return "1 year";
  return `${cleanDays} days`;
}

function buildDispositionGoogleMapEmbedUrl(target = {}, mapMode = "road") {
  const key = encodeURIComponent(googleMapsEmbedApiKey || "");
  const address = String(target?.address || "Dallas, TX").trim() || "Dallas, TX";
  const coordinates = target?.coordinates || {};
  const lat = Number(coordinates.lat);
  const lng = Number(coordinates.lng);
  const hasCoordinates = Number.isFinite(lat) && Number.isFinite(lng) && lat && lng;

  if (mapMode === "street") {
    const location = hasCoordinates ? `${lat},${lng}` : address;
    return `https://www.google.com/maps/embed/v1/streetview?key=${key}&location=${encodeURIComponent(location)}&heading=210&pitch=0&fov=80`;
  }

  if (mapMode === "satellite" || mapMode === "hybrid") {
    if (hasCoordinates) {
      return `https://www.google.com/maps/embed/v1/view?key=${key}&center=${lat},${lng}&zoom=17&maptype=satellite`;
    }
    return `https://www.google.com/maps/embed/v1/place?key=${key}&q=${encodeURIComponent(address)}&zoom=17`;
  }

  return `https://www.google.com/maps/embed/v1/place?key=${key}&q=${encodeURIComponent(address)}&zoom=16`;
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
    subject_property: "subject",
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
