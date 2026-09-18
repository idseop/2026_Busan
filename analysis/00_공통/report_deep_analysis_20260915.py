"""Create standalone case figures and auditable descriptive summaries."""
from pathlib import Path
import json
import hashlib
import calendar
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/심층분석-20260915'

def main():
    d=json.loads((OUT/'deep-data.json').read_text(encoding='utf-8'))
    pop=json.loads((ROOT/'web/final/data/dashboard.json').read_text(encoding='utf-8'))['population']
    f=pd.read_csv(OUT/'case_weekday_hour.csv');m=pd.read_csv(OUT/'case_month.csv')
    figs=OUT/'figures';figs.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'figure.facecolor':'#f4f7f9','axes.facecolor':'white','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','font.size':10})
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    summaries=[]
    for c,ax in zip(d['cases'],axes.flat):
        years=d['meta']['years'];current=c['yearCounts'];baseline=c['core8YearCounts']
        ax.plot(years,baseline,color='#98a5b2',marker='o',label='기본 8개 완전행 · 비교용')
        ax.plot(years,current,color='#167f88',marker='o',linewidth=2.5,label='선택 17개 완전행 · 분석대상')
        for y,n in zip(years,current):ax.annotate(f'{n:,}',(y,n),xytext=(0,-18),textcoords='offset points',ha='center',fontsize=9,color='#12666e')
        ax.set_title(c['title'],loc='left');ax.set_xticks(years);ax.set_ylim(bottom=0);ax.set_ylabel('신고접수 건수');ax.grid(axis='y',alpha=.12);ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
        sub=f[(f.caseIndex==c['index'])&(f.scopeIndex==2)]
        table=sub.pivot_table(index='weekday',columns='hourBandIndex',values='count',aggfunc='sum',fill_value=0).reindex(index=range(7),columns=range(6),fill_value=0)
        months=m[(m.caseIndex==c['index'])&(m.scopeIndex==2)].groupby('month')['count'].sum().reindex(range(1,13),fill_value=0)
        days={mo:sum(calendar.monthrange(y,mo)[1] for y in years) for mo in range(1,13)}
        rates={mo:float(months[mo]/days[mo]) for mo in range(1,13)}
        linked=next((r for r in c['populationLinks'] if r['year']==2024 and r['codeLevelEligible']),None)
        p=next((r for r in pop if r['year']==2024 and linked and r['code']==linked['uniqueCode']),None)
        population=None if not p else {'year':2024,'name':p['name'],'code':p['code'],'total':p['total'],'age0to14':sum(p['ages'][:15]),'age15to64':sum(p['ages'][15:65]),'age65plus':sum(p['ages'][65:]),'age65plusShare':sum(p['ages'][65:])/p['total'],'conditional':True}
        peak_hour=int(table.sum(axis=0).idxmax());peak_day=int(table.sum(axis=1).idxmax())
        summaries.append({'id':c['id'],'title':c['title'],'scope':'C','years':years,'total':sum(current),'core8Total':sum(baseline),'retention':sum(current)/sum(baseline),'yearCounts':current,'core8YearCounts':baseline,
                          'peakHourBand':d['meta']['hourBands'][peak_hour],'peakHourBandCount':int(table[peak_hour].sum()),'weekdayCounts':[int(v) for v in table.sum(axis=1)],'peakWeekday':d['meta']['weekdayLabels'][peak_day],
                          'monthCounts':[int(v) for v in months],'calendarDaysByMonth':days,'monthPerCalendarDay':rates,'population2024':population})
    axes.flat[0].legend(fontsize=8,frameon=False)
    fig.suptitle('반복 관측 4사례: 같은 신고 분류도 결측 제외의 영향이 다르다\n2020–2024 · C 정상 처리 중 운영성 분류 제외 · 원문 지역명 기준',fontsize=14)
    for ext in ['png','svg']:fig.savefig(figs/f'01_case_trends.{ext}',dpi=160)
    plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for c,ax in zip(d['cases'],axes.flat):
        sub=f[(f.caseIndex==c['index'])&(f.scopeIndex==2)]
        table=sub.pivot_table(index='weekday',columns='hourBandIndex',values='count',aggfunc='sum',fill_value=0).reindex(index=range(7),columns=range(6),fill_value=0)
        im=ax.imshow(table.to_numpy(),cmap='GnBu',aspect='auto',vmin=0)
        ax.set_xticks(range(6),d['meta']['hourBands']);ax.set_yticks(range(7),d['meta']['weekdayLabels']);ax.set_title(c['title'],loc='left')
        for i in range(7):
            for j in range(6):ax.text(j,i,str(table.iloc[i,j]),ha='center',va='center',fontsize=9,color='white' if table.iloc[i,j]>table.to_numpy().max()*.65 else '#102b3f')
        fig.colorbar(im,ax=ax,shrink=.8,label='5년 접수 건수 · 사례별 색상 범위')
    fig.suptitle('지역·세부유형별 접수 요일과 시간대\nC 조건 · 각 숫자는 해당 사례의 접수 건수 · 색 농도를 사례 간 직접 비교하지 않음',fontsize=14)
    for ext in ['png','svg']:fig.savefig(figs/f'02_case_weekday_hour.{ext}',dpi=160)
    plt.close(fig)
    (OUT/'case_findings.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
    paths=[OUT/'case_findings.json',*sorted(figs.glob('*'))]
    inputs=[OUT/'deep-data.json',OUT/'case_weekday_hour.csv',OUT/'case_month.csv',ROOT/'web/final/data/dashboard.json']
    hashes=lambda ps:[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in ps]
    (OUT/'figure_manifest.json').write_text(json.dumps({'inputSha256':hashlib.sha256((OUT/'deep-data.json').read_bytes()).hexdigest(),'inputs':hashes(inputs),'generator':hashes([Path(__file__)])[0],'outputs':hashes(paths)},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summaries,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
