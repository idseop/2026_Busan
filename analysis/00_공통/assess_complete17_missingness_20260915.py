"""Diagnose selective missingness; never modify the approved selected17 cohort."""
from collections import Counter, defaultdict
from itertools import zip_longest
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
from select_complete_receipts_2020_2024 import (
    ROOT,REQUIRED_DONG,KEYS,OPERATIONS,ID,DT,PROVINCE,SGG,EMD,TYPE,SUB,RESULT,PATH,sha)

INPUTS=ROOT/'data/processed/컬럼선별-결측제외-20260915'
SELECTED=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
OUT=ROOT/'data/processed/완전행-분석적합성-20260915/missingness'
MOBILE='이동전화'

def dump(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    input_manifest=json.loads((INPUTS/'manifest.json').read_text(encoding='utf-8'))
    selected_manifest=json.loads((SELECTED/'manifest.json').read_text(encoding='utf-8'))
    selected_fields=selected_manifest['current_selected_fields']; assert len(selected_fields)==17
    hashes={x['file']:x['sha256'] for x in input_manifest['outputs']}
    selected_hashes={x['file']:x['sha256'] for x in selected_manifest['outputs']}
    counters=defaultdict(Counter); dims={}; missing=Counter(); relaxed=Counter(); channel_totals=Counter(); checks=[]; input_evidence=[]
    def add(name,f,keys):
        dims[name]=keys
        counters[name].update(f.groupby(keys,sort=False,dropna=False).size().to_dict())
    for baseline in input_manifest['reconciliation']:
        year=baseline['year']; allpath=INPUTS/f'all_selected_{year}.csv.gz'; auxpath=INPUTS/f'auxiliary_{year}.csv.gz'
        selected_path=SELECTED/f'complete_17_{year}.csv.gz'
        for path,expected in [(allpath,hashes[allpath.name]),(auxpath,hashes[auxpath.name]),(selected_path,selected_hashes[selected_path.name])]:
            digest=sha(path); assert digest==expected,(year,path.name)
            input_evidence.append({'year':year,'file':str(path.relative_to(ROOT)),'sha256':digest,'bytes':path.stat().st_size})
        left=pd.read_csv(allpath,dtype=str,keep_default_na=False,chunksize=100000)
        right=pd.read_csv(auxpath,dtype=str,keep_default_na=False,chunksize=100000)
        count=Counter(); offset=0; selected_key_hash=hashlib.sha256(); source_file=None
        scope_counts=Counter()
        for a,b in zip_longest(left,right):
            assert a is not None and b is not None,'Input intermediate row counts differ'
            assert len(a)==len(b) and a[KEYS].equals(b[KEYS]),'Trace-key alignment mismatch'
            assert a[PATH].equals(b[PATH]),'Shared receipt-path field differs'
            assert np.array_equal(a['source_record_index'].astype(int).to_numpy(),np.arange(offset+1,offset+len(a)+1))
            files=a['source_file'].unique(); assert len(files)==1
            if source_file is None: source_file=files[0]
            assert files[0]==source_file
            count['source_rows']+=len(a); offset+=len(a)
            df=pd.concat([a,b.drop(columns=KEYS+[PATH])],axis=1)
            core8=df[PROVINCE].eq('부산광역시')&~df[REQUIRED_DONG].apply(lambda s:s.str.strip().eq('')).any(axis=1)
            df=df.loc[core8].copy(); count['core8_rows']+=len(df)
            blank=df[selected_fields].apply(lambda s:s.str.strip().eq(''))
            missing_count=blank.sum(axis=1); keep=missing_count.eq(0); count['selected17_rows']+=int(keep.sum())
            count['excluded17_rows']+=int((~keep).sum())
            keys=df.loc[keep,'source_record_index'].tolist()
            if keys: selected_key_hash.update(('\n'.join(keys)+'\n').encode())
            df['year']=year; stamp=df[DT].str.strip(); df['month']=stamp.str[4:6].astype(int); df['hour']=stamp.str[8:10].astype(int)
            df['missing_columns']=''
            for col in selected_fields: df['missing_columns']=df['missing_columns']+np.where(blank[col],col+'|','')
            df['missing_columns']=df['missing_columns'].str.rstrip('|')
            for channel,g in df.groupby(PATH,sort=False):
                idx=g.index; channel_totals[(year,channel)]+=len(g)
                for col in selected_fields:
                    missing[(year,channel,col)]+=int(blank.loc[idx,col].sum())
                    relaxed[(year,channel,col)]+=int((missing_count.loc[idx].eq(1)&blank.loc[idx,col]).sum())
            df['selected17']=keep
            add('channel_missing_patterns',df,['year',PATH,'selected17','missing_columns'])
            normal=df[RESULT].eq('정상'); scopes={'A':pd.Series(True,index=df.index),'B':normal,'C':normal&~df[SUB].isin(OPERATIONS)}
            for scope,scope_mask in scopes.items():
                for cohort,mask in [('core8',pd.Series(True,index=df.index)),('selected17',keep),('excluded17',~keep)]:
                    f=df.loc[mask&scope_mask].copy(); f['scope']=scope; f['cohort']=cohort
                    scope_counts[(scope,cohort)]+=len(f)
                    add('channel_retention_counts',f,['year','scope','cohort',PATH])
                    add('channel_type_comparison',f,['year','scope','cohort',PATH,TYPE,SUB,RESULT])
                    mob=f.loc[f[PATH].eq(MOBILE)].copy()
                    scope_counts[(scope,cohort,'mobile')]+=len(mob)
                    add('mobile_types',mob,['year','scope','cohort',TYPE,SUB,RESULT])
                    add('mobile_original_regions',mob,['year','scope','cohort',SGG,EMD,TYPE])
                    for dim in ['month','hour']:
                        add('mobile_'+dim,mob,['year','scope','cohort',TYPE,SUB,dim])
        expected_selected=next(x['provisional17'] for x in selected_manifest['year_counts'] if x['year']==year)
        assert count['source_rows']==baseline['source_rows']
        assert count['core8_rows']==baseline['counts']['complete_dong']
        assert count['selected17_rows']==expected_selected
        assert count['core8_rows']==count['selected17_rows']+count['excluded17_rows']
        expected_hash=hashlib.sha256(); expected_rows=0
        for df in pd.read_csv(selected_path,usecols=KEYS,dtype=str,keep_default_na=False,chunksize=100000):
            assert df.source_file.eq(source_file).all()
            expected_rows+=len(df); expected_hash.update(('\n'.join(df.source_record_index.tolist())+'\n').encode())
        assert expected_rows==count['selected17_rows'] and expected_hash.digest()==selected_key_hash.digest()
        checks.append({'year':year,**dict(count),'paired_intermediate_keys_match':True,'core8_baseline_matches':True,
            'selected17_exact_ordered_trace_keys_match':True,'selected17_record_index_sha256':selected_key_hash.hexdigest(),
            'scope_counts':[{'scope':k[0],'cohort':k[1],'mobile_only':len(k)==3,'rows':v} for k,v in scope_counts.items()]})
        print(f'{year}: core8={count["core8_rows"]:,}; selected17={count["selected17_rows"]:,}; excluded={count["excluded17_rows"]:,}',flush=True)
    missing_rows=[]
    for (year,channel,col),number in missing.items():
        denominator=channel_totals[(year,channel)]
        missing_rows.append({'year':year,PATH:channel,'column':col,'core8_rows':denominator,
            'missing_rows':number,'missing_share':number/denominator,
            'restored_if_only_this_column_requirement_relaxed':relaxed[(year,channel,col)],
            'diagnostic_only':'No relaxation applied; current selected17 unchanged.'})
    pd.DataFrame(missing_rows).to_csv(OUT/'channel_column_missing_and_single_relaxation.csv',index=False,encoding='utf-8-sig')
    frames={}; retentions={}
    for name,counter in counters.items():
        cols=dims[name]
        frame=pd.DataFrame([list(k)+[int(v)] for k,v in counter.items()],columns=cols+['count'])
        frame.sort_values(cols).to_csv(OUT/f'{name}.csv',index=False,encoding='utf-8-sig'); frames[name]=frame
        if 'cohort' in cols:
            keys=[c for c in cols if c!='cohort']
            r=frame.pivot(index=keys,columns='cohort',values='count').reindex(columns=['core8','selected17','excluded17']).fillna(0).astype(int).reset_index()
            assert (r.core8==r.selected17+r.excluded17).all()
            r['retention']=r.selected17/r.core8.replace(0,np.nan)
            r.to_csv(OUT/f'{name}_retention.csv',index=False,encoding='utf-8-sig'); retentions[name]=r
            for check in checks:
                for scope in ['A','B','C']:
                    for cohort in ['core8','selected17','excluded17']:
                        mobile=name.startswith('mobile_')
                        expected=next(x['rows'] for x in check['scope_counts'] if x['scope']==scope and x['cohort']==cohort and x['mobile_only']==mobile)
                        actual=int(frame.loc[frame.year.eq(check['year'])&frame.scope.eq(scope)&frame.cohort.eq(cohort),'count'].sum())
                        assert actual==expected,(name,check['year'],scope,cohort)
    # Descriptive composition shifts within MOBILE calls; no random-missingness inference or test.
    shifts=[]; compositions=[]
    dimensions=[('type','mobile_types',[TYPE]),('district','mobile_original_regions',[SGG]),
        ('original_dong','mobile_original_regions',[SGG,EMD]),('month','mobile_month',['month']),('hour','mobile_hour',['hour'])]
    for dimension,table,keys in dimensions:
        raw=frames[table]
        for scope in ['A','B','C']:
            for year in [2020,2021,2022,2023,2024,'pooled_2020_2024']:
                f=raw.loc[raw.scope.eq(scope)]
                if isinstance(year,int): f=f.loc[f.year.eq(year)]
                p=f.groupby(keys+['cohort'])['count'].sum().unstack('cohort').reindex(columns=['core8','selected17','excluded17']).fillna(0)
                base=p.core8.sum(); selected=p.selected17.sum()
                p['core8_share']=p.core8/base if base else np.nan
                p['selected17_share']=p.selected17/selected if selected else np.nan
                p['share_change_percentage_points']=(p.selected17_share-p.core8_share)*100
                p['retention']=p.selected17/p.core8.replace(0,np.nan)
                shifts.append({'year':year,'scope':scope,'dimension':dimension,'core8_mobile_rows':int(base),
                    'selected17_mobile_rows':int(selected),'total_variation_distance':float((p.selected17_share-p.core8_share).abs().sum()/2),
                    'maximum_absolute_share_change_percentage_points':float(p.share_change_percentage_points.abs().max()),
                    'original_categories_lost':int((p.core8.gt(0)&p.selected17.eq(0)).sum()),
                    'interpretation':'Descriptive composition change within mobile calls, not a random-missingness test.'})
                for index,row in p.iterrows():
                    label=' | '.join(map(str,index)) if isinstance(index,tuple) else str(index)
                    compositions.append({'year':year,'scope':scope,'dimension':dimension,'original_category':label,
                        **{k:int(row[k]) for k in ['core8','selected17','excluded17']},
                        **{k:float(row[k]) for k in ['core8_share','selected17_share','share_change_percentage_points','retention']}})
    pd.DataFrame(shifts).to_csv(OUT/'mobile_composition_shift_summary.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(compositions).to_csv(OUT/'mobile_composition_details.csv',index=False,encoding='utf-8-sig')
    dump('validation.json',{'years':checks,'all_aggregate_counts_and_partitions_match':True,
        'selection_unchanged':'Reconstructed selected17 matches exact ordered source trace keys of the existing approved files.',
        'missingness_interpretation':'Observed missing patterns do not establish MCAR/MAR/MNAR. Column-relaxation counts are diagnostics only.',
        'denominators':'Channel missingness denominator is core8 in the same year/channel. Mobile retention and share shifts compare mobile-only core8 vs mobile-only selected17 with the same scope.',
        'scope':'A all processing; B normal; C normal excluding 업무운행, 훈련출동, 구급차소독.',
        'geography':'Original district/dong strings; no administrative-dong or coordinate reassignment.',
        'beehive_policy':'All-type accounting only; no added beehive research or proposal.'})
    generated={'channel_column_missing_and_single_relaxation.csv','mobile_composition_shift_summary.csv','mobile_composition_details.csv','validation.json'}
    generated.update(f'{name}.csv' for name in counters)
    generated.update(f'{name}_retention.csv' for name in retentions)
    dump('manifest.json',{'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(__file__),
        'dependency_script':'analysis/00_공통/select_complete_receipts_2020_2024.py',
        'dependency_script_sha256':sha(ROOT/'analysis/00_공통/select_complete_receipts_2020_2024.py'),
        'input_manifest':str((INPUTS/'manifest.json').relative_to(ROOT)),'input_manifest_sha256':sha(INPUTS/'manifest.json'),
        'selected_manifest':str((SELECTED/'manifest.json').relative_to(ROOT)),'selected_manifest_sha256':sha(SELECTED/'manifest.json'),
        'input_files':input_evidence,'unit':'Receipt record; current selected17 and all originals unchanged.',
        'reconciliation':[{'year':x['year'],'source_rows':x['source_rows'],'core8_rows':x['core8_rows'],
            'selected17_rows':x['selected17_rows'],'excluded17_rows':x['excluded17_rows']} for x in checks],
        'outputs':[{'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name in generated]})

if __name__=='__main__': main()
