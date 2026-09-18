"""Exercise district -> neighbourhood -> back with filters and scroll retained."""
from playwright.sync_api import sync_playwright
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--browser',required=True)
args=parser.parse_args()
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=args.browser,headless=True)
    page=browser.new_page(viewport={'width':1366,'height':900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
    page.wait_for_selector('#region-list .region-row')
    page.locator('[data-year="2021"]').click()
    page.select_option('#scope','C')
    page.locator('#region-list [data-district="부산진구"]').click()
    link=page.locator('#overview-links [data-raw]').first
    link.scroll_into_view_if_needed()
    scroll=page.locator('#detail-content').evaluate('(e)=>e.scrollTop')
    name=link.get_attribute('data-raw')
    link.click()
    assert page.locator('#detail-title').inner_text()==name
    assert page.locator('#detail-back').is_visible()
    page.locator('#detail-back').click()
    page.wait_for_timeout(200)
    assert page.locator('#detail-title').inner_text()=='부산진구'
    assert page.locator('#year').input_value()=='2021'
    assert page.locator('#scope').input_value()=='C'
    assert abs(page.locator('#detail-content').evaluate('(e)=>e.scrollTop')-scroll)<3
    assert not page.locator('#detail-back').is_visible()
    page.locator('#overview-links [data-raw]').first.click()
    page.locator('#detail-close').click()
    page.locator('#region-list .region-row').first.click()
    assert not page.locator('#detail-back').is_visible()
    assert not errors,errors
    print('PASS: district/dong/back, year/scope, scroll restoration, close resets history; no page errors')
    browser.close()
