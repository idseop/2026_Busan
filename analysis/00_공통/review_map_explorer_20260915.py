"""Independent map application verification; immutable data and UI checks."""
from pathlib import Path
import json,hashlib,datetime,sys
ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_region(data,year,scope,typ,district=None,raw=None):
 rows=[r for r in data['rawRegions'] if r['scope']==scope and (year=='all' or r['year']==int(year)) and (district is None or r['district']==district) and (raw is None or r['rawDong']==raw)]
 return {'count':sum(r['total'] if typ=='all' else r['typeCounts'].get(typ,0) for r in rows),'core8':sum(r['core8Total'] if typ=='all' else r['core8TypeCounts'].get(typ,0) for r in rows)}
def validate_freeze(check):
 frozen=json.loads((OUT/'input_freeze.json').read_text(encoding='utf-8'))
 check('frozen_file_set',set(x['path'] for x in frozen['files'])=={str(p.relative_to(ROOT)) for p in (WEB/'data').iterdir() if p.is_file()})
 for item in frozen['files']:check('data_immutable_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
def freeze():
 OUT.mkdir(exist_ok=True)
 target=OUT/'input_freeze.json'
 if target.exists():raise RuntimeError('Existing input freeze must not be overwritten')
 files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((WEB/'data').iterdir()) if p.is_file()]
 target.write_text(json.dumps({'frozenAt':datetime.datetime.now().astimezone().isoformat(),'policy':'Existing public aggregate data immutable during map application rewrite; no raw reaggregation.','fileCount':len(files),'files':files},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'frozenFiles':len(files)}))
