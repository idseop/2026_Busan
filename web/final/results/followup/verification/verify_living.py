"""Independent month-cell and population-background verification."""
from pathlib import Path
import json,hashlib
import pandas as pd
R=Path(__file__).resolve().parents[4];B=R/'data/processed/후속입증-20260916/living';V=Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'));ctx=load(B/'living-context.json');checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
vals=['평균주거인구수','평균직장인구수','평균방문인구수'];means={};uses={}
for a,kind,key,n in zip(ctx['audits'],['hour','age'],['시간대','나이대'],[24,6]):
 p=R/a['path'];ck('source hash '+kind,hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'])
 f=pd.read_excel(p,dtype=str);s=f[f['기준년월'].str.startswith('2024')].copy();keys=['기준년월','행정동코드',key]
 ck('source ledger '+kind,len(f)==a['allRows'] and len(s)==a['selectedRows']==205*12*n and len(f)-len(s)==a['outside2024Rows'])
 ck('keys '+kind,not s.duplicated(keys).any() and s['기준년월'].nunique()==12 and s['행정동코드'].nunique()==205 and s.groupby(['기준년월','행정동코드']).size().eq(n).all())
 exported=pd.read_csv(B/f'all205-{kind}-2024-monthly.csv',dtype=str)
 for v in vals:s[v]=pd.to_numeric(s[v]);exported[v]=pd.to_numeric(exported[v])
 ck('all selected cells '+kind,s.reset_index(drop=True).equals(exported.reset_index(drop=True)))
 avg=s.groupby(['행정동코드','행정동명',key])[vals].agg(lambda x:sum(x)/len(x)).sort_index();pub=pd.read_csv(B/f'all205-{kind}-monthly-mean.csv',dtype={'행정동코드':str,key:str}).set_index(['행정동코드','행정동명',key]).sort_index()
 ck('all mean indexes '+kind,avg.index.equals(pub.index))
 for v in vals:ck('all mean cells '+kind+v,((avg[v]-pub[v]).abs()<1e-7).all())
 ck('equal month weights '+kind,(pub.months==12).all() and pub.aggregation.str.contains('동일 가중').all())
 means[kind]=avg.reset_index();uses[kind]=s
for p in ctx['allDongProfiles']:
 h=means['hour'][means['hour']['행정동코드']==p['code']];ck('profile matching name '+p['code'],set(h['행정동명'])=={p['name']})
 for v,label in zip(vals,['residential','workplace','visitor']):
  z=h.loc[h['시간대']=='00시',v].iloc[0];n=h.loc[h['시간대']=='12시',v].iloc[0];peak=h.loc[h[v].idxmax(),'시간대']
  ck('profile '+p['code']+label,abs(p[label+'00']-z)<1e-7 and abs(p[label+'12']-n)<1e-7 and abs(p[label+'NoonMidnightRatio']-n/z)<1e-9 and p[label+'PeakHour']==peak)
 m=uses['hour'];m=m[m['행정동코드']==p['code']].pivot(index='기준년월',columns='시간대',values='평균방문인구수');ck('monthly noon sensitivity '+p['code'],p['visitorNoonAboveMidnightMonths']==int((m['12시']>m['00시']).sum()))
dbp=R/ctx['reuseDashboard']['path'];db=load(dbp);orig=R/'data/processed/최종결과-20260915/dashboard.json';manifest=load(orig.parent/'manifest.json');ck('dashboard immutable verified',hashlib.sha256(dbp.read_bytes()).hexdigest()==ctx['reuseDashboard']['sha256']==next(x['sha256'] for x in manifest['outputs'] if x['path'].endswith('/dashboard.json')))
expected={(r['district'],r['rawDong'],c,len(r['candidateCodes'])) for r in db['rawRegions'] if r['year']==2024 and r['scope']=='C' for c in r['candidateCodes']};links=pd.read_csv(B/'raw-dong-candidate-links.csv',dtype={'candidateCode':str});got={(r.district,r.rawDong,r.candidateCode,r.candidateCount) for _,r in links.iterrows()};ck('all individual candidate links',got==expected and not links.geographyConfirmed.any())
for s in ctx['sources']:ck('official metadata hash '+s['url'],hashlib.sha256((R/s['path']).read_bytes()).hexdigest()==s['sha256'])
for n in ['official-hour-metadata.json','official-age-metadata.json']:
 text=load(B/n)['description'];ck('official definition '+n,all(t in text for t in ['전월','기지국','00 ~ 06','평일 09 ~ 18','30%']))
result={'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks,'scope':'생활인구 2024 원값·12기준월 동일가중 평균·시간비율·개별후보 대조. 실제인원·사고노출량이나 현재2026 추정 아님.'}
(V/'living-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False));assert not result['failed']
