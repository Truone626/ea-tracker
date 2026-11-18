// Finds each club's main color from its crest (crests/<id>.webp) and writes crests/colors.json.
// Ignores transparent, near-white, near-black and grey pixels; picks the most common strong hue,
// (hue averaged on the color wheel, so reds near 0°/360° stay red), then adjusts brightness so it reads well on the site's dark background.
import { readdirSync, writeFileSync } from 'node:fs';
import sharp from 'sharp';
const DIR = 'crests';
const rgb2hsl = (r, g, b) => { r /= 255; g /= 255; b /= 255; const mx = Math.max(r, g, b), mn = Math.min(r, g, b); let h = 0, s = 0; const l = (mx + mn) / 2;
  if (mx !== mn) { const d = mx - mn; s = l > .5 ? d / (2 - mx - mn) : d / (mx + mn); h = mx === r ? (g - b) / d + (g < b ? 6 : 0) : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h *= 60; } return [h, s, l]; };
const hex = (h, s, l) => { const a = s * Math.min(l, 1 - l); const f = n => { const k = (n + h / 30) % 12; const c = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1)); return Math.round(c * 255).toString(16).padStart(2, '0'); }; return '#' + f(0) + f(8) + f(4); };
const out = {};
for (const f of readdirSync(DIR).filter(f => f.endsWith('.webp'))) {
  const id = f.slice(0, -5);
  const { data, info } = await sharp(`${DIR}/${f}`).ensureAlpha().resize(64, 64, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } }).raw().toBuffer({ resolveWithObject: true });
  const bins = new Map();
  for (let i = 0; i < data.length; i += info.channels) {
    const [r, g, b, a] = [data[i], data[i + 1], data[i + 2], data[i + 3]];
    if (a < 160) continue;
    const [h, s, l] = rgb2hsl(r, g, b);
    if (l > .9 || l < .1 || s < .28) continue;
    const k = Math.round(h / 12) % 30;
    const e = bins.get(k) || { n: 0, x: 0, y: 0, s: 0, l: 0 };
    const w = .5 + s, rad = h * Math.PI / 180; e.n += w; e.x += Math.cos(rad) * w; e.y += Math.sin(rad) * w; e.s += s * w; e.l += l * w; bins.set(k, e);
  }
  const top = [...bins.values()].sort((a, b) => b.n - a.n)[0];
  if (!top || top.n < 40) continue; // no clear color: the site falls back to its teal
  let h = (Math.atan2(top.y, top.x) * 180 / Math.PI + 360) % 360, s = Math.max(.5, Math.min(.85, top.s / top.n)), l = top.l / top.n;
  l = Math.max(.5, Math.min(.64, l)); // readable on dark navy
  out[id] = hex(h, s, l);
}
writeFileSync(`${DIR}/colors.json`, JSON.stringify(out));
console.log(`club colors: ${Object.keys(out).length} of ${readdirSync(DIR).filter(f => f.endsWith('.webp')).length} crests`);
