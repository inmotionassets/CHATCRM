import React from "react";
import { buildGoogleVoiceUrl, buildGoogleVoiceTextUrl, normalizeCallablePhone, canCallContact, canTextContact } from "./contactCalling.js";

export default function GoogleVoiceActions({ contact, onCall, primary = false }) {
  const [notice, setNotice] = React.useState("");
  const number = normalizeCallablePhone(contact?.normalizedValue || contact?.value);
  React.useEffect(() => setNotice(""), [number]);
  async function copyNumber(forText = false) {
    try {
      await navigator.clipboard.writeText(number);
      setNotice(forText ? `${number} copied. In Google Voice, choose Send a message and paste the number.` : `${number} copied.`);
    } catch {
      setNotice(`Copy unavailable. Paste ${number} into Google Voice manually.`);
    }
  }
  return <span className="google-voice-actions">
    {canCallContact(contact) ? <a className={primary ? "primary-command" : undefined} href={buildGoogleVoiceUrl(number)} target="_blank" rel="noreferrer" onClick={() => onCall?.(number)}>Call</a> : <span className="disabled" aria-disabled="true">Call</span>}
    {canTextContact(contact) ? <a href={buildGoogleVoiceTextUrl(number)} target="_blank" rel="noreferrer" title="Open Google Voice Messages and copy this number" onClick={() => copyNumber(true)}>Text</a> : <span className="disabled" aria-disabled="true">Text</span>}
    {number ? <button type="button" onClick={() => copyNumber()}>Copy</button> : null}
    {notice ? <small role="status">{notice}</small> : null}
  </span>;
}
