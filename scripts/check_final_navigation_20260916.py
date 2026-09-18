from pathlib import Path
from urllib.parse import urlparse,parse_qs
from playwright.sync_api import sync_playwright
import json,hashlib
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import threading
R=Path(__file__).resolve().parents[1];O=R/'data/processed/최종마감-20260916/verification';O.mkdir(parents=True,exist_ok=True);checks=[];errors=[]
def ck(name,ok):checks.append({'check':name,'pass':bool(ok)})
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(R/'web/final')));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);page=b.new_page(viewport={'width':1600,'height':900});page.on('pageerror',lambda e:errors.append(str(e)));url=base+'/index.html';page.goto(url);page.wait_for_timeout(2500)
 ck('final results header',page.locator('#analysis-open').get_attribute('href')=='results/final/index.html')
 ck('gallery once',page.locator('.topbar a[href="results/final/gallery.html"]').count()==1)
 ck('map info plain name',page.locator('#map-source-open').inner_text()=='지도 정보 ⓘ')
 ck('nine focus shortcuts',page.locator('[data-deep-shortcut]').count()==9)
 page.screenshot(path=str(O/'after-map-1600.png'))
 registry=page.evaluate('window.BUSAN_FINAL_CASES.cases')
 for x in registry:
  page.locator('[data-deep-shortcut="'+x['id']+'"]').click();page.wait_for_timeout(250)
  ck(x['rawDong']+' map selection',x['rawDong'] in page.locator('#detail-title').inner_text())
  link=page.locator('[data-final-case="'+x['id']+'"]');ck(x['rawDong']+' exact link',link.count()==1)
  params=parse_qs(urlparse(link.get_attribute('href')).query)
  ck(x['rawDong']+' fixed C/dong/type',params=={'district':[x['district']],'dong':[x['rawDong']],'type':[x['subtype']],'scope':['C']})
  ck(x['rawDong']+' separate condition label','2020–2024 전체' in page.locator('.final-case-links').inner_text())
  if x['rawDong']=='연산동':page.screenshot(path=str(O/'after-map-yeonsan-1600.png'))
  target=link.get_attribute('href');t=b.new_page();t.goto((R/'web/final'/target.split('?')[0]).as_uri()+'?'+target.split('?')[1]);ck(x['rawDong']+' explorer selected',x['rawDong'] in t.locator('#detail h2').inner_text() and x['subtype'] in t.locator('#detail h2').inner_text());t.close()
 page.locator('#filters-reset').click();ck('reset closes detail',page.locator('#right-panel').is_hidden())
 ck('no JS errors',not errors);b.close()
server.shutdown()
(O/'navigation-author-checks.json').write_text(json.dumps({'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL','checks':checks,'errors':errors,'scope':'작성자 스모크; 독립 승인 별도','beforeScreenshot':'수정 전에 캡처하지 못해 신규 이전 화면으로 표시하지 않음'},ensure_ascii=False,indent=2),encoding='utf-8');print(len(checks),[x for x in checks if not x['pass']])
