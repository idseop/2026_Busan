"""Independent integration review; underlying selection values reuse separate review."""
from pathlib import Path
import json,hashlib
from playwright.sync_api import sync_playwright
O=Path(__file__).resolve().parent;R=O.parents[3];B=O.parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(name,value):checks.append({'name':name,'pass':bool(value)})
for name in ['selection-independent.json','selection-tvd-independent.json','response-independent.json','resolution-source-verification.json']:
 p=O/name;v=load(p);ck('independent evidence passed '+name,v.get('pass',False) or (bool(v.get('passed')) and not v.get('failed')));
report=R/'output/부산119-쟁점해결-20260916/index.html';s=report.read_text(encoding='utf-8')
for phrase in ['아직 참여자를 대상으로 실행하지 않았','현재 미조치','확보하지 못했습니다','실제 시설의 보수나 기관 대장 수정까지 우리가 시행한 것은 아닙니다','별도 비교 사례','다른 서비스입니다']:
 ck('report interpretation '+phrase,phrase in s)
cases=load(report.parent/'case-selection.json');ck('three distinct cases',len(cases)==3 and len({x['rawDong'] for x in cases})==3)
ck('no patient/real dong or efficacy assertion',all(not x['actualDongConfirmed'] and not x['effectsMeasured'] for x in cases))
errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 page=browser.new_page(viewport={'width':1600,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((R/'output/부산119-전지역후속검증-20260916/explorer.html').as_uri())
 for dong,sub in [('연산동','심정지'),('부전동','교통사고'),('광안동','교통사고')]:
  page.locator('#search').fill(dong);page.locator('#subtype').select_option(sub)
  for scope in 'ABC':
   page.locator('#scope').select_option(scope)
   state=page.evaluate('''() => {const r=d.catalogue.find(x=>x.district+'|'+x.rawDong===selected&&x.subtype===$('subtype').value&&x.scope===$('scope').value);const s=d.selectionDiagnostics.find(x=>x.CLMTY_SGG_NM===r.district&&x.CLMTY_EMD_NM===r.rawDong&&x.EMRG_RSCU_CLSF_NM===r.subtype&&x.scope===r.scope&&x.period==='2020–2024');return {count:r.count,after:Number(s.afterAll),text:$('selection-update').innerText,n:[s.beforeAll,s.beforeMobile,s.afterMobile],service:$('service-update')?.innerText}}''')
   ck(dong+scope+' current catalogue vs complete all',state['count']==state['after'])
   ck(dong+scope+' all three denominator labels',all(f'{int(n):,}건' in state['text'] for n in state['n']))
   ck(dong+scope+' service appropriate type',('실습 기자재' in state['service']) if sub=='심정지' else ('실습 기자재' not in state['service']))
 page.locator('#search').fill('없는지역검색검증');ck('empty state clears selection and services',page.locator('#selection-update').count()==0 and page.locator('#service-update').count()==0)
 page.goto(report.as_uri());ck('report renders ten sections',page.locator('section').count()==10)
 ck('all report images load',page.evaluate('Array.from(document.images).every(x=>x.complete&&x.naturalWidth>0)'))
 page.screenshot(path=str(O/'resolution-report-review-1600.png'))
 browser.close()
ck('no browser JavaScript errors',not errors)
out={'pass':all(c['pass'] for c in checks),'checks':checks,'errors':errors,'reviewedFiles':{str(p.relative_to(R)):sha(p) for p in [report,R/'scripts/build_resolution_report_20260916.py',R/'scripts/build_followup_explorer_20260916.py']},'scope':'3 cases × A/B/C; service subtype isolation; empty state; report figures. Packaging link copy pending separately. No user outcome experiment conducted.'}
(O/'resolution-integration-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'pass':out['pass'],'checks':len(checks),'failed':[c for c in checks if not c['pass']]},ensure_ascii=False));assert out['pass']
