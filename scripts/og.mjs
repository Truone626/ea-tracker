// Builds 1200x630 link-preview images (one per club, plus the home page) into <site>/og/.
import { readFileSync, existsSync, mkdirSync } from 'node:fs';
import sharp from 'sharp';
const data = JSON.parse(readFileSync(process.argv[2] || 'data/latest.json', 'utf8'));
const out = (process.argv[3] || 'site') + '/og';
mkdirSync(out, { recursive: true });
const x = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[c]));
const W = 1200, H = 630;
const stripes = [...Array(14)].map((_, i) => `<rect x="${i * 90}" y="0" width="45" height="${H}" fill="#0d3122" opacity=".55"/>`).join('');
const bg = `<rect width="${W}" height="${H}" fill="#060c17"/><g opacity=".7">${stripes}</g>
 <rect width="${W}" height="${H}" fill="url(#fade)"/>
 <defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0a1424" stop-opacity="1"/><stop offset=".55" stop-color="#0a1424" stop-opacity=".55"/><stop offset="1" stop-color="#060c17" stop-opacity=".9"/></linearGradient></defs>`;
const brand = `<g transform="translate(64,560)"><circle cx="14" cy="-9" r="11" fill="none" stroke="#2dd4bf" stroke-width="5"/><text x="38" y="0" font-family="DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="30" fill="#eef3fb" letter-spacing="2">EA <tspan fill="#2dd4bf">TRACKER</tspan></text></g>`;
function wrap(name, max) {
  const words = name.split(/\s+/); const lines = []; let cur = '';
  for (const w of words) { if ((cur + ' ' + w).trim().length > max && cur) { lines.push(cur); cur = w; } else cur = (cur + ' ' + w).trim(); }
  if (cur) lines.push(cur); return lines.slice(0, 3);
}
async function clubCard(id, name, comps) {
  const lines = wrap(name.toUpperCase(), 16);
  const longest = Math.max(...lines.map(l => l.length));
  const fs = Math.min(lines.length > 2 ? 64 : 78, Math.floor(700 / (longest * 0.66)));
  const txt = lines.map((l, i) => `<text x="440" y="${250 + i * (fs + 6) - (lines.length - 1) * (fs / 2)}" font-family="DejaVu Sans, Arial, sans-serif" font-stretch="condensed" font-weight="700" font-size="${fs}" fill="#eef3fb">${x(l)}</text>`).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${bg}
   <rect x="64" y="135" width="320" height="320" rx="56" fill="#f2f5fa"/>
   <text x="440" y="120" font-family="DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="24" fill="#5eead4" letter-spacing="4">ELITE ACADEMY LEAGUE · ${x(data.season)}</text>
   ${txt}
   <text x="440" y="${430}" font-family="DejaVu Sans, Arial, sans-serif" font-size="30" fill="#9aabc3">${x(comps)}</text>
   <text x="440" y="${474}" font-family="DejaVu Sans, Arial, sans-serif" font-size="26" fill="#9aabc3">Standings · Schedules · Results · Rankings</text>
   ${brand}</svg>`;
  let img = sharp(Buffer.from(svg));
  const crest = `crests/${id}.webp`;
  const layers = [];
  if (existsSync(crest)) layers.push({ input: await sharp(crest).resize(250, 250, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer(), left: 99, top: 170 });
  else {
    const ini = name.replace(/\(.*?\)/g, '').split(/\s+/).filter(w => !/^(SC|FC|Soccer|Club|Academy)$/i.test(w)).slice(0, 2).map(w => w[0]).join('').toUpperCase();
    layers.push({ input: Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320"><rect width="320" height="320" rx="56" fill="#1f4d63"/><text x="160" y="200" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="130" fill="#fff">${x(ini)}</text></svg>`), left: 64, top: 135 });
  }
  await img.composite(layers).png({ compressionLevel: 9, palette: true }).toFile(`${out}/club-${id}.png`);
}
const t0 = Date.now();
const comps = {};
for (const t of data.teams) (comps[t[1]] ||= new Set()).add(data.comps[t[2]]);
const ids = Object.keys(data.clubs);
let i = 0;
await Promise.all([0, 1, 2, 3].map(async () => { while (i < ids.length) { const id = ids[i++]; await clubCard(id, data.clubs[id], [...comps[id] || []].join(' · ')); } }));
// home card
const home = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">${bg}
 <text x="64" y="150" font-family="DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="26" fill="#5eead4" letter-spacing="4">ELITE ACADEMY LEAGUE · EA · EA NATIONAL · EA2</text>
 <text x="64" y="270" font-family="DejaVu Sans Condensed, DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="104" fill="#eef3fb">FIND YOUR</text>
 <text x="64" y="384" font-family="DejaVu Sans Condensed, DejaVu Sans, Arial, sans-serif" font-weight="700" font-size="104" fill="#2dd4bf">ELITE ACADEMY CLUB</text>
 <text x="64" y="452" font-family="DejaVu Sans, Arial, sans-serif" font-size="30" fill="#9aabc3">${ids.length} clubs · Standings, schedules, results, rankings · ${x(data.season)}</text>
 ${brand}</svg>`;
await sharp(Buffer.from(home)).png({ compressionLevel: 9, palette: true }).toFile(`${out}/home.png`);
console.log(`og images: ${ids.length + 1} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
