import { normalizeCallablePhone } from "./contactCalling.js";

export const dialerQueueFilters = new Set(["My Queue", "Available Leads", "Follow Up", "Due Today", "Overdue"]);

export function normalizeDialerQueue(filter = "") {
  return dialerQueueFilters.has(filter) ? filter : "My Queue";
}

export function leadHasStoredPhone(lead = {}) {
  const phones = [...(Array.isArray(lead.phones) ? lead.phones : []), lead.phone || ""];
  return phones.some((phone) => normalizeCallablePhone(phone));
}

export function getPowerDialerQueue(leads = [], filter = "My Queue", currentUser = {}, today = new Date().toISOString().slice(0, 10)) {
  const queue = normalizeDialerQueue(filter);
  const userId = String(currentUser?.username || "");
  return leads.filter((lead) => {
    if (String(lead.contactStatus || "").toLowerCase() === "interested") return false;
    if (queue === "Available Leads") return !lead.assignedToUserId;
    if (lead.assignedToUserId !== userId) return false;
    if (queue === "Follow Up") return lead.stage === "Follow Up" || lead.contactStatus === "follow-up" || Boolean(lead.followUpDate);
    if (queue === "Due Today") return lead.followUpDate === today;
    if (queue === "Overdue") return Boolean(lead.followUpDate && lead.followUpDate < today);
    return true;
  });
}

export function getNextPowerDialerLead(leads, currentLeadId, filter, currentUser, today) {
  const queue = getPowerDialerQueue(leads, filter, currentUser, today);
  if (!queue.length) return null;
  const index = queue.findIndex((lead) => lead.id === currentLeadId);
  const ordered = index >= 0 ? [...queue.slice(index + 1), ...queue.slice(0, index)] : queue;
  return ordered.find(leadHasStoredPhone) || null;
}

export function isSavedCallAttempt(activity = {}) {
  return new Set([
    "call_result",
    "called",
    "voicemail",
    "not_interested",
    "wrong_number",
    "disconnected",
    "interested_marked"
  ]).has(activity.actionType);
}


export async function saveBeforeAdvance(saveResult, advance) {
  const saved = await saveResult();
  await advance(saved);
  return saved;
}
