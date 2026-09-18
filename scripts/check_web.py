"""로컬 부산 지도 브라우저 기능 검증. 원시 데이터 서버는 열지 않는다."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/interim/웹화면검증'
OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1100}, device_scale_factor=1)
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto('http://127.0.0.1:8765/', wait_until='networkidle')
    page.wait_for_function("document.getElementById('load-status').hidden",timeout=30000)
    assert page.locator('path.district').count() == 16
    assert page.locator('#district-table tr').count() == 16
    assert '272,271건' in page.locator('#stats').inner_text()
    page.locator('#reportType').select_option('구급')
    assert '191,055건' in page.locator('#stats').inner_text()
    assert '87건' in page.locator('#stats').inner_text()
    page.locator('#reportType').select_option('미기재')
    assert '780건' in page.locator('#stats').inner_text()
    page.locator('#metric').select_option('population')
    assert page.locator('#reportType').is_disabled()
    assert '3,266,598명' in page.locator('.detail-main').inner_text()
    page.locator('#metric').select_option('reports')
    page.locator('#reportType').select_option('전체')
    page.locator('#condition').select_option('C')
    assert '210,109건' in page.locator('#stats').inner_text()
    page.locator('path[data-name="연제구"]').focus()
    page.keyboard.press('Enter')
    assert page.locator('#detail-title').inner_text() == '연제구'
    assert '12,610건' in page.locator('.detail-main').inner_text()
    page.locator('#year').select_option('2018')
    assert '200,309건' in page.locator('#stats').inner_text()
    page.locator('#metric').select_option('age65share')
    assert page.locator('#condition').is_disabled()
    assert '17.14%' in page.locator('#stats').inner_text()
    assert page.locator('.age-row').count() == 11
    page.locator('#reset').click()
    assert page.locator('#detail-title').inner_text() == '부산광역시'
    page.locator('#year').select_option('2024')
    page.locator('#metric').select_option('reports')
    page.locator('#condition').select_option('A')
    page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.locator('#district-table button[data-select="중구"]').click()
    assert page.locator('#detail-title').inner_text() == '중구'
    page.locator('#zoom-in').click()
    assert '1.3' in page.locator('#map-group').get_attribute('transform')
    page.locator('#zoom-reset').click()
    assert 'scale(1)' in page.locator('#map-group').get_attribute('transform')
    assert not errors, errors
    (OUT/'result.json').write_text(json.dumps({'passed':True,'districts':16,'ageBands':11,'tested':['2024 A/C counts','keyboard district selection','2018 C count','65+ metric','mobile table selection','zoom/reset','no viewport overflow','no page errors'],'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    browser.close()
print('부산 웹 지도 브라우저 검사 통과')
