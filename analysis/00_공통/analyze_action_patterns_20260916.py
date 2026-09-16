"""Reproducible prevention-domain exploration; counts are selected receipts, not risk."""
from pathlib import Path
import hashlib,json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/예방지원-근거분석-20260916/analysis'
BASE=ROOT/'data/processed/동대응-전체결측제외-20260915'
STAB=ROOT/'data/processed/완전행-분석적합성-20260915/stability'
YEARS=list(range(2020,2025)); SCOPES=['A','B','C']
D,N,T,U,R,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
KEY=[D,N,T,U]
DOMAINS=[('구급','심정지'),('화재','일반화재(주택)'),('구조','산악사고'),('구조','수난사고'),('구급','교통사고')]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x): (OUT/name).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 source=[]
 sm=json.loads((BASE/'completeness/manifest.json').read_text(encoding='utf-8'))
 expected={x['file']:x['sha256'] for x in sm['outputs']}
 stabpath=STAB/'all_original_dong_subtype_sensitivity.csv'
 previous=json.loads((STAB/'manifest.json').read_text(encoding='utf-8'))
 assert sha(stabpath)==next(x['sha256'] for x in previous['output_files'] if x['file']==stabpath.name)
 st=pd.read_csv(stabpath); st['total']=st[[f'complete17_{y}' for y in YEARS]].sum(axis=1)
 source.append({'path':str(stabpath.relative_to(ROOT)),'sha256':sha(stabpath),'role':'previous exclusion sensitivity aggregate'})
 c=st[st.scope.eq('C')].copy();selected=[];held=[]
 # Domain choice precedes temporal-profile inspection. Within-domain ordering is a
 # reproducible way to choose readable examples, explicitly not a policy ranking.
 for typ,sub in DOMAINS:
  candidates=c[c[T].eq(typ)&c[U].eq(sub)].sort_values(['total',D,N],ascending=[False,True,True])
  chosen=0
  for _,r in candidates.iterrows():
   ss=st.loc[(st[KEY]==r[KEY]).all(axis=1)]
   repeat=bool(ss.five_year_before.all() and ss.five_year_after.all())
   same_direction=not bool(ss.direction_reversal.any())
   if repeat and same_direction and chosen<2:
    selected.append(tuple(r[k] for k in KEY));chosen+=1
   else:
    held.append({'district':r[D],'rawDong':r[N],'type':typ,'subtype':sub,'countC':int(r.total),'reason': '결측 제외 전후 변화 방향 민감' if not same_direction else '5년 반복 조건 미충족' if not repeat else '동일 유형 2개 설명 사례 선정 범위 밖; 위험도 또는 정책 탈락 아님'})
 print('SELECTED',selected,flush=True)
 frames=[]
 for y in YEARS:
  p=BASE/f'completeness/complete_17_{y}.csv.gz';digest=sha(p);assert digest==expected[p.name]
  source.append({'path':str(p.relative_to(ROOT)),'sha256':digest,'priorManifestMatch':True})
  f=pd.read_csv(p,usecols=KEY+[R,DT],dtype=str,keep_default_na=False)
  stamp=pd.to_datetime(f[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert stamp.dt.year.eq(y).all()
  f['year']=y;f['hour']=stamp.dt.hour;f['weekday']=stamp.dt.dayofweek;f['month']=stamp.dt.month;f['date']=stamp.dt.normalize()
  frames.append(f.drop(columns=DT)); print(y,len(f),flush=True)
 full=pd.concat(frames,ignore_index=True);assert len(full)==704689
 dashboardpath=ROOT/'data/processed/최종결과-20260915/dashboard.json'
 dashboardmanifest=json.loads((dashboardpath.parent/'manifest.json').read_text(encoding='utf-8'))
 assert sha(dashboardpath)==next(x['sha256'] for x in dashboardmanifest['outputs'] if x['path'].endswith('/dashboard.json'))
 dashboard=json.loads(dashboardpath.read_text(encoding='utf-8'))
 source.append({'path':'data/processed/최종결과-20260915/dashboard.json','sha256':sha(ROOT/'data/processed/최종결과-20260915/dashboard.json'),'role':'existing aggregate reconciliation and conditional population linkage'})
 scopeframes={'A':full,'B':full[full[R].eq('정상')],'C':full[full[R].eq('정상')&~full[U].isin(['업무운행','훈련출동','구급차소독'])]}
 annual_rows=[];cross=[];profiles=[];checks=[];water_rows=[];domain_profiles=[]
 all_days=pd.date_range('2020-01-01','2024-12-31')
 def metrics(g,available):
  hour=g.groupby('hour').size().reindex(range(24),fill_value=0).astype(int).tolist()
  wd=g.groupby('weekday').size().reindex(range(7),fill_value=0).astype(int).tolist()
  mo=g.groupby('month').size().reindex(range(1,13),fill_value=0).astype(int).tolist()
  wd_days=[int((available.dayofweek==i).sum()) for i in range(7)]
  mo_days=[int((available.month==i).sum()) for i in range(1,13)]
  n=len(g);weekend=sum(wd[5:]);night=sum(hour[:6])+sum(hour[22:])
  return {'count':n,'yearCounts':[int(g.year.eq(y).sum()) for y in YEARS], 'hourCounts24':hour,'weekdayCounts7':wd,'monthlyCounts12':mo,
   'weekdayDays7':wd_days,'monthDays12':mo_days,'weekdayPerObservedDay7':[a/b if b else None for a,b in zip(wd,wd_days)],'monthPerObservedDay12':[a/b if b else None for a,b in zip(mo,mo_days)],
   'weekendCount':weekend,'weekendShare':weekend/n if n else None,'weekendPerObservedDay':weekend/sum(wd_days[5:]),'weekdayPerObservedDay':sum(wd[:5])/sum(wd_days[:5]),
   'night22to06Count':night,'night22to06Share':night/n if n else None,'observedDays':len(available),'calendarDays':len(all_days),'unobservedDates':[str(d.date()) for d in all_days.difference(available)]}
 for scope,g in scopeframes.items():
  counts=g.groupby(['year',T,U]).size().reset_index(name='count');counts['scope']=scope
  annual_rows.extend(counts.to_dict('records'))
  for y in YEARS:
   old=sum(r['count'] for r in dashboard['yearly'] if r['year']==y and r['scope']==scope)
   assert int(g.year.eq(y).sum())==old;checks.append({'check':'existing_annual','year':y,'scope':scope,'count':old})
  for typ,sub in DOMAINS:
   dg=g[g[T].eq(typ)&g[U].eq(sub)]
   domain_profiles.append({'scope':scope,'type':typ,'subtype':sub,**metrics(dg,pd.DatetimeIndex(sorted(g.date.unique())))})
  water=g[g[T].eq('구조')&g[U].eq('수난사고')]
  for area,w in [('부산',water)]+[(f'{d}|{n}',v) for (d,n),v in water.groupby([D,N])]:
   for y,v in [('all',w)]+[(str(y),v) for y,v in w.groupby('year')]:
    mmdd=v.date.dt.month*100+v.date.dt.day;inside=mmdd.between(704,830)
    days=all_days if y=='all' else all_days[all_days.year==int(y)];day_mmdd=days.month*100+days.day;inside_days=int(((day_mmdd>=704)&(day_mmdd<=830)).sum());outside_days=len(days)-inside_days
    water_rows.append({'scope':scope,'region':area,'year':y,'count':len(v),'withinCurrentSummerWindow':int(inside.sum()),'outsideCurrentSummerWindow':int((~inside).sum()),'julyAugustCount':int(v.month.isin([7,8]).sum()),'withinWindowCalendarDays':inside_days,'outsideWindowCalendarDays':outside_days,'withinPerCalendarDay':int(inside.sum())/inside_days,'outsidePerCalendarDay':int((~inside).sum())/outside_days,'comparisonStatus':'2026 자원봉사 모집공고상 활동기간(7/4~8/30)을 과거 달력에 대입; 전체 수상구조대 운영기간·당시 운영실적·미대응 건수 아님'})
 for i,(district,dong,typ,sub) in enumerate(selected):
  obj={'id':f'action-{i+1}','district':district,'rawDong':dong,'type':typ,'subtype':sub,
   'selectionReason':'예방 관련 5개 분류별 2개 설명 사례. 전체·정상·운영성 제외 3조건에서 제외 전후 5년 반복 및 변화 방향이 유지되는 조합 중 C조건 관측 규모순. 위험 순위 아님.',
   'scopeProfiles':{},'stability':{},'populationLinks':[]}
  for scope,g in scopeframes.items():
   available=pd.DatetimeIndex(sorted(g.date.unique()));city=g[g[T].eq(typ)&g[U].eq(sub)]
   local=city[city[D].eq(district)&city[N].eq(dong)];rest=city[~(city[D].eq(district)&city[N].eq(dong))]
   m=metrics(local,available);other=metrics(rest,available)
   allregion=g[g[D].eq(district)&g[N].eq(dong)]
   m['regionAllTypesCount']=len(allregion);m['regionSubtypeShare']=len(local)/len(allregion)
   m['restSameSubtype']=other;m['restAllTypesCount']=len(g)-len(allregion)
   m['restRegionSubtypeShare']=len(rest)/(len(g)-len(allregion))
   m['weekendShareDifferencePP']=100*(m['weekendShare']-other['weekendShare'])
   m['nightShareDifferencePP']=100*(m['night22to06Share']-other['night22to06Share'])
   obj['scopeProfiles'][scope]=m
   sr=st.loc[st.scope.eq(scope)&st[D].eq(district)&st[N].eq(dong)&st[T].eq(typ)&st[U].eq(sub)].iloc[0]
   old=[int(sr[f'complete17_{y}']) for y in YEARS]; assert m['yearCounts']==old
   core=[int(sr[f'core8_{y}']) for y in YEARS]
   obj['stability'][scope]={'core8YearCounts':core,'selected17YearCounts':old,'retention':sum(old)/sum(core),'directionReversal':bool(sr.direction_reversal),'repeatsBefore':bool(sr.five_year_before),'repeatsAfter':bool(sr.five_year_after)}
   for (y,w,h),n in local.groupby(['year','weekday','hour']).size().items():cross.append({'caseId':obj['id'],'scope':scope,'year':int(y),'weekday':int(w),'hour':int(h),'count':int(n)})
   checks.append({'check':'case_exact_hours_days_months_vs_previous_subtype','id':obj['id'],'scope':scope,'count':len(local),'passed':sum(m['hourCounts24'])==sum(m['weekdayCounts7'])==sum(m['monthlyCounts12'])==sum(old)})
  obj.update({k:v for k,v in obj['scopeProfiles']['C'].items() if k!='restSameSubtype'})
  obj['restSameSubtype']=obj['scopeProfiles']['C']['restSameSubtype']
  for y in YEARS:
   link=next((r for r in dashboard['rawRegions'] if r['year']==y and r['scope']=='C' and r['district']==district and r['rawDong']==dong),None)
   if link:obj['populationLinks'].append({'year':y,'candidateCodes':link['candidateCodes'],'uniqueCode':link['uniqueCode'],'codeLevelEligible':link['codeLevelEligible'],'geographyConfirmed':False})
  profiles.append(obj)
 pd.DataFrame(annual_rows).to_csv(OUT/'all_subtype_annual_scopes.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(cross).to_csv(OUT/'selected_case_year_weekday_exact_hour.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(held).to_csv(OUT/'selection_and_hold_reasons.csv',index=False,encoding='utf-8-sig')
 # Whole original-region catalogue, including unobserved region-domain combinations.
 catalogue=[]
 for (district,dong),reg in full.groupby([D,N]):
  for typ,sub in DOMAINS:
   ss=st[st[D].eq(district)&st[N].eq(dong)&st[T].eq(typ)&st[U].eq(sub)]
   cc=ss[ss.scope.eq('C')]
   record={'district':district,'rawDong':dong,'type':typ,'subtype':sub,'regionObservedYears':sorted(map(int,reg.year.unique())),'status':'해당 조건에서 관측된 신고 없음','countC':0,'candidateEligible':False}
   if len(cc):
    r=cc.iloc[0];same=not bool(ss.direction_reversal.any());rep=bool(ss.five_year_before.all() and ss.five_year_after.all())
    record.update({'status':'반복·방향 보존' if same and rep else '결측·처리조건 민감 또는 5년 반복 미충족','countC':int(r.total),'candidateEligible':same and rep,'yearCounts':[int(r[f'complete17_{y}']) for y in YEARS],'core8YearCounts':[int(r[f'core8_{y}']) for y in YEARS],'retention':float(r.total)/sum(int(r[f'core8_{y}']) for y in YEARS) if sum(int(r[f'core8_{y}']) for y in YEARS) else None,'directionPreservedAllScopes':same,'repeatedAllScopes':rep})
   record['selectedDetailedExample']=(district,dong,typ,sub) in selected
   catalogue.append(record)
 save('all_region_prevention_catalogue.json',catalogue)
 pd.DataFrame(catalogue).to_csv(OUT/'all_region_prevention_catalogue.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(water_rows).to_csv(OUT/'water_current_calendar_comparison.csv',index=False,encoding='utf-8-sig')
 payload={'meta':{'years':YEARS,'primaryScope':'C','scopeNames':{'A':'전체 처리','B':'정상 처리','C':'정상 처리·운영성 분류 제외'},'unit':'선택 조건의 신고접수 건; 사건·피해자·위험률 아님','spatialUnit':'구군+접수 지역명; 실제 행정동 배정 미확정','temporalPolicy':'야간 22~05시(8시간), 주말 토·일. 비율은 해당 지역 동일 세부유형 접수분모. 일수당 값은 해당 연도·조건에서 한 건 이상 접수가 존재한 날짜를 관측가능일로 사용; 무접수와 입력누락은 구분 불가. 다른 지역은 해당 지역을 제외한 부산의 같은 종별·세부유형. 인구 대비 신고율 미계산.','selectionPolicy':'시간분포를 보기 전에 5개 예방 관련 분류 지정. 3개 처리조건에서 결측 전후 5년 반복·증감방향 보존 조합 중 각 분류 관측수 상위2 예시. 대표표본/위험순위 아님. 범용 질병·질병외/부상은 세부 원인·개입대상 불명확하여 이번 심층 주제 확장에서 보류. 벌집제거 제외.','claimLimit':'현재 서비스 미충족·원인·효과·최근 신고 지속 여부 미입증. 운영 적용은 현행 운영자료와 별도 대조 필요.'},
  'summary':{'scopeTotals':{s:len(g) for s,g in scopeframes.items()},'subtypeAnnual':annual_rows,'totalRawRegions':int(full.groupby([D,N]).ngroups),'selectedExamples':len(profiles)},'domainProfiles':domain_profiles,'waterCalendarComparison':water_rows,'profiles':profiles,'heldList':held,'sourceEvidence':source}
 save('action-patterns.json',payload);save('validation.json',{'status':'passed','checks':checks,'sourceHashMatches':True,'sourceRows':len(full),'personalIdentifiersOrCoordinatesPublished':False,'independentReview':'requires separate verifier'})
 plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
 fig,axes=plt.subplots(5,2,figsize=(14,15),sharex=True)
 for ax,p in zip(axes.flat,profiles):
  m=p['scopeProfiles']['C'];o=m['restSameSubtype'];n=m['count'];rn=o['count']
  ax.plot(range(24),np.array(m['hourCounts24'])/n*100,color='#087b84',lw=2,label='선택 지역')
  ax.plot(range(24),np.array(o['hourCounts24'])/rn*100,color='#889bad',lw=1.4,label='부산 다른 지역·같은 유형')
  ax.set_title(f"{p['district']} {p['rawDong']} · {p['subtype']} ({n:,}건)",fontsize=11)
  ax.set_ylabel('유형 내부 구성비 (%)');ax.set_xticks([0,6,12,18,23]);ax.grid(alpha=.15);ax.legend(fontsize=8)
 fig.suptitle('반복된 신고의 시간 분포는 지역·유형별로 다르다\n2020–2024년 · 정상 처리·운영성 제외 · 접수 시각 · 위험도 비교 아님',fontsize=15)
 fig.tight_layout(rect=(0,0,1,.95))
 for ext in ['png','svg']:fig.savefig(OUT/f'case_hour_profiles.{ext}',dpi=150)
 plt.close(fig)
 fig,axes=plt.subplots(1,2,figsize=(14,6))
 for p in [d for d in domain_profiles if d['scope']=='C']:
  base=p['yearCounts'][0]
  axes[0].plot(YEARS,[100*v/base for v in p['yearCounts']],marker='o',label=p['subtype'])
  axes[1].plot(range(1,13),p['monthPerObservedDay12'],marker='.',label=p['subtype'])
 axes[0].set_title('분류별 5년 변화 · 2020년=100');axes[0].set_xticks(YEARS);axes[0].set_ylabel('신고 건수 지수')
 axes[1].set_title('월별 관측일당 신고 · 분류별 절대 규모 차이 포함');axes[1].set_xticks(range(1,13));axes[1].set_ylabel('건 / 해당 월 관측일');axes[1].set_xlabel('월')
 for ax in axes:ax.legend(fontsize=9);ax.grid(alpha=.15)
 axes[1].legend(fontsize=9,loc='center right',bbox_to_anchor=(.95,.70))
 fig.suptitle('2020–2024년 부산 선택 신고 · 정상 처리·운영성 제외\n서로 다른 분류를 임의 통합하지 않음 · 사고율·위험도 아님')
 fig.tight_layout()
 for ext in ['png','svg']:fig.savefig(OUT/f'domain_trends_seasons.{ext}',dpi=150)
 plt.close(fig)
 fig,ax=plt.subplots(figsize=(12,6));labs=[];before=[];after=[]
 for p in profiles:
  labs.append(f"{p['rawDong']} {p['subtype']}");s=p['stability']['C'];before.append(sum(s['core8YearCounts']));after.append(sum(s['selected17YearCounts']))
 x=np.arange(len(labs));ax.scatter(before,x,label='결측 제외 이전 비교집합',color='#8095a3');ax.scatter(after,x,label='현재 선택 신고',color='#087b84')
 for i,(a,b) in enumerate(zip(before,after)):ax.plot([a,b],[i,i],color='#c1ced4')
 ax.set_yticks(x,labs);ax.set_xlabel('신고접수 건');ax.set_title('반복 양상이 유지되어도 제외된 규모는 지역·유형마다 다르다\n2020–2024년 · 정상 처리·운영성 제외 · 서로 다른 두 집합');ax.legend();ax.grid(axis='x',alpha=.15);fig.tight_layout()
 for ext in ['png','svg']:fig.savefig(OUT/f'selection_retention.{ext}',dpi=150)
 plt.close(fig)
 water=pd.DataFrame(water_rows);v=water[water.scope.eq('C')&water.region.eq('부산')&water.year.ne('all')]
 fig,axes=plt.subplots(1,2,figsize=(14,6));ax=axes[0];ax.bar(v.year,v.withinCurrentSummerWindow,label='7/4~8/30 해당 날짜',color='#087b84');ax.bar(v.year,v.outsideCurrentSummerWindow,bottom=v.withinCurrentSummerWindow,label='나머지 날짜',color='#96b6c5')
 ax.set_ylim(0,float(v['count'].max())*1.30)
 totalwater=water[water.scope.eq('C')&water.region.eq('부산')&water.year.eq('all')].iloc[0]
 vals=[totalwater.withinPerCalendarDay,totalwater.outsidePerCalendarDay]
 axes[1].bar(['7/4~8/30','나머지 날짜'],vals,color=['#087b84','#96b6c5']);axes[1].set_ylabel('신고접수 건 / 달력일');axes[1].set_title('날짜 수를 맞추면 해당 활동기간의 일당 접수가 더 많음')
 for i,z in enumerate(vals):axes[1].text(i,z,f'{z:.3f}',ha='center',va='bottom')
 ax.set_ylabel('수난사고 신고접수 건');ax.set_title('연도별 절대 건수');ax.legend();fig.suptitle('수난 신고의 달력 분포와 2026 자원봉사 활동기간\n모집공고상 7/4~8/30 활동기간을 2020–2024년 접수일에 대입 · C조건');fig.text(.5,.055,f'전체 5년: 기간 안 {totalwater.withinCurrentSummerWindow}건 / {totalwater.withinWindowCalendarDays}일 · 밖 {totalwater.outsideCurrentSummerWindow}건 / {totalwater.outsideWindowCalendarDays:,}일',ha='center',fontsize=10);fig.text(.5,.015,'자원봉사 활동기간은 전체 수상구조대 운영기간이 아님. 기간 밖 신고는 미대응·서비스 공백의 증거가 아님.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.09,1,.90))
 for ext in ['png','svg']:fig.savefig(OUT/f'water_calendar_comparison.{ext}',dpi=150)
 plt.close(fig)
 save('manifest.json',{'script':str(Path(__file__).relative_to(ROOT)),'scriptSha256':sha(Path(__file__)),'inputs':source,'outputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']})
 print(json.dumps({'profiles':[(p['district'],p['rawDong'],p['subtype'],p['count']) for p in profiles],'checks':len(checks)},ensure_ascii=False))

if __name__=='__main__':main()
