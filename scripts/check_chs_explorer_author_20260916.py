from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright
import json
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/context';checks=[]
def ck(n,v):checks.append({'name':n,'pass':bool(v)});assert v,n
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page(viewport={'width':1600,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 url=(R/'web/final/results/followup/explorer.html').as_uri()
 for gu,dong,val in [('연제구','연산동','29.0%'),('부산진구','부전동','26.7%'),('수영구','광안동','24.3%')]:
  p.goto(url+'?'+urlencode({'district':gu,'dong':dong,'type':'심정지','scope':'C'}));sec=p.locator('#resident-education-context')
  ck(gu+' crude',val in sec.inner_text());ck(gu+' separate denominators','분모가 다릅니다' in sec.inner_text() and '13.8%' in sec.inner_text());ck(gu+' exactly3 indicators',sec.locator('tbody tr').count()==3)
  for scope in 'AB':p.locator('#scope').select_option(scope);ck(gu+scope+' fixed context',val in sec.inner_text())
  p.locator('#subtype').select_option('교통사고');ck(gu+' medical removed on traffic',p.locator('#resident-education-context').count()==0)
 p.goto(url+'?'+urlencode({'district':'연제구','dong':'연산동','type':'심정지','scope':'C'}));p.locator('#resident-education-context').scroll_into_view_if_needed();p.screenshot(path=str(O/'explorer-chs-context.png'))
 ck('temporal preserved',p.locator('#temporal-transfer').count()==1);ck('no page errors',not errors);b.close()
(O/'explorer-author-checks.json').write_text(json.dumps({'checks':checks,'authorChecksOnly':True,'independentReviewPending':True},ensure_ascii=False,indent=2),encoding='utf-8');print(len(checks),'author checks')
