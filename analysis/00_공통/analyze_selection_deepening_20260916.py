"""Same-channel temporal selection diagnostics; no reweighting or risk inference."""
from pathlib import Path
import json,hashlib
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[2]
O=R/'data/processed/고도화검증-20260916/selection';O.mkdir(parents=True,exist_ok=True)
D,N,T,U,P,DT,RES,PROV='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','RCPT_PATH_NM','DCLR_DT','PRCS_RSLT_SE_NM','CLMTY_CTPV_NM'
KEY=[D,N,T,U]
DOM={('구급','심정지'),('화재','일반화재(주택)'),('구조','산악사고'),('구조','수난사고'),('구급','교통사고')}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
inputs=[];pieces=[];reconciliation=[]
for stage,folder,prefix in [('core8','컬럼선별-결측제외-20260915','all_selected'),('complete17','동대응-전체결측제외-20260915/completeness','complete_17')]:
 base=R/'data/processed'/folder; man=read(base/'manifest.json'); hashes={Path(x['file']).name:x['sha256'] for x in man['outputs']}
 for y in range(2020,2025):
  p=base/f'{prefix}_{y}.csv.gz';h=sha(p);assert h==hashes[p.name];inputs.append({'path':str(p.relative_to(R)),'sha256':h,'priorHashMatch':True})
  f=pd.read_csv(p,dtype=str,keep_default_na=False,usecols=KEY+[P,DT,RES,PROV,'DCLR_RCPT_NO'])
  if stage=='core8':f=f[f[PROV].eq('부산광역시')&~f[KEY+[DT,RES,PROV,'DCLR_RCPT_NO']].apply(lambda c:c.str.strip().eq('')).any(axis=1)].copy()
  reconciliation.append({'year':y,'stage':stage,'allScopeA':len(f),'mobileScopeA':int(f[P].eq('이동전화').sum())})
  f=f[[tuple(v) in DOM for v in f[[T,U]].itertuples(index=False,name=None)]].copy()
  dt=pd.to_datetime(f[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert dt.dt.year.eq(y).all()
  f['year']=y;f['weekday']=dt.dt.weekday;f['hour']=dt.dt.hour
  for scope in 'ABC':
   g=f if scope=='A' else f[f[RES].eq('정상')]
   for channel in ['all','mobile']:
    z=g if channel=='all' else g[g[P].eq('이동전화')]
    a=z.groupby(KEY+['year','weekday','hour']).size().rename('count').reset_index();a['stage']=stage;a['channel']=channel;a['scope']=scope;pieces.append(a)
  print(stage,y,len(f),flush=True)
cross=pd.concat(pieces,ignore_index=True)
cross.to_csv(O/'region_type_year_weekday_hour.csv.gz',index=False,encoding='utf-8-sig')
old=read(R/'data/processed/후속입증-20260916/analysis/all-region-followup.json')
by={}
for v in old['catalogue']:by.setdefault((v['district'],v['rawDong'],v['type'],v['subtype']),[]).append(v)
stable={k for k,v in by.items() if len(v)==3 and all(r['repeatedBefore'] and r['repeatedAfter'] and not r['directionReversal'] for r in v)}
assert len(stable)==old['stabilityAcrossScopes']['combinations']
inputs.append({'path':'data/processed/후속입증-20260916/analysis/all-region-followup.json','sha256':sha(R/'data/processed/후속입증-20260916/analysis/all-region-followup.json')})
metrics=[]
for keys,g in cross.groupby(KEY+['scope','stage','channel']):
 for period,years in [('2020–2024',list(range(2020,2025)))]+[(str(y),[y]) for y in range(2020,2025)]:
  z=g[g.year.isin(years)];cal=pd.DatetimeIndex(np.concatenate([pd.date_range(f'{y}-01-01',f'{y}-12-31').values for y in years]));weDays=int((cal.weekday>=5).sum());wdDays=len(cal)-weDays
  total=int(z['count'].sum());we=int(z.loc[z.weekday>=5,'count'].sum());day=int(z.loc[z.hour.between(6,17),'count'].sum());hours=z.groupby('hour')['count'].sum().reindex(range(24),fill_value=0)
  metrics.append(dict(zip(KEY+['scope','stage','channel'],keys))|{'period':period,'count':total,'weekendCount':we,'weekdayCount':total-we,'weekendDays':weDays,'weekdayDays':wdDays,'weekendRatio':we/weDays/((total-we)/wdDays) if total>we else None,'dayShare':day/total if total else None,'hours':hours.tolist(),'priorStable':keys[:4] in stable})
mf=pd.DataFrame(metrics);mf.drop(columns='hours').to_csv(O/'temporal_metrics.csv',index=False,encoding='utf-8-sig')
comparisons=[]
for keys,g in mf.groupby(KEY+['scope','period']):
 lookup={(x.stage,x.channel):x for x in g.itertuples()}
 a=lookup.get(('core8','mobile'));b=lookup.get(('complete17','mobile'));c=lookup.get(('core8','all'));e=lookup.get(('complete17','all'))
 if a is None or b is None:continue
 assert b.count<=a.count
 av,bv=a.weekendRatio,b.weekendRatio
 comparisons.append(dict(zip(KEY+['scope','period'],keys))|{'priorStable':keys[:4] in stable,'beforeMobile':a.count,'afterMobile':b.count,'mobileRetention':b.count/a.count if a.count else None,'beforeWeekendRatio':av,'afterWeekendRatio':bv,'weekendDirectionReversed':bool(np.isfinite(av) and np.isfinite(bv) and (av-1)*(bv-1)<0),'weekendBeyond09_11':bool(np.isfinite(av) and np.isfinite(bv) and ((av<.9 and bv>1.1) or (bv<.9 and av>1.1))),'dayShareChangePP':100*(b.dayShare-a.dayShare),'hourTVD':float(np.abs(np.array(a.hours)/a.count-np.array(b.hours)/b.count).sum()/2) if a.count and b.count else None,'beforeAll':c.count,'afterAll':e.count,'removedOtherChannels':c.count-a.count,'removedWithinMobile':a.count-b.count,'otherChannelsSurviving':e.count-b.count})
cf=pd.DataFrame(comparisons);cf.to_csv(O/'same_mobile_comparison.csv',index=False,encoding='utf-8-sig')
pooled=cf[(cf.period=='2020–2024')&(cf.scope=='C')];ss=pooled[pooled.priorStable]
summary=[]
for minimum in [1,5,10,20]:
 eligible=[]
 for k,g in cf[(cf.scope=='C')&cf.period.ne('2020–2024')&cf.priorStable].groupby(KEY):
  if len(g)==5 and g.afterMobile.min()>=minimum:eligible.append(k)
 x=ss[[tuple(v) in eligible for v in ss[KEY].itertuples(index=False,name=None)]]
 summary.append({'minimumMobileAfterEachYear':minimum,'combinations':len(x),'weekendDirectionReversed':int(x.weekendDirectionReversed.sum()),'weekendBeyond09_11':int(x.weekendBeyond09_11.sum()),'medianHourTVD':float(x.hourTVD.median()) if len(x) else None})
result={'meta':{'period':'2020–2024','fiveDomains':sorted(DOM),'scope':'A 전체 처리, B 정상, C 정상·운영성 제외. 선택한 5유형에서 B와 C 동일','comparison':'같은 이동전화 접수: 기초8 필수값 충족 대 17개 충족. 공식 모집단 대표성 복구 아님','time':'주말/평일 각각 달력 일수 보정; 주간06–17시와 야간18–05시 각각12시간','geography':'접수 구·동명, 실제 행정동·개별 지점 배정 아님','priorStableDefinition':'기존 3처리조건 모두 5년 반복·2020→2024 방향역전 없음','priorStableCombinations':len(stable),'thresholds':'연간1/5/10/20은 표본 크기 민감도, 0.9/1.1은 작은 경계 변동 별도 구분. 정책 선정 기준·검정 아님'},'summary':summary,'scopeCComparisons':json.loads(pooled.to_json(orient='records',force_ascii=False)),'reconciliation':reconciliation}
(O/'selection-deepening.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(12,8));x=ss.dropna(subset=['beforeWeekendRatio','afterWeekendRatio']);ax.scatter(x.beforeWeekendRatio,x.afterWeekendRatio,s=30,alpha=.6,color='#187e8c');lim=max(x.beforeWeekendRatio.max(),x.afterWeekendRatio.max())*1.06;ax.plot([0,lim],[0,lim],color='#a9b2b6');ax.axhline(1,color='#bb8042',ls='--');ax.axvline(1,color='#bb8042',ls='--');ax.set(xlim=(0,lim),ylim=(0,lim),xlabel='결측 제외 전 이동전화 · 주말/평일 일평균 비',ylabel='17개 충족 이동전화 · 주말/평일 일평균 비',title='반복성이 유지되어도 시간 양상은 달라질 수 있다');ax.grid(alpha=.15)
fig.text(.08,.025,f'2020–2024 · 정상 처리 · 기존 반복 유지 {len(stable)}개 중 같은 이동전화 비교 가능 {len(x)}개\n점은 지역명×유형 조합. 대각선에서 멀수록 선택 영향이 큼. 사고 위험률·서비스 부족 판단 아님.',fontsize=11);fig.tight_layout(rect=(0,.08,1,1))
for ext in ['png','svg']:fig.savefig(O/f'same_mobile_weekend.{ext}',dpi=170)
plt.close(fig)
focus=pooled[pooled[N].isin(['거제동','범일동','남포동1가','남포동2가','남포동3가','남포동4가','남포동5가','남포동6가'])&pooled[U].eq('교통사고')].copy()
focus.to_csv(O/'focus_channel_decomposition.csv',index=False,encoding='utf-8-sig')
fig,ax=plt.subplots(figsize=(13,7));labels=(focus[D]+' '+focus[N]).tolist();left=np.zeros(len(focus))
for col,label,color in [('afterMobile','17개 충족 이동전화','#137e8b'),('removedWithinMobile','이동전화 내부 제외','#e7a34e'),('removedOtherChannels','다른 접수경로(제외 전)','#a6b4be')]:
 ax.barh(labels,focus[col],left=left,label=label,color=color);left+=focus[col].values
ax.set_xlabel('2020–2024 정상 처리 교통사고 접수 건수');ax.set_title('전화경로 차이와 이동전화 내부의 선택 영향을 분리');ax.legend(loc='lower right');fig.text(.07,.02,'전체 길이는 기초8 조건 접수. 다른 경로 중 17개 충족 건수는 CSV에 별도 기록. 결측 원인이나 사고 원인을 뜻하지 않음.',fontsize=10);fig.tight_layout(rect=(0,.06,1,1))
for ext in ['png','svg']:fig.savefig(O/f'channel_decomposition.{ext}',dpi=170)
plt.close(fig)
endpoint=[]
for k,g in cf[cf.period.isin(['2020','2024'])].groupby(KEY+['scope']):
 if set(g.period)!= {'2020','2024'}:continue
 a=g[g.period=='2020'].iloc[0];b=g[g.period=='2024'].iloc[0]
 delta={c:int(b[c]-a[c]) for c in ['beforeAll','afterAll','beforeMobile','afterMobile','removedOtherChannels','removedWithinMobile','otherChannelsSurviving']}
 assert delta['beforeAll']==delta['afterMobile']+delta['removedWithinMobile']+delta['removedOtherChannels']
 assert delta['afterAll']==delta['afterMobile']+delta['otherChannelsSurviving']
 endpoint.append(dict(zip(KEY+['scope'],k))|{'priorStable':k[:4] in stable,'fullChannelDirectionReversal':delta['beforeAll']*delta['afterAll']<0,'sameMobileDirectionReversal':delta['beforeMobile']*delta['afterMobile']<0,**{c+'Change2024minus2020':v for c,v in delta.items()}})
pd.DataFrame(endpoint).to_csv(O/'annual_direction_channel_decomposition.csv',index=False,encoding='utf-8-sig')
prior=read(R/'data/processed/동대응-전체결측제외-20260915/completeness/manifest.json')
for rec in reconciliation:
 expected=next(v for v in prior['year_counts'] if v['year']==rec['year']);assert rec['allScopeA']==expected['core8' if rec['stage']=='core8' else 'provisional17']
lookup={(v['district'],v['rawDong'],v['type'],v['subtype'],v['scope']):v for v in old['catalogue']}
checked=0
for v in metrics:
 k=tuple(v[c] for c in KEY)+ (v['scope'],)
 if v['stage']=='complete17' and v['channel']=='all' and v['period']=='2020–2024':
  assert v['count']==lookup[k]['count'];checked+=1
(O/'validation.json').write_text(json.dumps({'priorAnnualCountsMatch':True,'existingCatalogueChecks':checked,'endpointAdditiveChecks':len(endpoint),'noIdentifiersOrCoordinatesInOutputs':True},ensure_ascii=False,indent=2),encoding='utf-8')
(O/'README.md').write_text('''# 같은 이동전화 내부의 선택 영향 추가 검증

2020–2024년 동일 구·동명과 5개 예방 관련 유형을 비교한다. 기초8 조건 신고는 비교용이며, 현재 분석 입력을 변경하지 않는다. 입력 gzip은 기존 manifest SHA256과 일치한다. 개별 접수번호는 기초8 완전성 판정에만 읽고 결과에는 저장하지 않는다.

주말과 평일은 각각 실제 달력 일수로 나눈다. 24시간 분포 TVD는 두 시간별 구성비 차이 절댓값의 합/2이다. 시간 분포 차이는 서비스 부족·사고 원인이나 결측 발생 원인을 입증하지 않는다. 연간 표본 수 1/5/10/20과 0.9/1.1 비교는 민감도 표현이며 정책 선정 기준·통계적 유의성 판정이 아니다.

기존 반복 유지 325개에서도 주말/평일의 1배 기준을 넘나드는 조합은 33개다. 다만 0.9 미만과 1.1 초과를 오가는 것은 2개이며, 매년 이동전화 잔존 5건 이상 조건에서는 0개다. 작은 경계 변동과 충분한 건수에서의 일관성을 구분해야 한다.

annual_direction_channel_decomposition.csv는 2024−2020 건수 변화를 이동전화 잔존·이동전화 내부 제외·다른 경로의 기초8 신고 변화로 가산 분해한다. 이는 관측 구성의 산술 분해이며 인과 분해가 아니다. 순위·대표성 회복·예방 효과는 계산하지 않는다.
''',encoding='utf-8')
(O/'manifest.json').write_text(json.dumps({'inputs':inputs,'scriptSHA256':sha(Path(__file__)),'outputs':[{'file':p.name,'sha256':sha(p)} for p in sorted(O.iterdir()) if p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False),flush=True)
