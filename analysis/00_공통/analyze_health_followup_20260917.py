"""Link selected call profiles to independent public health/context evidence.

Does not attribute district survey outcomes to a dong or link individuals.
"""
from pathlib import Path
import hashlib, json, re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/신고보건심화-20260917'
SRC=OUT/'sources'; OUT.mkdir(parents=True,exist_ok=True)
OLD=ROOT/'data/processed/효과근거확장-20260916/context'
BASE=ROOT/'data/processed/신고주민연결심화-20260917/direction-connections'
FIG=ROOT/'figures/신고보건심화-20260917';FIG.mkdir(parents=True,exist_ok=True)
BOOKS={g:SRC/f'chs2024-{g}.xlsx' for g in ['북구','사하구']}
BOOKS.update({g:OLD/f'chs-{g}-tables.xlsx' for g in ['부산진구','연제구','수영구']})
CORE=[
 '연간 미충족의료율(병의원)',
 '고혈압 진단 경험률_30','고혈압 진단 경험자의 치료율_30','고혈압 관리교육 이수율_30',
 '당뇨병 진단 경험률_30','당뇨병 진단 경험자의 치료율_30','당뇨병 관리교육 이수율_30',
 '연간 사고 및 중독 경험률','연간 사고 및 중독 건수율',
]
PREFIX=['미충족의료 이유(병의원)_','사고 및 중독 원인_']
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def decode(v):
    m=re.fullmatch(r'([\d.]+)\(([\d.]+)\)',str(v))
    return (float(m[1]),float(m[2])) if m else (None,None)

# Keep the unweighted respondent/event denominator, published estimate, SE and RSE.
# Suppressed cells are never converted to 0. Formal education is not all counseling.
rows=[];inputs=[];definitions=[]
for gu,path in BOOKS.items():
    inputs.append(dict(file=str(path.relative_to(ROOT)),sha256=digest(path),role='CHS district survey 2024'))
    book=pd.ExcelFile(path)
    data=pd.read_excel(book,sheet_name='data',dtype=str)
    chosen=data[data.kor_var.isin(CORE)|data.kor_var.str.startswith(tuple(PREFIX),na=False)]
    for source_index,r in chosen.iterrows():
        if pd.isna(r.class_nm): continue
        sex_columns=[('전체','n0','m_se0','rse0'),('남자','n1','m_se1','rse1'),('여자','n2','m_se2','rse2')] if r.type=='type1' else [('별도 성 구분 없음','N','M_SE','rse')]
        for sex,ncol,vcol,rcol in sex_columns:
            if pd.isna(r[ncol]): continue
            value,se=decode(r[vcol]);rse=pd.to_numeric(r[rcol],errors='coerce')
            # RSE >=25% is a conservative project display flag, not a validity test.
            status='표본 부족 등 공표값 없음' if value is None else '정밀도 주의' if pd.notna(rse) and rse>=25 else '공표값'
            rows.append(dict(district=gu,year=2024,indicator=r.kor_var,group=r.class_nm,sex=sex,
                n=int(r[ncol]),estimate=value,se=se,rse=None if pd.isna(rse) else float(rse),
                lower_approx95=None if value is None else max(0,value-1.96*se),
                upper_approx95=None if value is None else min(1000 if '건수율' in r.kor_var else 100,value+1.96*se),
                status=status,published_value=r[vcol],source_file=str(path.relative_to(ROOT)),source_excel_row=source_index+2,
                unit='1,000명당 사고·중독 건수' if '건수율' in r.kor_var else '%'))
    for sheet in book.sheet_names:
        if any(k in sheet for k in ['미충족의료','사고및중독','고혈압','당뇨병']):
            frame=pd.read_excel(book,sheet_name=sheet,header=None,dtype=str)
            notes=[str(v) for v in frame.to_numpy().flatten() if isinstance(v,str) and re.match(r'\s*(주\s*\d|\d\))',v)]
            definitions.append(dict(district=gu,sheet=sheet,notes=notes))

