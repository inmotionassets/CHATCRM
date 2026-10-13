// Calling/display normalization only. Never rewrite imported lead values.
export function normalizeCallablePhone(value = "") {
  const raw = String(value).trim();
  if (!raw || !/^[+\d\s().-]+$/.test(raw)) return "";
  let digits = raw.replace(/\D/g, "");
  if (digits.length === 11 && digits.startsWith("1")) digits = digits.slice(1);
  return /^[2-9]\d{2}[2-9]\d{6}$/.test(digits) ? `+1${digits}` : "";
}
export function buildGoogleVoiceUrl(phone) {
  const normalized = normalizeCallablePhone(phone);
  return normalized ? `https://voice.google.com/u/0/calls?a=nc,${encodeURIComponent(normalized)}` : "";
}
export function buildGoogleVoiceTextUrl(phone) {
  // Google documents Messages navigation, not a stable recipient-compose URL.
  return normalizeCallablePhone(phone) ? "https://voice.google.com/u/0/messages" : "";
}
export function getContactCallStatus(contact) {
  const status = String(contact?.status || "").trim().toLowerCase().replace(/[ -]+/g, "_");
  if (contact?.doNotCall || contact?.wrongNumber || contact?.suppressed || contact?.isSuppressed
    || contact?.optedOut || contact?.optOut || contact?.doNotContact || contact?.litigationHold
    || ["dnc", "do_not_call", "public_dnc", "suppressed", "wrong_number", "opted_out", "opt_out", "do_not_contact", "litigation_hold"].includes(status)) return "suppressed";
  if (contact?.disconnected || status === "disconnected") return "disconnected";
  // An unreviewed owner/source association is visible and dialable just like the
  // original saved-phone workflow. Only explicit restrictions or a bad number block calling.
  if (!normalizeCallablePhone(contact?.normalizedValue || contact?.value || contact?.displayValue)) return "unreviewed";
  return "eligible";
}
export function canCallContact(contact) {
  return getContactCallStatus(contact) === "eligible";
}
export function canTextContact(contact) {
  return canCallContact(contact) && !contact.doNotText && contact.status !== "do_not_text"
    && contact.isTextable !== false;
}
export function getCallingContacts(lead = {}, snapshot = null) {
  const records = new Map();
  const values = [...(Array.isArray(lead.phones) ? lead.phones : []), lead.phone || ""];
  for (const raw of values.flatMap((value) => String(value).split(/[\n,;|]+/))) {
    const value = raw.trim();
    if (!value) continue;
    const normalized = normalizeCallablePhone(value);
    const key = normalized || value;
    if (!records.has(key)) records.set(key, {
      value, normalizedValue: normalized, contactType: "phone", source: "Imported lead data",
      // A syntactically valid phone is not an ownership/compliance review.
      status: "needs_review", isCallable: false, isTextable: false,
    });
  }
  const current = snapshot?.leadId === lead.id ? snapshot : null;
  for (const contact of [...(current?.contacts || []), ...(current?.bestContact ? [current.bestContact] : [])]) {
    if (contact.contactType !== "phone") continue;
    const value = contact.normalizedValue || contact.value || contact.displayValue;
    if (!value) continue;
    const key = normalizeCallablePhone(value) || String(value).trim();
    records.set(key, { ...records.get(key), ...contact });
  }
  let contacts = [...records.values()];
  const leadStatus = String(lead.contactStatus || "").trim().toLowerCase().replace(/[_ ]+/g, "-");
  if (lead.litigationHold === true) {
    contacts = contacts.map((contact) => ({ ...contact, isCallable: false, isTextable: false, status: "litigation_hold" }));
  } else if (["dnc", "do-not-call", "not-interested", "wrong-number", "suppressed", "opt-out", "opted-out", "do-not-contact"].includes(leadStatus)) {
    contacts = contacts.map((contact) => ({ ...contact, doNotCall: true, isCallable: false, status: "suppressed" }));
  } else if (leadStatus === "disconnected") {
    contacts = contacts.map((contact) => ({ ...contact, disconnected: true, isCallable: false, status: "disconnected" }));
  }
  const preferred = normalizeCallablePhone(current?.bestContact?.normalizedValue || current?.bestContact?.value);
  const best = contacts.find((contact) => preferred && normalizeCallablePhone(contact.normalizedValue || contact.value) === preferred && canCallContact(contact))
    || contacts.filter(canCallContact).sort((a, b) => (a.priorityRank ?? 999) - (b.priorityRank ?? 999))[0]
    || null;
  return { best, contacts: best ? [best, ...contacts.filter((contact) => contact !== best)] : contacts };
}

export function getLeadDisplayContact(lead = {}, snapshot = null) {
  const calling = getCallingContacts(lead, snapshot);
  return {
    contact: calling.best || calling.contacts[0] || null,
    isCallReady: Boolean(calling.best),
  };
}


export const noAnswerTextTemplate = "Hey, this is Virgo with LEGACY Land Acquisitions. I just tried reaching you about a property I believe you own. We’re looking to purchase in the area and wanted to see if you’d be open to an offer. If so, feel free to text or call me back when you get a chance. Thanks!";

export function openGoogleVoiceWindow(url, openWindow = globalThis.window?.open?.bind(globalThis.window)) {
  if (!url || typeof openWindow !== "function") return false;
  const opened = openWindow(url, "legacy-google-voice");
  if (!opened) return false;
  try {
    opened.opener = null;
    opened.focus?.();
  } catch {
    // Cross-origin access is intentionally not attempted.
  }
  return true;
}
