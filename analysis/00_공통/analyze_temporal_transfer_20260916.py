"""Calendar-normalized receipt seasonality; frozen specification precedes this execution."""
from pathlib import Path
import json,hashlib,calendar
from fractions import Fraction
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[2];O=R/'data/processed/효과근거확장-20260916/temporal';O.mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=load(O/'specification.json');inputs=[{'path':str((O/'specification.json').relative_to(R)),'sha256':sha(O/'specification.json')}]
base=R/'data/processed/동대응-전체결측제외-20260915/completeness';m=load(base/'manifest.json');hashes={x['file']:x['sha256'] for x in m['outputs']}
catalogpath=R/'data/processed/후속입증-20260916/analysis/all-region-followup.json';catalog=load(catalogpath);inputs.append({'path':str(catalogpath.relative_to(R)),'sha256':sha(catalogpath)})
previous_manifest=load(catalogpath.parent/'manifest.json')
assert any(x.get('file')==catalogpath.name and x.get('sha256')==sha(catalogpath) for value in previous_manifest.values() if isinstance(value,list) for x in value if isinstance(x,dict))
records=[x for x in catalog['catalogue'] if x['scope']=='C'];assert len(records)==970
D,N,T,U,P,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
keys=[D,N,T,U];years=list(range(2020,2025));frames=[];ledger=[]
for y in years:
 path=base/f'complete_17_{y}.csv.gz';h=sha(path);assert h==hashes[path.name];inputs.append({'path':str(path.relative_to(R)),'sha256':h})
 f=pd.read_csv(path,usecols=keys+[P,DT],dtype=str,keep_default_na=False);n=len(f);f=f[f[P].eq('정상')&~f[U].isin(['업무운행','훈련출동','구급차소독'])].copy();stamp=pd.to_datetime(f[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert stamp.dt.year.eq(y).all();f['year']=y;f['month']=stamp.dt.month
 domains=set((x['type'],x['subtype']) for x in records);f=f.assign(selected=[(a,b) in domains for a,b in zip(f[T],f[U])]);ledger.append({'year':y,'allComplete17':n,'C_allTypes':len(f),'C_fiveTypes':int(f.selected.sum())});frames.append(f[f.selected].groupby(keys+['year','month']).size().rename('count').reset_index())
cross=pd.concat(frames,ignore_index=True);lookup={tuple(row[:6]):int(row[6]) for row in cross.itertuples(index=False,name=None)}
assert sum(x['allComplete17'] for x in ledger)==704689 and sum(x['C_allTypes'] for x in ledger)==574662
windows=[('all',years)]+[(str(y),[y]) for y in years]+[(f'without_{y}',[z for z in years if z!=y]) for y in years]
seasons=spec['seasonMonths'];rows=[];profiles=[];checks=[]
def tops(counts,days):
 if not sum(counts):return []
 rates=[Fraction(int(n),int(d)) for n,d in zip(counts,days)];mx=max(rates);return [i for i,v in enumerate(rates) if v==mx]
for old in records:
 key=(old['district'],old['rawDong'],old['type'],old['subtype']);annual=[[lookup.get(key+(y,mo),0) for mo in range(1,13)] for y in years]
 assert [sum(v) for v in annual]==old['yearCounts'];assert [sum(v[i] for v in annual) for i in range(12)]==old['monthCounts']
 result=[]
 for name,ys in windows:
  cnt=[sum(annual[years.index(y)][mo-1] for y in ys) for mo in range(1,13)];days=[sum(calendar.monthrange(y,mo)[1] for y in ys) for mo in range(1,13)]
  sc=[sum(cnt[mo-1] for mo in ms) for ms in seasons.values()];sd=[sum(days[mo-1] for mo in ms) for ms in seasons.values()]
  rec={'district':key[0],'rawDong':key[1],'type':key[2],'subtype':key[3],'window':name,'years':ys,'count':sum(cnt),'monthCounts':cnt,'monthCalendarDays':days,'monthPerCalendarDay':[n/d for n,d in zip(cnt,days)],'topMonths':[i+1 for i in tops(cnt,days)],'seasonCounts':sc,'seasonCalendarDays':sd,'seasonPerCalendarDay':[n/d for n,d in zip(sc,sd)],'topSeasons':[list(seasons)[i] for i in tops(sc,sd)]};result.append(rec)
  for mo,(n,d) in enumerate(zip(cnt,days),1):rows.append({'district':key[0],'rawDong':key[1],'type':key[2],'subtype':key[3],'window':name,'month':mo,'count':n,'calendarDays':d,'receiptsPerCalendarDay':n/d})
 a=result[0];valid=[v for v in result[1:6] if v['count']];loo=result[6:]
 profiles.append({'district':key[0],'rawDong':key[1],'type':key[2],'subtype':key[3],'count':a['count'],'yearCounts':old['yearCounts'],'minimumAnnual':min(old['yearCounts']),'validAnnual':len(valid),'topMonths':a['topMonths'],'topSeasons':a['topSeasons'],'annualMonthExact':sum(v['topMonths']==a['topMonths'] for v in valid),'annualSeasonExact':sum(v['topSeasons']==a['topSeasons'] for v in valid),'leaveOneMonthExact':sum(v['topMonths']==a['topMonths'] and bool(a['topMonths']) for v in loo),'leaveOneSeasonExact':sum(v['topSeasons']==a['topSeasons'] and bool(a['topSeasons']) for v in loo),'leaveOneSeasonOverlap':sum(bool(set(v['topSeasons'])&set(a['topSeasons'])) for v in loo),'windows':result})
assert sum(x['count'] for x in profiles)==41720
pd.DataFrame(rows).to_csv(O/'all_region_month_windows.csv',index=False,encoding='utf-8-sig');pd.DataFrame([{k:v for k,v in p.items() if k!='windows'} for p in profiles]).to_csv(O/'stability_profiles.csv',index=False,encoding='utf-8-sig')
focuskeys=[('연산동','심정지'),('부전동','교통사고'),('광안동','교통사고'),('초읍동','산악사고'),('금성동','산악사고'),('다대동','수난사고'),('우동','수난사고'),('기장읍','일반화재(주택)'),('온천동','일반화재(주택)')]
focus=[next(p for p in profiles if (p['rawDong'],p['subtype'])==k) for k in focuskeys]
sensitivity=[]
for minimum in [1,5,10,20]:
 pp=[p for p in profiles if p['minimumAnnual']>=minimum];sensitivity.append({'minimumAnnual':minimum,'combinations':len(pp),'monthSameAllFiveLeaveOut':sum(p['leaveOneMonthExact']==5 for p in pp),'seasonSameAllFiveLeaveOut':sum(p['leaveOneSeasonExact']==5 for p in pp),'seasonSameAllFiveAnnual':sum(p['annualSeasonExact']==5 for p in pp)})
out={'specification':spec,'ledger':ledger,'sensitivity':sensitivity,'profiles':profiles,'focus':focus}
(O/'temporal-transfer.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');(O/'focus-summary.json').write_text(json.dumps(focus,ensure_ascii=False,indent=2),encoding='utf-8')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(3,3,figsize=(15,11),sharex=True)
for ax,p in zip(axes.flat,focus):
 for v in p['windows'][1:6]:ax.plot(range(1,13),v['monthPerCalendarDay'],color='#a7b6b4',alpha=.65,lw=.8)
 ax.plot(range(1,13),p['windows'][0]['monthPerCalendarDay'],color='#147d73',lw=2.3,label='5년 합계 / 달력 일수');ax.set_title(p['rawDong']+' · '+p['subtype']+f" ({p['count']:,}건)",fontsize=12);ax.set_xticks([1,3,6,9,12]);ax.set_ylim(bottom=0);ax.grid(alpha=.15);ax.set_ylabel('접수 / 달력일');ax.set_xlabel('접수 월')
for ax in axes.flat:ax.tick_params(labelbottom=True)
axes[0,0].legend(fontsize=8);fig.suptitle('한 해를 빼도 유지되는 시기인지: 월별 접수 양상을 연도와 함께 비교',fontsize=17);fig.text(.04,.015,'회색: 각 연도 2020–2024 / 초록: 전체기간. 각 패널 세로축은 다름. 선택 신고 C조건·주민 노출률 아님·해당 지역명 접수.',fontsize=10);fig.tight_layout(rect=(0,.04,1,.96))
for ext in ['png','svg']:fig.savefig(O/f'monthly_year_comparison.{ext}',dpi=160)
plt.close(fig)
fig,ax=plt.subplots(figsize=(13,7));ax.set_xlim(-.5,5.5);ax.set_ylim(len(focus)-.5,-.5)
colors={'봄':'#d6e8d5','여름':'#c4e1e8','가을':'#f2ddb8','겨울':'#dce0ed'}
for i,p in enumerate(focus):
 for j,v in enumerate([p['windows'][0]]+p['windows'][6:]):
  names=v['topSeasons'];ax.add_patch(plt.Rectangle((j-.48,i-.43),.96,.86,color=colors.get(names[0],'#eeeeee') if len(names)==1 else '#eeeeee'))
  ax.text(j,i,'·'.join(names) or '없음',ha='center',va='center',fontsize=12)
ax.set_xticks(range(6),['전체 5년']+[f'{y} 제외' for y in years]);ax.set_yticks(range(9),[p['rawDong']+' · '+p['subtype'] for p in focus]);ax.tick_params(length=0)
for spine in ax.spines.values():spine.set_visible(False)
ax.set_title('한 해를 제외했을 때 달력일수당 접수가 가장 많은 계절',fontsize=17,pad=20)
fig.text(.02,.03,'2020–2024 선택 신고 C조건. 동률은 모두 표시. 겨울=동일 달력연도의 1·2·12월. 최고계절은 위험도·배치 최적시기가 아님.',fontsize=10)
fig.tight_layout(rect=(0,.07,1,1))
for ext in ['png','svg']:fig.savefig(O/f'leave_one_season.{ext}',dpi=160)
plt.close(fig)
lines=['# 계절·월 특성의 연도 의존성','', 'C조건 선택 접수. 달력일수당 건수이며 위험·생활인구 노출률이 아니다. 겨울은 각 달력연도 1·2·12월의 묶음이다. 결측 제외 전후 계절성을 검증한 분석은 아니다.','', '|지역·유형|5년 건수|전체 최고월|전체 최고계절|최고월 유지(1년 제외)|최고계절 유지(1년 제외)|연간 최고계절 일치|','|---|---:|---|---|---:|---:|---:|']
for p in focus:lines.append(f"|{p['rawDong']} {p['subtype']}|{p['count']}|{p['topMonths']}|{','.join(p['topSeasons'])}|{p['leaveOneMonthExact']}/5|{p['leaveOneSeasonExact']}/5|{p['annualSeasonExact']}/{p['validAnnual']}|")
lines+=['','최고계절이 유지되어도 실제 사고 장소·인력 필요량·예방 효과는 확인하지 못한다. 안정된 시기는 계절 안내와 기존 운영기간을 대조할 배경이고, 흔들리는 시기는 단일 최고월에 맞춘 정책 근거로 쓰지 않는다. 낮은 건수의 최댓값은 작은 변동일 수 있어 매년 최소1·5·10·20건 기준을 모두 제공한다.','',
'## 이번 결과가 허용하는 구체적 안내 범위','',
'- 연산 심정지는 5년 합산 가을 최고가 2021년 제외 시 겨울로 바뀐다. 특정 계절에만 CPR 안내를 집중해야 한다고 정하지 않는다. 기존 교육의 대상·신청 조건은 연중 제공하되 시기별 수치는 탐색 정보로 둔다.',
'- 부전 교통은 전체 겨울 최고지만 2022년 제외 시 여름으로 바뀐다. 겨울 한정 보행시설 개선이나 특정 계절 순찰의 근거로 쓰지 않는다. 이후 정비 이력·현재 구간 상태 대조가 우선이다.',
'- 광안 교통의 최고월 4월은 5회 모두 유지되지만 최고계절은 2022년 제외 시 가을로 바뀐다. 월 최고와 계절 최고는 다른 질문이다. 처리조건 민감성이 이미 있어 단독 정책선정 사례로 격상하지 않는다.',
'- 다대동 수난은 전체 여름 최고가 1년씩 제외한 5회 모두 유지되어 여름 안전안내·기존 운영기간을 대조할 배경이다. 해당 접수가 다대포해수욕장 사건이라는 뜻도, 비여름 대응이 불필요하다는 뜻도 아니다.',
'- 초읍 산악은 전체 가을 최고가 3회 바뀐다. 동일 동명 접수를 특정 등산로·계절 사고로 규정하지 않는다. 현장 정비·공식 통제 구간의 현재 정보와 접수월을 구분한다.',
'- 기장·온천 주택화재는 전체 최고월 유지가 각각1/5·0/5이며 시기 한정 지원정책의 근거가 약하다. 지원 대상·주택 조건을 계절과 별개로 안내하는 범위를 유지한다.','',
'이번 비교의 반복 조합407개는 C에서 매년1건 이상인 집합이다. 이전의 제외 전후·세 처리조건 안정325개와 분모가 다르다. 월별 접수0일이 실제 무사고인지 관측누락인지 추가 입증하지 않았으며, 달력 분모는 관측누락을 보정하지 않는다. 월 최고와 계절 최고가 다른 것은 1개월과3개월 묶음의 비교이므로 오류가 아니다.','',json.dumps(sensitivity,ensure_ascii=False)]
(O/'분석결과.md').write_text('\n'.join(lines),encoding='utf-8')
(O/'manifest.json').write_text(json.dumps({'inputs':inputs,'codeSHA256':sha(Path(__file__)),'checks':{'complete17':704689,'C_allTypes':574662,'C_fiveTypes':41720,'profiles':len(profiles),'windowsPerProfile':11,'monthlyRows':len(rows),'priorAnnualAndMonthlyExact':True},'outputs':[{'file':p.name,'sha256':sha(p)} for p in O.iterdir() if p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(sensitivity,ensure_ascii=False));print('\n'.join(lines[6:15]))
