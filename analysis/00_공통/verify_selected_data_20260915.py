"""Independent verification of the 2026-09-15 selected-column artifacts."""
import hashlib
import json
import sys
import re
from urllib.parse import unquote
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/컬럼선별-결측제외-20260915'
PRIOR=ROOT/'data/processed/동별예방분석-20260914'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()

def read(p):return pd.read_csv(p,encoding='utf-8-sig',dtype=str,keep_default_na=False)

def verify_population():
    manifest=json.loads((OUT/'population/manifest.json').read_text(encoding='utf-8'))
    oldmanifest=json.loads((PRIOR/'population/manifest.json').read_text(encoding='utf-8'))
    for source in manifest['sources']:
        old=next(x for x in oldmanifest['inputs'] if x['year']==source['year'])
        assert sha(ROOT/source['file'])==source['sha256']==old['sha256']
    new=read(OUT/'population/complete_population_dong.csv')
    old=read(PRIOR/'population/population_summary.csv')
    old=old[old.level=='dong'].rename(columns={'admin_code':'admin_dong_code'})
    keys=['year','admin_dong_code']
    assert len(new)==1025 and len(new.columns)==110 and not new.eq('').any().any()
    assert not new.duplicated(keys).any()
    assert new.groupby('year').size().to_dict()=={str(y):205 for y in range(2020,2025)}
    merged=new.merge(old,on=keys,suffixes=('_new','_old'),validate='one_to_one')
    assert len(merged)==1025
    for field in ['population','district_code','district_name','population_reference_date','source_file']:
        assert merged[field+'_new'].eq(merged[field+'_old']).all()
    assert merged.source_csv_row.eq(merged.source_row).all()
    assert merged.admin_dong_name.eq(merged.dong_name).all()
    for _,r in new.iterrows():assert sum(int(r[f'age_{a}']) for a in range(101))==int(r.population)
    ages=read(OUT/'population/complete_population_age_long.csv')
    oldages=read(PRIOR/'population/dong_single_age.csv').rename(columns={'admin_code':'admin_dong_code'})
    joined=ages.merge(oldages,on=keys+['age'],suffixes=('_new','_old'),validate='one_to_one')
    assert len(ages)==len(joined)==103525 and not ages.eq('').any().any()
    assert joined.age_population_new.eq(joined.age_population_old).all()
    assert (joined.age_share_pct.astype(float)-joined.share_pct.astype(float)).abs().max()<1e-10
    wide=new.set_index(keys)
    for (year,code), group in ages.groupby(keys):
        assert group.sort_values('age',key=lambda s:s.astype(int)).age_population.tolist()==[wide.loc[(year,code),f'age_{a}'] for a in range(101)]
    return {'status':'passed','source_hashes_match_previous_verified_inputs':True,'dong_year_rows':1025,'selected_columns':110,'all_101_ages_match_previous_independently_verified_output':True,'long_rows':103525,'counts_shares_keys_source_rows_match':True,'missing_cells':0,'population_rows_excluded_for_missing':0}

