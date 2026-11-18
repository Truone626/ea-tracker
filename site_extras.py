"""Extra files built alongside the site on every update:
- calendar subscriptions (.ics) for every team and for each club per competition
- small share pages per club and team, so links get a proper preview card
- sitemap.xml and robots.txt
"""
import os, re, json, html as H, datetime as D

CK = ['ea', 'national', 'ea2']


def slugify(s):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-') or 'club'


def club_slugs(clubs):
    out, used = {}, set()
    for cid, name in sorted(clubs.items(), key=lambda kv: kv[1].lower()):
        s = slugify(name)
        if s in used:
            s = f'{s}-{cid}'
        used.add(s)
        out[cid] = s
    return out


# ---------- calendars ----------
def _esc(s):
    return str(s).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def _fold(line):
    b = line.encode('utf-8')
    if len(b) <= 75:
        return line
    parts, cur = [], b''
    for ch in line:
        e = ch.encode('utf-8')
        if len(cur) + len(e) > (75 if not parts else 74):
            parts.append(cur.decode('utf-8'))
            cur = b''
        cur += e
    parts.append(cur.decode('utf-8'))
    return '\r\n '.join(parts)


def _cal(name, desc, events):
    L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//EAL Tracker//Elite Academy League//EN', 'CALSCALE:GREGORIAN',
         'METHOD:PUBLISH', f'X-WR-CALNAME:{_esc(name)}', f'X-WR-CALDESC:{_esc(desc)}',
         'X-PUBLISHED-TTL:PT6H', 'REFRESH-INTERVAL;VALUE=DURATION:PT6H']
    L += events
    L.append('END:VCALENDAR')
    return '\r\n'.join(_fold(l) for l in L) + '\r\n'


def _event(m, teams, venues, comps, site, stamp, prefix='', owner=None):
    mid, when, hi, ai, hs, as_, vi = m
    h, a, v = teams[hi], teams[ai], venues[vi]
    dt = D.datetime.strptime(when, '%Y-%m-%dT%H:%M')
    tbd_time = dt.hour == 0 and dt.minute == 0
    venue = 'Venue TBD' if re.match(r'^\s*TBD\b', v[0] or '', re.I) else v[0]
    if hs is not None:
        summary = f'{prefix}{h[0]} {hs}-{as_} {a[0]} (final)'
    else:
        summary = f'{prefix}{h[0]} vs {a[0]}'
    desc = [f'{comps[h[2]]} {h[3]} · {h[4]}' + (f' v {a[4]}' if a[4] != h[4] else '')]
    if hs is None and tbd_time:
        desc.append('Kickoff time not set by the league yet.')
    elif hs is None:
        desc.append('Kickoff time as listed by the league. End time is an estimate.')
    o = owner if owner is not None else h
    desc.append(f'Match {mid}. Details: {site}#team-{CK[o[2]]}-{o[5]}' if o[5] else f'Match {mid}.')
    E = ['BEGIN:VEVENT', f'UID:match-{mid}@ea-tracker', f'DTSTAMP:{stamp}']
    if tbd_time:
        E += [f'DTSTART;VALUE=DATE:{dt:%Y%m%d}', f'DTEND;VALUE=DATE:{(dt + D.timedelta(days=1)):%Y%m%d}']
    else:
        E += [f'DTSTART:{dt:%Y%m%dT%H%M%S}', f'DTEND:{(dt + D.timedelta(minutes=90)):%Y%m%dT%H%M%S}']
    E += [f'SUMMARY:{_esc(summary)}', f'LOCATION:{_esc(venue)}', f'DESCRIPTION:{_esc(chr(10).join(desc))}', 'TRANSP:OPAQUE']
    if v[1] is not None and venue != 'Venue TBD':
        E.append(f'GEO:{v[1]};{v[2]}')
    E.append('END:VEVENT')
    return E


