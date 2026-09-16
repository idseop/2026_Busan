"""Capture the served final map with real controls; no synthetic map content."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[1]
O=R/'data/processed/지도입증확장-20260916/delivery-screens'
O.mkdir(exist_ok=True)
errors=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':900},device_scale_factor=1)
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
    page.wait_for_function('window.BUSAN_MAP_VIEW?.getState?.().heightFootprints === 1081 && window.BUSAN_MAP_VIEW?.getState?.().contextReady')
    page.wait_for_timeout(2500)
    page.screenshot(path=str(O/'01-busan-pc.png'))
    cases=page.evaluate('window.BUSAN_FINAL_CASES.cases')
    case=next(x for x in cases if x['rawDong']=='연산동' and x['subtype']=='심정지')
    page.locator('[data-deep-shortcut="'+case['id']+'"]').click()
    page.locator('[data-evidence-expand]').click()
    page.locator('[data-evidence-step="1"]').click()
    page.wait_for_timeout(800)
    page.screenshot(path=str(O/'02-report-step.png'))
    page.locator('[data-evidence-step="2"]').click()
    page.locator('[data-evidence-focus]').click()
    page.locator('[data-mode="3d"]').click()
    page.wait_for_timeout(1800)
    page.screenshot(path=str(O/'03-background-pin-3d.png'))
    focus=page.evaluate('window.BUSAN_MAP_VIEW.getState().focusPin')
    for step,name in [(3,'04-existing-response'),(4,'05-support-result')]:
        page.locator(f'[data-evidence-step="{step}"]').click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(O/(name+'.png')))
    browser.close()
(O/'capture.json').write_text(json.dumps({'status':'PASS' if not errors else 'FAIL','viewport':[1600,900],
    'errors':errors,'backgroundFocus':focus,'screens':sorted(x.name for x in O.glob('*.png'))},ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'errors':errors,'focus':focus},ensure_ascii=False))
