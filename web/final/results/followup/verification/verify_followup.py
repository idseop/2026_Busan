"""Recompute author's all-region aggregates from source complete17 gzip files."""
from pathlib import Path
import json,hashlib,datetime,collections
import pandas as pd
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
B=ROOT/'data/processed/후속입증-20260916/analysis'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def ck(n,a,b):
 ok=abs(a-b)<1e-10 if isinstance(a,float) and isinstance(b,(int,float)) else a==b
 checks.append({'name':n,'passed':bool(ok)})
 if not ok:print('FAIL',n,str(a)[:150],str(b)[:150])
data=load(B/'all-region-followup.json')
for r in load(B/'manifest.json')['inputs']:ck('input hash '+r['path'],sha(ROOT/r['path']),r['sha256'])
key=['CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'];frames=[]
for y in range(2020,2025):
 p=ROOT/f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{y}.csv.gz'
 f=pd.read_csv(p,usecols=key+['DCLR_DT','PRCS_RSLT_SE_NM'],dtype=str,keep_default_na=False)
 dates=pd.to_datetime(f.pop('DCLR_DT').str.strip(),format='%Y%m%d%H%M%S');f['year']=dates.dt.year;f['month']=dates.dt.month;f['weekday']=dates.dt.dayofweek;f['hour']=dates.dt.hour
 ck('source year '+str(y),bool(f.year.eq(y).all()),True);frames.append(f)
f=pd.concat(frames,ignore_index=True)
ck('original total',len(f),704689);ck('observed region names',len(f[key[:2]].drop_duplicates()),194)
st=pd.read_csv(ROOT/'data/processed/완전행-분석적합성-20260915/stability/all_original_dong_subtype_sensitivity.csv').set_index(['scope']+key)
scopeframes={'A':f,'B':f[f.PRCS_RSLT_SE_NM=='정상'],'C':f[(f.PRCS_RSLT_SE_NM=='정상')&(~f[key[3]].isin(['업무운행','훈련출동','구급차소독']))]}
ck('catalogue rows',len(data['catalogue']),2910)
independent={}
for scope,g in scopeframes.items():
 ck(scope+' total',len(g),{'A':704689,'B':579412,'C':574662}[scope])
 grouped={k:v for k,v in g.groupby(key)};totals=g.groupby(key[:2]).size().to_dict()
 for r in [r for r in data['catalogue'] if r['scope']==scope]+[r for r in data['buildingContext'] if r['scope']==scope]:
  k=(r['district'],r['rawDong'],r.get('type','화재'),r['subtype']);x=grouped.get(k,g.iloc[:0]);tag=scope+'/'+ '/'.join(k)
  annual=x.groupby('year').size().reindex(range(2020,2025),fill_value=0).tolist()
  ck(tag+' years',r['yearCounts'],annual);ck(tag+' count',r['count'],len(x))
  old=st.loc[(scope,)+k] if (scope,)+k in st.index else None
  before=[int(old[f'core8_{y}']) for y in range(2020,2025)] if old is not None else [0]*5
  ck(tag+' before',r.get('beforeComparisonYearCounts',r.get('beforeYearCounts')),before)
  ck(tag+' direction',r['directionReversal'],(before[-1]-before[0])*(annual[-1]-annual[0])<0)
  ck(tag+' retention',r['retention'],len(x)/sum(before) if sum(before) else None)
  if 'monthCounts' not in r:continue
  ck(tag+' region total',r['regionAllTypes'],int(totals.get(k[:2],0)))
  ck(tag+' share',r['regionShare'],len(x)/totals[k[:2]] if totals.get(k[:2]) else None)
  for col,field,levels in [('month','monthCounts',range(1,13)),('hour','hourCounts',range(24)),('weekday','weekdayCounts',range(7))]:ck(tag+' '+field,r[field],x.groupby(col).size().reindex(levels,fill_value=0).tolist())
  ck(tag+' repeatedBefore',r['repeatedBefore'],min(before)>0);ck(tag+' repeatedAfter',r['repeatedAfter'],min(annual)>0)
  ck(tag+' geography',r['geographyConfirmed'],False)
  ratios=[]
  for lo,hi in [(2020,2022),(2023,2024)]:
   first=datetime.date(lo,1,1);last=datetime.date(hi,12,31);days=(last-first).days+1
   we_days=sum((first+datetime.timedelta(days=i)).weekday()>=5 for i in range(days));wd_days=days-we_days
   xx=x[x.year.between(lo,hi)];we=int((xx.weekday>=5).sum());wd=len(xx)-we
   ratio=we*wd_days/(wd*we_days) if wd else None;ratios.append(ratio)
   ck(tag+' ratio '+str(lo),r[f'weekendRatio{lo}_{hi}'],ratio)
  independent[(scope,)+k]={'years':annual,'before':before,'reversal':(before[-1]-before[0])*(annual[-1]-annual[0])<0,'ratios':ratios}
