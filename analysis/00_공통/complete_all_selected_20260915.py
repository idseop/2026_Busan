"""Compare exact all-selected-field completeness without reinterpreting blank flags.

The 17-field set is the user-approved current analysis input. The internal label
provisional17 is retained only for compatibility with earlier comparison tables.
No input records, coordinates or flags are imputed or overwritten.
"""
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv, gzip, json
import numpy as np
import pandas as pd
from select_complete_receipts_2020_2024 import (
    ROOT,INPUT,REQUIRED_DONG,AUXILIARY,KEYS,OPERATIONS,ID,DT,PROVINCE,SGG,EMD,
    TYPE,SUB,RESULT,PATH,sha)

OUT=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
BASELINE=ROOT/'data/processed/컬럼선별-결측제외-20260915/manifest.json'
STAGES={
    'core8':REQUIRED_DONG,
    'core9':REQUIRED_DONG+[PATH],
    'provisional17':REQUIRED_DONG+AUXILIARY[:9],
    'selected22':REQUIRED_DONG+[c for c in AUXILIARY if c!='CENTR_RSUN_DSPT_DMND_YN'],
    'selected23':REQUIRED_DONG+AUXILIARY,
}
SELECTED=STAGES['selected23']
HIGH_CARDINALITY=[ID,DT,'ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']
OPTIONAL_PURPOSE={
    PATH:'접수경로별 정보 접근·연락 방식 비교가 필요한 질문에 사용.',
    'ACDNT_OCRN_LOT':'사고발생 좌표쌍의 경도. 공식 의미·좌표계 확인 뒤 위치 및 두 좌표쌍 불일치 검증에 사용.',
    'ACDNT_OCRN_LAT':'사고발생 좌표쌍의 위도. 경도와 함께 해석하며 공란을 다른 좌표로 대체하지 않음.',
    'DAMG_RGN_LOT':'손상지역 좌표쌍의 경도. 정확도·유형별 대표성 확인 뒤 공간 연결 후보로 검토.',
    'DAMG_RGN_LAT':'손상지역 좌표쌍의 위도. 좌표가 존재한다는 사실은 정확한 사건 위치를 보장하지 않음.',
    'GRNDS_CTPV_NM':'현장시도와 재난시도의 일치·불일치 점검. 재난지역을 임의 대체하지 않음.',
    'GRNDS_SGG_NM':'현장구군과 재난구군의 일치·불일치 점검. 추가 결측삭제의 지역 선택 영향을 확인.',
    'CMPTNC_FRSTN_NM':'과거 기록상 관할소방서 비교. 현재 대응의 운영 범위·가용성·도착시간은 별도 확인.',
    'PLCSCN_CNTR_NM':'과거 기록상 관할센터 비교. 현재 시설 운영이나 대응 공백으로 직접 해석하지 않음.',
    'OTR_CTPV_DCLR_YN':'타 시도본부에 같은 내용의 신고 여부 점검. Y를 부산 밖 사건으로 판정하지 않음.',
    'OTR_CTPV_DSPT_YN':'타 시도 출동 기록의 기재 상태와 연도별 도메인 비교. N과 공란을 구분.',
    'CLLBC_YN':'콜백이 실제 분석 질문에 필요할 때 재연락 기록으로 검토. 공란=N 미확인.',
    'JNT_CRSP_YN':'기관 간 공동대응 기록 비교가 필요한 경우 검토. 발생 원인·성과로 단정하지 않음.',
    'CENTR_RSUN_DSPT_DMND_YN':'중앙구조대 요청 여부의 잠재적 보조항목이나 현재 전부 공란이므로 실제 비교 불가.',
    'CHEM_ACDNT_YN':'화학사고 관련 질문이 선정될 때 기록상 플래그 검토. N·Y·공란 및 연도별 기재 체계 구분.',
}

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def write_optional_summary(missing_frame,domain_frame):
    rows=[]
    for col in AUXILIARY:
        m=missing_frame[missing_frame.basis.eq('core8')&missing_frame.column.eq(col)]
        count=int(m.missing_rows.sum()); total=int(m.rows.sum())
        d=domain_frame[domain_frame.basis.eq('core8')&domain_frame.column.eq(col)]
        observed=d.groupby('observed_value',dropna=False)['count'].sum().to_dict()
        rows.append({'column':col,'purpose_if_question_requires_it':OPTIONAL_PURPOSE[col],
            'used_now':('확정17개 분석 입력: 접수경로·관할기관 분포 및 지역·좌표 일관성 검증에 실제 사용.' if col in STAGES['provisional17'] else '현재17개 분석 입력에서 제외. 22·23개 조건 비교와 실제 플래그 도메인 점검에만 사용.'),
            'included_in_provisional17':col in STAGES['provisional17'],
            'core8_rows':total,'missing_rows':count,'missing_share':count/total,
            'observed_flag_values_core8':json.dumps(observed,ensure_ascii=False) if col.endswith('_YN') else '범주값 표 또는 고유값 수 요약 참조',
            'policy_status':'사용자 승인에 따라 필요한17개 전체의 결측행을 제외한 자료를 현재 분석에 사용. provisional17은 이전 표와의 호환용 내부명.'})
    pd.DataFrame(rows).to_csv(OUT/'optional_column_use_and_missing.csv',index=False,encoding='utf-8-sig')

