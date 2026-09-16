"""Independently check the revised map and local temporal views in Chrome."""
from pathlib import Path
from collections import defaultdict
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import hashlib
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'web/final'
OUT=ROOT/'data/processed/심층분석-20260915/browser_verification'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=json.loads((SITE/'data/dashboard.json').read_text(encoding='utf-8'))
    deep=json.loads((SITE/'data/deep-data.json').read_text(encoding='utf-8'))
    totals=defaultdict(int);local=defaultdict(int);heat=defaultdict(lambda:[0]*42)
    for row in d['rawRegions']:
        for y in [str(row['year']),'all']:
            for typ,count in [('all',row['total']),*row['typeCounts'].items()]:
                totals[(y,row['scope'],typ,row['district'])]+=count
                local[(y,row['scope'],typ,row['district'],row['rawDong'])]+=count
    for r,y,s,t,w,h,count in deep['dayHour']:
        region=deep['regions'][r]
        for yy in [str(y),'all']:
            for tt in [deep['meta']['types'][t],'all']:
                heat[(yy,deep['meta']['scopes'][s],tt,region['district'],region['rawDong'])][w*6+h]+=count
    checks=[];local_checks=[];errors=[];failed=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1600,'height':1100},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('requestfailed',lambda r:failed.append(r.url))
        page.goto((SITE/'index.html').as_uri(),wait_until='load')
        page.add_style_tag(content='html{scroll-behavior:auto!important}*{transition:none!important}')
        assert page.locator('.map-symbol').count()==16

        def check_local():
            if page.locator('#region-analysis').is_hidden():return
            data=page.locator('#local-metrics').evaluate('(e)=>({...e.dataset})')
            key=tuple(data[k] for k in ['year','scope','type','district','rawDong'])
            assert int(data['total'])==local[key],(key,data,local[key])
            cells=page.locator('#local-heatmap .heat-cell').evaluate_all('es=>es.map(e=>Number(e.dataset.count))')
            assert cells==heat[key],(key,sum(cells),sum(heat[key]))
            assert sum(cells)==int(data['total'])
            local_checks.append({'key':key,'count':sum(cells),'cells':42})

        for year in ['all','2020','2021','2022','2023','2024']:
            page.select_option('#year',year)
            for scope in ['A','B','C']:
                page.select_option('#scope',scope)
                for typ in ['all',*d['meta']['types']]:
                    page.select_option('#type',typ)
                    values=page.locator('.map-symbol').evaluate_all('es=>es.map(e=>({district:e.dataset.district,count:Number(e.dataset.count)}))')
                    assert len(values)==16
                    for v in values:assert v['count']==totals[(year,scope,typ,v['district'])],(year,scope,typ,v)
                    assert sum(v['count'] for v in values)==int(page.locator('#metric-total').inner_text().replace(',',''))
                    check_local();checks.append({'year':year,'scope':scope,'type':typ,'districts':16,'total':sum(v['count'] for v in values)})
        page.select_option('#year','all');page.select_option('#scope','C');page.select_option('#type','all')
        for district in sorted({r['district'] for r in d['rawRegions']}):
            target=page.locator(f'.map-place-label[data-district="{district}"]')
            target.focus();target.press('Enter')
            assert page.locator('#district').input_value()==district
            check_local()
        for case in deep['cases']:
            page.select_option('#district',case['district'])
            opts=page.locator('#raw-dong option').evaluate_all('es=>es.map(e=>({value:e.value,text:e.textContent}))')
            raw=next(x['value'] for x in opts if case['rawDong'] in x['text'])
            page.select_option('#raw-dong',raw)
            page.select_option('#type',case['type'])
            check_local()
            assert case['subtype'] in page.locator('#local-cases').inner_text()
            assert page.locator('#local-cases .case-service').count()>0
            page.select_option('#type','all')
        page.locator('#region-search').fill('ZZZZ_NO_MATCH')
        assert page.locator('#region-analysis').is_hidden()
        assert '없' in page.locator('#region-detail').inner_text()
        page.locator('#region-search').fill('')
        initial=page.locator('#map-camera').get_attribute('transform')
        page.locator('#map-zoom-in').click();assert page.locator('#map-camera').get_attribute('transform')!=initial
        page.locator('#map-reset').click()
        assert 'scale(1)' in page.locator('#map-camera').get_attribute('transform')
        page.select_option('#district','all');page.select_option('#year','all');page.select_option('#scope','A');page.select_option('#type','all')
        page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/'desktop-overview.png'))
        page.locator('#regions').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'desktop-map.png'))
        boxes=page.locator('.map-place-label').evaluate_all('es=>es.map(e=>{let b=e.getBoundingClientRect();return {name:e.dataset.district,x:b.x,y:b.y,w:b.width,h:b.height}})')
        overlaps=[]
        for i,a in enumerate(boxes):
            for b in boxes[i+1:]:
                if min(a['x']+a['w'],b['x']+b['w'])>max(a['x'],b['x']) and min(a['y']+a['h'],b['y']+b['h'])>max(a['y'],b['y']):overlaps.append([a['name'],b['name']])
        assert not overlaps,overlaps
        page.select_option('#district','기장군');page.select_option('#scope','C');page.select_option('#type','구급')
        raw=next(o.get_attribute('value') for o in page.locator('#raw-dong option').all() if '기장읍' in o.inner_text())
        page.select_option('#raw-dong',raw);page.locator('#region-analysis').scroll_into_view_if_needed()
        page.screenshot(path=str(OUT/'desktop-local.png'));page.screenshot(path=str(OUT/'desktop-full.png'),full_page=True)
        for width in [390,360]:
            page.set_viewport_size({'width':width,'height':844});page.evaluate('dispatchEvent(new Event("resize"))')
            page.locator('#map-reset').click();page.locator('#district-map').scroll_into_view_if_needed()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),width
            page.screenshot(path=str(OUT/f'mobile-map-{width}.png'))
            page.locator('#region-analysis').scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'mobile-local-{width}.png'))
        assert not errors,errors;assert not failed,failed
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(SITE)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
            assert page.locator('.map-symbol').count()==16
            check_local()
        finally:server.shutdown();server.server_close()
        assert not errors and not failed
        browser.close()
    evidence={'status':'passed','map_filter_combinations':checks,'local_heatmap_checks':local_checks,'desktop_label_overlaps':overlaps,'file_and_http':True,'mobile_widths':[360,390],'page_errors':errors,'failed_requests':failed,'site_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file()}}
    (OUT/'result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS {len(checks)} map filters x16 districts; {len(local_checks)} local heatmaps x42 cells')

if __name__=='__main__':main()
