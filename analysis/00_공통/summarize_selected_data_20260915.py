"""Compare complete-case populations using only the current selected-data run."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/processed/컬럼선별-결측제외-20260915'
OUT=BASE/'summary'
TYPE='EMRG_RSCU_ASSRT_NM'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=BASE/'annual_classification.csv'
    data=pd.read_csv(source,keep_default_na=False)
    totals=data.groupby(['year','cohort','scope'],as_index=False)['count'].sum()
    before=totals[totals.cohort.eq('before')].drop(columns='cohort').rename(columns={'count':'before_count'})
    totals=totals.merge(before,on=['year','scope'],validate='many_to_one')
    totals['removed_count']=totals.before_count-totals['count']
    totals['retention_pct']=100*totals['count']/totals.before_count
    totals.to_csv(OUT/'annual_completeness.csv',index=False,encoding='utf-8-sig')
    domain=pd.MultiIndex.from_product([sorted(data.cohort.unique()),sorted(data.scope.unique()),sorted(data[TYPE].unique())],names=['cohort','scope',TYPE])
    # Zero is valid here: counts in explicit filtered subsets of the same observed records.
    types=data.groupby(['cohort','scope',TYPE])['count'].sum().reindex(domain,fill_value=0).reset_index()
    types['denominator']=types.groupby(['cohort','scope'])['count'].transform('sum')
    types['share_pct']=100*types['count']/types.denominator
    b=types[types.cohort.eq('before')].drop(columns='cohort').rename(columns={'count':'before_count','share_pct':'before_share_pct'})
    types=types.merge(b[['scope',TYPE,'before_count','before_share_pct']],on=['scope',TYPE],validate='many_to_one')
    types['retention_pct']=100*types['count']/types.before_count
    types['share_change_pp']=types.share_pct-types.before_share_pct
    types.to_csv(OUT/'major_type_change.csv',index=False,encoding='utf-8-sig')
    major_year=data.groupby(['year','cohort','scope',TYPE],as_index=False)['count'].sum()
    major_year.to_csv(OUT/'major_type_by_year.csv',index=False,encoding='utf-8-sig')
    sources=[{'file':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}]
    for dim in ['month','weekday','hour','season']:
        path=BASE/f'time_{dim}.csv'
        f=pd.read_csv(path,keep_default_na=False)
        # Calendar days are unique by year/dimension, not additive across types.
        g=f.groupby(['year','cohort','scope',dim],as_index=False).agg(count=('count','sum'),calendar_days=('calendar_days','first'))
        assert f.groupby(['year',dim]).calendar_days.nunique().eq(1).all()
        g['receipts_per_calendar_day']=g['count']/g.calendar_days
        g.to_csv(OUT/f'city_{dim}.csv',index=False,encoding='utf-8-sig')
        sources.append({'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (OUT/'manifest.json').write_text(json.dumps({'sources':sources,
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'interpretation':'Complete-case comparison, not validated administrative-dong inference. Omitted classification rows may be concentrated in originally unclassified records.',
        'policy':'No policy candidates generated. User-excluded subtype retained only in total reconciliation.',
        'outputs':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.glob('*.csv')]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(totals.to_string(index=False))

if __name__=='__main__':main()
