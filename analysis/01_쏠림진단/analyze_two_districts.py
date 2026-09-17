"""부산진구·중구 1차 분석. 원본 불변, 집계만 출력, 미확보 자료는 수치화하지 않는다."""
from pathlib import Path
import sys
import json
import re
import hashlib
import html
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from style import setup, save, source, C

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data'
PRE = DATA / 'processed/신고17개-로컬전처리-20260917-133450'
OUT = ROOT / 'output/부산진구-중구-1차분석'
OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / 'figures/부산진구-중구-1차분석'
FIG.mkdir(parents=True, exist_ok=True)
DIST = ['부산진구', '중구']
CODE = {'부산 전체': '2600000000', '부산진구': '2623000000', '중구': '2611000000'}
YEARS = list(range(2020, 2025))
inputs, checks, charts = {}, {}, []
setup()


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read(path, **kwargs):
    inputs[str(path.relative_to(ROOT))] = digest(path)
    return pd.read_csv(path, **kwargs)


def table(df, name):
    df.to_csv(OUT / (name + '.csv'), index=False, encoding='utf-8-sig')


def finish(fig, name, note, src='부산소방재난본부 119 접수 원본의 로컬 C 전처리, 2020–2024'):
    fig.tight_layout(rect=(0, .04, 1, .94))
    source(fig.axes[0], src)
    save(fig, '부산진구-중구-1차분석/' + name)
    charts.append((name, note))
    plt.close(fig)


manifest = json.loads((PRE / 'manifest.json').read_text(encoding='utf-8-sig'))
book=DATA/'부산소방재난본부_119신고접수 현황_컬럼 정보 데이터.xlsx'
inputs[str(book.relative_to(ROOT))]=digest(book)
inputs[str((PRE / 'manifest.json').relative_to(ROOT))] = digest(PRE / 'manifest.json')
parts, sensitivity = [], []
quality = []
for year in YEARS:
    for stage in 'ABC':
        d = read(PRE / f'{stage}_{year}.csv.gz', dtype=str, keep_default_na=False)
        d['year'] = year
        for region in ['부산 전체'] + DIST:
            sub = d if region == '부산 전체' else d[d.CLMTY_SGG_NM == region]
            sensitivity.append([year, stage, region, len(sub)])
        if stage == 'C':
            dt = pd.to_datetime(d.DCLR_DT.str.strip(), format='%Y%m%d%H%M%S', errors='coerce')
            quality.append([year, len(d), d.DCLR_RCPT_NO.duplicated().sum(), dt.isna().sum(),
                            (dt.dt.year != year).sum(), d.CLMTY_SGG_NM.nunique()])
            assert dt.notna().all() and (dt.dt.year == year).all()
            d['month'] = dt.dt.month
            d['hour'] = dt.dt.hour
            d['dow'] = dt.dt.dayofweek
            parts.append(d)
reports = pd.concat(parts, ignore_index=True)
assert len(reports) == 574662
assert not reports.DCLR_RCPT_NO.duplicated().any()
sensitivity = pd.DataFrame(sensitivity, columns=['연도', '조건', '지역', '신고건수'])
table(sensitivity, '01_조건별_신고수')
table(pd.DataFrame(quality, columns=['연도', '행수', '접수번호중복', '일시변환실패', '연도불일치', '구군수']), '00_신고품질')
counts = reports.groupby('CLMTY_SGG_NM').size().sort_values()
table(counts.rename_axis('구군').reset_index(name='C신고건수'), '01_부산전체_구군비교')
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(counts.index, counts, color=[C['primary'] if x in DIST else C['neutral'] for x in counts.index])
for i, v in enumerate(counts):
    ax.text(v + 400, i, f'{v:,}', va='center', fontsize=9)
ax.set(xlabel='C 조건 신고 수 (건, 5년 합계)', xlim=(0, counts.max()*1.17), title='같은 조건으로 부산 16개 구·군을 먼저 비교')
finish(fig, '01_구군_신고규모', '선정한 두 구를 부산 전체의 같은 C 조건과 비교한다. 출동·피해자 수가 아니다.')

