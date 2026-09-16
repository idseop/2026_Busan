"""Package verified aggregates for the final local dashboard and export report figures.

No receipt identifiers, precision coordinates or individual records are published.
The approved selected17 membership is unchanged. Raw dong labels are not polygons.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, hashlib, calendar
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/최종결과-20260915'
WEB=ROOT/'web/final/data'
ANALYSIS=ROOT/'data/processed/동대응-전체결측제외-20260915/analysis'
LINKAGE=ROOT/'data/processed/동대응-전체결측제외-20260915/linkage'
COMPLETE=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
POP=ROOT/'data/processed/컬럼선별-결측제외-20260915/population'
SUIT=ROOT/'data/processed/완전행-분석적합성-20260915'
YEARS=list(range(2020,2025)); TYPES=['구급','구조','화재','기타']
TYPE,SUB,SGG,EMD='EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','CLMTY_SGG_NM','CLMTY_EMD_NM'
SCOPES={'A':'전체 처리결과','B':'정상 처리결과','C':'정상 중 업무운행·훈련출동·구급차소독 제외'}
SEASONS={1:'겨울',2:'겨울',3:'봄',4:'봄',5:'봄',6:'여름',7:'여름',8:'여름',9:'가을',10:'가을',11:'가을',12:'겨울'}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def records(frame): return json.loads(frame.to_json(orient='records',force_ascii=False))
def boolean(value): return str(value).lower()=='true'

def main():
    OUT.mkdir(parents=True,exist_ok=True); WEB.mkdir(parents=True,exist_ok=True)
    figures=OUT/'figures'; figures.mkdir(exist_ok=True)
    inputs=[]; manifests={}
    def read(directory,name,dtype=None):
        if directory not in manifests:
            manifests[directory]=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
        metadata=manifests[directory]
        entries=metadata.get('outputs',metadata.get('output_files'))
        if isinstance(entries,dict):
            expected=entries[name]['sha256'] if isinstance(entries[name],dict) else entries[name]
        else: expected=next(x['sha256'] for x in entries if Path(x['file']).name==name)
        path=directory/name; digest=sha(path); assert digest==expected,f'Input hash mismatch: {path}'
        inputs.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':digest,
            'producerManifest':str((directory/'manifest.json').relative_to(ROOT)).replace('\\','/'),'producerManifestSha256':sha(directory/'manifest.json')})
        return pd.read_csv(path,dtype=dtype,keep_default_na=False)
    annual=read(ANALYSIS,'annual_type.csv')
    scope_counts=read(ANALYSIS,'annual_scope_counts.csv')
    monthly=read(ANALYSIS,'month_type.csv'); weekday=read(ANALYSIS,'weekday_type.csv'); hour=read(ANALYSIS,'hour_band_type.csv')
    region=read(ANALYSIS,'original_region_type.csv')
    cross=read(LINKAGE,'all_raw_names_year_crosswalk.csv',str)
    pop=read(POP,'complete_population_dong.csv',str)
    original=read(COMPLETE,'original_region_classification.csv')
    sensitivity_annual=read(SUIT/'stability','annual_retention.csv')
    sensitivity_threshold=read(SUIT/'stability','five_year_repetition_threshold_sensitivity.csv')
    subtype_sensitivity=read(SUIT/'stability','all_original_dong_subtype_sensitivity.csv')
    channels=read(SUIT/'missingness','channel_retention_counts_retention.csv')
    mobile_shifts=read(SUIT/'missingness','mobile_composition_shift_summary.csv')
    yearly=annual.groupby(['year','scope',TYPE],as_index=False).receipt_count.sum().rename(columns={TYPE:'type','receipt_count':'count'})
    time=[]
    for dimension,frame,field in [('month',monthly,'month'),('weekday',weekday,'weekday'),('hourBand',hour,'hour_band')]:
        grouped=frame.groupby(['year','scope',TYPE,field],as_index=False).receipt_count.sum()
        for row in grouped.to_dict('records'):
            year=int(row['year']); value=row[field]
            dates=pd.date_range(f'{year}-01-01',f'{year}-12-31')
            days=calendar.monthrange(year,int(value))[1] if dimension=='month' else int((dates.dayofweek==int(value)).sum()) if dimension=='weekday' else len(dates)
            time.append({'year':year,'scope':row['scope'],'type':row[TYPE],'dimension':dimension,
                'value':int(value) if dimension!='hourBand' else value,'count':int(row['receipt_count']),'calendarDays':days})
    season=monthly.copy(); season['season']=season.month.map(SEASONS)
    for row in season.groupby(['year','scope',TYPE,'season'],as_index=False).receipt_count.sum().to_dict('records'):
        year=int(row['year']); value=row['season']
        days=sum(calendar.monthrange(year,m)[1] for m in range(1,13) if SEASONS[m]==value)
        time.append({'year':year,'scope':row['scope'],'type':row[TYPE],'dimension':'season','value':value,
            'count':int(row['receipt_count']),'calendarDays':days})
    link={(int(r.year),r.district_name,r.raw_dong_name):r._asdict() for r in cross.itertuples(index=False)}
    core=original.loc[original.stage.eq('core8')].groupby(['year','scope',SGG,EMD,TYPE],as_index=False)['count'].sum()
    core_lookup={(int(r['year']),r['scope'],r[SGG],r[EMD],r[TYPE]):int(r['count']) for r in core.to_dict('records')}
    raw=[]
    for keys,g in region.groupby(['year','scope',SGG,EMD]):
        year,scope,district,dong=keys; mapping=link[(int(year),district,dong)]
        type_counts={t:int(g.loc[g[TYPE].eq(t),'receipt_count'].sum()) for t in TYPES}
        before={t:core_lookup.get((int(year),scope,district,dong,t),0) for t in TYPES}
        assert all(type_counts[t]<=before[t] for t in TYPES)
        raw.append({'year':int(year),'scope':scope,'district':district,'rawDong':dong,'total':sum(type_counts.values()),
            'typeCounts':type_counts,'core8Total':sum(before.values()),'core8TypeCounts':before,
            'linkStatus':mapping['status'],'candidateCodes':[x for x in mapping['candidate_codes'].split('|') if x],
            'uniqueCode':mapping['unique_code'] or None,'codeLevelEligible':boolean(mapping['code_level_population_join_eligible']),
            'geographyConfirmed':False})
    population=[]
    for r in pop.to_dict('records'):
        ages=[int(r[f'age_{i}']) for i in range(101)]; total=int(r['population']); assert sum(ages)==total
        population.append({'year':int(r['year']),'referenceDate':r['population_reference_date'],'districtCode':r['district_code'],
            'district':r['district_name'],'code':r['admin_dong_code'],'name':r['admin_dong_name'],'total':total,'ages':ages})
    assert len(population)==1025
    assert all(sum(r['year']==y for r in population)==205 for y in YEARS)
    assert len({(r['year'],r['code']) for r in population})==1025
    population_keys={(r['year'],r['code']) for r in population}
    for r in raw:
        if r['codeLevelEligible']: assert (r['year'],r['uniqueCode']) in population_keys
    all_candidates=[]
    candidate_source=subtype_sensitivity.loc[subtype_sensitivity.scope.eq('C')&~subtype_sensitivity[SUB].eq('벌집제거')].copy()
    candidate_source=candidate_source.loc[candidate_source[[f'complete17_{y}' for y in YEARS]].gt(0).all(axis=1)]
    for r in candidate_source.sort_values([SGG,EMD,TYPE,SUB]).to_dict('records'):
        after=[int(r[f'complete17_{y}']) for y in YEARS]; before=[int(r[f'core8_{y}']) for y in YEARS]
        minimum=min(after); status='반복 관측 확인 · 정책 우선순위 보류'
        identifier=hashlib.sha256('|'.join([r[SGG],r[EMD],r[TYPE],r[SUB]]).encode()).hexdigest()[:12]
        reversal=(before[-1]-before[0])*(after[-1]-after[0])<0
        geography=[link[(y,r[SGG],r[EMD])] for y in YEARS]
        eligible=all(boolean(g['code_level_population_join_eligible']) for g in geography)
        all_candidates.append({'id':identifier,'title':f'{r[SGG]} {r[EMD]} · {r[SUB]}','district':r[SGG],'rawDong':r[EMD],
            'type':r[TYPE],'subtype':r[SUB],'scope':'C','years':YEARS,'yearCounts':after,'core8YearCounts':before,
            'minAnnualCount':minimum,'thresholdPass':{str(k):minimum>=k for k in [1,5,10,20]},
            'directionReversal':reversal,'retention':sum(after)/sum(before),'status':status,
            'scopeDescription':'2020~2024년 C조건의 매년 양수 관측 전체 목록. 1·5·10·20은 탐색용이며 후보 통과선이 아닙니다.',
            'receiptEvidence':f'선택17 연도별 {" / ".join(map(str,after))}건. 기본8 {" / ".join(map(str,before))}건. 필터 전후 증감 방향 '+('반전.' if reversal else '반전 없음.'),
            'residentEvidence':('연도별 코드 수준 단일 대응 후보는 있으나 실제 신고 행정동은 미확정입니다.' if eligible else '원문명칭의 행정동 대응을 추가 확인해야 하므로 주민 연령 배경의 자동 결합을 보류합니다.'),
            'responseEvidence':'해당 원문지역에 대한 서비스 대상·운영시간·이용조건·운영 범위 대조는 미완료입니다. 공식 기존 서비스 안내는 기존 대응 패널에서 확인할 수 있습니다.',
            'neededEvidence':'접수경로·현장구군 기록 규칙, 원문지역과 공식 경계의 시점별 대응, 해당 신고 유형에 필요한 현장 배경과 기존 대응 확인.',
            'proposalStatus':'정책·시설·인력 배치 제안 보류. 반복 관측은 대응 공백이나 인과관계의 증거가 아닙니다.',
            'sources':['selected17_analysis','stability','linkage','population','suitability']})
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['thresholdPass','sources','years']}|{f'threshold_{t}':r['thresholdPass'][str(t)] for t in [1,5,10,20]} for r in all_candidates]).to_csv(OUT/'repeated_observation_exploration.csv',index=False,encoding='utf-8-sig')
    channel_summary=channels.loc[channels.scope.eq('A')].groupby('RCPT_PATH_NM',as_index=False)[['core8','selected17']].sum().rename(columns={'RCPT_PATH_NM':'name','selected17':'complete17'})
    sources=[
        {'id':'selected17_analysis','title':'선택17 완전행 신고 집계','path':str((ANALYSIS/'manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(ANALYSIS/'manifest.json')},
        {'id':'linkage','title':'공식 코드 관계·시점별 원문명칭 대응 검토','path':str((LINKAGE/'manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(LINKAGE/'manifest.json'),'publicUrl':'https://www.code.go.kr/'},
        {'id':'population','title':'행정안전부 연말 주민등록 인구: 부산 205개 읍면동','path':str((POP/'manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(POP/'manifest.json'),'publicUrl':'https://jumin.mois.go.kr/ageStatMonth.do'},
        {'id':'stability','title':'조건·반복 기준별 결과 민감도','path':str((SUIT/'stability/manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(SUIT/'stability/manifest.json')},
        {'id':'missingness','title':'접수경로·이동전화 내부의 결측 선택 평가','path':str((SUIT/'missingness/manifest.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(SUIT/'missingness/manifest.json')},
        {'id':'suitability','title':'완전행 분석 사용 범위 결정','path':str((SUIT/'analysis_use_decision.json').relative_to(ROOT)).replace('\\','/'),'sha256':sha(SUIT/'analysis_use_decision.json')},
    ]
    extra_evidence={}
    evidence_titles={'ansim2023':'119안심콜 공식 안내(2023)','ansim2024':'119안심콜 공식 안내(2024)',
        'multimedia2024':'부산119 다매체 신고 공식 안내','emergency2026':'부산119 구급상황관리센터 안내(2026)',
        'sgis_request':'SGIS 공식 자료 제공 신청','receipt402':'부산119 신고접수 자료 공식 안내','ilgwang2022':'일광면의 일광읍 전환 공식 안내'}
    for name,key in [('response_evidence.json','responseEvidence'),('geographic_evidence.json','geographicEvidence')]:
        path=OUT/name; evidence=json.loads(path.read_text(encoding='utf-8')); extra_evidence[key]=evidence
        inputs.append({'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path),'evidenceKind':'Parent-authored official-source evidence record'})
        for source in evidence.get('sources',[]):
            local=ROOT/source['local_file']; assert sha(local)==source['sha256'],f'Official-source evidence hash mismatch: {local}'
            sources.append({'id':source['id'],'title':evidence_titles.get(source['id'],source['id']),
                'path':source['local_file'].replace('\\','/'),'sha256':source['sha256'],'publicUrl':source['url']})
    package={'meta':{'title':'부산 원문지역별 119 신고 특성과 주민 배경','subtitle':'검증된 선택17 완전행 기술통계 · 행정동·정책 판단은 구분',
        'datasetId':'busan_final_complete17_20260915','generatedAt':datetime.now(timezone(timedelta(hours=9))).isoformat(),
        'years':YEARS,'scopes':list(SCOPES),'scopeLabels':SCOPES,'types':TYPES,'sourceRowCount':4552768,'core8RowCount':1334514,
        'complete17RowCount':704689,'unit':'신고접수 기록 건수; 실제 사건·출동·환자 수가 아님',
        'filterSupport':{'yearly':['year','scope','type'],'time':['year','scope','type'],'rawRegions':['year','scope','type'],
            'population':['year','administrativeCode'],'candidates':['type','district','minimumPerYearExplorationOnly']},
        'unsupportedFilters':['원문지역 선택을 부산 전체 시간 분포에 적용하는 교차표는 제공되지 않음','인구에 신고 조건·종별 필터 적용 불가','인구의 5년 합산 금지'],
        'timeNotes':'시간은 신고시점. 4시간대는 00-03,04-07,08-11,12-15,16-19,20-23. 계절은 달력연도 기준; 겨울은1~2월과12월.',
        'populationNotes':'매년12월말 주민등록인구. 연평균·생활인구·신고대상자 인구가 아니며 개인 연령이나 연령별 신고를 추정하지 않음.',
        'candidateNotes':'C조건·5년양수관측 전체 탐색. 벌집제거는 전체 검산에만 포함. 어떤 최소건수도 정책 후보 통과선으로 채택하지 않음.',
        'limitations':['전체 부산 신고 모집단으로 일반화할 근거가 부족합니다. 이동전화와 위치정보가 기재된 행의 특성을 보여줍니다.',
            '코드 수준의 단일 대응 후보는 실제 신고 행정동 확정을 의미하지 않습니다. 정밀 위치와 역사 경계를 검증하기 전 공간 배정하지 않습니다.',
            '원문지역×시간 교차필터를 제공하지 않습니다. 해당 시간 패널은 부산 전체 선택집합입니다.',
            '기존 대응의 운영 범위가 대조되지 않아 정책 우선순위·대응 공백·시설 설치를 확정하지 않습니다.']},
        'scopeLabels':SCOPES,'yearly':records(yearly),'time':time,'rawRegions':raw,'population':population,
        'sensitivity':{'annual':records(sensitivity_annual),'channels':records(channel_summary),'channelsScope':'2020~2024 전체 A조건 고정; 상단 필터 미적용',
            'mobileShifts':records(mobile_shifts),'repetitionThresholds':records(sensitivity_threshold)},
        'candidates':all_candidates,'sources':sources,**extra_evidence}
    # Cross-table accounting validates all supported filter combinations, not just grand totals.
    time_frame=pd.DataFrame(time)
    for row in yearly.to_dict('records'):
        year,scope,typ,expected=row['year'],row['scope'],row['type'],row['count']
        for dimension in ['month','season','weekday','hourBand']:
            actual=int(time_frame.loc[time_frame.year.eq(year)&time_frame.scope.eq(scope)&time_frame.type.eq(typ)&time_frame.dimension.eq(dimension),'count'].sum())
            assert actual==expected,(year,scope,typ,dimension)
        assert sum(r['typeCounts'][typ] for r in raw if r['year']==year and r['scope']==scope)==expected
    for scope,expected in [('A',704689),('B',579412),('C',574662)]:
        assert int(yearly.loc[yearly.scope.eq(scope),'count'].sum())==expected
    serialized=json.dumps(package,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    assert 'DCLR_RCPT_NO' not in serialized and 'ACDNT_OCRN_LOT' not in serialized and 'DAMG_RGN_LAT' not in serialized
    (WEB/'dashboard.json').write_text(serialized,encoding='utf-8')
    (WEB/'dashboard-data.js').write_text('window.BUSAN_DATA='+serialized+';\n',encoding='utf-8')
    (OUT/'dashboard.json').write_text(serialized,encoding='utf-8')
    # Standalone figures, retaining Korean text and source-specific denominators.
    plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'svg.fonttype':'none','figure.dpi':130,
        'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.labelcolor':'#253750','text.color':'#172b45'})
    def save(fig,name):
        fig.savefig(figures/f'{name}.svg',bbox_inches='tight'); fig.savefig(figures/f'{name}.png',bbox_inches='tight',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8))
    for scope,color in zip(SCOPES,['#183a60','#3296a5','#e18b40']):
        g=scope_counts.loc[scope_counts.scope.eq(scope)].sort_values('year')
        ax.plot(g.year,g.records,marker='o',color=color,lw=2.5,label=f'{scope} · {SCOPES[scope]}')
    ax.set(title='선택17 완전행의 연도별 신고접수 기록',xlabel='연도',ylabel='접수 기록(건)',xticks=YEARS)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x,p:f'{x:,.0f}')); ax.grid(axis='y',alpha=.15); ax.legend(fontsize=9,loc='upper left')
    fig.text(.12,.01,'전체 부산 신고의 추세로 일반화하지 않음 · 17개 값이 모두 기재된 관측집합',fontsize=9); fig.tight_layout(rect=(0,.04,1,1)); save(fig,'01_yearly_scopes')
    fig,ax=plt.subplots(figsize=(9,4.8)); selected_channels=['이동전화','일반전화','IP전화','공중전화','기타']
    cc=channel_summary.set_index('name').loc[selected_channels]; x=np.arange(len(cc))
    ax.bar(x-.18,cc.core8/1000,width=.36,label='기본8 비교집합',color='#cad5df'); ax.bar(x+.18,cc.complete17/1000,width=.36,label='선택17 완전행',color='#1a7087')
    for i,r in enumerate(cc.itertuples()): ax.text(i,max(r.core8,r.complete17)/1000+15,f'{r.complete17/r.core8*100:.1f}% 잔존',ha='center',fontsize=10)
    ax.set(title='접수경로에 따라 크게 다른 완전행 잔존',ylabel='5년 A조건 접수 기록(천 건)',xticks=x,xticklabels=selected_channels); ax.legend(); ax.set_ylim(0,1100); ax.grid(axis='y',alpha=.15)
    fig.text(.12,.01,'이동전화 외 경로의 대규모 제외를 숨기지 않음 · 경로별 잔존율은 기본8 대비',fontsize=9); fig.tight_layout(rect=(0,.04,1,1)); save(fig,'02_channel_selection')
    fig,ax=plt.subplots(figsize=(9,4.8)); rr=sensitivity_threshold.loc[sensitivity_threshold.scope.eq('C')&sensitivity_threshold.minimum_per_year.isin([1,5,10,20])].sort_values('minimum_per_year')
    xx=np.arange(len(rr)); ax.bar(xx-.18,rr.before_qualifying_combinations,.36,color='#cad5df',label='기본8'); ax.bar(xx+.18,rr.after_qualifying_combinations,.36,color='#d18040',label='선택17')
    for i,r in enumerate(rr.itertuples()): ax.text(i,r.before_qualifying_combinations+35,f'{r.after_qualifying_combinations:,} / {r.before_qualifying_combinations:,}',ha='center',fontsize=9)
    ax.set(title='5년 반복 관측도 포함 조건과 탐색 기준에 민감',ylabel='원문지역 × 세부유형 조합 수',xticks=xx,xticklabels=[f'매년 {k}건 이상' for k in rr.minimum_per_year]); ax.legend(); ax.grid(axis='y',alpha=.15)
    fig.text(.12,.01,'C조건 · 벌집제거 제외 · 1·5·10·20은 민감도 비교이며 정책 후보 통과선이 아님',fontsize=9); fig.tight_layout(rect=(0,.04,1,1)); save(fig,'03_repetition_sensitivity')
    fig,ax=plt.subplots(figsize=(9,4.8)); groups=[('0~14세',0,15),('15~29세',15,30),('30~44세',30,45),('45~64세',45,65),('65~74세',65,75),('75세 이상',75,101)]
    colors=['#8ab7b8','#5e94a8','#3a6d96','#243e67','#dbab6f','#b76544']; xs=np.arange(2); bottoms=np.zeros(2)
    totals={y:sum(r['total'] for r in population if r['year']==y) for y in [2020,2024]}
    for (label,lo,hi),color in zip(groups,colors):
        values=np.array([sum(sum(r['ages'][lo:hi]) for r in population if r['year']==y)/totals[y]*100 for y in [2020,2024]])
        ax.bar(xs,values,bottom=bottoms,color=color,width=.48,label=label)
        for i,v in enumerate(values): ax.text(i,bottoms[i]+v/2,f'{v:.1f}%',ha='center',va='center',color='white',fontsize=10)
        bottoms+=values
    ax.set(title='부산 주민 연령 구성: 각 연도 12월 말',ylabel='해당 연도 주민 구성비(%)',xticks=xs,xticklabels=[f'{y}년\n{totals[y]:,}명' for y in [2020,2024]],ylim=(0,100))
    ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',frameon=False)
    fig.text(.12,.01,'읍면동 205행만 합산 · 원본 0~100세 이상 전 연령 보존 · 신고 대상자의 나이로 해석하지 않음',fontsize=9); fig.tight_layout(rect=(0,.05,1,1)); save(fig,'04_population_age_composition')
    validation={'selected17_unchanged':True,'A':704689,'B':579412,'C':574662,'population_rows':len(population),
        'raw_region_year_scope_rows':len(raw),'repeated_observation_records_C_5y':len(all_candidates),
        'supported_year_scope_type_crossfilters_reconcile':True,'all_101_ages_reconcile_to_population_total':True,
        'code_level_population_references_exist':True,'public_row_identifiers_and_precision_coordinates':False,
        'unsupported_crossfilters':package['meta']['unsupportedFilters']}
    (OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    output_paths=[OUT/'dashboard.json',OUT/'repeated_observation_exploration.csv',OUT/'validation.json',WEB/'dashboard.json',WEB/'dashboard-data.js']+sorted(figures.glob('*.svg'))+sorted(figures.glob('*.png'))
    (OUT/'manifest.json').write_text(json.dumps({'script':str(Path(__file__).relative_to(ROOT)).replace('\\','/'),'script_sha256':sha(__file__),
        'verified_aggregate_inputs':inputs,'output_schema_version':1,'outputs':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in output_paths]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False)); print('Dashboard bytes:',len(serialized.encode('utf-8')))

if __name__=='__main__': main()
