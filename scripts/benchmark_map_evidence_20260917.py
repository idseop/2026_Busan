"""Fixed-task inline evidence benchmark; this is not a human performance experiment."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import threading,zipfile,json,hashlib,re,csv
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];N=R/'data/processed/지도입증확장-20260916';O=N/'benchmark';O.mkdir(exist_ok=True)
truthPath=N/'verification/task-truth.json';truth=json.loads(truthPath.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=R/truth['baselineZIP']['path'];assert sha(archive)==truth['baselineZIP']['sha256']
baseline=O/'baseline';baseline.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
 for name in z.namelist():
  if name.startswith(('assets/','data/','results/')) or name=='index.html':
   dest=(baseline/name).resolve();assert dest.is_relative_to(baseline.resolve());dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
servers=[]
def serve(path):
 s=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(path)));threading.Thread(target=s.serve_forever,daemon=True).start();servers.append(s);return f'http://127.0.0.1:{s.server_port}'
urls={'baseline':serve(baseline),'candidate':serve(R/'web/final')};results=[];errors=[]
def match(groups,text):return all(any(token in text for token in alternatives) for alternatives in groups)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
 for version,base in urls.items():
  page=b.new_page(viewport={'width':1600,'height':900});page.on('pageerror',lambda e:errors.append(str(e)))
  # This task concerns HTML information retrieval. External basemap access is tested separately.
  page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
  page.goto(base+'/',wait_until='domcontentloaded');page.wait_for_selector('[data-deep-shortcut]')
  for task in truth['tasks']:
   cases=page.evaluate('window.BUSAN_FINAL_CASES.cases');case=next(x for x in cases if x['district']==task['district'] and x['rawDong']==task['rawDong'] and x['subtype']==task['subtype'])
   page.locator('[data-deep-shortcut="'+case['id']+'"]').click()
   texts=[];hrefs=set()
   # Both existing map tabs are eligible; do not force the baseline to its less informative tab.
   for tab in ['overview','services']:
    page.locator('[data-tab="'+tab+'"]').click()
    if version=='candidate':page.locator('[data-evidence-domain]').wait_for(state='attached') if tab=='services' else None
    if version=='candidate' and tab=='services':page.select_option('[data-evidence-domain]',task['subtype'])
    # Both versions may expose evidence through native disclosure controls.
    page.locator('#detail-content details').evaluate_all('(els)=>els.forEach(x=>x.open=true)')
    texts.append(page.locator('#detail-content').inner_text());hrefs.update(page.locator('#detail-content a[href]').evaluate_all('(els)=>els.map(x=>x.getAttribute("href"))'))
    # Progressive disclosure is eligible under the fixed same-document protocol.
    # Apply the same traversal rule to either version if step controls exist.
    if tab=='services' and page.locator('[data-evidence-step]').count():
     for step in page.locator('[data-evidence-step]').evaluate_all('(els)=>els.map(x=>x.dataset.evidenceStep)'):
      page.locator('[data-evidence-step="'+step+'"]').click()
      page.locator('#detail-content details').evaluate_all('(els)=>els.forEach(x=>x.open=true)')
      texts.append(page.locator('#detail-content').inner_text());hrefs.update(page.locator('#detail-content a[href]').evaluate_all('(els)=>els.map(x=>x.getAttribute("href"))'))
   text='\n'.join(texts);fields=task['fiveFields'];count=f"{task['expectedCount']:,}"
   canonical=page.locator('[data-evidence-domain]').input_value() if page.locator('[data-evidence-domain]').count() else None
   shownKey=page.locator('[data-evidence-key]').get_attribute('data-evidence-key') if page.locator('[data-evidence-key]').count() else None
   # The visible short label "주택 화재" maps to this exact original category;
   # verify selected canonical value and case identity, never just a loose text synonym.
   subtypeMatched=task['displaySubtype'] in text or (task['subtype']=='일반화재(주택)' and canonical==task['subtype'] and shownKey==task['id'] and '주택 화재' in text)
   matched={'receipt':bool(re.search(r'(?<![\d,])'+re.escape(count)+r'(?![\d,])',text)) and subtypeMatched}
   for name in ['context','existingResponse','proposal']:matched[name]=match(fields[name]['requiredConceptGroups'],text)
   matched['source']=fields['source']['requiredOfficialURL'] in hrefs
   forbidden=[x for x in task['forbiddenClaims'] if x in text]
   results.append({'version':version,'id':task['id'],'fields':matched,'matchedFields':sum(matched.values()),'allFiveInline':all(matched.values()),'stepControls':page.locator('[data-evidence-step]').count(),'alreadyAvailableElsewhere':task['baselineEvidence']['alreadyAvailableElsewhere'],'forbiddenClaimsFound':forbidden,'documentStayedOnMap':page.url.rstrip('/')==base,'text':text})
   if task['rawDong'] in ['연산동','기장읍']:page.screenshot(path=str(O/(version+'-'+task['rawDong']+'.png')))
  page.close()
 b.close()
for s in servers:s.shutdown()
summary={v:{'tasks':sum(x['version']==v for x in results),'inlineFiveFieldCases':sum(x['version']==v and x['allFiveInline'] for x in results),'matchedFields':sum(x['matchedFields'] for x in results if x['version']==v),'totalFields':45,'availableAcrossWholeSite':9} for v in urls}
out={'status':'PASS' if not errors and all(x['allFiveInline'] and not x['forbiddenClaimsFound'] for x in results if x['version']=='candidate') else 'FAIL','scope':'固定9사례의 지도 문서 내 근거 연결 기능. 사람 이해·시간·신청·피해 감소 효과가 아님.','truthSha256':sha(truthPath),'baselineSha256':sha(archive),'summary':summary,'errors':errors,'rows':results,'interpretation':'기존 웹에도9사례 근거가 다른페이지에 존재했다. 전체자료 신규확보율이나 실제사람성능의 전후효과로 해석하지 않는다.'}
(O/'results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
with (O/'task-results.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['version','id','matchedFields','allFiveInline','documentStayedOnMap']);w.writeheader();w.writerows({k:x[k] for k in w.fieldnames} for x in results)
print(json.dumps({'status':out['status'],'summary':summary,'errors':errors},ensure_ascii=False))
