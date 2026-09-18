"""Small, manual-equivalent official map reference capture (no map sweeps)."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/public-map-reference-20260916'
OUT.mkdir(parents=True, exist_ok=True)
SITES = [
    ('busan-data-map', 'https://data.busan.go.kr/bdip/opendata/mapBasedData.do'),
    ('safemap', 'https://www.safemap.go.kr/main/smap_renewal.do'),
    ('floodmap', 'https://www.floodmap.go.kr/combine'),
    ('safekorea', 'https://safekorea.go.kr/safekorea-kor/main/main.do'),
]
results = []
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=False)
    context = browser.new_context(viewport={'width':1600,'height':1000})
    for slug, url in SITES:
        page = context.new_page()
        result = {'name':slug, 'url':url, 'access_date':'2026-09-16', 'mode':'one headed initial viewport; no map pan, zoom, or tile sweep'}
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=25000)
            page.wait_for_timeout(2500)
            result.update(status=response.status if response else None, title=page.title(), final_url=page.url)
            page.screenshot(path=str(OUT / (slug + '.png')))
            (OUT / (slug + '.txt')).write_text(page.locator('body').inner_text(), encoding='utf-8')
        except Exception as error:
            result['error'] = str(error)
            try: page.screenshot(path=str(OUT / (slug + '.png')))
            except Exception: pass
        results.append(result)
        page.close()
    browser.close()
(OUT/'capture.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
