"""Select useful fields and execute complete-case receipt analysis, retaining exclusions.

Run from repository root. Inputs are ONLY the five manifest-selected raw receipts;
earlier hash-verified audit files are reused as quality evidence, never as observations.
"""
from pathlib import Path
from collections import Counter, defaultdict
from contextlib import ExitStack
import csv, gzip, hashlib, json
import numpy as np
import pandas as pd
import openpyxl

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/컬럼선별-결측제외-20260915'
INPUT=ROOT/'data/interim/분석입력-2020-2024/manifest.json'
PRIOR=ROOT/'data/processed/동별예방분석-20260914/receipts'
ID,DT,PROVINCE,SGG,EMD,TYPE,SUB,RESULT,PATH=(
    'DCLR_RCPT_NO','DCLR_DT','CLMTY_CTPV_NM','CLMTY_SGG_NM','CLMTY_EMD_NM',
    'EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','RCPT_PATH_NM')
REQUIRED_DONG=[ID,DT,PROVINCE,SGG,EMD,TYPE,SUB,RESULT]
REQUIRED_TIME=[ID,DT,PROVINCE,TYPE,SUB,RESULT]
SELECTED=REQUIRED_DONG+[PATH]
AUXILIARY=[PATH,'ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT',
           'GRNDS_CTPV_NM','GRNDS_SGG_NM','CMPTNC_FRSTN_NM','PLCSCN_CNTR_NM',
           'OTR_CTPV_DCLR_YN','OTR_CTPV_DSPT_YN','CLLBC_YN','JNT_CRSP_YN',
           'CENTR_RSUN_DSPT_DMND_YN','CHEM_ACDNT_YN']
