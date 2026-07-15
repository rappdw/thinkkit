/* Pure deck state machine — no DOM. Testable in Node, inlined into both windows.
   deck: [{id, steps}, ...] (linear order only; appendix is an overlay, not a slide)
   state: {slide: <index into deck>, step: <1..steps>} */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) { module.exports = factory(); }
  else { root.DeckState = factory(); }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  function clamp(deck, s) {
    var slide = Math.min(Math.max(0, s.slide | 0), deck.length - 1);
    var steps = deck[slide].steps || 1;
    var step = Math.min(Math.max(1, s.step | 0), steps);
    return { slide: slide, step: step };
  }

  function advance(deck, s) {
    s = clamp(deck, s);
    if (s.step < (deck[s.slide].steps || 1)) return { slide: s.slide, step: s.step + 1 };
    if (s.slide < deck.length - 1) return { slide: s.slide + 1, step: 1 };
    return s; // end of deck: hold
  }

  function back(deck, s) {
    s = clamp(deck, s);
    if (s.step > 1) return { slide: s.slide, step: s.step - 1 };
    if (s.slide > 0) return { slide: s.slide - 1, step: deck[s.slide - 1].steps || 1 };
    return s; // start of deck: hold
  }

  function nextSlide(deck, s) {
    s = clamp(deck, s);
    return s.slide < deck.length - 1 ? { slide: s.slide + 1, step: 1 } : s;
  }

  function prevSlide(deck, s) {
    s = clamp(deck, s);
    return s.slide > 0 ? { slide: s.slide - 1, step: 1 } : { slide: 0, step: 1 };
  }

  function home(deck) { return { slide: 0, step: 1 }; }
  function end(deck) { return { slide: deck.length - 1, step: 1 }; }

  /* hash <-> state: "#<id>.<step>" */
  function toHash(deck, s) {
    s = clamp(deck, s);
    return '#' + deck[s.slide].id + '.' + s.step;
  }
  function fromHash(deck, hash) {
    if (!hash) return null;
    var m = /^#?([\w-]+)(?:\.(\d+))?$/.exec(hash);
    if (!m) return null;
    for (var i = 0; i < deck.length; i++) {
      if (deck[i].id === m[1]) return clamp(deck, { slide: i, step: m[2] ? +m[2] : 1 });
    }
    return null;
  }

  /* planned cumulative minutes at the END of slide index i (budgets in minutes) */
  function plannedCumEnd(deck, i) {
    var t = 0;
    for (var k = 0; k <= i && k < deck.length; k++) t += (deck[k].budget || 0);
    return t;
  }

  return { clamp: clamp, advance: advance, back: back, nextSlide: nextSlide,
           prevSlide: prevSlide, home: home, end: end,
           toHash: toHash, fromHash: fromHash, plannedCumEnd: plannedCumEnd };
}));
