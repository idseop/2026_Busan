"""Bounded public-road follow-up snapshots; no private requests or prior-input edits."""
from pathlib import Path
import argparse, subprocess, hashlib, json, datetime, struct, zlib
import olefile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/효과근거확장-20260916/traffic';OUT.mkdir(parents=True,exist_ok=True)
def fetch(name,url):
 p=OUT/name;now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 if not p.exists():
  r=subprocess.run(['curl.exe','-L','--fail','--max-time','45','-A','Mozilla/5.0',url,'-o',str(p)],capture_output=True)
  status=r.returncode
 else:status=0
 result={'file':name,'url':url,'retrievedAt':now,'returncode':status,'bytes':p.stat().st_size if p.exists() else 0,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None}
 with (OUT/'download-manifest.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False)+'\n')
 if p.suffix=='.hwp' and status==0:
  o=olefile.OleFileIO(p);compressed=bool(o.openstream('FileHeader').read()[36]&1);paras=[]
  for sec in o.listdir():
   if sec[0]!='BodyText':continue
   b=o.openstream(sec).read();b=zlib.decompress(b,-15) if compressed else b;i=0
   while i<len(b):
    h=struct.unpack_from('<I',b,i)[0];i+=4;n=h>>20
    if n==4095:n=struct.unpack_from('<I',b,i)[0];i+=4
    if h&1023==67:paras.append(b[i:i+n].decode('utf-16le','replace'))
    i+=n
  p.with_suffix('.txt').write_text('\n'.join(paras),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
def analyse():
 import pandas as pd
 rows=[]
 for stem in ['bujeon-main-bill','bujeon-facilities-bill']:
  book=pd.read_excel(OUT/(stem+'.xls'),sheet_name=None,header=None)
  for sheet,df in book.items():
   (OUT/(stem+'-'+sheet+'.csv')).write_text(df.fillna('').to_csv(index=False,header=False),encoding='utf-8-sig')
  df=book['내역서'].fillna('')
  for idx,r in df.iterrows():
   if isinstance(r[2],(float,int)) and r[2]>0 and str(r[3]).strip():
    rows.append({'source':stem+'.xls','sheet':'내역서','excel_row':idx+1,'item':str(r[0]).strip(),'specification':str(r[1]).strip(),'quantity':r[2],'unit':str(r[3]),'stage':'입찰 설계수량; 실제 설치·준공수량 아님'})
 pd.DataFrame(rows).to_csv(OUT/'bujeon-designed-quantities.csv',index=False,encoding='utf-8-sig')
 reuse=[]
 for rel in ['data/processed/후속입증-20260916/traffic/bdi-elder-transport.pdf','data/processed/고도화검증-20260916/traffic/traffic-resolution.json','data/processed/동별보완-추가근거-20260916/followup/evaluation-detail.json']:
  p=ROOT/rel
  reuse.append({'path':rel,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,'reused':p.exists()})
 (OUT/'reused-inputs.json').write_text(json.dumps(reuse,ensure_ascii=False,indent=2),encoding='utf-8')
 assert next(x for x in rows if x['item']=='투수블록포장')['quantity']==3222
 assert sum(x['quantity'] for x in rows if x['item']=='안전유도블록포장')==226
 print(json.dumps({'designRows':len(rows),'verified':'보도3222, 안전유도88+138=226; 공종별 수량은 중복단계이므로 총시설수로 합산하지 않음'},ensure_ascii=False))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');a.add_argument('url',nargs='?');x=a.parse_args()
 if x.name=='--analyse' or x.name=='analyse':analyse()
 else:fetch(x.name,x.url)