types = reports.groupby(['CLMTY_SGG_NM', 'EMRG_RSCU_ASSRT_NM']).size().unstack(fill_value=0)
composition = pd.concat([types.loc[DIST], types.sum().to_frame().T.rename(index={0:'부산 전체'})])
table(composition.rename_axis('지역').reset_index(), '01_유형구성')
top = composition.loc['부산 전체'].nlargest(4).index.tolist()
plot = composition[top].copy()
plot['그 외'] = composition.sum(axis=1) - plot.sum(axis=1)
plot = plot.loc[:,plot.sum(axis=0)>0]
fig, ax = plt.subplots(figsize=(10, 4))
(plot.div(plot.sum(axis=1), axis=0)*100).plot.barh(stacked=True, ax=ax)
for container in ax.containers:
    ax.bar_label(container, labels=[f'{v:.1f}%' if v>=5 else '' for v in container.datavalues], label_type='center', color='white',fontsize=9)
ax.set(xlabel='지역별 C 신고 중 구성비 (%)', ylabel='', title='구급·구조 등 유형 구성을 같은 분모로 비교')
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.18), ncol=5)
finish(fig, '02_신고유형_구성', '각 구의 C 신고 전체가 분모다. 세부 유형별 원표도 함께 제공한다.')
table(reports[reports.CLMTY_SGG_NM.isin(DIST)].groupby(['year','CLMTY_SGG_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM']).size().reset_index(name='신고건수'), '01_세부유형_연도')

fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
annual = sensitivity[sensitivity['조건']=='C'].pivot(index='연도', columns='지역', values='신고건수')
annual[DIST].plot(marker='o', ax=axes[0])
axes[0].set(title='연도별 C 신고 수', ylabel='신고 수 (건)', xticks=YEARS)
ratios = sensitivity.pivot(index=['연도','지역'], columns='조건', values='신고건수')
ratios['C/A 비율(%)'] = ratios.C/ratios.A*100
ratios['C/A 비율(%)'].unstack()[DIST].plot(marker='o', ax=axes[1])
axes[1].set(title='선택한 조건에 따라 남는 비율도 다르다', ylabel='C / A (%)', xticks=YEARS, ylim=(0,100))
finish(fig, '03_연도와_조건민감도', 'A도 이미 선택 17개 결측 제외 후 자료다. 전체 원신고를 대표한다고 단정하지 않는다.')

calendar = pd.DataFrame({'date':pd.date_range('2020-01-01','2024-12-31')})
day_counts = calendar.date.dt.dayofweek.value_counts().reindex(range(7))
heat = []
for region in DIST:
    sub = reports[reports.CLMTY_SGG_NM==region]
    tab = sub.groupby(['dow','hour']).size().unstack(fill_value=0).reindex(index=range(7),columns=range(24),fill_value=0)
    heat.append(tab.div(day_counts, axis=0))
    table(tab.rename_axis('요일_월0').reset_index(), f'02_{region}_요일시간_건수')
fig, axes = plt.subplots(2, 1, figsize=(12, 6.5))
vmax = max(x.to_numpy().max() for x in heat)
for ax, region, tab in zip(axes, DIST, heat):
    im = ax.imshow(tab, cmap='Blues', aspect='auto', vmin=0, vmax=vmax)
    ax.set(title=region, xticks=range(0,24,2), xticklabels=range(0,24,2), yticks=range(7), yticklabels=list('월화수목금토일'), xlabel='접수 시간 (시)')
    ax.grid(False)
