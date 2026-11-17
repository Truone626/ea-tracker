import json,re,sys,os,datetime as D,collections
from zoneinfo import ZoneInfo
SRC=sys.argv[1] if len(sys.argv)>1 else 'data/raw.json'
OUT=sys.argv[2] if len(sys.argv)>2 else 'site/index.html'
P=json.load(open(SRC))
COMPS=['EA','EA National','EA2'];BI={47:0,51:1,48:2}
pulled=D.datetime.fromisoformat(P['pulledAt'].replace('Z','+00:00'))
local=pulled.astimezone(ZoneInfo('America/Los_Angeles'))
asof=local.strftime('%b %-d, %Y, %-I:%M %p')+' Pacific'
OVR={1363:'FC1 Academy',1379:'Atletico Rojo',902:'Seattle Celtic',1408:'FLYTE SC- Inland Empire',1355:'Steel United TX',1335:'Soccer Chance Academy',1333:'Oregon Surf SC',1606:'Saints Soccer Academy',1591:'Culver City Football Club',923:'Fram Soccer Club',1121:'LAIFC'}
teams=[];ix={};cl=collections.defaultdict(collections.Counter)
for r in P['standings']:
    n=r['n'].strip();k=(BI[r['b']],r['age'],n);N=r['nums']
    div=re.sub(r'^\s*U\d+ | Division\s*$','',r['div'].strip()).strip()
    ix[k]=len(teams)
    teams.append([n,r['ac'],BI[r['b']],r['age'],div,int(r['tid']),int(r['rank']),int(N[0]),int(N[2]),int(N[3]),int(N[5]),int(N[4]),int(N[6]),int(N[7]),N[1]])
    cl[r['ac']][re.sub(r' \(\d+\)$| \d+$','',n)]+=1
clubs={k:OVR.get(k,v.most_common(1)[0][0]) for k,v in cl.items()}
venues=[];vi={};matches=[];no=set();now=local.replace(tzinfo=None)
tally=collections.defaultdict(lambda:[0,0,0,0,0,0])
tbd=[];fut=[];mid=0
for m in P['matches']:
    c=COMPS.index(m['b']);when=D.datetime.strptime(m['dt'].upper(),'%m/%d/%y %I:%M%p')
    sides=[]
    for nm,ac,dv in((m['h'],m['ha'],m['dh']),(m['a'],m['aa'],m['da'])):
        nm=nm.strip();k=(c,m['age'],nm)
        if k not in ix:
            no.add(nm);ix[k]=len(teams);teams.append([nm,ac['a'],c,m['age'],dv,None,None,None,None,None,None,None,None,None,None]);clubs.setdefault(ac['a'],nm)
        sides.append(ix[k])
    s=re.fullmatch(r'(\d+) : (\d+)',m['s'])
    if not s and m['s']!='TBD': raise SystemExit('score '+m['s'])
    hs,as_=(int(s[1]),int(s[2])) if s else (None,None)
    vk=(m['v'],m['lat'],m['lng'])
    if vk not in vi: vi[vk]=len(venues);venues.append(list(vk))
    matches.append([m['id'],when.strftime('%Y-%m-%dT%H:%M'),sides[0],sides[1],hs,as_,vi[vk]])
    if s:
        for t,g,a in((sides[0],hs,as_),(sides[1],as_,hs)):
            x=tally[t];x[0]+=1;x[4]+=g;x[5]+=a;x[1 if g>a else 2 if g==a else 3]+=1
        if when>now: fut.append([m['id'],m['age'],m['b'],m['h'].strip(),m['s'].replace(' ',''),m['a'].strip(),when.strftime('%b %-d, %Y')])
    else:
        if when<now: tbd.append(m['id'])
        elif when.hour==0 and when.minute==0: mid+=1
ok=diff=0;bad=[]
for i,t in enumerate(teams):
    if t[6] is None: continue
    x=tally.get(i,[0]*6)
    if [t[8],t[9],t[10],t[11],t[12],t[13],t[7]]==[x[0],x[1],x[2],x[3],x[4],x[5],x[1]*3+x[2]]: ok+=1
    else: diff+=1;bad.append(t[0])
data=dict(season='2026–27',comps=COMPS,asOfLong=asof,clubs=clubs,teams=teams,matches=matches,venues=venues,
 check=dict(ok=ok,diff=diff,total=ok+diff,tbdPast=tbd,futureScored=fut,midnight=mid,noTable=sorted(no)))
js=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
body=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'template.html'),encoding='utf8').read().replace('__DATA__',js)
head='<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n<meta name="description" content="Standings, schedules, results and rankings for every Elite Academy League club. Independent, updated daily from the league\'s public data.">\n<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n'
html=head+body.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','',1).replace('<div class="wrap">','</head>\n<body>\n<div class="wrap">',1)+'\n</body>\n</html>\n'
os.makedirs(os.path.dirname(OUT) or '.',exist_ok=True)
open(OUT,'w',encoding='utf8').write(html)
os.makedirs('data',exist_ok=True)
open('data/latest.json','w',encoding='utf8').write(json.dumps(data,ensure_ascii=False,separators=(',',':')))
prev=os.environ.get('PREV_MATCHES')
if prev and len(matches)<0.9*int(prev): raise SystemExit(f'match count dropped from {prev} to {len(matches)}; not publishing')
if diff: print(f'::warning::{diff} official table lines do not match the match results; shown on the Data notes page')
print(asof,'teams',len(teams),'clubs',len(clubs),'matches',len(matches),'venues',len(venues),'KB',len(html)//1024,'check',ok,diff,bad[:5],'tbd',len(tbd),'fut',len(fut),'mid',mid,'noTable',sorted(no))
