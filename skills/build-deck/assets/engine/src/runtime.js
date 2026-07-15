/* Shared runtime for both windows. Expects globals injected at build time:
     window.DECK_MANIFEST  — parsed manifest.json
     window.DECK_ROLE      — 'presenter' | 'audience'

   SYNC DESIGN (transport-agnostic bus; no dependency on window.open):
   Messages travel over every available transport — (1) opener/child postMessage
   when a window relationship exists, (2) BroadcastChannel where the browser
   allows it, (3) localStorage 'storage' events, which fire across any two
   windows of the same origin (including file:// in Chromium/Arc/Safari).
   Every message carries a unique id; receivers dedupe, so multi-transport
   delivery is harmless.

   AUTHORITY MODEL: the presenter is the source of truth. The audience window
   applies its own keys locally (so it also works standalone for rehearsal)
   AND broadcasts them as intents; the presenter applies intents and pushes
   absolute state, which the audience always adopts. The protocol converges
   regardless of which transports are alive. */
(function () {
  'use strict';
  var M = window.DECK_MANIFEST;
  var ROLE = window.DECK_ROLE;
  var S = window.DeckState;

  var deck = M.order.map(function (id) {
    var s = M.slides[id];
    return { id: id, steps: s.steps || 1, budget: s.budget || 0, title: s.title || id };
  });

  var state = { slide: 0, step: 1 };
  var blank = false;
  var apx = false;
  var audienceWin = null;   // set if presenter opened the audience via the button
  var startedAt = null;     // wall-clock ms when the talk clock started
  var hooks = window.SlideHooks = window.SlideHooks || {};
  var lastSlideIdx = -1;

  /* ── transports ── */
  var CH = M.channel || 'harvard-deck';
  var LSKEY = CH + ':bus';
  var bc = null;
  try { bc = new BroadcastChannel(CH); } catch (e) { bc = null; }

  var seen = Object.create(null);
  var seenOrder = [];
  function remember(id) {
    if (!id) return true;               // no id: accept once (shouldn't happen)
    if (seen[id]) return false;
    seen[id] = 1; seenOrder.push(id);
    if (seenOrder.length > 300) delete seen[seenOrder.shift()];
    return true;
  }
  function uid() { return Math.random().toString(36).slice(2) + Date.now().toString(36); }

  function send(msg) {
    msg.src = ROLE;
    msg.id = uid();
    remember(msg.id); // never process our own message echoed back
    if (ROLE === 'presenter' && audienceWin && !audienceWin.closed) {
      try { audienceWin.postMessage(msg, '*'); } catch (e) {}
    }
    if (ROLE === 'audience' && window.opener && !window.opener.closed) {
      try { window.opener.postMessage(msg, '*'); } catch (e) {}
    }
    if (bc) { try { bc.postMessage(msg); } catch (e) {} }
    try { localStorage.setItem(LSKEY, JSON.stringify(msg)); } catch (e) {}
  }

  function onMessage(msg) {
    if (!msg || !msg.type || msg.src === ROLE) return;
    if (!remember(msg.id)) return;      // duplicate via another transport
    if (msg.type === 'state') {         // authoritative push (presenter → audience)
      if (ROLE === 'audience') {
        state = S.clamp(deck, msg.state);
        blank = !!msg.blank; apx = !!msg.apx;
        render();
      }
    } else if (msg.type === 'intent') { // audience keypress → presenter applies
      if (ROLE === 'presenter') applyAction(msg.action);
    } else if (msg.type === 'hello') {  // audience (re)loaded → presenter re-broadcasts
      if (ROLE === 'presenter') pushState();
    }
  }
  window.addEventListener('message', function (e) { onMessage(e.data); });
  if (bc) bc.onmessage = function (e) { onMessage(e.data); };
  window.addEventListener('storage', function (e) {
    if (e.key !== LSKEY || !e.newValue) return;
    try { onMessage(JSON.parse(e.newValue)); } catch (err) {}
  });

  function pushState() {
    send({ type: 'state', state: state, blank: blank, apx: apx });
  }

  /* ── actions ── */
  function applyAction(action) {
    if (action === 'advance')        { if (!startedAt) startedAt = Date.now(); state = S.advance(deck, state); }
    else if (action === 'back')      state = S.back(deck, state);
    else if (action === 'nextSlide') state = S.nextSlide(deck, state);
    else if (action === 'prevSlide') state = S.prevSlide(deck, state);
    else if (action === 'home')      state = S.home(deck);
    else if (action === 'end')       state = S.end(deck);
    else if (action === 'blank')     blank = !blank;
    else if (action === 'apx')       apx = !apx;
    else if (action === 'clock')     startedAt = startedAt ? null : Date.now();
    else if (action === 'qa')        state = S.end(deck);
    else return;
    render();
    if (ROLE === 'presenter') pushState();
  }

  var KEYMAP = {
    ' ': 'advance', 'ArrowRight': 'advance',
    'ArrowLeft': 'back',
    'PageDown': 'nextSlide', 'ArrowDown': 'nextSlide',
    'PageUp': 'prevSlide', 'ArrowUp': 'prevSlide',
    'Home': 'home', 'End': 'end',
    'b': 'blank', 'B': 'blank',
    'c': 'apx', 'C': 'apx',
    'q': 'qa', 'Q': 'qa',
    't': 'clock', 'T': 'clock'
  };

  document.addEventListener('keydown', function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var action = KEYMAP[e.key];
    if (!action) return;
    e.preventDefault();
    if (ROLE === 'presenter') {
      applyAction(action);
    } else {
      // Apply locally (works standalone) AND tell the presenter, if one exists.
      // If a presenter is alive it will push absolute state, which we adopt —
      // the double-apply converges because pushes are absolute, and the
      // presenter dedupes multi-transport intents by message id.
      applyAction(action);
      send({ type: 'intent', action: action });
    }
  });

  /* ── rendering ── */
  function render() {
    var cur = deck[state.slide];

    if (ROLE === 'audience') {
      var slides = document.querySelectorAll('.slide');
      for (var i = 0; i < slides.length; i++) {
        var el = slides[i];
        var active = el.getAttribute('data-slide') === cur.id;
        el.classList.toggle('active', active);
        if (active) {
          var stepped = el.querySelectorAll('[data-step]');
          for (var j = 0; j < stepped.length; j++) {
            stepped[j].classList.toggle('on', (+stepped[j].getAttribute('data-step')) <= state.step);
          }
        }
      }
      if (lastSlideIdx !== state.slide) {
        if (lastSlideIdx >= 0) {
          var prev = deck[lastSlideIdx];
          if (hooks[prev.id] && hooks[prev.id].onExit) { try { hooks[prev.id].onExit(); } catch (e) {} }
        }
        if (hooks[cur.id] && hooks[cur.id].onEnter) { try { hooks[cur.id].onEnter(state.step); } catch (e) {} }
        lastSlideIdx = state.slide;
      } else if (hooks[cur.id] && hooks[cur.id].onStep) {
        try { hooks[cur.id].onStep(state.step); } catch (e) {}
      }
      var bl = document.getElementById('blank-overlay');
      if (bl) bl.classList.toggle('show', blank);
      var ax = document.getElementById('apx-overlay');
      if (ax) ax.classList.toggle('show', apx);
      var foot = document.getElementById('slide-num');
      if (foot) foot.textContent = (state.slide + 1) + ' / ' + deck.length;
    }

    if (ROLE === 'presenter') {
      var cards = document.querySelectorAll('.note-card');
      for (var k = 0; k < cards.length; k++) {
        cards[k].classList.toggle('active', cards[k].getAttribute('data-slide') === cur.id);
      }
      setText('pc-slide-title', (state.slide + 1) + '. ' + cur.title);
      var dots = document.getElementById('pc-steps');
      if (dots) {
        var html = '';
        for (var d = 1; d <= cur.steps; d++) {
          html += '<span class="dot' + (d <= state.step ? ' filled' : '') + '"></span>';
        }
        dots.innerHTML = html;
      }
      setText('pc-budget', cur.budget + ' min · plan-through ' + fmtMin(S.plannedCumEnd(deck, state.slide)));
      var nxt = deck[state.slide + 1];
      setText('pc-next', nxt ? 'Next: ' + nxt.title : 'Next: — end of deck —');
      setText('pc-flags', (blank ? '[AUDIENCE BLANKED] ' : '') + (apx ? '[APPENDIX SHOWING] ' : ''));
      var activeCard = document.querySelector('.note-card.active');
      if (activeCard) {
        var marks = activeCard.querySelectorAll('[data-step]');
        for (var m2 = 0; m2 < marks.length; m2++) {
          marks[m2].classList.toggle('on', (+marks[m2].getAttribute('data-step')) <= state.step);
        }
      }
    }

    try { history.replaceState(null, '', S.toHash(deck, state)); } catch (e) {}
  }

  function setText(id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; }
  function fmtMin(mins) {
    var m = Math.floor(mins), s = Math.round((mins - m) * 60);
    return m + ':' + (s < 10 ? '0' : '') + s;
  }

  /* presenter clock: elapsed vs plan-through-current-slide */
  if (ROLE === 'presenter') {
    setInterval(function () {
      var el = document.getElementById('pc-clock');
      var ind = document.getElementById('pc-pace');
      if (!el) return;
      if (!startedAt) { el.textContent = '00:00'; if (ind) { ind.textContent = 'clock starts on first advance (T toggles)'; ind.className = 'pace'; } return; }
      var sec = Math.floor((Date.now() - startedAt) / 1000);
      el.textContent = Math.floor(sec / 60) + ':' + ('0' + (sec % 60)).slice(-2);
      if (ind) {
        var planSec = S.plannedCumEnd(deck, state.slide) * 60;
        var delta = Math.round(planSec - sec);
        ind.textContent = delta >= 0 ? ('ahead ' + fmtSec(delta)) : ('BEHIND ' + fmtSec(-delta));
        ind.className = 'pace ' + (delta >= 0 ? 'ok' : 'over');
      }
    }, 1000);
  }
  function fmtSec(s) { return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }

  /* ── boot ── */
  window.addEventListener('DOMContentLoaded', function () {
    var fromHash = S.fromHash(deck, location.hash);
    if (fromHash) state = fromHash;

    if (ROLE === 'presenter') {
      var btn = document.getElementById('pc-open-audience');
      if (btn) btn.addEventListener('click', function () {
        // Convenience only — sync works no matter how the audience window is
        // opened. Feature string asks for a real window; Arc may still tab it.
        audienceWin = window.open(
          'slides.html' + S.toHash(deck, state),
          'harvardDeckAudience',
          'popup=yes,width=1600,height=900,left=200,top=100'
        );
        setTimeout(pushState, 600);
      });
      // If an audience window already exists (opened by hand), let it know.
      pushState();
    } else {
      send({ type: 'hello' });
    }
    render();
  });
})();
