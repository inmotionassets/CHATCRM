import test from "node:test";
import assert from "node:assert/strict";
import { isAuthTokenExpired } from "./authSession.js";

function tokenWithExpiration(exp) {
  const payload = Buffer.from(JSON.stringify({ sub: "test-user", exp })).toString("base64url");
  return `${payload}.signature`;
}

test("accepts a session that has not expired", () => {
  assert.equal(isAuthTokenExpired(tokenWithExpiration(2_000), 1_000), false);
});

test("rejects an expired session before protected API calls begin", () => {
  assert.equal(isAuthTokenExpired(tokenWithExpiration(1_000), 1_000), true);
  assert.equal(isAuthTokenExpired(tokenWithExpiration(999), 1_000), true);
});

test("rejects malformed or expiration-free session tokens", () => {
  assert.equal(isAuthTokenExpired("not-a-token", 1_000), true);
  const noExpiration = `${Buffer.from(JSON.stringify({ sub: "test-user" })).toString("base64url")}.signature`;
  assert.equal(isAuthTokenExpired(noExpiration, 1_000), true);
});
