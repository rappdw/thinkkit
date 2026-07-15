/* Headless two-window integration test.
   Runs the REAL src/state.js + src/runtime.js in two vm sandboxes (presenter,
   audience) with a minimal DOM shim, wired together exactly like
   window.open/postMessage would wire them. Proves: boot, hello handshake,
   authoritative state push, step/slide advance & reverse, audience-side intents,
   blank + appendix toggles, hook API (onEnter/onStep/onExit), hash deep-links. */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const stateSrc = readFileSync(join(here, '../src/state.js'), 'utf8');
const runtimeSrc = readFileSync(join(here, '../src/runtime.js'), 'utf8');
// Pinned test manifest (placeholder slides) — decoupled from the live deck manifest.
const manifest = {
  title: 'test', channel: 'test-deck',
  order: ['p1', 'p2'],
  slides: {
    p1: { title: 'Placeholder A — declarative steps', steps: 3, budget: 1 },
    p2: { title: 'Placeholder B — hook API demo', steps: 2, budget: 1 },
  },
  appendix: null,
};

/* ── tiny DOM shim ── */
function makeEl(tag, attrs = {}) {
  const classes = new Set((attrs.class || '').split(/\s+/).filter(Boolean));
  return {
    tag, attrs: { ...attrs }, children: [], parent: null,
    textContent: '', innerHTML: '',
    _clickHandlers: [],
    getAttribute(n) { return n in this.attrs ? String(this.attrs[n]) : null; },
    classList: {
      toggle: (n, force) => {
        const has = classes.has(n);
        const want = force === undefined ? !has : !!force;
        want ? classes.add(n) : classes.delete(n);
        return want;
      },
      add: n => classes.add(n), remove: n => classes.delete(n),
      contains: n => classes.has(n),
    },
    hasClass(n) { return classes.has(n); },
    add(child) { child.parent = this; this.children.push(child); return child; },
    descendants() {
      const out = [];
      const walk = e => e.children.forEach(c => { out.push(c); walk(c); });
      walk(this); return out;
    },
    querySelectorAll(sel) {
      if (sel === '[data-step]') return this.descendants().filter(e => e.getAttribute('data-step') !== null);
      throw new Error('el.querySelectorAll unsupported: ' + sel);
    },
    addEventListener(type, fn) { if (type === 'click') this._clickHandlers.push(fn); },
    click() { this._clickHandlers.forEach(f => f()); },
  };
}

function makeWindow(role, dom) {
  const listeners = {};
  const win = {
    DECK_MANIFEST: manifest, DECK_ROLE: role,
    SlideHooks: undefined, opener: null, closed: false,
    addEventListener(type, fn) { (listeners[type] = listeners[type] || []).push(fn); },
    _fire(type, ev) { (listeners[type] || []).forEach(f => f(ev)); },
    postMessage(data) { win._fire('message', { data }); },
    open: null, // presenter shim installs this
  };
  win.self = win;
  const doc = {
    _ids: dom.ids, _all: dom.all,
    addEventListener(type, fn) { (listeners['doc:' + type] = listeners['doc:' + type] || []).push(fn); },
    _fireKey(key) {
      (listeners['doc:keydown'] || []).forEach(f =>
        f({ key, preventDefault() {}, metaKey: false, ctrlKey: false, altKey: false }));
    },
    getElementById(id) { return dom.ids[id] || null; },
    querySelectorAll(sel) {
      if (sel === '.slide') return dom.all.filter(e => e.hasClass('slide'));
      if (sel === '.note-card') return dom.all.filter(e => e.hasClass('note-card'));
      throw new Error('doc.querySelectorAll unsupported: ' + sel);
    },
    querySelector(sel) {
      if (sel === '.note-card.active') return dom.all.find(e => e.hasClass('note-card') && e.hasClass('active')) || null;
      throw new Error('doc.querySelector unsupported: ' + sel);
    },
  };
  const location = { hash: dom.hash || '' };
  const history = { replaceState(_a, _b, h) { location.hash = h.startsWith('#') ? h : '#' + h.split('#')[1]; } };
  const ctx = {
    window: win, document: doc, location, history, console,
    setTimeout: fn => { fn(); return 0; }, clearTimeout() {},
    setInterval: () => 0, clearInterval() {},
    Date, self: win, module: undefined,
    localStorage: { _s: {}, setItem(k, v) { this._s[k] = v; }, getItem(k) { return this._s[k] ?? null; }, removeItem(k) { delete this._s[k]; } },
  };
  vm.createContext(ctx);
  vm.runInContext(stateSrc, ctx);       // attaches DeckState to self (= win)
  win.DeckState = ctx.window.DeckState || ctx.self.DeckState;
  vm.runInContext(runtimeSrc, ctx);
  return { win, doc, location, boot: () => win._fire('DOMContentLoaded', {}) };
}

