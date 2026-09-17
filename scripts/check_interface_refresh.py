"""지도 UI 개편 후 필터·지역 상세·모바일 동작과 화면 배치를 확인한다."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--browser',required=True)
parser.add_argument('--url',default='http://127.0.0.1:8765/')
args=parser.parse_args()
out=Path(__file__).resolve().parents[1]/'outputs/ui-refresh'
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=args.browser,headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000})
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(args.url,wait_until='networkidle')
 page.wait_for_selector('.region-row')
 assert '704,689' in page.locator('#map-total').inner_text()
 assert page.locator('.case-disclosure').count()==1
 assert page.locator('.region-row').first.bounding_box()['y']<900
 page.screenshot(path=str(out/'01-desktop.png'))
 page.locator('[data-year="2021"]').click()
 page.wait_for_function("document.querySelector('#map-total').innerText.includes('139,189')")
 page.locator('.region-row').filter(has_text='부산진구').first.click()
 assert '15,560' in page.locator('.region-summary-heading').inner_text()
 for tab in ['time','population','services','overview']:
  page.locator(f'#detail-tabs [data-tab="{tab}"]').click()
  assert page.locator(f'#detail-tabs [data-tab="{tab}"]').get_attribute('aria-selected')=='true'
  assert page.locator('#detail-content').inner_text().strip()
 page.screenshot(path=str(out/'02-detail.png'))
 page.locator('[data-raw="부전동"]').first.click()
 assert '부전동' in page.locator('#detail-title').inner_text()
 page.locator('.detail-back').click()
 assert '부산진구' in page.locator('#detail-title').inner_text()
 page.locator('#detail-close').click()
 page.locator('#filters-reset').click()
 page.locator('#scope').select_option(label='업무성 기록 제외')
 page.wait_for_function("document.querySelector('#map-total').innerText.includes('574,662')")
 page.locator('#type').select_option(label='구급')
 page.wait_for_function("document.querySelector('#map-total').innerText.includes('474,392')")
 page.locator('.scene-row button').filter(has_text='접수 비중').click()
 assert page.locator('.scene-row button').filter(has_text='접수 비중').get_attribute('aria-pressed')=='true'
 page.locator('.scene-row button').filter(has_text='일반지도').click()
 page.locator('#filters-reset').click()
 page.locator('#region-search').fill('검색결과없음테스트')
 assert page.locator('.region-row').count()==0
 page.locator('#search-clear').click()
 page.locator('#list-districts').click()
 assert page.locator('.region-row').count()==16
 page.locator('.case-disclosure>summary').click()
 assert page.locator('.deep-shortcuts button').first.is_visible()
 page.locator('.case-disclosure>summary').click()
 page.locator('.fire-station-toggle').click()
 assert page.locator('.fire-station-marker:visible').count()==0
 page.locator('.fire-station-toggle').click()
 assert page.locator('.fire-station-marker:visible').count()==68
 page.locator('#about-open').click()
 assert page.locator('#about-dialog').is_visible()
 page.locator('#about-close').click()
 for width,height in [(1366,768),(1024,768),(390,844)]:
  page.set_viewport_size({'width':width,'height':height})
  page.reload(wait_until='networkidle')
  page.wait_for_timeout(600)
  assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),width
  if width>800:
   footer=page.locator('.left-footer').bounding_box()
   assert footer['y']+footer['height']<=height,(width,footer)
  else:
   page.locator('#left-toggle').click()
   page.wait_for_function("document.querySelector('#left-panel').getBoundingClientRect().x>=0")
   page.wait_for_timeout(250)
   page.screenshot(path=str(out/'04-mobile-filters.png'))
   page.locator('#left-close').click()
   page.wait_for_timeout(250)
  page.screenshot(path=str(out/f'03-layout-{width}.png'))
 page.locator('#left-toggle').click()
 page.locator('.region-row').first.click()
 page.wait_for_timeout(600)
 page.screenshot(path=str(out/'05-mobile-detail.png'))
 assert page.locator('#right-panel').is_visible()
 assert not errors,errors
 print(json.dumps({'status':'통과','viewports':[1440,1366,1024,390],'year_count':139189,'checks':['연도 동기화','상세 탭','지역 뒤로가기','검색 결과 없음','사례 접기','소방관서 표시','출처','모바일'],'page_errors':errors},ensure_ascii=False))
 browser.close()
