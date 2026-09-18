"""Independent checks of newly used channel, jurisdiction, region and coordinate fields."""
from collections import Counter
import json
import pandas as pd
from verify_all_selected_20260915 import BASE,OUT,CORE,EXTRA,read,sha

def main():
    dimensions={
       'selected17_receipt_path_distribution':['year','scope','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','RCPT_PATH_NM'],
       'selected17_jurisdiction_distribution':['year','scope','CLMTY_SGG_NM','EMRG_RSCU_ASSRT_NM','CMPTNC_FRSTN_NM','PLCSCN_CNTR_NM'],
       'selected17_region_name_comparison':['year','scope','EMRG_RSCU_ASSRT_NM','province_names_equal','district_names_equal'],
       'selected17_region_name_crosstab':['year','scope','EMRG_RSCU_ASSRT_NM','CLMTY_CTPV_NM','GRNDS_CTPV_NM','CLMTY_SGG_NM','GRNDS_SGG_NM']}
    counts={k:Counter() for k in dimensions};issues=set();paircounts={}
    qc=read(OUT/'selected17_coordinate_quality.csv')
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    assert set(manifest['current_selected_fields'])==set(CORE+EXTRA)
    assert 'approved' in manifest['status'].lower()
    for year in range(2020,2025):
        data=read(OUT/f'complete_17_{year}.csv.gz')
        data['province_names_equal']=data.CLMTY_CTPV_NM.eq(data.GRNDS_CTPV_NM).astype(str)
        data['district_names_equal']=data.CLMTY_SGG_NM.eq(data.GRNDS_SGG_NM).astype(str)
        for scope in 'ABC':
            selected=data.copy()
            if scope!='A':selected=selected[selected.PRCS_RSLT_SE_NM=='정상']
            if scope=='C':selected=selected[~selected.EMRG_RSCU_CLSF_NM.isin(['업무운행','훈련출동','구급차소독'])]
            selected['scope']=scope
            for name,keys in dimensions.items():counts[name].update(selected.groupby(keys).size().to_dict())
        numbers=data[['ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']].apply(pd.to_numeric,errors='coerce')
        for pair,fields in [('incident',['ACDNT_OCRN_LOT','ACDNT_OCRN_LAT']),('damage',['DAMG_RGN_LOT','DAMG_RGN_LAT'])]:
            x,y=(numbers[c] for c in fields)
            parsed=x.notna()&y.notna();valid=x.between(-180,180)&y.between(-90,90);zero=x.eq(0)|y.eq(0)
            expected={'rows':len(data),'numeric_parse_failure':int((~parsed).sum()),'zero_component':int(zero.sum()),'outside_degree_world_range':int((parsed&~valid).sum()),'within_degree_world_range':int(valid.sum())}
            saved=qc[(qc.year==str(year))&(qc.pair==pair)].iloc[0]
            for field,n in expected.items():assert int(saved[field])==n
            for index in data.index[(~parsed)|zero|(parsed&~valid)]:
                reasons=[]
                if not parsed[index]:reasons.append('numeric_parse_failure')
                if zero[index]:reasons.append('zero_component')
                if parsed[index] and not valid[index]:reasons.append('outside_degree_world_range')
                issues.add((str(year),data.at[index,'source_file'],data.at[index,'source_record_index'],pair,'|'.join(reasons)))
        parse=numbers.notna().all(axis=1)
        exact=numbers.ACDNT_OCRN_LOT.eq(numbers.DAMG_RGN_LOT)&numbers.ACDNT_OCRN_LAT.eq(numbers.DAMG_RGN_LAT)&parse
        near=(numbers.ACDNT_OCRN_LOT-numbers.DAMG_RGN_LOT).abs().le(1e-6)&(numbers.ACDNT_OCRN_LAT-numbers.DAMG_RGN_LAT).abs().le(1e-6)&parse
        literal=data.ACDNT_OCRN_LOT.eq(data.DAMG_RGN_LOT)&data.ACDNT_OCRN_LAT.eq(data.DAMG_RGN_LAT)
        paircounts[str(year)]={'rows':len(data),'both_pairs_numeric':int(parse.sum()),'both_coordinates_numeric_exact_equal':int(exact.sum()),'both_coordinates_text_exact_equal':int(literal.sum()),'both_deltas_within_1e_6_input_units':int(near.sum()),'numeric_pairs_differ':int((parse&~exact).sum()),'at_least_one_parse_failure':int((~parse).sum())}
    for name,expected in counts.items():
        saved=read(OUT/f'{name}.csv'); actual=Counter()
        for _,row in saved.iterrows():actual[tuple(row[k] for k in dimensions[name])]+=int(row['count'])
        assert actual==expected,name
    for _,row in read(OUT/'selected17_coordinate_pair_comparison.csv').iterrows():
        for key,n in paircounts[row.year].items():assert int(row[key])==n
    saved=read(OUT/'selected17_coordinate_quality_records.csv')
    assert set(saved.itertuples(index=False,name=None))==issues
    evidence_path=BASE/'independent_verification.json';evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
    evidence['selected17_new_field_usage']={'status':'passed','all_four_distribution_cells_match_complete17':True,'all_coordinate_quality_and_pair_comparison_counts_match':True,'coordinate_issue_records_match':True,'coordinate_issue_count':len(issues),'current_policy':'17 selected raw columns all required; no optional-field missingness in current input','scope':'New fields checked against previously raw-verified complete17 files; full raw verification not repeated.'}
    evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Selected17 extension independent checks passed')

if __name__=='__main__':main()