domains={(r['type'],r['subtype']) for r in data['catalogue']}
c=scopeframes['C'];mask=pd.Series(list(zip(c[key[2]],c[key[3]])),index=c.index).isin(domains)
expected=c[mask].groupby(key+['year','weekday','hour']).size().sort_index()
cross=pd.read_csv(B/'all_region_year_weekday_hour_C.csv').rename(columns=dict(zip(['district','rawDong','type','subtype'],key)))
actual=cross.set_index(key+['year','weekday','hour'])['count'].sort_index()
ck('entire exact hour cross',actual.equals(expected),True);ck('cross rows',len(cross),34377);ck('cross total',int(actual.sum()),len(c[mask]))
combos={k[1:] for k in independent if k[0]=='C'}
stable=[]
for k in combos:
 rs=[independent[(s,)+k] for s in 'ABC']
 if all(min(r['years'])>0 and min(r['before'])>0 and not r['reversal'] for r in rs):stable.append(rs[2])
ck('stable combinations',len(stable),data['stabilityAcrossScopes']['combinations'])
for row in data['stabilityAcrossScopes']['timeSensitivity']:
 selected=[r for r in stable if min(r['years'])>=row['minimumEachYear']];pairs=[r['ratios'] for r in selected if None not in r['ratios']]
 for label,value in [('eligibleCombinations',len(selected)),('finiteRatioPairs',len(pairs)),('ratioCrossesOne',sum((a<1<b) or (b<1<a) for a,b in pairs)),('ratioCrosses09and11',sum((a<.9 and b>1.1) or (b<.9 and a>1.1) for a,b in pairs))]:ck(str(row['minimumEachYear'])+' '+label,row[label],value)
cov=load(ROOT/'data/processed/동별보완-추가근거-20260916/place/coverage_all_busan.json')['mois14']
ck('site count',len(data['inspectionSites']),14)
for s,original in zip(data['inspectionSites'],cov):
 for k,v in original.items():ck('site original '+s['place']+k,s[k],v)
 expected=[r for r in data['catalogue'] if r['scope']=='C' and r['type']=='구급' and r['subtype']=='교통사고' and r['district']==s['district'] and r['rawDong'] in s['lawNameCandidates']]
 ck('site name only '+s['place'],s['rawRegionComparisons'],expected)
 ck('site no assignment '+s['place'],'배정하거나 후보 동을 합산하지 않음' in s['comparisonMeaning'],True)
ck('sites with named receipt region',sum(bool(s['rawRegionComparisons']) for s in data['inspectionSites']),11)
result={'checks':checks,'passed':sum(r['passed'] for r in checks),'failed':[r for r in checks if not r['passed']],'rawCount':len(f),'crossCount':int(actual.sum()),'stable':len(stable),'scope':'독립 코드로 원본 전처리 5gzip 재집계; outdoor는 본인 작성이므로 이 검증 범위에서 제외'}
(OUT/'followup-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
assert not result['failed']
