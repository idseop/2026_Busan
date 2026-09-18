"""One headed viewport review; never prefetch or sweep OSM tiles."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/processed/지도탐색웹-20260915/result-map/live'
OUT.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=False)
    page=browser.new_page(viewport={'width':1600,'height':1000})
    requests=[];errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append({'url':r.url,'referer':r.headers.get('referer')}) if 'tiles.openfreemap.org' in r.url else None)
    page.goto('http://127.0.0.1:8765/',wait_until='load')
    try:page.wait_for_function('window.BUSAN_MAP_VIEW?.getState().contextReady',timeout=25000)
    except Exception:pass
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT/'desktop-initial.png'))
    state=page.evaluate('BUSAN_MAP_VIEW.getState()')
    for width,height in [(1920,1080),(1600,900),(1366,768)]:
        page.set_viewport_size({'width':width,'height':height});page.locator('#map-reset').click();page.wait_for_timeout(800)
        page.screenshot(path=str(OUT/f'desktop-{width}.png'))
    page.set_viewport_size({'width':1600,'height':1000});page.locator('#filters-reset').click();page.wait_for_timeout(500)
    page.locator('#analysis-open').click();page.screenshot(path=str(OUT/'analysis-results.png'));page.locator('#analysis-close').click()
    page.locator('#region-search').fill('기장읍');page.locator('#region-list [data-key]').first.click();page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT/'desktop-selected.png'))
    page.locator('.case-conclusion').first.scroll_into_view_if_needed();page.screenshot(path=str(OUT/'case-evidence.png'))
    page.locator('[data-tab="services"]').click();page.screenshot(path=str(OUT/'service-results.png'))
    (OUT/'live-verification.json').write_text(json.dumps({'state':state,'selectedState':page.evaluate('BUSAN_MAP_VIEW.getState()'),'requests':requests,'errors':errors,'mode':'Headed PC 1920/1600/1366, contextual OpenFreeMap vector background; initial and selected case result. No tile archive.'},ensure_ascii=False,indent=2),encoding='utf-8')
    browser.close()
print(json.dumps({'state':state,'errors':errors},ensure_ascii=False))
