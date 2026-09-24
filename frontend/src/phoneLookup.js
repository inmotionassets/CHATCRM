export function normalizePhoneDigits(value = "") {
  const raw = String(value).trim();
  let digits = raw.replace(/\D/g, "");
  if (digits.startsWith("1") && (digits.length === 11 || /^\+?1[\s().-]/.test(raw))) {
    digits = digits.slice(1);
  }
  return digits;
}

export function isPhoneSearchQuery(value = "") {
  const raw = String(value).trim();
  const digits = normalizePhoneDigits(raw);
  return /^[+\d\s().-]+$/.test(raw) && digits.length >= 3 && digits.length <= 11;
}

export function getLeadPhoneValues(lead = {}) {
  const values = [...(Array.isArray(lead.phones) ? lead.phones : []), lead.phone || ""];
  const seen = new Set();
  const phones = [];

  for (const raw of values.flatMap((value) => String(value).split(/[\n,;|]+/))) {
    const phone = raw.trim();
    const digits = normalizePhoneDigits(phone);
    if (!phone || !digits || seen.has(digits)) continue;
    seen.add(digits);
    phones.push(phone);
  }

  return phones;
}

export function findPhoneLeadMatches(leads = [], query = "") {
  const digits = normalizePhoneDigits(query);
  if (!isPhoneSearchQuery(query)) return [];

  return leads.flatMap((lead) => {
    const phones = getLeadPhoneValues(lead);
    const matchedPhones = phones.filter((phone) => normalizePhoneDigits(phone).includes(digits));
    return matchedPhones.length ? [{ lead, matchedPhones, phones }] : [];
  });
}

export function getLatestLeadNote(notes = "") {
  return String(notes)
    .split(/\r?\n/)
    .map((note) => note.trim())
    .filter(Boolean)
    .at(-1) || "";
}