def analyze_selected17():
    """Use the nine additionally selected fields, without assigning coordinates to dongs."""
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    hashes={x['file']:x['sha256'] for x in manifest['outputs']}
    input_manifest=json.loads(INPUT.read_text(encoding='utf-8-sig'))
    tables=defaultdict(Counter); dimensions={}; quality=[]; pair_rows=[]; checks=[]; issues=[]
    def add(name,f,keys):
        dimensions[name]=keys
        tables[name].update(f.groupby(keys,sort=False,dropna=False).size().to_dict())
    pairs={'incident':('ACDNT_OCRN_LOT','ACDNT_OCRN_LAT'),'damage':('DAMG_RGN_LOT','DAMG_RGN_LAT')}
    for item in input_manifest['reports']:
        year=item['year']; path=OUT/f'complete_17_{year}.csv.gz'
        assert sha(path)==hashes[path.name]
        totals=Counter(); qc={p:Counter() for p in pairs}; comparison=Counter()
        for df in pd.read_csv(path,dtype=str,keep_default_na=False,chunksize=100000):
            n=len(df); totals['rows']+=n
            blank=df[STAGES['provisional17']].apply(lambda s:s.str.strip().eq(''))
            assert not blank.any().any(),'Complete17 contains missing selected values'
            numeric={c:pd.to_numeric(df[c],errors='coerce') for fields in pairs.values() for c in fields}
            for pair,(lon,lat) in pairs.items():
                bad=numeric[lon].isna()|numeric[lat].isna()
                zero=numeric[lon].eq(0)|numeric[lat].eq(0)
                plausible=numeric[lon].between(-180,180)&numeric[lat].between(-90,90)
                invalid=~bad&~plausible
                qc[pair].update({'rows':n,'numeric_parse_failure':int(bad.sum()),'zero_component':int(zero.sum()),
                    'outside_degree_world_range':int(invalid.sum()),'within_degree_world_range':int(plausible.sum())})
                flagged=bad|zero|invalid
                for idx in df.index[flagged]:
                    reasons=[name for name,mask in [('numeric_parse_failure',bad),('zero_component',zero),('outside_degree_world_range',invalid)] if mask.loc[idx]]
                    issues.append({'year':year,'source_file':df.at[idx,'source_file'],'source_record_index':df.at[idx,'source_record_index'],
                        'pair':pair,'quality_reasons':'|'.join(reasons)})
            ilon,ilat=numeric[pairs['incident'][0]],numeric[pairs['incident'][1]]
            dlon,dlat=numeric[pairs['damage'][0]],numeric[pairs['damage'][1]]
            parsed=ilon.notna()&ilat.notna()&dlon.notna()&dlat.notna()
            exact=parsed&ilon.eq(dlon)&ilat.eq(dlat)
            near=parsed&(ilon-dlon).abs().le(1e-6)&(ilat-dlat).abs().le(1e-6)
            exact_text=df[pairs['incident'][0]].eq(df[pairs['damage'][0]])&df[pairs['incident'][1]].eq(df[pairs['damage'][1]])
            comparison.update({'rows':n,'both_pairs_numeric':int(parsed.sum()),'both_coordinates_numeric_exact_equal':int(exact.sum()),
                'both_coordinates_text_exact_equal':int(exact_text.sum()),'both_deltas_within_1e_6_input_units':int(near.sum()),
                'numeric_pairs_differ':int((parsed&~exact).sum()),'at_least_one_parse_failure':int((~parsed).sum())})
            df['year']=year
            df['province_names_equal']=df[PROVINCE].eq(df['GRNDS_CTPV_NM'])
            df['district_names_equal']=df[SGG].eq(df['GRNDS_SGG_NM'])
            normal=df[RESULT].eq('정상')
            for scope,mask in [('A',pd.Series(True,index=df.index)),('B',normal),('C',normal&~df[SUB].isin(OPERATIONS))]:
                f=df.loc[mask].copy(); f['scope']=scope; totals[scope]+=len(f)
                add('selected17_receipt_path_distribution',f,['year','scope',TYPE,SUB,PATH])
                add('selected17_jurisdiction_distribution',f,['year','scope',SGG,TYPE,'CMPTNC_FRSTN_NM','PLCSCN_CNTR_NM'])
                add('selected17_region_name_comparison',f,['year','scope',TYPE,'province_names_equal','district_names_equal'])
                add('selected17_region_name_crosstab',f,['year','scope',TYPE,PROVINCE,'GRNDS_CTPV_NM',SGG,'GRNDS_SGG_NM'])
        for pair,count in qc.items(): quality.append({'year':year,'pair':pair,**dict(count)})
        pair_rows.append({'year':year,**dict(comparison)})
        expected=next(x['provisional17'] for x in manifest['year_counts'] if x['year']==year)
        assert totals['rows']==expected
        checks.append({'year':year,'counts':dict(totals),'selected17_missing_values':0,'complete_file_sha256':sha(path)})
    generated=set()
    for name,counter in tables.items():
        cols=dimensions[name]; f=pd.DataFrame([list(k)+[v] for k,v in counter.items()],columns=cols+['count'])
        for check in checks:
            for scope in ['A','B','C']:
                assert int(f.loc[f.year.eq(check['year'])&f.scope.eq(scope),'count'].sum())==check['counts'][scope]
        f.sort_values(cols).to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig'); generated.add(f'{name}.csv')
    for name,rows,columns in [('selected17_coordinate_quality',quality,None),('selected17_coordinate_pair_comparison',pair_rows,None),
        ('selected17_coordinate_quality_records',issues,['year','source_file','source_record_index','pair','quality_reasons'])]:
        pd.DataFrame(rows,columns=columns).to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig'); generated.add(f'{name}.csv')
    dump('selected17_analysis_validation.json',{'checks':checks,'analysis_policy':'Approved selected17 with zero missing values in all 17 raw fields.',
        'legacy_label':'provisional17 in previously generated tables means this same approved selected17 set; retained for backward compatibility.',
        'coordinate_interpretation':'Numeric and world-range checks assume degree-like axes only as diagnostics; no CRS/precision/incident-location validation, no spatial assignment. Near equality is in input units, not verified geographic tolerance.',
        'coordinate_quality_handling':'Parsing failures, zeros and range anomalies are recorded separately from missingness. They are not silently repaired or removed from descriptive receipt counts.',
        'region_interpretation':'Text inequality between GRNDS and CLMTY is diagnostic disagreement, not a verified location error.',
        'jurisdiction_interpretation':'Recorded historical jurisdiction names are distributions, not verified current staffing/operating coverage.',
        'aggregate_reconciliation':'All four distributions agree with selected17 A/B/C row counts in each year.'})
    generated.add('selected17_analysis_validation.json')
    policy=json.loads((OUT/'comparison_policy.json').read_text(encoding='utf-8'))
    policy['status']='User-approved current input: selected17; rows missing any selected field excluded.'
    policy['legacy_label']='provisional17 is the historical table label for the now-approved selected17; membership is unchanged.'
    policy['current_selected_fields']=STAGES['provisional17']
    dump('comparison_policy.json',policy)
    write_optional_summary(pd.read_csv(OUT/'selected_column_missing.csv'),pd.read_csv(OUT/'observed_categorical_and_flag_values.csv',keep_default_na=False))
    generated.update(['comparison_policy.json','optional_column_use_and_missing.csv'])
    output_names={x['file'] for x in manifest['outputs']}|generated
    manifest['status']='User-approved selected17 complete-case input; added fields used in region, coordinate, jurisdiction and contact-channel diagnostics.'
    manifest['legacy_label']='provisional17 denotes the approved selected17 set in retained comparison tables.'
    manifest['current_selected_fields']=STAGES['provisional17']; manifest['script_sha256']=sha(__file__)
    manifest['outputs']=[{'file':name,'bytes':(OUT/name).stat().st_size,'sha256':sha(OUT/name)} for name in sorted(output_names)]
    dump('manifest.json',manifest)
    print('Approved selected17 diagnostics completed:',sum(x['counts']['rows'] for x in checks),flush=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(INPUT.read_text(encoding='utf-8-sig'))
    baseline=json.loads(BASELINE.read_text(encoding='utf-8'))
    base_counts={r['year']:r['counts']['complete_dong'] for r in baseline['reconciliation']}
    assert [len(v) for v in STAGES.values()]==[8,9,17,22,23]
    assert all(len(v)==len(set(v)) for v in STAGES.values())
    tables=defaultdict(Counter); dims={}; stage_rows=[]; missing_rows=[]; domains=[]; evidence=[]; annual_checks=[]
    def add(name,frame,keys):
        dims[name]=keys
        tables[name].update(frame.groupby(keys,sort=False,dropna=False).size().to_dict())
    for item in manifest['reports']:
        year=item['year']; path=ROOT/item['file']; digest=sha(path)
        prior_path=ROOT/f'data/interim/119접수감사/{year}.json'
        prior=json.loads(prior_path.read_text(encoding='utf-8-sig'))
        assert digest==item['sha256']==prior['sha256']
        with path.open(encoding=item['encoding'],newline='') as f: header=next(csv.reader(f))
        assert header==prior['originalHeaders']
        evidence.append({'year':year,'file':item['file'],'sha256':digest,'header_matches_hash_verified_prior':True,
            'prior_audit_file':str(prior_path.relative_to(ROOT)),'prior_audit_sha256':sha(prior_path)})
        counts=Counter(); missing=Counter(); domain=defaultdict(Counter); distinct={c:set() for c in HIGH_CARDINALITY}
        offset=0; stage_count=Counter()
        complete_cols=KEYS+STAGES['provisional17']+['year','month','hour']
        excluded_cols=KEYS+['year','missing_provisional17_columns']
        with ExitStack() as stack:
            complete=stack.enter_context(gzip.open(OUT/f'complete_17_{year}.csv.gz','wt',encoding='utf-8',newline='',compresslevel=3))
            excluded=stack.enter_context(gzip.open(OUT/f'excluded_core8_to_17_{year}.csv.gz','wt',encoding='utf-8',newline='',compresslevel=3))
            pd.DataFrame(columns=complete_cols).to_csv(complete,index=False)
            pd.DataFrame(columns=excluded_cols).to_csv(excluded,index=False)
            for df in pd.read_csv(path,encoding=item['encoding'],dtype=str,keep_default_na=False,chunksize=100000):
                df.columns=df.columns.str.upper(); n=len(df)
                blank=pd.DataFrame({c:df[c].str.strip().eq('') for c in SELECTED})
                busan=df[PROVINCE].eq('부산광역시')
                raw_masks={stage:~blank[cols].any(axis=1) for stage,cols in STAGES.items()}
                masks={stage:busan&mask for stage,mask in raw_masks.items()}
                for smaller,larger in zip(list(STAGES),list(STAGES)[1:]):
                    assert not (raw_masks[larger]&~raw_masks[smaller]).any(),(year,smaller,larger)
                for stage,cols in STAGES.items():
                    assert not blank.loc[masks[stage],cols].any().any(),(year,stage)
                    stage_count[(stage,'all_source')]+=int(raw_masks[stage].sum())
                    stage_count[(stage,'busan_explicit')]+=int(masks[stage].sum())
                counts['source_rows']+=n; counts['busan_explicit']+=int(busan.sum())
                counts['core8']+=int(masks['core8'].sum()); counts['provisional17']+=int(masks['provisional17'].sum())
                basis_masks={'all_source':pd.Series(True,index=df.index),'busan_explicit':busan,'core8':masks['core8'],'provisional17':masks['provisional17']}
                for basis,bmask in basis_masks.items():
                    for col in SELECTED: missing[(basis,col)]+=int(blank.loc[bmask,col].sum())
                # Every categorical/flag value is counted verbatim, including empty strings.
                # Identifier, precise time and coordinate domains are characterized without publishing values.
                for col in SELECTED:
                    if col in HIGH_CARDINALITY:
                        distinct[col].update(df.loc[~blank[col],col].tolist())
                    else:
                        for basis,bmask in basis_masks.items():
                            domain[(basis,col)].update(df.loc[bmask,col].value_counts(dropna=False).to_dict())
                df['source_file']=item['file']; df['source_record_index']=np.arange(offset+1,offset+n+1)
                df['year']=year
                # Date syntax/components were previously checked on identical raw inputs.
                clean_dt=df[DT].str.strip(); df['month']=clean_dt.str[4:6].astype(int); df['hour']=clean_dt.str[8:10].astype(int)
                df.loc[masks['provisional17'],complete_cols].to_csv(complete,index=False,header=False)
                df['missing_provisional17_columns']=''
                for col in STAGES['provisional17']:
                    df['missing_provisional17_columns']=df['missing_provisional17_columns']+np.where(blank[col],col+'|','')
                df['missing_provisional17_columns']=df['missing_provisional17_columns'].str.rstrip('|')
                removed=masks['core8']&~masks['provisional17']; counts['removed_core8_to_17']+=int(removed.sum())
                df.loc[removed,excluded_cols].to_csv(excluded,index=False,header=False)
                add('core8_to_17_missing_patterns',df.loc[removed],['year','missing_provisional17_columns'])
                normal=df[RESULT].eq('정상'); operational_excluded=normal&~df[SUB].isin(OPERATIONS)
                for stage,mask in {'raw_busan':busan,**masks}.items():
                    for scope,scope_mask in [('A',pd.Series(True,index=df.index)),('B',normal),('C',operational_excluded)]:
                        f=df.loc[mask&scope_mask].copy(); f['stage']=stage; f['scope']=scope
                        stage_count[(stage,scope)]+=len(f)
                        add('annual_classification',f,['year','stage','scope',TYPE,SUB,RESULT])
                        add('original_region_classification',f,['year','stage','scope',SGG,EMD,TYPE,SUB,RESULT])
                        add('original_region_totals',f,['year','stage','scope',SGG,EMD])
                offset+=n
        assert offset==item['rowsFromPriorFullAudit']
        assert counts['core8']==base_counts[year]
        assert counts['core8']==counts['provisional17']+counts['removed_core8_to_17']
        for (stage,basis),count in stage_count.items():
            denominator=stage_count[('core8',basis)]
            stage_rows.append({'year':year,'stage':stage,'basis_or_scope':basis,'complete_rows':count,
                'raw_source_rows':offset,'busan_explicit_rows':counts['busan_explicit'],
                'core8_rows':counts['core8'],'core8_same_basis_or_scope_rows':denominator,
                'retention_vs_core8':count/denominator if stage!='raw_busan' and denominator else None})
        for (basis,col),count in missing.items():
            total=counts['source_rows'] if basis=='all_source' else counts[basis]
            missing_rows.append({'year':year,'basis':basis,'column':col,'rows':total,'missing_rows':count,'nonmissing_rows':total-count,'missing_share':count/total if total else None})
        for (basis,col),counter in domain.items():
            for value,count in counter.items():
                domains.append({'year':year,'basis':basis,'column':col,'observed_value':value,
                    'value_kind':'blank' if not value.strip() else 'literal','count':count})
        annual_checks.append({'year':year,'counts':dict(counts),'required_fields_missing_in_all_complete_sets':0,
            'nested_subset_violations':0,'core8_matches_previous_full_analysis':True,
            'high_cardinality_domains':[{'column':c,'nonblank_distinct_original_values':len(distinct[c]),
                'nonblank_rows':offset-missing[('all_source',c)],'missing_rows':missing[('all_source',c)],
                'observed_value_reporting':'Values intentionally not enumerated: receipt IDs, precise times and coordinates remain in local row-level files.'} for c in HIGH_CARDINALITY]})
        print(f'{year}: core8={counts["core8"]:,}, 9={stage_count[("core9","A")]:,}, 17={counts["provisional17"]:,}, 22={stage_count[("selected22","A")]:,}, 23={stage_count[("selected23","A")]:,}',flush=True)
    stages=['raw_busan']+list(STAGES)
    pd.DataFrame(stage_rows).to_csv(OUT/'stage_completeness.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(missing_rows).to_csv(OUT/'selected_column_missing.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(domains).to_csv(OUT/'observed_categorical_and_flag_values.csv',index=False,encoding='utf-8-sig')
    write_optional_summary(pd.DataFrame(missing_rows),pd.DataFrame(domains))
    for name,counter in tables.items():
        columns=dims[name]
        frame=pd.DataFrame([list(k)+[int(v)] for k,v in counter.items()],columns=columns+['count'])
        frame.sort_values(columns).to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig')
        if 'stage' in columns:
            keys=[c for c in columns if c!='stage']
            r=frame.pivot(index=keys,columns='stage',values='count').reindex(columns=stages).fillna(0).astype(int).reset_index()
            for stage in STAGES:
                assert (r[stage]<=r.raw_busan).all()
                if stage!='core8': assert (r[stage]<=r.core8).all()
                r[stage+'_retention_vs_raw']=r[stage]/r.raw_busan.replace(0,np.nan)
                r[stage+'_retention_vs_core8']=r[stage]/r.core8.replace(0,np.nan)
                r[stage+'_removed_vs_core8']=r.core8-r[stage]
            if name=='original_region_totals':
                r['name_present']=r[SGG].ne('')&r[EMD].ne('')
                r['disappears_at17_vs_core8']=r.core8.gt(0)&r.provisional17.eq(0)
                r['disappears_at23_vs_core8']=r.core8.gt(0)&r.selected23.eq(0)
            r.to_csv(OUT/f'{name}_retention.csv',index=False,encoding='utf-8-sig')
            for check in annual_checks:
                year=check['year']
                for stage in stages:
                    for scope in ['A','B','C']:
                        expected=next(x['complete_rows'] for x in stage_rows if x['year']==year and x['stage']==stage and x['basis_or_scope']==scope)
                        actual=int(frame.loc[frame.year.eq(year)&frame.stage.eq(stage)&frame.scope.eq(scope),'count'].sum())
                        assert actual==expected,(year,stage,scope,name)
    policy={'status':'User-approved current input: selected17; rows missing any selected field excluded.',
        'stages':STAGES,'complete_17_schema':complete_cols,'excluded_schema':excluded_cols,
        'missing_rule':'Empty or whitespace-only. Do not map blank flags to N or replace missing coordinates. No record deduplication.',
        'busan_rule':'CLMTY_CTPV_NM exactly 부산광역시; unknown province is not declared outside Busan.',
        'core8':'Receipt ID/time, declared disaster region and original type/subtype/result support receipt characterization.',
        'added_to17':{
            PATH:'Access/contact channel comparison; presence does not imply channel matters to every question.',
            'ACDNT_OCRN_LOT/LAT and DAMG_RGN_LOT/LAT':'Both complete pairs permit coordinate disagreement checks; completeness does not establish CRS or correct event position.',
            'GRNDS_CTPV_NM/GRNDS_SGG_NM':'Compare field region with declared disaster region; disagreement must not be silently resolved.',
            'CMPTNC_FRSTN_NM/PLCSCN_CNTR_NM':'Historical recorded jurisdiction comparison; not proof of current operation, coverage or response performance.'},
        'added_flags_in22_and23':'Literal complete-case requirement on flags, not a recommended filter on events. Blank is unconfirmed, not N. Fully blank columns can eliminate every record.',
        'spatial_status':'Original dong labels remain unverified against administrative/legal dong boundaries and population codes.',
        'scope_rules':{'A':'All processing results','B':'PRCS_RSLT_SE_NM == 정상','C':'B excluding '+', '.join(OPERATIONS)},
        'beehive_policy':'Retained only in all-category accounting. Not selected as a candidate, follow-up research or proposal.',
        'privacy':'Local complete_17 includes identifiers and precision coordinates; not for direct publication.'}
    dump('comparison_policy.json',policy); dump('validation_and_domains.json',annual_checks); dump('input_evidence.json',evidence)
    generated={'stage_completeness.csv','selected_column_missing.csv','observed_categorical_and_flag_values.csv','optional_column_use_and_missing.csv',
               'comparison_policy.json','validation_and_domains.json','input_evidence.json'}
    generated.update(f'{name}.csv' for name in tables)
    generated.update(f'{name}_retention.csv' for name in tables if 'stage' in dims[name])
    generated.update(f'{name}_{year}.csv.gz' for name in ['complete_17','excluded_core8_to_17'] for year in manifest['analysisYears'])
    dump('manifest.json',{'script':str(__file__),'script_sha256':sha(__file__),
        'dependency_script':'analysis/00_공통/select_complete_receipts_2020_2024.py',
        'dependency_script_sha256':sha(ROOT/'analysis/00_공통/select_complete_receipts_2020_2024.py'),
        'input_manifest':str(INPUT.relative_to(ROOT)),'input_manifest_sha256':sha(INPUT),
        'baseline_manifest':str(BASELINE.relative_to(ROOT)),'baseline_manifest_sha256':sha(BASELINE),
        'status':'Comparison complete; selected17 is the user-approved current analysis input.',
        'checks':'Raw hashes verified; core8 baseline matched; all selected complete sets have zero missing values; nested subsets and all stage/scope aggregate sums reconciled.',
        'year_counts':[x['counts']|{'year':x['year']} for x in annual_checks],
        'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name in generated]})

if __name__=='__main__':
    import sys
    if '--analyze-selected17' not in sys.argv: main()
    analyze_selected17()