fig.colorbar(im, ax=axes.tolist(), label='해당 요일 하루당 · 1시간 구간 신고 수', location='right', fraction=.02)
fig.suptitle('요일의 실제 일수로 나눈 시간대별 신고 집중')
# 공통 색 범례와 패널이 겹치지 않게 수동 배치
fig.subplots_adjust(right=.84, hspace=.55, bottom=.12, top=.86)
source(axes[0], '부산소방재난본부 C 신고, 2020–2024 · 날짜수는 전체 달력 기준')
save(fig,'부산진구-중구-1차분석/04_요일시간_집중')
charts.append(('04_요일시간_집중','같은 색 눈금. 해당 요일 일수로 나눠 요일 횟수 차이를 보정했다.'))
plt.close(fig)
fig, axes = plt.subplots(2,1,figsize=(11,7))
monthly = []
for ax, region in zip(axes,DIST):
    for year in YEARS:
        s = reports[(reports.CLMTY_SGG_NM==region)&(reports.year==year)].groupby('month').size().reindex(range(1,13),fill_value=0)
        days = pd.to_datetime([f'{year}-{m:02d}-01' for m in range(1,13)]).days_in_month
        ax.plot(s.index, s.to_numpy()/days, marker='.', label=str(year))
        monthly.extend([[region,year,m,int(n),float(n/day)] for m,n,day in zip(s.index,s,days)])
    ax.set(title=region, xlabel='월', ylabel='하루당 신고 수 (건)',xticks=range(1,13))
axes[0].legend(ncol=5)
finish(fig,'05_월별_연도비교','월 길이를 보정하고 연도를 분리한다. 반복적 계절성의 통계적 입증은 아직 하지 않았다.')
table(pd.DataFrame(monthly,columns=['지역','연도','월','신고건수','일평균']), '02_월별_신고')

fig, axes = plt.subplots(1,2,figsize=(13,6))
dong_rows=[]
for ax,region in zip(axes,DIST):
    s=reports[reports.CLMTY_SGG_NM==region].groupby('CLMTY_EMD_NM').size().sort_values(ascending=False)
    for name,n in s.items(): dong_rows.append([region,name,n,n/s.sum()*100])
    s.head(10).sort_values().plot.barh(ax=ax,color=C['primary'])
    ax.set(title=f'{region} · 원문 동명 상위 10개',xlabel='신고 수 (건) · 패널별 축 범위 다름',ylabel='')
finish(fig,'06_원문동_집중','원문 동명 집계다. 행정동 경계·인구와 결합하지 않았다. 여러 행정동에 걸친 동명을 임의 분배하지 않는다.')
table(pd.DataFrame(dong_rows,columns=['지역','원문동명','신고건수','구내비중(%)']), '03_원문동_분포')

# 관서 원본: 이름의 공백만 정리하고 일대일 대응을 검사한다.
loc=read(DATA/'소방서 및 119안전센터 위치 현황.csv',keep_default_na=False)
staff=read(DATA/'소방서 및 119안전센터 출동가능 인원 현황 (1).csv',keep_default_na=False)
veh=read(DATA/'소방서 및 119안전센터 출동가능 차량수.csv',keep_default_na=False)
norm=lambda s: s.astype(str).str.replace(r'\s+','',regex=True)
loc['key']=norm(loc['관서명']); staff['key']=norm(staff['관서명']); veh['key']=norm(veh['소방관서명'])
for frame in (loc,staff,veh):
    frame['key']=frame['key']+'|'+norm(frame['도로명 주소'].str.replace('부산광역시','부산',regex=False))
assert not loc.key.duplicated().any() and not staff.key.duplicated().any() and not veh.key.duplicated().any()
fac=loc.merge(staff[['key','출동가능 인원수']],on='key',how='left',validate='one_to_one').merge(veh[['key','소방차량 유형','차량 대수(대)']],on='key',how='left',validate='one_to_one')
fac['지역']=fac['도로명 주소'].str.extract(r'부산(?:광역시)?\s+(\S+[구군])')[0]
assert fac['지역'].notna().all()
table(fac.drop(columns='key'),'04_관서연결_검증')
resource=[]
for region in sorted(fac['지역'].unique()):
    f=fac[fac['지역']==region]
    resource.append([region,len(f),len(f[['X좌표','Y좌표']].drop_duplicates()),f['관서명'].str.contains('119안전센터').sum(),pd.to_numeric(f['출동가능 인원수']).sum(min_count=1),pd.to_numeric(f['차량 대수(대)']).sum(min_count=1)])
