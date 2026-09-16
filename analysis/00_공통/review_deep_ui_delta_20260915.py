"""Independent delta verification of month/case-time/resident additions."""
from pathlib import Path
import json,hashlib,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];WEB=ROOT/'web/final';OUT=ROOT/'data/processed/심층분석-20260915'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'));deep=json.loads((WEB/'data/deep-data.json').read_text(encoding='utf-8'));checks=[];errors=[]
 def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page(viewport={'width':1440,'height':1000});p.context.set_offline(True);p.on('pageerror',lambda e:errors.append(str(e)));p.goto((WEB/'index.html').as_uri())
  for c in deep['cases']:
   p.locator(f'[data-case-id="{c["id"]}"]').click()
   for scope in ['A','B','C']:
    p.select_option('#scope',scope)
    for year in ['all',2020,2024]:
     p.select_option('#year',str(year));name=f'{c["id"]}_{scope}_{year}'
     observed=[int(re.search(r': ([\d,]+)건',t)[1].replace(',','')) for t in p.locator('#local-month rect title').all_text_contents()]
     expected=[0]*12
     for row in deep['month']:
      if row[0]==c['regionIndex'] and row[2]==deep['meta']['scopes'].index(scope) and row[3]==deep['meta']['types'].index(c['type']) and (year=='all' or row[1]==year):expected[row[4]-1]+=row[5]
     check(name+'_month12',observed==expected and sum(observed)==int(p.locator('#local-metrics').get_attribute('data-total'))==int(p.locator('#local-month').get_attribute('data-total')))
     hours=[int(re.search(r': ([\d,]+)건',t)[1].replace(',','')) for t in p.locator(f'#case-hours-{c["index"]} rect title').all_text_contents()]
     expected_hours=[0]*6
     for row in deep['caseTime']:
      if row[0]==c['index'] and row[2]==deep['meta']['scopes'].index(scope):expected_hours[row[4]]+=row[5]
     check(name+'_case6_five_years',hours==expected_hours and sum(hours)==c['countsByScope'][scope]['selected17Total'] and '2020–2024년 합계' in p.locator('.case-time-insight').inner_text())
     py=2024 if year=='all' else year;link=next(x for x in c['populationLinks'] if x['year']==py);summary=p.locator('#local-population-summary')
     if link['codeLevelEligible']:
      pop=next(x for x in d['population'] if x['year']==py and x['code']==link['uniqueCode']);vals=[int(re.search(r'[\d,]+',t)[0].replace(',','')) for t in summary.locator('.population-stat strong').all_text_contents()]
      check(name+'_resident_counts',vals==[pop['total'],sum(pop['ages'][:15]),sum(pop['ages'][15:65]),sum(pop['ages'][65:])] and summary.get_attribute('data-year')==str(py))
      check(name+'_population_synchronized',p.locator('#population-dong').input_value()==pop['code'])
     else:check(name+'_multiple_not_merged',summary.get_attribute('data-total') is None and '개별 선택 필요' in summary.inner_text())
  p.locator('#region-search').fill('없는원문지역XYZ');check('empty_hides_resident_and_cases',p.locator('#region-analysis').is_hidden() and not p.locator('#local-cases').is_visible())
  check('no_page_errors',not errors);b.close()
 fm=json.loads((OUT/'figure_manifest.json').read_text(encoding='utf-8'))
 check('figure_four_inputs_and_generator',len(fm.get('inputs',[]))==4 and bool(fm.get('generator')))
 for item in fm.get('inputs',[])+[fm['generator']]+fm['outputs']:check('figure_chain_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
 paths=[WEB/'assets/app.js',WEB/'assets/style.css',WEB/'index.html',OUT/'figure_manifest.json']
 result={'passed':all(c['passed'] for c in checks),'checks':checks,'errors':errors,'hashes':{str(x.relative_to(ROOT)):sha(x) for x in paths},'scope':'Delta only. Prior independent_deep_ui_report_review.json provides 183 earlier checks; raw source cohort unchanged.'}
 (OUT/'independent_deep_ui_delta_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))
if __name__=='__main__':main()
