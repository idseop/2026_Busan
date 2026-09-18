"""Descriptive results for fixed complete-17 records; no policy ranking or allocation."""
from pathlib import Path
import hashlib,json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];B=R/'data/processed/동대응-전체결측제외-20260915'
O=B/'analysis';O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d,n):d.to_csv(O/n,index=False,encoding='utf-8-sig')
inputs=[]
def verified(path,manifest):
 m=json.loads(manifest.read_text(encoding='utf8'));e=next(e for e in m['outputs'] if Path(e['file']).name==path.name)
 digest=sha(path);assert digest==e['sha256'];inputs.append({'file':str(path.relative_to(R)),'sha256':digest,'manifest_match':True})
tables={k:[] for k in ['annual_type','month_type','weekday_type','hour_band_type','original_region_type','original_region_total','observed_day_denominators']}
counts=[]
major='EMRG_RSCU_ASSRT_NM';sub='EMRG_RSCU_CLSF_NM';district='CLMTY_SGG_NM';dong='CLMTY_EMD_NM'
for year in range(2020,2025):
 path=B/f'completeness/complete_17_{year}.csv.gz';verified(path,path.parent/'manifest.json')
 d=pd.read_csv(path,keep_default_na=False,dtype=str,usecols=['DCLR_DT',district,dong,major,sub,'PRCS_RSLT_SE_NM'])
 dt=pd.to_datetime(d.DCLR_DT.str.strip(),format='%Y%m%d%H%M%S',errors='raise')
 assert dt.dt.year.eq(year).all();d['date']=dt.dt.strftime('%Y-%m-%d');d['month']=dt.dt.month;d['weekday']=dt.dt.dayofweek
 d['hour_band']=(dt.dt.hour//4*4).map(lambda h:f'{h:02d}-{h+3:02d}')
 masks={'A':pd.Series(True,index=d.index),'B':d.PRCS_RSLT_SE_NM.eq('정상'),'C':d.PRCS_RSLT_SE_NM.eq('정상')&~d[sub].isin(['업무운행','훈련출동','구급차소독'])}
 for scope,mask in masks.items():
  x=d[mask].copy();n=len(x);counts.append({'year':year,'scope':scope,'records':n,'observed_dates':x.date.nunique()})
  for name,keys,timecol in [('annual_type',[major,sub],None),('month_type',['month',major,sub],'month'),('weekday_type',['weekday',major,sub],'weekday'),('hour_band_type',['hour_band',major,sub],'hour_band'),('original_region_type',[district,dong,major,sub],None),('original_region_total',[district,dong],None)]:
   t=x.groupby(keys,as_index=False,dropna=False).size().rename(columns={'size':'receipt_count'})
   assert t.receipt_count.sum()==n
   t.insert(0,'scope',scope);t.insert(0,'year',year)
   if timecol:
    denom=x.groupby(timecol).date.nunique().to_dict() if timecol!='hour_band' else {v:x.date.nunique() for v in x.hour_band.unique()}
    t['observed_days_denominator']=t[timecol].map(denom)
    t['receipts_per_observed_day']=t.receipt_count/t.observed_days_denominator
    for value,days in denom.items():tables['observed_day_denominators'].append(pd.DataFrame([{'year':year,'scope':scope,'dimension':timecol,'value':value,'observed_days':days}]))
   tables[name].append(t)
tabs={name:pd.concat(parts,ignore_index=True) for name,parts in tables.items()}
for name,t in tabs.items():save(t,name+'.csv')
save(pd.DataFrame(counts),'annual_scope_counts.csv')
reg=tabs['original_region_type'];eligible=reg[reg[sub].ne('벌집제거')]
keys=['scope',district,dong,major,sub]
wide=eligible.pivot(index=keys,columns='year',values='receipt_count').fillna(0).astype(int).reindex(columns=range(2020,2025),fill_value=0)
wide['observed_year_count']=wide.gt(0).sum(axis=1)
wide['change_2024_minus_2020']=wide[2024]-wide[2020]
wide['change_2024_vs_2020_pct']=((wide[2024]-wide[2020])/wide[2020].where(wide[2020].ne(0))*100).round(4)
wide['administrative_geography_confirmed']=False
wide=wide.reset_index();save(wide,'original_region_type_repetition_excluding_beehive.csv')
cross=B/'linkage/all_raw_names_year_crosswalk.csv';verified(cross,cross.parent/'manifest.json')
cw=pd.read_csv(cross,keep_default_na=False,dtype={'unique_code':str});cw=cw[cw.code_level_population_join_eligible.eq(True)].copy()
tot=tabs['original_region_total'].pivot(index=['year',district,dong],columns='scope',values='receipt_count').fillna(0).reset_index().rename(columns={district:'district_name',dong:'raw_dong_name','A':'receipts_A','B':'receipts_B','C':'receipts_C'})
joined=cw.merge(tot,on=['year','district_name','raw_dong_name'],how='inner',validate='one_to_one')
agepath=R/'data/processed/동별예방분석-20260914/population/dong_single_age.csv';verified(agepath,agepath.parent/'manifest.json')
ages=pd.read_csv(agepath,keep_default_na=False,dtype={'admin_code':str})
assert ages.groupby(['year','admin_code']).size().eq(101).all()
aw=ages.pivot(index=['year','admin_code'],columns='age',values=['age_population','share_pct'])
aw.columns=[f'{metric}_{age}' for metric,age in aw.columns];aw=aw.reset_index()
joined=joined.merge(aw,left_on=['year','unique_code'],right_on=['year','admin_code'],how='left',validate='many_to_one')
population_meta=ages[['year','admin_code','population_reference_date','district_code','source_file','source_row']].drop_duplicates().rename(columns={'source_file':'population_source_file','source_row':'population_source_row'})
joined=joined.merge(population_meta,on=['year','admin_code'],how='left',validate='many_to_one')
assert not joined['age_population_0'].isna().any()
assert joined[[f'age_population_{a}' for a in range(101)]].sum(axis=1).eq(pd.to_numeric(joined.population)).all()
joined['interpretation']='conditional source-name background; not administrative-dong total or age-specific receipts'
save(joined,'conditional_raw_name_population_all_101_ages.csv')
summary={'annual_scope_counts':counts,'input_rows_total':sum(x['records'] for x in counts if x['scope']=='A'),'repetition_rows_excluding_beehive':len(wide),'conditional_background_rows':len(joined),'conditional_by_year':joined.groupby('year').agg(raw_names=('unique_code','size'),unique_candidate_codes=('unique_code','nunique'),receipts_A=('receipts_A','sum'),receipts_B=('receipts_B','sum'),receipts_C=('receipts_C','sum')).reset_index().to_dict('records')}
assert summary['input_rows_total']==704689
stagepath=B/'completeness/stage_completeness.csv';verified(stagepath,stagepath.parent/'manifest.json')
stage=pd.read_csv(stagepath);stage=stage[stage.basis_or_scope.eq('busan_explicit')&stage.stage.isin(['core8','provisional17'])]
chart=stage.pivot(index='year',columns='stage',values='complete_rows').sort_index()
plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(10,5));ix=list(range(5));width=.36
ax.bar([v-width/2 for v in ix],chart.core8,width,label='핵심 8개 완전기록',color='#91a4b8')
bars=ax.bar([v+width/2 for v in ix],chart.provisional17,width,label='최종 17개 완전기록',color='#167d8d')
for bar,year in zip(bars,chart.index):
 value=int(chart.loc[year,'provisional17']);pct=value/chart.loc[year,'core8']*100
 ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+4500,f'{value:,}\n({pct:.1f}%)',ha='center',va='bottom',fontsize=9)
