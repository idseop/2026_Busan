"""Join verified district call composition and resident background, without risk scores."""
from pathlib import Path
import json, hashlib
import pandas as pd

R=Path(__file__).resolve().parents[2]
N=R/'data/processed/신고인구특성재정립-20260917'
O=N/'tables'; O.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf8'))
calls=read(N/'calls/district-profiles.json')
pop=read(N/'population/profiles.json')
meta=read(N/'calls/manifest.json')
P='CLMTY_SGG_NM';T='EMRG_RSCU_ASSRT_NM';U='EMRG_RSCU_CLSF_NM'
cache=R/'data/processed/동대응-전체결측제외-20260915/completeness/original_region_classification.csv'
z=pd.read_csv(cache,keep_default_na=False)
z=z[z.stage.isin(['core8','provisional17']) & z[U].ne('벌집제거')].copy()
z['stage']=z.stage.replace({'provisional17':'complete17'})
types=['구급','구조','화재','기타']
assert len(calls)==16 and len(pop['districts'])==80
rows=[];annual=[]
for c in calls:
 p=next(p for p in pop['summary2024'] if p['district']==c['district'])
 r={**p,'callCount2020To2024':c['count'],'retentionPct':100*c['retentionCNoBee']}
 for t in types:
  v=c['types'][t]
  r[t+'Count']=v['count'];r[t+'Pct']=100*v['share']
  r[t+'AboveRestConditions']=v['aboveRestConditions'];r[t+'AboveRestYears']=v['annualAboveRestYears']
 r['peak4HourBands']=' / '.join(f'{b*4:02}–{b*4+4:02}시' for b in c['peakHourBands'])
 r['weekendPerDayRatio']=c['weekendWeekdayRatio']
 rows.append(r)
 for i,y in enumerate(range(2020,2025)):
  pp=next(p for p in pop['districts'] if p['district']==c['district'] and p['year']==y)
  a={k:v for k,v in pp.items() if k not in ('ages','ageSharesPct','dongRows')}
  a.update(callCount=c['yearCounts'][i])
  for t in types:
   v=c['types'][t]['annual'][i]
   a[t+'Count']=v['count'];a[t+'Pct']=100*v['share']
  annual.append(a)