resource=pd.DataFrame(resource,columns=['지역','관서행수','좌표위치수','안전센터명칭수','출동가능인원_원표','차량대수_원표'])
table(resource,'04_소재지별_자원')
fig,axes=plt.subplots(1,3,figsize=(12,4.5))
for ax,col in zip(axes,['안전센터명칭수','출동가능인원_원표','차량대수_원표']):
    s=resource.set_index('지역').loc[DIST,col]
    ax.bar(s.index,s,color=C['primary'])
    for i,v in enumerate(s): ax.text(i,v,str(int(v)),ha='center',va='bottom')
    title={'안전센터명칭수':'119안전센터 (소재지 기준)','출동가능인원_원표':'출동가능 인원 (원표 합계)','차량대수_원표':'차량 대수 (원표 합계)'}[col]
    ax.set(title=title,ylim=(0,s.max()*1.25),ylabel='개소' if col=='안전센터명칭수' else ('명' if '인원' in col else '대'))
finish(fig,'07_소방자원_소재지비교','센터 수·인원·차량은 서로 다른 단위다. 기준일·교대인원·관할범위 미확인으로 부족 판정은 보류한다.','사용자 제공 소방관서 위치·인원·차량 CSV 3종 · 기준일 미확인')

assigned=reports[reports.CLMTY_SGG_NM.isin(DIST)].groupby(['CLMTY_SGG_NM','PLCSCN_CNTR_NM']).size().reset_index(name='신고건수')
table(assigned,'05_기록상센터_구성')
fig,axes=plt.subplots(1,2,figsize=(13,6))
for ax,region in zip(axes,DIST):
    s=assigned[assigned.CLMTY_SGG_NM==region].set_index('PLCSCN_CNTR_NM')['신고건수'].nlargest(8).sort_values()
    s.plot.barh(ax=ax,color=C['primary'])
    ax.set(title=f'{region} · 기록상 센터 상위 8개',xlabel='신고 수 (건) · 패널별 축 범위 다름',ylabel='')
finish(fig,'08_접근성_전_센터기록확인','접근성 축의 사전 진단이다. PLCSCN_CNTR_NM 기록은 실제 출동·도착시간·센터별 업무량을 보장하지 않는다. 도로망·출동시각·도착시각·당시 가용인원 확보 전 접근성 판정 보류.')

pop=[]; pop_checks=[]
for year in YEARS:
    p=read(DATA/f'MOIS_{year}12_연령별인구_부산전체읍면동.csv',encoding='cp949',dtype=str)
    p['code']=p.iloc[:,0].str.extract(r'\((\d{10})\)')[0]
    assert p.code.notna().all() and not p.code.duplicated().any()
    ages=[c for c in p if re.search(r'_계_\d+세',c)]
    assert len(ages)==101
    values=p[ages].apply(lambda s:pd.to_numeric(s.str.replace(',','',regex=False)))
    total=pd.to_numeric(p[f'{year}년12월_계_총인구수'].str.replace(',','',regex=False))
    assert (values.sum(axis=1)==total).all()
    pop_checks.append([year,len(p),p.code.duplicated().sum(),int((values.sum(axis=1)!=total).sum())])
    for region,code in CODE.items():
        idx=p.index[p.code==code]
        assert len(idx)==1
        i=idx[0]
        elderly=[int(values.loc[i,[c for c in ages if int(re.search(r'_계_(\d+)세',c)[1])>=cut]].sum()) for cut in (65,75,85)]
        pop.append([year,region,code,int(total[i]),*elderly])