def write_calendars(data, outdir, site):
    teams, matches, venues, comps, clubs = data['teams'], data['matches'], data['venues'], data['comps'], data['clubs']
    stamp = D.datetime.now(D.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    by_team = {}
    for m in matches:
        for side in (m[2], m[3]):
            by_team.setdefault(side, []).append(m)
    os.makedirs(f'{outdir}/cal', exist_ok=True)
    n = 0
    for i, t in enumerate(teams):
        if not t[5]:
            continue
        ms = sorted(by_team.get(i, []), key=lambda m: (m[1], m[0]))
        ev = []
        for m in ms:
            ev += _event(m, teams, venues, comps, site, stamp, owner=t)
        name = f'{t[0]} {t[3]} ({comps[t[2]]})'
        open(f'{outdir}/cal/{CK[t[2]]}-{t[5]}.ics', 'w', encoding='utf-8', newline='').write(
            _cal(name, f'{t[3]} {t[4]} schedule and results. Updated twice a day by EAL Tracker.', ev))
        n += 1
    # club calendars per competition: every match of every team the club has in it
    for cid, cname in clubs.items():
        cid = int(cid)
        for c in range(3):
            idx = {i for i, t in enumerate(teams) if t[1] == cid and t[2] == c}
            if not idx:
                continue
            ms = sorted({m[0]: m for i in idx for m in by_team.get(i, [])}.values(), key=lambda m: (m[1], m[0]))
            ev = []
            for m in ms:
                own = teams[m[2]] if m[2] in idx else teams[m[3]]
                ev += _event(m, teams, venues, comps, site, stamp, prefix=f'{teams[m[2]][3]} ', owner=own)
            open(f'{outdir}/cal/club-{cid}-{CK[c]}.ics', 'w', encoding='utf-8', newline='').write(
                _cal(f'{cname} · {comps[c]}', f'All {cname} {comps[c]} matches. Updated twice a day by EAL Tracker.', ev))
            n += 1
    return n


# ---------- share pages ----------
STUB = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="EAL Tracker">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">
<meta http-equiv="refresh" content="0; url={target}">
<script>location.replace({target_js});</script>
<style>body{{background:#060c17;color:#eef3fb;font-family:system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0}}a{{color:#2dd4bf}}</style>
</head><body><p>Opening <a href="{target}">{name}</a> on EAL Tracker…</p></body></html>
'''


def _ord(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def write_share_pages(data, outdir, site, slugs):
    teams, comps, clubs = data['teams'], data['comps'], data['clubs']
    urls = []
    for cid, name in clubs.items():
        cid = str(cid)
        ts = [t for t in teams if t[1] == int(cid)]
        cs = sorted({t[2] for t in ts})
        best = sorted([t for t in ts if t[6] is not None and t[8]], key=lambda t: (t[6], -t[7]))
        bits = [f"{len(ts)} teams in {', '.join(comps[c] for c in cs)}"]
        if best:
            bits.append(f'{best[0][3]} {comps[best[0][2]]} is {_ord(best[0][6])} in {best[0][4]}')
        desc = f"{name} in the Elite Academy League {data['season']}: standings, schedules, results and rankings. " + '. '.join(bits) + '.'
        url = f'{site}club/{slugs[cid]}/'
        target = f'../../#club-{cid}'
        p = f'{outdir}/club/{slugs[cid]}'
        os.makedirs(p, exist_ok=True)
        open(f'{p}/index.html', 'w', encoding='utf-8').write(STUB.format(
            title=H.escape(f'{name} · EAL Tracker'), desc=H.escape(desc), url=url, img=f'{site}og/club-{cid}.png',
            target=target, target_js=json.dumps(target), name=H.escape(name)))
        urls.append(url)
    for t in teams:
        if not t[5]:
            continue
        key = f'{CK[t[2]]}-{t[5]}'
        rec = f'{t[9]}-{t[10]}-{t[11]} W-D-L' if t[8] is not None else 'not in the league table yet'
        pos = f'{_ord(t[6])} in {t[4]}' if t[6] is not None else t[4]
        desc = f"{t[0]} {t[3]} · {comps[t[2]]} · {pos} · {rec}. Schedule, results, standings and match-day weather."
        url = f'{site}team/{key}/'
        target = f'../../#team-{key}'
        p = f'{outdir}/team/{key}'
        os.makedirs(p, exist_ok=True)
        open(f'{p}/index.html', 'w', encoding='utf-8').write(STUB.format(
            title=H.escape(f'{t[0]} {t[3]} · EAL Tracker'), desc=H.escape(desc), url=url, img=f'{site}og/club-{t[1]}.png',
            target=target, target_js=json.dumps(target), name=H.escape(f'{t[0]} {t[3]}')))
        urls.append(url)
    today = data['asOfIso'][:10]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in [site] + urls:
        sm.append(f'<url><loc>{H.escape(u)}</loc><lastmod>{today}</lastmod></url>')
    sm.append('</urlset>')
    open(f'{outdir}/sitemap.xml', 'w', encoding='utf-8').write('\n'.join(sm) + '\n')
    open(f'{outdir}/robots.txt', 'w', encoding='utf-8').write(f'User-agent: *\nAllow: /\nSitemap: {site}sitemap.xml\n')
    return len(urls)


def analytics_snippet(code):
    code = (code or '').strip()
    if not re.fullmatch(r'[a-z0-9-]{1,63}', code or ''):
        return ''
    return ('<script>window.goatcounter={no_onload:true};'
            'function eaCount(){if(window.goatcounter&&window.goatcounter.count)window.goatcounter.count({path:location.pathname+location.search+location.hash})}'
            "window.addEventListener('hashchange',eaCount);</script>\n"
            f'<script data-goatcounter="https://{code}.goatcounter.com/count" async src="//gc.zgo.at/count.js" onload="eaCount()"></script>')