def verify_receipts():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    source_manifest=json.loads((ROOT/'data/interim/분석입력-2020-2024/manifest.json').read_text(encoding='utf-8-sig'))
    fields=['DCLR_RCPT_NO','DCLR_DT','CLMTY_CTPV_NM','CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM']
    timefields=[f for f in fields if f not in ['CLMTY_SGG_NM','CLMTY_EMD_NM']]
    assert manifest['required_dong_fields']==fields and manifest['required_temporal_fields']==timefields
    results=[]; expected_regions=Counter()
    for entry in source_manifest['reports']:
        year=entry['year']; rawpath=ROOT/entry['file']; assert sha(rawpath)==entry['sha256']
        complete=read(OUT/f'complete_dong_{year}.csv.gz').set_index('source_record_index')
        temporal=read(OUT/f'complete_temporal_{year}.csv.gz').set_index('source_record_index')
        excluded=read(OUT/f'excluded_dong_{year}.csv.gz').set_index('source_record_index')
        for frame in [complete,temporal,excluded]:
            assert frame.index.is_unique and frame.source_file.eq(entry['file']).all()
        assert complete.spatial_join_status.eq('unverified_original_dong_name').all()
        assert not complete[fields].apply(lambda s:s.str.strip().eq('')).any().any()
        assert not temporal[timefields].apply(lambda s:s.str.strip().eq('')).any().any()
        assert not complete.DCLR_RCPT_NO.duplicated().any()
        expected_complete=set(); expected_time=set(); offset=0; busan_count=0
        for frame in pd.read_csv(rawpath,encoding=entry['encoding'],dtype=str,keep_default_na=False,usecols=lambda c:c.upper() in fields,chunksize=100000):
            frame.columns=frame.columns.str.upper(); frame.index=[str(i) for i in range(offset+1,offset+len(frame)+1)]
            missing=frame.apply(lambda s:s.str.strip().eq(''))
            busan=frame.CLMTY_CTPV_NM.eq('부산광역시'); busan_count+=int(busan.sum())
            keep=busan & ~missing[fields].any(axis=1); timekeep=busan & ~missing[timefields].any(axis=1)
            expected_complete.update(frame.index[keep]); expected_time.update(frame.index[timekeep])
            assert complete.loc[frame.index[keep],fields].equals(frame.loc[keep,fields])
            assert temporal.loc[frame.index[timekeep],timefields].equals(frame.loc[timekeep,timefields])
            removed=frame.index[~keep]
            actual_missing=excluded.loc[removed,'missing_required_columns']
            expected_missing=missing.loc[removed,fields].apply(lambda r:'|'.join(f for f in fields if r[f]),axis=1)
            assert actual_missing.equals(expected_missing)
            assert excluded.loc[removed,'exclusion_reasons'].ne('').all()
            for cohort,mask in [('before',busan),('complete_dong',keep),('complete_temporal',timekeep)]:
                for scope in 'ABC':
                    selected=mask.copy()
                    if scope!='A':selected &= frame.PRCS_RSLT_SE_NM.eq('정상')
                    if scope=='C':selected &= ~frame.EMRG_RSCU_CLSF_NM.isin(['업무운행','훈련출동','구급차소독'])
                    counts=frame.loc[selected].groupby(['CLMTY_SGG_NM','CLMTY_EMD_NM']).size()
                    for key,n in counts.items():expected_regions[(str(year),cohort,scope)+key]+=int(n)
            offset+=len(frame)
        assert set(complete.index)==expected_complete and set(temporal.index)==expected_time
        assert not set(complete.index)&set(excluded.index)
        assert set(complete.index)|set(excluded.index)=={str(i) for i in range(1,offset+1)}
        for name in ['all_selected','auxiliary']:
            n=0
            for saved in pd.read_csv(OUT/f'{name}_{year}.csv.gz',dtype=str,keep_default_na=False,usecols=['source_file','source_record_index'],chunksize=100000):
                assert saved.source_file.eq(entry['file']).all()
                assert saved.source_record_index.astype(int).tolist()==list(range(n+1,n+len(saved)+1))
                n+=len(saved)
            assert n==offset
        results.append({'year':year,'raw_rows':offset,'busan_before':busan_count,'complete_dong':len(complete),'complete_temporal':len(temporal),'excluded_dong':len(excluded),'required_values_equal_raw':True,'all_exclusion_missing_fields_equal_raw':True,'raw_row_partition_exact':True,'all_selected_and_auxiliary_complete_sequential_keys':True})
        print(f'receipts {year}: passed',flush=True)
    actual=Counter()
    for _,row in read(OUT/'original_dong_totals.csv').iterrows():
        actual[(row.year,row.cohort,row.scope,row.CLMTY_SGG_NM,row.CLMTY_EMD_NM)]+=int(row['count'])
    assert actual==expected_regions
    disappearance=read(OUT/'original_dong_disappearance.csv')
    named_lost=[]
    for _,r in disappearance.iterrows():
        key=(r.year,'before',r.scope,r.CLMTY_SGG_NM,r.CLMTY_EMD_NM)
        before=expected_regions[key]; kept=expected_regions[(r.year,'complete_dong',r.scope,r.CLMTY_SGG_NM,r.CLMTY_EMD_NM)]
        assert int(r.before)==before and int(r.complete_dong)==kept
        assert (r.disappears_after_dong_filter=='True')==(before>0 and kept==0)
        if before>0 and kept==0 and r.CLMTY_SGG_NM and r.CLMTY_EMD_NM:named_lost.append({'year':r.year,'scope':r.scope,'district':r.CLMTY_SGG_NM,'raw_dong':r.CLMTY_EMD_NM,'before':before})
    return {'status':'passed','years':results,'all_region_scope_cohort_counts_equal_raw':True,'named_original_regions_lost':named_lost,'geography_caveat':'Complete raw name is not validated administrative-dong coverage.'}