pop=pd.DataFrame(pop,columns=['연도','지역','지역코드','연말인구','65세이상','75세이상','85세이상'])
for age in (65,75,85): pop[f'{age}세이상비율']=pop[f'{age}세이상']/pop['연말인구']*100
joined=pop.merge(sensitivity[sensitivity['조건']=='C'][['연도','지역','신고건수']],on=['연도','지역'],validate='one_to_one')
joined['연말주민1천명대비신고']=joined['신고건수']/joined['연말인구']*1000
table(joined,'06_구별인구와_신고'); table(pd.DataFrame(pop_checks,columns=['연도','행수','코드중복','연령합계불일치']),'00_인구품질')
fig,axes=plt.subplots(1,2,figsize=(12,5))
for region in ['부산 전체']+DIST:
    sub=joined[joined['지역']==region]
    axes[0].plot(sub['연도'],sub['65세이상비율'],marker='o',label=region)
    axes[1].plot(sub['연도'],sub['연말주민1천명대비신고'],marker='o',label=region)
axes[0].set(title='65세 이상 주민 비율',ylabel='연말 주민 중 비율 (%)',xticks=YEARS)
axes[1].set(title='주민 규모 대비 신고는 노출 보정의 일부',ylabel='연말 주민 1천 명 대비 연간 신고 (건)',xticks=YEARS)
axes[0].legend(); axes[1].legend()
finish(fig,'09_고령인구_지역맥락','구 코드와 연도를 고정해 연결했다. 신고자의 나이를 뜻하지 않으며 유동인구·방문객 노출이 반영되지 않은 비율이다.','행정안전부 2020–2024년 12월 연령별 인구 CSV + 부산소방재난본부 C 신고')
fig,ax=plt.subplots(figsize=(10,4.5))
p=pop[pop['연도']==2024].set_index('지역').loc[DIST+['부산 전체']]
bands=pd.DataFrame({'65–74세':p['65세이상']-p['75세이상'],'75–84세':p['75세이상']-p['85세이상'],'85세 이상':p['85세이상']}).div(p['연말인구'],axis=0)*100
bands.plot.barh(stacked=True,ax=ax)
ax.set(title='고령층을 연령 구간으로 나눠 지역 지원 검토의 배경을 확인',xlabel='전체 주민 중 비율 (%)',ylabel='')
finish(fig,'10_고령층_구간','겹치지 않는 연령 구간. 고령 주민 수를 고령 신고 수·독거·고독사 위험으로 바꾸지 않는다.','행정안전부 2024년 12월 연령별 인구 CSV')

def status_chart(name,title,rows,note):
    fig,ax=plt.subplots(figsize=(12,5.5)); ax.axis('off'); ax.set_title(title,loc='left')
    for i,(left,right) in enumerate(rows):
        y=.85-i*.18
        ax.text(.02,y,left,weight='bold',va='top',color=C['primary'],fontsize=12)
        ax.text(.31,y,right,va='top',fontsize=11)
        ax.axhline(y-.11,xmin=.02,xmax=.97,color=C['grid'])
    finish(fig,name,note,'이번 로컬 파일 점검 및 위 1차 분석 결과 · 미확보는 서비스 부재를 의미하지 않음')

status_chart('11_지원범위_근거공백','실제 지원 공백을 판정하기 위해 필요한 근거',[
    ('현재 계산 가능','주민 연령 구성 · 신고 유형/시기 · 소방관서 소재지별 자원'),
    ('지원 대상·지역','사업별 이용 자격, 담당 구역, 실제 이용자 지역 자료 필요'),
    ('운영·수용 능력','운영 요일/시간, 정원, 담당 인원, 대기자·거절 기록 필요'),
    ('현 단계 결론','기존 시설·사업이 없거나 미지원 지역이라고 판정하지 않음')],
    '지원범위 축은 데이터 확보 현황의 시각화다. 실제 서비스 커버리지 분석은 미완료다.')
