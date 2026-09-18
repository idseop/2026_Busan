"""Aggregate-only full regional profiles and retrospective 2024 transfer check."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];O=R/'data/processed/지도입증확장-20260916/profiles';O.mkdir(parents=True,exist_ok=True)
inputs=[]
def load(path):
 p=R/path;inputs.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return json.loads(p.read_text(encoding='utf-8'))
def csvload(path):
 p=R/path;inputs.append({'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return pd.read_csv(p,dtype=str,keep_default_na=False)
def dump(name,x):(O/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def save(name,x):pd.DataFrame(x).to_csv(O/name,index=False,encoding='utf-8-sig')
spec={'fixedBeforeCalculation':'2026-09-16','scope':'2020–2024 선택 신고 C; ABC와 기초8 비교는 별도 민감도','universe':'기존 194원문지역×5예방유형. 벌집 제외; 위험등급 없음','holdout':'2020–2023 학습,2024 검증. 시간 연산은 연도별 월/계절 집계 재사용. 사후 holdout 점검이며 미래 예측 성능이나 정책효과 아님.','eligibility':'학습4년 모두 1건 이상. 2024=0도 목록에 보존하되 검증 분포/오차는 미정의. 2024건수로 적격한계 조정 안함.','baselines':['2024 계절 일수 비례(일별 균등)','동일유형 부산 나머지지역의 2020–23 일수당 분포를 2024달력에 환산'],'metric':'계절 구성비 평균절대오차(%p), 최고 일평균 계절 일치; 동률은 집합을 보존하여 교집합 여부. 건수 예측/위험 예측 아님.','support':'보조자료의 코드/명칭 후보는 개별 보존. 행정동 실제 사건 배정 아님. 상권 법정동전체,주택2024통계/2025경계,생활2023–24,시설현재는 각각 별도 시점.'}
spec['formulas']={'seasonOrder':['봄(3~5)','여름(6~8)','가을(9~11)','겨울(1·2·12)'],'projection':'p_s=(2020–23 count_s / calendarDays_s × 2024 calendarDays_s) / sum of those weights','actual':'q_s=2024 count_s/2024 total','MAEpp':'100×sum_s(abs(p_s-q_s))/4; 사례별 동일가중 평균','ties':'일수당 비율 최대값과 절대차1e-12 이내인 모든 계절을 보존','trainingSizeSensitivity':[1,5,20],'restBusan':'해당 지역을 제외한 동일 종별·세부유형 C조건의 기존194지역 합계. 부산 원신고 전체 모집단은 아님.'}
dump('specification.json',spec)
a=load('data/processed/후속입증-20260916/analysis/all-region-followup.json');t=load('data/processed/효과근거확장-20260916/temporal/temporal-transfer.json')['profiles'];dash=load('data/processed/최종결과-20260915/dashboard.json');cases=load('data/processed/통합완성-20260916/evidence/case-assessments.json')['cases']
commerce=csvload('data/processed/통합완성-20260916/context/commerce-all-geographies-total.csv');living=csvload('data/processed/통합완성-20260916/context/living-all205-yearly-hour-metrics.csv');housing=csvload('data/processed/후속입증-20260916/housing/housing_sum_audit.csv');aed=load('data/processed/동별보완-추가근거-20260916/services/aed-summary.json')
catalogue=a['catalogue'];bykey={(x['district'],x['rawDong'],x['subtype'],x['scope']):x for x in catalogue};raw=sorted(set((x['district'],x['rawDong']) for x in catalogue));assert len(raw)==194
annual={}
for p in t:annual[(p['district'],p['rawDong'],p['subtype'])]={int(w['window']):w for w in p['windows'] if w['window'] in ['2020','2021','2022','2023','2024']}
city={}
for key,years in annual.items():
 train=np.sum([years[y]['seasonCounts'] for y in range(2020,2024)],axis=0);city.setdefault(key[2],np.zeros(4));city[key[2]]+=train
hold=[];holdmap={};names=['봄','여름','가을','겨울']
for key,years in annual.items():
 train=np.sum([years[y]['seasonCounts'] for y in range(2020,2024)],axis=0);trainDays=np.sum([years[y]['seasonCalendarDays'] for y in range(2020,2024)],axis=0);test=np.array(years[2024]['seasonCounts']);testDays=np.array(years[2024]['seasonCalendarDays']);eligible=all(years[y]['count']>0 for y in range(2020,2024));valid=bool(eligible and test.sum()>0)
 def projected(v):
  weights=v/trainDays*testDays;return weights/weights.sum() if weights.sum() else np.zeros(4)
 local=projected(train);rest=projected(city[key[2]]-train);uniform=testDays/testDays.sum();actual=test/test.sum() if test.sum() else None
 row=dict(district=key[0],rawDong=key[1],subtype=key[2],trainCounts=int(train.sum()),testCount=int(test.sum()),trainEachYearPositive=eligible,comparisonEligible=valid,status='비교 가능' if valid else '학습4년 미반복' if not eligible else '2024 0건: 분포 미정의',trainSeasonCounts=train.astype(int).tolist(),testSeasonCounts=test.tolist(),trainSeasonDays=trainDays.tolist(),testSeasonDays=testDays.tolist(),predictedShare=local.tolist(),uniformShare=uniform.tolist(),restBusanShare=rest.tolist(),actualShare=actual.tolist() if actual is not None else None)
 if valid:
  tops=lambda values:[i for i,v in enumerate(values) if np.isclose(v,max(values),rtol=0,atol=1e-12)]
  trtops=tops(train/trainDays);tetops=tops(test/testDays);row.update(localMAEpp=float(np.mean(abs(local-actual))*100),uniformMAEpp=float(np.mean(abs(uniform-actual))*100),restBusanMAEpp=float(np.mean(abs(rest-actual))*100),trainingTopSeason=[names[i] for i in trtops],testTopSeason=[names[i] for i in tetops],topSeasonOverlap=bool(set(trtops)&set(tetops)))
 hold.append(row);holdmap[key]=row
save('holdout-2024.csv',[{k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in x.items()} for x in hold]);dump('holdout-2024.json',hold)
pop={(x['year'],x['code']):x for x in dash['population']};links={(x['district'],x['rawDong']):x for x in dash['rawRegions'] if x['year']==2024 and x['scope']=='C'};profiles=[];coverage=[]
for district,dong in raw:
 rows=[x for x in catalogue if x['scope']=='C' and x['district']==district and x['rawDong']==dong];rows.sort(key=lambda x:(-x['count'],x['subtype']));ln=links.get((district,dong),{});codes=ln.get('candidateCodes',[]);pops=[pop[(2024,c)] for c in codes if (2024,c) in pop]
 shops=commerce[(commerce.level=='lawDong')&commerce.district.eq(district)&commerce.lawDong.eq(dong)];single=shops.lawDongCode.nunique()==1;lv=living[living.year.isin(['2023','2024'])&living.code.isin(codes)];house=housing[housing.level.eq('dong')&housing.district.eq(district)&housing.name.isin([p['name'] for p in pops])]
 case=[x for x in cases if x['district']==district and x['rawDong']==dong];sites=[x for x in a['inspectionSites'] if x['district']==district and dong in x.get('lawNameCandidates',[])];aedrows=[x for x in aed if x['region']==dong]
 env={'residentCandidates':len(pops),'livingCandidates':lv.code.nunique(),'commerceExactLawCode':single,'commerceSnapshots':len(shops) if single else 0,'housingCandidateNames':len(house),'aedOperatingEvidence':len(aedrows)>0,'officialCaseEvidence':len(case)>0,'officialInspectionSites':len(sites)}
 coverage.append({'district':district,'rawDong':dong,**env,'candidateCodes':'|'.join(codes),'actualReceiptDongConfirmed':False})
 types=[]
 for x in rows:
  abc={s:bykey[(district,dong,x['subtype'],s)]['count'] for s in ['A','B','C']};h=holdmap[(district,dong,x['subtype'])];highest=np.flatnonzero(np.array(x['hourCounts'])==max(x['hourCounts'])).tolist() if x['count'] else []
  types.append({'subtype':x['subtype'],'major':x['type'],'count':x['count'],'sharePct':100*x['count']/x['regionAllTypes'] if x['regionAllTypes'] else None,'denominatorAllTypes':x['regionAllTypes'],'yearCounts':x['yearCounts'],'hours':x['hourCounts'],'months':x['monthCounts'],'peakHours':highest,'scopes':abc,'core8Comparison':{'years':x['beforeComparisonYearCounts'],'retention':x['retention'],'directionReversal':x['directionReversal'],'repeatedBefore':x['repeatedBefore'],'repeatedAfter':x['repeatedAfter']},'holdout':h,'statement':f"{x['subtype']} {x['count']:,}건, 5년 중 {sum(v>0 for v in x['yearCounts'])}년 관측. "+('제외 전후 증가·감소 방향이 달라졌다.' if x['directionReversal'] else '제외 전후 방향 반전은 확인되지 않았다.')})
 dominant=rows[0];resident=[{'code':p['code'],'name':p['name'],'year':2024,'total':p['total'],'ages':p['ages'],'shares':[100*v/p['total'] if p['total'] else 0 for v in p['ages']],'age65Plus':sum(p['ages'][65:])} for p in pops]
 profile={'district':district,'rawDong':dong,'scope':'C','period':'2020–2024','coverage':env,'populationCandidates':resident,'livingCandidates':lv.to_dict('records'),'commerceHistory':shops[['snapshot','shops']].to_dict('records') if single else [],'housingCandidates':house.to_dict('records'),'typeProfiles':types,'caseResults':case,'inspectionPlaces':[{'place':s['place'],'date':s['date'],'currentCompletion':s['currentCompletion']} for s in sites],'aedEvidence':aedrows,'headline':f"예방 관련 5유형 중 {dominant['subtype']} {dominant['count']:,}건이 가장 많이 관측됐다." if dominant['count'] else '예방 관련 5유형에서 남은 신고가 없다. 전체 신고가 없다는 뜻은 아니다.','denominatorNote':'5유형 내 최다이며 지역 위험 순위가 아니다. 구성비 분모는 해당 지역 전체 종별 C조건 신고.','geographyNote':'신고 지역명 집계. 주민·생활·주택 후보를 합치거나 실제 신고 위치로 확정하지 않는다.'}
 profiles.append(profile)
 profile['coverageDetails']={
 'resident':{'available':bool(pops),'reason':'2024 공식 코드 후보별 주민 구성; 복수 후보 합산 안함' if pops else '2024 공식 코드 후보가 없어 연결 보류'},
 'living':{'available':not lv.empty,'reason':'2023·2024 해당 후보 코드별 시간 배경; 신고자·등산객 아님' if not lv.empty else '동일 공식 후보 코드 자료 연결 없음'},
 'commerce':{'available':single,'reason':'구·군과 법정동 명칭 및 단일 코드 일치; 실제 신고 상점 배정 아님' if single else '동일 구·군 법정동 명칭 단일 코드 대응 없음'},
 'housing':{'available':not house.empty,'reason':'구·군과 주민 후보명이 같은 2024 주택통계; 2025경계 기준으로 신고 위치 확정 아님' if not house.empty else '보유 주택통계와 구·군·주민 후보명 대응 없음'},
 'aed':{'available':bool(aedrows),'reason':'기존 공식 운영시간 실조사 범위' if aedrows else '지역별 운영시간 실조사 범위 밖; AED 부재를 뜻하지 않음'},
 'case':{'available':bool(case),'reason':'지역·유형별 공식 대응 심층 근거 확보' if case else '지역별 확정 보완안을 제시할 공식 운영·현장 대조 미완료'}}
dump('regional-profiles.json',{'meta':spec,'profiles':profiles});save('coverage-194.csv',coverage)
df=pd.DataFrame(hold);valid=df[df.comparisonEligible];by=[]
for subtype,g in valid.groupby('subtype'):
 by.append({'subtype':subtype,'eligible':len(g),'topSeasonOverlap':int(g.topSeasonOverlap.sum()),'overlapPct':100*g.topSeasonOverlap.mean(),'localMAEpp':g.localMAEpp.mean(),'uniformMAEpp':g.uniformMAEpp.mean(),'restBusanMAEpp':g.restBusanMAEpp.mean(),'localBetterThanUniform':int((g.localMAEpp<g.uniformMAEpp).sum()),'localBetterThanRest':int((g.localMAEpp<g.restBusanMAEpp).sum())})
save('holdout-summary.csv',by)
strata=[]
for floor in [1,5,20]:
 eligible_keys={k for k,v in annual.items() if min(v[y]['count'] for y in range(2020,2024))>=floor}
 subset=valid[valid.apply(lambda r:(r.district,r.rawDong,r.subtype) in eligible_keys,axis=1)]
 for subtype,g in subset.groupby('subtype'):
  strata.append({'minimumTrainingAnnualCount':floor,'subtype':subtype,'comparisons':len(g),'median2024Count':float(g.testCount.median()),'localMAEpp':float(g.localMAEpp.mean()),'uniformMAEpp':float(g.uniformMAEpp.mean()),'restBusanMAEpp':float(g.restBusanMAEpp.mean())})
save('holdout-training-size-sensitivity.csv',strata)
for floor in [1,5,20]:
 for subtype in sorted(city):
  if not any(r['minimumTrainingAnnualCount']==floor and r['subtype']==subtype for r in strata):strata.append({'minimumTrainingAnnualCount':floor,'subtype':subtype,'comparisons':0,'median2024Count':None,'localMAEpp':None,'uniformMAEpp':None,'restBusanMAEpp':None})
strata.sort(key=lambda r:(r['minimumTrainingAnnualCount'],r['subtype']))
save('holdout-training-size-sensitivity.csv',strata)
representatives=[p for p in profiles if p['caseResults']]
save('representative-case-cards.csv',[{'district':p['district'],'rawDong':p['rawDong'],'subtype':c['subtype'],'count':c['observation']['count'],'background':c['context'],'existingResponse':c['existingResponse'],'proposal':c['proposal'],'status':c['status'],'trainingTopSeason':'|'.join(holdmap[(p['district'],p['rawDong'],c['subtype'])].get('trainingTopSeason',[])),'actual2024TopSeason':'|'.join(holdmap[(p['district'],p['rawDong'],c['subtype'])].get('testTopSeason',[]))} for p in representatives for c in p['caseResults']])
summary={'regionCount':len(profiles),'typeCombinations':len(hold),'trainingEligible':int(df.trainEachYearPositive.sum()),'distributionComparisons':len(valid),'testZeroAmongTrainingEligible':int((df.trainEachYearPositive&df.testCount.eq(0)).sum()),'coverage':{k:sum(bool(x[k]) for x in coverage) for k in env},'holdoutSummary':by,'trainingSizeSensitivity':strata,'interpretation':'지역의 과거 계절분포가 다음해에도 유지되는지 별도 검증했다. 유형 전체 평균에서 기준선보다 작지 않은 오차는 지역별 특정 계절 집중 안내를 일괄 채택할 근거가 아니다. 개별 조합의 우수 결과도 한 번의 2024 검증으로 확정하지 않는다. 위험 예측 성능 또는 정책 효과가 아니다.'}
dump('summary.json',summary);dump('input-manifest.json',inputs)
assert len(hold)==970 and len(profiles)==194
assert sum(x['count'] for p in profiles for x in p['typeProfiles'])==41720
assert all(sum(x['yearCounts'])==x['count']==sum(x['months'])==sum(x['hours']) for p in profiles for x in p['typeProfiles'])
assert all(abs(sum(x['predictedShare'])-1)<1e-10 for x in hold if x['trainCounts']>0)
assert all(abs(sum(x['actualShare'])-1)<1e-10 for x in hold if x['actualShare'] is not None)
dump('author-validation.json',{'status':'PASS','regions':194,'combinations':970,'CPreventionTotal':41720,'yearMonthHourTotalsAgree':True,'sharesNormalized':True,'reviewScope':'작성자 검사이며 독립 검증 별도','inputHashes':'input-manifest.json','notes':['2024값은 학습구성비 및 적격 학습건수 판단에 사용하지 않음','2024 0건 28개는 분포비교에서만 제외','훈련연도 각5/20 이상은 작은표본 영향 민감도; 결과에맞춘후보재선정아님']})
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'svg.fonttype':'none','font.size':11})
def figsave(fig,name):
 for ext in ['png','svg']:fig.savefig(O/(name+'.'+ext),dpi=160,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(11,6));labels={'residentCandidates':'2024 주민 후보','livingCandidates':'2023–24 생활 후보','commerceExactLawCode':'같은 구·법정동 상권','housingCandidateNames':'주민 후보명 주택 배경','aedOperatingEvidence':'AED 운영 조사','officialCaseEvidence':'공식 심층 사례','officialInspectionSites':'공식 점검 장소'};vals=[summary['coverage'][k] for k in labels];ax.barh(list(labels.values()),vals,color='#187d80');ax.invert_yaxis();ax.set_xlim(0,225)
for i,v in enumerate(vals):ax.text(v+2,i,str(v)+' / 194',va='center')
ax.set_title('194개 신고 지역명: 연결 가능한 배경의 범위가 다르다',pad=18);ax.set_xlabel('자료가 연결된 지역명 수 · 실제 사건 위치 확정 아님');figsave(fig,'coverage-194')
g=pd.DataFrame(by);fig,ax=plt.subplots(figsize=(12,7));fig.subplots_adjust(bottom=.25);pos=np.arange(len(g));w=.25
for i,(c,l,col) in enumerate([('localMAEpp','해당 지역 2020–23','#157a80'),('uniformMAEpp','달력일수 비례','#a8b5b8'),('restBusanMAEpp','부산 나머지 동일 유형','#b77935')]):ax.bar(pos+(i-1)*w,g[c],w,label=l,color=col)
ax.set_xticks(pos,[f"{x.subtype}\n비교 {x.eligible}조합" for x in g.itertuples()]);ax.set_ylabel('2024 계절 구성비 평균절대오차 (%p) · 낮을수록 일치');ax.set_title('지역별 과거 계절 구성은 2024년에 기준선보다 더 잘 유지되지 않았다');ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=3);fig.text(.1,.02,'학습4년 매년 1건 이상·2024 양수 조합의 동일가중 평균. 사후 시점분리 검증이며 위험 예측·정책 효과가 아니다.',fontsize=10);figsave(fig,'holdout-season-baselines')
fig,ax=plt.subplots(figsize=(11,5));ax.bar(g.subtype,g.overlapPct,color='#187d80');ax.set_ylim(0,110);ax.set_ylabel('학습 최고계절과 2024 최고계절이 겹친 조합 (%)');ax.set_title('반복 접수가 있어도 가장 많은 계절은 달라질 수 있다')
for i,r in enumerate(g.itertuples()):ax.text(i,r.overlapPct+2,f'{r.topSeasonOverlap}/{r.eligible}',ha='center')
fig.text(.1,-.02,'계절별 달력일수당 값 비교. 동률은 모두 보존해 교집합 여부로 판단하며 우연 일치율과 통계검정한 결과는 아니다.',fontsize=10);figsave(fig,'holdout-top-season')
(O/'results.md').write_text('# 전지역 프로파일과 2024 시점 분리 점검\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n194지역 모두에 같은 정책문장을 복사하지 않았다. 지역별 5유형 건수·전체신고 대비비중·5년 변화·월/24시간·포함조건·제외영향을 수치로 보존하고, 연결 가능한 배경과 공식 사례가 있는 범위를 별도로 표시했다.\n\n보조자료 없음은 서비스 없음이 아니다. 주택은 2024통계/2025경계의 후보명별 배경이고 신고를 재배정하지 않는다. 상권은 이름이 일치하는 법정동 전체이며 시장 구간과 다르다. 2025 생활자료는 이번 전지역 프로파일 비교에서 제외했다.\n\n2020–23→2024 비교는 이미 과거가 된 자료의 시점분리 검증이다. 이전9사례는2024까지 사용해 선정했으므로9사례만의 결과를독립미래평가로제시하지않는다. 전194×5조합에서동일기준을적용했다. 월/계절 기준을유리하게재선택하지않았고시설·인력최적화모형을실행하지않았다.\n',encoding='utf-8')
dump('output-manifest.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file() and p.name!='output-manifest.json'})
print(json.dumps(summary,ensure_ascii=False,indent=2))


