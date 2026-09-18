"""Restore all call categories and describe districts without choosing a policy topic."""
from pathlib import Path
import hashlib, json
import pandas as pd

R=Path(__file__).resolve().parents[2]
N=R/'data/processed/신고인구특성재정립-20260917'
O=N/'calls';O.mkdir(parents=True,exist_ok=True)
B=R/'data/processed/동대응-전체결측제외-20260915/completeness'
D,NM,T,U,P,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
YEARS=list(range(2020,2025)); TYPES=['구급','구조','화재','기타']; OP=['업무운행','훈련출동','구급차소독']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((B/'manifest.json').read_text(encoding='utf8'))
hashes={x['file']:x['sha256'] for x in manifest['outputs']}
inputs=[]
def checked(p):
 h=sha(p);assert h==hashes[p.name],p
 inputs.append({'path':str(p.relative_to(R)),'sha256':h,'priorManifestMatch':True})
def dump(name,obj):
 (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
spec={'period':YEARS,'unit':'신고 접수 기록; 사건·환자·출동·주민당 위험 아님',
 'mainScope':'17개 완전행 중 정상, 운영성3분류 제외(C), 벌집제거 제외(P)',
 'allCategories':'세부유형 사전5개 제한 철회. 모든 종별·세부유형을 보존; 벌집제거는 검산에만 보존.',
 'population':'별도 MOIS12월말 전체연령, 신고자 연령으로 변환 안함. 주민수로 나누지 않음.',
 'profile':'유형별 비중·지역을 뺀 부산 비중·달력보정 시간·선택 민감도를 병렬 제시. 점수·군집·위험순위 없음.',
 'comparison':'core8 비교집합과 complete17을 구분. A/B/C 각 벌집 제외의 종별구성 변화 확인.',
 'aboveRest':'해당 종별의 지역비중이 같은 조건 나머지 부산비중보다 큰가. 통계적 유의성 판정 아님.',
 'time':'P조건 전체 종별. 월요일0,토일주말; 같은길이 00–03/04–07/08–11/12–15/16–19/20–23시.',
 'existingCorrection':'기존5유형41,720건 내부 규모로 교통 중심을 정한 선택논리는 본 분석에 사용하지 않음.'}
dump('specification.json',spec)
path=B/'original_region_classification.csv';checked(path)
old=pd.read_csv(path,keep_default_na=False)
assert set(old['scope'])==set('ABC')
# The validated cache predates the final terminology. Check its provisional17
# rows against the actual complete-17 records below before reusing the counts.
assert {'core8','provisional17'}.issubset(set(old['stage']))
old=old[old['stage'].isin(['core8','provisional17'])].copy()
old['stage']=old['stage'].replace({'provisional17':'complete17'})
spec['cachedStageAlias']='original_region_classification.csv의 provisional17은 작업상 complete17로 표기; 실제 17개 완전행과 연도×구군×동명×종별×세부유형별 전수 대조 후 재사용.'
dump('specification.json',spec)
frames=[]
for y in YEARS:
 p=B/f'complete_17_{y}.csv.gz';checked(p)
 f=pd.read_csv(p,usecols=[D,NM,T,U,P,DT],dtype=str,keep_default_na=False)
 ts=pd.to_datetime(f[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert ts.dt.year.eq(y).all()
 f=f.drop(columns=DT);f['year']=y;f['month']=ts.dt.month;f['weekday']=ts.dt.dayofweek;f['hourBand']=ts.dt.hour//4
 frames.append(f)
f=pd.concat(frames,ignore_index=True);assert len(f)==704689
scopes={'A':f,'B':f[f[P].eq('정상')],'C':f[f[P].eq('정상')&~f[U].isin(OP)]}
assert [len(scopes[s]) for s in 'ABC']==[704689,579412,574662]
audits=[]
for scope,x in scopes.items():
 expected=old[(old.scope==scope)&(old.stage=='complete17')].groupby(['year',D,NM,T,U])['count'].sum().sort_index()
 actual=x.groupby(['year',D,NM,T,U]).size().sort_index()
 assert actual.equals(expected),scope
 audits.append({'scope':scope,'all':len(x),'beehive':int(x[U].eq('벌집제거').sum()),'profile':int(x[U].ne('벌집제거').sum()),'cachedFullClassificationsMatch':True})
x=scopes['C'][scopes['C'][U].ne('벌집제거')].copy(); total=len(x)
assert x[U].eq('벌집제거').sum()==0
profileOld=old[old[U].ne('벌집제거')].copy()
city=x.groupby(T).size().reindex(TYPES,fill_value=0).to_dict()
districts=sorted(x[D].unique());assert len(districts)==16
sub=x.groupby([D,T,U]).size().rename('count').reset_index()
sub.to_csv(O/'district-all-subtypes.csv',index=False,encoding='utf-8-sig')
region=x.groupby([D,NM,T,U,'year']).size().rename('count').reset_index()
region.to_csv(O/'region-all-subtypes-by-year.csv',index=False,encoding='utf-8-sig')
citysub=x.groupby([T,U]).size().sort_values(ascending=False).rename('count').reset_index()
citysub['pctAllP']=100*citysub['count']/total
citysub.to_csv(O/'city-all-subtypes.csv',index=False,encoding='utf-8-sig')
calendar=pd.date_range('2020-01-01','2024-12-31');weekendDays=int((calendar.dayofweek>=5).sum());weekdayDays=len(calendar)-weekendDays
out=[];conditions=[];raw=[]
for district,g in x.groupby(D):
 n=len(g);counts=g.groupby(T).size().reindex(TYPES,fill_value=0).to_dict()
 r={'district':district,'count':n,'yearCounts':[int(g.year.eq(y).sum()) for y in YEARS], 'types':{},'topSubtypes':[], 'topNonEMS':{}}
 for t in TYPES:
  c=int(counts[t]);share=c/n;rest=(int(city[t])-c)/(total-n)
  evidence=[]
  for scope in 'ABC':
   for stage in ['core8','complete17']:
    z=profileOld[(profileOld.scope==scope)&(profileOld.stage==stage)]
    dn=int(z.loc[z[D].eq(district),'count'].sum());tn=int(z.loc[z[D].eq(district)&z[T].eq(t),'count'].sum());alln=int(z['count'].sum());allt=int(z.loc[z[T].eq(t),'count'].sum())
    a=tn/dn;b=(allt-tn)/(alln-dn)
    evidence.append({'scope':scope,'stage':stage,'count':tn,'denominator':dn,'share':a,'restShare':b,'aboveRest':a>b})
  selectedAnnual=[]
  for y in YEARS:
   gy=g[g.year.eq(y)];cy=x[x.year.eq(y)];nc=len(gy);tc=int(gy[T].eq(t).sum());allc=len(cy);at=int(cy[T].eq(t).sum())
   selectedAnnual.append({'year':y,'count':tc,'share':tc/nc,'restShare':(at-tc)/(allc-nc),'aboveRest':tc/nc>(at-tc)/(allc-nc)})
  r['types'][t]={'count':c,'share':share,'restShare':rest,'differencePp':100*(share-rest),'aboveRestAll6':all(z['aboveRest'] for z in evidence),'aboveRestConditions':sum(z['aboveRest'] for z in evidence),'annualAboveRestYears':sum(z['aboveRest'] for z in selectedAnnual),'annual':selectedAnnual}
  conditions.extend([{'district':district,'type':t,**z} for z in evidence])
  top=g[g[T].eq(t)][U].value_counts()
  r['topNonEMS'][t]=[{'subtype':u,'count':int(v),'withinTypeShare':int(v)/c if c else None} for u,v in top.head(4).items()]
 r['topSubtypes']=[{'type':t,'subtype':u,'count':int(v),'share':int(v)/n} for (t,u),v in g.groupby([T,U]).size().sort_values(ascending=False).head(5).items()]
 hour=g.hourBand.value_counts().reindex(range(6),fill_value=0);peak=int(hour.max());r['hourCounts']=[int(v) for v in hour];r['peakHourBands']=[int(k) for k,v in hour.items() if v==peak]
 r['monthCounts']=[int(g.month.eq(m).sum()) for m in range(1,13)];r['weekdayCounts']=[int(g.weekday.eq(k).sum()) for k in range(7)]
 we=int(g.weekday.ge(5).sum());wd=n-we;r['weekendPerDay']=we/weekendDays;r['weekdayPerDay']=wd/weekdayDays;r['weekendWeekdayRatio']=r['weekendPerDay']/r['weekdayPerDay']
 r['retentionCNoBee']=n/int(profileOld.loc[(profileOld.scope=='C')&(profileOld.stage=='core8')&profileOld[D].eq(district),'count'].sum())
 assert sum(r['yearCounts'])==sum(r['hourCounts'])==sum(r['monthCounts'])==sum(r['weekdayCounts'])==n
 out.append(r)
 for name,q in g.groupby(NM):
  raw.append({'district':district,'rawDong':name,'count':len(q),'typeCounts':{t:int(q[T].eq(t).sum()) for t in TYPES},'yearCounts':[int(q.year.eq(y).sum()) for y in YEARS]})
dump('district-profiles.json',out);dump('raw-name-profiles.json',raw);dump('condition-comparison.json',conditions)
pd.DataFrame(conditions).to_csv(O/'condition-comparison.csv',index=False,encoding='utf-8-sig')
pd.DataFrame([{'district':r['district'],'count':r['count'],**{t+'Count':r['types'][t]['count'] for t in TYPES},**{t+'Pct':100*r['types'][t]['share'] for t in TYPES},'retentionPct':100*r['retentionCNoBee'],'peak4HourBands':r['peakHourBands'],'weekendWeekdayRatio':r['weekendWeekdayRatio']} for r in out]).to_csv(O/'district-summary.csv',index=False,encoding='utf-8-sig')
dump('manifest.json',{'inputs':inputs,'profileCount':total,'cityTypeCounts':{k:int(v) for k,v in city.items()},'cityTypeShares':{k:int(v)/total for k,v in city.items()},'audit':audits,'districtCount':16,'rawNames':len(raw),'subtypeCombinations':len(citysub),'calendar':{'days':len(calendar),'weekend':weekendDays,'weekday':weekdayDays},'pandas':pd.__version__})
print(json.dumps({'count':total,'types':{k:int(v) for k,v in city.items()},'audit':audits,'subtypeCombinations':len(citysub)},ensure_ascii=False))
for r in out:print(r['district'],r['count'],[(t,round(r['types'][t]['share']*100,1),r['types'][t]['aboveRestConditions']) for t in TYPES],r['topNonEMS']['구조'][:2],r['topNonEMS']['화재'][:2])
