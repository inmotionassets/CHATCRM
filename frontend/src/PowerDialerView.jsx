import React from "react";
import GoogleVoiceActions from "./GoogleVoiceActions.jsx";
import { canCallContact, getCallingContacts, getContactCallStatus, noAnswerTextTemplate, normalizeCallablePhone } from "./contactCalling.js";
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
  campaignCompletedCount = 0,
  campaignSummary = null,
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
  const [contactsLoaded, setContactsLoaded] = React.useState(false);
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
    setContactsLoaded(false);
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
        if (!nextSnapshot || nextSnapshot.leadId !== lead.id) throw new Error("Contact snapshot identity did not match the open lead.");
        setSnapshot(nextSnapshot);
        setContactsLoaded(true);
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
  const usableContacts = contactsLoaded ? calling.contacts.filter(canCallContact) : [];
  const activeContact = contactsLoaded
    ? usableContacts.find((contact) => normalizeCallablePhone(contact.normalizedValue || contact.value) === activePhone)
      || calling.best
      || usableContacts[0]
      || null
    : null;
  const activeNumber = normalizeCallablePhone(activeContact?.normalizedValue || activeContact?.value);
  const activeIndex = usableContacts.findIndex((contact) => normalizeCallablePhone(contact.normalizedValue || contact.value) === activeNumber);
  const nextContact = activeIndex >= 0 ? usableContacts[activeIndex + 1] : usableContacts[1];
  const callIsForActiveNumber = Boolean(attemptedPhone && attemptedPhone === activeNumber && attemptedContactId && attemptedContactId === activeContact?.id);
  const attemptCount = activities.filter(isSavedCallAttempt).length;
  const lastContact = activities.find(isSavedCallAttempt);
  const ownerName = lead.name || lead.ownerName || "Owner name needed";
  const needsFollowUp = outcome === "follow-up";
  const canSave = Boolean(outcome)
    && (!needsFollowUp || Boolean(followUpDate && notes.trim()))
    && callIsForActiveNumber
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

  if (!contactsLoaded || !activeContact || !activeNumber) {
    const statusCounts = { eligible: 0, unreviewed: 0, disconnected: 0, suppressed: 0 };
    if (contactsLoaded) {
      for (const contact of calling.contacts) {
        if (contact.contactType === "phone") statusCounts[getContactCallStatus(contact)] += 1;
      }
    }
    return (
      <section className="power-dialer-shell">
        <header className="power-dialer-header">
          <div><p className="eyebrow">Power Dialer / {queueLabel}</p><h2>{lead.address || "Missing address"}</h2></div>
          <button className="secondary-button" onClick={onClose}>Exit Calling Mode</button>
        </header>
        <div className="power-dialer-empty">
          <h3>{contactsLoaded ? "Contact Review" : "Phone status could not be verified"}</h3>
          <p>{contactsLoaded
            ? "No eligible number is available. Review, disconnected, and DNC numbers are shown below and cannot be called."
            : "Saved contact and compliance status did not load. Calling is paused for this lead; retry the campaign after reconnecting."}</p>
          {contactsLoaded ? <div className="power-contact-status-summary">
            <span>Eligible: {statusCounts.eligible}</span><span>Review: {statusCounts.unreviewed}</span>
            <span>Disconnected: {statusCounts.disconnected}</span><span>Suppressed / DNC: {statusCounts.suppressed}</span>
          </div> : null}
          {contactsLoaded ? <div className="power-contact-list">
            {calling.contacts.filter((contact) => contact.contactType === "phone").map((contact, index) => {
              const status = getContactCallStatus(contact);
              const label = status === "suppressed" ? "Suppressed / DNC" : status === "disconnected" ? "Disconnected" : status === "unreviewed" ? "Needs review" : "Eligible";
              return <button disabled type="button" key={contact.id || contact.value || index}>
                <strong>{label}</strong><span>{displayPhone(contact)}</span><small>{contact.source || contact.status || "Saved phone"}</small>
              </button>;
            })}
          </div> : null}
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
        <span><b>Contact Status</b>{activeContact.verifiedOwner ? "Verified · Call Ready" : "Saved number · Call Ready"}<br /><small>{activeContact.sourceConfidence == null ? "Source score not provided" : `${activeContact.sourceConfidence}% source confidence`}</small></span>
        <span><b>Attempts</b>{attemptCount}</span>
        <span><b>Last Contact</b>{lastContact ? `${lastContact.callOutcome} / ${formatTime(lastContact.createdAt)}` : "None"}</span>
        <span><b>Follow-Up</b>{lead.followUpDate || "None"}</span>
      </div>

      {campaignSummary ? <div className="power-dialer-campaign-summary" role="status">
        <strong>Campaign: {campaignSummary.leadCounts?.eligible || 0} eligible leads / {campaignSummary.numberCounts?.eligible || 0} eligible numbers</strong>
        <span>{campaignCompletedCount} completed · {campaignSummary.leadCounts?.unreviewed || 0} review · {campaignSummary.leadCounts?.disconnected || 0} disconnected · {campaignSummary.leadCounts?.suppressed || 0} suppressed/DNC · {campaignSummary.leadCounts?.no_numbers || 0} no numbers</span>
      </div> : null}
      {message ? <p className="queue-message" role="status">{message}</p> : null}

      <div className="power-dialer-grid">
        <main className="power-dialer-call-card">
          <div className="power-dialer-next-call">
            <span>Next eligible call</span><strong>{displayPhone(activeContact)}</strong>
            <small>{ownerName} · {lead.address || "Property address missing"}</small>
          </div>
          <div className="power-dialer-primary-action">
            <GoogleVoiceActions
              callLabel="Open Google Voice"
              contact={activeContact}
              leadContext={{ ownerName, address: lead.address || "Missing address" }}
              onCall={(phone) => {
                setAttemptedPhone(phone);
                setAttemptedContactId(activeContact.id || "");
                setOutcome("");
                setFeedbackReceipt("");
                onVoiceAction("voice_opened", phone);
              }}
              onText={(phone) => onVoiceAction("voice_text_opened", phone)}
              primary
            />
          </div>

          <div className="power-contact-list" aria-label="Phone numbers and call status">
            {calling.contacts.filter((contact) => contact.contactType === "phone").map((contact, index) => {
              const phone = normalizeCallablePhone(contact.normalizedValue || contact.value);
              const status = getContactCallStatus(contact);
              const eligible = status === "eligible";
              const label = status === "suppressed" ? "Suppressed / DNC" : status === "disconnected" ? "Disconnected" : status === "unreviewed" ? "Needs review" : index === 0 ? "Eligible · Best" : "Eligible";
              return (
                <button
                  className={phone === activeNumber ? "active" : ""}
                  disabled={!eligible}
                  key={contact.id || phone || `${status}-${index}`}
                  onClick={() => {
                    setActivePhone(phone);
                    setOutcome("");
                    setAttemptedPhone("");
                    setAttemptedContactId("");
                    setFeedbackReceipt("");
                  }}
                  type="button"
                >
                  <strong>{label}</strong>
                  <span>{displayPhone(contact)}</span>
                  <small>{contact.source || contact.status || "Saved contact"}</small>
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
              <button className={outcome === value ? "active" : ""} disabled={!callIsForActiveNumber} key={value} onClick={() => {
                setOutcome(value);
                setFeedbackReceipt("");
              }} type="button">{label}</button>
            ))}
          </div>
          {!callIsForActiveNumber ? <small className="power-call-guidance">Open Google Voice for {displayPhone(activeContact)} first. Results will be saved to that exact number.</small> : <small className="power-call-guidance">Result applies to {displayPhone(activeContact)}.</small>}

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