KEYS=['source_file','source_record_index']
DERIVED=['year','month','weekday','hour','season']
OPERATIONS=['업무운행','훈련출동','구급차소독']
WEEK=['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
SEASON={1:'겨울',2:'겨울',3:'봄',4:'봄',5:'봄',6:'여름',7:'여름',8:'여름',9:'가을',10:'가을',11:'가을',12:'겨울'}

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads(INPUT.read_text(encoding='utf-8-sig'))
    old_manifest=json.loads((PRIOR/'manifest.json').read_text(encoding='utf-8'))
    evidence_path=PRIOR/'audit_evidence.json'
    evidence_hash=next(x['sha256'] for x in old_manifest['outputs'] if x['file']==evidence_path.name)
    assert sha(evidence_path)==evidence_hash,'Prior audit artifact has changed'
    old_evidence={x['year']:x for x in json.loads(evidence_path.read_text(encoding='utf-8'))}
    workbook=ROOT/'data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx'
    wb=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    descriptions={}
    for row in wb.active.values:
        if len(row)>5 and isinstance(row[1],str) and row[1].upper() in set(manifest['reports'][0]['sourceColumns']):
            descriptions[row[1].upper()]=(row[4],row[5])
    wb.close()
    tables=defaultdict(Counter); dimensions={}; missing=[]; evidence=[]; reconciliation=[]
    def add(name,frame,keys):
        dimensions[name]=keys
        tables[name].update(frame.groupby(keys,sort=False,dropna=False).size().to_dict())
    for item in manifest['reports']:
        year=item['year']; path=ROOT/item['file']; digest=sha(path)
        prior=old_evidence[year]
        assert digest==item['sha256']==prior['sha256'],f'Input SHA mismatch {year}'
        with path.open(encoding=item['encoding'],newline='') as f: headers=next(csv.reader(f))
        assert headers==prior['original_headers'],f'Header mismatch {year}'
        normalized=[h.upper() for h in headers]
        assert set(normalized)==set(manifest['reports'][0]['sourceColumns']) and len(normalized)==38
        assert prior['new_checks']['datetime_invalid']==0,'Prior invalid datetime requires a revised complete-case policy'
        evidence.append({'year':year,'file':item['file'],'sha256':digest,'bytes':path.stat().st_size,
            'headers_match_prior_audit':True,'prior_quality_evidence':str(evidence_path.relative_to(ROOT)),
            'prior_quality_evidence_sha256':evidence_hash,'reused_checks':'Date/time components and ID uniqueness were verified against this identical raw SHA; not repeated.'})
        counts=Counter(); source_missing=Counter(); busan_missing=Counter(); offset=0
        file_schemas={
            'all_selected':KEYS+SELECTED,
            'auxiliary':KEYS+AUXILIARY,
            'complete_dong':KEYS+REQUIRED_DONG+DERIVED+['spatial_join_status'],
            'complete_temporal':KEYS+REQUIRED_TIME+DERIVED,
            'excluded_dong':KEYS+['region_status','missing_required_columns','exclusion_reasons'],
        }
        with ExitStack() as stack:
            files={name:stack.enter_context(gzip.open(OUT/f'{name}_{year}.csv.gz','wt',encoding='utf-8',newline='',compresslevel=3)) for name in file_schemas}
            for name,cols in file_schemas.items(): pd.DataFrame(columns=cols).to_csv(files[name],index=False)
            for df in pd.read_csv(path,encoding=item['encoding'],dtype=str,keep_default_na=False,chunksize=100000):
                df.columns=df.columns.str.upper(); n=len(df)
                blank=pd.DataFrame({c:df[c].str.strip().eq('') for c in normalized})
                busan=df[PROVINCE].eq('부산광역시')
                for col in normalized:
                    source_missing[col]+=int(blank[col].sum()); busan_missing[col]+=int(blank.loc[busan,col].sum())
                complete_dong=busan&~blank[REQUIRED_DONG].any(axis=1)
                complete_time=busan&~blank[REQUIRED_TIME].any(axis=1)
                assert not (complete_dong&~complete_time).any()
                df['source_file']=item['file']; df['source_record_index']=np.arange(offset+1,offset+n+1)
                # String slicing is justified by reused, hash-matched full datetime validation.
                cleaned_dt=df[DT].str.strip(); dates=pd.to_datetime(cleaned_dt,format='%Y%m%d%H%M%S',errors='raise')
                df['year']=year; df['month']=dates.dt.month; df['hour']=dates.dt.hour
                df['weekday']=dates.dt.dayofweek.map(dict(enumerate(WEEK))); df['season']=df['month'].map(SEASON)
                df['spatial_join_status']='unverified_original_dong_name'
                df['region_status']=np.select([busan,blank[PROVINCE]],['busan_explicit','province_missing'],default='other_province')
                df['missing_required_columns']=''
                for col in REQUIRED_DONG:
                    df['missing_required_columns']=df['missing_required_columns']+np.where(blank[col],col+'|','')
                df['missing_required_columns']=df['missing_required_columns'].str.rstrip('|')
                df['exclusion_reasons']=np.select([blank[PROVINCE],~busan],['province_missing_not_proven_outside_busan','explicit_other_province'],default='')
                df['exclusion_reasons']=df['exclusion_reasons']+np.where(df['missing_required_columns'].ne(''),'|required_fields_missing','')
                df['exclusion_reasons']=df['exclusion_reasons'].str.strip('|')
                masks={'all_selected':pd.Series(True,index=df.index),'auxiliary':pd.Series(True,index=df.index),
                       'complete_dong':complete_dong,'complete_temporal':complete_time,'excluded_dong':~complete_dong}
                for name,cols in file_schemas.items():
                    df.loc[masks[name],cols].to_csv(files[name],index=False,header=False)
                    counts[name]+=int(masks[name].sum())
                df['complete_dong']=complete_dong; df['complete_temporal']=complete_time
                add('exclusion_patterns',df,['year','region_status','complete_dong','complete_temporal','missing_required_columns','exclusion_reasons'])
                # This table includes ALL original regions, including missing province/name strings.
                add('all_original_region_flow',df,['year','region_status',SGG,EMD,'complete_dong','complete_temporal'])
                normal=df[RESULT].eq('정상'); substantive=normal&~df[SUB].isin(OPERATIONS)
                for cohort,cohort_mask in [('before',busan),('complete_temporal',complete_time),('complete_dong',complete_dong)]:
                    for scope,scope_mask in [('A',pd.Series(True,index=df.index)),('B',normal),('C',substantive)]:
                        f=df.loc[cohort_mask&scope_mask].copy(); f['cohort']=cohort; f['scope']=scope
                        counts[f'{cohort}_{scope}']+=len(f)
                        add('annual_classification',f,['year','cohort','scope',TYPE,SUB,RESULT])
                        add('original_dong_classification',f,['year','cohort','scope',SGG,EMD,TYPE,SUB,RESULT])
                        add('original_dong_totals',f,['year','cohort','scope',SGG,EMD])
                        add('receipt_path',f,['year','cohort','scope',PATH])
                        for dim in ['month','weekday','hour','season']:
                            add('time_'+dim,f,['year','cohort','scope',TYPE,SUB,dim])
                        for dim in ['month','hour']:
                            add('original_dong_'+dim,f,['year','cohort','scope',SGG,EMD,TYPE,dim])
                offset+=n
        assert offset==item['rowsFromPriorFullAudit']
        assert counts['complete_dong']+counts['excluded_dong']==offset==counts['all_selected']==counts['auxiliary']
        assert counts['complete_temporal']>=counts['complete_dong']
        for col in normalized:
            for basis,miss,total in [('all_source',source_missing[col],offset),('busan_explicit',busan_missing[col],counts['before_A'])]:
                missing.append({'year':year,'column':col,'basis':basis,'rows':total,'missing_rows':miss,'nonmissing_rows':total-miss,'missing_share':miss/total})
        reconciliation.append({'year':year,'source_rows':offset,'counts':dict(counts),'ledger_partition_verified':True})
        print(f'{year}: source={offset:,}; busan={counts["before_A"]:,}; complete dong={counts["complete_dong"]:,}; temporal={counts["complete_temporal"]:,}',flush=True)
    pd.DataFrame(missing).sort_values(['column','year','basis']).to_csv(OUT/'column_missing_by_year.csv',index=False,encoding='utf-8-sig')
    decisions=[]
    for col in manifest['reports'][0]['sourceColumns']:
        if col in REQUIRED_DONG:
            selection='기본분석 선택'; required='동 완전행 필수'+('·시간 완전행 필수' if col in REQUIRED_TIME else '')
            reason={ID:'접수행 식별 확인. 사건·환자 고유성은 뜻하지 않음; 공개 웹에는 제공하지 않음.',DT:'신고 시점의 단일 기준. 기존 전체 검증된 일시에서 연월요일시간계절 파생.',PROVINCE:'부산 명시 판정. 미기재를 부산 밖으로 단정하지 않음.',SGG:'동명 동명이인 구분과 구군별 비교. 공간 연결 검증은 별도.',EMD:'원문 읍면동 비교. 행정동·법정동 및 시점별 경계 미검증.',TYPE:'신고 종별 구성 비교. 사건·출동·환자 수와 구분.',SUB:'세부 신고 특성 비교. 분류 신규 관측을 코드 신설로 단정하지 않음.',RESULT:'전체/정상/운영성 제외 조건 비교. 동일신고도 전체 검산에 유지.'}[col]
        elif col in AUXILIARY:
            selection='보조자료 분리보관'; required='필수 아님'
            if col==PATH: reason='접수경로 특성에 유용하나 사건 특성의 필수값은 아니므로 결측으로 행을 제외하지 않음.'
            elif col in ['ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']: reason='좌표 의미·좌표계·정확도·유형별 적용 범위 확인 후 공간 검증에 사용. 결측 대체·두 좌표 혼용·필수 삭제조건 적용 금지.'
            elif col.startswith('GRNDS'): reason='재난지역과 현장지역의 불일치 검증용. CLMTY 지역을 임의 대체하지 않음.'
            elif col in ['CMPTNC_FRSTN_NM','PLCSCN_CNTR_NM']: reason='기존 관할·대응 배경의 보조 기록. 실제 운영 범위·가용성·응답 성과는 별도 확인.'
            elif col=='OTR_CTPV_DCLR_YN': reason='타 시도본부에 같은 내용의 신고 여부. Y를 부산 밖 사건으로 해석하지 않음. 공란을 N으로 바꾸지 않음.'
            else: reason='콜백·공동대응·출동 및 특수상황 보조 플래그. 공란이 많고 공란=N 미확인이므로 필수값으로 사용하지 않음.'
        else:
            selection='현재 분석표 제외·원본 유지'; required='필수 아님'
            if col in ['DCLR_YMD','DCLR_TM','DCLR_YR','DCLR_MM','DCLR_DAY','DCLR_HR','DCLR_MN','DCLR_DOW','SEASN_NM','QTR_NO']:
                reason='DCLR_DT와 일관성 검증된 중복 시간 표현. 기본표에는 단일 일시에서 파생한 필요한 시간 변수 사용.'
            elif col.startswith('RCPT_END'): reason='접수종료 시점은 신고 시점·현장 도착시간과 다름. 현재 질문에 필요하지 않고 종료역전 6행은 기존 감사에 보존.'
            elif col=='EMRG_RSCU_SCL_NM': reason='긴급구조규모명은 출동·사건 수를 대신하지 않음. 현재 종별·분류 기술통계에 추가 필요성 없음.'
            elif col=='CTY_FRMVL_SE_NM': reason='현재 부산 원문지역별 비교에 추가 설명력이 확인되지 않은 도시농촌 구분. 상세 지역 환경은 질문 선정 후 확보.'
            else: raise AssertionError(f'Unexplained column {col}')
        korean,description=descriptions.get(col,('',''))
        decisions.append({'column':col,'korean_name':korean,'selection':selection,'requiredness':required,'reason':reason,'source_description':description})
    assert len(decisions)==38
    pd.DataFrame(decisions).to_csv(OUT/'column_decisions.csv',index=False,encoding='utf-8-sig')
    frames={}
    for name,counts in tables.items():
        cols=dimensions[name]; rows=[list(k)+[int(v)] for k,v in counts.items()]
        f=pd.DataFrame(rows,columns=cols+['count']).sort_values(cols)
        if name.startswith('time_'):
            dim=name[5:]; denom=[]
            for yr in manifest['analysisYears']:
                dates=pd.date_range(f'{yr}-01-01',f'{yr}-12-31')
                domain={'month':range(1,13),'weekday':WEEK,'hour':range(24),'season':list(set(SEASON.values()))}[dim]
                for value in domain:
                    days=(sum(dates.month==value) if dim=='month' else sum(WEEK[d]==value for d in dates.dayofweek) if dim=='weekday' else sum(SEASON[m]==value for m in dates.month) if dim=='season' else len(dates))
                    denom.append({'year':yr,dim:value,'calendar_days':int(days)})
            f=f.merge(pd.DataFrame(denom),on=['year',dim],validate='many_to_one'); f['receipts_per_calendar_day']=f['count']/f['calendar_days']
        f.to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig'); frames[name]=f
        if 'cohort' in cols:
            index=[c for c in cols if c!='cohort']
            retention=f.pivot(index=index,columns='cohort',values='count').fillna(0).astype(int).reset_index()
            for cohort in ['before','complete_temporal','complete_dong']:
                if cohort not in retention: retention[cohort]=0
            for cohort in ['complete_temporal','complete_dong']:
                assert (retention[cohort]<=retention['before']).all()
                retention[cohort+'_retention']=retention[cohort]/retention['before'].replace(0,np.nan)
                retention[cohort+'_removed']=retention['before']-retention[cohort]
            retention.to_csv(OUT/f'{name}_retention.csv',index=False,encoding='utf-8-sig')
    dong_retention=pd.read_csv(OUT/'original_dong_totals_retention.csv',keep_default_na=False)
    dong_retention['disappears_after_dong_filter']=(dong_retention['before']>0)&dong_retention['complete_dong'].eq(0)
    dong_retention['name_present']=dong_retention[SGG].ne('')&dong_retention[EMD].ne('')
    dong_retention['interpretation']='Original text name only; disappearing does not mean a real administrative dong has zero incidents.'
    dong_retention.to_csv(OUT/'original_dong_disappearance.csv',index=False,encoding='utf-8-sig')
    for rec in reconciliation:
        year=rec['year']
        for cohort in ['before','complete_temporal','complete_dong']:
            for scope in ['A','B','C']:
                expected=rec['counts'][f'{cohort}_{scope}']
                for name in ['annual_classification','original_dong_classification','original_dong_totals','receipt_path','time_month','time_weekday','time_hour','time_season','original_dong_month','original_dong_hour']:
                    f=frames[name]; actual=int(f.loc[f.year.eq(year)&f.cohort.eq(cohort)&f.scope.eq(scope),'count'].sum())
                    assert actual==expected,(year,cohort,scope,name,actual,expected)
        rec['ten_aggregate_tables_reconciled_for_all_cohorts_and_scopes']=True
    dump('input_and_reused_audit_evidence.json',evidence)
    dump('schemas.json',{'language':'Raw column English names uppercased; values unchanged, even padding. Blank detection strips whitespace only.',
        'files':file_schemas,'trace_key':'source_file + source_record_index (1-based parsed CSV data record; header excluded)',
        'complete_dong':'Exactly eight required raw values nonblank and explicitly Busan. All raw selected columns in this file are nonblank.',
        'complete_temporal':'Exactly six required raw values nonblank and explicitly Busan; district and dong deliberately omitted, not imputed.',
        'all_selected':'Nine useful raw columns with original missing values retained; RCPT_PATH_NM also copied to auxiliary for independent optional use.',
        'auxiliary':'All raw rows, no coordinate or flag fills. Join one-to-one by trace key. Not a public web input.',
        'excluded_dong':'Every raw row not in complete_dong; all missing required columns enumerated, plus independent province ascertainment reason.',
        'derived':{'year':'source-year consistent with verified DCLR_DT','month':'calendar month 1..12','weekday':'Korean weekday from DCLR_DT','hour':'0..23 hour of DCLR_DT','season':'Mar-May spring, Jun-Aug summer, Sep-Nov autumn, Dec-Feb winter; calendar-year winter is not contiguous'},
        'privacy':'Local row-level intermediates include receipt identifiers and auxiliary coordinates. Only reviewed aggregated data may be supplied to the web.'})
    writer_names={'column_missing_by_year.csv','column_decisions.csv','original_dong_disappearance.csv',
                  'input_and_reused_audit_evidence.json','schemas.json'}
    writer_names.update(f'{name}_{year}.csv.gz' for name in file_schemas for year in manifest['analysisYears'])
    writer_names.update(f'{name}.csv' for name in tables)
    writer_names.update(f'{name}_retention.csv' for name in tables if 'cohort' in dimensions[name])
    dump('manifest.json',{'input_manifest':str(INPUT.relative_to(ROOT)),'input_manifest_sha256':sha(INPUT),
        'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(Path(__file__)),
        'workbook':str(workbook.relative_to(ROOT)),'workbook_sha256':sha(workbook),
        'required_dong_fields':REQUIRED_DONG,'required_temporal_fields':REQUIRED_TIME,
        'missing_rule':'Empty or whitespace-only; literal strings such as NA are not silently converted to missing. No imputation. Exact Busan province match.',
        'scope_rules':{'A':'All processing results in corresponding cohort','B':'A and processing result 정상','C':'B excluding exact subtypes '+', '.join(OPERATIONS)},
        'before_definition':'Busan-explicit rows BEFORE required-field missing exclusions. Exclusion ledger additionally retains all non-Busan-established raw rows.',
        'unit':'Receipt record, not distinct incident/dispatch/patient. No deduplication.',
        'spatial_status':'Every original dong remains unverified for administrative-boundary/population joining. Complete fields do not validate geography.',
        'beehive_policy':'벌집제거 remains only in all-type aggregates for conservation checks; excluded from candidate selection, further investigation and proposals.',
        'retention_denominator':'Matching before-filter Busan cohort, same year/scope/category; zero denominator has no defined retention.',
        'zero_cells':'Observed group combinations only. Do not interpret an unobserved code as proven zero under a stable code system.',
        'reconciliation':reconciliation,
        'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name in writer_names]})

if __name__=='__main__': main()
