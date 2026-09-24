import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeCallablePhone, buildGoogleVoiceUrl, buildGoogleVoiceTextUrl, getCallingContacts, canCallContact, canTextContact } from './contactCalling.js';
const lead = { id: 'dallas-test', phones: ['4696288298', '2145551234', '9725554567', '4695557890', '2145559999'], phone: '+1 469 628 8298' };
test('normalizes supported US formats and rejects broken actions', () => {
  for (const value of ['4696288298', '(469) 628-8298', '469-628-8298', '+1 469 628 8298']) assert.equal(normalizeCallablePhone(value), '+14696288298');
  for (const value of ['', '123', '0000000000', '4696288298 ext 12', 'call 4696288298', '+444696288298']) {
    assert.equal(buildGoogleVoiceUrl(value), ''); assert.equal(buildGoogleVoiceTextUrl(value), '');
  }
});
test('all five imports survive missing or stale intelligence without mutating the lead', () => {
  const before = JSON.stringify(lead);
  const snapshot = {leadId: lead.id, contacts: [{id:'saved', contactType:'phone',value:'4696288298',isCallable:true, status:'imported'}]};
  assert.equal(getCallingContacts(lead, snapshot).contacts.length, 5);
  assert.equal(getCallingContacts(lead).contacts.length, 5);
  assert.equal(JSON.stringify(lead), before);
});
test('ranked best is first, additional calls use their own numbers, saved-only records survive', () => {
  const best = {id:'best',contactType:'phone',value:'9725554567',isCallable:true,verifiedOwner:true};
  const result = getCallingContacts(lead, {leadId:lead.id,bestContact:best,contacts:[best,{contactType:'phone',value:'2145550109'}]});
  assert.equal(result.contacts.length,6);
  assert.equal(result.best.id,'best');
  assert.equal(buildGoogleVoiceUrl(result.contacts[0].value),'https://voice.google.com/u/0/calls?a=nc,%2B19725554567');
  assert.equal(buildGoogleVoiceUrl(result.contacts[1].value),'https://voice.google.com/u/0/calls?a=nc,%2B14696288298');
});
test('blocked contacts stay visible with no call/text action and no text when opted out', () => {
  for (const flag of ['doNotCall','wrongNumber','disconnected']) {
    const contact={contactType:'phone',value:lead.phones[0],[flag]:true};
    const result=getCallingContacts(lead,{leadId:lead.id,contacts:[contact],bestContact:contact});
    assert.equal(result.contacts.length,5);
    assert.notEqual(result.best.value,contact.value);
    assert.equal(canCallContact(contact),false); assert.equal(canTextContact(contact),false);
  }
  assert.equal(canTextContact({value:lead.phones[0],doNotText:true}),false);
});
test('missing phone and another lead snapshot never create calling actions', () => {
  for (const name of ['Agustin Jaramillo','Gilberto Lopez']) {
    const result=getCallingContacts({id:name, name}, {leadId:lead.id,contacts:[{contactType:'phone',value:lead.phones[0]}]});
    assert.equal(result.best,null); assert.equal(result.contacts.length,0);
  }
});
