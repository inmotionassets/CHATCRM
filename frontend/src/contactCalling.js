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
export function canCallContact(contact) {
  return Boolean(contact && normalizeCallablePhone(contact.normalizedValue || contact.value)
    && !contact.doNotCall && !contact.wrongNumber && !contact.disconnected
    && !["do_not_call", "wrong_number", "disconnected"].includes(contact.status)
    && contact.isCallable !== false);
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
      status: normalized ? "imported" : "needs_review", isCallable: Boolean(normalized),
      isTextable: Boolean(normalized),
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
  const contacts = [...records.values()];
  const preferred = normalizeCallablePhone(current?.bestContact?.normalizedValue || current?.bestContact?.value);
  const best = contacts.find((contact) => preferred && normalizeCallablePhone(contact.normalizedValue || contact.value) === preferred && canCallContact(contact))
    || contacts.filter(canCallContact).sort((a, b) => (a.priorityRank ?? 999) - (b.priorityRank ?? 999))[0]
    || null;
  return { best, contacts: best ? [best, ...contacts.filter((contact) => contact !== best)] : contacts };
}
