import argparse
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--browser',required=True)
args=parser.parse_args()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.browser,headless=True)
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
    page.wait_for_function('window.BUSAN_FIRE_STATIONS?.locations===68')
    page.wait_for_timeout(2000)
    assert page.locator('.fire-station-marker').count()==68
    page.locator('.fire-station-marker').first.click()
    page.wait_for_selector('.fire-station-popup')
    assert '부산소방재난본부' in page.locator('.fire-station-popup').inner_text()
    assert page.locator('#right-panel').is_hidden()
    page.screenshot(path='outputs/fire-stations.png')
    page.locator('.fire-station-toggle').click()
    assert page.locator('.fire-station-toggle').get_attribute('aria-pressed')=='false'
    assert page.locator('.fire-station-marker:visible').count()==0
    page.locator('.fire-station-toggle').click()
    assert page.locator('.fire-station-toggle').get_attribute('aria-pressed')=='true'
    assert page.locator('.fire-station-marker:visible').count()==68
    page.locator('[data-year="2021"]').click()
    assert page.locator('.fire-station-marker').count()==68
    assert not errors,errors
    print('PASS: 91 stations / 68 markers, popup, no district click, hide/show, year change; page errors 0')
    browser.close()
