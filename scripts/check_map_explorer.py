"""Browser acceptance checks for the full-height Busan map explorer."""
from pathlib import Path
from collections import defaultdict
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
import hashlib
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915/browser'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    d=json.loads((SITE/'data/dashboard.json').read_text(encoding='utf-8'))
    deep=json.loads((SITE/'data/deep-data.json').read_text(encoding='utf-8'))
    counts=defaultdict(int);heats=defaultdict(lambda:[0]*42)
    for row in d['rawRegions']:
        for yy in ['all',str(row['year'])]:
            for typ,n in [('all',row['total']),*row['typeCounts'].items()]:
                for raw in ['*',row['rawDong']]:counts[(yy,row['scope'],typ,row['district'],raw)]+=n
    for ri,y,si,ti,w,h,n in deep['dayHour']:
        r=deep['regions'][ri]
        for yy in ['all',str(y)]:
            for typ in ['all',deep['meta']['types'][ti]]:
                for raw in ['*',r['rawDong']]:heats[(yy,deep['meta']['scopes'][si],typ,r['district'],raw)][w*6+h]+=n
    checks=[];local_checks=[];errors=[];failed=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        p=b.new_page(viewport={'width':1600,'height':1000},device_scale_factor=1)
        p.on('pageerror',lambda e:errors.append(str(e)));p.on('requestfailed',lambda r:failed.append(r.url))
        p.goto((SITE/'index.html').as_uri(),wait_until='load')
        p.add_style_tag(content='*{transition:none!important;scroll-behavior:auto!important}')
        assert p.locator('#right-panel').is_hidden(),'Initial detail must be closed'
        rect=p.locator('#map-viewport').bounding_box();left=p.locator('#left-panel').bounding_box()
        assert rect['width']>left['width']*2 and rect['height']>=900,(rect,left)
        assert p.evaluate('document.documentElement.scrollHeight<=innerHeight+1')
        p.screenshot(path=str(OUT/'desktop-initial.png'))

        def choose_district(name):
            target=p.locator(f'#district-map [data-district="{name}"][tabindex="0"]').first
            target.focus();target.press('Enter')

        def detail_check():
            ds=p.locator('#detail-content').evaluate('(e)=>({...e.dataset})')
            raw=ds.get('rawDong') if ds['kind']=='raw' else '*'
            key=(ds['year'],ds['scope'],ds['type'],ds['district'],raw)
            assert int(ds['total'])==counts[key],(ds,counts[key])
            local_checks.append({'kind':ds['kind'],'key':key,'count':int(ds['total'])})
            return key

        choose_district('기장군');assert p.locator('#right-panel').is_visible();detail_check()
        assert p.locator('#detail-content').get_attribute('data-kind')=='district'
        for yy in ['all','2020','2021','2022','2023','2024']:
            p.select_option('#year',yy,force=True)
            for scope in ['A','B','C']:
                p.select_option('#scope',scope)
                for typ in ['all',*d['meta']['types']]:
                    p.select_option('#type',typ)
                    values=p.locator('.map-region').evaluate_all('es=>es.map(e=>({district:e.dataset.district,count:Number(e.dataset.count)}))')
                    assert len(values)==16,len(values)
                    for v in values:assert v['count']==counts[(yy,scope,typ,v['district'],'*')],(yy,scope,typ,v)
                    detail_check();checks.append({'year':yy,'scope':scope,'type':typ,'districts':16})
        p.select_option('#year','all',force=True);p.select_option('#scope','A');p.select_option('#type','all')
        for district in sorted({r['district'] for r in d['rawRegions']}):choose_district(district);detail_check()
        p.select_option('#district','all');p.locator('#list-raw').click();p.locator('#region-search').fill('기장읍')
        p.locator('#region-list [data-key]').first.click();key=detail_check();assert key[-1]=='기장읍'
        assert p.locator('#detail-content').get_attribute('data-kind')=='raw'
        p.locator('#detail-tabs [data-tab="time"]').click()
        cells=p.locator('#detail-content .heat-cell').evaluate_all('es=>es.map(e=>Number(e.dataset.count))')
        assert cells==heats[key],(len(cells),sum(cells),sum(heats[key]))
        p.locator('#detail-tabs [data-tab="population"]').click()
        assert '51,101' in p.locator('#detail-content').inner_text()
        p.locator('#detail-tabs [data-tab="overview"]').click()
        rect=p.locator('#map-viewport').bounding_box();right=p.locator('#right-panel').bounding_box()
        assert rect['width']>right['width'] and rect['height']>=900,(rect,right)
        p.screenshot(path=str(OUT/'desktop-selected.png'))
        p.locator('#detail-close').click();assert p.locator('#right-panel').is_hidden()
        p.locator('#region-search').fill('ZZZZ_NO_RESULTS');assert p.locator('#region-list [data-key]').count()==0
        p.locator('#region-search').fill('');p.select_option('#sort','count')
        rows=p.locator('#region-list [data-key]').evaluate_all('es=>es.map(e=>Number(e.dataset.count))')
        assert rows==sorted(rows,reverse=True)
        p.locator('#map-reset').click()
        initial=p.locator('#map-camera').get_attribute('transform')
        p.locator('#map-zoom-in').click();assert p.locator('#map-camera').get_attribute('transform')!=initial
        p.locator('#map-reset').click()
        map_rect=p.locator('#map-viewport').bounding_box();x=map_rect['x']+map_rect['width']*.4;y=map_rect['y']+map_rect['height']*.8
        before=p.locator('#map-camera').get_attribute('transform')
        p.mouse.move(x,y);p.mouse.down();p.mouse.move(x+80,y-40,steps=8);p.mouse.up()
        assert p.locator('#map-camera').get_attribute('transform')!=before,'Drag pan failed'
        before=p.locator('#map-camera').get_attribute('transform');p.mouse.wheel(0,-200);p.wait_for_timeout(100)
        assert p.locator('#map-camera').get_attribute('transform')!=before,'Wheel zoom failed'
        p.locator('#map-reset').click()
        for width in [390,360]:
            p.set_viewport_size({'width':width,'height':844});p.wait_for_timeout(100)
            assert p.evaluate('document.documentElement.scrollHeight<=innerHeight+1 && document.documentElement.scrollWidth<=innerWidth+1')
            p.screenshot(path=str(OUT/f'mobile-initial-{width}.png'))
            p.locator('#left-toggle').click()
            assert p.locator('#left-panel').bounding_box()['x']>=0
            p.locator('#filters-reset').click();p.locator('#list-raw').click();p.locator('#region-search').fill('기장읍')
            p.screenshot(path=str(OUT/f'mobile-search-{width}.png'))
            p.locator('#region-list [data-key]').first.click()
            assert p.locator('#right-panel').is_visible();detail_check()
            assert p.locator('#map-viewport').is_visible()
            p.screenshot(path=str(OUT/f'mobile-selected-{width}.png'))
            before=p.locator('#right-panel').bounding_box()['height']
            p.locator('#sheet-toggle').click()
            assert p.locator('#right-panel').bounding_box()['height']>before
            p.locator('#detail-close').click();assert p.locator('#right-panel').is_hidden()
            p.locator('#map-reset').click()
        assert not errors,errors;assert not failed,failed
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*_):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(SITE)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='load')
            assert p.locator('.map-region').count()==16
        finally:server.shutdown();server.server_close()
        assert not errors and not failed;b.close()
    result={'status':'passed','map_filter_checks':checks,'detail_checks':local_checks,'fullscreen_desktop':True,'drag_pan':True,'wheel_zoom':True,'empty_search':True,'count_sort':True,'file_and_http':True,'mobile_widths':[390,360],'errors':errors,'failed_requests':failed,'site_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file()}}
    (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(checks)} map filter combinations, {len(local_checks)} detail states')

if __name__=='__main__':main()
