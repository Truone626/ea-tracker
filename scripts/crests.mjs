// Downloads each club's crest once from the league's image host, resizes it,
// and stores it in crests/<clubId>.webp. Only new or changed crests are fetched.
// A missing crest never fails the update; the site shows initials instead.
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import sharp from 'sharp';

const HOST = process.env.EA_CREST_HOST || 'https://d11602kq9f3hhz.cloudfront.net';
const UA = process.env.EA_UA || 'EA-Tracker (independent fan site; daily public data refresh)';
const raw = JSON.parse(readFileSync(process.argv[2] || 'data/raw.json', 'utf8'));
const DIR = 'crests';
mkdirSync(DIR, { recursive: true });
const manPath = `${DIR}/manifest.json`;
const man = existsSync(manPath) ? JSON.parse(readFileSync(manPath, 'utf8')) : {};

// Most common crest path per club id, from standings and both sides of every match.
const seen = {};
const add = (id, c) => { if (!id || !c) return; (seen[id] ||= {})[c] = (seen[id][c] || 0) + 1; };
for (const r of raw.standings) add(r.ac, r.c);
for (const m of raw.matches) { add(m.ha?.a, m.ha?.c); add(m.aa?.a, m.aa?.c); }
const want = Object.fromEntries(Object.entries(seen).map(([id, cs]) => [id, Object.entries(cs).sort((a, b) => b[1] - a[1])[0][0]]));

const todo = Object.entries(want).filter(([id, c]) => man[id] !== c || !existsSync(`${DIR}/${id}.webp`));
let ok = 0, failed = [];
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function one([id, c]) {
  for (let i = 0; i < 3; i++) {
    try {
      const r = await fetch(HOST + c, { headers: { 'User-Agent': UA } });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const buf = Buffer.from(await r.arrayBuffer());
      await sharp(buf).resize(128, 128, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).webp({ quality: 85 }).toFile(`${DIR}/${id}.webp`);
      man[id] = c; ok++; return;
    } catch (e) {
      if (i === 2) failed.push(`${id}: ${e.message}`); else await sleep(1500 * (i + 1));
    }
  }
}
let ix = 0;
await Promise.all([0, 1, 2, 3].map(async () => { while (ix < todo.length) { await one(todo[ix++]); await sleep(150); } }));
writeFileSync(manPath, JSON.stringify(man, null, 0));
const have = Object.keys(want).filter(id => existsSync(`${DIR}/${id}.webp`)).length;
console.log(`crests: ${Object.keys(want).length} clubs, ${have} stored, ${ok} downloaded now, ${failed.length} failed`);
if (failed.length) console.log(`::warning::${failed.length} club crests could not be downloaded; those clubs show initials. ${failed.slice(0, 5).join('; ')}`);
