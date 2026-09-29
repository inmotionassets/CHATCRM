import React from "react";
import { buildGoogleVoiceUrl, buildGoogleVoiceTextUrl, normalizeCallablePhone, canCallContact, canTextContact, openGoogleVoiceWindow } from "./contactCalling.js";

export default function GoogleVoiceActions({ callLabel = "Call", contact, leadContext, onCall, onText, primary = false }) {
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
  function openVoice(event, url, action) {
    if (!url) return;
    if (openGoogleVoiceWindow(url)) {
      event.preventDefault();
      action?.(number);
      return;
    }
    action?.(number);
  }
  return <span className="google-voice-actions">
    {leadContext?.ownerName && leadContext?.address ? (
      <span className="google-voice-context">
        <b>{leadContext.ownerName}</b>
        <small>{leadContext.address}</small>
      </span>
    ) : null}
    {canCallContact(contact) ? <a className={primary ? "primary-command" : undefined} href={buildGoogleVoiceUrl(number)} target="legacy-google-voice" rel="noopener" onClick={(event) => openVoice(event, buildGoogleVoiceUrl(number), onCall)}>{callLabel}</a> : <span className="disabled" aria-disabled="true">{callLabel}</span>}
    {canTextContact(contact) ? <a href={buildGoogleVoiceTextUrl(number)} target="legacy-google-voice" title="Open Google Voice Messages and copy this number" onClick={(event) => { copyNumber(true); openVoice(event, buildGoogleVoiceTextUrl(number), onText); }}>Text</a> : <span className="disabled" aria-disabled="true">Text</span>}
    {number ? <button type="button" onClick={() => copyNumber()}>Copy</button> : null}
    {notice ? <small role="status">{notice}</small> : null}
  </span>;
}