def main():
 from playwright.sync_api import sync_playwright
 d=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'));deep=json.loads((WEB/'data/deep-data.json').read_text(encoding='utf-8'))
 checks=[];errors=[]
 def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
 validate_freeze(check)
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page(viewport={'width':1440,'height':900});p.context.set_offline(True);p.on('pageerror',lambda e:errors.append(str(e)));p.goto((WEB/'index.html').as_uri());p.wait_for_selector('#app:not([hidden])');p.add_style_tag(content='*{transition:none!important}')
  check('initial_no_implicit_region',p.locator('#right-panel').is_hidden() and p.locator('#region-list button').count()==16)
  def district(name):
   el=p.locator(f'.map-place-label[data-district="{name}"]');el.focus();el.press('Enter')
  for name in sorted({r['district'] for r in d['rawRegions']}):
   district(name);expected=expected_region(d,'all','A','all',name)
   check(name+'_district_not_first_raw',p.locator('#detail-content').get_attribute('data-kind')=='district' and int(p.locator('#detail-content').get_attribute('data-total'))==expected['count'])
   p.locator('[data-tab="population"]').click();pop=[r for r in d['population'] if r['district']==name and r['year']==2024]
   check(name+'_single_year_population',int(p.locator('#population-summary').get_attribute('data-total'))==sum(r['total'] for r in pop) and p.locator('#population-summary').get_attribute('data-year')=='2024')
   # Population uses mutually exclusive 읍면동 rows; age detail reconciles all 101 ages.
   cells=p.locator('.age-table-wrap tbody tr td:nth-child(2)').all_text_contents()
   check(name+'_101_ages', [int(v.replace(',','')) for v in cells]==[sum(r['ages'][i] for r in pop) for i in range(101)])
  for c in deep['cases']:
   p.locator('#filters-reset').click();p.locator('#list-raw').click();p.locator('#region-search').fill(c['rawDong']);p.locator(f'#region-list [data-key="{c["district"]}|{c["rawDong"]}"]').click()
   p.select_option('#type',c['type'])
   for scope in ['A','B','C']:
    p.select_option('#scope',scope);p.select_option('#year','2020');expected=expected_region(d,2020,scope,c['type'],c['district'],c['rawDong'])
    check(c['id']+scope+'_raw_scope',int(p.locator('#detail-content').get_attribute('data-total'))==expected['count'] and p.locator('#detail-content').get_attribute('data-kind')=='raw')
    p.locator('[data-tab="time"]').click();cells=[0]*42;months=[0]*12
    for row in deep['dayHour']:
     if row[0]==c['regionIndex'] and row[1]==2020 and row[2]==deep['meta']['scopes'].index(scope) and row[3]==deep['meta']['types'].index(c['type']):cells[row[4]*6+row[5]]+=row[6]
    for row in deep['month']:
     if row[0]==c['regionIndex'] and row[1]==2020 and row[2]==deep['meta']['scopes'].index(scope) and row[3]==deep['meta']['types'].index(c['type']):months[row[4]-1]+=row[5]
    actual=p.locator('.heat-cell').evaluate_all('(es)=>es.map(e=>Number(e.dataset.count))');actualm=p.locator('#detail-month rect').evaluate_all('(es)=>es.map(e=>Number(e.dataset.count))')
    check(c['id']+scope+'_time_joint_cells',actual==cells and actualm==months and sum(cells)==expected['count'])
    p.locator('[data-tab="services"]').click();check(c['id']+scope+'_case_five_year_fixed',int(p.locator('#case-hours').get_attribute('data-total'))==c['countsByScope'][scope]['selected17Total'] and '2020–2024년 고정 비교' in p.locator('#detail-content').inner_text())
   p.select_option('#year','2024');p.locator('[data-tab="population"]').click()
   if c['rawDong']=='연산동':
    check('multiple_candidates_no_automatic_sum',p.locator('#population-summary').count()==0)
    code=p.locator('#population-dong option').nth(1).get_attribute('value');p.select_option('#population-dong',code);expectedp=next(r for r in d['population'] if r['year']==2024 and r['code']==code)
    check('explicit_single_candidate_population',int(p.locator('#population-summary').get_attribute('data-total'))==expectedp['total'])
   else:
    code=next(x for x in c['populationLinks'] if x['year']==2024)['uniqueCode'];check(c['id']+'_exact_population',p.locator('#population-summary').get_attribute('data-code')==code)
  p.locator('#filters-reset').click();check('reset_closes_and_defaults',p.locator('#right-panel').is_hidden() and p.locator('#year').input_value()=='all' and p.locator('#region-list button').count()==16)
  p.locator('#region-search').fill('NOT_A_REGION');check('empty_list',p.locator('#region-list button').count()==0 and '일치하는 지역이 없습니다' in p.locator('#region-list').inner_text());p.locator('#filters-reset').click()
  p.locator('#map-source-open').click();check('geography_qualified','원의 면적' in p.locator('#about-content').inner_text() and '실제 신고 위치가 아닙니다' in p.locator('#about-content').inner_text());p.locator('#about-close').click()
  for width,height in [(390,844),(360,640),(800,900),(801,900)]:
   p.set_viewport_size({'width':width,'height':height});p.wait_for_timeout(100)
   check(f'{width}_no_page_overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1 && document.documentElement.scrollHeight<=innerHeight+1'))
   if width<=800:
    p.locator('#left-toggle').click();check(f'{width}_drawer_visible',p.locator('#left-panel').bounding_box()['x']>=0);p.locator('#left-close').click();district('기장군');before=p.locator('#right-panel').bounding_box()['height'];p.locator('#sheet-toggle').click();check(f'{width}_sheet_expands',p.locator('#right-panel').bounding_box()['height']>before);p.locator('#detail-close').click();check(f'{width}_detail_closes',p.locator('#right-panel').is_hidden())
   else:check('801_desktop_panels',p.locator('#left-panel').bounding_box()['x']==0 and p.locator('#map-viewport').bounding_box()['width']>0)
  check('no_browser_errors',not errors);b.close()
 validate_freeze(check)
 result={'passed':all(c['passed'] for c in checks),'checks':checks,'errors':errors,'reviewedFiles':{str(x.relative_to(ROOT)):sha(x) for x in [WEB/'index.html',WEB/'assets/app.js',WEB/'assets/style.css']},'scope':'Independent UI arithmetic/state/geometry semantics/responsive behavior. Parent separately runs full 90 filter and browser visual checks. No raw reaggregation.'}
 (OUT/'independent_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))
if __name__=='__main__':
 if '--freeze' in sys.argv:freeze()
 else:main()
