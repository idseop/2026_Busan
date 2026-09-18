from pathlib import Path
import json,hashlib,zipfile
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/context';attempts=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);c=b.new_context(ignore_https_errors=False);p=c.new_page()
 landing='https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do'
 try:
  p.goto(landing,timeout=45000,wait_until='load');p.wait_for_timeout(1000)
  body=p.evaluate("async url=>{let r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'year=2024&ctprvn=26'});return await r.text()}",landing);(O/'chs-browser-post.html').write_text(body,encoding='utf-8')
  from lxml import html
  tree=html.fromstring(body)
  for a in tree.xpath('//a[@downloadname]'):
   name=a.get('downloadname');gu=next((x for x in ['연제구','부산진구','수영구'] if x in name),None)
   if not gu:continue
   url=a.get('href');path=O/f'chs-browser-{gu}.bin'
   try:
    with p.expect_download(timeout=20000) as info:
     p.evaluate('u=>{let a=document.createElement("a");a.href=u;a.textContent="download";document.body.appendChild(a);a.click()}',url)
    info.value.save_as(path);content=path.read_bytes()
   except Exception as e:
    content=p.content().encode('utf-8');path.write_bytes(content)
   item={'district':gu,'url':url,'method':'fresh browser session, browser POST and public attachment click','bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'file':path.name,'zip':zipfile.is_zipfile(path)};attempts.append(item);print(item)
   if item['zip']:
    with zipfile.ZipFile(path) as z:
     for i,n in enumerate(z.namelist()):
      if n.lower().endswith('.pdf'):(O/f'chs-browser-{gu}-{i}.pdf').write_bytes(z.read(n))
 except Exception as e:attempts.append({'error':str(e)})
 b.close()
(O/'chs-browser-attempts.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2),encoding='utf-8')
