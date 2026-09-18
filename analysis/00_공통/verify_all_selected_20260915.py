"""Independent raw verification of the 8/9/17/22/23 complete-case comparisons."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/processed/동대응-전체결측제외-20260915'
OUT=BASE/'completeness'
CORE=['DCLR_RCPT_NO','DCLR_DT','CLMTY_CTPV_NM','CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM']
EXTRA=['RCPT_PATH_NM','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT','GRNDS_CTPV_NM','GRNDS_SGG_NM','CMPTNC_FRSTN_NM','PLCSCN_CNTR_NM']
FLAGS=['OTR_CTPV_DCLR_YN','OTR_CTPV_DSPT_YN','CLLBC_YN','JNT_CRSP_YN','CENTR_RSUN_DSPT_DMND_YN','CHEM_ACDNT_YN']
SETS={'core8':CORE,'core9':CORE+EXTRA[:1],'provisional17':CORE+EXTRA,'selected22':CORE+EXTRA+[x for x in FLAGS if x!='CENTR_RSUN_DSPT_DMND_YN'],'selected23':CORE+EXTRA+FLAGS}

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def read(path):return pd.read_csv(path,encoding='utf-8-sig',dtype=str,keep_default_na=False)

def main():
    inputs=json.loads((ROOT/'data/interim/분석입력-2020-2024/manifest.json').read_text(encoding='utf-8-sig'))
    policy=json.loads((OUT/'comparison_policy.json').read_text(encoding='utf-8'))
    assert {k:set(v) for k,v in policy['stages'].items()}=={k:set(v) for k,v in SETS.items()}
    results=[]; counts=Counter(); regions=Counter()
    for source in inputs['reports']:
        year=source['year']; path=ROOT/source['file']; assert sha(path)==source['sha256']
        complete=read(OUT/f'complete_17_{year}.csv.gz').set_index('source_record_index')
        excluded=read(OUT/f'excluded_core8_to_17_{year}.csv.gz').set_index('source_record_index')
        for table in [complete,excluded]:assert table.index.is_unique and table.source_file.eq(source['file']).all()
        assert not complete[CORE+EXTRA].apply(lambda s:s.str.strip().eq('')).any().any()
        assert not complete.DCLR_RCPT_NO.duplicated().any()
        expected_keys=set(); expected_excluded=set(); offset=0
        for raw in pd.read_csv(path,encoding=source['encoding'],dtype=str,keep_default_na=False,usecols=lambda c:c.upper() in SETS['selected23'],chunksize=100000):
            raw.columns=raw.columns.str.upper();raw.index=[str(i) for i in range(offset+1,offset+len(raw)+1)]
            missing=raw.apply(lambda s:s.str.strip().eq('')); busan=raw.CLMTY_CTPV_NM.eq('부산광역시')
            masks={name:~missing[fields].any(axis=1) for name,fields in SETS.items()}
            keep17=busan&masks['provisional17']; remove=busan&masks['core8']&~masks['provisional17']
            expected_keys.update(raw.index[keep17]);expected_excluded.update(raw.index[remove])
            assert complete.loc[raw.index[keep17],CORE+EXTRA].equals(raw.loc[keep17,CORE+EXTRA])
            actual=excluded.loc[raw.index[remove],'missing_provisional17_columns']
            expect=missing.loc[remove,CORE+EXTRA].apply(lambda r:'|'.join(f for f in CORE+EXTRA if r[f]),axis=1)
            assert actual.equals(expect)
            for stage,mask in {'raw_busan':busan,**masks}.items():
                if stage!='raw_busan':
                    counts[(str(year),stage,'all_source')]+=int(mask.sum())
                    counts[(str(year),stage,'busan_explicit')]+=int((mask&busan).sum())
                for scope in 'ABC':
                    selected=mask&busan
                    if scope!='A':selected &= raw.PRCS_RSLT_SE_NM.eq('정상')
                    if scope=='C':selected &= ~raw.EMRG_RSCU_CLSF_NM.isin(['업무운행','훈련출동','구급차소독'])
                    counts[(str(year),stage,scope)]+=int(selected.sum())
                    for key,n in raw.loc[selected].groupby(['CLMTY_SGG_NM','CLMTY_EMD_NM']).size().items():regions[(str(year),stage,scope)+key]+=int(n)
            offset+=len(raw)
        assert set(complete.index)==expected_keys and set(excluded.index)==expected_excluded
        assert not expected_keys&expected_excluded
        assert len(expected_keys)+len(expected_excluded)==counts[(str(year),'core8','A')]
        results.append({'year':year,'source_rows':offset,'complete17_rows':len(complete),'core8_to17_excluded':len(excluded),'all_17_values_equal_raw':True,'all_excluded_missing_fields_match_raw':True,'complete_and_excluded_exactly_partition_core8':True})
        print(f'{year}: independent verification passed',flush=True)
    stages=read(OUT/'stage_completeness.csv')
    for _,r in stages.iterrows():
        n=counts[r.year,r.stage,r.basis_or_scope];denom=counts[r.year,'core8',r.basis_or_scope]
        assert n==int(r.complete_rows) and denom==int(r.core8_same_basis_or_scope_rows)
        if r.stage!='raw_busan':assert abs(float(r.retention_vs_core8)-n/denom)<1e-10
    actual=Counter()
    for _,r in read(OUT/'original_region_totals.csv').iterrows():actual[(r.year,r.stage,r.scope,r.CLMTY_SGG_NM,r.CLMTY_EMD_NM)]+=int(r['count'])
    assert actual==regions
    assert all(n==0 for key,n in counts.items() if key[1]=='selected23')
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    for artifact in manifest['outputs']:assert sha(OUT/artifact['file'])==artifact['sha256']
    assert sha(ROOT/'analysis/00_공통/complete_all_selected_20260915.py')==manifest['script_sha256']
    evidence={'status':'passed','scope':'Full raw-field comparison, complete17/exclusion partition, all-stage/scope original-region cells, denominators and manifest output hashes. Spatial matching and final report reviewed separately.',
       'years':results,'all_17_selected_fields_nonmissing':True,'selected23_rows_zero_every_year_all_scopes':True,'selected22_A_by_year':{str(y):counts[str(y),'selected22','A'] for y in range(2020,2025)},'all_stage_scope_counts_and_retention_denominators_match':True,
       'all_original_region_cells_match_raw':True,'completeness_manifest_sha256':sha(OUT/'manifest.json')}
    (BASE/'independent_verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
