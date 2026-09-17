"""Browser checks for curated results, evidence navigation and supplementary figures."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];root=R/'web/final/results/complete';out=R/'outputs/ui-refresh';out.mkdir(exist_ok=True,parents=True)
parser=argparse.ArgumentParser()
parser.add_argument('--browser',help='Optional Chromium executable; defaults to Playwright installed Chromium')
args=parser.parse_args()
data=json.loads((root/'content-inventory.json').read_text(encoding='utf-8'))
assert len(data['figures'])==60 and sum(x['core'] for x in data['figures'])==18
for x in data['figures']:
 for ext in ['png','svg']:assert (root/x[ext]).is_file(),x
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=args.browser,headless=True)
 page=b.new_page(viewport={'width':1440,'height':1000});errors=[];failed=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:failed.append(r.url) if r.status>=400 and '127.0.0.1' in r.url else None)
 page.goto('http://127.0.0.1:8765/',wait_until='networkidle')
 page.get_by_role('tab',name='최종 결과',exact=True).click()
 f=page.frame_locator('.workspace-frame');f.locator('.policy-card').first.wait_for()
 page.wait_for_function("document.querySelector('.workspace-frame').style.visibility==='visible'")
 assert f.locator('.policy-card').count()==9
 assert f.locator('.proposal-card').count()==3
 f.locator('.reading-nav a[href="#policy"]').click()
 page.wait_for_timeout(650)
 assert '시행 확정 아님' in f.locator('#policy').inner_text()
 assert '노인 일자리' in f.locator('#proposal-2').inner_text()
 f.locator('#proposal-2 summary').click()
 assert f.locator('#proposal-2 details').get_attribute('open') is not None
 page.screenshot(path=str(out/'17-policy-proposals.png'))
 f.locator('.result-intro').evaluate('(e)=>e.scrollIntoView()')
 assert '65,302' in f.locator('#districts').inner_text() and '14,650' in f.locator('#districts').inner_text()
 page.screenshot(path=str(out/'12-results-content.png'))
 f.locator('.reading-nav a[href="#districts"]').click();page.wait_for_timeout(650)
 page.screenshot(path=str(out/'13-district-results.png'))
 f.locator('.policy-card summary').first.click()
 assert f.locator('.policy-card details').first.get_attribute('open') is not None
 page.get_by_role('tab',name='그림 모음',exact=True).click()
 f.locator('#library-count').wait_for()
 assert f.locator('.visual:visible').count()==18
 f.locator('[data-mode="all"]').click();assert f.locator('.visual:visible').count()==60
 f.locator('button[data-topic="부산진구·중구"]').click();assert f.locator('.visual:visible').count()==12
 f.locator('#figure-search').fill('없는검색어');assert f.locator('#library-empty').is_visible()
 f.locator('#figure-search').fill('고령');assert f.locator('.visual:visible').count()>0
 f.locator('#figure-search').fill('');f.locator('[data-mode="core"]').click()
 assert f.locator('.visual:visible').count()==6
 page.screenshot(path=str(out/'14-gallery-content.png'))
 f.locator('.visual:visible [data-image]').first.click();assert f.locator('#image-dialog').is_visible();f.locator('#close-image').click()
 page.get_by_role('tab',name='최종 결과',exact=True).click();f.locator('#districts').wait_for()
 f.locator('#proposal-2 a[href="gallery.html#district-09"]').click();f.locator('#district-09').wait_for()
 assert page.get_by_role('tab',name='그림 모음',exact=True).get_attribute('aria-selected')=='true'
 assert f.locator('#district-09').is_visible()
 for width in [390,768]:
  page.set_viewport_size({'width':width,'height':844})
  page.wait_for_timeout(400)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  assert f.locator('html').evaluate('(e)=>e.scrollWidth<=innerWidth'),width
  page.screenshot(path=str(out/f'15-gallery-{width}.png'))
  page.get_by_role('tab',name='최종 결과',exact=True).click();f.locator('#districts').wait_for()
  assert f.locator('html').evaluate('(e)=>e.scrollWidth<=innerWidth'),width
  page.screenshot(path=str(out/f'16-results-{width}.png'))
  f.locator('.reading-nav a[href="#policy"]').click();page.wait_for_timeout(650)
  assert f.locator('html').evaluate('(e)=>e.scrollWidth<=innerWidth'),width
  page.screenshot(path=str(out/f'18-policy-{width}.png'))
  page.get_by_role('tab',name='그림 모음',exact=True).click();f.locator('#library-count').wait_for()
 page.get_by_role('tab',name='최종 결과',exact=True).click();f.locator('#districts').wait_for()
 f.locator('#districts a[href="district-report.html"]').click()
 f.locator('.report').wait_for()
 assert f.locator('.report img').count()==12
 assert f.locator('.report table').count()>0
 assert page.url=='http://127.0.0.1:8765/'
 page.get_by_role('tab',name='신고 지도',exact=True).click()
 assert page.locator('.map-app').is_visible()
 assert not errors,errors
 assert not failed,failed
 print(json.dumps({'figures':60,'core':18,'cases':9,'supplement_figures':12,'page_errors':errors,'failed_local_requests':failed,'status':'PASS'},ensure_ascii=False))
 b.close()