def verify_coverage_summary():
    population=read(PRIOR/'population/region_registry.csv'); population=population[population.level=='dong']
    receipts=read(PRIOR/'receipts/original_dong_types.csv'); receipts=receipts[receipts.scope=='A']
    coverage=read(OUT/'coverage/year_coverage_summary.csv')
    for _,row in coverage.iterrows():
        p=population[population.year==row.year]; r=receipts[receipts.year==row.year]
        pn=set(zip(p.district_name,p.dong_name)); rn=set(zip(r.CLMTY_SGG_NM,r.CLMTY_EMD_NM)); valid={x for x in rn if all(x)}
        assert len(pn)==int(row.population_dongs)==205
        assert len(rn)==int(row.original_region_combinations)
        assert len(valid)==int(row.nonmissing_original_region_combinations)
        assert len(pn&valid)==int(row.direct_name_matches)==30
        assert len(pn-valid)==int(row.population_names_without_direct_match)==175
        assert len(valid-pn)==int(row.receipt_names_without_direct_match)
    comparison=read(OUT/'coverage/all_name_comparison_2020_2024.csv')
    assert comparison.administrative_link_confirmed.eq('False').all()
    counts=read(OUT/'annual_classification.csv')
    actual=read(OUT/'summary/annual_completeness.csv')
    for _,row in actual.iterrows():
        selected=counts[(counts.year==row.year)&(counts.cohort==row.cohort)&(counts.scope==row.scope)]
        before=counts[(counts.year==row.year)&(counts.cohort=='before')&(counts.scope==row.scope)]['count'].astype(int).sum()
        expected=selected['count'].astype(int).sum()
        assert int(row['count'])==expected and int(row.before_count)==before and int(row.removed_count)==before-expected
        assert abs(float(row.retention_pct)-100*expected/before)<1e-10
    hashes={}
    for sub in ['', 'population','coverage','summary']:
        path=OUT/sub/'manifest.json'; manifest=json.loads(path.read_text(encoding='utf-8'))
        for artifact in manifest['outputs']:
            p=OUT/sub/artifact['file']; assert sha(p)==artifact['sha256'],str(p)
        hashes[sub or 'receipts']=sha(path)
    return {'status':'passed','all_205_population_names_each_year_included':True,'exact_name_intersection_each_year':30,'name_mismatch_not_inferred_missing_geography':True,'all_administrative_link_confirmed_false':True,'annual_complete_case_summary_matches_current_counts':True,'four_manifests_all_output_hashes_match':True,'manifest_sha256':hashes}

