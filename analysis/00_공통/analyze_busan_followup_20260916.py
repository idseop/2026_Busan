"""Expand descriptive follow-up to every observed region; never assign calls to sites."""
from pathlib import Path
import json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/후속입증-20260916/analysis';OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
D,N,T,U,R,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
KEY=[D,N,T,U];YEARS=list(range(2020,2025))
DOMAINS=[('구급','심정지'),('화재','일반화재(주택)'),('구조','산악사고'),('구조','수난사고'),('구급','교통사고')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
manifest=read(BASE/'manifest.json'); hashes={x['file']:x['sha256'] for x in manifest['outputs']}
inputs=[];frames=[]
for y in YEARS:
 p=BASE/f'complete_17_{y}.csv.gz';h=sha(p);assert h==hashes[p.name]
 inputs.append({'path':str(p.relative_to(ROOT)),'sha256':h})
 f=pd.read_csv(p,usecols=KEY+[R,DT],dtype=str,keep_default_na=False)
 stamp=pd.to_datetime(f.pop(DT).str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert stamp.dt.year.eq(y).all()
 f['year']=y;f['month']=stamp.dt.month;f['weekday']=stamp.dt.dayofweek;f['hour']=stamp.dt.hour
 frames.append(f)
allf=pd.concat(frames,ignore_index=True)
scopes={'A':allf,'B':allf[allf[R].eq('정상')],'C':allf[allf[R].eq('정상')&~allf[U].isin(['업무운행','훈련출동','구급차소독'])]}
assert [len(scopes[s]) for s in 'ABC']==[704689,579412,574662]
stpath=ROOT/'data/processed/완전행-분석적합성-20260915/stability/all_original_dong_subtype_sensitivity.csv'
stmanifest=read(stpath.parent/'manifest.json')
assert sha(stpath)==next(x['sha256'] for x in stmanifest['output_files'] if x['file']==stpath.name)
st=pd.read_csv(stpath).set_index(['scope']+KEY);inputs.append({'path':str(stpath.relative_to(ROOT)),'sha256':sha(stpath)})
regions=sorted(set(zip(allf[D],allf[N])));assert len(regions)==194
calendar=pd.date_range('2020-01-01','2024-12-31');periods=[(2020,2022),(2023,2024)]
rows=[];cross=[];checks=[]
for scope,g in scopes.items():
 grouped={(d,n,t,u):x for (d,n,t,u),x in g.groupby(KEY)}
 totals=g.groupby([D,N]).size().to_dict()
 for d,n in regions:
  for t,u in DOMAINS:
   x=grouped.get((d,n,t,u),g.iloc[:0]);count=len(x)
   annual=[int(x.year.eq(y).sum()) for y in YEARS]
   old=st.loc[(scope,d,n,t,u)] if (scope,d,n,t,u) in st.index else None
   if old is not None:assert annual==[int(old[f'complete17_{y}']) for y in YEARS]
   else:assert count==0
   before=[int(old[f'core8_{y}']) for y in YEARS] if old is not None else [0]*5
   rec={'scope':scope,'district':d,'rawDong':n,'type':t,'subtype':u,'count':count,'regionAllTypes':int(totals.get((d,n),0)),
     'yearCounts':annual,'beforeComparisonYearCounts':before,'retention':count/sum(before) if sum(before) else None,
     'repeatedBefore':all(v>0 for v in before),'repeatedAfter':all(v>0 for v in annual),
     'directionReversal':bool(old.direction_reversal) if old is not None else False,'geographyConfirmed':False,
     'monthCounts':[int(x.month.eq(m).sum()) for m in range(1,13)],'hourCounts':[int(x.hour.eq(h).sum()) for h in range(24)],
     'weekdayCounts':[int(x.weekday.eq(w).sum()) for w in range(7)]}
   for lo,hi in periods:
    xx=x[x.year.between(lo,hi)];cal=calendar[calendar.year.to_series(index=calendar).between(lo,hi).values]
    we=int(xx.weekday.ge(5).sum());wd=len(xx)-we;wedays=int((cal.dayofweek>=5).sum());wddays=len(cal)-wedays
    rec[f'weekendRatio{lo}_{hi}']=(we/wedays)/(wd/wddays) if wd else None
   rec['regionShare']=count/rec['regionAllTypes'] if rec['regionAllTypes'] else None
   assert sum(rec['monthCounts'])==sum(rec['hourCounts'])==sum(rec['weekdayCounts'])==sum(annual)==count
   rows.append(rec)
   if scope=='C' and count:
    for (year,weekday,hour),v in x.groupby(['year','weekday','hour']).size().items():cross.append({'district':d,'rawDong':n,'type':t,'subtype':u,'year':int(year),'weekday':int(weekday),'hour':int(hour),'count':int(v)})
 checks.append({'scope':scope,'allCounts':len(g),'domainCounts':sum(r['count'] for r in rows if r['scope']==scope)})
print('catalogue',len(rows),'cross',len(cross),flush=True)
coveragepath=ROOT/'data/processed/동별보완-추가근거-20260916/place/coverage_all_busan.json'
coverage=read(coveragepath);inputs.append({'path':str(coveragepath.relative_to(ROOT)),'sha256':sha(coveragepath)})
sites=[]
for site in coverage['mois14']:
 matches=[]
 for dong in site['lawNameCandidates']:
  r=next((r for r in rows if r['scope']=='C' and r['district']==site['district'] and r['rawDong']==dong and r['type']=='구급' and r['subtype']=='교통사고'),None)
  if r:matches.append(r)
 sites.append({**site,'rawRegionComparisons':matches,'comparisonMeaning':'해당 동명으로 접수된 교통신고의 배경 비교. 점검지점 사고로 배정하거나 후보 동을 합산하지 않음.'})
grouped_rows={}
for r in rows:grouped_rows.setdefault((r['district'],r['rawDong'],r['type'],r['subtype']),[]).append(r)
stable=[v for v in grouped_rows.values() if all(r['repeatedBefore'] and r['repeatedAfter'] and not r['directionReversal'] for r in v)]
sensitivity=[]
for minimum in [1,5,10,20]:
 chosen=[next(x for x in v if x['scope']=='C') for v in stable if min(next(x for x in v if x['scope']=='C')['yearCounts'])>=minimum]
 pairs=[(r['weekendRatio2020_2022'],r['weekendRatio2023_2024']) for r in chosen if r['weekendRatio2020_2022'] is not None and r['weekendRatio2023_2024'] is not None]
 sensitivity.append({'minimumEachYear':minimum,'eligibleCombinations':len(chosen),'finiteRatioPairs':len(pairs),'ratioCrossesOne':sum((a-1)*(b-1)<0 for a,b in pairs),'ratioCrosses09and11':sum((a<.9 and b>1.1) or (b<.9 and a>1.1) for a,b in pairs),'meaning':'각 기준별 민감도; 정책 후보 통과선 아님. 0.9/1.1은 1배 주변 작은 변동을 별도 표시하기 위한 보조 비교.'})
building=[]
for scope,g in scopes.items():
 for district,dong in [('기장군','기장읍'),('동래구','온천동')]:
  subtype='고층건물(3층이상,아파트)';x=g[g[D].eq(district)&g[N].eq(dong)&g[T].eq('화재')&g[U].eq(subtype)]
  old=st.loc[(scope,district,dong,'화재',subtype)] if (scope,district,dong,'화재',subtype) in st.index else None
  annual=[int(x.year.eq(y).sum()) for y in YEARS];before=[int(old[f'core8_{y}']) for y in YEARS] if old is not None else [0]*5
  if old is not None:assert annual==[int(old[f'complete17_{y}']) for y in YEARS]
  building.append({'scope':scope,'district':district,'rawDong':dong,'subtype':subtype,'count':len(x),'yearCounts':annual,'beforeYearCounts':before,'retention':len(x)/sum(before) if sum(before) else None,'directionReversal':bool(old.direction_reversal) if old is not None else False,'relation':'추가로 확인한 고층건물 분류. 아파트만의 신고가 아니며 포털 등록 건물의 실제 발생 신고로 배정하지 않음.'})
data={'meta':{'period':'2020–2024','allSelected':704689,'scopeC':574662,'regionNames':194,'domainCombinationsPerScope':970,'noRiskRanking':True,'calendarDays':1827,'selection':'기존 5개 예방 관련 유형 × 관측된 전체 지역명. 관측 0도 남기며 정책 탈락 아님.','spatial':'구·동 이름 비교, 실제 신고 지점과 공식 점검 지점의 공간 결합 아님.'},'catalogue':rows,'inspectionSites':sites,'checks':checks,'stabilityAcrossScopes':{'combinations':len(stable),'timeSensitivity':sensitivity},'buildingContext':building}
(OUT/'all-region-followup.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
flat=[]
for r in rows:
 v={k:x for k,x in r.items() if not isinstance(x,list)}
 for y,n in zip(YEARS,r['yearCounts']):v[f'count_{y}']=n
 for y,n in zip(YEARS,r['beforeComparisonYearCounts']):v[f'before_{y}']=n
 flat.append(v)
pd.DataFrame(flat).to_csv(OUT/'all_194_regions_5_domains_3_scopes.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(cross).to_csv(OUT/'all_region_year_weekday_hour_C.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(sensitivity).to_csv(OUT/'time_threshold_sensitivity.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(building).to_csv(OUT/'building_type_comparison.csv',index=False,encoding='utf-8-sig')
(OUT/'manifest.json').write_text(json.dumps({'inputs':inputs,'script':str(Path(__file__).relative_to(ROOT)),'scriptSha256':sha(Path(__file__)),'outputs':[{'file':p.name,'sha256':sha(p)} for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'scopeChecks':checks,'sites':len(sites),'linkedSiteNames':sum(bool(s['rawRegionComparisons']) for s in sites)},ensure_ascii=False))