ax.set_xticks(ix,chart.index);ax.set_ylabel('신고접수 기록 수');ax.set_ylim(0,330000)
ax.set_title('분석 조건에 따른 기록 수 변화 · 2020~2024');ax.legend(loc='upper left')
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
fig.text(.1,.01,'괄호: 핵심 8개 완전기록 대비 잔존비율. 실제 사건 감소나 지역 위험 감소를 뜻하지 않음.',fontsize=9)
fig.tight_layout(rect=(0,.04,1,1));fig.savefig(O/'core8_vs_complete17.png',dpi=160);fig.savefig(O/'core8_vs_complete17.svg');plt.close(fig)
manifest={'inputs':inputs,'summary':summary,'scopes':{'A':'all fixed complete17 records','B':'A and processing normal','C':'B excluding subtypes 업무운행 훈련출동 구급차소독'},'unit':'receipt record; no incident deduplication','geography':'Original district/dong names; no confirmed administrative allocation. Conditional code background is not whole administrative-dong counts.','beehive_policy':'벌집제거 retained only in full reconciled aggregate CSVs, excluded from repetition candidate summary and further thematic analysis. Background table has whole-category totals only.','observed_day_denominator':'Dates with any retained receipt in the same year/scope/month or weekday; hour bands divide by all observed dates in the same year/scope. It is not days where a particular subtype occurred. Filtering may remove dates; these are observed-record dates, not proof of perfect calendar coverage.','repetition_zero_rule':'Within fixed five-year input domain, missing raw-name/type cells shown as zero selected records, not zero real incidents or zero administrative-dong demand.','age':'0..99 and 100=100+; resident year-end counts and percentage; not ages of receipt subjects; age denominators are not receipt rate denominators.','script_sha256':sha(Path(__file__)),'outputs':[{'file':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.csv'))]}
manifest['timestamp_handling']='Leading/trailing whitespace stripped for parsing only, original DCLR_DT preserved in input; no dropped or repaired invalid dates.'
manifest['outputs']=[{'file':p.name,'sha256':sha(p)} for p in sorted(O.iterdir()) if p.suffix in ['.csv','.png','.svg']]
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
