import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeCallablePhone, buildGoogleVoiceUrl, buildGoogleVoiceTextUrl, getCallingContacts, getLeadDisplayContact, canCallContact, canTextContact, getContactCallStatus, noAnswerTextTemplate, openGoogleVoiceWindow } from './contactCalling.js';
const lead = { id: 'dallas-test', phones: ['4696288298', '2145551234', '9725554567', '4695557890', '2145559999'], phone: '+1 469 628 8298' };
test('normalizes supported US formats and rejects broken actions', () => {
  for (const value of ['4696288298', '(469) 628-8298', '469-628-8298', '+1 469 628 8298']) assert.equal(normalizeCallablePhone(value), '+14696288298');
  for (const value of ['', '123', '0000000000', '4696288298 ext 12', 'call 4696288298', '+444696288298']) {
    assert.equal(buildGoogleVoiceUrl(value), ''); assert.equal(buildGoogleVoiceTextUrl(value), '');
  }
});
test('all five imports survive missing or stale intelligence without mutating the lead', () => {
  const before = JSON.stringify(lead);
  const snapshot = {leadId: lead.id, contacts: [{id:'saved', contactType:'phone',value:'4696288298',isCallable:true, verifiedOwner:true, sourceQualityReviewed:true, status:'confirmed_owner'}]};
  assert.equal(getCallingContacts(lead, snapshot).contacts.length, 5);
  const missingIntelligence = getCallingContacts(lead);
  assert.equal(missingIntelligence.contacts.length, 5);
  assert.ok(missingIntelligence.best);
  assert.ok(missingIntelligence.contacts.every((contact) => canCallContact(contact) && !canTextContact(contact)));
  assert.equal(JSON.stringify(lead), before);
});
test('ranked best is first, additional calls use their own numbers, saved-only records survive', () => {
  const best = {id:'best',contactType:'phone',value:'9725554567',isCallable:true,verifiedOwner:true,sourceQualityReviewed:true,status:'confirmed_owner'};
  const result = getCallingContacts(lead, {leadId:lead.id,bestContact:best,contacts:[best,{contactType:'phone',value:'2145550109'}]});
  assert.equal(result.contacts.length,6);
  assert.equal(result.best.id,'best');
  assert.equal(buildGoogleVoiceUrl(result.contacts[0].value),'https://voice.google.com/u/0/calls?a=nc,%2B19725554567');
  assert.equal(canCallContact(result.contacts[1]),true);
});
test('blocked contacts stay visible with no call/text action and no text when opted out', () => {
  for (const flag of ['doNotCall','wrongNumber','disconnected']) {
    const contact={contactType:'phone',value:lead.phones[0],[flag]:true};
    const result=getCallingContacts(lead,{leadId:lead.id,contacts:[contact],bestContact:contact});
    assert.equal(result.contacts.length,5);
    assert.notEqual(normalizeCallablePhone(result.best?.value), normalizeCallablePhone(contact.value));
    assert.equal(canCallContact(contact),false); assert.equal(canTextContact(contact),false);
  }
  assert.equal(canTextContact({value:lead.phones[0],doNotText:true}),false);
});
test('saved unreviewed PropStream phones remain visible and callable without a verification click', () => {
  const snapshot = {
    leadId: lead.id,
    contacts: [
      { id: 'candidate', contactType: 'phone', value: '2145550101', status: 'needs_review', isCallable: false },
      { id: 'restricted', contactType: 'phone', value: '2145550102', status: 'public_dnc', doNotCall: true },
    ],
  };
  const display = getLeadDisplayContact({ id: lead.id }, snapshot);
  assert.equal(display.contact.value, '2145550101');
  assert.equal(display.isCallReady, true);
  assert.equal(canCallContact(display.contact), true);
  assert.equal(getContactCallStatus(snapshot.contacts[1]), 'suppressed');
});

test('opt-outs, litigation, suppression, disconnected and wrong numbers stay blocked', () => {
  for (const contact of [
    { value: '2145550199', optedOut: true },
    { value: '2145550199', optOut: true },
    { value: '2145550199', doNotContact: true },
    { value: '2145550199', litigationHold: true },
    { value: '2145550199', status: 'public_dnc' },
    { value: '2145550199', status: 'wrong_number' },
    { value: '2145550199', status: 'disconnected' },
  ]) assert.equal(canCallContact(contact), false);
});
test('missing phone and another lead snapshot never create calling actions', () => {
  for (const name of ['Agustin Jaramillo','Gilberto Lopez']) {
    const result=getCallingContacts({id:name, name}, {leadId:lead.id,contacts:[{contactType:'phone',value:lead.phones[0]}]});
    assert.equal(result.best,null); assert.equal(result.contacts.length,0);
  }
});

test('Google Voice launcher reuses one named window without controlling its contents', () => {
  const calls = [];
  const fakeWindow = { focus() {}, opener: {} };
  assert.equal(openGoogleVoiceWindow('https://voice.google.com/u/0/calls?a=nc,%2B14696288298', (url, name) => {
    calls.push({ url, name });
    return fakeWindow;
  }), true);
  assert.equal(calls[0].name, 'legacy-google-voice');
  assert.equal(fakeWindow.opener, null);
  assert.equal(openGoogleVoiceWindow('', () => fakeWindow), false);
});

test('manual no-answer text remains a reusable template', () => {
  assert.match(noAnswerTextTemplate, /LEGACY Land Acquisitions/);
  assert.match(noAnswerTextTemplate, /text or call me back/);
});

test('valid saved numbers need no owner review while explicit restrictions remain blocked', () => {
  const number = { contactType: 'phone', value: '2145550199', normalizedValue: '2145550199', isCallable: true, verifiedOwner: true, sourceQualityReviewed: true, status: 'confirmed_owner' };
  assert.equal(getContactCallStatus(number), 'eligible');
  assert.equal(canCallContact(number), true);
  const unreviewed = { ...number, status: 'needs_review', isCallable: false };
  assert.equal(getContactCallStatus(unreviewed), 'eligible');
  assert.equal(canCallContact(unreviewed), true);
  assert.equal(getContactCallStatus({ ...number, verifiedOwner: false, sourceQualityReviewed: false, status: 'imported', isCallable: false }), 'eligible');
  assert.equal(getContactCallStatus({ ...number, doNotCall: true }), 'suppressed');
  assert.equal(getContactCallStatus({ ...number, disconnected: true }), 'disconnected');
  assert.equal(getContactCallStatus({ ...number, status: 'litigation_hold', isCallable: false }), 'suppressed');
});

test('lead-level DNC and disconnected dispositions suppress all dialer numbers', () => {
  const snapshot = { leadId: 'blocked', contacts: [{ id: 'n1', contactType: 'phone', value: '2145550199', isCallable: true, verifiedOwner: true, sourceQualityReviewed: true, status: 'confirmed_owner' }] };
  const dnc = getCallingContacts({ id: 'blocked', phone: '2145550199', contactStatus: 'do-not-call' }, snapshot);
  assert.equal(dnc.best, null);
  assert.equal(getContactCallStatus(dnc.contacts[0]), 'suppressed');
  const disconnected = getCallingContacts({ id: 'blocked', phone: '2145550199', contactStatus: 'disconnected' }, snapshot);
  assert.equal(disconnected.best, null);
  assert.equal(getContactCallStatus(disconnected.contacts[0]), 'disconnected');
  const litigation = getCallingContacts({ id: 'held', phone: '2145550199', litigationHold: true }, snapshot);
  assert.equal(litigation.best, null);
  assert.equal(getContactCallStatus(litigation.contacts[0]), 'suppressed');
});
