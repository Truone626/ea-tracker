// App icons and the web app manifest, so the site can be added to a phone's home screen.
import { writeFileSync, mkdirSync } from 'node:fs';
import sharp from 'sharp';
const out = process.argv[2] || 'site';
mkdirSync(out, { recursive: true });
// full: rounded tile for favicon; square: edge-to-edge for app icons (phones round the corners themselves)
const mark = (r, scale = 1) => {
  const s = 512, c = s / 2, k = scale;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${s} ${s}">
<defs><radialGradient id="g" cx=".5" cy=".38" r=".7"><stop offset="0" stop-color="#12304a"/><stop offset="1" stop-color="#060c17"/></radialGradient></defs>
<rect width="${s}" height="${s}" rx="${r}" fill="url(#g)"/>
<path d="M${c} ${c - 190 * k}V${c + 190 * k}" stroke="#2dd4bf" stroke-width="${26 * k}" stroke-linecap="round" opacity=".55"/>
<circle cx="${c}" cy="${c}" r="${118 * k}" fill="none" stroke="#2dd4bf" stroke-width="${40 * k}"/>
<circle cx="${c}" cy="${c}" r="${38 * k}" fill="#2dd4bf"/></svg>`;
};
writeFileSync(`${out}/favicon.svg`, mark(112));
const png = (svg, size, file) => sharp(Buffer.from(svg)).resize(size, size).png().toFile(`${out}/${file}`);
await png(mark(0), 180, 'apple-touch-icon.png');
await png(mark(0), 192, 'icon-192.png');
await png(mark(0), 512, 'icon-512.png');
await png(mark(0, .72), 512, 'icon-maskable-512.png'); // smaller mark stays inside the safe zone
writeFileSync(`${out}/manifest.webmanifest`, JSON.stringify({
  name: 'EAL Tracker', short_name: 'EAL Tracker',
  description: 'Elite Academy League standings, schedules, results and rankings.',
  start_url: './', scope: './', display: 'standalone', background_color: '#060c17', theme_color: '#060c17',
  icons: [
    { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
    { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
    { src: 'icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
  ],
}, null, 2));
console.log('icons and manifest written to', out);
