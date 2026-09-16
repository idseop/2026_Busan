"""Check whether pooled case timing persists across years; no patient inference or forecast."""
from pathlib import Path
from datetime import date,timedelta
import csv,json,hashlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'data/processed/예방지원-근거분석-20260916/analysis'
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/time'
OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((SRC/'action-patterns.json').read_text(encoding='utf-8'))
df=pd.read_csv(SRC/'selected_case_year_weekday_exact_hour.csv')
calendar={}
for y in range(2020,2025):
    d=date(y,1,1); end=date(y+1,1,1); counts=[0]*7
    while d<end: counts[d.weekday()]+=1; d+=timedelta(days=1)
    calendar[y]=counts
def metric(frame,years):
    weekend=int(frame.loc[frame.weekday>=5,'count'].sum()); weekday=int(frame.loc[frame.weekday<5,'count'].sum())
    we=sum(sum(calendar[y][5:]) for y in years); wd=sum(sum(calendar[y][:5]) for y in years)
    ratio=(weekend/we)/(weekday/wd) if weekday else None
    # Equal twelve-hour windows, set before reading case time distributions.
    day=int(frame.loc[(frame.hour>=6)&(frame.hour<18),'count'].sum())
    night=int(frame['count'].sum())-day
    return dict(count=int(frame['count'].sum()),weekendCount=weekend,weekdayCount=weekday,weekendDays=we,weekdayDays=wd,weekendPerDay=weekend/we,weekdayPerDay=weekday/wd,weekendRatio=ratio,day06to18=day,night18to06=night,dayShare=day/(day+night) if day+night else None)
rows=[];cases=[]
for p in data['profiles']:
    byscope={}
    for scope in ['A','B','C']:
        base=df.loc[(df.caseId==p['id'])&(df.scope==scope)]
        assert int(base['count'].sum())==p['scopeProfiles'][scope]['count']
        annual=[]
        for y in range(2020,2025):
            m=metric(base.loc[base.year==y],[y]);annual.append(dict(year=y,**m))
            rows.append(dict(caseId=p['id'],district=p['district'],rawDong=p['rawDong'],subtype=p['subtype'],scope=scope,period=str(y),**m))
        periods=[]
        for name,ys in [('2020–2022',[2020,2021,2022]),('2023–2024',[2023,2024])]:
            m=metric(base.loc[base.year.isin(ys)],ys);periods.append(dict(period=name,**m))
            rows.append(dict(caseId=p['id'],district=p['district'],rawDong=p['rawDong'],subtype=p['subtype'],scope=scope,period=name,**m))
        leave=[]
        for excluded in range(2020,2025):
            ys=[y for y in range(2020,2025) if y!=excluded]
            leave.append(dict(excludedYear=excluded,**metric(base.loc[base.year.isin(ys)],ys)))
        byscope[scope]=dict(annual=annual,periods=periods,leaveOneYearOut=leave,weekendHigherYears=sum(m['weekendRatio'] is not None and m['weekendRatio']>1 for m in annual))
    cases.append(dict(id=p['id'],district=p['district'],rawDong=p['rawDong'],subtype=p['subtype'],scopes=byscope))
result=dict(meta=dict(period='2020–2024',method='연도별·전후 기간·1년 제외 기술적 민감도 비교',dayDefinition='06:00–17:59 대 18:00–05:59, 각각 12시간',weekend='토·일/월~금, 각 달력 일수 보정',selectionCaution='전체 5년으로 선택한 사례의 기간 비교이며 독립 미래 검증이 아님',scopeC='정상 처리·운영성 분류 제외',noPatientAgeInference=True),cases=cases)
(OUT/'time-robustness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame(rows).to_csv(OUT/'time-robustness.csv',index=False,encoding='utf-8-sig')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(14,8));colors=['#146e82','#d88b2c']
for i,c in enumerate(cases):
    ms=c['scopes']['C']['periods']
    for k,m in enumerate(ms):ax.scatter(m['weekendRatio'],i+(k-.5)*.2,s=85,color=colors[k],label=m['period'] if i==0 else None)
    ax.plot([m['weekendRatio'] for m in ms],[i-.1,i+.1],color='#a6b7b9',lw=1,zorder=0)
ax.axvline(1,color='#78898a',ls='--');ax.set_yticks(range(len(cases)),[f"{c['district']} {c['rawDong']} · {c['subtype']}" for c in cases]);ax.invert_yaxis();ax.set_xlim(left=0);ax.grid(axis='x',alpha=.18)
ax.set_xlabel('주말 하루 평균 접수 / 평일 하루 평균 접수 (배)');ax.legend(loc='lower right')
ax.set_title('같은 지역의 주말 양상은 앞·뒤 기간에도 유지되는가',fontsize=19,pad=22)
fig.text(.03,.025,'2020–2024 선택 신고 · 정상 처리·운영성 제외 | 1보다 크면 주말 일평균이 높음\n전체 5년으로 선정한 사례의 민감도 비교이며 예측 검증·사고 위험률·서비스 부족 판정이 아님',fontsize=11)
fig.tight_layout(rect=(0,.085,1,1))
for ext in ['png','svg']:fig.savefig(OUT/f'period_weekend_comparison.{ext}',dpi=180)
plt.close(fig)
manifest={'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SRC/'action-patterns.json',SRC/'selected_case_year_weekday_exact_hour.csv']},'rows':len(rows),'cases':len(cases),'calendar':calendar}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'region':c['rawDong'],'subtype':c['subtype'],'periodRatios':[round(x['weekendRatio'],2) for x in c['scopes']['C']['periods']],'yearsAbove1':c['scopes']['C']['weekendHigherYears']} for c in cases],ensure_ascii=False))