long=pd.DataFrame(rows)
assert not long.duplicated(['district','indicator','group','sex']).any()
long.to_csv(OUT/'health-indicators-all-published-groups.csv',index=False,encoding='utf-8-sig')
summary=long[(long.group=='전체')&long.sex.isin(['전체','별도 성 구분 없음'])].copy()
summary.to_csv(OUT/'health-district-summary-2024.csv',index=False,encoding='utf-8-sig')
(OUT/'indicator-definition-footnotes.json').write_text(json.dumps(definitions,ensure_ascii=False,indent=2),encoding='utf-8')

# 2023's old download route has different workbooks: read visible tables by labels.
# Limit cross-year comparisons to unchanged core indicators, not changed reason options.
trend_keys=[CORE[0],CORE[2],CORE[3],CORE[5],CORE[6]]
trend=summary[summary.district.isin(['북구','사하구','부산진구'])&summary.indicator.isin(trend_keys)].to_dict('records')
for gu in ['북구','사하구','부산진구']:
    path=SRC/f'chs2023-{gu}.xlsx'
    w=openpyxl.load_workbook(path,read_only=True,data_only=True)
    inputs.append(dict(file=str(path.relative_to(ROOT)),sha256=digest(path),role='CHS 2023 same-indicator persistence check'))
    for indicator in trend_keys:
        wanted='<표>'+indicator.removesuffix('_30').replace(' ','')
        sheet=next(s for s in w if s.title.replace(' ','')==wanted)
        records=list(sheet.values)
        label='30세 이상' if indicator.endswith('_30') else '전체'
        match=[]
        for row_index,row in enumerate(records):
            for col,cell in enumerate(row[:2]):
                if str(cell).startswith(label) and col+3<len(row) and decode(row[col+2])[0] is not None:
                    match.append((row_index,col,row))
        assert len(match)==1,(gu,indicator,len(match))
        row_index,col,row=match[0];estimate,se=decode(row[col+2]);rse=float(row[col+3])
        trend.append(dict(district=gu,year=2023,indicator=indicator,group='전체',sex='전체',n=int(row[col+1]),
            estimate=estimate,se=se,rse=rse,lower_approx95=max(0,estimate-1.96*se),upper_approx95=min(100,estimate+1.96*se),
            status='정밀도 주의' if rse>=25 else '공표값',published_value=row[col+2],source_file=str(path.relative_to(ROOT)),
            source_excel_row=row_index+1,source_sheet=sheet.title,unit='%'))
        notes=[str(v) for rr in records for v in rr if isinstance(v,str) and ('× 100' in v or '×100' in v)]
        definitions.append(dict(district=gu,year=2023,sheet=sheet.title,notes=notes))
trend=pd.DataFrame(trend).sort_values(['indicator','district','year'])
trend.to_csv(OUT/'health-same-indicators-2023-2024.csv',index=False,encoding='utf-8-sig')
(OUT/'indicator-definition-footnotes.json').write_text(json.dumps(definitions,ensure_ascii=False,indent=2),encoding='utf-8')

calls=pd.read_csv(BASE/'major-burden-top10.csv')
time=pd.read_csv(BASE/'major-burden-time-summary.csv')
targets=[('사하구','다대동','질병'),('북구','금곡동','질병'),('부산진구','부전동','질병외'),('부산진구','부전동','부상')]
linked=[]
for gu,dong,sub in targets:
    q=calls[(calls.district==gu)&(calls.rawDong==dong)&(calls.subtype==sub)]
    assert len(q)==1
    r=q.iloc[0].to_dict()
    t=time[(time.district==gu)&(time.rawDong==dong)&(time.subtype==sub)&(time.scope=='P')&(time.year==0)]
    assert len(t)==1
    r['night20to07Pct']=float(t.iloc[0].night20to07Pct)
    for indicator,key in [('연간 미충족의료율(병의원)','districtUnmetMedicalPct'),('고혈압 관리교육 이수율_30','districtHypertensionEducationPct'),('당뇨병 관리교육 이수율_30','districtDiabetesEducationPct')]:
        x=summary[(summary.district==gu)&(summary.indicator==indicator)].iloc[0]
        r[key]=x.estimate
    r['healthSpatialScope']='구 전체 조사; 해당 동 신고자 또는 동별 유병률 아님'
    linked.append(r)
