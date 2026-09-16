"""Independent SEMAS input and aggregation audit (no author code imports)."""
from pathlib import Path
import json,hashlib,zipfile
import pandas as pd
R=Path(__file__).resolve().parents[4];B=R/'data/processed/후속입증-20260916/commerce';O=Path(__file__).parent
checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
load=lambda n:json.loads((B/n).read_text(encoding='utf-8'))
ctx=load('commerce-context.json'); m=load('source-manifest.json')
ck('primary pre-field snapshot',ctx['primarySnapshot']=='20240930' and ctx['fieldStudyDate']=='2024-10-26~2024-10-27')
ck('selected four snapshots',{a['snapshot'] for a in m['selectedInputs']}=={'20240331','20240630','20240930','20241231'})
frames={n:pd.read_csv(B/n,dtype=str,keep_default_na=False) for n in ['all-busan-categories.csv','all16-district-categories.csv','four-law-dong-categories.csv','four-law-dong-middle-categories.csv','four-area-snapshot-summary.csv','quarter-sensitivity.csv']}
for a in m['selectedInputs']:
 p=R/a['file'];z=zipfile.ZipFile(R/a['zip']);raw=p.read_bytes();ck('raw ZIP member '+a['snapshot'],hashlib.sha256(raw).hexdigest()==a['sha256']==hashlib.sha256(z.read(a['zipMember'])).hexdigest())
 f=pd.read_csv(p,dtype=str,keep_default_na=False)
 required=['상가업소번호','시도코드','시군구코드','시군구명','법정동코드','법정동명','상권업종대분류코드','상권업종대분류명','상권업종중분류코드','상권업종중분류명']
 missing=f[required].apply(lambda s:s.str.strip().eq('')).any(axis=1);outside=f['시도코드']!='26';u=f[~(missing|outside)]
 ck('inclusion ledger '+a['snapshot'],len(f)==a['originalRows'] and len(u)==a['includedRows'] and int(missing.sum())==a['missingRequiredRows'] and int(outside.sum())==a['outsideBusanRows'] and int((missing|outside).sum())==a['excludedUnionRows'])
 ck('ID and province/district '+a['snapshot'],not u['상가업소번호'].duplicated().any() and u['시군구코드'].nunique()==16 and (u['법정동코드'].str[:5]==u['시군구코드']).all())
 cat='상권업종대분류명';ck('ten categories '+a['snapshot'],u[cat].nunique()==10)
 for name in ['all-busan-categories.csv','all16-district-categories.csv','four-law-dong-categories.csv','four-law-dong-middle-categories.csv']:
  out=frames[name];out=out[out.snapshot==a['snapshot']]
  for _,r in out.iterrows():
   scope=u
   if 'district' in r:scope=scope[scope['시군구명']==r.district]
   if 'lawDong' in r:scope=scope[scope['법정동명']==r.lawDong]
   c='상권업종중분류명' if 'middle' in name else cat
   count=int((scope[c]==r.category).sum());den=len(scope)
   ck(name+a['snapshot']+r.category+str(r.get('district',''))+str(r.get('lawDong','')),count==int(r.shops) and den==int(r.denominatorShops) and abs(count/den*100-float(r.sharePct))<1e-9)
   if 'lawDongCode' in r:ck('legal code '+r.lawDong,scope['법정동코드'].unique().tolist()==[r.lawDongCode])
   if 'busanSameSnapshotSharePct' in r:
    bs=(u[cat]==r.category).sum()/len(u)*100;ck('same-period percentage point '+r.lawDong+r.category,abs(bs-float(r.busanSameSnapshotSharePct))<1e-9 and abs(count/den*100-bs-float(r.differenceFromBusanPercentagePoints))<1e-9)
  if name in ['all-busan-categories.csv','all16-district-categories.csv']:ck('total '+name+a['snapshot'],out.shops.astype(int).sum()==len(u))
 for _,r in frames['four-area-snapshot-summary.csv'].query('snapshot == @a["snapshot"]').iterrows():
  s=u[(u['시군구명']==r.district)&(u['법정동명']==r.rawDong)];ck('profile '+r.rawDong+a['snapshot'],len(s)==int(r.shops) and (s[cat]=='음식').sum()==int(r.foodShops) and (s[cat]=='소매').sum()==int(r.retailShops))
profiles=frames['four-area-snapshot-summary.csv']
for _,r in frames['quarter-sensitivity.csv'].iterrows():
 s=profiles[profiles.rawDong==r.rawDong];ck('quarter range '+r.rawDong,s.shops.astype(int).min()==int(r.minQuarterShops) and s.shops.astype(int).max()==int(r.maxQuarterShops) and abs(s.foodRetailSharePct.astype(float).min()-float(r.minFoodRetailSharePct))<1e-9 and abs(s.foodRetailSharePct.astype(float).max()-float(r.maxFoodRetailSharePct))<1e-9)
ck('primary Busan and four names',ctx['primaryBusanShops']==143964 and {p['rawDong']:p['shops'] for p in ctx['profiles']}=={'부전동':6216,'대연동':4314,'광안동':3203,'신평동':1081})
ck('output row contracts',len(frames['all16-district-categories.csv'])==640 and len(frames['four-law-dong-categories.csv'])==160)
result={'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks,'scope':'4분기 원 CSV/원 ZIP 부산 멤버 및 별도 집계 대조. 업소수는 방문량·사고노출량이 아님.'}
(O/'commerce-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False));assert not result['failed']
