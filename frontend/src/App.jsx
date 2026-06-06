import React from "react";

const starterLeads = [
  {
    id: "lead-1",
    name: "Maria Thompson",
    address: "1428 Oak Hollow Dr",
    parcelNumber: "",
    county: "Dallas",
    bedrooms: "",
    bathrooms: "",
    sqft: "",
    yearBuilt: "",
    lotSize: "",
    stage: "New Lead",
    score: 78,
    owner: "Admin",
    source: "Tax List",
    phone: "214-555-0142",
    phones: ["214-555-0142"],
    email: "maria@example.com",
    notes: "Imported from a tax list. Needs first call.",
    estimatedArv: "",
    repairBudget: "",
    maxOfferPercent: "70",
    assignmentFee: "",
    contactStatus: "needs-review",
    followUpDate: ""
  },
  {
    id: "lead-2",
    name: "James Carter",
    address: "817 Pine Ridge Ave",
    parcelNumber: "",
    county: "Dallas",
    bedrooms: "",
    bathrooms: "",
    sqft: "",
    yearBuilt: "",
    lotSize: "",
    stage: "Contacted",
    score: 64,
    owner: "Cold Caller",
    source: "Probate PDF",
    phone: "972-555-0187",
    phones: ["972-555-0187"],
    email: "james@example.com",
    notes: "Seller answered once. Follow up this week.",
    estimatedArv: "",
    repairBudget: "",
    maxOfferPercent: "70",
    assignmentFee: "",
    contactStatus: "left-voicemail",
    followUpDate: ""
  },
  {
    id: "lead-3",
    name: "Lena Brooks",
    address: "2309 Maple Bend Ln",
    parcelNumber: "",
    county: "Dallas",
    bedrooms: "",
    bathrooms: "",
    sqft: "",
    yearBuilt: "",
    lotSize: "",
    stage: "Follow Up",
    score: 85,
    owner: "Acquisitions",
    source: "Manual Entry",
    phone: "469-555-0164",
    phones: ["469-555-0164"],
    email: "lena@example.com",
    notes: "High motivation. Check comps before offer.",
    estimatedArv: "",
    repairBudget: "",
    maxOfferPercent: "70",
    assignmentFee: "",
    contactStatus: "follow-up",
    followUpDate: ""
  }
];

const stages = ["New Lead", "Contacted", "Follow Up", "Offer", "Closed"];
const contactStatuses = [
  { value: "needs-review", label: "Needs Review", color: "orange" },
  { value: "confirmed", label: "Confirmed Owner", color: "green" },
  { value: "not-interested", label: "Not Interested", color: "red" },
  { value: "no-answer", label: "Did Not Answer", color: "gray" },
  { value: "left-voicemail", label: "Left Voicemail", color: "blue" },
  { value: "follow-up", label: "Follow Up", color: "yellow" }
];
const mainViews = ["Leads", "Pipeline", "Imports", "Analytics", "Training"];
const callScript = {
  objective: "Verify ownership, determine interest, gather good contact notes, and schedule the right follow-up. Do not make offers on the first call.",
  opening: "Hello, is this {ownerName}? My name is [AGENT NAME], and I am calling about {propertyAddress}. Did I catch you at a bad time?",
  questions: [
    "Do you still own the property?",
    "Have you thought about selling it recently?",
    "If the right offer came along, would you consider selling?",
    "Is there anything preventing you from selling right now?",
    "How soon would you like to sell?"
  ],
  classifications: [
    { label: "Hot", detail: "Wants an offer, inherited property, back taxes, or wants to sell quickly." },
    { label: "Warm", detail: "Interested but not rushed, wants information, or needs a later follow-up." },
    { label: "Cold", detail: "Not interested, keeping long term, already listed, or wrong fit." }
  ],
  rebuttals: [
    { prompt: "How did you get my number?", response: "Public property records and data providers." },
    { prompt: "What is my property worth?", response: "Our acquisitions team reviews each property before giving numbers." },
    { prompt: "Make me an offer right now.", response: "We need to review the property first so we can provide accurate numbers." }
  ],
  voicemail: "Hello, this is [AGENT NAME]. I am calling regarding {propertyAddress}, a property we believe you own in the Dallas area. Please call me back at [PHONE NUMBER]. Thank you."
};
const trainingSections = [
  {
    title: "Mission",
    items: [
      "Find out if the owner would consider selling.",
      "Verify owner and property details before moving the lead forward.",
      "Do not quote prices, values, guarantees, or closing dates."
    ]
  },
  {
    title: "Call Flow",
    items: [
      "Verify owner.",
      "Verify property.",
      "Determine interest.",
      "Gather motivation.",
      "Determine timeline.",
      "Schedule follow-up."
    ]
  },
  {
    title: "Seller Types",
    items: [
      "Motivated Seller: wants cash, inherited property, tired of taxes.",
      "Curious Seller: wants information and may not know value.",
      "Future Seller: may sell later.",
      "Permanent Owner: keeping long term."
    ]
  },
  {
    title: "Lead Scoring",
    items: [
      "Hot: wants an offer, inherited property, back taxes, wants to sell quickly.",
      "Warm: interested but not rushed.",
      "Cold: not interested or wrong fit."
    ]
  },
  {
    title: "CRM Statuses",
    items: [
      "New, No Answer, Voicemail, Callback, Wrong Number, Not Interested.",
      "Warm, Hot, Offer Requested, Follow-Up Scheduled, Contract Sent, Closed."
    ]
  },
  {
    title: "Common Motivations",
    items: [
      "Inherited property, back taxes, need cash, divorce, estate settlement.",
      "Moving, retirement, financial hardship."
    ]
  }
];
const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ||
  (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8001"
    : "https://chatcrm.onrender.com");
const authStorageKey = "chatcrm.auth";
const emptyLead = {
  name: "",
  address: "",
  parcelNumber: "",
  county: "",
  bedrooms: "",
  bathrooms: "",
  sqft: "",
  yearBuilt: "",
  lotSize: "",
  stage: "New Lead",
  score: 50,
  owner: "",
  source: "Manual Entry",
  phone: "",
  phones: [],
  email: "",
  notes: "",
  estimatedArv: "",
  repairBudget: "",
  maxOfferPercent: "70",
  assignmentFee: "",
  followUpDate: ""
};

