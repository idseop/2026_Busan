"""Independent result-comparison verification; no website mutations or remote data."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json, threading, hashlib
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web/final'
OUT=ROOT/'data/processed/지도탐색웹-20260915/context-map/independent-result.json'
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass

def main():
 d=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf8'))
 deep=json.loads((WEB/'data/deep-data.json').read_text(encoding='utf8'))
 checks=[]; errors=[]
 def check(name,ok,detail=None): checks.append(dict(name=name,passed=bool(ok),detail=detail))
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(WEB)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
  page=browser.new_page(viewport={'width':1600,'height':900})
  page.route('**/*',lambda route: route.continue_() if '127.0.0.1' in route.request.url else route.abort())
  page.on('pageerror',lambda e: errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/')
  page.wait_for_selector('[data-deep-shortcut]')
  for case in deep['cases']:
   page.locator(f'[data-deep-shortcut="{case["id"]}"]').click()
   selected=page.locator('#detail-content')
   check('shortcut_'+case['rawDong'],selected.get_attribute('data-district')==case['district'] and case['rawDong'] in page.locator('#right-panel').inner_text())
   for scope in ['A','B','C']:
    page.select_option('#scope',scope)
    for year in ['all','2020','2024']:
     page.locator(f'#year-buttons [data-year="{year}"]').click()
     for typ in ['all',case['type']]:
      page.select_option('#type',typ)
      rows=[r for r in d['rawRegions'] if r['scope']==scope and (year=='all' or r['year']==int(year))]
      local=[r for r in rows if r['district']==case['district'] and r['rawDong']==case['rawDong']]
      other=[r for r in rows if not(r['district']==case['district'] and r['rawDong']==case['rawDong'])]
      lt=sum(r['total'] for r in local); ot=sum(r['total'] for r in other)
      eligible=d['meta']['types'] if typ=='all' else [typ]
      comp=[]
      for t in eligible:
       l=sum(r['typeCounts'].get(t,0) for r in local)/lt
       o=sum(r['typeCounts'].get(t,0) for r in other)/ot
       comp.append((l-o,l,o,t))
      expected=max(comp,key=lambda x:x[0]); element=page.locator('.composition-contrast')
      actual=(float(element.get_attribute('data-local-share')),float(element.get_attribute('data-rest-share')))
      check(f'share_{case["rawDong"]}_{scope}_{year}_{typ}',abs(actual[0]-expected[1])<1e-12 and abs(actual[1]-expected[2])<1e-12,{'type':expected[3],'localDenominator':lt,'restDenominator':ot})
      wanted=sum(r['total'] if typ=='all' else r['typeCounts'].get(typ,0) for r in local)
      check(f'total_{case["rawDong"]}_{scope}_{year}_{typ}',int(selected.get_attribute('data-total'))==wanted)
      summary=page.locator('.case-conclusion').first.inner_text()
      count=case['countsByScope'][scope]['yearCounts']
      wanted=sum(count) if year=='all' else count[int(year)-2020]
      check(f'case_count_{case["rawDong"]}_{scope}_{year}_{typ}',f'{wanted:,}건' in summary)
      stable=all(all(n>0 for n in v['yearCounts']) and (v['yearCounts'][-1]-v['yearCounts'][0])*(v['core8YearCounts'][-1]-v['core8YearCounts'][0])>=0 for v in case['countsByScope'].values())
      check(f'stability_{case["rawDong"]}_{scope}_{year}_{typ}',('변화 방향이 유지됩니다' in summary)==stable)
   page.locator('#filters-reset').click()
  check('no_browser_errors',not errors,errors)
  browser.close()
 server.shutdown()
 result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'scope':'Independent Python recomputation of raw region type shares, selected totals, deep case counts and change signs; browser shortcuts. Remote map requests blocked deliberately; no cartographic visual validation.', 'files':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [WEB/'assets/detail-extension.js',WEB/'assets/detail-model.js',WEB/'data/dashboard.json',WEB/'data/deep-data.json']}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))

if __name__=='__main__':main()