status_chart('12_정책판단_다음검증','분석에서 정책으로 넘어갈 때의 판단 조건',[
    ('소방 대응 보완','기록상 센터 구성 → 실제 출동/동시수요/도착시간 검증\n→ 취약 시간·구역이 반복될 때 배치 시나리오 비교'),
    ('고령층 지원','고령 주민 맥락 → 실제 지원 대상·기존 사업 이용 공백 검증\n→ 방문건강·돌봄 연계 대안을 담당 기관과 검토'),
    ('일자리 제안','수행 가능한 비의료 업무·훈련·감독·예산 먼저 확인\n→ 응급처치·전문 돌봄 인력 대체 효과로 표현하지 않음'),
    ('효과 비교','같은 인력·시간·예산에서 도달 범위·대기·업무부담 비교\n→ 현재 자료만으로 개선율이나 신설 필요성 확정 불가')],
    '정책 방향은 검증할 가설이다. 특정 정책의 효과나 기관 업무 근거를 이번 분석에서 확정하지 않았다.')

checks.update({'C_total':len(reports),'C_unique_ids':int(reports.DCLR_RCPT_NO.nunique()),
               'district_count':len(counts),'type_sum_matches':bool(composition.loc[DIST].sum(axis=1).equals(counts.reindex(DIST))),
               'staff_unmatched':int(fac['출동가능 인원수'].isna().sum()),'vehicle_unmatched':int(fac['차량 대수(대)'].isna().sum()),
               'population_age_sums':'전체 행 일치','raw_or_preprocessed_modified':False})
assert checks['district_count']==16 and checks['type_sum_matches']
assert checks['staff_unmatched']==0 and checks['vehicle_unmatched']==0
latest=joined[joined['연도']==2024].set_index('지역')
lines=['# 부산진구·중구 신고 기반 정책 검토 — 1차 분석',
       '', '## 지금 확인한 결과', '',
       '| 지역 | C 신고 5년 합계 | 2024 C 신고 | 2024 연말 주민 | 65세 이상 비율 |',
       '|---|---:|---:|---:|---:|']
for region in DIST:
    r=latest.loc[region]
    lines.append(f'| {region} | {counts[region]:,} | {int(r["신고건수"]):,} | {int(r["연말인구"]):,} | {r["65세이상비율"]:.1f}% |')
lines += ['', '**현재 결과로 좁힐 수 있는 후속 질문**', '']
for region in DIST:
    r=latest.loc[region]
    emergency=composition.loc[region,'구급']/counts[region]*100
    lines.append(f'- {region}: 구급은 C 신고의 {emergency:.1f}%. 2024년 연말 주민 1천 명 대비 C 신고는 {r["연말주민1천명대비신고"]:.1f}건. 구급 세부유형과 기존 건강·돌봄 지원의 대상·시간 범위가 맞는지 후속 확인한다.')
lines += ['- 부산진구는 신고 총량이 크고, 중구는 고령 주민 비율과 주민 규모 대비 신고가 높다. 두 구를 같은 이유로 선정하거나 같은 정책으로 묶을 근거는 부족하다.',
          '- 중구의 신고 기록에는 소재지가 서구인 부민·충무119안전센터도 나타난다. 현재 위치 원표와 과거 기록을 대조한 단서이며 실제 지원 출동을 입증하지 않는다. 구 안의 2개 센터만으로 대응 범위를 계산하면 안 된다.',
          '- 고령 비율과 구급 비율을 함께 제시해도 고령자가 구급 신고를 했다는 증거가 아니다. 고독사 예방·보건소 신설·노인 일자리 확대 필요성은 추가 자료로 검증해야 한다.']
