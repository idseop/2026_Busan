"""Audit all recorded names against official dated relations; never allocate counts."""
from pathlib import Path
import hashlib,json,zipfile,io,re
import pandas as pd
import openpyxl
R=Path(__file__).resolve().parents[2]
I=R/'data/interim/동연결검토-20260915'
O=R/'data/processed/동대응-전체결측제외-20260915/linkage';O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d,n):d.to_csv(O/n,index=False,encoding='utf-8-sig')
def readzip(path,prefix):
 z=zipfile.ZipFile(path,metadata_encoding='cp949');assert z.testzip() is None
 n=next(n for n in z.namelist() if n.split('/')[-1].lower().startswith(prefix.lower()+'.') and n.endswith('.xlsx'))
 it=iter(openpyxl.load_workbook(io.BytesIO(z.read(n)),read_only=True,data_only=True).active.values);h=next(it)
 d=pd.DataFrame(it,columns=h).fillna('').astype(str)
 return d[d['시도명'].eq('부산광역시')].copy()
def active(d,day):return d[d['생성일자'].le(day)&(d['말소일자'].eq('')|d['말소일자'].gt(day))]
mix=readzip(I/'jscode20250101-retired.zip','KIKmix');mix=mix[mix['읍면동명'].ne('')].copy()
h=readzip(I/'jscode20250101-retired.zip','KIKcd_H');h=h[h['읍면동명'].ne('')].copy()
save(mix,'official_busan_relations_with_dates.csv');save(h,'official_administrative_codes_with_dates.csv')
files=list(I.glob('jscode*.zip'))+list((R/'data/interim/동연결검토-20260914').glob('jscode*-including-retired.zip'))
checks=[];discrepancies=[]
for path in sorted(files):
 stamp=re.search(r'20\d{6}',path.name).group()
 old=readzip(path,'KIKmix');old=old[old['읍면동명'].ne('')]
 cols=['행정동코드','시군구명','읍면동명','법정동코드','동리명']
 a=set(active(old,stamp)[cols].itertuples(index=False,name=None));b=set(active(mix,stamp)[cols].itertuples(index=False,name=None))
 for kind,diff in [('snapshot_only',a-b),('later_reconstruction_only',b-a)]:
  for row in sorted(diff):discrepancies.append({'snapshot_date':stamp,'difference':kind,**dict(zip(cols,row))})
 checks.append({'file':str(path.relative_to(R)),'sha256':sha(path),'snapshot_date':stamp,'snapshot_active_relations':len(a),'reconstructed_active_relations':len(b),'missing_from_reconstruction':len(a-b),'extra_in_reconstruction':len(b-a),'exact_match':a==b})
save(pd.DataFrame(checks),'snapshot_reconstruction_checks.csv')
save(pd.DataFrame(discrepancies),'retrospective_record_discrepancies.csv')
population_path=R/'data/processed/동별예방분석-20260914/population/region_registry.csv'
coverage_path=R/'data/processed/컬럼선별-결측제외-20260915/coverage/all_original_region_names_before_filter.csv'
source_checks=[]
for path,manifest_path in [(population_path,population_path.parent/'manifest.json'),(coverage_path,coverage_path.parent/'manifest.json')]:
 previous=json.loads(manifest_path.read_text(encoding='utf8'))
 entry=next(x for x in previous['outputs'] if Path(x['file']).name==path.name)
 assert sha(path)==entry['sha256']
 source_checks.append({'file':str(path.relative_to(R)),'sha256':sha(path),'prior_hash_match':True})
pop=pd.read_csv(population_path,keep_default_na=False,dtype={'admin_code':str,'district_code':str})
pop=pop[pop.level.eq('dong')]
popchecks=[]
for year,p in pop.groupby('year'):
 day=f'{year}1231';hh=active(h,day)
 a=set(hh['행정동코드']);b=set(p.admin_code)
 popchecks.append({'year':int(year),'official_active_codes':len(a),'population_codes':len(b),'missing_codes':len(b-a),'extra_codes':len(a-b),'exact_code_set_match':a==b})
