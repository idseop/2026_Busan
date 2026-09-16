from pathlib import Path
import json,re,hashlib
from urllib.parse import unquote,urlsplit
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];V=R/'data/processed/고도화검증-20260916/verification';V.mkdir(exist_ok=True)
O=R/'output/부산119-쟁점해결-20260916';F=R/'output/부산119-전지역후속검증-20260916';checks=[];errors=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 p=b.new_page();p.on('pageerror',lambda e:errors.append(str(e)))
 for w,h in [(1920,1080),(1600,900),(1366,768)]:
  p.set_viewport_size({'width':w,'height':h});p.goto('http://127.0.0.1:8765/results/advance/',wait_until='networkidle')
  assert p.locator('section').count()==13
  assert p.locator('figure img').count()==5
  assert p.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.screenshot(path=str(V/f'advance-first-{w}.png'))
  if w==1600:
   for s in ['s2','s4','s5','s8']:
    p.locator('#'+s).evaluate('(e)=>e.scrollIntoView({block:"start"})');p.screenshot(path=str(V/f'advance-{s}.png'))
  p.goto('http://127.0.0.1:8765/results/followup/explorer.html',wait_until='networkidle')
  assert p.locator('#list button').count()==194
  assert '1,048' in p.locator('#selection-update').inner_text()
  assert '맞이길' in p.locator('#service-update').inner_text()
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
  p.screenshot(path=str(V/f'advance-explorer-{w}.png'))
  checks.append({'viewport':[w,h],'reportSections':13,'figures':5,'overflow':False})
 for scope in ['A','B','C']:
  p.select_option('#scope',scope)
  r=p.evaluate("s=>FOLLOWUP.catalogue.find(r=>r.scope===s&&r.district==='부산진구'&&r.rawDong==='부전동'&&r.subtype==='교통사고')",scope)
  assert f"{r['count']:,}" in p.locator('.number').inner_text()
  diag=p.evaluate("s=>FOLLOWUP.selectionDiagnostics.find(r=>r.scope===s&&r.CLMTY_SGG_NM==='부산진구'&&r.CLMTY_EMD_NM==='부전동'&&r.EMRG_RSCU_CLSF_NM==='교통사고'&&r.period==='2020–2024')",scope)
  assert int(float(diag['afterAll']))==r['count']
  assert f"{int(float(diag['beforeMobile'])):,}" in p.locator('#selection-update').inner_text()
  checks.append({'scope':scope,'count':r['count'],'beforeMobile':int(float(diag['beforeMobile']))})
 p.select_option('#scope','C');p.select_option('#subtype','심정지');p.fill('#search','연산동')
 assert '511' in p.locator('.number').inner_text() and '710' in p.locator('#selection-update').inner_text()
 assert '교육용 AED' in p.locator('#service-update').inner_text() and '7일' in p.locator('#service-update').inner_text()
 assert '수료증' in p.locator('#service-update').inner_text() and '맞이길' not in p.locator('#service-update').inner_text()
 p.locator('#service-update').evaluate('(e)=>e.scrollIntoView({block:"start"})');p.screenshot(path=str(V/'advance-yeonsan-services.png'))
 p.select_option('#subtype','일반화재(주택)');p.fill('#search','온천동')
 assert '동래소방서·동래/사직복지관' in p.locator('#detail').inner_text()
 assert '교육용 AED' not in p.locator('#detail').inner_text()
 p.fill('#search','신평동');assert '상충' in p.locator('#service-update').inner_text()
 assert '현재 신청 가능' not in p.locator('#service-update').inner_text()
 p.fill('#search','없는지역XYZ');assert p.locator('#selection-update').count()==0 and p.locator('#service-update').count()==0
 checks.append({'regionalAndTypeEvidenceNotMixed':True,'dongnaeProgrammeLinked':True,'publicationConflictNotOpenNow':True,'emptyStateNoStaleFacts':True})
 for path in [O/'index.html',F/'explorer.html',F/'쟁점해결.html']:
  p.goto(path.as_uri(),wait_until='load');assert p.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)')
  for a in p.locator('a').all():
   h=a.get_attribute('href')
   if h and not h.startswith(('http','#')):assert (path.parent/unquote(urlsplit(h).path)).exists(),h
 checks.append({'fileDirectAndLocalLinks':True})
 p.goto('http://127.0.0.1:8765/',wait_until='networkidle');p.locator('a[href="results/advance/index.html"]').click();assert '/results/advance/' in p.url
 checks.append({'mapLatestLink':True})
 b.close()
assert not errors,errors
for folder in [O,F]:
 for f in folder.iterdir():
  if f.suffix in ['.csv','.js','.json','.html']:
   txt=f.read_text(encoding='utf-8-sig');assert not re.search('DCLR_RCPT_NO|ACDNT_OCRN_LOT|DAMG_RGN_LAT|custReprNm|bizRegNo',txt),f
checks.append({'privateIncidentFieldsAbsent':True})
out={'checks':checks,'errors':errors,'testedFiles':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [O/'index.html',F/'explorer.html',F/'explorer-data.js']]}
(V/'web-validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'checks':len(checks),'errors':errors}))
