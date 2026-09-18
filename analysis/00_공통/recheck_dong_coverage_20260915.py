"""Compare recorded place names, not administrative coverage or population linkage."""
from pathlib import Path
import hashlib,json,zipfile,io
import pandas as pd
import openpyxl
R=Path(__file__).resolve().parents[2]
OLD=R/'data/processed/동별예방분석-20260914'
O=R/'data/processed/컬럼선별-결측제외-20260915/coverage'
O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for folder,filename in [('receipts','original_dong_types.csv'),('population','region_registry.csv')]:
    m=json.loads((OLD/folder/'manifest.json').read_text(encoding='utf8'))
    rec=next(x for x in m['outputs'] if Path(x['file']).name==filename)
    p=OLD/folder/filename
    actual=sha(p)
    assert actual==rec['sha256'],(filename,actual,rec['sha256'])
    checks.append({'file':str(p.relative_to(R)),'sha256':actual,'prior_manifest_match':True})
r=pd.read_csv(OLD/'receipts/original_dong_types.csv',keep_default_na=False)
r=r[r.scope=='A'].groupby(['year','CLMTY_SGG_NM','CLMTY_EMD_NM'],dropna=False,as_index=False)['count'].sum()
r=r.rename(columns={'CLMTY_SGG_NM':'district_name','CLMTY_EMD_NM':'dong_name','count':'receipt_count'})
r['district_missing']=r.district_name.eq('');r['dong_missing']=r.dong_name.eq('')
p=pd.read_csv(OLD/'population/region_registry.csv',keep_default_na=False,dtype={'admin_code':str,'district_code':str})
p=p[p.level.eq('dong')].copy()
assert len(p)==1025 and p.groupby('year').size().eq(205).all()
keys=['year','district_name','dong_name']
assert not p.duplicated(keys).any()
c=p.merge(r,on=keys,how='outer',indicator=True)
c['name_comparison']=c['_merge'].map({'both':'direct_name_match_only','left_only':'population_name_only','right_only':'receipt_name_only'}).astype(str)
c.loc[c.dong_missing.eq(True)|c.district_missing.eq(True),'name_comparison']='receipt_region_missing'
c=c.drop(columns='_merge')
c['administrative_link_confirmed']=False
def save(df,name):df.to_csv(O/name,index=False,encoding='utf-8-sig')
save(r,'all_original_region_names_before_filter.csv');save(p,'all_population_205_per_year.csv');save(c,'all_name_comparison_2020_2024.csv')
for label in c.name_comparison.unique():save(c[c.name_comparison.eq(label)],label+'.csv')
summary=[]
for year in range(2020,2025):
    cy=c[c.year.eq(year)];ry=r[r.year.eq(year)]
    summary.append({'year':year,'population_dongs':205,'original_region_combinations':len(ry),'nonmissing_original_region_combinations':int((~ry.district_missing & ~ry.dong_missing).sum()),'direct_name_matches':int(cy.name_comparison.eq('direct_name_match_only').sum()),'population_names_without_direct_match':int(cy.name_comparison.eq('population_name_only').sum()),'receipt_names_without_direct_match':int(cy.name_comparison.eq('receipt_name_only').sum()),'missing_region_combinations':int(cy.name_comparison.eq('receipt_region_missing').sum()),'busan_labelled_receipts':int(ry.receipt_count.sum()),'receipts_missing_dong':int(ry.loc[ry.dong_missing,'receipt_count'].sum())})
save(pd.DataFrame(summary),'year_coverage_summary.csv')
examples=[]
for stamp in ['20201201','20210705']:
    zp=R/f'data/interim/동연결검토-20260914/jscode{stamp}-including-retired.zip'
    z=zipfile.ZipFile(zp,metadata_encoding='cp949')
    name=next(n for n in z.namelist() if 'KIKmix' in n and n.endswith('.xlsx'))
    vals=list(openpyxl.load_workbook(io.BytesIO(z.read(name)),read_only=True,data_only=True).active.values)
    mix=pd.DataFrame(vals[1:],columns=vals[0])
    mix=mix[mix['시도명'].eq('부산광역시') & mix['읍면동명'].notna() & mix['말소일자'].isna()].copy()
    mix['snapshot_date']=stamp
    save(mix,f'official_active_busan_legal_administrative_relations_{stamp}.csv')
    grouped=mix.groupby(['시군구명','동리명'])['읍면동명'].agg(lambda s:'|'.join(sorted(set(s)))).reset_index()
    grouped['administrative_name_count']=grouped['읍면동명'].str.count(r'\|')+1
    grouped['snapshot_date']=stamp
    save(grouped,f'official_legal_name_relation_counts_{stamp}.csv')
    examples.extend(grouped[grouped['동리명'].isin(['연산동','우동','좌동','부전동'])].to_dict('records'))
    checks.append({'file':str(zp.relative_to(R)),'sha256':sha(zp),'zip_crc_pass':z.testzip() is None})
manifest={'scope':'A: CLMTY_CTPV_NM == 부산광역시; all processing results; before new complete-case filtering','inputs':checks,'summary':summary,'official_examples':examples,'interpretation':'Name presence only. Missing direct name match does not establish an unobserved administrative dong. Direct name match does not establish linkage. No geographic assignment.','outputs':[{'file':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.csv'))]}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'summary':summary,'examples':examples},ensure_ascii=False,indent=2))