assert all(x['exact_code_set_match'] for x in popchecks)
save(pd.DataFrame(popchecks),'year_end_population_code_checks.csv')
raw=pd.read_csv(coverage_path,keep_default_na=False)
records=[];evidence=[]
for r in raw.itertuples(index=False):
 year=int(r.year);lo=f'{year}0101';hi=f'{year+1}0101'
 mm=mix[mix['생성일자'].lt(hi)&(mix['말소일자'].eq('')|mix['말소일자'].gt(lo))&mix['시군구명'].eq(r.district_name)]
 hh=h[h['생성일자'].lt(hi)&(h['말소일자'].eq('')|h['말소일자'].gt(lo))&h['시군구명'].eq(r.district_name)]
 legal=mm[mm['동리명'].eq(r.dong_name)]
 alias=set(pop.loc[pop.year.eq(year)&pop.district_name.eq(r.district_name)&pop.dong_name.eq(r.dong_name),'admin_code'])
 admin=hh[hh['읍면동명'].eq(r.dong_name)|hh['행정동코드'].isin(alias)]
 lc=set(legal['행정동코드']);ac=set(admin['행정동코드']);union=lc|ac
 if not r.district_name or not r.dong_name:status='missing_region'
 elif not union:status='unregistered_name_in_year'
 elif len(union)>1:status='multiple_or_conflicting_codes'
 elif lc and ac:status='both_hypotheses_same_unique_code'
 elif lc:status='legal_hypothesis_unique_only'
 else:status='administrative_hypothesis_unique_only'
 periods=[]
 for hypothesis,df in [('legal',legal),('administrative',admin)]:
  for _,row in df.iterrows():
   start=max(lo,row['생성일자']);end=min(hi,row['말소일자'] or hi)
   periods.append((start,end))
   evidence.append({'year':year,'district_name':r.district_name,'raw_dong_name':r.dong_name,'hypothesis':hypothesis,'admin_code':row['행정동코드'],'official_admin_name':row['읍면동명'],'legal_code':row.get('법정동코드',''),'legal_name':row.get('동리명',''),'record_created':row['생성일자'],'record_retired':row['말소일자'],'valid_from_in_year':start,'valid_until_exclusive_in_year':end})
 cursor=lo
 for start,end in sorted(periods):
  if start<=cursor:cursor=max(cursor,end)
 whole=cursor>=hi
 code=next(iter(union)) if len(union)==1 else ''
 pr=pop[pop.year.eq(year)&pop.admin_code.eq(code)]
 conflict=any(x['시군구명']==r.district_name and (x['동리명']==r.dong_name or x['읍면동명']==r.dong_name) and int(x['snapshot_date'][:4])<=year<=2021 for x in discrepancies)
 eligible=bool(code and whole and len(pr)==1 and not conflict)
 records.append({'year':year,'district_name':r.district_name,'raw_dong_name':r.dong_name,'receipt_count_before_filter':r.receipt_count,'status':status,'legal_codes':'|'.join(sorted(lc)),'administrative_codes':'|'.join(sorted(ac)),'candidate_codes':'|'.join(sorted(union)),'candidate_count':len(union),'record_interval_covers_full_year':whole,'temporal_reconstruction_conflict':conflict,'unique_code':code,'year_end_population_code_exists':len(pr)==1,'code_level_population_join_eligible':eligible,'receipt_geography_confirmed':False,'raw_field_semantics_confirmed':False,'population_name':pr.iloc[0].dong_name if len(pr)==1 else '', 'population':pr.iloc[0].population if eligible else None})
d=pd.DataFrame(records);ev=pd.DataFrame(evidence).drop_duplicates()
save(d,'all_raw_names_year_crosswalk.csv');save(ev,'all_candidate_relation_intervals.csv')
save(d[d.code_level_population_join_eligible],'unique_code_population_background.csv')
save(d[~d.code_level_population_join_eligible],'held_names.csv')
summary=d.groupby(['year','status'],as_index=False).agg(raw_name_combinations=('status','size'),receipt_records=('receipt_count_before_filter','sum'))
save(summary,'status_summary.csv')
assert len(d)==len(raw) and d.receipt_count_before_filter.sum()==raw.receipt_count.sum()
manifest={'inputs':checks,'aggregate_inputs':source_checks,'year_end_population_code_checks':popchecks,'scope':'All five years of Busan-labelled pre-filter raw district/dong combinations, including missing names','reconstruction_rule':'creation inclusive; retirement exclusive; 2025-01-01 retired-inclusive official records crosschecked against independent historical snapshots; discrepancy retained. Does not reconstruct polygon boundaries or certify dates as geometric relation effective dates.','receipt_linkage_policy':'Code-level unique eligibility is not an approval of raw-field semantics or individual location. No receipt counts allocated to administrative dongs. Population shown only as candidate-code background.','rows':len(d),'code_level_eligible':int(d.code_level_population_join_eligible.sum()),'outputs':[{'file':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.csv'))]}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(summary.to_string(index=False));print('code-level eligible',d.groupby('year').code_level_population_join_eligible.sum().to_dict());print('snapshots',checks)
