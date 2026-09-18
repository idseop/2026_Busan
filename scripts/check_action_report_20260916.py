from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/예방지원-근거분석-20260916/verification'
errors=[];checks=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    for w,h in [(1920,1080),(1600,900),(1366,768)]:
        page.set_viewport_size({'width':w,'height':h})
        page.goto('http://127.0.0.1:8765/results/',wait_until='networkidle')
        assert page.locator('article').count()==10
        assert page.locator('figure img').count()==6
        assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(OUT/f'report-{w}.png'))
        checks.append({'viewport':[w,h],'caseCount':10,'figures':6,'imagesLoaded':True,'horizontalOverflow':False})
    page.locator('#action-3').evaluate('(e)=>e.scrollIntoView({block:"start"})')
    page.screenshot(path=str(OUT/'report-case.png'))
    page.goto((ROOT/'output/부산119-예방지원-분석결과-20260916/index.html').as_uri(),wait_until='load')
    assert page.locator('article').count()==10
    assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
    checks.append({'fileDirect':True,'imagesLoaded':True})
    page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
    page.locator('a[href="results/index.html"]').click()
    page.wait_for_url('**/results/index.html')
    assert page.locator('article').count()==10
    checks.append({'mapToReportNavigation':True})
    browser.close()
assert not errors,errors
(OUT/'report-browser.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'errors':errors}))
