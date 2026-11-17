import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { parseMatchesPage, parseStandings } from '../scripts/pull.mjs';
const m = parseMatchesPage(readFileSync(new URL('./fixture-matches.html', import.meta.url), 'utf8'));
assert.equal(m.pages, 6); assert.equal(m.page, 1); assert.equal(m.rows.length, 1);
assert.deepEqual(m.rows[0], { id: 124255, g: 'MALE', dt: '09/12/26 09:00am', v: 'Field #5 - Robb Athletic Field', lat: 32.754337, lng: -117.2414474, age: 'U11', b: 'EA', d: 'Southwest EA', dh: 'Southwest EA', da: 'Southwest EA', r: '1', gm: '1', h: 'ALBION SC San Diego (1)', a: 'SoCal Elite FC', ha: { a: 101, c: '/academy/101/10716/877a/10716.png' }, aa: { a: 903, c: '/academy/903/208024/ad1d/208024.png' }, s: '10 : 0' });
const s = parseStandings(readFileSync(new URL('./fixture-standings.html', import.meta.url), 'utf8'), 51, 'U13');
assert.deepEqual(s, [{ b: 51, age: 'U13', div: 'U13 Mid-America Division', grp: '67', tid: '7023', rank: '1', n: 'Chicago Empire FC', nums: ['6', '3.00', '2', '2', '0', '0', '12', '1', '5.50'], ac: 1368, c: '/academy/1368/403633/97f0/403633.png' }]);
console.log('parse tests passed');