summary=pd.DataFrame(rows).sort_values('districtCode')
summary.to_csv(O/'구군별-신고특성과-2024주민구성.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(annual).sort_values(['year','districtCode']).to_csv(O/'구군별-같은연도신고와-연말주민-2020-2024.csv',index=False,encoding='utf-8-sig')

# Use the complete list of observed P subtype combinations, with explicit zeros.
combos=pd.read_csv(N/'calls/city-all-subtypes.csv')[[T,U]].itertuples(index=False,name=None)
combos=list(combos)
all_counts=z.groupby(['scope','stage',T,U])['count'].sum().to_dict()
all_den=z.groupby(['scope','stage'])['count'].sum().to_dict()
gu_counts=z.groupby(['scope','stage',P,T,U])['count'].sum().to_dict()
gu_den=z.groupby(['scope','stage',P])['count'].sum().to_dict()
gu_type=z.groupby(['scope','stage',P,T])['count'].sum().to_dict()
all_type=z.groupby(['scope','stage',T])['count'].sum().to_dict()
selected=z[(z.scope=='C')&(z.stage=='complete17')]
year_counts=selected.groupby(['year',P,T,U])['count'].sum().to_dict()
year_den=selected.groupby(['year',P])['count'].sum().to_dict()
year_all=selected.groupby(['year',T,U])['count'].sum().to_dict()
year_all_den=selected.groupby('year')['count'].sum().to_dict()
out=[]
for d in summary.district:
 for t,u in combos:
  n=int(gu_counts.get(('C','complete17',d,t,u),0));den=int(gu_den['C','complete17',d])
  restn=int(all_counts.get(('C','complete17',t,u),0))-n;restd=int(all_den['C','complete17'])-den
  evidence=[];within=[]
  for scope in 'ABC':
   for stage in ['core8','complete17']:
    num=gu_counts.get((scope,stage,d,t,u),0);dd=gu_den[scope,stage,d]
    rn=all_counts.get((scope,stage,t,u),0)-num;rd=all_den[scope,stage]-dd
    evidence.append(num/dd>rn/rd)
    td=gu_type.get((scope,stage,d,t),0);trd=all_type.get((scope,stage,t),0)-td
    within.append(td>0 and trd>0 and num/td>rn/trd)
  ys=[int(year_counts.get((y,d,t,u),0)) for y in range(2020,2025)]
  aboveYears=sum(ys[i]/year_den[y,d]>(year_all.get((y,t,u),0)-ys[i])/(year_all_den[y]-year_den[y,d]) for i,y in enumerate(range(2020,2025)))
  out.append({'district':d,'type':t,'subtype':u,'count':n,'districtDenominator':den,'pctDistrict':n/den*100,'pctRestBusan':restn/restd*100,
   'withinTypePct':100*n/gu_type['C','complete17',d,t], 'aboveRestConditions':int(sum(evidence)), 'withinTypeAboveRestConditions':int(sum(within)),
   'aboveRestYears':int(aboveYears),'observedYears':sum(v>0 for v in ys),**{str(y):ys[i] for i,y in enumerate(range(2020,2025))}})
sub=pd.DataFrame(out)
assert sub['count'].sum()==meta['profileCount']
sub.to_csv(O/'구군별-전체70유형-반복과선택영향.csv',index=False,encoding='utf-8-sig')

lines=['# 16개 구·군 신고 특성과 주민 연령 구성','',
 '신고: 2020~2024년 선택 17개 컬럼 결측 제외 후 정상 처리, 운영성 3분류와 벌집제거 제외 **555,786건**. 신고접수 기록이며 실제 사건·환자 수가 아니다.',
 '주민: 2024년 12월 말. 신고 비중과 주민 비중은 서로 다른 분모이며, 주민 연령을 신고자 연령으로 해석하지 않는다. 각 연도 신고와 해당 연말 주민을 연결한 80행 별도 CSV도 제공한다.','',
 '| 구·군 | 신고 건수 | 구급 % | 구조 % | 화재 % | 기타 % | 2024 주민 수 | 0~14세 % | 15~39세 % | 40~64세 % | 65세 이상 % |',
 '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for r in summary.to_dict('records'):
 lines.append('| '+r['district']+' | '+f"{r['callCount2020To2024']:,}"+' | '+' | '.join(f'{r[t+"Pct"]:.1f}' for t in types)+' | '+f"{r['total']:,}"+' | '+' | '.join(f'{r[k]:.1f}' for k in ['pct_0_14','pct_15_39','pct_40_64','pct_65_plus'])+' |')
lines+=['','## 시간과 선택 영향','',
 '모든 종별을 합친 접수 시각. 4시간대는 길이가 같으며, 주말/평일은 관측기간의 토·일 522일과 평일 1,305일로 각각 나눈 일수당 접수의 비율이다. 공휴일 효과는 별도로 분리하지 않았다.','',
 '| 구·군 | 가장 많은 4시간대 | 주말/평일 일수당 비 | 비교집합 대비 잔존율 |', '|---|---|---:|---:|']
for r in summary.to_dict('records'):
 lines.append(f"| {r['district']} | {r['peak4HourBands']} | {r['weekendPerDayRatio']:.3f} | {r['retentionPct']:.1f}% |")
lines+=['','잔존율은 같은 정상·운영성 제외·벌집 제외 조건의 core8 비교집합 대비 값이다. 전체 원본 대비 비율과 다르다. 시간대 최댓값이 바로 인력 부족 또는 추가 운영 필요성을 뜻하지 않는다.','',
 '## 세부유형과 검증 표 읽기','',
 '`구군별-전체70유형-반복과선택영향.csv`는 종별과 세부유형을 함께 구분한 70조합×16구군=1,120행이다. `pctDistrict`는 지역 전체 신고 대비, `withinTypePct`는 해당 종별 대비다. `aboveRestConditions`는 결측 제외 전후×3처리조건에서 해당 지역을 제외한 나머지 부산보다 지역 전체 대비 비중이 높은 조건 수(0~6)다. `aboveRestYears`는 주 분석조건의 5개 연도에서 비중이 높은 연도 수다. 통계적 유의성 검정이나 위험 점수가 아니다.','',
 '연령별 실제 인원과 비중 101개 값은 population 출력에 보존했다. 15~39세 등 표시 구간은 분포를 읽기 위한 요약 구간이며 정책의 법적 대상 연령을 정한 것이 아니다.']
(O/'구군별-결과표.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
used=[N/'calls/district-profiles.json',N/'calls/manifest.json',N/'calls/city-all-subtypes.csv',N/'population/profiles.json',cache]
manifest={'inputs':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in used],
 'rows':{'districtSummary':len(summary),'districtYear':len(annual),'districtSubtype':len(sub)},'noPatientAgeInference':True,'noRiskScore':True,'noBeehiveFocus':True,
 'sourceAlias':'provisional17 means the rows independently reconciled to actual complete_17 files in calls/manifest.json',
 'outputs':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.iterdir() if p.is_file() and p.name!='manifest.json']}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(manifest['rows']))
print(sub[(sub.type=='구급')&sub.subtype.isin(['질병','질병외'])][['district','subtype','count','pctDistrict','aboveRestConditions','aboveRestYears']].to_string(index=False))
