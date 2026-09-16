"""Select all ages and district keys from the five supplied MOIS files."""
import csv
import hashlib
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/컬럼선별-결측제외-20260915/population'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prior=json.loads((ROOT/'data/processed/동별예방분석-20260914/population/manifest.json').read_text(encoding='utf-8'))
    rows=[]; evidence=[]; ages=[]
    for year in range(2020,2025):
        path=ROOT/f'data/raw/인구배경/MOIS_{year}12_연령별인구_부산전체읍면동.csv'
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest==next(x['sha256'] for x in prior['inputs'] if x['year']==year)
        raw=list(csv.DictReader(path.open(encoding='cp949',newline='')))
        parsed=[]
        for i,row in enumerate(raw,2):
            name,code=re.fullmatch(r'\s*(.*?)\s*\((\d{10})\)\s*',row['행정구역']).groups()
            parsed.append((i,' '.join(name.split()),code,row))
        names={code:name for _,name,code,_ in parsed}
        population_sum=0; count=0
        for i,name,code,row in parsed:
            if code.endswith('00000'):continue
            parent=code[:5]+'00000'
            metadata={'year':year,'population_reference_date':f'{year}-12-31','district_code':parent,
                      'district_name':names[parent].removeprefix('부산광역시 '),'admin_dong_code':code,
                      'admin_dong_name':name.removeprefix(names[parent]+' '),
                      'source_file':path.relative_to(ROOT).as_posix(),'source_csv_row':i}
            pop=int(row[f'{year}년12월_계_총인구수'].replace(',',''))
            vals=[int(row[f'{year}년12월_계_{age}세'].replace(',','')) for age in range(100)]
            vals.append(int(row[f'{year}년12월_계_100세 이상'].replace(',','')))
            assert sum(vals)==pop
            rows.append({**metadata,'population':pop,**{f'age_{a}':v for a,v in enumerate(vals)}})
            for age,value in enumerate(vals):
                ages.append({**metadata,'age':age,'age_label':f'{age}세' if age<100 else '100세 이상',
                             'age_population':value,'age_share_pct':100*value/pop})
            population_sum+=pop;count+=1
        assert count==205 and population_sum==int(raw[0][f'{year}년12월_계_총인구수'].replace(',',''))
        evidence.append({'year':year,'file':path.relative_to(ROOT).as_posix(),'sha256':digest,
                         'prior_full_audit_reusable':True,'input_rows':len(raw),'dong_rows':count,
                         'hierarchy_summary_rows_separated':17,'missing_rows_removed':0,'population_sum':population_sum})
    pd.DataFrame(rows).to_csv(OUT/'complete_population_dong.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(ages).to_csv(OUT/'complete_population_age_long.csv',index=False,encoding='utf-8-sig')
    for path in OUT.glob('*.csv'):
        check=pd.read_csv(path,dtype=str,keep_default_na=False)
        assert not check.eq('').any().any()
    (OUT/'manifest.json').write_text(json.dumps({'sources':evidence,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'age_policy':'age_0 through age_99 and age_100=open-ended 100+. All ages retained; counts and shares in separate long table.',
        'selection':'Region split into year/date/district/dong keys; total and 101 age columns retained. Male/female and duplicate age-total columns omitted after prior full reconciliation; city/district aggregates separated.',
        'join_policy':'MOIS administrative codes retained. No raw receipt-name join; no inferred patient ages or receipt rates.',
        'outputs':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.glob('*.csv')]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'dong_year_rows':len(rows),'age_rows':len(ages),'missing_rows_removed':0},ensure_ascii=False))

if __name__=='__main__':main()
