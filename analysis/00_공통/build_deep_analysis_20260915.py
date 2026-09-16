"""Add original-region temporal cross-tabs without changing selected17 membership."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone,timedelta
import hashlib,json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
FINAL=ROOT/'data/processed/최종결과-20260915'
OUT=ROOT/'data/processed/심층분석-20260915'
WEB=ROOT/'web/final/data'
YEARS=list(range(2020,2025)); SCOPES=['A','B','C']; TYPES=['구급','구조','화재','기타']
SGG,EMD,TYPE,SUB,RESULT,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
BANDS=['00-03','04-07','08-11','12-15','16-19','20-23']

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True); WEB.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    hashes={x['file']:x['sha256'] for x in manifest['outputs']}
    fm=json.loads((FINAL/'manifest.json').read_text(encoding='utf-8'))
    finalpath=FINAL/'dashboard.json'; assert sha(finalpath)==next(x['sha256'] for x in fm['outputs'] if x['path']==str(finalpath.relative_to(ROOT)).replace('\\','/'))
    dashboard=json.loads(finalpath.read_text(encoding='utf-8'))
    region_names=sorted({(r['district'],r['rawDong']) for r in dashboard['rawRegions']})
    regions=[{'index':i,'id':'|'.join(names),'district':names[0],'rawDong':names[1]} for i,names in enumerate(region_names)]
    region_lookup={names:i for i,names in enumerate(region_names)}
    case_specs=[
        ('기장군','기장읍','구급','질병','동일 군·동일 분류의 조건부 주민 배경과 선택 영향을 비교하는 기준 사례',
         ['주요 반복 분류 질병이 5년 모두 관측됨','각 연도 단일 인구 코드 후보가 있어 주민 배경을 조건부로 대조 가능','정관읍과 같은 군·같은 분류를 비교해 포함 조건의 영향을 확인']),
        ('기장군','정관읍','구급','질병','같은 군에서도 크게 다른 완전행 잔존을 확인하는 대조 사례',
         ['질병 분류가 5년 모두 관측되고 단일 인구 코드 후보가 존재','기장읍과 같은 군·같은 분류의 짝 비교','낮은 선택17 잔존을 신고 위험의 낮음으로 오해하지 않도록 명시']),
        ('연제구','연산동','구급','질병','관측 규모가 커도 행정동 배정을 확정할 수 없음을 보여 주는 사례',
         ['C조건 5년 반복 질병 조합 가운데 선택17 합계가 가장 큰 원문 지역명','복수 행정동 대응 후보로 주민 인구의 자동 결합을 보류','큰 건수·5년 반복만으로 정책 우선순위를 결정할 수 없음을 대조']),
        ('북구','금곡동','구조','시건개방','구급 외 반복 유형의 시간대와 처리 범위를 확인하는 사례',
         ['시건개방이 5년 모두 관측되고 연도별 단일 인구 코드 후보가 존재','이미 포함한 기장읍을 제외한 단일 코드 후보 명칭 중 시건개방 관측 합계가 가장 큼','5년 반복·다른 신고 유형·동 대응 후보 여부를 함께 확인하는 설명용 사례']),
    ]
    cases=[]; case_lookup={}
    for i,(district,dong,typ,subtype,role,reasons) in enumerate(case_specs):
        c=next(c for c in dashboard['candidates'] if (c['district'],c['rawDong'],c['type'],c['subtype'])==(district,dong,typ,subtype))
        links=[next(r for r in dashboard['rawRegions'] if r['year']==y and r['scope']=='C' and (r['district'],r['rawDong'])==(district,dong)) for y in YEARS]
        case={'index':i,'id':'deep-'+c['id'],'title':f'{district} {dong} · {subtype}','district':district,'rawDong':dong,
            'regionIndex':region_lookup[(district,dong)],'type':typ,'subtype':subtype,'role':role,'selectionReasons':reasons,
            'limitations':['사후 탐색에서 선정한 설명용 사례로 부산 전체의 대표 표본이나 정책 우선순위가 아님',
                '원문지역의 정확한 행정동 경계·신고 대상자 연령은 미확정',
                '선택17에서 제외된 접수를 같은 특성으로 간주하지 않음',
                '해당 유형의 기존 대응 대상·운영 범위와 현장 원인은 별도 확인 필요'],
            'yearCounts':c['yearCounts'],'core8YearCounts':c['core8YearCounts'],'minAnnualCount':c['minAnnualCount'],
            'retention':c['retention'],'directionReversal':c['directionReversal'],
            'populationLinks':[{'year':r['year'],'codeLevelEligible':r['codeLevelEligible'],'uniqueCode':r['uniqueCode'],
                'candidateCodes':r['candidateCodes'],'geographyConfirmed':False} for r in links]}
        assert subtype!='벌집제거' and min(case['yearCounts'])>0
        cases.append(case);case_lookup[(district,dong,typ,subtype)]=i
    day_hour=Counter(); month=Counter(); case_time=Counter(); case_month=Counter(); annual=Counter(); source_evidence=[]
    for year in YEARS:
        path=SOURCE/f'complete_17_{year}.csv.gz'; digest=sha(path);assert digest==hashes[path.name]
        source_evidence.append({'year':year,'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':digest})
        rows=0
        for f in pd.read_csv(path,usecols=[SGG,EMD,TYPE,SUB,RESULT,DT],dtype=str,keep_default_na=False,chunksize=100000):
            rows+=len(f);f['regionIndex']=[region_lookup[(d,n)] for d,n in zip(f[SGG],f[EMD])]
            f['typeIndex']=f[TYPE].map(dict(zip(TYPES,range(4))))
            parsed=pd.to_datetime(f[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise')
            f['weekday']=parsed.dt.dayofweek;f['hourBandIndex']=parsed.dt.hour//4;f['month']=parsed.dt.month
            f['caseIndex']=[case_lookup.get((d,n,t,s),-1) for d,n,t,s in zip(f[SGG],f[EMD],f[TYPE],f[SUB])]
            normal=f[RESULT].eq('정상')
            for si,scope in enumerate(SCOPES):
                mask=pd.Series(True,index=f.index) if scope=='A' else normal if scope=='B' else normal&~f[SUB].isin(['업무운행','훈련출동','구급차소독'])
                g=f.loc[mask];annual[(year,si)]+=len(g)
                for key,count in g.groupby(['regionIndex','typeIndex','weekday','hourBandIndex']).size().items():
                    ri,ti,wd,hb=key;day_hour[(int(ri),year,si,int(ti),int(wd),int(hb))]+=int(count)
                for key,count in g.groupby(['regionIndex','typeIndex','month']).size().items():
                    ri,ti,mo=key;month[(int(ri),year,si,int(ti),int(mo))]+=int(count)
                cc=g.loc[g.caseIndex.ge(0)]
                for key,count in cc.groupby(['caseIndex','weekday','hourBandIndex']).size().items():
                    ci,wd,hb=key;case_time[(int(ci),year,si,int(wd),int(hb))]+=int(count)
                for key,count in cc.groupby(['caseIndex','month']).size().items():
                    ci,mo=key;case_month[(int(ci),year,si,int(mo))]+=int(count)
        assert rows==next(x['provisional17'] for x in manifest['year_counts'] if x['year']==year)
        print(f'{year}: {rows:,} existing selected17 rows cross-tabulated',flush=True)
    day_rows=[list(k)+[v] for k,v in sorted(day_hour.items())];month_rows=[list(k)+[v] for k,v in sorted(month.items())]
    case_rows=[list(k)+[v] for k,v in sorted(case_time.items())];case_month_rows=[list(k)+[v] for k,v in sorted(case_month.items())]
    cols=['regionIndex','year','scopeIndex','typeIndex','weekday','hourBandIndex','count'];mcols=['regionIndex','year','scopeIndex','typeIndex','month','count']
    ctcols=['caseIndex','year','scopeIndex','weekday','hourBandIndex','count'];cmcols=['caseIndex','year','scopeIndex','month','count']
    dh=pd.DataFrame(day_rows,columns=cols);mm=pd.DataFrame(month_rows,columns=mcols)
    checks=[]
    for r in dashboard['rawRegions']:
        ri=region_lookup[(r['district'],r['rawDong'])];si=SCOPES.index(r['scope']);year=r['year']
        for ti,typ in enumerate(TYPES):
            expected=r['typeCounts'][typ]
            actual=int(dh.loc[dh.regionIndex.eq(ri)&dh.year.eq(year)&dh.scopeIndex.eq(si)&dh.typeIndex.eq(ti),'count'].sum())
            other=int(mm.loc[mm.regionIndex.eq(ri)&mm.year.eq(year)&mm.scopeIndex.eq(si)&mm.typeIndex.eq(ti),'count'].sum())
            assert expected==actual==other,(year,r['district'],r['rawDong'],r['scope'],typ)
    for year in YEARS:
        for si,scope in enumerate(SCOPES):
            expected=sum(r['count'] for r in dashboard['yearly'] if r['year']==year and r['scope']==scope)
            assert annual[(year,si)]==expected
            checks.append({'year':year,'scope':scope,'count':expected,'matches_existing_verified_yearly_and_region_type':True})
    case_df=pd.DataFrame(case_rows,columns=ctcols)
    for case in cases:
        for y,expected in zip(YEARS,case['yearCounts']):
            assert int(case_df.loc[case_df.caseIndex.eq(case['index'])&case_df.year.eq(y)&case_df.scopeIndex.eq(2),'count'].sum())==expected
        f=case_df.loc[case_df.caseIndex.eq(case['index'])&case_df.scopeIndex.eq(2)]
        case['weekdayCounts']=[int(f.loc[f.weekday.eq(w),'count'].sum()) for w in range(7)]
        case['hourBandCounts']=[int(f.loc[f.hourBandIndex.eq(h),'count'].sum()) for h in range(6)]
    payload={'meta':{'datasetId':'busan_deep_complete17_20260915','generatedAt':datetime.now(timezone(timedelta(hours=9))).isoformat(),
        'years':YEARS,'scopes':SCOPES,'types':TYPES,'hourBands':BANDS,'weekdayLabels':['월','화','수','목','금','토','일'],
        'dayHourColumns':cols,'monthColumns':mcols,'caseTimeColumns':ctcols,'caseMonthColumns':cmcols,
        'complete17Rows':704689,'unit':'신고접수 기록; 실제 사건·출동·환자 수 아님',
        'geography':'구군+신고 원문 읍면동 명칭. 행정동 경계 배정은 미확정.',
        'supportedJointFilters':['region+year+scope+type+weekday+hourBand','region+year+scope+type+month','case+year+scope+weekday+hourBand'],
        'unsupportedJointFilters':['month와weekday/hourBand를동시에교차필터링하는표는제공하지않음'],
        'zeroCells':'같은 기존 관측 지역·연도·조건·종별 영역에서 누락된 희소 셀은0. 지역명 자체가 없는 연도는 관측 없음이며 자동 동명 변경·합산하지 않음.',
        'casesPolicy':'가중점수·정책순위 없음. 반복 관측·선택 민감도·코드 수준 대응 차이를 설명하는4개 사례이며 사후탐색임.',
        'beehivePolicy':'전체 종별 검산에만 포함하며 심층 사례·추가 연구·제안에서 제외.'},
        'regions':regions,'dayHour':day_rows,'month':month_rows,'caseTime':case_rows,'caseMonth':case_month_rows,'cases':cases,
        'sourceManifest':str((OUT/'manifest.json').relative_to(ROOT)).replace('\\','/')}
    text=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (WEB/'deep-data.json').write_text(text,encoding='utf-8');(WEB/'deep-data.js').write_text('window.BUSAN_DEEP='+text+';\n',encoding='utf-8')
    (OUT/'deep-data.json').write_text(text,encoding='utf-8')
    for name,frame in [('regional_weekday_hour',dh),('regional_month',mm),('case_weekday_hour',case_df),('case_month',pd.DataFrame(case_month_rows,columns=cmcols))]:
        frame.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
    case_table=[]
    for c in cases:
        case_table.append({'id':c['id'],'district':c['district'],'raw_dong':c['rawDong'],'type':c['type'],'subtype':c['subtype'],
            'role':c['role'],'selected17_total_C':sum(c['yearCounts']),'core8_total_C':sum(c['core8YearCounts']),
            'retention':c['retention'],'observed_years':5,'minimum_selected17_annual_count':c['minAnnualCount'],
            'five_year_code_level_eligible':all(r['codeLevelEligible'] for r in c['populationLinks']),
            'administrative_geography_confirmed':False,'selection_reasons':' | '.join(c['selectionReasons']),
            'limitations':' | '.join(c['limitations']),**{f'selected17_{y}':n for y,n in zip(YEARS,c['yearCounts'])},
            **{f'core8_{y}':n for y,n in zip(YEARS,c['core8YearCounts'])}})
    pd.DataFrame(case_table).to_csv(OUT/'case_selection_evidence.csv',index=False,encoding='utf-8-sig')
    (OUT/'validation.json').write_text(json.dumps({'status':'passed','annual_checks':checks,'all_2901_region_year_scope_by4type_crosschecks':True,
        'case_subtype_counts_match_previous_C_evidence':True,'selected17_unchanged':True,'published_individual_identifiers_or_precision_coordinates':False,
        'day_hour_sparse_rows':len(day_rows),'month_sparse_rows':len(month_rows),'case_rows':len(cases)},ensure_ascii=False,indent=2),encoding='utf-8')
    outputs=[OUT/n for n in ['deep-data.json','regional_weekday_hour.csv','regional_month.csv','case_weekday_hour.csv','case_month.csv','case_selection_evidence.csv','validation.json']]+[WEB/'deep-data.json',WEB/'deep-data.js']
    (OUT/'manifest.json').write_text(json.dumps({'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(__file__),
        'input_files':source_evidence,'source_manifest_sha256':sha(SOURCE/'manifest.json'),'previous_final_dashboard':str(finalpath.relative_to(ROOT)),
        'previous_final_dashboard_sha256':sha(finalpath),'outputs':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Deep payload {len(text.encode()):,} bytes; day-hour cells {len(day_rows):,}; monthly cells {len(month_rows):,}; cases {len(cases)}')

def enrich_case_sensitivity():
    """Derive condition and coarser time-bin comparisons from already verified counts."""
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    payload=json.loads((OUT/'deep-data.json').read_text(encoding='utf-8'))
    source_manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
    source=SOURCE/'original_region_classification.csv'
    assert sha(source)==next(x['sha256'] for x in source_manifest['outputs'] if x['file']==source.name)
    original=pd.read_csv(source,keep_default_na=False)
    ct=pd.read_csv(OUT/'case_weekday_hour.csv')
    sensitivity=[]
    for case in payload['cases']:
        match=original.loc[original[SGG].eq(case['district'])&original[EMD].eq(case['rawDong'])&original[TYPE].eq(case['type'])&original[SUB].eq(case['subtype'])]
        conditions={};bins=[]
        for si,scope in enumerate(SCOPES):
            before=[int(match.loc[match.year.eq(y)&match.scope.eq(scope)&match.stage.eq('core8'),'count'].sum()) for y in YEARS]
            after=[int(ct.loc[ct.caseIndex.eq(case['index'])&ct.year.eq(y)&ct.scopeIndex.eq(si),'count'].sum()) for y in YEARS]
            expected=[int(match.loc[match.year.eq(y)&match.scope.eq(scope)&match.stage.eq('provisional17'),'count'].sum()) for y in YEARS]
            assert after==expected
            conditions[scope]={'yearCounts':after,'core8YearCounts':before,'selected17Total':sum(after),'core8Total':sum(before),
                'retention':sum(after)/sum(before) if sum(before) else None,
                'selected17Change2024Minus2020':after[-1]-after[0],'core8Change2024Minus2020':before[-1]-before[0],
                'directionReversal':(after[-1]-after[0])*(before[-1]-before[0])<0,
                'positiveInAllFiveYears':min(after)>0}
            f=ct.loc[ct.caseIndex.eq(case['index'])&ct.scopeIndex.eq(si)]
            four=[int(f.loc[f.hourBandIndex.eq(b),'count'].sum()) for b in range(6)]
            for width in [4,8,12]:
                step=width//4;values=[sum(four[i:i+step]) for i in range(0,6,step)]
                labels=[f'{start:02d}-{start+width-1:02d}' for start in range(0,24,width)]
                peaks=[labels[i] for i,v in enumerate(values) if v==max(values)]
                bins.append({'scope':scope,'widthHours':width,'labels':labels,'counts':values,'peakLabels':peaks,
                    'peakShare':max(values)/sum(values) if sum(values) else None})
        case['countsByScope']=conditions;case['timebinSensitivity']=bins
        case['timebinSensitivityNote']='자정 기준의4시간 집계를8·12시간으로 재합산한 비교. 다른 시작시각이나 월×요일×시간 결합의 안정성을 검증한 것은 아님. 시간구간 폭에 따라 최대구간이 달라질 수 있음.'
        sensitivity.append({'id':case['id'],'title':case['title'],'countsByScope':conditions,'timebinSensitivity':bins,'interpretation':case['timebinSensitivityNote']})
    payload['meta']['timeBinSensitivity']='사례별 A/B/C 및 4·8·12시간 고정자정구간 비교 제공. 정책 임계값·현장출동시간으로 해석하지 않음.'
    text=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    (OUT/'deep-data.json').write_text(text,encoding='utf-8');(WEB/'deep-data.json').write_text(text,encoding='utf-8');(WEB/'deep-data.js').write_text('window.BUSAN_DEEP='+text+';\n',encoding='utf-8')
    extra=OUT/'case_condition_time_sensitivity.json';extra.write_text(json.dumps(sensitivity,ensure_ascii=False,indent=2),encoding='utf-8')
    validation=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    validation['all_4cases_5years_3scopes_match_before_after_evidence']=True
    validation['coarser_case_timebins_derived_without_changing_membership']=True
    (OUT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
    names={x['path'] for x in manifest['outputs']};names.add(str(extra.relative_to(ROOT)).replace('\\','/'))
    manifest['script_sha256']=sha(__file__)
    manifest['case_sensitivity_input']={'path':str(source.relative_to(ROOT)).replace('\\','/'),'sha256':sha(source)}
    manifest['outputs']=[{'path':name,'sha256':sha(ROOT/name),'bytes':(ROOT/name).stat().st_size} for name in sorted(names)]
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Case scope and 4/8/12-hour sensitivity added; approved selected17 unchanged.')

if __name__=='__main__':
    import sys
    if '--enrich-only' not in sys.argv:main()
    enrich_case_sensitivity()
