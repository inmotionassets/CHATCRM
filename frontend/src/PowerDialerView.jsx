import React from "react";
import GoogleVoiceActions from "./GoogleVoiceActions.jsx";
import { getCallingContacts, noAnswerTextTemplate, normalizeCallablePhone } from "./contactCalling.js";
import { isSavedCallAttempt, saveBeforeAdvance } from "./powerDialer.js";

const outcomes = [
  ["did-not-answer", "No Answer"],
  ["left-voicemail", "Left Voicemail"],
  ["confirmed-owner", "Confirmed Owner"],
  ["wrong-number", "Wrong Number"],
  ["disconnected", "Disconnected"],
  ["do-not-call", "DNC"],
  ["not-interested", "Not Interested"],
  ["follow-up", "Follow Up"],
  ["interested", "Interested"]
];

const feedbackByOutcome = {
  "wrong-number": "wrong_number",
  disconnected: "disconnected",
  "do-not-call": "do_not_call"
};

function displayPhone(contact = {}) {
  const normalized = normalizeCallablePhone(contact.normalizedValue || contact.value);
  if (!normalized) return contact.displayValue || contact.value || "Missing";
  const digits = normalized.replace(/\D/g, "").slice(-10);
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
}

function formatTime(value = "") {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "None" : date.toLocaleString();
}