export function App() {
  const [auth, setAuth] = React.useState(() => loadAuth());
  const [loginError, setLoginError] = React.useState("");
  const [leads, setLeads] = React.useState(() => loadLeads());
  const [imports, setImports] = React.useState(() => loadImports());
  const [query, setQuery] = React.useState("");
  const [stageFilter, setStageFilter] = React.useState("All");
  const [reviewFilter, setReviewFilter] = React.useState("All");
  const [sortMode, setSortMode] = React.useState("zip");
  const [hotOnly, setHotOnly] = React.useState(false);
  const [formLead, setFormLead] = React.useState(emptyLead);
  const [editingId, setEditingId] = React.useState(null);
  const [isFormOpen, setIsFormOpen] = React.useState(false);
  const [importMessage, setImportMessage] = React.useState("");
  const [selectedLeadId, setSelectedLeadId] = React.useState(null);
  const [activeView, setActiveView] = React.useState("Leads");
  const [backendReady, setBackendReady] = React.useState(false);
  const [saveStatus, setSaveStatus] = React.useState("Connecting...");
  const [theme, setTheme] = React.useState(() => safeStorageGet("chatcrm.theme") || "light");
  const [selectedLeadIds, setSelectedLeadIds] = React.useState([]);
  const [agreementLead, setAgreementLead] = React.useState(null);
  const fileInputRef = React.useRef(null);
  const authToken = auth?.accessToken || "";

  async function login(username, password) {
    setLoginError("");
    if (!username.trim() || !password) {
      setLoginError("Enter your username and password.");
      return;
    }

    try {
      const response = await fetch(`${apiBaseUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      const result = await response.json();
      const nextAuth = {
        accessToken: result.access_token,
        user: result.user
      };
      setAuth(nextAuth);
      safeStorageSet(authStorageKey, JSON.stringify(nextAuth));
      setBackendReady(false);
      setLeads([]);
      setSaveStatus("Connecting...");
    } catch {
      setLoginError("Login failed. Check the username and password.");
    }
  }

  function logout() {
    setAuth(null);
    setBackendReady(false);
    setLeads([]);
    safeStorageRemove(authStorageKey);
    safeStorageRemove("chatcrm.leads");
  }

  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    safeStorageSet("chatcrm.theme", theme);
  }, [theme]);

  React.useEffect(() => {
    safeStorageSet("chatcrm.leads", JSON.stringify(leads));
  }, [leads]);

  React.useEffect(() => {
    let cancelled = false;
    setBackendReady(false);

    async function hydrateLeads() {
      if (!authToken) return;
      try {
        const storedLeads = await fetchBackendLeads(authToken);
        if (cancelled) return;

        setLeads(storedLeads);

        setBackendReady(true);
        setSaveStatus("Saved");
      } catch {
        if (!cancelled) {
          setSaveStatus("Browser Save");
        }
      }
    }

    hydrateLeads();
    return () => {
      cancelled = true;
    };
  }, [authToken]);

  React.useEffect(() => {
    if (!backendReady || !authToken || leads.length === 0) return undefined;
    setSaveStatus("Saving...");
    const timeoutId = window.setTimeout(async () => {
      try {
        await syncLeadsToBackend(leads, authToken);
        setSaveStatus("Saved");
      } catch {
        setSaveStatus("Browser Save");
      }
    }, 350);

    return () => window.clearTimeout(timeoutId);
  }, [backendReady, leads, authToken]);

  React.useEffect(() => {
    safeStorageSet("chatcrm.imports", JSON.stringify(imports));
  }, [imports]);

  if (!authToken) {
    return <LoginPage error={loginError} onLogin={login} />;
  }

  const filteredLeads = leads.filter((lead) => {
    const searchText = `${lead.name} ${lead.address} ${getLeadPhones(lead).join(" ")} ${lead.email} ${lead.source}`.toLowerCase();
    const matchesQuery = searchText.includes(query.toLowerCase());
    const matchesStage = stageFilter === "All" || lead.stage === stageFilter;
    const matchesReview =
      reviewFilter === "All" ||
      (reviewFilter === "Needs Review" && lead.needsReview) ||
      (reviewFilter === "Reviewed" && !lead.needsReview);
    const matchesHot = !hotOnly || Number(lead.score) >= 80;
    return matchesQuery && matchesStage && matchesReview && matchesHot;
  });
  const sortedLeads = sortLeads(filteredLeads, sortMode);

  const hotLeads = leads.filter((lead) => Number(lead.score) >= 80).length;
  const followUps = leads.filter((lead) => lead.stage === "Follow Up").length;
  const selectedLead = leads.find((lead) => lead.id === selectedLeadId);
  const displayedLeads = sortedLeads.slice(0, 250);
  const visibleLeadIds = displayedLeads.map((lead) => lead.id);
  const allVisibleSelected = visibleLeadIds.length > 0 && visibleLeadIds.every((id) => selectedLeadIds.includes(id));

  function openCreateForm() {
    setEditingId(null);
    setFormLead(emptyLead);
    setIsFormOpen(true);
    setSelectedLeadId(null);
  }

  function openEditForm(lead) {
    setEditingId(lead.id);
    setFormLead(lead);
    setIsFormOpen(true);
    setSelectedLeadId(null);
  }

  function saveLead(event) {
    event.preventDefault();
    const cleanLead = {
      ...formLead,
      score: clampScore(formLead.score),
      phones: getLeadPhones(formLead),
      phone: getLeadPhones(formLead)[0] || "",
      id: editingId || `lead-${Date.now()}`
    };

    if (editingId) {
      setLeads((current) => current.map((lead) => (lead.id === editingId ? cleanLead : lead)));
    } else {
      setLeads((current) => [cleanLead, ...current]);
    }

    setIsFormOpen(false);
    setEditingId(null);
    setFormLead(emptyLead);
    setSelectedLeadId(cleanLead.id);
  }

  function deleteLead(id) {
    setLeads((current) => current.filter((lead) => lead.id !== id));
    setSelectedLeadIds((current) => current.filter((selectedId) => selectedId !== id));
    if (selectedLeadId === id) {
      setSelectedLeadId(null);
    }
  }

  function toggleLeadSelection(id) {
    setSelectedLeadIds((current) =>
      current.includes(id) ? current.filter((selectedId) => selectedId !== id) : [...current, id]
    );
  }

  function toggleAllVisible() {
    setSelectedLeadIds((current) => {
      if (allVisibleSelected) {
        return current.filter((id) => !visibleLeadIds.includes(id));
      }

      return [...new Set([...current, ...visibleLeadIds])];
    });
  }

  function updateLead(id, updates) {
    setLeads((current) => current.map((lead) => (lead.id === id ? { ...lead, ...updates } : lead)));
  }

  function markReviewed(id) {
    updateLead(id, { needsReview: false, contactStatus: "confirmed" });
  }

  function updateContactStatus(id, status) {
    const statusLabel = getContactStatus(status).label;
    const lead = leads.find((item) => item.id === id);
    const noteLine = `[${new Date().toLocaleString()}] ${statusLabel}`;
    const nextNotes = lead?.notes ? `${lead.notes}\n${noteLine}` : noteLine;
    const stage = status === "follow-up" || status === "left-voicemail" || status === "no-answer" ? "Follow Up" : lead?.stage;

    updateLead(id, {
      contactStatus: status,
      needsReview: status === "needs-review",
      notes: nextNotes,
      stage
    });
  }

  function moveSelectedLead(direction) {
    if (!selectedLead) return;
    const currentIndex = filteredLeads.findIndex((lead) => lead.id === selectedLead.id);
    if (currentIndex === -1) return;
    const nextIndex = (currentIndex + direction + filteredLeads.length) % filteredLeads.length;
    setSelectedLeadId(filteredLeads[nextIndex]?.id || null);
  }

  function markReviewedAndNext() {
    if (!selectedLead) return;
    const currentIndex = filteredLeads.findIndex((lead) => lead.id === selectedLead.id);
    const nextLead = filteredLeads[currentIndex + 1] || filteredLeads[0];
    markReviewed(selectedLead.id);
    setSelectedLeadId(nextLead && nextLead.id !== selectedLead.id ? nextLead.id : null);
  }

  function clearFilters() {
    setQuery("");
    setStageFilter("All");
    setReviewFilter("All");
    setSortMode("zip");
    setHotOnly(false);
  }

  function openReviewQueue() {
    setActiveView("Leads");
    setQuery("");
    setStageFilter("All");
    setReviewFilter("Needs Review");
    setHotOnly(false);
    setSelectedLeadId(null);
  }

  function showFollowUps() {
    setActiveView("Leads");
    setQuery("");
    setStageFilter("Follow Up");
    setReviewFilter("All");
    setHotOnly(false);
  }

  function showHotLeads() {
    setActiveView("Leads");
    setQuery("");
    setStageFilter("All");
    setReviewFilter("All");
    setHotOnly(true);
  }

  function applyBulkStatus(status) {
    if (selectedLeadIds.length === 0 || !status) return;
    const statusLabel = getContactStatus(status).label;
    const noteLine = `[${new Date().toLocaleString()}] Bulk update: ${statusLabel}`;

    setLeads((current) =>
      current.map((lead) => {
        if (!selectedLeadIds.includes(lead.id)) return lead;
        const nextNotes = lead.notes ? `${lead.notes}\n${noteLine}` : noteLine;
        const stage = status === "follow-up" || status === "left-voicemail" || status === "no-answer" ? "Follow Up" : lead.stage;
        return { ...lead, contactStatus: status, needsReview: status === "needs-review", notes: nextNotes, stage };
      })
    );
  }

  function applyBulkStage(stage) {
    if (selectedLeadIds.length === 0 || !stage) return;
    setLeads((current) =>
      current.map((lead) => (selectedLeadIds.includes(lead.id) ? { ...lead, stage } : lead))
    );
  }

  function deleteSelectedLeads() {
    if (selectedLeadIds.length === 0) return;
    setLeads((current) => current.filter((lead) => !selectedLeadIds.includes(lead.id)));
    setSelectedLeadIds([]);
    setSelectedLeadId(null);
  }

  function removeDuplicateLeads() {
    const seen = new Set();
    const uniqueLeads = [];

    for (const lead of leads) {
      const key = `${normalizeText(lead.address)}|${getLeadPhones(lead).map(normalizePhone).join("|")}`;
      if (seen.has(key)) continue;
      seen.add(key);
      uniqueLeads.push(lead);
    }

    setLeads(uniqueLeads);
    setSelectedLeadIds([]);
  }

  async function uploadFiles(event) {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    const uploadedAt = new Date().toISOString();
    setImportMessage(`Parsing ${files.length} file${files.length === 1 ? "" : "s"}...`);
    const parsedImports = [];
    const parsedLeads = [];

    for (const file of files) {
      const importRecord = {
        id: `import-${Date.now()}-${file.name}`,
        fileName: file.name,
        size: file.size,
        uploadedAt,
        status: "Parsing",
        type: guessImportType(file.name),
        warnings: []
      };

      try {
        const result = await parseImportFile(file, authToken);
        importRecord.status = result.leads.length > 0 ? "Parsed" : "Needs Review";
        importRecord.warnings = result.warnings || [];

        if (result.leads.length > 0) {
          parsedLeads.push(...result.leads.map((lead, index) => createLeadFromParsedPdf(lead, file.name, index)));
        } else {
          parsedLeads.push(createDraftLeadFromImport(importRecord));
        }
      } catch {
        importRecord.status = "Needs Review";
        importRecord.warnings = ["The parser could not read this file. A manual draft lead was created."];
        parsedLeads.push(createDraftLeadFromImport(importRecord));
      }

      parsedImports.push(importRecord);
    }

    setImports((current) => [...parsedImports, ...current]);
    setLeads((current) => mergeImportedLeads(current, parsedLeads));
    setQuery("");
    setStageFilter("All");
    setReviewFilter("All");
    setHotOnly(false);
    setImportMessage(`${parsedLeads.length} lead draft${parsedLeads.length === 1 ? "" : "s"} parsed. Matching addresses were updated with any new phone numbers.`);
    event.target.value = "";
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <ChatCrmLogo />
          <div>
            <p className="eyebrow">ChatCRM</p>
            <h1>Lead Intelligence</h1>
          </div>
        </div>

        <nav className="nav-list" aria-label="Main navigation">
          {mainViews.map((view) => (
            <button
              className={`nav-item ${activeView === view ? "active" : ""}`}
              key={view}
              onClick={() => setActiveView(view)}
            >
              {view}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button
            aria-pressed={theme === "dark"}
            aria-label={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
            className="theme-toggle"
            onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
          >
            <span className="theme-toggle-track">
              <span className="theme-toggle-thumb" />
            </span>
            <span>{theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}</span>
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="search-box">
            <Search size={18} />
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search leads, addresses, phone, email..."
              value={query}
            />
          </div>

          <div className="actions">
            <span className={`save-status ${saveStatus === "Saved" ? "saved" : ""}`}>{saveStatus}</span>
            <span className="user-badge">{auth.user?.role}</span>
            <input
              accept="application/pdf,text/csv,.pdf,.csv"
              className="file-input"
              multiple
              onChange={uploadFiles}
              ref={fileInputRef}
              type="file"
            />
            <button
              className="secondary-button"
              onClick={() => fileInputRef.current?.click()}
              title="Upload PDF or CSV"
            >
              <Upload size={18} />
              Upload Files
            </button>
            <button className="primary-button" onClick={openCreateForm}>
              <Plus size={18} />
              Add Lead
            </button>
            <button className="secondary-button" onClick={() => exportLeadsCsv(leads)}>
              Export CSV
            </button>
            <button className="secondary-button" onClick={openReviewQueue}>
              Review Queue
            </button>
            <button
              aria-label={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
              className="secondary-button toolbar-theme-button"
              onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
            >
              {theme === "dark" ? "Light Mode" : "Dark Mode"}
            </button>
            <button className="secondary-button" onClick={logout}>
              Logout
            </button>
          </div>
        </header>

        <section className="stats-grid" aria-label="Lead stats">
          <Stat label="Total Leads" value={leads.length} />
          <Stat label="Needs Follow-Up" value={followUps} />
          <Stat label="Hot Leads" value={hotLeads} />
          <Stat label="PDF Imports" value={imports.length} />
        </section>

        <section className="content-grid">
          {activeView === "Leads" ? (
          <div className="panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">Leads</p>
                <h2>Active Leads</h2>
              </div>
              <div className="lead-filters">
                <select
                  aria-label="Filter by pipeline stage"
                  className="stage-filter"
                  onChange={(event) => setStageFilter(event.target.value)}
                  value={stageFilter}
                >
                  <option>All</option>
                  {stages.map((stage) => (
                    <option key={stage}>{stage}</option>
                  ))}
                </select>
                <select
                  aria-label="Filter by review status"
                  className="stage-filter"
                  onChange={(event) => setReviewFilter(event.target.value)}
                  value={reviewFilter}
                >
                  <option>All</option>
                  <option>Needs Review</option>
                  <option>Reviewed</option>
                </select>
                <select
                  aria-label="Sort leads"
                  className="stage-filter"
                  onChange={(event) => setSortMode(event.target.value)}
                  value={sortMode}
                >
                  <option value="zip">ZIP Code</option>
                  <option value="score">Score</option>
                  <option value="address">Address</option>
                </select>
                <button className="ghost-button" onClick={clearFilters}>Clear</button>
                {hotOnly ? <span className="active-filter">Hot Leads</span> : null}
              </div>
            </div>

            <p className="results-count">
              Showing {displayedLeads.length} of {filteredLeads.length} matching leads / {leads.length} total
            </p>
            <StatusLegend />
            <BulkToolbar
              allVisibleSelected={allVisibleSelected}
              onApplyStage={applyBulkStage}
              onApplyStatus={applyBulkStatus}
              onClear={() => setSelectedLeadIds([])}
              onDelete={deleteSelectedLeads}
              onRemoveDuplicates={removeDuplicateLeads}
              onToggleAll={toggleAllVisible}
              selectedCount={selectedLeadIds.length}
            />

            <div className="lead-table">
              {displayedLeads.length > 0 ? (
                displayedLeads.map((lead) => (
                  <article className="lead-row" key={lead.id}>
                    <label className="lead-checkbox">
                      <input
                        aria-label={`Select ${lead.address}`}
                        checked={selectedLeadIds.includes(lead.id)}
                        onChange={() => toggleLeadSelection(lead.id)}
                        type="checkbox"
                      />
                    </label>
                    <button className="lead-main" onClick={() => setSelectedLeadId(lead.id)}>
                      <h3>
                        {lead.address}
                        <StatusDot lead={lead} />
                      </h3>
                      <p>{getDisplayOwnerName(lead) || "Owner name needed"}</p>
                      <small>{formatPhoneList(lead) || "No phone yet"}</small>
                    </button>
                    <div className="lead-meta-grid">
                      <span className="lead-meta"><b>Stage</b>{lead.stage}</span>
                      <span className="lead-meta"><b>Score</b>{lead.score}</span>
                      <span className="lead-meta"><b>Assigned To</b>{lead.owner || "Unassigned"}</span>
                      <span className="lead-meta"><b>Source</b>{cleanSourceName(lead.source)}</span>
                    </div>
                    <div className="row-actions">
                      <button onClick={() => setSelectedLeadId(lead.id)}>View</button>
                      <a href={buildGoogleMapsUrl(lead.address)} rel="noreferrer" target="_blank">Map</a>
                      <a href={buildStreetViewUrl(lead.address)} rel="noreferrer" target="_blank">Street</a>
                      <button onClick={() => openEditForm(lead)}>Edit</button>
                      <button className="danger-button" onClick={() => deleteLead(lead.id)}>
                        Delete
                      </button>
                    </div>
                  </article>
                ))
              ) : (
                <div className="empty-state">
                  <h3>No leads found</h3>
                  <p>Try a different search or add a new lead.</p>
                </div>
              )}
            </div>
          </div>
          ) : null}

          {activeView === "Pipeline" ? (
            <PipelineView leads={leads} onViewLead={setSelectedLeadId} />
          ) : null}

          {activeView === "Imports" ? (
            <ImportsView importMessage={importMessage} imports={imports} />
          ) : null}

          {activeView === "Analytics" ? (
            <AnalyticsView followUps={followUps} hotLeads={hotLeads} imports={imports} leads={leads} />
          ) : null}

          {activeView === "Training" ? (
            <TrainingView />
          ) : null}

          <aside className="panel side-panel">
            {isFormOpen ? (
              <LeadForm
                formLead={formLead}
                isEditing={Boolean(editingId)}
                onCancel={() => setIsFormOpen(false)}
                onChange={setFormLead}
              onSubmit={saveLead}
              />
            ) : (
              <>
                <div className="panel-header">
                  <div>
                    <p className="eyebrow">Assistant</p>
                    <h2>Next Actions</h2>
                  </div>
                  <Bot size={20} />
                </div>

                <div className="assistant-list">
                  <Action icon={<Phone size={18} />} onClick={openReviewQueue} text={`${leads.filter((lead) => lead.needsReview).length} leads ready for review`} />
                  <Action icon={<Mail size={18} />} onClick={showFollowUps} text={`${followUps} follow-ups need attention`} />
                  <Action icon={<Map size={18} />} onClick={showHotLeads} text={`${hotLeads} hot leads should be researched first`} />
                </div>

                <ImportList importMessage={importMessage} imports={imports} />
              </>
            )}
          </aside>
        </section>

        {selectedLead ? (
          <>
            <button className="detail-backdrop" aria-label="Close lead details" onClick={() => setSelectedLeadId(null)} />
            <LeadDetail
              lead={selectedLead}
              onClose={() => setSelectedLeadId(null)}
              onEdit={() => openEditForm(selectedLead)}
            onMarkReviewed={() => markReviewed(selectedLead.id)}
              onMarkReviewedAndNext={markReviewedAndNext}
              onNext={() => moveSelectedLead(1)}
              onPrevious={() => moveSelectedLead(-1)}
              onStartAgreement={() => setAgreementLead(selectedLead)}
              onStatusChange={(status) => updateContactStatus(selectedLead.id, status)}
            onUpdate={(updates) => updateLead(selectedLead.id, updates)}
          />
          </>
        ) : null}

        {agreementLead ? (
          <>
            <button className="detail-backdrop agreement-layer" aria-label="Close agreement form" onClick={() => setAgreementLead(null)} />
            <AgreementForm authToken={authToken} lead={agreementLead} onClose={() => setAgreementLead(null)} />
          </>
        ) : null}
      </section>
    </main>
  );
}

function Stat({ label, value }) {
  return (
    <article className="stat">
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function LoginPage({ error, onLogin }) {
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");

  function submitLogin(event) {
    event.preventDefault();
    onLogin(username, password);
  }

  return (
    <main className="login-shell">
      <section className="login-hero">
        <div className="brand-block">
          <ChatCrmLogo />
          <div>
            <p className="eyebrow">ChatCRM</p>
            <h1>Lead Intelligence</h1>
          </div>
        </div>
        <div>
          <p className="login-kicker">ChatCRM Command Center</p>
          <h2>Find the owner. Make the offer. Track the deal.</h2>
          <p>
            Built for land acquisitions: skip traced leads, call notes, maps, ARV math, and purchase agreements in one clean workspace.
          </p>
        </div>
      </section>

      <form className="login-panel" onSubmit={submitLogin}>
        <div>
          <p className="eyebrow">Login</p>
          <h2>Access ChatCRM</h2>
        </div>

        <label>
          Username
          <input
            autoComplete="off"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </label>
        <label>
          Password
          <input
            autoComplete="new-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        {error ? <p className="login-error">{error}</p> : null}

        <button className="primary-button" type="submit">Login</button>
      </form>
    </main>
  );
}

function Action({ icon, onClick, text }) {
  return (
    <button className="assistant-action" onClick={onClick}>
      {icon}
      <span>{text}</span>
    </button>
  );
}

function ImportList({ importMessage, imports }) {
  const recentImports = imports.slice(0, 4);

  return (
    <section className="import-list" aria-label="Recent PDF imports">
      <div className="section-heading">
        <p className="eyebrow">PDF Queue</p>
        <h2>Recent Imports</h2>
      </div>

      {importMessage ? <p className="import-status">{importMessage}</p> : null}

      {recentImports.length > 0 ? (
        <>
          <p className="import-help">
            Uploaded PDFs are parsed by the backend. Review all drafts before using them for outreach.
          </p>
        <div className="import-items">
          {recentImports.map((item) => (
            <article className="import-item" key={item.id}>
              <div>
                <h3>{item.fileName}</h3>
                <p>{item.type} / {formatFileSize(item.size)}</p>
              </div>
              <span>{item.status}</span>
            </article>
          ))}
        </div>
        </>
      ) : (
        <div className="mini-empty">
          <p>No PDFs uploaded yet.</p>
        </div>
      )}
    </section>
  );
}

function PipelineView({ leads, onViewLead }) {
  return (
    <div className="panel wide-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Pipeline</p>
          <h2>Deal Stages</h2>
        </div>
      </div>

      <div className="pipeline-board">
        {stages.map((stage) => {
          const stageLeads = leads.filter((lead) => lead.stage === stage);

          return (
            <section className="pipeline-column" key={stage}>
              <div className="pipeline-heading">
                <h3>{stage}</h3>
                <span>{stageLeads.length}</span>
              </div>

              {stageLeads.length > 0 ? (
                stageLeads.map((lead) => (
                  <button className="pipeline-card" key={lead.id} onClick={() => onViewLead(lead.id)}>
                    <strong>{getDisplayOwnerName(lead) || "Owner name needed"}</strong>
                    <span>{lead.address}</span>
                    <small>{formatPhoneList(lead) || "No phone"}</small>
                  </button>
                ))
              ) : (
                <p className="pipeline-empty">No leads</p>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}

function ImportsView({ importMessage, imports }) {
  return (
    <div className="panel wide-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Imports</p>
          <h2>PDF Import History</h2>
        </div>
      </div>

      {importMessage ? <p className="import-status">{importMessage}</p> : null}

      {imports.length > 0 ? (
        <div className="import-history">
          {imports.map((item) => (
            <article className="import-history-row" key={item.id}>
              <div>
                <h3>{cleanSourceName(item.fileName)}</h3>
                <p>{item.type} / {formatFileSize(item.size)}</p>
                {item.warnings?.length ? <small>{item.warnings.join(" ")}</small> : null}
              </div>
              <span>{item.status}</span>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <h3>No imports yet</h3>
          <p>Use Upload PDF to start an import.</p>
        </div>
      )}
    </div>
  );
}

function AnalyticsView({ followUps, hotLeads, imports, leads }) {
  const reviewed = leads.filter((lead) => !lead.needsReview).length;
  const reviewNeeded = leads.filter((lead) => lead.needsReview).length;

  return (
    <div className="panel wide-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Analytics</p>
          <h2>Snapshot</h2>
        </div>
      </div>

      <div className="analytics-grid">
        <Stat label="Total Leads" value={leads.length} />
        <Stat label="Needs Review" value={reviewNeeded} />
        <Stat label="Reviewed" value={reviewed} />
        <Stat label="Follow-Ups" value={followUps} />
        <Stat label="Hot Leads" value={hotLeads} />
        <Stat label="PDF Imports" value={imports.length} />
      </div>
    </div>
  );
}

function TrainingView() {
  return (
    <div className="panel wide-panel training-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Training</p>
          <h2>Dallas Land Acquisition Playbook</h2>
        </div>
      </div>

      <div className="training-hero">
        <div>
          <p className="training-kicker">Winning Formula</p>
          <h3>Ask questions. Listen more than you talk. Take clean notes. Schedule the next step.</h3>
        </div>
        <p>
          This training keeps the team focused on owner verification, motivation, timeline, and follow-up.
          Acquisitions reviews numbers before any offer is made.
        </p>
      </div>

      <div className="training-grid">
        {trainingSections.map((section) => (
          <section className="training-card" key={section.title}>
            <h3>{section.title}</h3>
            <ul>
              {section.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>

      <section className="training-card warning-card">
        <h3>Never Say</h3>
        <ul>
          <li>Do not quote property values, offer amounts, guarantees, or closing dates.</li>
          <li>Do not negotiate. Move interested sellers to acquisitions for review.</li>
          <li>Do not argue. Confirm the call result, save notes, and move to the next lead.</li>
        </ul>
      </section>
    </div>
  );
}

function LeadForm({ formLead, isEditing, onCancel, onChange, onSubmit }) {
  function updateField(field, value) {
    onChange({ ...formLead, [field]: value });
  }

  return (
    <form className="lead-form" onSubmit={onSubmit}>
      <div className="panel-header">
        <div>
          <p className="eyebrow">{isEditing ? "Edit Lead" : "New Lead"}</p>
          <h2>{isEditing ? formLead.name : "Add Lead"}</h2>
        </div>
      </div>

      <label>
        Name
        <input required value={formLead.name} onChange={(event) => updateField("name", event.target.value)} />
      </label>

      <label>
        Property Address
        <input required value={formLead.address} onChange={(event) => updateField("address", event.target.value)} />
      </label>

      <div className="form-grid">
        <label>
          Parcel / APN
          <input value={formLead.parcelNumber || ""} onChange={(event) => updateField("parcelNumber", event.target.value)} />
        </label>

        <label>
          County
          <input value={formLead.county || ""} onChange={(event) => updateField("county", event.target.value)} />
        </label>
      </div>

      <div className="form-grid">
        <label>
          Phone Numbers
          <textarea
            placeholder="One per line, or separate with commas"
            value={getLeadPhones(formLead).join("\n")}
            onChange={(event) => updateField("phone", event.target.value)}
          />
        </label>

        <label>
          Email
          <input type="email" value={formLead.email} onChange={(event) => updateField("email", event.target.value)} />
        </label>
      </div>

      <div className="form-grid property-form-grid">
        <label>
          Beds
          <input value={formLead.bedrooms || ""} onChange={(event) => updateField("bedrooms", event.target.value)} />
        </label>

        <label>
          Baths
          <input value={formLead.bathrooms || ""} onChange={(event) => updateField("bathrooms", event.target.value)} />
        </label>

        <label>
          Sq Ft
          <input value={formLead.sqft || ""} onChange={(event) => updateField("sqft", event.target.value)} />
        </label>

        <label>
          Year Built
          <input value={formLead.yearBuilt || ""} onChange={(event) => updateField("yearBuilt", event.target.value)} />
        </label>
      </div>

      <label>
        Lot Size
        <input value={formLead.lotSize || ""} onChange={(event) => updateField("lotSize", event.target.value)} />
      </label>

      <div className="form-grid">
        <label>
          Estimated ARV
          <input min="0" type="number" value={formLead.estimatedArv || ""} onChange={(event) => updateField("estimatedArv", event.target.value)} />
        </label>

        <label>
          Repair Budget
          <input min="0" type="number" value={formLead.repairBudget || ""} onChange={(event) => updateField("repairBudget", event.target.value)} />
        </label>
      </div>

      <div className="form-grid">
        <label>
          Offer %
          <input min="0" max="100" type="number" value={formLead.maxOfferPercent || "70"} onChange={(event) => updateField("maxOfferPercent", event.target.value)} />
        </label>

        <label>
          Assignment Fee
          <input min="0" type="number" value={formLead.assignmentFee || ""} onChange={(event) => updateField("assignmentFee", event.target.value)} />
        </label>
      </div>

      <div className="form-grid">
        <label>
          Stage
          <select value={formLead.stage} onChange={(event) => updateField("stage", event.target.value)}>
            {stages.map((stage) => (
              <option key={stage}>{stage}</option>
            ))}
          </select>
        </label>

        <label>
          Score
          <input
            max="100"
            min="0"
            type="number"
            value={formLead.score}
            onChange={(event) => updateField("score", event.target.value)}
          />
        </label>
      </div>

      <div className="form-grid">
        <label>
          Owner
          <input value={formLead.owner} onChange={(event) => updateField("owner", event.target.value)} />
        </label>

        <label>
          Source
          <input value={formLead.source} onChange={(event) => updateField("source", event.target.value)} />
        </label>
      </div>

      <label>
        Follow-Up Date
        <input
          type="date"
          value={formLead.followUpDate || ""}
          onChange={(event) => updateField("followUpDate", event.target.value)}
        />
      </label>

      <label>
        Notes
        <textarea value={formLead.notes} onChange={(event) => updateField("notes", event.target.value)} />
      </label>

      <div className="form-actions">
        <button className="secondary-button" type="button" onClick={onCancel}>
          Cancel
        </button>
        <button className="primary-button" type="submit">
          {isEditing ? "Save Lead" : "Create Lead"}
        </button>
      </div>
    </form>
  );
}

function CallScriptPanel({ lead }) {
  const ownerName = getDisplayOwnerName(lead) || "[OWNER NAME]";
  const propertyAddress = lead.address || "the Dallas-area property";
  const opening = callScript.opening
    .replace("{ownerName}", ownerName)
    .replace("{propertyAddress}", propertyAddress);
  const voicemail = callScript.voicemail.replace("{propertyAddress}", propertyAddress);

  return (
    <section className="call-script-panel" aria-label="Call script">
      <div className="script-header">
        <div>
          <p className="eyebrow">Call Script</p>
          <h3>Owner Interest Check</h3>
        </div>
        <span>Dallas Land</span>
      </div>

      <p className="script-objective">{callScript.objective}</p>

      <div className="script-block">
        <span>Opening</span>
        <p>{opening}</p>
      </div>

      <div className="script-block">
        <span>Qualification</span>
        <ol>
          {callScript.questions.map((question) => (
            <li key={question}>{question}</li>
          ))}
        </ol>
      </div>

      <div className="script-classification-grid">
        {callScript.classifications.map((item) => (
          <div key={item.label}>
            <strong>{item.label}</strong>
            <p>{item.detail}</p>
          </div>
        ))}
      </div>

      <details className="script-details">
        <summary>Rebuttals + Voicemail</summary>
        <div className="rebuttal-list">
          {callScript.rebuttals.map((item) => (
            <p key={item.prompt}>
              <strong>{item.prompt}</strong>
              {item.response}
            </p>
          ))}
        </div>
        <div className="script-block">
          <span>Voicemail</span>
          <p>{voicemail}</p>
        </div>
      </details>
    </section>
  );
}

function LeadDetail({
  lead,
  onClose,
  onEdit,
  onMarkReviewed,
  onMarkReviewedAndNext,
  onNext,
  onPrevious,
  onStartAgreement,
  onStatusChange,
  onUpdate
}) {
  const [showMap, setShowMap] = React.useState(false);
  const [myMapsUrl, setMyMapsUrl] = React.useState(() => safeStorageGet("chatcrm.myMapsUrl") || "");
  const mapUrl = buildGoogleMapsUrl(lead.address);
  const streetViewUrl = buildStreetViewUrl(lead.address);
  const taxUrl = buildCountyTaxUrl(lead);
  const myMapsEmbedUrl = buildMyMapsEmbedUrl(myMapsUrl);
  const myMapsOpenUrl = buildMyMapsOpenUrl(myMapsUrl);
  const offer = calculateOffer(lead);
  const phones = getLeadPhones(lead);
  const phoneHref = phones[0] ? `tel:${phones[0].replace(/[^\d+]/g, "")}` : null;
  const emailHref = lead.email ? `mailto:${lead.email}` : null;
  const ownerLabel = getDisplayOwnerName(lead);
  const rawOwnerName = safeText(lead.name).trim();
  const ownerPlaceholder =
    rawOwnerName && rawOwnerName !== "Unknown Owner"
      ? "Replace parsed text with owner name"
      : "Enter owner name";

  function saveMyMapsUrl(value) {
    setMyMapsUrl(value);
    safeStorageSet("chatcrm.myMapsUrl", value);
  }

  return (
    <section className="lead-detail" aria-label="Lead details">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Lead Detail</p>
          <h2>{ownerLabel || "Owner name needed"}</h2>
          <p className="detail-subtitle">{lead.address || "Missing Address"}</p>
        </div>
        <button className="ghost-button" onClick={onClose}>Close</button>
      </div>

      <div className="detail-nav">
        <button className="secondary-button" onClick={onPrevious}>Previous</button>
        <button className="secondary-button" onClick={onNext}>Next</button>
      </div>

      <div className="detail-address">
        <label className="owner-name-field">
          Owner Name
          <input
            placeholder={ownerPlaceholder}
            value={ownerLabel}
            onChange={(event) => onUpdate({ name: event.target.value })}
          />
        </label>
        <div className="property-address-line">
          <span>Property Address</span>
          <strong>{lead.address || "Missing Address"}</strong>
        </div>
        <span className="detail-status"><StatusDot lead={lead} />{getLeadContactStatus(lead).label}</span>
        <button className="inline-map-button" onClick={() => setShowMap((current) => !current)}>
          {showMap ? "Hide Map" : "Show Map"}
        </button>
      </div>

      <div className="quick-actions">
        <ContactLink disabled={!phoneHref} href={phoneHref} label="Call" />
        <ContactLink disabled={!emailHref} href={emailHref} label="Email" />
        <ContactLink href={streetViewUrl} label="Street View" />
        <ContactLink href={mapUrl} label="Map" />
      </div>

      <div className="call-workspace">
        {phones.length > 0 ? (
          <section className="phone-stack" aria-label="Phone numbers">
            <p>Phone Numbers</p>
            <div>
              {phones.map((phone) => (
                <span className="phone-action-group" key={phone}>
                  <a href={`tel:${phone.replace(/[^\d+]/g, "")}`}>{formatPhone(phone)}</a>
                  <a href={buildGoogleVoiceUrl(phone)} rel="noreferrer" target="_blank">Voice</a>
                </span>
              ))}
            </div>
          </section>
        ) : (
          <section className="phone-stack" aria-label="Phone numbers">
            <p>Phone Numbers</p>
            <span className="missing-copy">No phone numbers saved yet.</span>
          </section>
        )}
        <CallScriptPanel lead={lead} />
      </div>

      <div className="detail-grid">
        <DetailItem label="Email" value={lead.email || "Missing"} />
        <DetailItem label="Stage" value={lead.stage} />
        <DetailItem label="Score" value={lead.score} />
        <DetailItem label="Owner" value={lead.owner || "Unassigned"} />
        <DetailItem label="Source" value={cleanSourceName(lead.source)} />
      </div>

      <details className="tool-section" open>
        <summary>Property / Offer Tools</summary>
        <section className="property-workbench">
          <div className="section-heading compact-heading">
            <p className="eyebrow">Property</p>
            <h2>Property Snapshot</h2>
          </div>
          <div className="detail-grid">
            <DetailItem label="Parcel / APN" value={lead.parcelNumber || "Missing"} />
            <DetailItem label="County" value={lead.county || "Missing"} />
            <DetailItem label="Beds / Baths" value={`${lead.bedrooms || "-"} / ${lead.bathrooms || "-"}`} />
            <DetailItem label="Sq Ft" value={lead.sqft || "Missing"} />
            <DetailItem label="Year Built" value={lead.yearBuilt || "Missing"} />
            <DetailItem label="Lot Size" value={lead.lotSize || "Missing"} />
          </div>

          <div className="property-input-grid">
            <label className="detail-field">
              Parcel / APN
              <input value={lead.parcelNumber || ""} onChange={(event) => onUpdate({ parcelNumber: event.target.value })} />
            </label>
            <label className="detail-field">
              County
              <input value={lead.county || ""} onChange={(event) => onUpdate({ county: event.target.value })} />
            </label>
          </div>
          <div className="map-panel-actions">
            <a href={taxUrl} rel="noreferrer" target="_blank">Open County Tax</a>
          </div>
        </section>

        <section className="offer-workbench">
          <div className="section-heading compact-heading">
            <p className="eyebrow">ARV Engine</p>
            <h2>Offer Calculator</h2>
          </div>
          <div className="property-input-grid">
            <label className="detail-field">
              Estimated ARV
              <input min="0" type="number" value={lead.estimatedArv || ""} onChange={(event) => onUpdate({ estimatedArv: event.target.value })} />
            </label>
            <label className="detail-field">
              Repairs
              <input min="0" type="number" value={lead.repairBudget || ""} onChange={(event) => onUpdate({ repairBudget: event.target.value })} />
            </label>
            <label className="detail-field">
              Offer %
              <input min="0" max="100" type="number" value={lead.maxOfferPercent || "70"} onChange={(event) => onUpdate({ maxOfferPercent: event.target.value })} />
            </label>
            <label className="detail-field">
              Assignment Fee
              <input min="0" type="number" value={lead.assignmentFee || ""} onChange={(event) => onUpdate({ assignmentFee: event.target.value })} />
            </label>
          </div>
          <div className="offer-result-grid">
            <DetailItem label="Max Offer" value={offer.maxOffer ? formatMoney(offer.maxOffer) : "Enter ARV"} />
            <DetailItem label="Potential Spread" value={offer.spread ? formatMoney(offer.spread) : "Enter ARV"} />
          </div>
        </section>
      </details>

      {showMap ? (
        <section className="map-panel" aria-label="Embedded map">
          <iframe
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            src={buildGoogleMapsEmbedUrl(lead.address)}
            title={`Map for ${lead.address}`}
          />
          <div className="map-panel-actions">
            <a href={mapUrl} rel="noreferrer" target="_blank">Open Google Map</a>
            <a href={taxUrl} rel="noreferrer" target="_blank">Open County Tax</a>
            <a href={streetViewUrl} rel="noreferrer" target="_blank">Open Street View</a>
          </div>
          <label className="detail-field">
            Google My Maps Embed Link
            <input
              placeholder="Paste your Google My Maps share, edit, or embed link"
              value={myMapsUrl}
              onChange={(event) => saveMyMapsUrl(event.target.value)}
            />
          </label>
          {myMapsOpenUrl ? (
            <div className="map-panel-actions">
              <a href={myMapsOpenUrl} rel="noreferrer" target="_blank">Open My Maps</a>
            </div>
          ) : null}
          {myMapsEmbedUrl ? (
            <iframe
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              src={myMapsEmbedUrl}
              title="Custom Google My Maps"
            />
          ) : null}
        </section>
      ) : null}

      <label className="detail-field">
        Follow-Up Date
        <input
          type="date"
          value={lead.followUpDate || ""}
          onChange={(event) => onUpdate({ followUpDate: event.target.value, stage: event.target.value ? "Follow Up" : lead.stage })}
        />
      </label>

      <label className="detail-field">
        Notes
        <textarea value={lead.notes || ""} onChange={(event) => onUpdate({ notes: event.target.value })} />
      </label>

      <div className="disposition-section">
        <p>Call Result</p>
        <div className="disposition-grid">
          {contactStatuses.map((status) => (
            <button
              className={`disposition-button ${getLeadContactStatus(lead).value === status.value ? "active" : ""}`}
              key={status.value}
              onClick={() => onStatusChange(status.value)}
            >
              <span className={`status-dot ${status.color}`} />
              {status.label}
            </button>
          ))}
        </div>
      </div>

      <div className="detail-actions">
        <button className="agreement-button" onClick={onStartAgreement}>Create Purchase Agreement</button>
        {lead.needsReview ? (
          <>
            <button className="secondary-button" onClick={onMarkReviewed}>Mark Reviewed</button>
            <button className="primary-button" onClick={onMarkReviewedAndNext}>Reviewed + Next</button>
          </>
        ) : null}
        <button className="secondary-button" onClick={onEdit}>Edit Full Lead</button>
      </div>
    </section>
  );
}

function AgreementForm({ authToken, lead, onClose }) {
  const [draft, setDraft] = React.useState(() => ({
    seller_name: lead.name || "",
    property_address: lead.address || "",
    parcel_number: lead.parcelNumber || "",
    purchase_price: "",
    earnest_money: "100",
    agreement_date: new Date().toISOString().slice(0, 10),
    closing_date: "",
    buyer_name: "Virgo Davis",
    buyer_vesting: "and/or assigns",
    title_company: "",
    additional_terms: ""
  }));
  const [message, setMessage] = React.useState("");

  function updateField(field, value) {
    setDraft((current) => ({ ...current, [field]: value }));
  }

  async function generateAgreement(event) {
    event.preventDefault();
    setMessage("Generating PDF...");

    try {
      const response = await fetch(`${apiBaseUrl}/agreements/generate`, {
        method: "POST",
        headers: { ...authHeaders(authToken), "Content-Type": "application/json" },
        body: JSON.stringify(draft)
      });

      if (!response.ok) throw new Error("Agreement generation failed");
      const result = await response.json();
      window.open(`${apiBaseUrl}${result.download_url}`, "_blank", "noopener,noreferrer");
      setMessage("PDF generated and saved.");
    } catch {
      setMessage("Could not generate the PDF. Confirm the backend is running.");
    }
  }

  return (
    <form className="agreement-form" onSubmit={generateAgreement}>
      <div className="panel-header">
        <div>
          <p className="eyebrow">Contract Draft</p>
          <h2>Create Purchase Agreement</h2>
        </div>
        <button className="ghost-button" onClick={onClose} type="button">Close</button>
      </div>

      <p className="agreement-notice">
        Draft template for review. Use an attorney-approved or state-required contract form before signing.
      </p>

      <div className="form-grid">
        <label>Seller / Owner<input required value={draft.seller_name} onChange={(event) => updateField("seller_name", event.target.value)} /></label>
        <label>Parcel / APN<input value={draft.parcel_number} onChange={(event) => updateField("parcel_number", event.target.value)} /></label>
      </div>

      <label>Property Address<input required value={draft.property_address} onChange={(event) => updateField("property_address", event.target.value)} /></label>

      <div className="form-grid">
        <label>Purchase Price<input min="0" required type="number" value={draft.purchase_price} onChange={(event) => updateField("purchase_price", event.target.value)} /></label>
        <label>Earnest Money<input min="0" type="number" value={draft.earnest_money} onChange={(event) => updateField("earnest_money", event.target.value)} /></label>
      </div>

      <div className="form-grid">
        <label>Agreement Date<input type="date" value={draft.agreement_date} onChange={(event) => updateField("agreement_date", event.target.value)} /></label>
        <label>Closing Date<input type="date" value={draft.closing_date} onChange={(event) => updateField("closing_date", event.target.value)} /></label>
      </div>

      <div className="form-grid">
        <label>Buyer<input required value={draft.buyer_name} onChange={(event) => updateField("buyer_name", event.target.value)} /></label>
        <label>Buyer Vesting<input value={draft.buyer_vesting} onChange={(event) => updateField("buyer_vesting", event.target.value)} /></label>
      </div>

      <label>Title Company / Closing Agent<input value={draft.title_company} onChange={(event) => updateField("title_company", event.target.value)} /></label>
      <label>Additional Terms<textarea value={draft.additional_terms} onChange={(event) => updateField("additional_terms", event.target.value)} /></label>

      {message ? <p className="import-status">{message}</p> : null}

      <div className="form-actions">
        <button className="secondary-button" onClick={onClose} type="button">Cancel</button>
        <button className="agreement-button" type="submit">Generate PDF</button>
      </div>
    </form>
  );
}

function DetailItem({ label, value }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ContactLink({ disabled = false, href, label }) {
  if (disabled) {
    return <span className="quick-link disabled">{label}</span>;
  }

  return (
    <a className="quick-link" href={href} rel="noreferrer" target={href?.startsWith("http") ? "_blank" : undefined}>
      {label}
    </a>
  );
}

function StatusDot({ lead }) {
  const status = getLeadContactStatus(lead);
  return <span aria-label={status.label} className={`status-dot ${status.color}`} title={status.label} />;
}

function StatusLegend() {
  return (
    <div className="status-legend" aria-label="Lead color guide">
      <strong>Color Guide</strong>
      {contactStatuses.map((status) => (
        <span key={status.value}>
          <span className={`status-dot ${status.color}`} />
          {status.label}
        </span>
      ))}
    </div>
  );
}

function BulkToolbar({
  allVisibleSelected,
  onApplyStage,
  onApplyStatus,
  onClear,
  onDelete,
  onRemoveDuplicates,
  onToggleAll,
  selectedCount
}) {
  return (
    <section className="bulk-toolbar" aria-label="Bulk lead tools">
      <label className="bulk-select-all">
        <input checked={allVisibleSelected} onChange={onToggleAll} type="checkbox" />
        Select visible
      </label>
      <strong>{selectedCount} selected</strong>

      <select aria-label="Bulk update contact status" defaultValue="" onChange={(event) => onApplyStatus(event.target.value)}>
        <option disabled value="">Set status</option>
        {contactStatuses.map((status) => (
          <option key={status.value} value={status.value}>{status.label}</option>
        ))}
      </select>

      <select aria-label="Bulk update pipeline stage" defaultValue="" onChange={(event) => onApplyStage(event.target.value)}>
        <option disabled value="">Set stage</option>
        {stages.map((stage) => (
          <option key={stage} value={stage}>{stage}</option>
        ))}
      </select>

      <button onClick={onRemoveDuplicates}>Remove Duplicates</button>
      <button onClick={onClear}>Clear</button>
      <button className="danger-button" onClick={onDelete}>Delete Selected</button>
    </section>
  );
}

function loadLeads() {
  try {
    const savedLeads = JSON.parse(safeStorageGet("chatcrm.leads"));
    const cleanLeads = sanitizeLeads(savedLeads);
    return cleanLeads;
  } catch {
    return [];
  }
}

function loadImports() {
  try {
    const savedImports = JSON.parse(safeStorageGet("chatcrm.imports"));
    return sanitizeImports(savedImports);
  } catch {
    return [];
  }
}

function safeStorageGet(key) {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeStorageSet(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // The backend remains the source of truth if the browser cache is full or blocked.
  }
}

function safeStorageRemove(key) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Ignore browser storage errors.
  }
}

function loadAuth() {
  try {
    const savedAuth = JSON.parse(safeStorageGet(authStorageKey));
    if (savedAuth?.accessToken && savedAuth?.user) return savedAuth;
  } catch {
    return null;
  }

  return null;
}

function sanitizeLeads(value) {
  if (!Array.isArray(value)) return [];

  return value
    .filter((lead) => lead && typeof lead === "object")
    .map((lead, index) => normalizeLeadPhones({
      ...emptyLead,
      ...lead,
      id: safeText(lead.id) || `lead-${Date.now()}-${index}`,
      address: safeText(lead.address) || "Missing Address",
      name: safeText(lead.name || lead.ownerName) || "Unknown Owner",
      parcelNumber: safeText(lead.parcelNumber),
      county: safeText(lead.county),
      bedrooms: safeText(lead.bedrooms),
      bathrooms: safeText(lead.bathrooms),
      sqft: safeText(lead.sqft),
      yearBuilt: safeText(lead.yearBuilt),
      lotSize: safeText(lead.lotSize),
      stage: safeText(lead.stage) || "New Lead",
      score: clampScore(lead.score ?? 50),
      owner: safeText(lead.owner),
      source: safeText(lead.source) || "Imported",
      phone: safeText(lead.phone),
      phones: Array.isArray(lead.phones) ? lead.phones.map(safeText).filter(Boolean) : [],
      email: safeText(lead.email),
      notes: safeText(lead.notes),
      estimatedArv: safeText(lead.estimatedArv),
      repairBudget: safeText(lead.repairBudget),
      maxOfferPercent: safeText(lead.maxOfferPercent) || "70",
      assignmentFee: safeText(lead.assignmentFee),
      contactStatus: safeText(lead.contactStatus),
      followUpDate: safeText(lead.followUpDate)
    }));
}

function sanitizeImports(value) {
  if (!Array.isArray(value)) return [];

  return value
    .filter((item) => item && typeof item === "object")
    .map((item, index) => ({
      id: safeText(item.id) || `import-${Date.now()}-${index}`,
      fileName: safeText(item.fileName) || "Uploaded file",
      size: Number(item.size) || 0,
      uploadedAt: safeText(item.uploadedAt),
      status: safeText(item.status) || "Parsed",
      type: safeText(item.type) || "Import",
      warnings: Array.isArray(item.warnings) ? item.warnings.map(safeText).filter(Boolean) : []
    }));
}

function safeText(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return "";
}

async function parsePdf(file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/imports/parse-pdf`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });

  if (!response.ok) {
    throw new Error("PDF parse failed");
  }

  return response.json();
}

async function parseCsv(file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/imports/parse-csv`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });

  if (!response.ok) {
    throw new Error("CSV parse failed");
  }

  return response.json();
}

async function parseImportFile(file, token) {
  const lowerName = file.name.toLowerCase();
  if (lowerName.endsWith(".csv") || file.type === "text/csv") {
    return parseCsv(file, token);
  }

  return parsePdf(file, token);
}

async function fetchBackendLeads(token) {
  const response = await fetch(`${apiBaseUrl}/leads`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Lead fetch failed");
  }

  return sanitizeLeads(await response.json());
}

async function syncLeadsToBackend(leads, token) {
  const response = await fetch(`${apiBaseUrl}/leads/sync`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(leads)
  });

  if (!response.ok) {
    throw new Error("Lead save failed");
  }

  return response.json();
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function clampScore(score) {
  const numberScore = Number(score);
  if (Number.isNaN(numberScore)) return 0;
  return Math.min(100, Math.max(0, numberScore));
}

function guessImportType(fileName) {
  const lowerName = fileName.toLowerCase();
  if (lowerName.includes("tax")) return "Tax List";
  if (lowerName.includes("probate")) return "Probate";
  if (lowerName.includes("foreclosure")) return "Foreclosure";
  if (lowerName.includes("county")) return "County Record";
  return "PDF Upload";
}

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", {
    currency: "USD",
    maximumFractionDigits: 0,
    style: "currency"
  }).format(value);
}

function cleanSourceName(source = "") {
  try {
    return decodeURIComponent(source).replace(/^\d{10,}[_\s-]*/, "").replace(/[_-]+/g, " ").replace(/\.pdf$/i, "").trim();
  } catch {
    return source.replace(/^\d{10,}[_\s-]*/, "").replace(/[_-]+/g, " ").replace(/\.pdf$/i, "").trim();
  }
}

function formatPhone(phone = "") {
  const digits = phone.replace(/\D/g, "");
  const normalized = digits.length === 11 && digits.startsWith("1") ? digits.slice(1) : digits;

  if (normalized.length !== 10) {
    return phone;
  }

  if (!/^[2-9]\d{2}[2-9]\d{6}$/.test(normalized)) {
    return "Needs Review";
  }

  return `(${normalized.slice(0, 3)}) ${normalized.slice(3, 6)}-${normalized.slice(6)}`;
}

function getLeadPhones(lead = {}) {
  const values = [];
  if (Array.isArray(lead.phones)) {
    values.push(...lead.phones);
  }
  if (lead.phone) {
    values.push(...String(lead.phone).split(/[\n,;|]+/));
  }

  const seen = new Set();
  return values
    .map((phone) => String(phone).trim())
    .filter(Boolean)
    .filter((phone) => {
      const key = normalizePhone(phone);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function formatPhoneList(lead = {}) {
  return getLeadPhones(lead).map(formatPhone).join(", ");
}

function normalizeText(value = "") {
  return value.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizePhone(value = "") {
  return value.replace(/\D/g, "");
}

function sortLeads(leads, sortMode) {
  return [...leads].sort((first, second) => {
    if (sortMode === "score") {
      return (Number(second.score) || 0) - (Number(first.score) || 0);
    }

    if (sortMode === "address") {
      return safeText(first.address).localeCompare(safeText(second.address), undefined, { numeric: true });
    }

    const firstZip = getLeadZip(first);
    const secondZip = getLeadZip(second);

    if (firstZip && secondZip && firstZip !== secondZip) {
      return firstZip.localeCompare(secondZip, undefined, { numeric: true });
    }

    if (firstZip && !secondZip) return -1;
    if (!firstZip && secondZip) return 1;

    return safeText(first.address).localeCompare(safeText(second.address), undefined, { numeric: true });
  });
}

function getLeadZip(lead = {}) {
  const searchText = [lead.zip, lead.zipCode, lead.postalCode, lead.address].filter(Boolean).join(" ");
  const match = String(searchText).match(/\b\d{5}(?:-\d{4})?\b/);
  return match ? match[0].slice(0, 5) : "";
}

function getDisplayOwnerName(lead = {}) {
  const name = safeText(lead.name).trim();
  if (!name || name === "Unknown Owner") return "";

  if (isLikelyParsedAddressName(name, lead.address)) return "";

  return name;
}

function isLikelyParsedAddressName(name, address = "") {
  const normalizedName = normalizeText(name);
  const normalizedAddress = normalizeText(address);
  const blockedNames = new Set(["owner oc", "owner occupied", "import review", "review owner"]);
  const streetWords = /\b(st|street|dr|drive|rd|road|ave|avenue|ln|lane|ct|court|cir|circle|blvd|boulevard|pkwy|parkway|trl|trail|way)\b/i;
  const ownerSignals = /\b(llc|inc|corp|co|company|trust|estate|properties|property|holdings|capital|partners|lp|llp)\b/i;
  const addressOverlap = normalizedName.length >= 8 && normalizedAddress.includes(normalizedName.slice(0, 8));

  return blockedNames.has(normalizedName) || (!ownerSignals.test(name) && (streetWords.test(name) || addressOverlap));
}

function getLeadContactStatus(lead) {
  return getContactStatus(lead.contactStatus || (lead.needsReview ? "needs-review" : "confirmed"));
}

function getContactStatus(value) {
  return contactStatuses.find((status) => status.value === value) || contactStatuses[0];
}

function mergeBackendLeads(currentLeads, backendLeads) {
  const byAddress = new Map();

  for (const lead of currentLeads) {
    byAddress.set(normalizeText(lead.address), lead);
  }

  for (const backendLead of backendLeads) {
    const key = normalizeText(backendLead.address);
    const currentLead = byAddress.get(key);

    if (!currentLead) {
      byAddress.set(key, normalizeLeadPhones(backendLead));
      continue;
    }

    const phones = mergePhones(currentLead, backendLead);
    byAddress.set(key, normalizeLeadPhones({
      ...currentLead,
      ...backendLead,
      phones,
      phone: phones[0] || backendLead.phone || currentLead.phone || "",
      notes: currentLead.notes || backendLead.notes || "",
      contactStatus: currentLead.contactStatus || backendLead.contactStatus,
      followUpDate: currentLead.followUpDate || backendLead.followUpDate || ""
    }));
  }

  return Array.from(byAddress.values());
}

function normalizeLeadPhones(lead) {
  const phones = getLeadPhones(lead);
  return {
    ...lead,
    phones,
    phone: phones[0] || lead.phone || ""
  };
}

function mergeImportedLeads(currentLeads, importedLeads) {
  const merged = [...currentLeads];

  for (const importedLead of importedLeads) {
    const importedAddress = normalizeText(importedLead.address);
    const existingIndex = merged.findIndex((lead) => normalizeText(lead.address) === importedAddress);

    if (existingIndex === -1 || importedLead.address === "Open this draft and enter the property address") {
      merged.unshift(importedLead);
      continue;
    }

    const existingLead = merged[existingIndex];
    const phones = mergePhones(existingLead, importedLead);
    merged[existingIndex] = {
      ...existingLead,
      phones,
      phone: phones[0] || existingLead.phone || importedLead.phone || "",
      email: existingLead.email || importedLead.email || "",
      parcelNumber: existingLead.parcelNumber || importedLead.parcelNumber || "",
      county: existingLead.county || importedLead.county || "",
      bedrooms: existingLead.bedrooms || importedLead.bedrooms || "",
      bathrooms: existingLead.bathrooms || importedLead.bathrooms || "",
      sqft: existingLead.sqft || importedLead.sqft || "",
      yearBuilt: existingLead.yearBuilt || importedLead.yearBuilt || "",
      lotSize: existingLead.lotSize || importedLead.lotSize || "",
      estimatedArv: existingLead.estimatedArv || importedLead.estimatedArv || "",
      source: existingLead.source || importedLead.source,
      score: Math.max(Number(existingLead.score) || 0, Number(importedLead.score) || 0)
    };
  }

  return merged;
}

function mergePhones(...leads) {
  const seen = new Set();
  const phones = [];

  for (const lead of leads) {
    for (const phone of getLeadPhones(lead)) {
      const key = normalizePhone(phone);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      phones.push(phone);
    }
  }

  return phones;
}

function exportLeadsCsv(leads) {
  const headers = [
    "Property Address",
    "Owner Name",
    "Parcel / APN",
    "County",
    "Phone Numbers",
    "Email",
    "Beds",
    "Baths",
    "Sq Ft",
    "Year Built",
    "Lot Size",
    "Estimated ARV",
    "Repair Budget",
    "Offer %",
    "Assignment Fee",
    "Max Offer",
    "Potential Spread",
    "Stage",
    "Score",
    "Assigned To",
    "Source",
    "Follow-Up Date",
    "Notes",
    "Review Status"
  ];
  const rows = leads.map((lead) => {
    const offer = calculateOffer(lead);
    return [
      lead.address,
      lead.name,
      lead.parcelNumber,
      lead.county,
      formatPhoneList(lead),
      lead.email,
      lead.bedrooms,
      lead.bathrooms,
      lead.sqft,
      lead.yearBuilt,
      lead.lotSize,
      lead.estimatedArv,
      lead.repairBudget,
      lead.maxOfferPercent,
      lead.assignmentFee,
      offer.maxOffer ? formatMoney(offer.maxOffer) : "",
      offer.spread ? formatMoney(offer.spread) : "",
      lead.stage,
      lead.score,
      lead.owner,
      cleanSourceName(lead.source),
      lead.followUpDate,
      lead.notes,
      lead.needsReview ? "Needs Review" : "Reviewed"
    ];
  });
  const csv = [headers, ...rows].map((row) => row.map(escapeCsvValue).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `chatcrm-leads-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function escapeCsvValue(value = "") {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function buildGoogleMapsUrl(address) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address || "")}`;
}

function buildStreetViewUrl(address) {
  return `https://www.google.com/maps/search/${encodeURIComponent(address || "")}`;
}