pd.DataFrame(linked).to_csv(OUT/'selected-region-evidence-links.csv',index=False,encoding='utf-8-sig')
for p in [BASE/'major-burden-top10.csv',BASE/'major-burden-time-summary.csv',BASE/'major-burden-population-candidates.csv',BASE/'major-burden-commerce-share-range.csv',BASE/'major-burden-living-candidates-2023-2024.csv']:
    inputs.append(dict(file=str(p.relative_to(ROOT)),sha256=digest(p),role='reused verified call/population/context evidence'))

plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f7fafb','axes.facecolor':'#f7fafb','text.color':'#183644','axes.labelcolor':'#183644'})
order=['북구','부산진구','사하구','연제구','수영구']
def vals(ind):return summary[summary.indicator==ind].set_index('district').loc[order]
def errors(frame):return np.vstack([frame.estimate-frame.lower_approx95,frame.upper_approx95-frame.estimate])
def save(fig,name):
    fig.savefig(FIG/f'{name}.png',dpi=170,bbox_inches='tight');fig.savefig(FIG/f'{name}.svg',bbox_inches='tight');plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(14,6),gridspec_kw={'width_ratios':[1,1.4]})
x=vals('연간 미충족의료율(병의원)');y=np.arange(5)
axes[0].errorbar(x.estimate,y,xerr=errors(x),fmt='o',color='#087f8c',markersize=9,capsize=4)
for j,r in enumerate(x.itertuples()):axes[0].annotate(f'{r.estimate:.1f}% · n={r.n}',(r.upper_approx95+.35,j),fontsize=11,va='center')
axes[0].set(yticks=y,yticklabels=order,xlim=(0,22),xlabel='진료가 필요했던 응답자 중 비율(%)',title='북구·부산진구에서 의료 미이용 경험 확인')
axes[0].invert_yaxis();axes[0].grid(axis='x',alpha=.15)
reason_names=['시간이 없어서','증세가 가벼워서','경제적인 이유']
colors=['#087f8c','#de8847','#719a54']
for j,(reason,color) in enumerate(zip(reason_names,colors)):
    r=vals('미충족의료 이유(병의원)_'+reason)
    axes[1].errorbar(r.estimate,y+(j-1)*.2,xerr=errors(r),fmt='o',label=reason,color=color,capsize=3,markersize=6)
axes[1].set(yticks=y,yticklabels=order,xlabel='진료가 필요했던 응답자 중 각 사유의 비율(%)',title='의료 미이용의 사유도 지역에 따라 다름',xlim=(-.2,10))
axes[1].invert_yaxis();axes[1].grid(axis='x',alpha=.15);axes[1].legend(loc='lower right',frameon=False,fontsize=11)
fig.suptitle('신고·인구 다음 단계: 실제 의료 이용 경험으로 보완 방향 구분',fontsize=20,fontweight='bold',y=1.03)
fig.text(.02,-.055,'2024 지역사회건강조사 · 구 전체 조율 · 선은 공표 SE로 계산한 근사 95% 범위\n부전·금곡·다대동의 수치나 신고 원인이 아님. 구별 순위·통계적 유의차를 주장하지 않음.',fontsize=11)
fig.tight_layout();save(fig,'01-의료이용-추가근거')

fig,axes=plt.subplots(1,2,figsize=(14,5.3))
for ax,disease in zip(axes,['고혈압','당뇨병']):
    for j,(suffix,color,label) in enumerate([('진단 경험자의 치료율_30','#087f8c','치료'),('관리교육 이수율_30','#de8847','관리교육 경험')]):
        x=vals(disease+' '+suffix).loc[['북구','사하구','부산진구']]
        ax.errorbar(x.estimate,np.arange(3)+(j-.5)*.16,xerr=errors(x),fmt='o',color=color,label=label,capsize=4,markersize=8)
        for i,r in enumerate(x.itertuples()):ax.annotate(f'{r.estimate:.1f}%',(r.estimate,i+(j-.5)*.16),xytext=(0,12 if j==0 else -20),textcoords='offset points',ha='center',fontsize=12)
    ax.set(yticks=range(3),yticklabels=['북구','사하구','부산진구'],xlim=(-6,109),xlabel='30세 이상 해당 질환 진단 경험자 중 비율(%)',title=disease)
    ax.set_ylim(2.6,-.45);ax.grid(axis='x',alpha=.15)
