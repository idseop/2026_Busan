"""Download public CHS reports for selected Busan case districts, without microdata."""
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
import subprocess,json,hashlib,zipfile,io
from lxml import html
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/context'
tree=html.fromstring((O/'chs-busan-2024-post.html').read_text(encoding='utf-8'))
records=[]
for a in tree.xpath('//a[@downloadname]'):
 name=a.get('downloadname')
 if not any(gu in name for gu in ['연제구','부산진구','수영구']):continue
 u=urlsplit(a.get('href'));url=urlunsplit((u.scheme,u.netloc,u.path,urlencode(parse_qsl(u.query)),''))
 gu=next(g for g in ['연제구','부산진구','수영구'] if g in name);p=O/f'chs2024-{gu}.zip'
 if not p.exists():subprocess.run(['curl.exe','--silent','--show-error','--fail','--location','--max-time','45',url,'--output',str(p)],check=True)
 valid=zipfile.is_zipfile(p)
 rec={'name':name,'district':gu,'url':url,'landing':'https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do','form':{'year':2024,'ctprvn':26},'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'validZip':valid,'files':[]}
 if valid:
  with zipfile.ZipFile(p) as z:
   assert z.testzip() is None
   for i,n in enumerate(z.namelist()):
    if n.lower().endswith('.pdf'):
     dest=O/f'chs2024-{gu}-{i}.pdf';dest.write_bytes(z.read(n));rec['files'].append(dest.name)
 records.append(rec)
(O/'chs-report-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
