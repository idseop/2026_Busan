"""Summarize only the current five-year run; never consume legacy analysis outputs."""
from pathlib import Path
import calendar
import hashlib
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/processed/동별예방분석-20260914'
OUT = BASE / 'synthesis'
TYPE, SUB = 'EMRG_RSCU_ASSRT_NM', 'EMRG_RSCU_CLSF_NM'
SGG, EMD = 'CLMTY_SGG_NM', 'CLMTY_EMD_NM'
YEARS = list(range(2020, 2025))

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = []
    def read(name):
        p = BASE / name
        inputs.append({'file':str(p.relative_to(ROOT)), 'sha256':sha(p)})
        return pd.read_csv(p, keep_default_na=False, dtype={'admin_code':str,'district_code':str})
    def save(df, name):
        df.to_csv(OUT / (name+'.csv'), index=False, encoding='utf-8-sig')
    annual = read('receipts/annual_types.csv')
    months = read('receipts/time_month.csv')
    hours = read('receipts/time_hour.csv')
    days = read('receipts/time_date.csv')
    districts = read('receipts/district_types.csv')
    rawdong = read('receipts/original_dong_types.csv')
    pop = read('population/population_summary.csv')
    flow = read('receipts/flow.csv')
    assert set(annual.year) == set(pop.year) == set(YEARS)
    city = annual.groupby(['year','scope'], as_index=False)['count'].sum()
    save(city, 'annual_scopes')
    major = annual.groupby(['year','scope',TYPE], as_index=False)['count'].sum()
    major = major.merge(city.rename(columns={'count':'scope_total'}), on=['year','scope'], validate='many_to_one')
    major['share_pct'] = 100*major['count']/major.scope_total
    save(major, 'annual_major_types')
    # Exhaustive joint type/subtype panel: no weighted score, no hidden type filtering.
    candidates = []
    for key, group in annual.groupby([TYPE,SUB], dropna=False):
        kind, subtype = key
        sums = group.groupby('scope')['count'].sum()
        b = group[group.scope.eq('B')].groupby('year')['count'].sum().reindex(YEARS, fill_value=0)
        m = months[(months[TYPE].eq(kind)) & months[SUB].eq(subtype) & months.scope.eq('B')]
        h = hours[(hours[TYPE].eq(kind)) & hours[SUB].eq(subtype) & hours.scope.eq('B')]
        mt = m.groupby('month')['count'].sum().reindex(range(1,13), fill_value=0)
        rates = mt / pd.Series({mo:sum(calendar.monthrange(y,mo)[1] for y in YEARS) for mo in range(1,13)})
        ht = h.groupby('hour')['count'].sum().reindex(range(24), fill_value=0)
        yearly = []
        for y in YEARS:
            my = m[m.year.eq(y)].groupby('month')['count'].sum().reindex(range(1,13),fill_value=0)
            if my.sum(): yearly.append(int((my/pd.Series({mo:calendar.monthrange(y,mo)[1] for mo in range(1,13)})).idxmax()))
        total = int(b.sum())
        row = {'type':kind, 'subtype':subtype, 'A_count':int(sums.get('A',0)),
               'B_count':total, 'C_count':int(sums.get('C',0)),
               **{f'B_{y}':int(b[y]) for y in YEARS}, 'years_observed_B':int((b>0).sum()),
               'max_year_share_B_pct':100*b.max()/total if total else None,
               'B_share_within_type_pct':100*total/annual.loc[annual.scope.eq('B') & annual[TYPE].eq(kind),'count'].sum(),
               'normal_retention_pct':100*total/sums.get('A',1),
               'peak_month_daily_average_B':int(rates.idxmax()) if total else None,
               'annual_peak_months_daily_average_B':','.join(map(str,yearly)),
               'peak_hour_B':int(ht.idxmax()) if total else None,
               'jul_sep_B_pct':100*mt.loc[7:9].sum()/total if total else None,
               'night_22_05_B_pct':100*ht.loc[[22,23,0,1,2,3,4,5]].sum()/total if total else None,
               'night_18_05_B_pct':100*ht.loc[list(range(18,24))+list(range(6))].sum()/total if total else None,
               'dong_selection_status':'excluded_user_scope' if subtype=='벌집제거' else 'held_unvalidated_linkage',
               'selection_reason':'사용자 지정: 예방·지원 검토 범위에서 제외; 전체 접수 검산에만 보존' if subtype=='벌집제거' else '동별 신고·주민 배경 연결 검증 후 주제 적합성과 보완 필요성 판단',
               'zero_interpretation':'absent observed cells within supplied files; not confirmed population incidence zero'}
        candidates.append(row)
    panel = pd.DataFrame(candidates).sort_values(['type','B_count'],ascending=[True,False])
    save(panel, 'all_type_review_panel')
    # Raw labels only: retain all labels and missing values, never attach MOIS codes.
    r = rawdong.groupby(['year','scope',SGG,EMD,TYPE],as_index=False)['count'].sum()
    den = r.groupby(['year','scope',SGG,EMD],as_index=False)['count'].sum().rename(columns={'count':'raw_label_total'})
    r = r.merge(den,on=['year','scope',SGG,EMD],validate='many_to_one')
    r['share_within_raw_label_pct'] = 100*r['count']/r.raw_label_total
    r['admin_dong_linkage_status'] = 'not_validated'
    save(r, 'raw_label_profile_unlinked')
    dr = districts.groupby(['year','scope',SGG],as_index=False)['count'].sum()
    dr['count_rank_within_scope'] = dr.groupby(['year','scope'])['count'].rank(method='min',ascending=False)
    dr['rank_interpretation'] = 'descriptive count rank only; not policy priority'
    save(dr, 'district_scope_sensitivity')
    peaks = days[days.scope.eq('B')].groupby(['year','date'],as_index=False)['count'].sum()
    save(peaks.sort_values(['year','count'],ascending=[True,False]).groupby('year').head(3), 'annual_top_dates')
    # Structured records for future web work: real population and explicit unavailable metrics.
    dongpop = pop[pop.level.eq('dong')]
    records = []
    for row in dongpop.to_dict('records'):
        records.append({'year':row['year'], 'admin_dong_code':row['admin_code'],
                        'district_code':row['district_code'],'district_name':row['district_name'],
                        'dong_name':row['dong_name'], 'population_reference_date':row['population_reference_date'],
                        'population':row['population'], 'age_details_source':'../population/dong_single_age.csv',
                        'receipt_metrics':None,'linkage_status':'not_validated',
                        'boundary_version':None, 'response_evidence':None,'gap_status':'unverified',
                        'proposal_candidate':None,'source_file':row['source_file'],'source_row':row['source_row']})
    (OUT/'map_population_records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    # Exportable figures: distinct scales and no ecological relation implied.
    plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':10})
    fig, axes = plt.subplots(1,2,figsize=(12,4.8))
    for scope,label in [('A','전체 처리'),('B','정상'),('C','정상·운영성 분류 제외')]:
        z=city[city.scope.eq(scope)]
        axes[0].plot(z.year,z['count']/10000,marker='o',label=label)
    axes[0].set(title='부산 명시 접수: 포함조건 비교',ylabel='접수행수 (만 행)',xticks=YEARS)
    axes[0].legend(fontsize=8); axes[0].grid(alpha=.2)
    flows=flow.groupby(['year','region_status'])['count'].sum().unstack(fill_value=0)
    axes[1].bar(YEARS,flows['busan_explicit']/10000,label='부산 명시')
    axes[1].bar(YEARS,flows['province_missing']/10000,bottom=flows['busan_explicit']/10000,label='재난시도 미기재')
    axes[1].set(title='원본 지역 기재 범위',ylabel='접수행수 (만 행)',xticks=YEARS); axes[1].legend(fontsize=8)
    fig.text(.5,.01,'접수는 실제 사건·출동·환자 수가 아님. 미기재는 부산 밖으로 판정하지 않음.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'receipt_scope.png',dpi=160);plt.close(fig)
    # Show the citywide starting point, not a preselected policy or subtype.
    fig, axes=plt.subplots(2,2,figsize=(12,8))
    for ax,kind in zip(axes.flat,['구급','구조','화재','기타']):
        for y in YEARS:
            z=months[months.scope.eq('B') & months[TYPE].eq(kind) & months.year.eq(y)]
            s=z.groupby('month')['count'].sum().reindex(range(1,13),fill_value=0)
            s=s/pd.Series({m:calendar.monthrange(y,m)[1] for m in range(1,13)})
            ax.plot(s.index,s.values,label=str(y),marker='.',lw=1.3)
        ax.set(title=f'{kind} · 전체 세부분류',xlabel='월',ylabel='해당 월 달력 일수당 접수행수',xticks=range(1,13));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.text(.5,.01,'부산 명시·정상 처리. 접수 시점의 분포이며 발생 원인이나 대응 공백을 의미하지 않음.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'monthly_review.png',dpi=160);plt.close(fig)
    age=read('population/age_decade_all_levels.csv'); age=age[age.level.eq('city')]
    order=[f'{i}~{i+9}' for i in range(0,100,10)]+['100+']
    fig,ax=plt.subplots(figsize=(10,4.8))
    for y in YEARS:
        z=age[age.year.eq(y)].set_index('age_group').reindex(order)
        ax.plot(order,z['share_pct'],marker='.',label=str(y))
    ax.set(title='부산시 연말 주민의 전체 연령 구성',ylabel='해당 연도 인구 내 비중 (%)',xlabel='연령 구간');ax.legend();ax.grid(alpha=.2)
    fig.text(.5,.01,'12월 말 주민등록인구. 신고 대상자의 연령 분포가 아님.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1));fig.savefig(OUT/'population_age.png',dpi=160);plt.close(fig)
    assert len(records)==1025 and all(x['receipt_metrics'] is None for x in records)
    (OUT/'manifest.json').write_text(json.dumps({'years':YEARS,'inputs':inputs,'script':str(Path(__file__).relative_to(ROOT)),
        'script_sha256':sha(Path(__file__)),'panel_policy':'All observed labels retained for total reconciliation. 벌집제거 explicitly excluded from focus/research/proposals per user scope. Other dong selection held pending validated linkage and subject relevance. No weighted score.',
        'peak_tie_policy':'Earliest month/hour shown when maximum is tied; descriptive only.',
        'method':'Descriptive counts, composition, repeated-year and alternative processing/time-window comparisons; no hypothesis test or prediction.',
        'zero_policy':'No spatially unlinked value filled with zero. Year/subtype absence is observed-file absence, not verified event absence.',
        'outputs':[{'file':p.name,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'panel_rows':len(panel),'map_records':len(records),'outputs':len(list(OUT.iterdir()))},ensure_ascii=False))

if __name__=='__main__':main()
