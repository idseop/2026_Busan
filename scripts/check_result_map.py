"""Independent localhost result-map QA. OSM tiles ALWAYS mocked, never downloaded."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse
import hashlib,json,threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915/result-map'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def main():
 OUT.mkdir(parents=True,exist_ok=True);checks=[];errors=[];remote=[];tile_requests=[];mode={'fail':False}
 def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
 d=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'))
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(WEB)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/index.html'
 def route(request):
  host=urlparse(request.request.url).hostname or ''
  if host in ['127.0.0.1','localhost'] or urlparse(request.request.url).scheme=='file':request.continue_();return
  if host=='tiles.openfreemap.org':request.abort('failed');return
  if host=='tile.openstreetmap.org' or host.endswith('.tile.openstreetmap.org'):
   tile_requests.append(request.request.url)
   if mode['fail']:request.abort('failed')
   else:request.fulfill(status=200,content_type='image/svg+xml',body='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256"><rect width="256" height="256" fill="#eaf3f6"/><text x="12" y="30" fill="#789">MOCK TILE — QA ONLY</text></svg>')
   return
  remote.append(request.request.url);request.abort('blockedbyclient')
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);context=browser.new_context(viewport={'width':1600,'height':900},service_workers='block');context.route('**/*',route);page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url);page.wait_for_selector('#app:not([hidden])')
  page.wait_for_function('Boolean(window.BUSAN_MAP_VIEW && window.BUSAN_DETAIL_MODEL)')
  def totals(year,scope,typ):
   values={r['district']:0 for r in d['rawRegions']}
   for r in d['rawRegions']:
    if r['scope']==scope and (year=='all' or r['year']==int(year)):values[r['district']]+=r['total'] if typ=='all' else r['typeCounts'].get(typ,0)
   return values
  for width,height in [(1920,1080),(1600,900),(1366,768)]:
   page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
   page.locator('#map-reset').click();page.wait_for_timeout(100)
   check(f'{width}_all_busan_visible',page.evaluate('BUSAN_MAP_VIEW.map.getBounds().contains(L.geoJSON(BUSAN_MAP).getBounds())'))
   check(f'{width}_list_usable',page.locator('#region-list').bounding_box()['height']>=120)
   check(f'{width}_fills_map',page.locator('.leaflet-container').bounding_box()['width']==page.locator('#map-viewport').bounding_box()['width'])
   check(f'{width}_no_page_overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth && document.documentElement.scrollHeight<=innerHeight'))
   check(f'{width}_no_label_decoration',page.locator('.map-place-label,.map-callout,.label-backing,.map-symbol').count()==0)
   check(f'{width}_attribution',page.locator('.leaflet-control-attribution').is_visible() and 'SGIS' in page.locator('.leaflet-control-attribution').inner_text())
   check(f'{width}_readable_filters',page.locator('#scope').evaluate('e=>parseFloat(getComputedStyle(e).fontSize)')>=14)
  page.set_viewport_size({'width':1600,'height':900});page.wait_for_timeout(200)
  page.locator('#map-reset').click()
  check('busan_mask_opaque',page.locator('.busan-outside-mask').get_attribute('fill-opacity')=='1')
  check('busan_16_regions_only',page.locator('.map-region').count()==16)
  check('busan_mask_geometry',page.evaluate('''()=>{
   const map=BUSAN_MAP_VIEW.map,path=document.querySelector('.busan-outside-mask');
   const covered=(lat,lng)=>{const p=map.latLngToLayerPoint([lat,lng]);return path.isPointInFill(new DOMPoint(p.x,p.y));};
   return covered(35.2285,128.8894) && covered(35.335,129.037) && !covered(35.1796,129.0756);
  }'''))
  page.evaluate('BUSAN_MAP_VIEW.map.setZoom(2)');page.wait_for_timeout(300)
  check('cannot_zoom_to_country',page.evaluate('BUSAN_MAP_VIEW.map.getZoom()===BUSAN_MAP_VIEW.map.getMinZoom() && BUSAN_MAP_VIEW.map.getMinZoom()>8'))
  page.evaluate('BUSAN_MAP_VIEW.map.panTo([37.5665,126.978],{animate:false})');page.wait_for_timeout(300)
  check('cannot_pan_to_seoul',page.evaluate('BUSAN_MAP_VIEW.map.options.maxBounds.contains(BUSAN_MAP_VIEW.map.getCenter())'))
  page.locator('#map-reset').click()
  for district in sorted(totals('all','A','all')):
   page.evaluate('(d)=>BUSAN_MAP_VIEW.select(d)',district)
   check('select_'+district,page.locator('#detail-content').get_attribute('data-district')==district)
  page.evaluate("BUSAN_MAP_VIEW.select('기장군')")
  for year in ['all',*map(str,range(2020,2025))]:
   page.locator(f'#year-buttons [data-year="{year}"]').click()
   for scope in ['A','B','C']:
    page.select_option('#scope',scope)
    for typ in ['all',*d['meta']['types']]:
     page.select_option('#type',typ);expected=totals(year,scope,typ)
     check(f'counts_{year}_{scope}_{typ}',page.evaluate('BUSAN_MAP_VIEW.getCounts()')==expected and int(page.locator('#detail-content').get_attribute('data-total'))==expected['기장군'])
  page.locator('#filters-reset').click();check('reset',page.locator('#right-panel').is_hidden() and page.locator('#year').input_value()=='all')
  before=page.evaluate('BUSAN_MAP_VIEW.getState().zoom');page.locator('#map-zoom-in').click();page.wait_for_timeout(350);check('zoom',page.evaluate('BUSAN_MAP_VIEW.getState().zoom')>before)
  box=page.locator('#district-map').bounding_box();before=page.evaluate('BUSAN_MAP_VIEW.getState().center');page.mouse.move(box['x']+150,box['y']+150);page.mouse.down();page.mouse.move(box['x']+220,box['y']+170,steps=5);page.mouse.up();page.wait_for_timeout(350);check('pan',page.evaluate('BUSAN_MAP_VIEW.getState().center')!=before)
  deep=json.loads((WEB/'data/deep-data.json').read_text(encoding='utf-8'))
  for case in deep['cases']:
   page.locator('#filters-reset').click();page.locator('#region-search').fill(case['rawDong']);page.locator(f'#region-list [data-district="{case["district"]}"]').first.click();page.locator('[data-tab="services"]').click()
   for scope in ['A','B','C']:
    page.select_option('#scope',scope)
    for year in ['all','2020','2024']:
     page.locator(f'#year-buttons [data-year="{year}"]').click();wanted=sum(case['countsByScope'][scope]['yearCounts']) if year=='all' else case['countsByScope'][scope]['yearCounts'][int(year)-2020]
     check(f'case_{case["rawDong"]}_{year}_{scope}',int(page.locator('.case-observation').get_attribute('data-case-count'))==wanted)
   check('no_questions_'+case['rawDong'],not any(t in page.locator('#detail-content').inner_text() for t in ['살펴볼 질문','확인할 자료','왜 인구','무엇을 더','어떤 연결']))
   check('no_details_'+case['rawDong'],page.locator('#detail-content details').count()==0)
  page.locator('#analysis-open').click();text=page.locator('#analysis-content').inner_text();check('project_result',all(t in text for t in ['704,689','이번 프로젝트','기존 대응','확정되지 않았습니다']));page.locator('#analysis-close').click()
  page.locator('#filters-reset').click();page.locator('#region-search').fill('NO_SUCH_REGION');check('empty_search',page.locator('#region-list [data-key]').count()==0)
  check('no_raster_road_labels',page.evaluate("BUSAN_CONTEXT_STYLE.layers.every(l=>l.type!=='symbol' && l.type!=='raster')"))
  check('local_dong_names',page.evaluate('BUSAN_PLACE_LABELS.places.length===206'))
  check('context_network_fallback',page.locator('#tile-status').is_visible() and page.locator('.map-region').count()==16)
  for theme in ['share','cases','base']:
   page.locator(f'[data-map-theme="{theme}"]').click();check('theme_'+theme,page.evaluate('BUSAN_MAP_VIEW.getState().theme')==theme and page.locator(f'[data-map-theme="{theme}"]').get_attribute('aria-pressed')=='true')
  page.evaluate('BUSAN_MAP_VIEW.map.setZoom(14)');page.wait_for_timeout(300)
  check('dong_labels_on_zoom',page.locator('.dong-name:visible').count()>0)
  check('plain_text_labels',page.locator('.place-name:visible').first.evaluate("e=>getComputedStyle(e).backgroundColor==='rgba(0, 0, 0, 0)' && getComputedStyle(e).boxShadow==='none'"))
  check('label_collisions',page.evaluate("""()=>{const a=[...document.querySelectorAll('.place-name')].filter(e=>e.style.display!=='none').map(e=>e.querySelector('span').getBoundingClientRect());return a.every((r,i)=>a.slice(i+1).every(v=>r.right<=v.left||v.right<=r.left||r.bottom<=v.top||v.bottom<=r.top));}"""))
  page.goto((WEB/'index.html').as_uri());page.wait_for_timeout(300);check('file_local_map',not tile_requests and page.locator('#tile-status').is_visible() and page.locator('.map-region').count()==16)
  check('no_external_dependencies',not remote,remote)
  browser.close()
 server.shutdown()
 freeze=json.loads((ROOT/'data/processed/지도탐색웹-20260915/input_freeze.json').read_text(encoding='utf-8'))
 for item in freeze['files']:check('immutable_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
 check('no_browser_errors',not errors,errors)
 result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checks':checks,'tile_policy':'Local administrative map: all external requests blocked; no road or raster tile layers permitted.','mockTileRequests':len(tile_requests),'blockedRemoteRequests':remote,'site_sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(WEB.rglob('*')) if p.is_file()}}
 (OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))
if __name__=='__main__':main()