axes[1].legend(loc='lower center',bbox_to_anchor=(.45,-.28),ncol=2,frameon=False)
fig.suptitle('치료율은 높고, 관리교육 경험은 낮게 나타남',fontsize=20,fontweight='bold',y=1.03)
fig.text(.01,-.10,'2024 지역사회건강조사 · 구별 조율 · 선은 근사 95% 범위\n교육 경험은 모든 진료·상담을 뜻하지 않음. 두 비율의 차이를 같은 사람의 교육 누락 건수로 계산하지 않음.\n고혈압 교육: 북구 RSE 29.6%, 사하구 33.7%, 부산진구 34.4%. 정밀도가 낮아 작은 차이로 지역 순위를 정하지 않음.',fontsize=11)
fig.tight_layout();save(fig,'02-기존치료와-관리교육')

fig,axes=plt.subplots(1,3,figsize=(14,5.3))
for ax,ind,title in zip(axes,[CORE[0],CORE[3],CORE[6]],['진료 필요자 중 의료 미이용','고혈압 진단자 중 관리교육 경험','당뇨병 진단자 중 관리교육 경험']):
    for j,(gu,color) in enumerate(zip(['북구','사하구','부산진구'],colors)):
        q=trend[(trend.district==gu)&(trend.indicator==ind)].sort_values('year')
        ax.errorbar(q.year+(j-1)*.025,q.estimate,yerr=errors(q),fmt='o-',color=color,capsize=4,label=gu,markersize=7)
    ax.set(xticks=[2023,2024],xticklabels=['2023','2024'],title=title,xlim=(2022.83,2024.17),ylabel='공표 조율(%)')
    ax.grid(axis='y',alpha=.15);ax.set_ylim(bottom=0)
axes[1].legend(loc='upper center',bbox_to_anchor=(.5,-.16),ncol=3,frameon=False)
fig.suptitle('한 해의 수치만으로 보완 방향을 정하지 않음',fontsize=20,fontweight='bold',y=1.03)
fig.text(.02,-.07,'2023·2024 지역사회건강조사 · 매년 다른 표본의 구 전체 지표 · 선은 근사 95% 범위\n연도 차이는 기술 비교이며 사업 효과나 유의한 증감을 뜻하지 않음. 신고 분석은 기존 2020~2024년 유지.',fontsize=11)
fig.tight_layout();save(fig,'03-두해-보건지표-검토')

spec=dict(callPeriod='2020-2024',complete17=704689,primaryScopeP=555786,
    purpose='119 반복 지역에서 보조자료로 필요의 종류를 구분하고 기존 서비스를 활용한 보완 후보를 구체화',
    surveyPeriod='주 분석 2024-05-16~2024-07-31 조사; 2023 같은 지표 5개 별도 비교. 연간 문항은 응답시점 직전 1년',
    surveyPopulation='표본가구 19세 이상; 30세 이상 지표는 해당 기준 및 진단 경험자 분모 적용',
    selectedIndicators=CORE+PREFIX,
    surveyGeography='북구·사하구·부산진구 중심, 기존 연제구·수영구 비교자료 재사용; 부산 전체 순위 아님',
    confidence='공표된 복합표본 SE의 1.96배. 반올림된 수치 기반 근사구간; 다중비교 검정하지 않음',
    precisionRule='RSE >=25%는 프로젝트의 보수적 표시 규칙. 결측/공표중단은 0으로 채우지 않음',
    linkage='구 단위 보조 근거와 원문 지역 신고를 나란히 제시. 개인결합/원인 추정/동별 건강률 배정 없음',
    expectedImpact='기존 서비스 안내 후 실제 교육·상담 연결 완료율을 평가. 사고·119 감소 효과는 미검증',
    inputs=inputs,rows=len(long),summaryRows=len(summary))
(OUT/'analysis-specification.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(rows=len(long),summaryRows=len(summary),inputs=len(inputs),selectedRegions=len(linked)),ensure_ascii=False))
