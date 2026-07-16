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
const mainViews = ["Leads", "Pipeline", "Property Intelligence", "Buyer Network", "Imports", "Analytics", "Training"];
const callerViews = ["Dashboard", "Leads", "Training", "Leaderboard", "Profile"];
const commissionTiers = [
  { min: 0, max: 9999, rate: 0.15, label: "$0 - $9,999" },
  { min: 10000, max: 19999, rate: 0.2, label: "$10,000 - $19,999" },
  { min: 20000, max: 34999, rate: 0.225, label: "$20,000 - $34,999" },
  { min: 35000, max: Infinity, rate: 0.25, label: "$35,000+" }
];
const partnerAgreementClauses = [
  { title: "Confidentiality", detail: "Seller lists, buyer lists, lead data, training, scripts, processes, and ChatCRM information stay confidential and remain property of ChatCRM." },
  { title: "Non-Circumvention", detail: "Team members may not bypass ChatCRM to work directly with sellers, buyers, investors, builders, or relationships introduced through the platform." },
  { title: "Compensation", detail: "Commissions are paid after a successful closing and receipt of funds. ChatCRM handles compensation and applicable tax reporting requirements." },
  { title: "Caller Responsibilities", detail: "Contact sellers, verify ownership, determine motivation, gather property details, update ChatCRM, and schedule follow-ups." }
];
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
    { prompt: "Who are you?", response: "We work with a local acquisition team that reviews vacant land and residential lots in the Dallas area." },
    { prompt: "Are you a realtor?", response: "No. We are not calling to list the property. We are checking whether you would consider a direct sale." },
    { prompt: "What is my property worth?", response: "Our acquisitions team reviews each property before giving numbers." },
    { prompt: "Make me an offer right now.", response: "We need to review the property first so we can provide accurate numbers." },
    { prompt: "I am not interested.", response: "No problem. Is it something you would never sell, or would it make sense to check back later?" },
    { prompt: "Remove me from your list.", response: "Absolutely. I will mark that down. Thank you for letting me know." },
    { prompt: "I do not own that property.", response: "Thank you for clarifying. Do you know if it was sold, inherited, or titled under a different name?" },
    { prompt: "I already sold it.", response: "Got it. Do you remember roughly when it sold so we can update our records?" },
    { prompt: "I need to talk to family.", response: "Of course. Who else should be part of that conversation, and when would be a good time to follow up?" },
    { prompt: "Call me later.", response: "Absolutely. What day and time works best for you?" },
    { prompt: "Text me.", response: "Sure. I can send a quick text with who we are and the property we are calling about." },
    { prompt: "Send me something in writing.", response: "Sure. What is the best email or mailing address to send information to?" },
    { prompt: "I want full market value.", response: "I understand. Our team reviews the property first, then decides whether we can make an offer that makes sense." },
    { prompt: "I do not want a low offer.", response: "I hear you. I am not here to throw out a number. My job is only to confirm interest and get the property reviewed." },
    { prompt: "How fast can you close?", response: "That depends on title, taxes, and the property review. Acquisitions can give a better answer after checking those items." },
    { prompt: "I owe back taxes.", response: "That is helpful to know. Our acquisitions team can review taxes and see whether that affects the offer." },
    { prompt: "There is a lien or title issue.", response: "Thank you for mentioning that. I will note it so acquisitions can review title before discussing numbers." },
    { prompt: "The property is listed.", response: "Thanks for letting me know. Is it currently active with an agent, or was it listed before?" },
    { prompt: "Is this a scam?", response: "I understand the concern. We are only verifying ownership and interest right now. You do not need to provide private financial information on this call." },
    { prompt: "I am busy.", response: "No problem. I can keep this short. Is this a bad time, or should I call back later?" }
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
  followUpDate: "",
  contactStatus: "needs-review",
  lastContactedUserId: "",
  lastContactedBy: "",
  lastContactedAt: "",
  lastActivityAction: "",
  lockedByUserId: "",
  lockedByUserName: "",
  lockedUntil: ""
};

const emptyBuyer = {
  id: "",
  name: "",
  company: "",
  phone: "",
  phones: [],
  email: "",
  website: "",
  socialLinks: [],
  counties: [],
  zipCodes: [],
  priceMin: "",
  priceMax: "",
  propertyTypes: [],
  fundingType: "",
  builderType: "",
  activityStatus: "warm",
  relationshipTier: "C",
  pastDealsBought: "",
  assignmentFeeTolerance: "",
  notes: "",
  source: "Manual Entry"
};

const parcelMapLayers = [
  "Satellite",
  "Parcel",
  "Zoning",
  "Flood",
  "Utility",
  "Tax Delinquent",
  "Opportunity Zone"
];

