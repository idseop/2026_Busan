"""Verify new complete17 time panels and conditional age backgrounds."""
from collections import Counter
import json
import pandas as pd
from verify_all_selected_20260915 import BASE,ROOT,OUT,read,sha

def main():
    analysis=BASE/'analysis'
    fields={'annual_type':['EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'],
      'month_type':['month','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'],
      'weekday_type':['weekday','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'],
      'hour_band_type':['hour_band','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'],
      'original_region_type':['CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'],
      'original_region_total':['CLMTY_SGG_NM','CLMTY_EMD_NM']}
    counters={name:Counter() for name in fields};days={}
    for year in range(2020,2025):
        data=read(OUT/f'complete_17_{year}.csv.gz')
        dt=pd.to_datetime(data.DCLR_DT.str.strip(),format='%Y%m%d%H%M%S')
        data['month']=dt.dt.month.astype(str);data['weekday']=dt.dt.dayofweek.astype(str);data['date']=dt.dt.strftime('%Y-%m-%d')
        data['hour_band']=dt.dt.hour.map(lambda h:f'{h//4*4:02d}-{h//4*4+3:02d}')
        for scope in 'ABC':
            selected=data
            if scope!='A':selected=selected[selected.PRCS_RSLT_SE_NM=='정상']
            if scope=='C':selected=selected[~selected.EMRG_RSCU_CLSF_NM.isin(['업무운행','훈련출동','구급차소독'])]
            for name,keys in fields.items():
                for key,n in selected.groupby(keys).size().items():counters[name][(str(year),scope)+key]+=int(n)
            for dim in ['month','weekday','hour_band']:
                for value,g in selected.groupby(dim):days[str(year),scope,dim,value]=g.date.nunique() if dim!='hour_band' else selected.date.nunique()
    for name,keys in fields.items():
        saved=read(analysis/f'{name}.csv');actual=Counter()
        for _,r in saved.iterrows():
            actual[tuple(r[k] for k in ['year','scope']+keys)]+=int(r.receipt_count)
            if 'observed_days_denominator' in saved:
                denom=days[r.year,r.scope,keys[0],r[keys[0]]]
                assert int(r.observed_days_denominator)==denom
                assert abs(float(r.receipts_per_observed_day)-int(r.receipt_count)/denom)<1e-10
        assert actual==counters[name],name
    repetition=read(analysis/'original_region_type_repetition_excluding_beehive.csv')
    assert not repetition.EMRG_RSCU_CLSF_NM.eq('벌집제거').any()
    for _,r in repetition.iterrows():
        observed=[]
        for year in range(2020,2025):
            n=counters['original_region_type'][str(year),r.scope,r.CLMTY_SGG_NM,r.CLMTY_EMD_NM,r.EMRG_RSCU_ASSRT_NM,r.EMRG_RSCU_CLSF_NM]
            assert int(r[str(year)])==n;observed.append(n)
        assert int(r.observed_year_count)==sum(n>0 for n in observed)
    background=read(analysis/'conditional_raw_name_population_all_101_ages.csv')
    cross=read(BASE/'linkage/all_raw_names_year_crosswalk.csv')
    age=read(ROOT/'data/processed/동별예방분석-20260914/population/dong_single_age.csv')
    grouped={k:g.sort_values('age',key=lambda s:s.astype(int)) for k,g in age.groupby(['year','admin_code'])}
    assert len(background)==int(cross.code_level_population_join_eligible.eq('True').sum())
    for _,r in background.iterrows():
        assert r.receipt_geography_confirmed=='False' and r.raw_field_semantics_confirmed=='False'
        assert r.code_level_population_join_eligible=='True'
        g=grouped[r.year,r.admin_code]
        for a,(_,original) in enumerate(g.iterrows()):
            assert float(r[f'age_population_{a}'])==int(original.age_population)
            assert abs(float(r[f'share_pct_{a}'])-float(original.share_pct))<1e-10
        for scope in 'ABC':
            assert float(r[f'receipts_{scope}'])==counters['original_region_total'][r.year,scope,r.district_name,r.raw_dong_name]
    manifest=json.loads((analysis/'manifest.json').read_text(encoding='utf-8'))
    for source in manifest['inputs']:assert sha(ROOT/source['file'])==source['sha256']
    for artifact in manifest['outputs']:assert sha(analysis/artifact['file'])==artifact['sha256']
    path=BASE/'independent_verification.json';evidence=json.loads(path.read_text(encoding='utf-8'))
    evidence['complete17_analysis']={'status':'passed','six_full_tables_match_complete17':True,'time_denominators_independently_verified':True,'repetition_rows':len(repetition),'beehive_excluded_from_repetition':True,'conditional_background_rows':len(background),'all_101_age_counts_shares_match_population':True,'no_geographic_confirmation_or_1toN_allocation':True,'analysis_manifest_sha256':sha(analysis/'manifest.json')}
    path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Complete17 analysis independent checks passed')

if __name__=='__main__':main()