/* ── audience DOM matching the built structure ── */
function audienceDom() {
  const all = []; const ids = {};
  const track = e => { all.push(e); return e; };
  const s1 = track(makeEl('section', { class: 'slide', 'data-slide': 'p1', 'data-steps': '3' }));
  for (let i = 1; i <= 3; i++) track(s1.add(makeEl('p', { 'data-step': String(i) })));
  const s2 = track(makeEl('section', { class: 'slide', 'data-slide': 'p2', 'data-steps': '2' }));
  track(s2.add(makeEl('p', { 'data-step': '1' })));
  ids['p2-hook-msg'] = track(s2.add(makeEl('p', { id: 'p2-hook-msg' })));
  ids['slide-num'] = track(makeEl('span'));
  ids['blank-overlay'] = track(makeEl('div'));
  ids['apx-overlay'] = track(makeEl('div'));
  return { all, ids, s1, s2 };
}
function presenterDom() {
  const all = []; const ids = {};
  const track = e => { all.push(e); return e; };
  const n1 = track(makeEl('article', { class: 'note-card', 'data-slide': 'p1' }));
  for (let i = 1; i <= 3; i++) track(n1.add(makeEl('span', { 'data-step': String(i) })));
  const n2 = track(makeEl('article', { class: 'note-card', 'data-slide': 'p2' }));
  track(n2.add(makeEl('span', { 'data-step': '1' })));
  for (const id of ['pc-slide-title', 'pc-steps', 'pc-budget', 'pc-next', 'pc-flags', 'pc-clock', 'pc-pace'])
    ids[id] = track(makeEl('span', { id }));
  ids['pc-open-audience'] = track(makeEl('button', { id: 'pc-open-audience' }));
  return { all, ids, n1, n2 };
}

/* ── wire the two windows ── */
const pDom = presenterDom();
const presenter = makeWindow('presenter', pDom);

let audience = null, aDom = null;
presenter.win.open = (_url, _name) => {
  aDom = audienceDom();
  audience = makeWindow('audience', aDom);
  audience.win.opener = { closed: false, postMessage: d => presenter.win.postMessage(d) };
  const proxy = { closed: false, postMessage: d => audience.win.postMessage(d) };
  // boot the audience window (fires hello to opener)
  audience.boot();
  return proxy;
};

presenter.boot();

// 1) presenter booted at p1.1
assert.equal(pDom.ids['pc-slide-title'].textContent, '1. Placeholder A — declarative steps');

// 2) open audience → hello handshake → authoritative sync
pDom.ids['pc-open-audience'].click();
assert.ok(audience, 'audience window created');
assert.ok(aDom.s1.hasClass('active'), 'audience shows slide 1 after handshake');
assert.equal(aDom.ids['slide-num'].textContent, '1 / 2');

// register the p2 hook in the audience context (mirrors the fragment script)
const hookCalls = [];
audience.win.SlideHooks['p2'] = {
  onEnter: s => hookCalls.push(['enter', s]),
  onStep: s => hookCalls.push(['step', s]),
  onExit: () => hookCalls.push(['exit']),
};

