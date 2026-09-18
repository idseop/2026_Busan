"""Independent CSV reconciliation and actual Chromium interaction checks."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, json, hashlib
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web/submission'
OUT=ROOT/'output/최신웹-20260918'
AUDIT=ROOT/'data/processed/최신웹연결-20260918'
checks=[]
def check(name,condition,detail=None):
    checks.append(dict(name=name,passed=bool(condition),detail=detail))
    if not condition: raise AssertionError(name+': '+str(detail))
def read(p): return list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
def data(p):
    s=p.read_text(encoding='utf-8-sig');return json.loads(s[s.index('=')+1:].strip().rstrip(';'))
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=data(WEB/'data/current-data.js')
    base=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
    rows=read(ROOT/'data/processed/신고인구특성재정립-20260917/calls/region-all-subtypes-by-year.csv')
    by_gu=Counter();by_year=Counter();by_subtype=Counter();by_key=Counter()
    for r in rows:
        v=int(r['count']);gu=r['CLMTY_SGG_NM'];raw=r['CLMTY_EMD_NM'];year=int(r['year']);st=r['EMRG_RSCU_CLSF_NM']
        typ=r['EMRG_RSCU_ASSRT_NM'];by_gu[gu]+=v;by_year[year]+=v;by_subtype[typ+'|'+st]+=v;by_key[(gu,raw,year,typ,st)]+=v
    published=Counter()
    for gu,raw,year,typ,st,v in d['counts']:published[(gu,raw,year,typ,st)]+=v
    check('public annual cells equal verified source',published==by_key,len(published))
    for r in read(base/'01-16구군-5년합계와-한해제외순위.csv'):check('P district '+r['district'],by_gu[r['district']]==int(r['countP']))
    check('P total',sum(by_gu.values())==555786)
    check('70 subtypes',len(by_subtype)==70)
    check('194 names',len({(r[0],r[1]) for r in published})==194)
    for p in d['population']:check('population sum '+str(p['code'])+' '+str(p['year']),sum(p['ages'])==p['total'] and len(p['ages'])==101)
    check('population unique 205x5',len(d['population'])==len({(p['code'],p['year']) for p in d['population']})==1025)
    check('no private row identifiers in public payload',all(k not in (WEB/'data/current-data.js').read_text(encoding='utf-8') for k in ['DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']))
    t=defaultdict(Counter)
    for r in d['time']:t[(r['district'],r['rawDong'],r['subtype'])][r['dimension']]+=int(r['count'])
    for r in d['focus']:
        sums=t[(r['district'],r['rawDong'],r['subtype'])]
        check('four time margins '+r['rawDong']+r['subtype'],len(sums)==4 and all(v==int(r['countP']) for v in sums.values()))
    manifest=json.loads((AUDIT/'build-manifest.json').read_text(encoding='utf-8'))
    check('all publication input hashes',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['inputs'].items()))
    figures=data(WEB/'analysis/figures.js');check('current 9 plus remote 12 figures',len(figures['figures'])==9 and len(figures['remoteFigures'])==12)
    errors=[];screens=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True,args=['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1600,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:8766/',wait_until='networkidle',timeout=60000)
        check('latest develop cache headers','no-store' in page.request.get('http://127.0.0.1:8766/').headers.get('cache-control',''))
        page.wait_for_function('window.BUSAN_FIRE_STATIONS?.records===91')
        check('map initial P total',page.evaluate('BUSAN_CURRENT_STATE.total')==555786)
        check('map initial all16',page.locator('.region-row').count()==16)
        check('map polygon counts',page.evaluate('BUSAN_MAP_VIEW.getCounts()')==dict(by_gu))
        check('stations 91 records 68 locations',page.evaluate('BUSAN_FIRE_STATIONS')==dict(records=91,locations=68))
        for width,height in [(1920,1080),(1600,900),(1366,768)]:
            page.set_viewport_size({'width':width,'height':height});page.click('#filters-reset');page.wait_for_timeout(650)
            check(f'no page overflow {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight'))
            check(f'map larger than sidebar {width}',page.locator('#district-map').bounding_box()['width']>width*.65)
            path=OUT/f'map-first-{width}.png';page.screenshot(path=str(path));screens.append(str(path.relative_to(ROOT)))
            page.locator('.region-row').first.click();page.wait_for_timeout(650)
            check(f'selection count {width}',page.locator('#detail-total').get_attribute('data-count')=='64059')
            check(f'map selection {width}',page.evaluate('BUSAN_MAP_VIEW.getState().selected')=='부산진구')
            path=OUT/f'map-selected-{width}.png';page.screenshot(path=str(path));screens.append(str(path.relative_to(ROOT)))
        page.set_viewport_size({'width':1600,'height':900});page.click('#filters-reset')
        for year,count in sorted(by_year.items()):
            page.click(f'[data-year="{year}"]');check('year total '+str(year),page.evaluate('BUSAN_CURRENT_STATE.total')==count)
            check('year map/list '+str(year),page.evaluate('Object.values(BUSAN_MAP_VIEW.getCounts()).reduce((a,b)=>a+b,0)')==count)
        page.click('[data-year="all"]')
        for st,count in by_subtype.items():
            page.select_option('#type','all')
            page.select_option('#subtype',st);check('subtype '+st,page.evaluate('BUSAN_CURRENT_STATE.total')==count)
        page.select_option('#type','all')
        for scope,count in [('A',704689),('B',579412),('C',574662),('P',555786)]:
            page.select_option('#scope',scope);check('scope total '+scope,page.evaluate('BUSAN_CURRENT_STATE.total')==count)
            check('subtype support '+scope,page.locator('#subtype').is_disabled()==(scope!='P'))
        page.click('#filters-reset');page.locator('.region-row').first.click();page.locator('[data-child="부전동"]').click()
        check('gu to dong navigation',page.locator('#detail-title').inner_text()=='부전동')
        page.click('#detail-back');check('develop back function',page.locator('#detail-title').inner_text()=='부산진구')
        page.fill('#region-search','금곡');check('raw search',page.locator('.region-row').count()==1);page.locator('.region-row').click()
        page.select_option('#subtype','구급|질병');check('Geumgok disease count',page.locator('#detail-total').get_attribute('data-count')=='3615')
        page.click('[data-tab="time"]');check('Geumgok heatmap sum',page.locator('.heatmap .cell').evaluate_all('(els)=>els.reduce((s,e)=>s+Number(e.textContent.replaceAll(",","")),0)')==3615)
        page.screenshot(path=str(OUT/'map-time.png'))
        page.click('[data-year="2024"]');check('year-specific time count','543' in page.locator('#detail-content').inner_text())
        check('fixed period heatmap hidden on single year',page.locator('.heatmap').count()==0)
        page.click('[data-tab="population"]');pop=page.locator('#population-total').get_attribute('data-count');page.select_option('#type','화재');check('population independent of type',page.locator('#population-total').get_attribute('data-count')==pop)
        page.select_option('#type','구급');page.select_option('#subtype','구급|질병');page.click('[data-year="all"]');page.click('[data-tab="services"]')
        check('Geumgok conditional proposal','30일' in page.locator('#detail-content').inner_text() and '금곡' in page.locator('#detail-content').inner_text());page.screenshot(path=str(OUT/'map-proposal.png'))
        page.click('#filters-reset');page.fill('#region-search','부전');page.locator('.region-row').click();page.click('[data-tab="population"]')
        check('multiple population no sum',page.locator('#population-choice option').count()==3 and page.locator('#population-total').count()==0)
        page.select_option('#population-choice',index=1);check('population choice',page.locator('#population-total').count()==1);page.screenshot(path=str(OUT/'map-population.png'))
        page.fill('#region-search','존재하지않는지역');check('empty search',page.locator('.region-row').count()==0)
        a_keys={(r['district'],r['rawDong'],r['year']) for r in d['existing'] if r['scope']=='A'}
        missing=[(gu,raw,y) for gu,raw in {(r[0],r[1]) for r in published} for y in range(2020,2025) if (gu,raw,y) not in a_keys]
        for gu,raw,y in missing:
            page.evaluate('(s)=>BUSAN_CURRENT_ACTIONS.select(s)',dict(kind='raw',district=gu,rawDong=raw));page.click(f'[data-year="{y}"]')
            check('missing year not zero '+str((gu,raw,y)),'해당 연도 자료 없음' in page.locator('#detail-content').inner_text() and page.locator('#detail-total').count()==0)
        page.click('#filters-reset');page.evaluate('BUSAN_MAP_VIEW.select("중구")');check('map click updates detail',page.locator('#detail-title').inner_text()=='중구')
        check('map click updates list',page.locator('.region-row.active').get_attribute('data-district')=='중구')
        page.click('#detail-close');check('close detail',page.locator('#right-panel').is_hidden())
        check('latest develop compact map controls',page.locator('[data-mode]').count()==0 and page.locator('[data-theme]').count()==2)
        check('latest develop left year controls',page.locator('#left-panel [data-year]').count()==6)
        page.click('#filters-reset');page.wait_for_timeout(650);check('reset camera',page.evaluate('BUSAN_MAP_VIEW.getState().mode')=='2d')
        z=page.evaluate('BUSAN_MAP_VIEW.getState().zoom');page.click('#map-zoom-in');page.wait_for_timeout(550);check('zoom control',page.evaluate('BUSAN_MAP_VIEW.getState().zoom')>z)
        page.evaluate('BUSAN_MAP_VIEW.select("부산진구")');page.wait_for_timeout(650)
        check('compact symbols enlarge on selected district',page.locator('.fire-station-marker.compact').count()==0)
        # Click a station within viewport, verify latest popup wording and hide behavior.
        visible=page.locator('.fire-station-marker').evaluate_all('(els)=>els.findIndex(e=>{const r=e.getBoundingClientRect();return r.x>500&&r.x<1000&&r.y>200&&r.y<700})')
        check('station visible in selected area',visible>=0);page.locator('.fire-station-marker').nth(visible).click();check('station resource popup','자료상 인원' in page.locator('.fire-station-popup').inner_text())
        page.locator('.fire-station-toggle').click();check('station toggle clears popup',page.locator('.fire-station-popup').count()==0)
        page.goto('http://127.0.0.1:8766/analysis/',wait_until='networkidle')
        check('report all16 rows',page.locator('#district-table tbody tr').count()==16)
        check('report top row',page.locator('#district-table tbody tr').first.inner_text().find('64,059')>=0)
        check('report main gallery 9',page.locator('#figure-gallery img').count()==9)
        page.screenshot(path=str(OUT/'analysis-first.png'))
        page.click('[data-gallery="remote"]');check('report remote gallery 12',page.locator('#figure-gallery img').count()==12)
        page.locator('#remote').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'analysis-remote.png'))
        page.click('[data-gallery="current"]');page.locator('#proposals').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'analysis-proposals.png'))
        check('all figure files exist',all((WEB/'analysis'/r['file']).exists() for r in figures['figures']+figures['remoteFigures']))
        for path in ['../?district=북구&dong=금곡동&subtype=질병','downloads/전체결과보고서.md']:
            check('linked endpoint '+path,page.request.get('http://127.0.0.1:8766/analysis/'+path).status==200)
        for pdf in (WEB/'analysis/downloads').glob('*.pdf'):
            response=page.request.get('http://127.0.0.1:8766/analysis/downloads/'+pdf.name)
            check('develop PDF download '+pdf.name,response.status==200 and response.body()==pdf.read_bytes())
        check('no JS runtime errors',not errors,errors)
        # Offline basemap still leaves local map and values available; no fake loaded status.
        offline=browser.new_page(viewport={'width':1366,'height':768})
        offline.route('**/*',lambda route:route.continue_() if route.request.url.startswith('http://127.0.0.1:8766/') or route.request.url.startswith('blob:') else route.abort())
        offline.goto('http://127.0.0.1:8766/',wait_until='networkidle');offline.wait_for_timeout(1000)
        check('network failure keeps local totals',offline.evaluate('BUSAN_CURRENT_STATE.total')==555786)
        check('network failure status visible',offline.locator('#tile-status').is_visible())
        offline.screenshot(path=str(OUT/'map-network-unavailable.png'));browser.close()
    result=dict(status='PASS',checks=checks,screenshots=screens,scope='CSV independent reconciliation and actual PC Chromium; not public deployment or policy effect validation')
    (AUDIT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'PASS','checks':len(checks),'screenshots':len(screens),'JS_errors':errors},ensure_ascii=False))

if __name__=='__main__':main()