export function App() {
  const [auth, setAuth] = React.useState(() => loadAuth());
  const [loginError, setLoginError] = React.useState("");
  const [leads, setLeads] = React.useState(() => loadLeads());
  const [buyers, setBuyers] = React.useState(() => loadBuyers());
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
  const [buyerMessage, setBuyerMessage] = React.useState("");
  const [onboardingMessage, setOnboardingMessage] = React.useState("");
  const [teamOnboardingRows, setTeamOnboardingRows] = React.useState([]);
  const [teamOnboardingMessage, setTeamOnboardingMessage] = React.useState("");
  const fileInputRef = React.useRef(null);
  const buyerFileInputRef = React.useRef(null);
  const cadFileInputRef = React.useRef(null);
  const authToken = auth?.accessToken || "";
  const isAdmin = auth?.user?.role === "Admin";
  const visibleMainViews = isAdmin ? [...mainViews, "Team"] : callerViews;

  React.useEffect(() => {
    if (!visibleMainViews.includes(activeView)) {
      setActiveView(visibleMainViews[0] || "Leads");
    }
  }, [activeView, visibleMainViews.join("|")]);

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
      setBuyers([]);
      setSaveStatus("Connecting...");
    } catch {
      setLoginError("Login failed. Check the username and password.");
    }
  }

  function logout() {
    setAuth(null);
    setBackendReady(false);
    setLeads([]);
    setBuyers([]);
    safeStorageRemove(authStorageKey);
    safeStorageRemove("chatcrm.leads");
    safeStorageRemove("chatcrm.buyers");
  }

  function updateStoredAuthUser(user) {
    const nextAuth = { accessToken: authToken, user };
    setAuth(nextAuth);
    safeStorageSet(authStorageKey, JSON.stringify(nextAuth));
  }

  async function saveCallerProfile(profile) {
    setOnboardingMessage("Saving your profile...");
    const user = await saveOnboardingProfile(profile, authToken);
    updateStoredAuthUser(user);
    setOnboardingMessage("Profile saved. Review and sign your agreement next.");
  }

  async function signCallerAgreement(payload) {
    setOnboardingMessage("Saving your signed agreement...");
    const result = await signOnboardingAgreement(payload, authToken);
    updateStoredAuthUser(result.user);
    setOnboardingMessage("Signed agreement saved. Download started.");
    await downloadSignedOnboardingAgreement(authToken);
  }

  async function downloadCallerAgreement() {
    setOnboardingMessage("Preparing your signed agreement download...");
    await downloadSignedOnboardingAgreement(authToken);
    setOnboardingMessage("Download started.");
  }

  async function refreshTeamOnboarding() {
    if (!authToken || auth?.user?.role !== "Admin") return;

    setTeamOnboardingMessage("Checking team onboarding...");
    try {
      const rows = await fetchAdminOnboardingStatuses(authToken);
      setTeamOnboardingRows(rows);
      setTeamOnboardingMessage("");
    } catch {
      setTeamOnboardingMessage("Could not load team onboarding yet.");
    }
  }
  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    safeStorageSet("chatcrm.theme", theme);
  }, [theme]);

  React.useEffect(() => {
    let cancelled = false;

    async function refreshUser() {
      if (!authToken) return;
      try {
        const user = await fetchCurrentUser(authToken);
        if (!cancelled) updateStoredAuthUser(user);
      } catch {
        // Keep the existing session; protected API calls will handle expired tokens.
      }
    }

    refreshUser();
    return () => {
      cancelled = true;
    };
  }, [authToken]);
  React.useEffect(() => {
    safeStorageSet("chatcrm.leads", JSON.stringify(leads));
  }, [leads]);

  React.useEffect(() => {
    safeStorageSet("chatcrm.buyers", JSON.stringify(buyers));
  }, [buyers]);

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
    let cancelled = false;

    async function hydrateBuyers() {
      if (!authToken) return;

      try {
        const storedBuyers = await fetchBackendBuyers(authToken);
        if (!cancelled) setBuyers(storedBuyers);
      } catch {
        if (!cancelled) setBuyerMessage("Buyer Network is using browser backup until the backend responds.");
      }
    }

    hydrateBuyers();
    return () => {
      cancelled = true;
    };
  }, [authToken]);

  React.useEffect(() => {
    let cancelled = false;

    async function hydrateTeamOnboarding() {
      if (!authToken || auth?.user?.role !== "Admin") {
        setTeamOnboardingRows([]);
        return;
      }

      try {
        const rows = await fetchAdminOnboardingStatuses(authToken);
        if (!cancelled) {
          setTeamOnboardingRows(rows);
          setTeamOnboardingMessage("");
        }
      } catch {
        if (!cancelled) setTeamOnboardingMessage("Could not load team onboarding yet.");
      }
    }

    hydrateTeamOnboarding();
    return () => {
      cancelled = true;
    };
  }, [authToken, auth?.user?.role]);
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

  const needsCallerOnboarding =
    auth?.user?.role === "Acquisition" && (!auth.user.profile_complete || !auth.user.agreement_signed);

  if (needsCallerOnboarding) {
    return (
      <OnboardingPage
        message={onboardingMessage}
        onDownloadAgreement={downloadCallerAgreement}
        onLogout={logout}
        onSaveProfile={saveCallerProfile}
        onSignAgreement={signCallerAgreement}
        user={auth.user}
      />
    );
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

  async function updateContactStatus(id, status) {
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

    if (!authToken) return null;

    try {
      const activity = await recordLeadActivity(
        id,
        {
          actionType: getActivityTypeForStatus(status),
          callOutcome: statusLabel,
          notes: statusLabel,
          followUpDate: status === "follow-up" ? lead?.followUpDate || "" : ""
        },
        authToken
      );
      updateLead(id, applyActivityToLead(activity));
      return activity;
    } catch {
      return null;
    }
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

    if (authToken) {
      selectedLeadIds.forEach((leadId) => {
        recordLeadActivity(
          leadId,
          {
            actionType: getActivityTypeForStatus(status),
            callOutcome: statusLabel,
            notes: `Bulk update: ${statusLabel}`
          },
          authToken
        ).catch(() => {});
      });
    }
  }

  function applyBulkStage(stage) {
    if (selectedLeadIds.length === 0 || !stage) return;
    setLeads((current) =>
      current.map((lead) => (selectedLeadIds.includes(lead.id) ? { ...lead, stage } : lead))
    );

    if (authToken) {
      selectedLeadIds.forEach((leadId) => {
        recordLeadActivity(
          leadId,
          {
            actionType: "status_changed",
            callOutcome: `Stage: ${stage}`,
            notes: `Bulk stage changed to ${stage}`
          },
          authToken
        ).catch(() => {});
      });
    }
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

  async function uploadBuyerFiles(event) {
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;

    setBuyerMessage(`Importing ${files.length} buyer file${files.length === 1 ? "" : "s"}...`);

    try {
      let latestBuyers = buyers;
      const warnings = [];

      for (const file of files) {
        const result = await importBuyerCsv(file, authToken);
        latestBuyers = sanitizeBuyers(result.buyers);
        warnings.push(...(result.warnings || []));
      }

      setBuyers(latestBuyers);
      setBuyerMessage(`${latestBuyers.length} buyer profile${latestBuyers.length === 1 ? "" : "s"} ready. ${warnings.join(" ")}`.trim());
    } catch {
      setBuyerMessage("Buyer import failed. Check that the file is a CSV with name, company, phone/email, county, ZIP, and buy box columns.");
    }

    event.target.value = "";
  }

  async function saveBuyerProfile(buyer) {
    const savedBuyer = await saveBuyerToBackend(buyer, authToken);
    setBuyers((current) => mergeBuyerProfiles(current, [savedBuyer]));
    setBuyerMessage(`${savedBuyer.name || savedBuyer.company} saved.`);
    return savedBuyer;
  }

  async function deleteBuyerProfile(id) {
    await deleteBuyerFromBackend(id, authToken);
    setBuyers((current) => current.filter((buyer) => buyer.id !== id));
    setBuyerMessage("Buyer removed.");
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
          {visibleMainViews.map((view) => (
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

      <section className={`workspace ${isAdmin ? "admin-workspace" : "caller-workspace"}`}>
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
            {isAdmin ? (
            <>
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
            </>
            ) : null}
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

        {activeView === "Dashboard" || (isAdmin && activeView === "Leads") ? (
          <>
            <section className="stats-grid" aria-label="Lead stats">
              <Stat label="Total Leads" value={leads.length} />
              <Stat label="Needs Follow-Up" value={followUps} />
              <Stat label="Hot Leads" value={hotLeads} />
              {isAdmin ? (
              <>
              <Stat label="Buyers" value={buyers.length} />
              <Stat label="PDF Imports" value={imports.length} />
              </>
              ) : null}
            </section>

            <section className="dashboard-support-grid" aria-label="Dashboard tools">
              <CommissionDashboardCard />
              <DailyQuoteCard authToken={authToken} />
            </section>
          </>
        ) : null}
        <section className={`content-grid ${(isAdmin && activeView === "Leads") || isFormOpen ? "" : "single-column"}`}>
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
            {isAdmin ? (
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
            ) : null}

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
                      {isRecentlyContactedByAnother(lead, auth.user) ? (
                        <small className="recent-contact-note">
                          Recently contacted by {lead.lastContactedBy} at {formatActivityTime(lead.lastContactedAt)}
                        </small>
                      ) : null}
                    </button>
                    <div className="lead-meta-grid">
                      <span className="lead-meta"><b>Stage</b>{lead.stage}</span>
                      <span className="lead-meta"><b>Score</b>{lead.score}</span>
                      <span className="lead-meta"><b>Assigned To</b>{lead.owner || "Unassigned"}</span>
                      <span className="lead-meta"><b>Source</b>{cleanSourceName(lead.source)}</span>
                      <span className="lead-meta"><b>Last By</b>{lead.lastContactedBy || "None"}</span>
                      <span className="lead-meta"><b>Last At</b>{lead.lastContactedAt ? formatActivityTime(lead.lastContactedAt) : "None"}</span>
                    </div>
                    <div className="row-actions">
                      <button onClick={() => setSelectedLeadId(lead.id)}>View</button>
                      <a href={buildGoogleMapsUrl(lead.address)} rel="noreferrer" target="_blank">Map</a>
                      <a href={buildStreetViewUrl(lead.address)} rel="noreferrer" target="_blank">Street</a>
                      <button onClick={() => openEditForm(lead)}>Edit</button>
                      {isAdmin ? (
                        <button className="danger-button" onClick={() => deleteLead(lead.id)}>
                          Delete
                        </button>
                      ) : null}
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

          {activeView === "Property Intelligence" ? (
            <PropertyIntelligenceView authToken={authToken} buyers={buyers} leads={leads} />
          ) : null}

          {activeView === "Buyer Network" ? (
            <BuyerNetworkView
              authToken={authToken}
              buyerFileInputRef={buyerFileInputRef}
              buyerMessage={buyerMessage}
              buyers={buyers}
              cadFileInputRef={cadFileInputRef}
              leads={leads}
              onDeleteBuyer={deleteBuyerProfile}
              onBuyerListUpdated={setBuyers}
              onSaveBuyer={saveBuyerProfile}
              onUploadBuyers={uploadBuyerFiles}
              setBuyerMessage={setBuyerMessage}
            />
          ) : null}

          {activeView === "Imports" ? (
            <ImportsView importMessage={importMessage} imports={imports} />
          ) : null}

          {activeView === "Analytics" ? (
            <AnalyticsView authToken={authToken} currentUser={auth.user} followUps={followUps} hotLeads={hotLeads} imports={imports} leads={leads} />
          ) : null}

          {activeView === "Training" ? (
            <TrainingView />
          ) : null}

          {activeView === "Leaderboard" ? (
            <LeaderboardView leads={leads} currentUser={auth.user} />
          ) : null}

          {activeView === "Profile" ? (
            <CallerProfileView currentUser={auth.user} leads={leads} />
          ) : null}


          {activeView === "Team" && auth.user?.role === "Admin" ? (
            <TeamOnboardingView
              authToken={authToken}
              message={teamOnboardingMessage}
              onRefresh={refreshTeamOnboarding}
              rows={teamOnboardingRows}
            />
          ) : null}

          {(isAdmin && activeView === "Leads") || isFormOpen ? (
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
          ) : null}
        </section>

        {selectedLead ? (
          <>
            <button className="detail-backdrop" aria-label="Close lead details" onClick={() => setSelectedLeadId(null)} />
            <LeadDetail
              authToken={authToken}
              currentUser={auth.user}
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

function OnboardingPage({ message, onDownloadAgreement, onLogout, onSaveProfile, onSignAgreement, user }) {
  const [profile, setProfile] = React.useState({
    name: user.profile_complete ? user.name || "" : "",
    email: user.email || ""
  });
  const [signature, setSignature] = React.useState(user.profile_complete ? user.name || "" : "");
  const [accepted, setAccepted] = React.useState(false);
  const [localMessage, setLocalMessage] = React.useState("");
  const [isSaving, setIsSaving] = React.useState(false);
  const profileReady = Boolean(user.profile_complete);
  const agreementReady = Boolean(user.agreement_signed);

  function updateProfile(field, value) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  async function submitProfile(event) {
    event.preventDefault();
    setIsSaving(true);
    setLocalMessage("");
    try {
      await onSaveProfile(profile);
    } catch {
      setLocalMessage("Could not save your profile yet. Check your name and email.");
    } finally {
      setIsSaving(false);
    }
  }

  async function submitSignature(event) {
    event.preventDefault();
    setIsSaving(true);
    setLocalMessage("");
    try {
      await onSignAgreement({ ...profile, signature, accepted });
    } catch {
      setLocalMessage("Could not save your signed agreement yet. Confirm every field is complete.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="onboarding-shell">
      <section className="onboarding-card">
        <div className="brand-block">
          <ChatCrmLogo />
          <div>
            <p className="eyebrow">ChatCRM Team Access</p>
            <h1>Complete Your Caller Setup</h1>
          </div>
        </div>

        <p className="onboarding-intro">
          Your login password stays the same. Add your real name and email, sign the partner agreement, then ChatCRM opens automatically.
        </p>

        <div className="onboarding-steps">
          <span className={profileReady ? "complete" : "active"}>1 Profile</span>
          <span className={agreementReady ? "complete" : profileReady ? "active" : ""}>2 Agreement</span>
          <span className={agreementReady ? "complete" : ""}>3 Download</span>
        </div>

        {!profileReady ? (
          <form className="onboarding-form" onSubmit={submitProfile}>
            <label>
              Full Name
              <input required value={profile.name} onChange={(event) => updateProfile("name", event.target.value)} />
            </label>
            <label>
              Email
              <input required type="email" value={profile.email} onChange={(event) => updateProfile("email", event.target.value)} />
            </label>
            <button className="primary-button" disabled={isSaving} type="submit">
              {isSaving ? "Saving..." : "Save Profile"}
            </button>
          </form>
        ) : (
          <form className="onboarding-form" onSubmit={submitSignature}>
            <div className="agreement-reader">
              <h2>Partner & Acquisition Agreement</h2>
              {partnerAgreementClauses.map((clause) => (
                <article key={clause.title}>
                  <h3>{clause.title}</h3>
                  <p>{clause.detail}</p>
                </article>
              ))}
              <div className="commission-line">
                15% under $10k / 20% at $10k-$19,999 / 22.5% at $20k-$34,999 / 25% at $35k+
              </div>
            </div>

            <label>
              Electronic Signature
              <input required value={signature} onChange={(event) => setSignature(event.target.value)} />
            </label>
            <label className="checkbox-line">
              <input checked={accepted} onChange={(event) => setAccepted(event.target.checked)} type="checkbox" />
              I have read and agree to the ChatCRM partner agreement.
            </label>
            <button className="primary-button" disabled={isSaving || !accepted} type="submit">
              {isSaving ? "Saving..." : "Sign & Download"}
            </button>
          </form>
        )}

        {agreementReady ? <button className="secondary-button" onClick={onDownloadAgreement}>Download Signed Agreement</button> : null}
        {message || localMessage ? <p className="import-status">{localMessage || message}</p> : null}
        <button className="ghost-button" onClick={onLogout}>Logout</button>
      </section>
    </main>
  );
}

function CommissionDashboardCard() {
  const [assignmentFee, setAssignmentFee] = React.useState("25000");
  const [closedDeals, setClosedDeals] = React.useState("0");
  const commission = calculateCallerCommission(assignmentFee, closedDeals);

  return (
    <section className="dashboard-card commission-card">
      <div>
        <p className="eyebrow">Commission</p>
        <h2>Real-Time Earnings</h2>
      </div>
      <div className="commission-inputs">
        <label>
          Assignment Fee
          <input min="0" type="number" value={assignmentFee} onChange={(event) => setAssignmentFee(event.target.value)} />
        </label>
        <label>
          Closed Deals
          <input min="0" type="number" value={closedDeals} onChange={(event) => setClosedDeals(event.target.value)} />
        </label>
      </div>
      <div className="commission-result">
        <span>{commission.tierLabel}</span>
        <strong>{formatMoney(commission.payout)}</strong>
        <small>{formatPercent(commission.totalRate)} total rate including {formatPercent(commission.bonusRate)} retention bonus</small>
      </div>
    </section>
  );
}

function DailyQuoteCard({ authToken }) {
  const [quote, setQuote] = React.useState({ quote: "Loading today's quote...", author: "", source: "ZenQuotes" });

  React.useEffect(() => {
    let cancelled = false;

    async function loadQuote() {
      if (!authToken) return;
      try {
        const result = await fetchDailyQuote(authToken);
        if (!cancelled) setQuote(result);
      } catch {
        if (!cancelled) setQuote({ quote: "Discipline turns opportunity into income.", author: "ChatCRM", source: "Fallback" });
      }
    }

    loadQuote();
    return () => {
      cancelled = true;
    };
  }, [authToken]);

  return (
    <section className="dashboard-card quote-card">
      <div>
        <p className="eyebrow">Daily Quote</p>
        <h2>Stay Sharp</h2>
      </div>
      <blockquote>{quote.quote}</blockquote>
      <p>{quote.author ? `- ${quote.author}` : quote.source}</p>
    </section>
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

function LeaderboardView({ leads, currentUser }) {
  const rows = buildCallerLeaderboard(leads);
  const myName = safeText(currentUser?.name || currentUser?.username);

  return (
    <div className="panel wide-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Leaderboard</p>
          <h2>Caller Activity</h2>
        </div>
      </div>

      <div className="leaderboard-list">
        {rows.length > 0 ? rows.map((row, index) => (
          <article className={`leaderboard-row ${row.name === myName ? "active" : ""}`} key={row.name}>
            <strong>#{index + 1}</strong>
            <span>{row.name}</span>
            <small>{row.calls} calls / {row.hotLeads} hot leads / {row.followUps} follow-ups</small>
          </article>
        )) : (
          <div className="empty-state">
            <h3>No activity yet</h3>
            <p>Caller rankings will build automatically from call outcomes and lead updates.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function CallerProfileView({ currentUser, leads }) {
  const myName = safeText(currentUser?.name || currentUser?.username);
  const myLeads = leads.filter((lead) => safeText(lead.lastContactedBy) === myName || safeText(lead.owner) === myName);
  const hotLeads = myLeads.filter((lead) => getLeadContactStatus(lead).value === "confirmed" || Number(lead.score) >= 80).length;

  return (
    <div className="panel wide-panel profile-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Profile</p>
          <h2>{myName || "Caller Profile"}</h2>
        </div>
      </div>

      <div className="detail-grid">
        <DetailItem label="Username" value={currentUser?.username || "Missing"} />
        <DetailItem label="Role" value={currentUser?.role || "Acquisition"} />
        <DetailItem label="Email" value={currentUser?.email || "Add during onboarding"} />
        <DetailItem label="My Leads" value={myLeads.length} />
        <DetailItem label="Hot Leads" value={hotLeads} />
        <DetailItem label="Agreement" value={currentUser?.agreement_signed ? "Signed" : "Needs Signature"} />
      </div>
    </div>
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

function PropertyIntelligenceView({ authToken, buyers, leads }) {
  const [dashboards, setDashboards] = React.useState([]);
  const [selectedCountyId, setSelectedCountyId] = React.useState("tx-dallas");
  const [message, setMessage] = React.useState("Loading county registry...");

  React.useEffect(() => {
    let cancelled = false;

    async function hydrateCounties() {
      try {
        const result = await fetchCountyDashboards(authToken);
        if (cancelled) return;
        setDashboards(result);
        if (result.length && !result.some((item) => item.county.id === selectedCountyId)) {
          setSelectedCountyId(result[0].county.id);
        }
        setMessage("");
      } catch {
        if (!cancelled) setMessage("County registry will load once the backend responds.");
      }
    }

    hydrateCounties();
    return () => {
      cancelled = true;
    };
  }, [authToken]);

  const selected = dashboards.find((item) => item.county.id === selectedCountyId) || dashboards[0];
  const selectedCounty = selected?.county;
  const selectedCountyKey = normalizeCountyName(selectedCounty?.countyName || "");
  const countyLeads = leads
    .filter((lead) => normalizeCountyName(lead.county) === selectedCountyKey)
    .slice(0, 14);
  const countyBuyers = buyers.filter((buyer) =>
    (buyer.counties || []).some((county) => normalizeCountyName(county) === selectedCountyKey)
  );
  const groupedDashboards = groupCountyDashboards(dashboards);

  return (
    <div className="panel wide-panel property-intelligence-view">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Property Intelligence</p>
          <h2>County Intelligence Module</h2>
        </div>
      </div>

      {message ? <p className="import-status">{message}</p> : null}

      <section className="county-intelligence-grid">
        <aside className="county-menu">
          {Object.entries(groupedDashboards).map(([market, items]) => (
            <div key={market}>
              <p className="eyebrow">{market}</p>
              {items.map((item) => (
                <button
                  className={item.county.id === selectedCountyId ? "active" : ""}
                  key={item.county.id}
                  onClick={() => setSelectedCountyId(item.county.id)}
                >
                  {item.county.countyName}
                  <span>{item.buyerMatches} buyers</span>
                </button>
              ))}
            </div>
          ))}
        </aside>

        {selectedCounty ? (
          <section className="county-dashboard">
            <div className="county-hero">
              <div>
                <p className="eyebrow">{selectedCounty.market}</p>
                <h3>{selectedCounty.countyName}</h3>
                <p>CAD, GIS, tax, parcel lookup, builder detection, and buyer matching rules are tracked here.</p>
              </div>
              <div className="county-source-actions">
                <a href={selectedCounty.cadUrl} rel="noreferrer" target="_blank">CAD</a>
                <a href={selectedCounty.gisUrl} rel="noreferrer" target="_blank">GIS</a>
                <a href={selectedCounty.taxUrl} rel="noreferrer" target="_blank">Tax</a>
                <a href={selectedCounty.parcelUrl} rel="noreferrer" target="_blank">Parcel</a>
              </div>
            </div>

            <div className="county-stat-grid">
              <Stat label="Leads" value={selected.leadCount} />
              <Stat label="Parcel Found" value={selected.parcelFound} />
              <Stat label="Buyer Matches" value={selected.buyerMatches || countyBuyers.length} />
              <Stat label="Avg Builder Score" value={selected.avgBuilderScore || "-"} />
            </div>

            <div className="county-readiness-grid">
              <CountyReadiness label="Parcel Lookup" ready={selectedCounty.supportsParcelLookup} />
              <CountyReadiness label="GIS" ready={selected.gisReady} />
              <CountyReadiness label="Tax Data" ready={selected.taxReady} />
              <CountyReadiness label="Public Enrichment" ready />
            </div>

            <section className="county-rules">
              <CountyRuleList title="Buyer Import Rules" items={selectedCounty.buyerImportRules} />
              <CountyRuleList title="Builder Detection" items={selectedCounty.builderDetectionRules} />
              <CountyRuleList title="Parcel Mapping" items={selectedCounty.parcelMapping} />
            </section>

            <section className="county-lead-snapshot">
              <div className="section-heading">
                <p className="eyebrow">Lead Snapshot</p>
                <h3>{selectedCounty.countyName} leads</h3>
              </div>

              {countyLeads.length > 0 ? (
                <div className="county-lead-list">
                  {countyLeads.map((lead) => (
                    <article className="county-lead-row" key={lead.id}>
                      <div>
                        <h3>{lead.address || "Missing address"}</h3>
                        <p>{getDisplayOwnerName(lead) || "Owner needed"}</p>
                      </div>
                      <span>{lead.parcelNumber ? "Parcel: Found" : "Parcel: Needed"}</span>
                      <span>{selected.gisReady ? "GIS: Ready" : "GIS: Manual"}</span>
                      <span>{lead.assessedValue ? "Tax Data: Found" : "Tax Data: Needed"}</span>
                      <span>{selected.buyerMatches || countyBuyers.length} buyer matches</span>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="mini-empty">
                  <p>No leads in this county yet.</p>
                </div>
              )}
            </section>
          </section>
        ) : (
          <div className="empty-state">
            <h3>No counties loaded</h3>
            <p>County registry is waiting on the backend.</p>
          </div>
        )}
      </section>
    </div>
  );
}

function CountyReadiness({ label, ready }) {
  return (
    <div className="county-readiness">
      <span className={`status-dot ${ready ? "green" : "orange"}`} />
      <strong>{label}</strong>
      <small>{ready ? "Ready" : "Needs setup"}</small>
    </div>
  );
}

function CountyRuleList({ title, items = [] }) {
  return (
    <div className="county-rule-card">
      <h3>{title}</h3>
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

const cadWizardSteps = [
  "Upload CSV",
  "Preview columns",
  "Map columns",
  "Detect buyers",
  "Score records",
  "Enrich contacts",
  "Review results",
  "Import selected"
];

function createCadWizardState() {
  return {
    step: 0,
    fileName: "",
    isRunning: false,
    preview: null,
    selectedCandidateIds: [],
    controls: {
      enrichmentEnabled: true,
      maxRecords: 500,
      minBuilderScore: 20,
      rateLimitMs: 750
    }
  };
}

function BuyerNetworkView({
  authToken,
  buyerFileInputRef,
  buyerMessage,
  buyers,
  cadFileInputRef,
  leads,
  onBuyerListUpdated,
  onDeleteBuyer,
  onSaveBuyer,
  onUploadBuyers,
  setBuyerMessage
}) {
  const dealOptions = leads.filter((lead) => ["Offer", "Closed", "Contracted", "Under Contract", "Follow Up"].includes(lead.stage));
  const firstDeal = dealOptions[0] || leads[0] || {};
  const [buyerDraft, setBuyerDraft] = React.useState(emptyBuyer);
  const [buyerSearch, setBuyerSearch] = React.useState("");
  const [dealDraft, setDealDraft] = React.useState(() => createDealDraft(firstDeal));
  const [matches, setMatches] = React.useState([]);
  const [isMatching, setIsMatching] = React.useState(false);
  const [isSavingBuyer, setIsSavingBuyer] = React.useState(false);
  const [isFindingBuyerPhones, setIsFindingBuyerPhones] = React.useState(false);
  const autoPhoneSearchRanRef = React.useRef(false);
  const [cadWizard, setCadWizard] = React.useState(() => createCadWizardState());

  const hotBuyers = buyers.filter((buyer) => normalizeText(buyer.activityStatus) === "hot").length;
  const tierABuyers = buyers.filter((buyer) => safeText(buyer.relationshipTier).toUpperCase() === "A").length;
  const coveredZips = new Set(buyers.flatMap((buyer) => buyer.zipCodes || [])).size;
  const filteredBuyers = buyers.filter((buyer) => {
    const haystack = [
      buyer.name,
      buyer.company,
      buyer.email,
      formatBuyerPhoneList(buyer),
      buyer.counties?.join(" "),
      buyer.zipCodes?.join(" "),
      buyer.propertyTypes?.join(" "),
      buyer.fundingType,
      buyer.builderType,
      buyer.activityStatus,
      buyer.relationshipTier,
      buyer.notes
    ]
      .join(" ")
      .toLowerCase();

    return haystack.includes(buyerSearch.toLowerCase());
  });


  const missingPublicPhoneBuyers = buyers.filter(
    (buyer) => getBuyerPhones(buyer).length === 0 && isLikelyPublicBusinessBuyer(buyer)
  );

  React.useEffect(() => {
    if (autoPhoneSearchRanRef.current || isFindingBuyerPhones || !authToken || missingPublicPhoneBuyers.length === 0) {
      return undefined;
    }

    autoPhoneSearchRanRef.current = true;
    let cancelled = false;

    async function runAutomaticPhoneSearch() {
      setIsFindingBuyerPhones(true);
      setBuyerMessage("Auto-searching public buyer phone numbers...");
      try {
        const result = await enrichPublicBuyerContacts(authToken, { maxBuyers: 25 });
        if (cancelled) return;
        onBuyerListUpdated(sanitizeBuyers(result.buyers));
        setBuyerMessage(
          `Auto phone search checked ${result.checkedCount || 0} buyer${result.checkedCount === 1 ? "" : "s"} and found ${result.phonesFound || 0} phone number${result.phonesFound === 1 ? "" : "s"}.`
        );
      } catch {
        if (!cancelled) setBuyerMessage("Auto phone search paused. Use Find Buyer Phones to try again.");
      } finally {
        if (!cancelled) setIsFindingBuyerPhones(false);
      }
    }

    runAutomaticPhoneSearch();
    return () => {
      cancelled = true;
    };
  }, [authToken, buyers.length]);

  function updateBuyerDraft(field, value) {
    const arrayFields = new Set(["phones", "socialLinks", "counties", "zipCodes", "propertyTypes"]);
    setBuyerDraft((current) => ({
      ...current,
      [field]: arrayFields.has(field) ? splitInputValues(value) : value
    }));
  }

  function updateDealDraft(field, value) {
    setDealDraft((current) => ({ ...current, [field]: value }));
  }

  function selectDeal(id) {
    const lead = leads.find((item) => item.id === id);
    setDealDraft(createDealDraft(lead || {}));
    setMatches([]);
  }

  async function submitBuyer(event) {
    event.preventDefault();
    setIsSavingBuyer(true);
    try {
      const savedBuyer = await onSaveBuyer({
        ...buyerDraft,
        phones: buyerDraft.phones.length ? buyerDraft.phones : splitInputValues(buyerDraft.phone),
        source: buyerDraft.source || "Manual Entry"
      });
      setBuyerDraft(emptyBuyer);
      setBuyerMessage(`${savedBuyer.name} added to Buyer Network.`);
    } catch {
      setBuyerMessage("Could not save buyer. Check the fields and try again.");
    } finally {
      setIsSavingBuyer(false);
    }
  }

  async function findBuyerMatches() {
    setIsMatching(true);
    setBuyerMessage("Matching buyers...");
    try {
      const result = await matchDealToBuyers(dealDraft, authToken);
      setMatches(result);
      setBuyerMessage(`${result.length} buyer match${result.length === 1 ? "" : "es"} found for this deal.`);
    } catch {
      setBuyerMessage("Buyer matching failed. Confirm the backend is online and try again.");
    } finally {
      setIsMatching(false);
    }
  }

  async function findMissingBuyerPhones() {
    if (buyers.length === 0) {
      setBuyerMessage("Add buyers first, then run public phone search.");
      return;
    }

    setIsFindingBuyerPhones(true);
    setBuyerMessage("Searching public business pages for missing buyer phone numbers...");
    try {
      const result = await enrichPublicBuyerContacts(authToken, { maxBuyers: 40 });
      const nextBuyers = sanitizeBuyers(result.buyers);
      onBuyerListUpdated(nextBuyers);
      setBuyerMessage(
        `Public phone search checked ${result.checkedCount || 0} buyer${result.checkedCount === 1 ? "" : "s"} and found ${result.phonesFound || 0} phone number${result.phonesFound === 1 ? "" : "s"}.`
      );
    } catch {
      setBuyerMessage("Could not finish public phone search. Try again with fewer buyers or refresh later.");
    } finally {
      setIsFindingBuyerPhones(false);
    }
  }
  function updateCadControl(field, value) {
    setCadWizard((current) => ({
      ...current,
      controls: {
        ...current.controls,
        [field]: field === "enrichmentEnabled" ? Boolean(value) : value
      }
    }));
  }

  function setCadStep(step) {
    setCadWizard((current) => ({ ...current, step }));
  }

  async function uploadDallasCadFiles(event) {
    const file = Array.from(event.target.files || [])[0];
    if (!file) return;

    setBuyerMessage("Reading Dallas CAD file...");
    setCadWizard((current) => ({ ...current, fileName: file.name, isRunning: true, step: 3 }));

    try {
      const result = await previewDallasCadUpload(file, cadWizard.controls, authToken);
      const candidates = sanitizeBuyers(result.buyers);
      const selectedIds = candidates
        .filter((buyer) => Number(buyer.builderScore) >= Number(cadWizard.controls.minBuilderScore || 0))
        .map((buyer) => buyer.id);

      setCadWizard((current) => ({
        ...current,
        fileName: file.name,
        isRunning: false,
        preview: { ...result, buyers: candidates },
        selectedCandidateIds: selectedIds,
        step: 6
      }));
      setBuyerMessage(`${candidates.length} Dallas CAD buyer/builder candidate${candidates.length === 1 ? "" : "s"} ready to review.`);
    } catch {
      setCadWizard((current) => ({ ...current, isRunning: false, step: 0 }));
      setBuyerMessage("Dallas CAD preview failed. Upload the official DCAD ZIP or CSV and try again.");
    }

    event.target.value = "";
  }

  function toggleCadCandidate(id) {
    setCadWizard((current) => {
      const selected = new Set(current.selectedCandidateIds);
      if (selected.has(id)) {
        selected.delete(id);
      } else {
        selected.add(id);
      }
      return { ...current, selectedCandidateIds: Array.from(selected) };
    });
  }

  function selectAllCadCandidates() {
    setCadWizard((current) => ({
      ...current,
      selectedCandidateIds: sanitizeBuyers(current.preview?.buyers || []).map((buyer) => buyer.id)
    }));
  }

  function clearCadCandidates() {
    setCadWizard((current) => ({ ...current, selectedCandidateIds: [] }));
  }

  async function refreshCadEnrichment() {
    if (!cadWizard.preview?.jobId) return;

    setBuyerMessage("Refreshing public contact sources...");
    setCadWizard((current) => ({ ...current, isRunning: true, step: 5 }));

    try {
      const result = await refreshDallasCadEnrichment(
        cadWizard.preview.jobId,
        cadWizard.selectedCandidateIds,
        cadWizard.controls,
        authToken
      );
      setCadWizard((current) => ({
        ...current,
        isRunning: false,
        preview: { ...current.preview, ...result, buyers: sanitizeBuyers(result.buyers) },
        step: 6
      }));
      setBuyerMessage("Public contact sources refreshed.");
    } catch {
      setCadWizard((current) => ({ ...current, isRunning: false, step: 6 }));
      setBuyerMessage("Could not refresh contact sources. You can still review and import the candidates.");
    }
  }

  async function importSelectedCadBuyers() {
    if (!cadWizard.preview?.jobId || cadWizard.selectedCandidateIds.length === 0) {
      setBuyerMessage("Select at least one CAD candidate to import.");
      return;
    }

    setBuyerMessage("Importing selected buyers/builders...");
    setCadWizard((current) => ({ ...current, isRunning: true, step: 7 }));

    try {
      const result = await importDallasCadSelection(cadWizard.preview.jobId, cadWizard.selectedCandidateIds, authToken);
      const nextBuyers = sanitizeBuyers(result.buyers);
      onBuyerListUpdated(nextBuyers);
      setCadWizard((current) => ({
        ...current,
        isRunning: false,
        preview: { ...current.preview, ...result },
        step: 7
      }));
      setBuyerMessage(
        `Imported ${result.newBuyers} buyer/builder profile${result.newBuyers === 1 ? "" : "s"}. ${result.duplicatesSkipped} duplicate${result.duplicatesSkipped === 1 ? "" : "s"} skipped.`
      );
    } catch {
      setCadWizard((current) => ({ ...current, isRunning: false, step: 6 }));
      setBuyerMessage("CAD import failed. Try again or lower the selected count.");
    }
  }

  const cadCandidates = sanitizeBuyers(cadWizard.preview?.buyers || []);
  const selectedCadCount = cadWizard.selectedCandidateIds.length;
  const cadSelectedSet = new Set(cadWizard.selectedCandidateIds);

  return (
    <div className="panel wide-panel buyer-network">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Buyer Network</p>
          <h2>Disposition Desk</h2>
        </div>
        <div className="lead-filters">
          <input
            accept=".csv,text/csv"
            className="file-input"
            multiple
            onChange={onUploadBuyers}
            ref={buyerFileInputRef}
            type="file"
          />
          <input
            accept=".zip,.csv,text/csv,application/zip,application/x-zip-compressed"
            className="file-input"
            onChange={uploadDallasCadFiles}
            ref={cadFileInputRef}
            type="file"
          />
          <button className="secondary-button" onClick={() => buyerFileInputRef.current?.click()}>
            <Upload size={18} />
            Upload Buyer CSV
          </button>
          <button className="secondary-button" onClick={() => cadFileInputRef.current?.click()}>
            <Upload size={18} />
            Dallas CAD Import
          </button>
          <button className="secondary-button" disabled={isFindingBuyerPhones || buyers.length === 0} onClick={findMissingBuyerPhones}>
            {isFindingBuyerPhones ? "Finding..." : "Find Buyer Phones"}
          </button>
          <button className="secondary-button" onClick={() => exportBuyersCsv(buyers)}>
            Export Buyers
          </button>
        </div>
      </div>

      {buyerMessage ? <p className="import-status">{buyerMessage}</p> : null}

      <section className="cad-import-wizard">
        <div className="cad-wizard-top">
          <div>
            <p className="eyebrow">Dallas CAD Wizard</p>
            <h3>Import Dallas CAD buyers/builders.</h3>
            <p>Upload DCAD ZIP/CSV, review the scores, then import only the buyers you choose.</p>
          </div>
          <button className="primary-button" disabled={cadWizard.isRunning} onClick={() => cadFileInputRef.current?.click()}>
            <Upload size={18} />
            {cadWizard.isRunning ? "Working..." : "Upload DCAD File"}
          </button>
        </div>

        <details className="cad-advanced-tools" open={Boolean(cadWizard.preview)}>
          <summary>
            <span>Import setup</span>
            <small>Preview columns, settings, and results</small>
          </summary>

          <div className="cad-stepper">
          {cadWizardSteps.map((step, index) => (
            <button
              className={index <= cadWizard.step ? "active" : ""}
              key={step}
              onClick={() => setCadStep(index)}
              type="button"
            >
              <span>{index + 1}</span>
              {step}
            </button>
          ))}
        </div>

        <div className="cad-admin-controls">
          <label className="toggle-row">
            <input
              checked={cadWizard.controls.enrichmentEnabled}
              onChange={(event) => updateCadControl("enrichmentEnabled", event.target.checked)}
              type="checkbox"
            />
            Public enrichment
          </label>
          <label>
            Max records
            <input
              min="25"
              onChange={(event) => updateCadControl("maxRecords", event.target.value)}
              type="number"
              value={cadWizard.controls.maxRecords}
            />
          </label>
          <label>
            Min score
            <input
              min="0"
              max="100"
              onChange={(event) => updateCadControl("minBuilderScore", event.target.value)}
              type="number"
              value={cadWizard.controls.minBuilderScore}
            />
          </label>
          <label>
            Rate limit ms
            <input
              min="0"
              onChange={(event) => updateCadControl("rateLimitMs", event.target.value)}
              type="number"
              value={cadWizard.controls.rateLimitMs}
            />
          </label>
          <button className="secondary-button" disabled={!cadWizard.preview?.jobId || cadWizard.isRunning} onClick={refreshCadEnrichment}>
            Refresh Contact Data
          </button>
        </div>

        {cadWizard.preview ? (
          <div className="cad-preview-grid">
            <section>
              <div className="section-heading">
                <p className="eyebrow">Preview Columns</p>
                <h3>{cadWizard.fileName || cadWizard.preview.fileName}</h3>
              </div>
              <div className="cad-column-list">
                {(cadWizard.preview.columns || []).slice(0, 18).map((column) => (
                  <span key={column}>{column}</span>
                ))}
              </div>
            </section>

            <section>
              <div className="section-heading">
                <p className="eyebrow">Map Columns</p>
                <h3>Auto-mapped fields</h3>
              </div>
              <div className="cad-map-list">
                {Object.entries(cadWizard.preview.mappedColumns || {}).slice(0, 10).map(([field, column]) => (
                  <span key={field}>
                    <b>{field}</b>
                    {column || "Not found"}
                  </span>
                ))}
              </div>
            </section>
          </div>
        ) : (
          <div className="mini-empty">
            <p>No CAD file loaded yet.</p>
          </div>
        )}

        {cadCandidates.length > 0 ? (
          <section className="cad-results">
            <div className="cad-results-header">
              <div>
                <p className="eyebrow">Review Results</p>
                <h3>{cadCandidates.length} candidates / {selectedCadCount} selected</h3>
              </div>
              <div className="lead-filters">
                <button className="secondary-button" onClick={selectAllCadCandidates}>Select All</button>
                <button className="secondary-button" onClick={clearCadCandidates}>Clear</button>
                <button className="secondary-button" onClick={() => exportBuyersCsv(cadCandidates)}>Export Enriched CSV</button>
                <button className="primary-button" disabled={cadWizard.isRunning || selectedCadCount === 0} onClick={importSelectedCadBuyers}>
                  Import Selected
                </button>
              </div>
            </div>

            <div className="cad-candidate-list">
              {cadCandidates.slice(0, 80).map((buyer) => (
                <article className="cad-candidate-row" key={buyer.id}>
                  <input
                    checked={cadSelectedSet.has(buyer.id)}
                    onChange={() => toggleCadCandidate(buyer.id)}
                    type="checkbox"
                  />
                  <BuyerScore score={buyer.builderScore || 0} />
                  <div>
                    <h3>{buyer.company || buyer.name}</h3>
                    <p>{buyer.buyerType || "unknown"} / {buyer.propertyCount || 0} properties / {buyer.vacantLotCount || 0} vacant lots</p>
                    <small>{formatBuyerPhoneList(buyer) || "Public phone not found yet"}</small>
                  </div>
                  <div className="buyer-buybox">
                    <b>{buyer.estimatedBuyBox || formatBuyBox(buyer)}</b>
                    <small>{[buyer.counties?.join(", "), buyer.zipCodes?.join(", ")].filter(Boolean).join(" / ") || "No geography"}</small>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ) : null}
        </details>
      </section>

      <div className="buyer-stats">
        <Stat label="Buyer Profiles" value={buyers.length} />
        <Stat label="Hot Buyers" value={hotBuyers} />
        <Stat label="A-Tier Buyers" value={tierABuyers} />
        <Stat label="ZIP Coverage" value={coveredZips} />
      </div>

      <details className="buyer-tools-drawer">
        <summary>
          <span>Buyer tools</span>
          <small>Add buyers or run a manual deal match when needed</small>
        </summary>
        <section className="buyer-workbench">
        <form className="buyer-card buyer-form" onSubmit={submitBuyer}>
          <div className="section-heading">
            <p className="eyebrow">Add Buyer</p>
            <h3>Buyer / Builder Profile</h3>
          </div>

          <div className="buyer-form-grid">
            <label>Name<input value={buyerDraft.name} onChange={(event) => updateBuyerDraft("name", event.target.value)} /></label>
            <label>Company<input value={buyerDraft.company} onChange={(event) => updateBuyerDraft("company", event.target.value)} /></label>
            <label>Phone<input value={buyerDraft.phone} onChange={(event) => updateBuyerDraft("phone", event.target.value)} /></label>
            <label>Email<input value={buyerDraft.email} onChange={(event) => updateBuyerDraft("email", event.target.value)} /></label>
            <label>Counties<input value={buyerDraft.counties.join(", ")} onChange={(event) => updateBuyerDraft("counties", event.target.value)} /></label>
            <label>ZIP Codes<input value={buyerDraft.zipCodes.join(", ")} onChange={(event) => updateBuyerDraft("zipCodes", event.target.value)} /></label>
            <label>Min Price<input value={buyerDraft.priceMin} onChange={(event) => updateBuyerDraft("priceMin", event.target.value)} /></label>
            <label>Max Price<input value={buyerDraft.priceMax} onChange={(event) => updateBuyerDraft("priceMax", event.target.value)} /></label>
            <label>Property Types<input value={buyerDraft.propertyTypes.join(", ")} onChange={(event) => updateBuyerDraft("propertyTypes", event.target.value)} /></label>
            <label>Funding
              <select value={buyerDraft.fundingType} onChange={(event) => updateBuyerDraft("fundingType", event.target.value)}>
                <option value="">Unknown</option>
                <option>Cash / POF</option>
                <option>Hard Money</option>
                <option>Private Money</option>
              </select>
            </label>
            <label>Activity
              <select value={buyerDraft.activityStatus} onChange={(event) => updateBuyerDraft("activityStatus", event.target.value)}>
                <option value="hot">Hot</option>
                <option value="warm">Warm</option>
                <option value="dead">Dead</option>
              </select>
            </label>
            <label>Tier
              <select value={buyerDraft.relationshipTier} onChange={(event) => updateBuyerDraft("relationshipTier", event.target.value)}>
                <option>A</option>
                <option>B</option>
                <option>C</option>
              </select>
            </label>
          </div>

          <label>Notes<textarea value={buyerDraft.notes} onChange={(event) => updateBuyerDraft("notes", event.target.value)} /></label>
          <button className="primary-button" disabled={isSavingBuyer} type="submit">
            <Plus size={18} />
            {isSavingBuyer ? "Saving..." : "Save Buyer"}
          </button>
        </form>

        <section className="buyer-card match-card">
          <div className="section-heading">
            <p className="eyebrow">Auto-Match</p>
            <h3>Best Buyers For This Deal</h3>
          </div>

          <div className="buyer-form-grid">
            <label>Contracted Lead
              <select value={dealDraft.id} onChange={(event) => selectDeal(event.target.value)}>
                <option value="">Manual Deal</option>
                {dealOptions.map((lead) => (
                  <option key={lead.id} value={lead.id}>{lead.address}</option>
                ))}
              </select>
            </label>
            <label>Address<input value={dealDraft.address} onChange={(event) => updateDealDraft("address", event.target.value)} /></label>
            <label>County<input value={dealDraft.county} onChange={(event) => updateDealDraft("county", event.target.value)} /></label>
            <label>ZIP<input value={dealDraft.zipCode} onChange={(event) => updateDealDraft("zipCode", event.target.value)} /></label>
            <label>Property Type<input value={dealDraft.propertyType} onChange={(event) => updateDealDraft("propertyType", event.target.value)} /></label>
            <label>Deal Price<input value={dealDraft.price} onChange={(event) => updateDealDraft("price", event.target.value)} /></label>
            <label>Rehab Level
              <select value={dealDraft.rehabLevel} onChange={(event) => updateDealDraft("rehabLevel", event.target.value)}>
                <option value="">Unknown</option>
                <option>Light</option>
                <option>Medium</option>
                <option>Heavy</option>
                <option>New Build</option>
              </select>
            </label>
          </div>

          <button className="primary-button" disabled={isMatching || buyers.length === 0} onClick={findBuyerMatches} type="button">
            <Map size={18} />
            {isMatching ? "Matching..." : "Find Best Buyers"}
          </button>

          <div className="match-results">
            {matches.length > 0 ? (
              matches.slice(0, 8).map((match) => (
                <article className="match-row" key={match.buyer.id}>
                  <BuyerScore score={match.score} />
                  <div>
                    <h3>{match.buyer.company || match.buyer.name}</h3>
                    <p>{match.buyer.name}{match.buyer.company && match.buyer.name ? ` / ${match.buyer.company}` : ""}</p>
                    <small>{formatBuyerPhoneList(match.buyer) || match.buyer.email || "Contact needed"}</small>
                    <div className="reason-list">
                      {match.reasons.map((reason) => <span key={reason}>{reason}</span>)}
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <div className="mini-empty">
                <p>No matches run yet.</p>
              </div>
            )}
          </div>
        </section>
              </section>
      </details>

      <section className="buyer-list-section">
        <div className="panel-header compact-header">
          <div>
            <p className="eyebrow">Database</p>
            <h2>Buyer / Builder Profiles</h2>
          </div>
          <div className="search-box compact-search">
            <Search size={16} />
            <input
              onChange={(event) => setBuyerSearch(event.target.value)}
              placeholder="Search buyers, ZIPs, counties, companies..."
              value={buyerSearch}
            />
          </div>
        </div>

        {filteredBuyers.length > 0 ? (
          <div className="buyer-list">
            {filteredBuyers.slice(0, 120).map((buyer) => (
              <article className="buyer-row" key={buyer.id}>
                <div>
                  <h3>{buyer.company || buyer.name}</h3>
                  <p>{buyer.name}{buyer.company && buyer.name ? ` / ${buyer.company}` : ""}</p>
                  <small>{formatBuyerPhoneList(buyer) || buyer.email || "Contact needed"}</small>
                </div>
                <div className="buyer-tags">
                  <span>{buyer.builderScore ? `${buyer.builderScore} Score` : "Unscored"}</span>
                  <span>{buyer.buyerType || "unknown"}</span>
                  <span>{safeText(buyer.relationshipTier).toUpperCase() || "C"} Tier</span>
                  <span>{buyer.activityStatus || "warm"}</span>
                  <span>{buyer.fundingType || "Funding Unknown"}</span>
                </div>
                <div className="buyer-buybox">
                  <b>{formatBuyBox(buyer)}</b>
                  <small>{[buyer.counties?.join(", "), buyer.zipCodes?.join(", ")].filter(Boolean).join(" / ") || "No geography"}</small>
                </div>
                <button className="ghost-button danger-text" onClick={() => onDeleteBuyer(buyer.id)}>Delete</button>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <h3>No buyer profiles yet</h3>
            <p>Upload a buyer CSV or add your first buyer profile.</p>
          </div>
        )}
      </section>
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

function AnalyticsView({ authToken, currentUser, followUps, hotLeads, imports, leads }) {
  const reviewed = leads.filter((lead) => !lead.needsReview).length;
  const reviewNeeded = leads.filter((lead) => lead.needsReview).length;
  const [recentActivity, setRecentActivity] = React.useState([]);
  const [dailyCalls, setDailyCalls] = React.useState([]);
  const [activityMessage, setActivityMessage] = React.useState("");

  React.useEffect(() => {
    let cancelled = false;

    async function hydrateActivityDashboard() {
      if (!authToken) return;

      try {
        const [activityResult, countsResult] = await Promise.all([
          fetchRecentTeamActivity(authToken),
          fetchDailyCallCounts(authToken)
        ]);
        if (cancelled) return;
        setRecentActivity(activityResult);
        setDailyCalls(countsResult);
        setActivityMessage("");
      } catch {
        if (!cancelled) setActivityMessage("Team activity will load once the backend responds.");
      }
    }

    hydrateActivityDashboard();
    return () => {
      cancelled = true;
    };
  }, [authToken]);

  return (
    <div className="panel wide-panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Analytics</p>
          <h2>{currentUser?.role === "Admin" ? "Team Snapshot" : "My Snapshot"}</h2>
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

      <div className="team-activity-grid">
        <section className="team-activity-card">
          <div className="section-heading compact-heading">
            <p className="eyebrow">Today</p>
            <h2>Calls By User</h2>
          </div>
          {dailyCalls.length > 0 ? (
            <div className="daily-call-list">
              {dailyCalls.map((item) => (
                <div key={item.userId}>
                  <span>{item.userName}</span>
                  <strong>{item.count}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="mini-empty">
              <p>No calls logged today.</p>
            </div>
          )}
        </section>

        <section className="team-activity-card">
          <div className="section-heading compact-heading">
            <p className="eyebrow">Team Feed</p>
            <h2>Recent Activity</h2>
          </div>
          {activityMessage ? <p className="parcel-message">{activityMessage}</p> : null}
          {recentActivity.length > 0 ? (
            <div className="activity-list compact-activity-list">
              {recentActivity.slice(0, 10).map((activity) => (
                <article className="activity-item" key={activity.id}>
                  <div>
                    <strong>{activity.userNameSnapshot}</strong>
                    <span>{getActivityActionLabel(activity.actionType)}</span>
                  </div>
                  <p>
                    {activity.leadAddress ? <b>{activity.leadAddress}</b> : null}
                    {activity.callOutcome ? <span>{activity.callOutcome}</span> : null}
                  </p>
                  <small>{formatActivityTime(activity.createdAt)}</small>
                </article>
              ))}
            </div>
          ) : (
            <div className="mini-empty">
              <p>No team activity logged yet.</p>
            </div>
          )}
        </section>
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

function TeamOnboardingView({ authToken, message, onRefresh, rows }) {
  const signedCount = rows.filter((row) => row.agreementSigned).length;
  const profileCount = rows.filter((row) => row.profileComplete).length;
  const missingNames = rows.filter((row) => !row.name && row.role !== "Admin").length;

  async function downloadAgreement(row) {
    try {
      await downloadAdminSignedAgreement(row.username, authToken);
    } catch {
      window.alert("Signed agreement is not ready to download yet.");
    }
  }

  return (
    <div className="panel wide-panel team-onboarding">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Team</p>
          <h2>Onboarding Tracker</h2>
        </div>
        <button className="secondary-button" onClick={onRefresh}>Refresh</button>
      </div>

      <p className="team-onboarding-note">
        Watch each caller finish their first login, add their name and email, sign the agreement, and download the signed PDF.
      </p>

      <div className="team-summary-grid">
        <Stat label="Total Accounts" value={rows.length} />
        <Stat label="Profiles Done" value={profileCount} />
        <Stat label="Agreements Signed" value={signedCount} />
        <Stat label="Names Missing" value={missingNames} />
      </div>

      {message ? <div className="mini-empty"><p>{message}</p></div> : null}

      <div className="onboarding-table-wrap">
        <table className="onboarding-table">
          <thead>
            <tr>
              <th>Login</th>
              <th>Role</th>
              <th>Name</th>
              <th>Email</th>
              <th>Profile</th>
              <th>Agreement</th>
              <th>Signed</th>
              <th>PDF</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.username}>
                <td><strong>{row.username}</strong><span>{row.displayName}</span></td>
                <td>{row.role}</td>
                <td>{row.name || "Waiting"}</td>
                <td>{row.email || "Waiting"}</td>
                <td><StatusPill good={row.profileComplete} label={row.profileComplete ? "Complete" : "Missing"} /></td>
                <td><StatusPill good={row.agreementSigned} label={row.agreementSigned ? "Signed" : "Not signed"} /></td>
                <td>{row.signedAt ? formatActivityTime(row.signedAt) : row.role === "Admin" ? "Admin" : "Waiting"}</td>
                <td>
                  {row.downloadUrl ? (
                    <button className="mini-action-button" onClick={() => downloadAgreement(row)}>Download</button>
                  ) : (
                    <span className="muted-table-text">Not ready</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatusPill({ good, label }) {
  return <span className={`status-pill ${good ? "good" : "warn"}`}>{label}</span>;
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
  authToken,
  currentUser,
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
  const [parcel, setParcel] = React.useState(() => createEmptyParcelRecord(lead));
  const [parcelMessage, setParcelMessage] = React.useState("");
  const [isParcelSaving, setIsParcelSaving] = React.useState(false);
  const [buyerMatches, setBuyerMatches] = React.useState([]);
  const [buyerMatchMessage, setBuyerMatchMessage] = React.useState("");
  const [isFindingBuyers, setIsFindingBuyers] = React.useState(false);
  const [activities, setActivities] = React.useState([]);
  const [leadLock, setLeadLock] = React.useState(null);
  const [activityMessage, setActivityMessage] = React.useState("");
  const notesSnapshotRef = React.useRef(lead.notes || "");
  const ownerPlaceholder =
    rawOwnerName && rawOwnerName !== "Unknown Owner"
      ? "Replace parsed text with owner name"
      : "Enter owner name";
  const canUseAdminDealTools = currentUser?.role === "Admin";

  React.useEffect(() => {
    let cancelled = false;
    setParcel(createEmptyParcelRecord(lead));
    setParcelMessage("Loading parcel research...");

    async function hydrateParcel() {
      if (!canUseAdminDealTools || !authToken || !lead.id) {
        setParcelMessage("");
        return;
      }

      try {
        const savedParcel = await fetchParcelIntelligence(lead.id, authToken);
        if (!cancelled) {
          setParcel(mergeParcelWithLead(savedParcel, lead));
          setParcelMessage(savedParcel.updatedAt ? "Parcel research loaded." : "");
        }
      } catch {
        if (!cancelled) setParcelMessage("Parcel research will save once the backend responds.");
      }
    }

    hydrateParcel();
    return () => {
      cancelled = true;
    };
  }, [authToken, lead.id, canUseAdminDealTools]);

  React.useEffect(() => {
    setBuyerMatches([]);
    setBuyerMatchMessage("");
    setIsFindingBuyers(false);
    setActivities([]);
    setLeadLock(null);
    setActivityMessage("");
    notesSnapshotRef.current = lead.notes || "";
  }, [lead.id]);

  React.useEffect(() => {
    let cancelled = false;

    async function hydrateActivity() {
      if (!authToken || !lead.id) return;

      try {
        const [activityResult, lockResult] = await Promise.all([
          fetchLeadActivity(lead.id, authToken),
          lockLeadForUser(lead.id, authToken)
        ]);

        if (cancelled) return;
        setActivities(activityResult);
        setLeadLock(lockResult);
        if (lockResult?.lockedByUserId) {
          onUpdate({
            lockedByUserId: lockResult.lockedByUserId,
            lockedByUserName: lockResult.lockedByUserName,
            lockedUntil: lockResult.lockedUntil
          });
        }
      } catch {
        if (!cancelled) setActivityMessage("Activity timeline will load once the backend responds.");
      }
    }

    hydrateActivity();
    return () => {
      cancelled = true;
    };
  }, [authToken, lead.id]);

  function saveMyMapsUrl(value) {
    setMyMapsUrl(value);
    safeStorageSet("chatcrm.myMapsUrl", value);
  }

  function updateParcelField(field, value) {
    setParcel((current) => ({ ...current, [field]: value }));
  }

  function toggleParcelLayer(layer) {
    setParcel((current) => {
      const layers = Array.isArray(current.mapLayers) ? current.mapLayers : [];
      return {
        ...current,
        mapLayers: layers.includes(layer) ? layers.filter((item) => item !== layer) : [...layers, layer]
      };
    });
  }

  async function saveParcel() {
    setIsParcelSaving(true);
    setParcelMessage("Saving parcel research...");

    try {
      const savedParcel = await saveParcelIntelligence(mergeParcelWithLead(parcel, lead), authToken);
      setParcel(mergeParcelWithLead(savedParcel, lead));
      setParcelMessage("Parcel Intelligence saved.");

      const leadUpdates = {};
      if (savedParcel.apn && savedParcel.apn !== lead.parcelNumber) leadUpdates.parcelNumber = savedParcel.apn;
      if (savedParcel.county && savedParcel.county !== lead.county) leadUpdates.county = savedParcel.county;
      if (Object.keys(leadUpdates).length) onUpdate(leadUpdates);
    } catch {
      setParcelMessage("Could not save Parcel Intelligence yet.");
    } finally {
      setIsParcelSaving(false);
    }
  }

  async function findBuyersForProperty() {
    setIsFindingBuyers(true);
    setBuyerMatchMessage("Finding best buyers for this property...");

    try {
      const result = await matchDealToBuyers(createDealDraft(lead), authToken);
      setBuyerMatches(result);
      setBuyerMatchMessage(`${result.length} buyer match${result.length === 1 ? "" : "es"} found.`);
    } catch {
      setBuyerMatchMessage("Could not match buyers yet. Confirm the backend is online.");
    } finally {
      setIsFindingBuyers(false);
    }
  }

  async function addLeadActivity(activity) {
    if (!authToken || !lead.id) return null;

    try {
      const savedActivity = await recordLeadActivity(lead.id, activity, authToken);
      setActivities((current) => [savedActivity, ...current.filter((item) => item.id !== savedActivity.id)]);
      if (["called", "call_started", "voicemail", "not_interested", "wrong_number", "status_changed", "follow_up_set", "hot_lead_marked"].includes(savedActivity.actionType)) {
        onUpdate(applyActivityToLead(savedActivity));
      } else {
        onUpdate({ lastActivityAction: savedActivity.actionType });
      }
      return savedActivity;
    } catch {
      setActivityMessage("Could not save activity yet.");
      return null;
    }
  }

  function handleCallClick(phone = "") {
    addLeadActivity({
      actionType: "call_started",
      callOutcome: "Call started",
      notes: phone ? `Clicked call for ${formatPhone(phone)}` : "Clicked call",
      phoneNumber: phone
    });
  }

  async function handleStatusChange(status) {
    const activity = await onStatusChange(status);
    if (activity) {
      setActivities((current) => [activity, ...current.filter((item) => item.id !== activity.id)]);
    }
  }

  function handleFollowUpChange(value) {
    onUpdate({ followUpDate: value, stage: value ? "Follow Up" : lead.stage });
    if (value) {
      addLeadActivity({
        actionType: "follow_up_set",
        callOutcome: "Follow Up",
        notes: `Follow-up set for ${value}`,
        followUpDate: value
      });
    }
  }

  function handleNotesBlur() {
    const currentNotes = lead.notes || "";
    if (currentNotes === notesSnapshotRef.current) return;
    notesSnapshotRef.current = currentNotes;
    addLeadActivity({
      actionType: "note_added",
      callOutcome: "Note Updated",
      notes: "Lead notes updated."
    });
  }

  function handleMarkReviewed() {
    onMarkReviewed();
    addLeadActivity({
      actionType: "status_changed",
      callOutcome: "Reviewed",
      notes: "Lead marked reviewed."
    });
  }

  function handleMarkReviewedAndNext() {
    addLeadActivity({
      actionType: "status_changed",
      callOutcome: "Reviewed",
      notes: "Lead marked reviewed and moved to next lead."
    });
    onMarkReviewedAndNext();
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

      {isActiveLeadLock(leadLock) && leadLock.lockedByUserId !== currentUser?.username ? (
        <div className="recent-contact-warning">
          Recently opened by {leadLock.lockedByUserName} until {formatActivityTime(leadLock.lockedUntil)}.
          Admin can continue if needed.
        </div>
      ) : null}

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
        <ContactLink disabled={!phoneHref} href={phoneHref} label="Call" onClick={() => handleCallClick(phones[0])} />
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
                  <a href={`tel:${phone.replace(/[^\d+]/g, "")}`} onClick={() => handleCallClick(phone)}>{formatPhone(phone)}</a>
                  <a href={buildGoogleVoiceUrl(phone)} onClick={() => handleCallClick(phone)} rel="noreferrer" target="_blank">Voice</a>
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

      {canUseAdminDealTools ? (
      <details className="tool-section" open>
        <summary>Property / Offer Tools</summary>
        <section className="parcel-intelligence-panel simple-parcel-panel">
          <div className="panel-header compact-header">
            <div>
              <p className="eyebrow">Parcel Intelligence</p>
              <h2>Parcel Snapshot</h2>
            </div>
            <button className="primary-button" disabled={isParcelSaving} onClick={saveParcel} type="button">
              {isParcelSaving ? "Saving..." : "Save Parcel"}
            </button>
          </div>

          {parcelMessage ? <p className="parcel-message">{parcelMessage}</p> : null}

          <div className="property-input-grid parcel-core-grid">
            <label className="detail-field">
              APN
              <input value={parcel.apn || ""} onChange={(event) => updateParcelField("apn", event.target.value)} />
            </label>
            <label className="detail-field">
              Acreage
              <input value={parcel.acreage || ""} onChange={(event) => updateParcelField("acreage", event.target.value)} />
            </label>
            <label className="detail-field">
              Zoning
              <input value={parcel.zoning || ""} onChange={(event) => updateParcelField("zoning", event.target.value)} />
            </label>
            <label className="detail-field">
              Flood Zone
              <input value={parcel.floodZone || ""} onChange={(event) => updateParcelField("floodZone", event.target.value)} />
            </label>
            <label className="detail-field">
              Utilities
              <input value={parcel.utilityAvailability || ""} onChange={(event) => updateParcelField("utilityAvailability", event.target.value)} />
            </label>
            <label className="detail-field">
              Tax Status
              <select value={parcel.taxDelinquencyStatus || ""} onChange={(event) => updateParcelField("taxDelinquencyStatus", event.target.value)}>
                <option value="">Unknown</option>
                <option>Current</option>
                <option>Delinquent</option>
                <option>Payment Plan</option>
                <option>Needs Review</option>
              </select>
            </label>
            <label className="detail-field">
              Research Status
              <select value={parcel.researchStatus || "Needs Research"} onChange={(event) => updateParcelField("researchStatus", event.target.value)}>
                <option>Needs Research</option>
                <option>In Review</option>
                <option>Verified</option>
                <option>Missing Data</option>
              </select>
            </label>
          </div>

          <details className="parcel-advanced">
            <summary>More Parcel Details</summary>
            <div className="property-input-grid parcel-input-grid">
              <label className="detail-field">
                County
                <input value={parcel.county || ""} onChange={(event) => updateParcelField("county", event.target.value)} />
              </label>
              <label className="detail-field">
                Lot Dimensions
                <input value={parcel.lotDimensions || ""} onChange={(event) => updateParcelField("lotDimensions", event.target.value)} />
              </label>
              <label className="detail-field">
                Land Use
                <input value={parcel.landUse || ""} onChange={(event) => updateParcelField("landUse", event.target.value)} />
              </label>
              <label className="detail-field">
                Tax Balance
                <input value={parcel.taxBalance || ""} onChange={(event) => updateParcelField("taxBalance", event.target.value)} />
              </label>
              <label className="detail-field">
                Assessed Value
                <input value={parcel.assessedValue || ""} onChange={(event) => updateParcelField("assessedValue", event.target.value)} />
              </label>
              <label className="detail-field">
                Land Value
                <input value={parcel.landValue || ""} onChange={(event) => updateParcelField("landValue", event.target.value)} />
              </label>
              <label className="detail-field">
                Improvement Value
                <input value={parcel.improvementValue || ""} onChange={(event) => updateParcelField("improvementValue", event.target.value)} />
              </label>
              <label className="detail-field">
                Last Sale Date
                <input value={parcel.lastSaleDate || ""} onChange={(event) => updateParcelField("lastSaleDate", event.target.value)} />
              </label>
              <label className="detail-field">
                Last Sale Price
                <input value={parcel.lastSalePrice || ""} onChange={(event) => updateParcelField("lastSalePrice", event.target.value)} />
              </label>
              <label className="detail-field">
                Ownership Duration
                <input value={parcel.ownershipDuration || ""} onChange={(event) => updateParcelField("ownershipDuration", event.target.value)} />
              </label>
              <label className="detail-field">
                Mortgage Estimate
                <input value={parcel.mortgageEstimate || ""} onChange={(event) => updateParcelField("mortgageEstimate", event.target.value)} />
              </label>
              <label className="detail-field">
                Estimated Equity
                <input value={parcel.estimatedEquity || ""} onChange={(event) => updateParcelField("estimatedEquity", event.target.value)} />
              </label>
              <label className="detail-field">
                Opportunity Zone
                <select value={parcel.opportunityZone || ""} onChange={(event) => updateParcelField("opportunityZone", event.target.value)}>
                  <option value="">Unknown</option>
                  <option>Yes</option>
                  <option>No</option>
                  <option>Needs Review</option>
                </select>
              </label>
            </div>

            <div className="parcel-layer-grid">
              {parcelMapLayers.map((layer) => (
                <label key={layer}>
                  <input
                    checked={(parcel.mapLayers || []).includes(layer)}
                    onChange={() => toggleParcelLayer(layer)}
                    type="checkbox"
                  />
                  {layer}
                </label>
              ))}
            </div>

            <label className="detail-field">
              Legal Description
              <textarea value={parcel.legalDescription || ""} onChange={(event) => updateParcelField("legalDescription", event.target.value)} />
            </label>
            <label className="detail-field">
              Ownership History
              <textarea value={parcel.ownershipHistory || ""} onChange={(event) => updateParcelField("ownershipHistory", event.target.value)} />
            </label>
            <label className="detail-field">
              Parcel Notes
              <textarea value={parcel.notes || ""} onChange={(event) => updateParcelField("notes", event.target.value)} />
            </label>
          </details>
        </section>

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
      ) : null}

      {canUseAdminDealTools ? (
      <section className="property-buyer-panel">
        <div className="panel-header compact-header">
          <div>
            <p className="eyebrow">Disposition</p>
            <h2>Find Buyers</h2>
          </div>
          <button className="primary-button" disabled={isFindingBuyers} onClick={findBuyersForProperty} type="button">
            {isFindingBuyers ? "Matching..." : "Find Best Buyers"}
          </button>
        </div>

        <p className="buyer-match-help">
          Matches use county, ZIP, property type, price, buyer activity, and builder score.
        </p>
        {buyerMatchMessage ? <p className="parcel-message">{buyerMatchMessage}</p> : null}

        {buyerMatches.length > 0 ? (
          <div className="property-buyer-list">
            {buyerMatches.slice(0, 8).map((match) => (
              <PropertyBuyerMatch match={match} key={match.buyer.id} />
            ))}
          </div>
        ) : (
          <div className="mini-empty">
            <p>No buyer match run yet.</p>
          </div>
        )}
      </section>
      ) : null}

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
          onChange={(event) => handleFollowUpChange(event.target.value)}
        />
      </label>

      <label className="detail-field">
        Notes
        <textarea value={lead.notes || ""} onBlur={handleNotesBlur} onChange={(event) => onUpdate({ notes: event.target.value })} />
      </label>

      <ActivityTimeline activities={activities} message={activityMessage} />

      <div className="disposition-section">
        <p>Call Result</p>
        <div className="disposition-grid">
          {contactStatuses.map((status) => (
            <button
              className={`disposition-button ${getLeadContactStatus(lead).value === status.value ? "active" : ""}`}
              key={status.value}
              onClick={() => handleStatusChange(status.value)}
            >
              <span className={`status-dot ${status.color}`} />
              {status.label}
            </button>
          ))}
        </div>
      </div>

      <div className="detail-actions">
        {canUseAdminDealTools ? <button className="agreement-button" onClick={onStartAgreement}>Create Purchase Agreement</button> : null}
        {lead.needsReview ? (
          <>
            <button className="secondary-button" onClick={handleMarkReviewed}>Mark Reviewed</button>
            <button className="primary-button" onClick={handleMarkReviewedAndNext}>Reviewed + Next</button>
          </>
        ) : null}
        {canUseAdminDealTools ? <button className="secondary-button" onClick={onEdit}>Edit Full Lead</button> : null}
      </div>
    </section>
  );
}

function PropertyBuyerMatch({ match }) {
  const buyer = match?.buyer || {};
  const phones = getBuyerPhones(buyer);
  const primaryPhone = phones[0] || "";
  const phoneHref = primaryPhone ? `tel:${primaryPhone.replace(/[^\d+]/g, "")}` : "";
  const buyerName = buyer.company || buyer.name || "Buyer name needed";

  return (
    <article className="property-buyer-row">
      <BuyerScore score={match.score || 0} />
      <div className="property-buyer-main">
        <h3>{buyerName}</h3>
        <p>{buyer.buyerType || "buyer"} / {buyer.propertyCount || 0} properties / {buyer.relationshipTier || "C"} tier</p>
        <small>{formatBuyerPhoneList(buyer) || buyer.email || "Phone not found yet"}</small>
        <div className="reason-list">
          {(match.reasons || []).slice(0, 4).map((reason) => <span key={reason}>{reason}</span>)}
        </div>
      </div>
      <div className="property-buyer-actions">
        {primaryPhone ? <a href={phoneHref}>Call</a> : <a href={buildBuyerContactSearchUrl(buyer)} rel="noreferrer" target="_blank">Research Phone</a>}
        {primaryPhone ? <a href={buildGoogleVoiceUrl(primaryPhone)} rel="noreferrer" target="_blank">Voice</a> : null}
        {buyer.email ? <a href={`mailto:${buyer.email}`}>Email</a> : null}
        {buyer.website ? <a href={buyer.website} rel="noreferrer" target="_blank">Website</a> : null}
        <a href={buildBuyerContactSearchUrl(buyer)} rel="noreferrer" target="_blank">Public Search</a>
      </div>
    </article>
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

function ActivityTimeline({ activities, message }) {
  return (
    <section className="activity-timeline" aria-label="Lead activity timeline">
      <div className="section-heading compact-heading">
        <p className="eyebrow">Activity</p>
        <h2>Call Timeline</h2>
      </div>

      {message ? <p className="parcel-message">{message}</p> : null}

      {activities.length > 0 ? (
        <div className="activity-list">
          {activities.slice(0, 12).map((activity) => (
            <article className="activity-item" key={activity.id}>
              <div>
                <strong>{activity.userNameSnapshot}</strong>
                <span>{getActivityActionLabel(activity.actionType)}</span>
              </div>
              <p>
                {activity.callOutcome ? <b>{activity.callOutcome}</b> : null}
                {activity.notes ? <span>{activity.notes}</span> : null}
              </p>
              <small>{formatActivityTime(activity.createdAt)}</small>
            </article>
          ))}
        </div>
      ) : (
        <div className="mini-empty">
          <p>No activity logged yet.</p>
        </div>
      )}
    </section>
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

function ContactLink({ disabled = false, href, label, onClick }) {
  if (disabled) {
    return <span className="quick-link disabled">{label}</span>;
  }

  return (
    <a className="quick-link" href={href} onClick={onClick} rel="noreferrer" target={href?.startsWith("http") ? "_blank" : undefined}>
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

function loadBuyers() {
  try {
    const savedBuyers = JSON.parse(safeStorageGet("chatcrm.buyers"));
    return sanitizeBuyers(savedBuyers);
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
      followUpDate: safeText(lead.followUpDate),
      lastContactedUserId: safeText(lead.lastContactedUserId),
      lastContactedBy: safeText(lead.lastContactedBy),
      lastContactedAt: safeText(lead.lastContactedAt),
      lastActivityAction: safeText(lead.lastActivityAction),
      lockedByUserId: safeText(lead.lockedByUserId),
      lockedByUserName: safeText(lead.lockedByUserName),
      lockedUntil: safeText(lead.lockedUntil)
    }));
}

function sanitizeLeadActivities(value) {
  if (!Array.isArray(value)) return [];

  return value
    .filter((item) => item && typeof item === "object")
    .map((item, index) => ({
      id: safeText(item.id) || `activity-${Date.now()}-${index}`,
      leadId: safeText(item.leadId),
      userId: safeText(item.userId),
      userNameSnapshot: safeText(item.userNameSnapshot) || "Unknown User",
      actionType: safeText(item.actionType) || "note_added",
      callOutcome: safeText(item.callOutcome),
      notes: safeText(item.notes),
      createdAt: safeText(item.createdAt),
      followUpDate: safeText(item.followUpDate),
      leadAddress: safeText(item.leadAddress)
    }));
}

function sanitizeLeadLock(value = {}) {
  const lock = value && typeof value === "object" ? value : {};
  return {
    leadId: safeText(lock.leadId),
    lockedByUserId: safeText(lock.lockedByUserId),
    lockedByUserName: safeText(lock.lockedByUserName),
    lockedUntil: safeText(lock.lockedUntil),
    isActive: Boolean(lock.isActive)
  };
}

function sanitizeOnboardingStatuses(value) {
  if (!Array.isArray(value)) return [];

  return value
    .filter((item) => item && typeof item === "object")
    .map((item) => ({
      username: safeText(item.username),
      displayName: safeText(item.displayName || item.display_name),
      role: safeText(item.role),
      name: safeText(item.name),
      email: safeText(item.email),
      profileComplete: Boolean(item.profileComplete ?? item.profile_complete),
      agreementSigned: Boolean(item.agreementSigned ?? item.agreement_signed),
      signedAt: safeText(item.signedAt || item.signed_at),
      agreementVersion: safeText(item.agreementVersion || item.agreement_version),
      downloadUrl: safeText(item.downloadUrl || item.download_url)
    }))
    .filter((item) => item.username)
    .sort((a, b) => {
      if (a.role === "Admin" && b.role !== "Admin") return -1;
      if (a.role !== "Admin" && b.role === "Admin") return 1;
      return a.username.localeCompare(b.username);
    });
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

function sanitizeBuyers(value) {
  if (!Array.isArray(value)) return [];

  return value
    .filter((buyer) => buyer && typeof buyer === "object")
    .map((buyer, index) => normalizeBuyerPhones({
      ...emptyBuyer,
      ...buyer,
      id: safeText(buyer.id) || `buyer-${Date.now()}-${index}`,
      name: safeText(buyer.name) || safeText(buyer.company) || "Unknown Buyer",
      normalizedCompanyName: safeText(buyer.normalizedCompanyName),
      company: safeText(buyer.company),
      buyerType: safeText(buyer.buyerType) || "unknown",
      phone: safeText(buyer.phone),
      phones: Array.isArray(buyer.phones) ? buyer.phones.map(safeText).filter(Boolean) : [],
      email: safeText(buyer.email),
      website: safeText(buyer.website),
      linkedinUrl: safeText(buyer.linkedinUrl),
      facebookUrl: safeText(buyer.facebookUrl),
      contactFormUrl: safeText(buyer.contactFormUrl),
      socialLinks: Array.isArray(buyer.socialLinks) ? buyer.socialLinks.map(safeText).filter(Boolean) : [],
      counties: Array.isArray(buyer.counties) ? buyer.counties.map(safeText).filter(Boolean) : splitInputValues(buyer.counties),
      zipCodes: Array.isArray(buyer.zipCodes) ? buyer.zipCodes.map(safeText).filter(Boolean) : splitInputValues(buyer.zipCodes),
      priceMin: safeText(buyer.priceMin),
      priceMax: safeText(buyer.priceMax),
      propertyTypes: Array.isArray(buyer.propertyTypes) ? buyer.propertyTypes.map(safeText).filter(Boolean) : splitInputValues(buyer.propertyTypes),
      fundingType: safeText(buyer.fundingType),
      builderType: safeText(buyer.builderType),
      activityStatus: safeText(buyer.activityStatus) || "warm",
      relationshipTier: safeText(buyer.relationshipTier) || "C",
      mailingAddress: safeText(buyer.mailingAddress),
      registeredAgent: safeText(buyer.registeredAgent),
      pastDealsBought: safeText(buyer.pastDealsBought),
      propertyCount: Number(buyer.propertyCount) || 0,
      vacantLotCount: Number(buyer.vacantLotCount) || 0,
      averageLandValue: safeText(buyer.averageLandValue),
      averagePurchasePrice: safeText(buyer.averagePurchasePrice),
      lastPurchaseDate: safeText(buyer.lastPurchaseDate),
      estimatedBuyBox: safeText(buyer.estimatedBuyBox),
      confidenceScore: Number(buyer.confidenceScore) || 0,
      builderScore: Number(buyer.builderScore) || 0,
      assignmentFeeTolerance: safeText(buyer.assignmentFeeTolerance),
      notes: safeText(buyer.notes),
      source: safeText(buyer.source) || "Imported",
      sourceUrls: Array.isArray(buyer.sourceUrls) ? buyer.sourceUrls.map(safeText).filter(Boolean) : []
    }));
}

function createEmptyParcelRecord(lead = {}) {
  return {
    leadId: safeText(lead.id),
    address: safeText(lead.address),
    apn: safeText(lead.parcelNumber),
    county: safeText(lead.county),
    acreage: "",
    lotDimensions: safeText(lead.lotSize),
    legalDescription: "",
    zoning: "",
    landUse: "",
    floodZone: "",
    utilityAvailability: "",
    opportunityZone: "",
    taxBalance: "",
    taxDelinquencyStatus: "",
    assessedValue: safeText(lead.assessedValue),
    landValue: "",
    improvementValue: "",
    lastSaleDate: "",
    lastSalePrice: "",
    ownershipDuration: "",
    mortgageEstimate: "",
    estimatedEquity: "",
    ownershipHistory: "",
    mapLayers: [],
    researchStatus: "Needs Research",
    dataSource: "",
    notes: "",
    updatedAt: ""
  };
}

function sanitizeParcelRecord(value = {}) {
  const parcel = value && typeof value === "object" ? value : {};
  return {
    ...createEmptyParcelRecord({ id: parcel.leadId }),
    ...parcel,
    leadId: safeText(parcel.leadId),
    address: safeText(parcel.address),
    apn: safeText(parcel.apn),
    county: safeText(parcel.county),
    acreage: safeText(parcel.acreage),
    lotDimensions: safeText(parcel.lotDimensions),
    legalDescription: safeText(parcel.legalDescription),
    zoning: safeText(parcel.zoning),
    landUse: safeText(parcel.landUse),
    floodZone: safeText(parcel.floodZone),
    utilityAvailability: safeText(parcel.utilityAvailability),
    opportunityZone: safeText(parcel.opportunityZone),
    taxBalance: safeText(parcel.taxBalance),
    taxDelinquencyStatus: safeText(parcel.taxDelinquencyStatus),
    assessedValue: safeText(parcel.assessedValue),
    landValue: safeText(parcel.landValue),
    improvementValue: safeText(parcel.improvementValue),
    lastSaleDate: safeText(parcel.lastSaleDate),
    lastSalePrice: safeText(parcel.lastSalePrice),
    ownershipDuration: safeText(parcel.ownershipDuration),
    mortgageEstimate: safeText(parcel.mortgageEstimate),
    estimatedEquity: safeText(parcel.estimatedEquity),
    ownershipHistory: safeText(parcel.ownershipHistory),
    mapLayers: Array.isArray(parcel.mapLayers) ? parcel.mapLayers.map(safeText).filter(Boolean) : [],
    researchStatus: safeText(parcel.researchStatus) || "Needs Research",
    dataSource: safeText(parcel.dataSource),
    notes: safeText(parcel.notes),
    updatedAt: safeText(parcel.updatedAt)
  };
}

function mergeParcelWithLead(parcel, lead = {}) {
  const cleanParcel = sanitizeParcelRecord(parcel);
  return {
    ...cleanParcel,
    leadId: cleanParcel.leadId || safeText(lead.id),
    address: cleanParcel.address || safeText(lead.address),
    apn: cleanParcel.apn || safeText(lead.parcelNumber),
    county: cleanParcel.county || safeText(lead.county),
    lotDimensions: cleanParcel.lotDimensions || safeText(lead.lotSize),
    assessedValue: cleanParcel.assessedValue || safeText(lead.assessedValue)
  };
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

async function fetchCurrentUser(token) {
  const response = await fetch(`${apiBaseUrl}/auth/me`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("User fetch failed");
  }

  return response.json();
}

async function saveOnboardingProfile(profile, token) {
  const response = await fetch(`${apiBaseUrl}/auth/profile`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(profile)
  });

  if (!response.ok) {
    throw new Error("Profile save failed");
  }

  return response.json();
}

async function signOnboardingAgreement(payload, token) {
  const response = await fetch(`${apiBaseUrl}/auth/onboarding/sign`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Agreement signature failed");
  }

  return response.json();
}

async function downloadSignedOnboardingAgreement(token) {
  const response = await fetch(`${apiBaseUrl}/auth/onboarding/agreement`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Agreement download failed");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "chatcrm-signed-partner-agreement.pdf";
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 500);
}

async function fetchAdminOnboardingStatuses(token) {
  const response = await fetch(`${apiBaseUrl}/auth/admin/onboarding`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Team onboarding fetch failed");
  }

  return sanitizeOnboardingStatuses(await response.json());
}

async function downloadAdminSignedAgreement(username, token) {
  const response = await fetch(`${apiBaseUrl}/auth/admin/onboarding/${encodeURIComponent(username)}/agreement`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Admin agreement download failed");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `chatcrm-signed-agreement-${username}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 500);
}
async function fetchDailyQuote(token) {
  const response = await fetch(`${apiBaseUrl}/auth/quote/today`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Quote fetch failed");
  }

  return response.json();
}

async function fetchLeadActivity(leadId, token) {
  const response = await fetch(`${apiBaseUrl}/leads/${encodeURIComponent(leadId)}/activity`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Lead activity fetch failed");
  }

  return sanitizeLeadActivities(await response.json());
}

async function recordLeadActivity(leadId, activity, token) {
  const response = await fetch(`${apiBaseUrl}/leads/${encodeURIComponent(leadId)}/activity`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(activity)
  });

  if (!response.ok) {
    throw new Error("Lead activity save failed");
  }

  return sanitizeLeadActivities([await response.json()])[0];
}

async function lockLeadForUser(leadId, token) {
  const response = await fetch(`${apiBaseUrl}/leads/${encodeURIComponent(leadId)}/lock`, {
    method: "POST",
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Lead lock failed");
  }

  return sanitizeLeadLock(await response.json());
}

async function fetchRecentTeamActivity(token) {
  const response = await fetch(`${apiBaseUrl}/leads/activity/recent`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Recent activity fetch failed");
  }

  return sanitizeLeadActivities(await response.json());
}

async function fetchDailyCallCounts(token) {
  const response = await fetch(`${apiBaseUrl}/leads/activity/daily-counts`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Daily call counts fetch failed");
  }

  const result = await response.json();
  return Array.isArray(result)
    ? result.map((item) => ({
        userId: safeText(item.userId),
        userName: safeText(item.userName),
        count: Number(item.count) || 0
      }))
    : [];
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

async function fetchBackendBuyers(token) {
  const response = await fetch(`${apiBaseUrl}/buyers`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Buyer fetch failed");
  }

  return sanitizeBuyers(await response.json());
}

async function importBuyerCsv(file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/buyers/import-csv`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });

  if (!response.ok) {
    throw new Error("Buyer import failed");
  }

  const result = await response.json();
  return {
    buyers: sanitizeBuyers(result.buyers),
    warnings: Array.isArray(result.warnings) ? result.warnings : []
  };
}

async function previewDallasCadUpload(file, controls, token) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("enrichmentEnabled", controls.enrichmentEnabled ? "true" : "false");
  formData.append("maxRecords", String(controls.maxRecords || 500));
  formData.append("minBuilderScore", String(controls.minBuilderScore || 20));
  formData.append("rateLimitMs", String(controls.rateLimitMs || 750));

  const response = await fetch(`${apiBaseUrl}/buyers/import-dcad/preview`, {
    method: "POST",
    headers: authHeaders(token),
    body: formData
  });

  if (!response.ok) {
    throw new Error("Dallas CAD import failed");
  }

  const result = await response.json();
  return {
    ...result,
    buyers: sanitizeBuyers(result.buyers),
    warnings: Array.isArray(result.warnings) ? result.warnings : []
  };
}

async function refreshDallasCadEnrichment(jobId, selectedBuyerIds, controls, token) {
  const response = await fetch(`${apiBaseUrl}/buyers/import-dcad/enrich`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({
      jobId,
      selectedBuyerIds,
      enrichmentEnabled: Boolean(controls.enrichmentEnabled),
      minBuilderScore: Number(controls.minBuilderScore) || 20,
      rateLimitMs: Number(controls.rateLimitMs) || 750
    })
  });

  if (!response.ok) {
    throw new Error("Dallas CAD enrichment failed");
  }

  const result = await response.json();
  return {
    ...result,
    buyers: sanitizeBuyers(result.buyers),
    warnings: Array.isArray(result.warnings) ? result.warnings : []
  };
}

async function enrichPublicBuyerContacts(token, options = {}) {
  const response = await fetch(`${apiBaseUrl}/buyers/enrich-public`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({ maxBuyers: options.maxBuyers || 40, minBuilderScore: 0, rateLimitMs: 750 })
  });

  if (!response.ok) {
    throw new Error("Buyer public enrichment failed");
  }

  const result = await response.json();
  return {
    ...result,
    buyers: sanitizeBuyers(result.buyers),
    checkedCount: Number(result.checkedCount) || 0,
    updatedCount: Number(result.updatedCount) || 0,
    phonesFound: Number(result.phonesFound) || 0
  };
}
async function importDallasCadSelection(jobId, selectedBuyerIds, token) {
  const response = await fetch(`${apiBaseUrl}/buyers/import-dcad/import`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token)
    },
    body: JSON.stringify({ jobId, selectedBuyerIds })
  });

  if (!response.ok) {
    throw new Error("Dallas CAD import failed");
  }

  const result = await response.json();
  return {
    ...result,
    buyers: sanitizeBuyers(result.buyers),
    warnings: Array.isArray(result.warnings) ? result.warnings : []
  };
}

async function saveBuyerToBackend(buyer, token) {
  const method = buyer.id ? "PUT" : "POST";
  const url = buyer.id ? `${apiBaseUrl}/buyers/${encodeURIComponent(buyer.id)}` : `${apiBaseUrl}/buyers`;
  const response = await fetch(url, {
    method,
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(buyer)
  });

  if (!response.ok) {
    throw new Error("Buyer save failed");
  }

  return sanitizeBuyers([await response.json()])[0];
}

async function deleteBuyerFromBackend(id, token) {
  const response = await fetch(`${apiBaseUrl}/buyers/${encodeURIComponent(id)}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Buyer delete failed");
  }

  return response.json();
}

async function matchDealToBuyers(deal, token) {
  const response = await fetch(`${apiBaseUrl}/buyers/match`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(deal)
  });

  if (!response.ok) {
    throw new Error("Buyer match failed");
  }

  const matches = await response.json();
  return matches.map((match) => ({
    ...match,
    buyer: sanitizeBuyers([match.buyer])[0],
    score: clampScore(match.score),
    reasons: Array.isArray(match.reasons) ? match.reasons.map(safeText).filter(Boolean) : []
  }));
}

async function fetchParcelIntelligence(leadId, token) {
  const response = await fetch(`${apiBaseUrl}/parcels/${encodeURIComponent(leadId)}`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("Parcel fetch failed");
  }

  return sanitizeParcelRecord(await response.json());
}

async function fetchCountyDashboards(token) {
  const response = await fetch(`${apiBaseUrl}/counties/dashboard`, {
    headers: authHeaders(token)
  });

  if (!response.ok) {
    throw new Error("County dashboard fetch failed");
  }

  const result = await response.json();
  return Array.isArray(result) ? result : [];
}

async function saveParcelIntelligence(parcel, token) {
  const response = await fetch(`${apiBaseUrl}/parcels/${encodeURIComponent(parcel.leadId)}`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json"
    },
    body: JSON.stringify(parcel)
  });

  if (!response.ok) {
    throw new Error("Parcel save failed");
  }

  return sanitizeParcelRecord(await response.json());
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function normalizeCountyName(value = "") {
  return safeText(value).toLowerCase().replace("county", "").trim();
}

function groupCountyDashboards(dashboards = []) {
  return dashboards.reduce((groups, item) => {
    const market = item?.county?.market || "Other";
    return {
      ...groups,
      [market]: [...(groups[market] || []), item]
    };
  }, {});
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

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(value % 1 ? 1 : 0)}%`;
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
  const blockedNames = new Set([
    "apn owner",
    "balch springs",
    "cedar hill",
    "city state",
    "city state zip",
    "county record",
    "dallas",
    "duncanville",
    "garland",
    "grand prairie",
    "hutchins",
    "import review",
    "irving",
    "lancaster",
    "mesquite",
    "owner oc",
    "owner occupied",
    "property address",
    "review owner",
    "rowlett",
    "sachse",
    "seagoville",
    "tax list",
    "unit city",
    "zip county"
  ]);
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

function getActivityActionLabel(actionType = "") {
  const labels = {
    called: "called this lead",
    call_started: "started a call",
    note_added: "added a note",
    status_changed: "changed status",
    follow_up_set: "set a follow-up",
    hot_lead_marked: "marked Hot Lead",
    not_interested: "marked Not Interested",
    voicemail: "left voicemail",
    wrong_number: "marked Wrong Number"
  };
  return labels[actionType] || actionType.replace(/_/g, " ") || "updated this lead";
}

function getActivityTypeForStatus(status = "") {
  if (status === "left-voicemail") return "voicemail";
  if (status === "not-interested") return "not_interested";
  if (status === "follow-up") return "follow_up_set";
  if (status === "confirmed") return "called";
  if (status === "no-answer") return "called";
  return "status_changed";
}

function formatActivityTime(value = "") {
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return "Time missing";

  const date = new Date(timestamp);
  const now = new Date();
  const time = date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  if (date.toDateString() === now.toDateString()) return `Today at ${time}`;

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return `Yesterday at ${time}`;

  return `${date.toLocaleDateString()} at ${time}`;
}

function isRecentTimestamp(value = "", minutes = 10) {
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return false;
  return Date.now() - timestamp <= minutes * 60 * 1000;
}

function isRecentlyContactedByAnother(lead = {}, user = {}) {
  return Boolean(
    lead.lastContactedAt &&
    lead.lastContactedUserId &&
    lead.lastContactedUserId !== user?.username &&
    isRecentTimestamp(lead.lastContactedAt, 10)
  );
}

function isActiveLeadLock(lock) {
  const safeLock = lock && typeof lock === "object" ? lock : {};
  const timestamp = Date.parse(safeLock.lockedUntil || "");
  return Boolean(safeLock.isActive && Number.isFinite(timestamp) && timestamp > Date.now());
}

function applyActivityToLead(activity = {}) {
  return {
    lastContactedUserId: activity.userId || "",
    lastContactedBy: activity.userNameSnapshot || "",
    lastContactedAt: activity.createdAt || "",
    lastActivityAction: activity.actionType || ""
  };
}

function pickLatestLeadActivity(currentLead = {}, backendLead = {}) {
  const currentTime = Date.parse(currentLead.lastContactedAt || "");
  const backendTime = Date.parse(backendLead.lastContactedAt || "");
  if (Number.isFinite(backendTime) && (!Number.isFinite(currentTime) || backendTime >= currentTime)) {
    return backendLead;
  }
  return currentLead;
}

function mergeBackendLeads(currentLeads, backendLeads) {
  const byAddress = new globalThis.Map();

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
    const activityLead = pickLatestLeadActivity(currentLead, backendLead);
    byAddress.set(key, normalizeLeadPhones({
      ...currentLead,
      ...backendLead,
      phones,
      phone: phones[0] || backendLead.phone || currentLead.phone || "",
      notes: currentLead.notes || backendLead.notes || "",
      contactStatus: currentLead.contactStatus || backendLead.contactStatus,
      followUpDate: currentLead.followUpDate || backendLead.followUpDate || "",
      lastContactedUserId: activityLead.lastContactedUserId || "",
      lastContactedBy: activityLead.lastContactedBy || "",
      lastContactedAt: activityLead.lastContactedAt || "",
      lastActivityAction: activityLead.lastActivityAction || "",
      lockedByUserId: backendLead.lockedByUserId || currentLead.lockedByUserId || "",
      lockedByUserName: backendLead.lockedByUserName || currentLead.lockedByUserName || "",
      lockedUntil: backendLead.lockedUntil || currentLead.lockedUntil || ""
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

function getBuyerPhones(buyer = {}) {
  const values = [];
  if (Array.isArray(buyer.phones)) {
    values.push(...buyer.phones);
  }
  if (buyer.phone) {
    values.push(...String(buyer.phone).split(/[\n,;|]+/));
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

function normalizeBuyerPhones(buyer) {
  const phones = getBuyerPhones(buyer);
  return {
    ...buyer,
    phones,
    phone: phones[0] || buyer.phone || ""
  };
}

function formatBuyerPhoneList(buyer = {}) {
  return getBuyerPhones(buyer).map(formatPhone).join(", ");
}

function splitInputValues(value = "") {
  if (Array.isArray(value)) return value.map(safeText).filter(Boolean);

  return String(value || "")
    .split(/[,;|\n]+/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function createDealDraft(lead = {}) {
  const offer = calculateOffer(lead);
  return {
    id: safeText(lead.id),
    address: safeText(lead.address),
    county: safeText(lead.county) || inferCountyFromAddress(lead.address),
    zipCode: getLeadZip(lead),
    propertyType: safeText(lead.propertyType) || "Land",
    price: safeText(lead.contractPrice) || safeText(lead.maxOffer) || (offer.maxOffer ? Math.round(offer.maxOffer).toString() : ""),
    rehabLevel: safeText(lead.rehabLevel),
    stage: safeText(lead.stage)
  };
}

function inferCountyFromAddress(address = "") {
  const text = safeText(address).toLowerCase();
  if (text.includes("dallas")) return "Dallas";
  if (text.includes("tarrant")) return "Tarrant";
  if (text.includes("kaufman")) return "Kaufman";
  return "";
}

function mergeBuyerProfiles(currentBuyers, incomingBuyers) {
  const merged = new globalThis.Map();

  for (const buyer of sanitizeBuyers(currentBuyers)) {
    merged.set(getBuyerMergeKey(buyer), buyer);
  }

  for (const buyer of sanitizeBuyers(incomingBuyers)) {
    merged.set(getBuyerMergeKey(buyer), buyer);
  }

  return Array.from(merged.values());
}

function getBuyerMergeKey(buyer = {}) {
  return normalizeText(buyer.email || buyer.phone || buyer.company || buyer.name || buyer.id);
}


function isLikelyPublicBusinessBuyer(buyer = {}) {
  const text = [buyer.company, buyer.name, buyer.normalizedCompanyName, buyer.builderType, buyer.buyerType]
    .filter(Boolean)
    .join(" ");
  return /\b(llc|inc|corp|company|co\.?|builders?|homes?|construction|development|properties|investments|realty|land|capital|holdings|partners|ventures|group)\b/i.test(text);
}

function formatBuyBox(buyer = {}) {
  const priceRange = [buyer.priceMin, buyer.priceMax].filter(Boolean).join(" - ");
  const typeText = Array.isArray(buyer.propertyTypes) && buyer.propertyTypes.length ? buyer.propertyTypes.join(", ") : "Any type";
  return [priceRange || "Open price", typeText].join(" / ");
}

function BuyerScore({ score }) {
  return (
    <div className="buyer-score">
      <strong>{score}</strong>
      <span>Match</span>
    </div>
  );
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
    "Last Contacted By",
    "Last Contacted At",
    "Last Activity",
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
      lead.lastContactedBy,
      lead.lastContactedAt,
      lead.lastActivityAction,
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

function exportBuyersCsv(buyers) {
  const headers = [
    "Name",
    "Normalized Company",
    "Company",
    "Buyer Type",
    "Builder Score",
    "Confidence Score",
    "Phone Numbers",
    "Email",
    "Website",
    "LinkedIn",
    "Facebook",
    "Contact Form",
    "Social Links",
    "Counties",
    "ZIP Codes",
    "Property Count",
    "Vacant Lot Count",
    "Average Land Value",
    "Average Purchase Price",
    "Last Purchase Date",
    "Estimated Buy Box",
    "Price Min",
    "Price Max",
    "Property Types",
    "Funding Type",
    "Builder Type",
    "Activity Status",
    "Relationship Tier",
    "Mailing Address",
    "Registered Agent",
    "Past Deals Bought",
    "Assignment Fee Tolerance",
    "Notes",
    "Source",
    "Source URLs"
  ];
  const rows = sanitizeBuyers(buyers).map((buyer) => [
    buyer.name,
    buyer.normalizedCompanyName,
    buyer.company,
    buyer.buyerType,
    buyer.builderScore,
    buyer.confidenceScore,
    formatBuyerPhoneList(buyer),
    buyer.email,
    buyer.website,
    buyer.linkedinUrl,
    buyer.facebookUrl,
    buyer.contactFormUrl,
    buyer.socialLinks.join(", "),
    buyer.counties.join(", "),
    buyer.zipCodes.join(", "),
    buyer.propertyCount,
    buyer.vacantLotCount,
    buyer.averageLandValue,
    buyer.averagePurchasePrice,
    buyer.lastPurchaseDate,
    buyer.estimatedBuyBox,
    buyer.priceMin,
    buyer.priceMax,
    buyer.propertyTypes.join(", "),
    buyer.fundingType,
    buyer.builderType,
    buyer.activityStatus,
    buyer.relationshipTier,
    buyer.mailingAddress,
    buyer.registeredAgent,
    buyer.pastDealsBought,
    buyer.assignmentFeeTolerance,
    buyer.notes,
    buyer.source,
    buyer.sourceUrls.join(", ")
  ]);
  const csv = [headers, ...rows].map((row) => row.map(escapeCsvValue).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = `chatcrm-buyers-${new Date().toISOString().slice(0, 10)}.csv`;
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

function buildBuyerContactSearchUrl(buyer = {}) {
  const company = buyer.company || buyer.name || "";
  const county = (buyer.counties || ["Dallas"])[0] || "Dallas";
  const query = [company, county, "phone contact website"].filter(Boolean).join(" ");
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
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

function buildCallerLeaderboard(leads = []) {
  const map = new globalThis.Map();

  for (const lead of leads) {
    const name = safeText(lead.lastContactedBy || lead.owner);
    if (!name || name === "Import Review" || name === "Unassigned") continue;

    const current = map.get(name) || { name, calls: 0, hotLeads: 0, followUps: 0 };
    if (lead.lastContactedAt || lead.lastActivityAction) current.calls += 1;
    if (getLeadContactStatus(lead).value === "confirmed" || Number(lead.score) >= 80) current.hotLeads += 1;
    if (safeText(lead.stage) === "Follow Up" || lead.followUpDate) current.followUps += 1;
    map.set(name, current);
  }

  return Array.from(map.values()).sort((a, b) => (b.calls + b.hotLeads * 3 + b.followUps) - (a.calls + a.hotLeads * 3 + a.followUps));
}

function calculateCallerCommission(assignmentFee, closedDeals = 0) {
  const fee = numberFromMoney(assignmentFee);
  const dealCount = numberFromMoney(closedDeals);
  const tier = commissionTiers.find((item) => fee >= item.min && fee <= item.max) || commissionTiers[0];
  const bonusRate = dealCount >= 25 ? 0.05 : dealCount >= 10 ? 0.025 : 0;
  const totalRate = tier.rate + bonusRate;
  return {
    baseRate: tier.rate,
    bonusRate,
    payout: Math.round(fee * totalRate),
    tierLabel: tier.label,
    totalRate
  };
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
    followUpDate: "",
    lastContactedUserId: "",
    lastContactedBy: "",
    lastContactedAt: "",
    lastActivityAction: "",
    lockedByUserId: "",
    lockedByUserName: "",
    lockedUntil: ""
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
    followUpDate: "",
    lastContactedUserId: "",
    lastContactedBy: "",
    lastContactedAt: "",
    lastActivityAction: "",
    lockedByUserId: "",
    lockedByUserName: "",
    lockedUntil: ""
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
