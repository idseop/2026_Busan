from pathlib import Path
import json,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/verification'
OUT.mkdir(parents=True,exist_ok=True)
errors=[];checks=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 for w,h in [(1920,1080),(1600,900),(1366,768)]:
  page.set_viewport_size({'width':w,'height':h})
  page.goto('http://127.0.0.1:8765/results/deepening/',wait_until='networkidle')
  assert page.locator('section').count()==9
  assert page.locator('img').count()==6
  assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(OUT/f'deepening-{w}.png'))
  for anchor in ['#s2','#s3','#s4','#s5','#s6']:
   page.locator(anchor).evaluate('(e)=>e.scrollIntoView({block:"start"})')
   assert page.locator(anchor).bounding_box()['width']<=w
   if w==1600:page.screenshot(path=str(OUT/f'deepening-{anchor[1:]}.png'))
  checks.append({'viewport':[w,h],'images':6,'sections':9,'overflow':False})
 for a in page.locator('a').all():
  href=a.get_attribute('href')
  if href and not href.startswith(('http','#')):
   assert (ROOT/'web/final/results/deepening'/href).exists(),href
 page.goto((ROOT/'output/부산119-동별보완-심화결과-20260916/index.html').as_uri(),wait_until='load')
 assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
 checks.append({'fileDirect':True,'localLinks':True})
 page.goto('http://127.0.0.1:8765/',wait_until='domcontentloaded')
 page.locator('a[href="results/deepening/index.html"]').click()
 page.wait_for_url('**/results/deepening/index.html')
 checks.append({'mapNavigation':True})
 browser.close()
assert not errors,errors
public=ROOT/'web/final/results/deepening'
for p in public.iterdir():
 if p.suffix in ['.html','.csv','.json','.md']:
  assert not re.search(r'DCLR_RCPT_NO|ACDNT_OCRN_LOT|DAMG_RGN_LAT|custReprNm|bizRegNo',p.read_text(encoding='utf-8-sig')),p
checks.append({'publicIndividualCallFieldsAbsent':True})
(OUT/'deepening-browser.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'errors':errors}))
