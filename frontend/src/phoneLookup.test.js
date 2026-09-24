import test from "node:test";
import assert from "node:assert/strict";
import { findPhoneLeadMatches, getLatestLeadNote, isPhoneSearchQuery, normalizePhoneDigits } from "./phoneLookup.js";

const leads = [
  {
    id: "lead-one",
    name: "Cosme Gallegos",
    address: "10618 Bruton Rd",
    phone: "(214) 555-1212",
    phones: ["(214) 555-1212", "972-555-0100"]
  },
  {
    id: "lead-two",
    name: "Second Owner",
    address: "200 Main St",
    phones: ["+1 214-555-1212"]
  },
  {
    id: "lead-three",
    name: "Different Owner",
    address: "300 Main St",
    phones: ["469-555-9898"]
  }
];

test("normalizes common US phone formats to the same searchable digits", () => {
  for (const value of ["(214) 555-1212", "214-555-1212", "+1 2145551212", "2145551212"]) {
    assert.equal(normalizePhoneDigits(value), "2145551212");
  }
});

test("only plausible partial or full phone input opens reverse lookup", () => {
  assert.equal(isPhoneSearchQuery("214"), true);
  assert.equal(isPhoneSearchQuery("+1 (214) 555-1212"), true);
  assert.equal(isPhoneSearchQuery("10618 Bruton Rd"), false);
  assert.equal(isPhoneSearchQuery("00-0062-809-000-0000"), false);
});

test("full and partial phone searches return every associated lead", () => {
  assert.deepEqual(findPhoneLeadMatches(leads, "2145551212").map((match) => match.lead.id), ["lead-one", "lead-two"]);
  assert.deepEqual(findPhoneLeadMatches(leads, "1212").map((match) => match.lead.id), ["lead-one", "lead-two"]);
});

test("phone lookup keeps all stored numbers attached to each matching lead", () => {
  const [match] = findPhoneLeadMatches(leads, "(214) 555");
  assert.deepEqual(match.matchedPhones, ["(214) 555-1212"]);
  assert.deepEqual(match.phones, ["(214) 555-1212", "972-555-0100"]);
});

test("latest note returns the newest non-empty note line", () => {
  assert.equal(getLatestLeadNote("Initial import\n\nSeller called back"), "Seller called back");
});