function buildGoogleMapsEmbedUrl(address) {
  return `https://maps.google.com/maps?q=${encodeURIComponent(address || "")}&output=embed`;
}

function buildMyMapsEmbedUrl(value = "") {
  const url = parseUrl(value);
  if (!url) return "";

  if (url.pathname.includes("/maps/d/embed")) {
    return url.toString();
  }

  const mapId = url.searchParams.get("mid");
  if (mapId) {
    return `https://www.google.com/maps/d/embed?mid=${encodeURIComponent(mapId)}`;
  }

  return value;
}

function buildMyMapsOpenUrl(value = "") {
  const url = parseUrl(value);
  if (!url) return "";

  const mapId = url.searchParams.get("mid");
  if (mapId && url.pathname.includes("/maps/d/embed")) {
    return `https://www.google.com/maps/d/viewer?mid=${encodeURIComponent(mapId)}`;
  }

  return url.toString();
}

function parseUrl(value = "") {
  try {
    return value.trim() ? new URL(value.trim()) : null;
  } catch {
    return null;
  }
}

function buildCountyTaxUrl(lead) {
  const county = `${lead.county || ""} ${lead.source || ""} ${lead.address || ""}`.toLowerCase();

  if (county.includes("dallas")) {
    return "https://www.dallasact.com/act_webdev/dallas/index.jsp";
  }

  const query = [lead.county, lead.parcelNumber, lead.address, "county appraisal district property search"].filter(Boolean).join(" ");
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function buildGoogleVoiceUrl(phone = "") {
  const digits = normalizePhone(phone);
  const dialNumber = digits.length === 10 ? `1${digits}` : digits;
  return dialNumber ? `https://voice.google.com/u/0/calls?a=nc,%2B${dialNumber}` : "https://voice.google.com/u/0/calls";
}

function calculateOffer(lead) {
  const arv = numberFromMoney(lead.estimatedArv);
  const repairs = numberFromMoney(lead.repairBudget);
  const percent = numberFromMoney(lead.maxOfferPercent || "70") / 100;
  const assignmentFee = numberFromMoney(lead.assignmentFee);
  const maxOffer = Math.max(0, Math.round(arv * percent - repairs - assignmentFee));
  const spread = Math.max(0, Math.round(arv - repairs - maxOffer));
  return { maxOffer, spread };
}

function numberFromMoney(value) {
  const number = Number(String(value || "").replace(/[$,\s]/g, ""));
  return Number.isFinite(number) ? number : 0;
}

function createDraftLeadFromImport(item) {
  return {
    id: `draft-${item.id}`,
    name: `Review ${item.type}`,
    address: "Open this draft and enter the property address",
    parcelNumber: "",
    county: "",
    bedrooms: "",
    bathrooms: "",
    sqft: "",
    yearBuilt: "",
    lotSize: "",
    stage: "New Lead",
    score: 40,
    owner: "Import Review",
    source: item.fileName,
    phone: "",
    phones: [],
    email: "",
    notes: `Created from uploaded PDF: ${item.fileName}. Review this draft and replace it with the extracted seller/property details.`,
    estimatedArv: "",
    repairBudget: "",
    maxOfferPercent: "70",
    assignmentFee: "",
    needsReview: true,
    contactStatus: "needs-review",
    followUpDate: ""
  };
}

function createLeadFromParsedPdf(parsedLead, fileName, index) {
  return {
    id: `parsed-${normalizeText(parsedLead.address)}-${index}`,
    name: parsedLead.name || "Unknown Owner",
    address: parsedLead.address || "Review parsed address",
    parcelNumber: "",
    county: "",
    bedrooms: "",
    bathrooms: "",
    sqft: "",
    yearBuilt: "",
    lotSize: "",
    stage: "New Lead",
    score: parsedLead.confidence || 60,
    owner: "Import Review",
    source: fileName,
    phone: parsedLead.phone || "",
    phones: parsedLead.phones?.length ? parsedLead.phones : parsedLead.phone ? [parsedLead.phone] : [],
    email: parsedLead.email || "",
    notes: "",
    estimatedArv: "",
    repairBudget: "",
    maxOfferPercent: "70",
    assignmentFee: "",
    needsReview: true,
    contactStatus: "needs-review",
    followUpDate: ""
  };
}

function ChatCrmLogo() {
  return (
    <img
      alt="ChatCRM logo"
      className="brand-logo"
      src="/assets/chatcrm-logo.png"
    />
  );
}

function Icon({ label, children, size = 18 }) {
  return (
    <span
      aria-label={label}
      className="text-icon"
      role="img"
      style={{ fontSize: `${size}px`, height: `${size}px`, width: `${size}px` }}
    >
      {children}
    </span>
  );
}

function Search({ size }) {
  return <Icon label="Search" size={size}>S</Icon>;
}

function Plus({ size }) {
  return <Icon label="Add" size={size}>+</Icon>;
}

function Upload({ size }) {
  return <Icon label="Upload" size={size}>U</Icon>;
}

function Phone({ size }) {
  return <Icon label="Phone" size={size}>P</Icon>;
}

function Mail({ size }) {
  return <Icon label="Email" size={size}>M</Icon>;
}

function Map({ size }) {
  return <Icon label="Map" size={size}>A</Icon>;
}

function Bot({ size }) {
  return <Icon label="Assistant" size={size}>AI</Icon>;
}