lines += ['', '## 읽는 기준', '',
          '- 2020–2024년 C 조건을 주 분석으로 사용. A·B·C별 연도·지역 민감도 표 제공.',
          '- A: 부산 명시 + 선택 17개 완전기재. B: A 중 정상. C: B 중 업무운행·훈련출동·구급차소독 제외.',
          '- 원신고 4,552,768건 → A 704,689건 → B 579,412건 → C 574,662건. C는 전체 신고의 대표 표본으로 보장되지 않는다.',
          '- 동일 접수번호는 C 내 중복 없음. 반복 신고자·동일 사고 연결 키는 검증되지 않아 반복 사고율을 계산하지 않았다.',
          '- 공간 집중은 원문 동명 기준. 법정동·행정동 불일치 때문에 동별 인구율로 임의 결합하지 않았다.',
          '- 공식 컬럼표는 PLCSCN_CNTR_NM을 관할서센터명(발생지역에 실제 초동 대응을 수행하는 센터)으로 설명한다. 이번에는 이 신고 필드의 구성을 집계했으며 출동실적·도착시간 로그와 대조하지 않았다.',
          '- 구 인구는 26110(중구), 26230(부산진구)의 10자리 지역코드와 연도로 선택. 신고의 구명은 이 코드와 명시적으로 대응한다.',
          '- 소방자원은 소재지 기준이며 실제 관할·교대 가용량·자료 기준일은 미확인. 신고/센터 비율만으로 부족을 판정하지 않는다.',
          '- 원격 develop은 로컬보다 UI 관련 2개 커밋 앞섰다. 이 분석은 로컬 검증된 전처리 파일로 수행하며 웹 파일은 변경하지 않았다.',
          '', '## 분석 축별 그림과 해석', '']
for name,note in charts:
    lines += [f'### {name}',note,f'![{name}](../../figures/부산진구-중구-1차분석/{name}.png)','']
lines += ['## 다음 확보 자료와 판단',
          '- 접근성: 시점이 맞는 도로망·통행조건, 출동/도착 시각, 관할·상호지원 및 실제 교대 가용 자료. 지금 그림 08은 기록상 센터 구성까지만 확인했다.',
          '- 지원범위: 보건·돌봄 사업별 담당 구역·자격·시간·정원·실제 이용·대기 자료. 로컬 파일에서 측정 가능한 원본을 확인하지 못했다. 기존 공개 웹 분석 문서의 주장만으로 대체하지 않았다.',
          '- 정책 효과: 비교할 대안과 같은 예산·인력 조건이 정해진 후 검증. 노인 일자리·보건소 신설이 필요하다는 결론은 현재 미확정.',
          '', '## 재현', '`.venv/Scripts/python.exe -X utf8 analysis/01_쏠림진단/analyze_two_districts.py`',
          'CSV는 같은 폴더, 원본 해시·출력 해시·검증 요약은 manifest.json. PNG·SVG는 figures/부산진구-중구-1차분석.']
(OUT/'분석보고서.md').write_text('\n'.join(lines),encoding='utf-8')
cards=''.join(f'<section><h2>{html.escape(n)}</h2><p>{html.escape(note)}</p><img src="../../figures/부산진구-중구-1차분석/{n}.png"></section>' for n,note in charts)
(OUT/'시각화.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>부산진구·중구 1차 분석</title><style>body{font-family:Malgun Gothic,sans-serif;background:#f2f5f7;color:#163447;max-width:1200px;margin:32px auto;padding:0 24px}section{background:white;padding:24px;margin:24px 0;border-radius:14px}img{width:100%;height:auto}p{line-height:1.8}h2{font-size:21px}</style><h1>부산진구·중구 신고 기반 정책 검토</h1><p>2020–2024 · C 조건 574,662건에서 두 구 분석<br>8개 축, 그림 12개. 접근성과 실제 지원범위는 추가 원본이 필요하며 현재 그림은 사전 진단과 근거 공백을 보여줍니다.</p>'+cards+'</html>',encoding='utf-8')
outputs={str(p.relative_to(ROOT)):digest(p) for p in list(OUT.glob('*'))+list(FIG.glob('*')) if p.is_file() and p.name not in ('manifest.json','독립검증.json','브라우저검증.json')}
(OUT/'manifest.json').write_text(json.dumps({'generated_at':datetime.now().isoformat(),'inputs_sha256':inputs,'checks':checks,'outputs_sha256':outputs},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'checks':checks,'summary':latest.loc[DIST].to_dict('index'),'charts':len(charts)},ensure_ascii=False,indent=2))
