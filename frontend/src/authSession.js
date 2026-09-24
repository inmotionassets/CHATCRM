export function isAuthTokenExpired(token = "", nowSeconds = Math.floor(Date.now() / 1000)) {
  try {
    const payloadPart = String(token).split(".", 1)[0];
    if (!payloadPart) return true;
    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const payload = JSON.parse(atob(padded));
    const expiresAt = Number(payload.exp);
    return !Number.isFinite(expiresAt) || expiresAt <= nowSeconds;
  } catch {
    return true;
  }
}
