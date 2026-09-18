"""Filter sensitivity diagnostics; no replacement input, inferential tests or policy ranks."""
from pathlib import Path
import hashlib,json
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[2]
B=R/'data/processed/동대응-전체결측제외-20260915'
O=R/'data/processed/완전행-분석적합성-20260915/stability';O.mkdir(parents=True,exist_ok=True)
METHOD={'recorded_before_result_computation':True,'scope':'core8 and fixed complete17 with identical A/all, B/normal, C/normal excluding operational subtypes; baseline diagnostic only','composition':'Each same year/scope distribution normalized separately; difference = complete17 share - core8 share, percentage points. TVD=0.5*sum(abs(proportion difference)); 0 to 1.','ranks':'Filter diagnostic, not policy prioritization. Top k includes all ties at kth count. Spearman computed as Pearson correlation of average ranks across the full union, zeros included. A constant rank vector yields undefined correlation.','k':[10,20,30],'annual_thresholds':[0,1,5,10,20],'threshold_rule':'Each year must have count>0 and count>=threshold, so 0 and 1 intentionally coincide. These are sensitivity settings, not selection or acceptability cutoffs.','repetition':'Same original district+dong+major+subtype, positive selected records in all five years. No historical administrative alignment.','direction_reversal':'Opposite strict signs of (2024 count - 2020 count) before and after filtering. Zero changes are not reversals. Percent change omitted if start-year count is zero.','beehive':'Retained in full composition reconciliation only. Excluded from ranking, repetition, direction reversal and examples.','spatial_join_confirmed':False,'judgement_thresholds':'No acceptability threshold or weighted score chosen here; root applies separately recorded criteria.'}
(O/'predeclared_methods.json').write_text(json.dumps(METHOD,ensure_ascii=False,indent=2),encoding='utf8')
METHOD['registration_limit']='Methods written before this computation, but source data and earlier summaries were already known; not a blind preregistration. No pass/fail cutoffs inferred from results.'
(O/'predeclared_methods.json').write_text(json.dumps(METHOD,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(d,n):d.to_csv(O/n,index=False,encoding='utf-8-sig')
inputs=[]
def verified(p,m):
 mm=json.loads(m.read_text(encoding='utf8')); rec=next(x for x in mm['outputs'] if Path(x['file']).name==p.name)
 actual=sha(p);assert actual==rec['sha256'];inputs.append({'file':str(p.relative_to(R)),'sha256':actual,'prior_manifest_match':True})
path=B/'completeness/original_region_classification.csv';verified(path,path.parent/'manifest.json')
g=pd.read_csv(path,keep_default_na=False);g=g[g.stage.isin(['core8','provisional17'])].copy();g['stage']=g.stage.replace({'provisional17':'complete17'})
MAJ='EMRG_RSCU_ASSRT_NM';SUB='EMRG_RSCU_CLSF_NM';DIST='CLMTY_SGG_NM';DONG='CLMTY_EMD_NM'
ret=g.groupby(['year','scope','stage'])['count'].sum().unstack('stage').reset_index();ret['retention_pct']=ret.complete17/ret.core8*100;ret['excluded']=ret.core8-ret.complete17
assert ret.complete17.le(ret.core8).all();save(ret,'annual_retention.csv')
assert ret[ret.scope.eq('A')].complete17.sum()==704689
composition=[];tvds=[]
def compare(frame,dimension,keys):
 agg=frame.groupby(['year','scope','stage']+keys,as_index=False)['count'].sum()
 z=agg.pivot(index=['year','scope']+keys,columns='stage',values='count').fillna(0).reset_index()
 for (year,scope),part in z.groupby(['year','scope']):
  n0=part.core8.sum();n1=part.complete17.sum(); assert n1<=n0
  a=part.copy();a['share_core8_pct']=a.core8/n0*100;a['share_complete17_pct']=a.complete17/n1*100;a['share_difference_pp']=a.share_complete17_pct-a.share_core8_pct
  a['cell_retention_pct']=a.complete17/a.core8.where(a.core8.ne(0))*100
  a['category']=a[keys].astype(str).agg(' | '.join,axis=1);a['dimension']=dimension;a['administrative_geography_confirmed']=False
  composition.append(a[['year','scope','dimension','category','core8','complete17','share_core8_pct','share_complete17_pct','share_difference_pp','cell_retention_pct','administrative_geography_confirmed']])
  tvds.append({'year':int(year),'scope':scope,'dimension':dimension,'TVD':float(a.share_difference_pp.abs().sum()/200),'max_abs_share_difference_pp':float(a.share_difference_pp.abs().max()),'categories':len(a),'core8':int(n0),'complete17':int(n1)})
for dimension,keys in [('major_type',[MAJ]),('subtype',[MAJ,SUB]),('district',[DIST]),('original_dong',[DIST,DONG])]:compare(g,dimension,keys)
# Read existing exact core8 and complete17 memberships with identical time parsing.
times=[];dayrows=[]
for year in range(2020,2025):
 for stage,root,name in [('core8',R/'data/processed/컬럼선별-결측제외-20260915',f'complete_dong_{year}.csv.gz'),('complete17',B/'completeness',f'complete_17_{year}.csv.gz')]:
  p=root/name;verified(p,root/'manifest.json')
  d=pd.read_csv(p,dtype=str,keep_default_na=False,usecols=['DCLR_DT',SUB,'PRCS_RSLT_SE_NM'])
  dt=pd.to_datetime(d.DCLR_DT.str.strip(),format='%Y%m%d%H%M%S',errors='raise');assert dt.dt.year.eq(year).all()
  d['month']=dt.dt.month;d['hour']=dt.dt.hour;d['weekday']=dt.dt.dayofweek;d['date']=dt.dt.strftime('%Y-%m-%d')
  normal=d.PRCS_RSLT_SE_NM.eq('정상')
  for scope,mask in [('A',pd.Series(True,index=d.index)),('B',normal),('C',normal&~d[SUB].isin(['업무운행','훈련출동','구급차소독']))]:
   x=d[mask];expected=int(ret.loc[ret.year.eq(year)&ret.scope.eq(scope),stage].iloc[0]);assert len(x)==expected
   dayrows.append({'year':year,'stage':stage,'scope':scope,'observed_dates':x.date.nunique(),'records':len(x)})
   for dim in ['month','hour','weekday']:
    t=x.groupby(dim,as_index=False).size().rename(columns={'size':'count',dim:'time_category'});t['dimension']=dim;t['year']=year;t['scope']=scope;t['stage']=stage;times.append(t)
time=pd.concat(times,ignore_index=True);save(time,'compatible_time_counts.csv');save(pd.DataFrame(dayrows),'observed_date_reconciliation.csv')
for dim in ['month','hour','weekday']:compare(time[time.dimension.eq(dim)],dim,['time_category'])
save(pd.concat(composition,ignore_index=True),'composition_differences_pp.csv');save(pd.DataFrame(tvds),'TVD_summary.csv')
# Exclude bees from all filter-sensitive candidate diagnostics.
e=g[g[SUB].ne('벌집제거')].groupby(['year','scope','stage',DIST,DONG,MAJ,SUB],as_index=False)['count'].sum()
keys=['scope',DIST,DONG,MAJ,SUB]
w=e.pivot(index=keys,columns=['stage','year'],values='count').fillna(0)
for stage in ['core8','complete17']:
 for y in range(2020,2025):
  if (stage,y) not in w:w[(stage,y)]=0
w=w.astype(int);w.columns=[f'{s}_{y}' for s,y in w.columns]
w=w.reset_index();a0=[f'core8_{y}' for y in range(2020,2025)];a1=[f'complete17_{y}' for y in range(2020,2025)]
assert (w[a1].to_numpy()<=w[a0].to_numpy()).all()
w['observed_years_core8']=w[a0].gt(0).sum(axis=1);w['observed_years_complete17']=w[a1].gt(0).sum(axis=1)
w['five_year_before']=w.observed_years_core8.eq(5);w['five_year_after']=w.observed_years_complete17.eq(5);w['lost_five_year_observation']=w.five_year_before&~w.five_year_after
w['change_core8']=w.core8_2024-w.core8_2020;w['change_complete17']=w.complete17_2024-w.complete17_2020
w['direction_reversal']=w.change_core8*w.change_complete17<0
w['pct_change_core8']=w.change_core8/w.core8_2020.where(w.core8_2020.ne(0))*100;w['pct_change_complete17']=w.change_complete17/w.complete17_2020.where(w.complete17_2020.ne(0))*100
w['all_four_endpoints_positive']=w[['core8_2020','core8_2024','complete17_2020','complete17_2024']].gt(0).all(axis=1);w['administrative_geography_confirmed']=False
save(w,'all_original_dong_subtype_sensitivity.csv');save(w[w.direction_reversal],'direction_reversal_details.csv')
substantial=w[w.direction_reversal&w[['core8_2020','core8_2024','complete17_2020','complete17_2024']].ge(20).all(axis=1)].copy()
substantial['example_screen']='all four endpoint counts >=20; illustration screen only, not candidate selection or statistical significance'
save(substantial,'direction_reversal_all_endpoints_at_least20.csv')
reps=[]
for scope,x in w.groupby('scope'):
 for minimum in [0,1,5,10,20]:
  before=x[a0].gt(0).all(axis=1)&x[a0].ge(minimum).all(axis=1);after=x[a1].gt(0).all(axis=1)&x[a1].ge(minimum).all(axis=1)
  assert not (after&~before).any()
  reps.append({'scope':scope,'minimum_per_year':minimum,'before_qualifying_combinations':int(before.sum()),'after_qualifying_combinations':int(after.sum()),'lost':int((before&~after).sum()),'retained_fraction':float(after.sum()/before.sum()) if before.sum() else None})
save(pd.DataFrame(reps),'five_year_repetition_threshold_sensitivity.csv')
rankrows=[]
for entity,fields in [('original_dong',[DIST,DONG]),('original_dong_subtype',[DIST,DONG,MAJ,SUB])]:
 ag=e.groupby(['year','scope','stage']+fields,as_index=False)['count'].sum()
 for (year,scope),x in ag.groupby(['year','scope']):
  x=x.pivot(index=fields,columns='stage',values='count').fillna(0)
  rho=x.core8.rank(method='average').corr(x.complete17.rank(method='average'))
  for k in [10,20,30]:
   c0=x.core8.nlargest(min(k,len(x))).iloc[-1];c1=x.complete17.nlargest(min(k,len(x))).iloc[-1]
   s0=set(x.index[x.core8.ge(c0)]);s1=set(x.index[x.complete17.ge(c1)])
   rankrows.append({'year':int(year),'scope':scope,'entity':entity,'k':k,'before_top_size_with_ties':len(s0),'after_top_size_with_ties':len(s1),'intersection':len(s0&s1),'union':len(s0|s1),'Jaccard':len(s0&s1)/len(s0|s1),'spearman_full_union_average_ties':rho,'full_union_size':len(x),'administrative_geography_confirmed':False})
save(pd.DataFrame(rankrows),'rank_filter_sensitivity.csv')
direction=w.groupby('scope').agg(combinations=('direction_reversal','size'),five_year_before=('five_year_before','sum'),five_year_after=('five_year_after','sum'),lost_five_year=('lost_five_year_observation','sum'),direction_reversals=('direction_reversal','sum')).reset_index()
direction['reversals_all_endpoints_positive']=[int(w[w.scope.eq(s)].eval('direction_reversal & all_four_endpoints_positive').sum()) for s in direction.scope]
direction['reversals_all_endpoints_at_least20']=[int(substantial.scope.eq(s).sum()) for s in direction.scope]
save(direction,'direction_and_repetition_summary.csv')
manifest={'inputs':inputs,'methods':METHOD,'script_sha256':sha(Path(__file__)),'reconciled_complete17_A_total':int(ret[ret.scope.eq('A')].complete17.sum()),'geography_confirmed':False,'output_files':[{'file':p.name,'sha256':sha(p)} for p in sorted(O.glob('*.csv'))]}
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(direction.to_string(index=False));print(pd.DataFrame(tvds).groupby(['scope','dimension']).TVD.agg(['min','max']).to_string())
