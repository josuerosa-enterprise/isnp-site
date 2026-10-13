'use strict';
// Browser-independent behavior tests; native layout and dialog focus trapping need browser QA.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
class Element {
  constructor() {
    this.listeners = {}; this.attrs = {}; this.children = []; this.classes = new Set();
    this.hidden = false; this.value = ''; this.textContent = '';
    this.classList = {add: n => this.classes.add(n), remove: n => this.classes.delete(n), contains: n => this.classes.has(n), toggle: (n, on) => on ? this.classes.add(n) : this.classes.delete(n)};
  }
  addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  async fire(type, event = {}) { for (const callback of this.listeners[type] || []) await callback(event); }
  getAttribute(name) { return this.attrs[name]; }
  setAttribute(name, value) { this.attrs[name] = value; }
  querySelectorAll() { return this.children; }
  contains(el) { return this.children.includes(el); }
  focus() { this.focused = true; }
  select() { this.selected = true; }
  showModal() { this.open = true; }
  close() { this.open = false; return this.fire('close'); }
}
function boot({mobile = true, home = true, clipboardFails = false, observer = true} = {}) {
  const ids = ['.menu-toggle','#navigation','#proposal-dialog','#privacy-dialog','#privacy-open','#proposal-form','#proposal-result','#proposal-output','#proposal-status','#whatsapp-proposal','#email-proposal','#edit-proposal','#copy-proposal','#download-proposal','.contact-dock'];
  if (home) ids.push('#conectar');
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  const menu = elements['.menu-toggle']; menu.setAttribute('aria-expanded','false');
  const nav = elements['#navigation'], navLink = new Element(), navProposal = new Element(), heroProposal = new Element();
  nav.children = [navLink, navProposal];
  const dialog = elements['#proposal-dialog'], privacy = elements['#privacy-dialog'];
  dialog.children = [new Element()]; privacy.children = [new Element()];
  const form = elements['#proposal-form']; form.valid = true; form.reportValidity = () => form.valid;
  form.fields = {organization:'  Hospital São José  ',city:'Marabá / PA',contact:'Ana — direção',kind:'Gestão de equipes e escalas médicas',idea:'Equipes de pediatria & plantão\nAlinhamento inicial.'};
  form.elements = {organization: new Element()};
  elements['#proposal-result'].hidden = true;
  const document = new Element(); document.body = new Element(); document.documentElement = new Element();
  document.querySelector = selector => elements[selector] || null;
  document.querySelectorAll = selector => selector === '[data-open-proposal]' ? [navProposal, heroProposal] : selector === 'dialog' ? [dialog, privacy] : [];
  const media = new Element(); const observed = [], copied = [];
  const window = {matchMedia: query => query.includes('min-width') ? media : {matches:mobile}};
  function IntersectionObserver(callback) { this.observe = element => observed.push({element,callback}); }
  if (observer) window.IntersectionObserver = IntersectionObserver;
  const context = vm.createContext({document, window, IntersectionObserver, FormData: class {constructor(f){this.form=f} get(key){return this.form.fields[key]}}, navigator:{clipboard:{async writeText(value){if(clipboardFails)throw Error('Unavailable');copied.push(value)}}}, URL, Blob, setTimeout});
  vm.runInContext(source, context);
  return {elements, document, nav, navLink, navProposal, heroProposal, dialog, privacy, menu, media, form, observed, copied};
}
test('shared script runs on home and news; observer remains optional', () => {
  assert.doesNotThrow(() => boot());
  assert.doesNotThrow(() => boot({home:false}));
  assert.doesNotThrow(() => boot({observer:false}));
});
test('mobile menu closes on navigation, Escape and desktop transition', async () => {
  const ui = boot();
  await ui.menu.fire('click'); assert.equal(ui.menu.getAttribute('aria-expanded'),'true');
  await ui.navLink.fire('click'); assert.equal(ui.nav.classes.has('is-open'),false);
  await ui.menu.fire('click'); await ui.document.fire('keydown',{key:'Escape'});
  assert.equal(ui.menu.focused,true); assert.equal(ui.menu.getAttribute('aria-expanded'),'false');
  await ui.menu.fire('click'); await ui.media.fire('change',{matches:true});
  assert.equal(ui.nav.classes.has('is-open'),false);
});
test('closing a proposal opened from mobile navigation returns focus to a visible menu button', async () => {
  const ui = boot();
  await ui.menu.fire('click'); await ui.navProposal.fire('click');
  assert.equal(ui.dialog.open,true); assert.equal(ui.nav.classes.has('is-open'),false);
  assert.equal(ui.document.body.classes.has('modal-open'),true);
  await ui.dialog.close();
  assert.equal(ui.menu.focused,true); assert.equal(ui.document.body.classes.has('modal-open'),false);
  const desktop = boot({mobile:false}); await desktop.navProposal.fire('click'); await desktop.dialog.close();
  assert.equal(desktop.navProposal.focused,true);
});
test('proposal review preserves fields, accents and line breaks in both channels; edit and invalid inputs are safe', async () => {
  const ui = boot(), e = ui.elements;
  ui.form.valid = false; await ui.form.fire('submit',{preventDefault(){}});
  assert.equal(e['#proposal-result'].hidden,true); assert.equal(e['#whatsapp-proposal'].href,undefined);
  ui.form.valid = true; await ui.form.fire('submit',{preventDefault(){}});
  const wa = new URL(e['#whatsapp-proposal'].href), text = wa.searchParams.get('text');
  assert.equal(wa.origin+wa.pathname,'https://wa.me/5594981081535');
  assert.match(text,/Hospital \/ instituição: Hospital São José\nCidade \/ UF: Marabá \/ PA/);
  assert.match(text,/Equipes de pediatria & plantão\nAlinhamento inicial\./);
  const email = new URL(e['#email-proposal'].href);
  assert.equal(email.pathname,'institutodesaudedonortedopara@gmail.com');
  assert.equal(email.searchParams.get('body'),text); assert.equal(e['#proposal-output'].value,text);
  assert.equal(ui.form.hidden,true); assert.equal(e['#proposal-result'].hidden,false);
  await e['#edit-proposal'].fire('click');
  assert.equal(ui.form.hidden,false); assert.equal(e['#proposal-result'].hidden,true);
  assert.equal(ui.form.elements.organization.focused,true);
});
test('clipboard failure offers manual copy without losing the proposal', async () => {
  for (const clipboardFails of [false,true]) {
    const ui = boot({clipboardFails}), e = ui.elements;
    await ui.form.fire('submit',{preventDefault(){}}); await e['#copy-proposal'].fire('click');
    if(clipboardFails) {assert.equal(e['#proposal-output'].selected,true);assert.match(e['#proposal-status'].textContent,/copie/)}
    else assert.equal(ui.copied[0],e['#proposal-output'].value);
  }
});
test('contact dock is hidden only while the contact section is visible', () => {
  const ui = boot();
  assert.equal(ui.observed[0].element,ui.elements['#conectar']);
  ui.observed[0].callback([{isIntersecting:true}]); assert.equal(ui.elements['.contact-dock'].classes.has('is-hidden'),true);
  ui.observed[0].callback([{isIntersecting:false}]); assert.equal(ui.elements['.contact-dock'].classes.has('is-hidden'),false);
  assert.equal(boot({home:false}).observed.length,0);
});