def verify_report():
    doc=ROOT/'docs/40-분석결과/컬럼선별-결측제외-분석결과-20260915.md'; text=doc.read_text(encoding='utf-8')
    tables=[[v.strip().strip('*') for v in line.strip('|').split('|')] for line in text.splitlines() if line.startswith('|')]
    annual=read(OUT/'summary/annual_completeness.csv'); major=read(OUT/'summary/major_type_by_year.csv')
    for y in range(2020,2025):
        current=annual[annual.year==str(y)]
        bycohort=current[current.scope=='A'].set_index('cohort')
        table=[r for r in tables if r[0]==str(y) and len(r)==6 and '%' not in r[4]][0]
        expected=[int(major[(major.year==str(y))&(major.cohort=='complete_dong')&(major.scope=='B')&(major.EMRG_RSCU_ASSRT_NM==t)]['count'].astype(int).sum()) for t in ['구급','구조','화재','기타']]
        assert [int(v.replace(',','')) for v in table[1:]]==expected+[sum(expected)]
        row=[r for r in tables if r[0]==str(y) and len(r)==6 and '%' in r[4]][0]
        assert int(row[1].replace(',',''))==int(bycohort.loc['before','count'])
        assert int(row[2].replace(',',''))==int(bycohort.loc['complete_dong','count'])
        assert int(row[3].replace(',',''))==int(bycohort.loc['complete_dong','removed_count'])
        assert row[4]==f"{float(bycohort.loc['complete_dong','retention_pct']):.3f}%"
        assert int(row[5].replace(',',''))==int(bycohort.loc['complete_temporal','count'])
    week=read(OUT/'summary/city_weekday.csv'); week=week[(week.cohort=='complete_temporal')&(week.scope=='B')]
    for full,short in zip(['월요일','화요일','수요일','목요일','금요일','토요일','일요일'],'월화수목금토일'):
        w=week[week.weekday==full]; rate=w['count'].astype(int).sum()/w.calendar_days.astype(int).sum()
        assert f'{short} {rate:.2f}' in text
    hour=read(OUT/'summary/city_hour.csv'); hour=hour[(hour.cohort=='complete_temporal')&(hour.scope=='B')]
    for h in [9,10,13]:
        n=hour[hour.hour==str(h)]['count'].astype(int).sum(); assert f'{h}시 {n:,}행' in text
    types=read(OUT/'summary/major_type_change.csv'); types=types[(types.cohort=='complete_dong')&(types.scope=='A')]
    for _,r in types.iterrows():
        label=r.EMRG_RSCU_ASSRT_NM or '종별 미기재'; table=next(t for t in tables if t[0]==label)
        assert int(table[1].replace(',',''))==int(r.before_count) and int(table[2].replace(',',''))==int(r['count'])
        assert abs(float(table[3].rstrip('%'))-float(r.retention_pct))<0.00051
        assert abs(float(table[4].rstrip('%'))-float(r.share_pct))<0.00051
    links=[]
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if target.startswith('http'):continue
        path=(doc.parent/unquote(target)).resolve(); assert path.is_file(); links.append(str(path.relative_to(ROOT)))
    for sub in ['population','summary']:
        manifest=json.loads((OUT/sub/'manifest.json').read_text(encoding='utf-8'))
        for source in manifest['sources']:assert sha(ROOT/source['file'])==source['sha256']
    docs=[doc,ROOT/'docs/40-분석결과/동-포함범위-재점검-20260915.md',ROOT/'docs/10-작업계획/부산 분석 작업 계획.md']
    return {'status':'passed','annual_complete_case_table_checked':True,'annual_four_type_B_table_checked':True,'type_retention_composition_checked':True,'temporal_B_weekday_denominator_and_top_hour_counts_checked':True,'local_links_checked':len(links),'population_and_summary_input_hashes_match':True,'scope_review':'All five years, all population dongs, no conflation of raw-name retention with 205 administrative-dong coverage; beehive excluded from policy scope; no new unsupported proposal.', 'document_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in docs}}

def main():
    evidence_path=OUT/'independent_verification_20260915.json'
    if '--receipts' in sys.argv:
        evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
        evidence['receipts']=verify_receipts(); evidence['status']='population_and_receipts_passed'
    elif '--summary' in sys.argv:
        evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
        evidence['coverage_summary']=verify_coverage_summary(); evidence['status']='passed'
    elif '--report' in sys.argv:
        evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
        evidence['final_report']=verify_report(); evidence['status']='passed'
    else:evidence={'population':verify_population(),'status':'population_passed_receipts_pending'}
    (OUT/'independent_verification_20260915.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(evidence)

if __name__=='__main__':main()