// 3) presenter advances through p1's steps; audience reveals follow
const stepEls = aDom.s1.querySelectorAll('[data-step]');
assert.ok(stepEls[0].hasClass('on') && !stepEls[1].hasClass('on'), 'step 1 visible, step 2 hidden');
presenter.doc._fireKey(' ');
assert.ok(stepEls[1].hasClass('on') && !stepEls[2].hasClass('on'), 'space revealed step 2');
presenter.doc._fireKey(' ');
assert.ok(stepEls[2].hasClass('on'), 'space revealed step 3');

// 4) next space crosses the slide boundary; p2 hook fires onEnter
presenter.doc._fireKey(' ');
assert.ok(aDom.s2.hasClass('active') && !aDom.s1.hasClass('active'), 'crossed to slide 2');
assert.deepEqual(hookCalls.at(-1), ['enter', 1], 'p2 onEnter(1) fired');
assert.equal(pDom.ids['pc-slide-title'].textContent, '2. Placeholder B — hook API demo');
assert.equal(pDom.ids['pc-next'].textContent, 'Next: — end of deck —');

// 5) advance within p2 fires onStep(2)
presenter.doc._fireKey(' ');
assert.deepEqual(hookCalls.at(-1), ['step', 2], 'p2 onStep(2) fired');

// 6) AUDIENCE-side key sends an intent; presenter applies and pushes back
audience.doc._fireKey('ArrowLeft');
assert.deepEqual(hookCalls.at(-1), ['step', 1], 'audience back-key round-tripped to step 1');

// 7) audience PgUp intent → back to slide 1; p2 onExit fired
audience.doc._fireKey('PageUp');
assert.ok(aDom.s1.hasClass('active'), 'PgUp intent returned to slide 1');
assert.deepEqual(hookCalls.at(-1), ['exit'], 'p2 onExit fired on departure');

// 8) blank + appendix toggles propagate
presenter.doc._fireKey('b');
assert.ok(aDom.ids['blank-overlay'].hasClass('show'), 'audience blanked');
assert.equal(pDom.ids['pc-flags'].textContent.includes('AUDIENCE BLANKED'), true);
presenter.doc._fireKey('b');
assert.ok(!aDom.ids['blank-overlay'].hasClass('show'), 'unblanked');
presenter.doc._fireKey('c');
assert.ok(aDom.ids['apx-overlay'].hasClass('show'), 'appendix overlay shown');
presenter.doc._fireKey('c');

// 9) hash deep-link tracking on both windows
presenter.doc._fireKey('End');
assert.equal(presenter.location.hash, '#p2.1', 'presenter hash tracks state');
assert.equal(audience.location.hash, '#p2.1', 'audience hash tracks state');

// 10) refresh recovery: new audience window re-syncs via hello
pDom.ids['pc-open-audience'].click(); // simulates reopening after a crash
assert.ok(aDom.s2.hasClass('active'), 'reopened audience landed on current slide (p2)');
assert.equal(aDom.ids['slide-num'].textContent, '2 / 2');

// 11) multi-transport dedupe: the same intent delivered twice applies once
const beforeTitle = pDom.ids['pc-slide-title'].textContent; // at p2 (End state)
presenter.doc._fireKey('Home');
assert.equal(pDom.ids['pc-slide-title'].textContent.startsWith('1.'), true);
const dupMsg = { type: 'intent', action: 'advance', src: 'audience', id: 'dup-test-1' };
presenter.win.postMessage(dupMsg);
const afterFirst = presenter.location.hash;
presenter.win.postMessage(dupMsg); // duplicate via a "second transport"
assert.equal(presenter.location.hash, afterFirst, 'duplicate intent ignored (deduped by id)');

console.log('integration.test: ALL PASS (boot, handshake, steps, intents, hooks, blank/apx, hash, refresh-recovery, dedupe)');
