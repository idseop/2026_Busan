"""Fetch only explicitly reviewed official pages; do not crawl attachments or personal rosters."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, urllib.request, sys
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/예방지원-근거분석-20260916/response'
class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'): self.skip += 1
    def handle_endtag(self, tag):
        if tag in ('script','style'): self.skip = max(0,self.skip-1)
    def handle_data(self, s):
        if not self.skip and s.strip(): self.parts.append(s.strip())

def fetch(s):
    rec={'id':s['id'],'url':s['url'],'accessedAt':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(s['url'],headers={'User-Agent':'Busan119-Research/1.0 (official-page evidence review)'})
        with urllib.request.urlopen(req,timeout=30) as r:
            b=r.read(); enc=r.headers.get_content_charset() or 'utf-8'; rec.update(status=r.status,finalUrl=r.url)
        ispdf=b.startswith(b'%PDF')
        p=OUT/(s['id']+('.pdf' if ispdf else '.html')); p.write_bytes(b)
        if ispdf:
            import pymupdf
            with pymupdf.open(stream=b,filetype='pdf') as doc:
                txt='\n'.join(f'PDF page {i+1}\n'+page.get_text() for i,page in enumerate(doc))
                for pn in s.get('renderPages',[]):
                    doc[pn-1].get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(OUT/(s['id']+f'-page-{pn}.png'))
        else:
            parser=Text(); parser.feed(b.decode(enc,errors='replace'))
            txt='\n'.join(parser.parts)
        t=OUT/(s['id']+'.txt'); t.write_text(txt,encoding='utf-8')
        rec.update(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(b).hexdigest(),textPath=t.relative_to(ROOT).as_posix(),textSha256=hashlib.sha256(t.read_bytes()).hexdigest(),quoteFound=''.join(s['quote'].split()) in ''.join(txt.split()))
    except Exception as e: rec.update(status='failed',error=repr(e))
    return rec

if __name__=='__main__':
    data=json.loads((OUT/'official-response.json').read_text(encoding='utf-8'))
    if '--verify-only' in sys.argv:
        manifest=json.loads((OUT/'collection-manifest.json').read_text(encoding='utf-8'))
        receipts=manifest['sources']
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: receipts=list(pool.map(fetch,data['sources']))
        manifest={'createdAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':receipts,'note':'Raw official page snapshots are internal evidence. No attachment roster was fetched.'}
    checks=[]
    for s in data['sources']:
        r=next(x for x in receipts if x['id']==s['id'])
        checks.append({'id':s['id']+':download','passed':r['status']==200})
        if r['status']!=200: continue
        for pathkey,hashkey in [('path','sha256'),('textPath','textSha256')]:
            checks.append({'id':s['id']+':'+hashkey,'passed':hashlib.sha256((ROOT/r[pathkey]).read_bytes()).hexdigest()==r[hashkey]})
        txt=(ROOT/r['textPath']).read_text(encoding='utf-8')
        r['quoteFound']=''.join(s['quote'].split()) in ''.join(txt.split())
        checks.append({'id':s['id']+':quote','passed':r['quoteFound']})
    comp=data['comparisons'][0]
    checks.append({'id':'recruitment_arithmetic','passed':comp['planned']-comp['recruited']==comp['difference'] and round(comp['recruited']/comp['planned']*100,1)==comp['attainmentPercent']})
    checks.append({'id':'no_confirmed_unmet_claim','passed':all(s['confirmedGap'] is False for s in data['sources'])})
    (OUT/'collection-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    verification={'checkedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'authorVerification':True,'independentReview':False}
    (OUT/'evidence-verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{'id':r['id'],'status':r['status'],'quoteFound':r.get('quoteFound')} for r in receipts],ensure_ascii=False))
    if verification['status']!='passed': raise SystemExit(1)
