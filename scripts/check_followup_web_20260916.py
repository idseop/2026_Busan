from pathlib import Path
import json,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'data/processed/후속입증-20260916/verification';V.mkdir(parents=True,exist_ok=True)
OUT=ROOT/'output/부산119-전지역후속검증-20260916';errors=[];checks=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 for w,h in [(1920,1080),(1600,900),(1366,768)]:
  page.set_viewport_size({'width':w,'height':h});page.goto('http://127.0.0.1:8765/results/followup/',wait_until='networkidle')
  assert page.locator('section').count()==14
  assert page.locator('figure img').count()==11
  assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(V/f'followup-report-{w}.png'))
  for sid in ['s4','s6','s10','s11']:
   page.locator('#'+sid).evaluate('(e)=>e.scrollIntoView({block:"start"})')
   if w==1600:page.screenshot(path=str(V/f'followup-{sid}.png'))
  page.goto('http://127.0.0.1:8765/results/followup/explorer.html',wait_until='networkidle')
  assert page.locator('#list button').count()==194
  assert '부전동' in page.locator('h2').inner_text()
  assert '723' in page.locator('.number').inner_text()
  assert '6,216' in page.locator('#detail').inner_text()
  assert '부전1동' in page.locator('#living-context').inner_text()
  assert '부전2동' in page.locator('#living-context').inner_text()
  assert '14시' in page.locator('#living-context').inner_text() and '19시' in page.locator('#living-context').inner_text()
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(V/f'followup-explorer-{w}.png'))
  checks.append({'viewport':[w,h],'reportImages':11,'regions':194,'overflow':False})
 page.select_option('#pop-code',index=1)
 population=page.locator('#population p').first.inner_text()
 for scope in ['A','B','C']:
  page.select_option('#scope',scope)
  expected=page.evaluate("s=>window.FOLLOWUP.catalogue.find(r=>r.scope===s&&r.rawDong==='부전동'&&r.district==='부산진구'&&r.subtype==='교통사고').count",scope)
  assert f'{expected:,}' in page.locator('.number').inner_text()
  assert page.locator('#population p').first.inner_text()==population
  checks.append({'scope':scope,'selectedCount':expected,'populationUnchanged':True})
 for y in [2020,2021,2022,2023,2024]:
  page.select_option('#pop-year',str(y));page.select_option('#pop-code',index=1)
  assert str(y)+'-12-31' in page.locator('#population').inner_text()
  assert '2024 기준월' in page.locator('#living-context').inner_text()
  assert page.locator('#population svg rect').count()==101
 checks.append({'populationYears':5,'allAges':101,'multipleCandidatesNotSummed':True})
 page.select_option('#subtype','산악사고')
 assert '부산연구원 현장연구' not in page.locator('#detail').inner_text()
 assert '동 전체의 상권 배경' not in page.locator('#detail').inner_text()
 page.fill('#search','존재하지않는지역xyz')
 assert page.locator('#list button').count()==0 and '검색 결과 없음' in page.locator('#detail').inner_text()
 page.fill('#search','초읍동');assert page.locator('#list button').count()==1
 assert '찬물샘' in page.locator('#detail').inner_text()
 page.select_option('#subtype','수난사고');page.fill('#search','다대동')
 assert '감시탑2개소' in page.locator('#detail').inner_text()
 page.select_option('#subtype','교통사고');page.fill('#search','거제동')
 assert '증감 방향 민감' not in page.locator('h2').inner_text()
 assert '거제시장' in page.locator('#detail').inner_text()
 page.screenshot(path=str(V/'followup-geoje.png'))
 checks.append({'emptyResult':True,'typeEvidenceNotMixed':True,'outdoorAndTrafficLinked':True})
 for name in ['index.html','explorer.html']:
  page.goto((OUT/name).as_uri(),wait_until='load')
  assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  if name=='explorer.html':assert page.locator('#list button').count()==194
  for a in page.locator('a').all():
   href=a.get_attribute('href')
   if href and not href.startswith(('http','#')):assert (OUT/href).exists(),href
 checks.append({'fileDirectAndLocalLinks':True})
 page.set_viewport_size({'width':1366,'height':768})
 page.goto('http://127.0.0.1:8765/',wait_until='networkidle')
 page.locator('a[href="results/followup/index.html"]').click()
 assert page.url.endswith('/results/followup/index.html')
 checks.append({'mainMapLatestResultLink':True})
 browser.close()
assert not errors,errors
for p in OUT.iterdir():
 if p.suffix in ['.json','.js','.html','.csv']:
  text=p.read_text(encoding='utf-8-sig')
  assert not re.search(r'DCLR_RCPT_NO|ACDNT_OCRN_LOT|DAMG_RGN_LAT|custReprNm|bizRegNo',text),p
checks.append({'individualCallFieldsAbsent':True})
(V/'web-validation.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':len(checks),'errors':errors}))
