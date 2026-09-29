import test from "node:test";
import assert from "node:assert/strict";
import { getPowerDialerQueue, getNextPowerDialerLead, isSavedCallAttempt, normalizeDialerQueue, saveBeforeAdvance } from "./powerDialer.js";

const user = { username: "caller-a" };
const leads = [
  { id: "mine-1", assignedToUserId: "caller-a", phones: ["2145551212"], contactStatus: "needs-review" },
  { id: "mine-no-phone", assignedToUserId: "caller-a", phones: [], contactStatus: "contact-review" },
  { id: "other", assignedToUserId: "caller-b", phones: ["4695551212"], contactStatus: "needs-review" },
  { id: "available", assignedToUserId: "", phones: ["9725551212"], contactStatus: "needs-review" },
  { id: "due", assignedToUserId: "caller-a", phones: ["2145552323"], followUpDate: "2026-09-29", contactStatus: "follow-up" },
  { id: "overdue", assignedToUserId: "caller-a", phones: ["2145553434"], followUpDate: "2026-09-28", contactStatus: "follow-up" },
  { id: "interested", assignedToUserId: "caller-a", phones: ["2145554545"], contactStatus: "interested" }
];

test("active queues enforce caller ownership and exclude interested review leads", () => {
  assert.deepEqual(getPowerDialerQueue(leads, "My Queue", user).map((lead) => lead.id), ["mine-1", "mine-no-phone", "due", "overdue"]);
  assert.deepEqual(getPowerDialerQueue(leads, "Available Leads", user).map((lead) => lead.id), ["available"]);
  assert.deepEqual(getPowerDialerQueue(leads, "Follow Up", user, "2026-09-29").map((lead) => lead.id), ["due", "overdue"]);
  assert.deepEqual(getPowerDialerQueue(leads, "Due Today", user, "2026-09-29").map((lead) => lead.id), ["due"]);
  assert.deepEqual(getPowerDialerQueue(leads, "Overdue", user, "2026-09-29").map((lead) => lead.id), ["overdue"]);
});

test("next lead respects queue order and skips no-phone records", () => {
  assert.equal(getNextPowerDialerLead(leads, "mine-1", "My Queue", user, "2026-09-29").id, "due");
  assert.equal(getNextPowerDialerLead(leads, "", "Available Leads", user, "2026-09-29").id, "available");
});

test("unsupported queues safely start from My Queue", () => {
  assert.equal(normalizeDialerQueue("Interested"), "My Queue");
});

test("only an explicitly saved result is a call attempt", () => {
  assert.equal(isSavedCallAttempt({ actionType: "voice_opened" }), false);
  assert.equal(isSavedCallAttempt({ actionType: "call_started" }), false);
  assert.equal(isSavedCallAttempt({ actionType: "call_result" }), true);
  assert.equal(isSavedCallAttempt({ actionType: "voicemail" }), true);
});


test("Save & Next advances only after a confirmed save", async () => {
  const order = [];
  const saved = await saveBeforeAdvance(
    async () => { order.push("save"); return { id: "mine-1" }; },
    async (lead) => { order.push(`advance:${lead.id}`); }
  );
  assert.equal(saved.id, "mine-1");
  assert.deepEqual(order, ["save", "advance:mine-1"]);
});

test("save failure never advances", async () => {
  let advanced = false;
  await assert.rejects(
    saveBeforeAdvance(
      async () => { throw new Error("backend down"); },
      async () => { advanced = true; }
    ),
    /backend down/
  );
  assert.equal(advanced, false);
});
