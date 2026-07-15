import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const S = require('../src/state.js');

const deck = [
  { id: 's1', steps: 1, budget: 1 },
  { id: 's2', steps: 3, budget: 2 },
  { id: 's3', steps: 2, budget: 2.5 },
];

// advance walks every step then crosses slides
let st = { slide: 0, step: 1 };
st = S.advance(deck, st); assert.deepEqual(st, { slide: 1, step: 1 }, 'crosses slide boundary');
st = S.advance(deck, st); assert.deepEqual(st, { slide: 1, step: 2 });
st = S.advance(deck, st); assert.deepEqual(st, { slide: 1, step: 3 });
st = S.advance(deck, st); assert.deepEqual(st, { slide: 2, step: 1 });
st = S.advance(deck, st); assert.deepEqual(st, { slide: 2, step: 2 });
st = S.advance(deck, st); assert.deepEqual(st, { slide: 2, step: 2 }, 'holds at deck end');

// back reverses exactly, landing on the LAST step of the previous slide
st = S.back(deck, st); assert.deepEqual(st, { slide: 2, step: 1 });
st = S.back(deck, st); assert.deepEqual(st, { slide: 1, step: 3 }, 'back lands on prev last step');
st = S.back(deck, { slide: 0, step: 1 }); assert.deepEqual(st, { slide: 0, step: 1 }, 'holds at start');

// full round trip: advance N times then back N times returns to origin
let fwd = { slide: 0, step: 1 };
const trail = [fwd];
for (let i = 0; i < 5; i++) { fwd = S.advance(deck, fwd); trail.push(fwd); }
let rev = fwd;
for (let i = trail.length - 2; i >= 0; i--) {
  rev = S.back(deck, rev);
  assert.deepEqual(rev, trail[i], `reverse step ${i} retraces`);
}

// whole-slide nav resets step to 1
assert.deepEqual(S.nextSlide(deck, { slide: 1, step: 3 }), { slide: 2, step: 1 });
assert.deepEqual(S.prevSlide(deck, { slide: 2, step: 2 }), { slide: 1, step: 1 });
assert.deepEqual(S.home(deck), { slide: 0, step: 1 });
assert.deepEqual(S.end(deck), { slide: 2, step: 1 });

// clamp sanitizes garbage
assert.deepEqual(S.clamp(deck, { slide: 99, step: 99 }), { slide: 2, step: 2 });
assert.deepEqual(S.clamp(deck, { slide: -3, step: 0 }), { slide: 0, step: 1 });

// hash round trip
const h = S.toHash(deck, { slide: 1, step: 2 });
assert.equal(h, '#s2.2');
assert.deepEqual(S.fromHash(deck, h), { slide: 1, step: 2 });
assert.deepEqual(S.fromHash(deck, '#s3'), { slide: 2, step: 1 }, 'stepless hash defaults to 1');
assert.equal(S.fromHash(deck, '#nope.4'), null, 'unknown id is null');
assert.deepEqual(S.fromHash(deck, '#s2.99'), { slide: 1, step: 3 }, 'overlarge step clamps');

// planned cumulative minutes
assert.equal(S.plannedCumEnd(deck, 0), 1);
assert.equal(S.plannedCumEnd(deck, 2), 5.5);

console.log('state.test: ALL PASS');