export default function PowerDialerView({
  currentUser,
  lead,
  loadActivities,
  loadContacts,
  onAdvance,
  onClose,
  onContactFeedback,
  onLeadSaved,
  onSaveResult,
  onVoiceAction,
  queueLabel
}) {
  const [snapshot, setSnapshot] = React.useState(null);
  const [activities, setActivities] = React.useState([]);
  const [activePhone, setActivePhone] = React.useState("");
  const [outcome, setOutcome] = React.useState("");
  const [attemptedPhone, setAttemptedPhone] = React.useState("");
  const [attemptedContactId, setAttemptedContactId] = React.useState("");
  const [feedbackReceipt, setFeedbackReceipt] = React.useState("");
  const [notes, setNotes] = React.useState(lead.notes || "");
  const [followUpDate, setFollowUpDate] = React.useState(lead.followUpDate || "");
  const [message, setMessage] = React.useState("Loading calling context...");
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    setSnapshot(null);
    setActivities([]);
    setOutcome("");
    setAttemptedPhone("");
    setAttemptedContactId("");
    setFeedbackReceipt("");
    setNotes(lead.notes || "");
    setFollowUpDate(lead.followUpDate || "");
    setMessage("Loading calling context...");
    Promise.all([loadContacts(lead.id), loadActivities(lead.id)])
      .then(([nextSnapshot, nextActivities]) => {
        if (cancelled) return;
        setSnapshot(nextSnapshot);
        setActivities(nextActivities);
        setMessage("");
      })
      .catch(() => {
        if (!cancelled) setMessage("Calling context could not fully load. The current lead stays open.");
      });
    return () => {
      cancelled = true;
    };
  }, [lead.id]);

  const calling = getCallingContacts(lead, snapshot);
  const usableContacts = calling.contacts.filter((contact) => {
    const normalized = normalizeCallablePhone(contact.normalizedValue || contact.value);
    return normalized && contact.isCallable !== false && !contact.doNotCall && !contact.wrongNumber && !contact.disconnected
      && !["do_not_call", "wrong_number", "disconnected"].includes(contact.status);
  });
  const activeContact = usableContacts.find((contact) => normalizeCallablePhone(contact.normalizedValue || contact.value) === activePhone)
    || calling.best
    || usableContacts[0]
    || null;
  const activeNumber = normalizeCallablePhone(activeContact?.normalizedValue || activeContact?.value);
  const activeIndex = usableContacts.findIndex((contact) => normalizeCallablePhone(contact.normalizedValue || contact.value) === activeNumber);
  const nextContact = activeIndex >= 0 ? usableContacts[activeIndex + 1] : usableContacts[1];
  const attemptCount = activities.filter(isSavedCallAttempt).length;
  const lastContact = activities.find(isSavedCallAttempt);
  const ownerName = lead.name || lead.ownerName || "Owner name needed";
  const needsFollowUp = outcome === "follow-up";
  const canSave = Boolean(outcome)
    && (!needsFollowUp || Boolean(followUpDate && notes.trim()))
    && Boolean(attemptedPhone)
    && !saving;

  async function copyTemplate() {
    try {
      await navigator.clipboard.writeText(noAnswerTextTemplate);
      setMessage("No-answer text copied. Google Voice will not send it automatically.");
    } catch {
      setMessage("Copy was blocked. Select the template text and copy it manually.");
    }
  }

  async function saveCurrent({ advance, tryNextNumber = false }) {
    if (!canSave) {
      setMessage(needsFollowUp ? "Follow Up requires a date and notes." : "Choose a result before saving.");
      return;
    }
    setSaving(true);
    setMessage("Saving call result...");
    try {
      const feedback = feedbackByOutcome[outcome];
      const receiptKey = `${outcome}:${attemptedContactId}:${attemptedPhone}`;
      if (feedback && feedbackReceipt !== receiptKey) {
        if (!attemptedContactId) throw new Error("This contact is missing its saved Contact Intelligence identity.");
        const updatedSnapshot = await onContactFeedback(attemptedContactId, feedback);
        setSnapshot(updatedSnapshot);
        setFeedbackReceipt(receiptKey);
      }
      const saveResult = () => onSaveResult(lead.id, {
        contactStatus: outcome,
        notes,
        followUpDate: needsFollowUp ? followUpDate : "",
        phoneNumber: attemptedPhone
      });
      if (advance) {
        await saveBeforeAdvance(saveResult, async (saved) => {
          onLeadSaved(saved);
          await onAdvance(saved);
        });
        return;
      }
      const saved = await saveResult();
      onLeadSaved(saved);
      const nextActivities = await loadActivities(lead.id);
      setActivities(nextActivities);
      if (tryNextNumber && nextContact) {
        setActivePhone(normalizeCallablePhone(nextContact.normalizedValue || nextContact.value));
        setOutcome("");
        setAttemptedPhone("");
        setAttemptedContactId("");
        setFeedbackReceipt("");
        setMessage("Attempt saved. Next usable number is ready; you still choose whether to call it.");
        return;
      }
      setOutcome("");
      setAttemptedPhone("");
      setAttemptedContactId("");
      setFeedbackReceipt("");
      setMessage("Result saved.");
    } catch (error) {
      setMessage(error?.message || "Save failed. Notes are still here; retry before moving on.");
    } finally {
      setSaving(false);
    }
  }

  if (!activeContact || !activeNumber) {
    return (
      <section className="power-dialer-shell">
        <header className="power-dialer-header">
          <div><p className="eyebrow">Power Dialer / {queueLabel}</p><h2>{lead.address || "Missing address"}</h2></div>
          <button className="secondary-button" onClick={onClose}>Exit Calling Mode</button>
        </header>
        <div className="power-dialer-empty">
          <h3>Contact Review</h3>
          <p>No usable phone number is available. DNC, wrong, and disconnected contacts stay suppressed.</p>
          <button className="primary-button" onClick={() => onAdvance(lead)}>Skip to Next Eligible Lead</button>
        </div>
      </section>
    );
  }

  return (
    <section className="power-dialer-shell" aria-label="Power Dialer">
      <header className="power-dialer-header">
        <div>
          <p className="eyebrow">Power Dialer / {queueLabel}</p>
          <h2>{ownerName}</h2>
          <p>{lead.address || "Property address missing"}{lead.parcelNumber ? ` / APN ${lead.parcelNumber}` : ""}</p>
        </div>
        <button className="secondary-button" onClick={onClose}>Exit Calling Mode</button>
      </header>

      <div className="power-dialer-context">
        <span><b>Assigned Caller</b>{lead.assignedToName || currentUser?.name || currentUser?.username}</span>
        <span><b>Best Contact</b>{displayPhone(activeContact)}</span>
        <span><b>Contact Status</b>{activeContact.status || "Stored"} / {activeContact.matchConfidence || activeContact.sourceConfidence || 0}%</span>
        <span><b>Attempts</b>{attemptCount}</span>
        <span><b>Last Contact</b>{lastContact ? `${lastContact.callOutcome} / ${formatTime(lastContact.createdAt)}` : "None"}</span>
        <span><b>Follow-Up</b>{lead.followUpDate || "None"}</span>
      </div>

      {message ? <p className="queue-message" role="status">{message}</p> : null}

      <div className="power-dialer-grid">
        <main className="power-dialer-call-card">
          <div className="power-dialer-primary-action">
            <GoogleVoiceActions
              callLabel="Open Google Voice"
              contact={activeContact}
              leadContext={{ ownerName, address: lead.address || "Missing address" }}
              onCall={(phone) => onVoiceAction("voice_opened", phone)}
              onText={(phone) => onVoiceAction("voice_text_opened", phone)}
              primary
            />
          </div>

          <div className="power-contact-list">
            {usableContacts.map((contact, index) => {
              const phone = normalizeCallablePhone(contact.normalizedValue || contact.value);
              return (
                <button
                  className={phone === activeNumber ? "active" : ""}
                  key={contact.id || phone}
                  onClick={() => {
                    setActivePhone(phone);
                    setOutcome("");
                    setAttemptedPhone("");
                    setAttemptedContactId("");
                    setFeedbackReceipt("");
                  }}
                  type="button"
                >
                  <strong>{index === 0 ? "Best Contact" : `Additional ${index}`}</strong>
                  <span>{displayPhone(contact)}</span>
                  <small>{contact.status || contact.source || "Stored contact"}</small>
                </button>
              );
            })}
          </div>

          <section className="power-call-script">
            <p className="eyebrow">Call Script</p>
            <p>Hi, is this {ownerName}? This is Virgo with LEGACY Land Acquisitions. I’m calling about {lead.address || "a property in the area"}. Would you be open to discussing an offer?</p>
          </section>

          <section className="power-text-template">
            <div><p className="eyebrow">No-Answer Text</p><button onClick={copyTemplate} type="button">Copy Message</button></div>
            <p>{noAnswerTextTemplate}</p>
            <small>LEGACY only copies the message and opens Google Voice Messages. The caller sends it.</small>
          </section>
        </main>

        <aside className="power-dialer-result-card">
          <div><p className="eyebrow">Call Result</p><h3>What happened?</h3></div>
          <div className="power-result-buttons">
            {outcomes.map(([value, label]) => (
              <button className={outcome === value ? "active" : ""} key={value} onClick={() => {
                setOutcome(value);
                setAttemptedPhone(activeNumber);
                setAttemptedContactId(activeContact?.id || "");
                setFeedbackReceipt("");
              }} type="button">{label}</button>
            ))}
          </div>

          <label className="power-notes">
            <span>Call Notes{needsFollowUp ? " (required)" : ""}</span>
            <textarea onChange={(event) => setNotes(event.target.value)} rows="7" value={notes} />
          </label>

          {needsFollowUp ? (
            <label className="power-follow-up">
              <span>Follow-Up Date</span>
              <input min={new Date().toISOString().slice(0, 10)} onChange={(event) => setFollowUpDate(event.target.value)} type="date" value={followUpDate} />
            </label>
          ) : null}

          {outcome === "did-not-answer" && nextContact ? (
            <button className="secondary-button" disabled={!canSave} onClick={() => saveCurrent({ advance: false, tryNextNumber: true })} type="button">
              Try Next Number
            </button>
          ) : null}
          <button className="primary-button power-save-next" disabled={!canSave} onClick={() => saveCurrent({ advance: true })} type="button">
            {saving ? "Saving..." : "Save & Next"}
          </button>
          <small>LEGACY advances only after the backend confirms the result and any contact feedback.</small>
        </aside>
      </div>
    </section>
  );
}
