"""Independent aggregate, case-selection and official-service verification."""
from pathlib import Path
from collections import Counter
import json,hashlib
import pandas as pd
R=Path(__file__).resolve().parents[2];O=R/'data/processed/심층분석-20260915';W=R/'web/final/data'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(name,condition,detail=None):
 checks.append({'name':name,'passed':bool(condition),'detail':detail})
 assert condition,name
m=json.loads((O/'manifest.json').read_text(encoding='utf-8'));frozen=sha(O/'manifest.json')
for e in m['outputs']:check('output_hash:'+e['path'],sha(R/e['path'])==e['sha256'])
check('builder_hash',sha(R/m['script'])==m['script_sha256'])
check('upstream_dashboard_hash',sha(R/m['previous_final_dashboard'])==m['previous_final_dashboard_sha256'])
for e in m['input_files']:check('selected17_hash:'+str(e['year']),sha(R/e['path'])==e['sha256'])
D=json.loads((R/m['previous_final_dashboard']).read_text(encoding='utf-8'))
txt=(O/'deep-data.json').read_text(encoding='utf-8'); X=json.loads(txt)
check('json_js_identity',(W/'deep-data.js').read_text(encoding='utf-8')=='window.BUSAN_DEEP='+txt+';\n' and (W/'deep-data.json').read_text(encoding='utf-8')==txt)
frames={}
for key,cols,file in [('dayHour','dayHourColumns','regional_weekday_hour.csv'),('month','monthColumns','regional_month.csv'),('caseTime','caseTimeColumns','case_weekday_hour.csv'),('caseMonth','caseMonthColumns','case_month.csv')]:
 f=pd.DataFrame(X[key],columns=X['meta'][cols]); source=pd.read_csv(O/file)
 check('published_source_rows_'+key,f.equals(source))
 check('unique_sparse_keys_'+key,not f.duplicated(subset=list(f.columns[:-1])).any() and f['count'].gt(0).all())
 frames[key]=f
regions={r['index']:(r['district'],r['rawDong']) for r in X['regions']};scopes=X['meta']['scopes'];types=X['meta']['types']
expected={ (r['year'],scopes.index(r['scope']),r['district'],r['rawDong'],types.index(t)):n for r in D['rawRegions'] for t,n in r['typeCounts'].items() }
for key in ['dayHour','month']:
 actual=Counter()
 for row in frames[key].itertuples(index=False):actual[(row.year,row.scopeIndex,*regions[row.regionIndex],row.typeIndex)]+=row.count
 check('all_region_year_scope_type_totals_'+key,all(actual[k]==v for k,v in expected.items()) and not(set(actual)-set(expected)))
 check('all_year_scope_type_totals_'+key,all(sum(v for (y,s,d,n,t),v in actual.items() if (y,s,t)==(r['year'],scopes.index(r['scope']),types.index(r['type'])))==r['count'] for r in D['yearly']))
for key,dim,field in [('dayHour','weekday','weekday'),('dayHour','hourBand','hourBandIndex'),('month','month','month')]:
 actual=frames[key].groupby(['year','scopeIndex','typeIndex',field])['count'].sum().to_dict()
 expectedtime={(r['year'],scopes.index(r['scope']),types.index(r['type']),X['meta']['hourBands'].index(r['value']) if dim=='hourBand' else r['value']):r['count'] for r in D['time'] if r['dimension']==dim}
 check('all_existing_time_marginals_'+dim,actual==expectedtime)
check('42_and_12_bin_domains',frames['dayHour'].weekday.between(0,6).all() and frames['dayHour'].hourBandIndex.between(0,5).all() and frames['month'].month.between(1,12).all())
candidates={(r['district'],r['rawDong'],r['type'],r['subtype']):r for r in D['candidates']}
links={(r['year'],r['district'],r['rawDong']):r for r in D['rawRegions'] if r['scope']=='C'}
def eligible(c):return all(links[(y,c['district'],c['rawDong'])]['codeLevelEligible'] for y in range(2020,2025))
case_notes=[]
for c in X['cases']:
 key=(c['district'],c['rawDong'],c['type'],c['subtype']);base=candidates[key]
 check('case_candidate_values_'+c['rawDong'],all(c[k]==base[k] for k in ['yearCounts','core8YearCounts','minAnnualCount','retention','directionReversal']))
 check('case_retention_denominator_'+c['rawDong'],abs(c['retention']-sum(c['yearCounts'])/sum(c['core8YearCounts']))<1e-12)
 f=frames['caseTime'].loc[frames['caseTime'].caseIndex.eq(c['index'])];q=frames['caseMonth'].loc[frames['caseMonth'].caseIndex.eq(c['index'])]
 check('case_month_heatmap_totals_'+c['rawDong'],f.groupby(['year','scopeIndex'])['count'].sum().to_dict()==q.groupby(['year','scopeIndex'])['count'].sum().to_dict())
 check('case_C_year_totals_'+c['rawDong'],[int(f.loc[f.year.eq(y)&f.scopeIndex.eq(2),'count'].sum()) for y in range(2020,2025)]==c['yearCounts'])
 cc=f.loc[f.scopeIndex.eq(2)]
 check('case_weekday_hour_summaries_'+c['rawDong'],c['weekdayCounts']==[int(cc.loc[cc.weekday.eq(w),'count'].sum()) for w in range(7)] and c['hourBandCounts']==[int(cc.loc[cc.hourBandIndex.eq(h),'count'].sum()) for h in range(6)])
 check('case_population_link_flags_'+c['rawDong'],all(p['codeLevelEligible']==links[(p['year'],c['district'],c['rawDong'])]['codeLevelEligible'] and p['uniqueCode']==links[(p['year'],c['district'],c['rawDong'])]['uniqueCode'] and p['geographyConfirmed'] is False for p in c['populationLinks']))
 case_notes.append({'rawDong':c['rawDong'],'type':c['type'],'subtype':c['subtype'],'selected17_C':sum(c['yearCounts']),'core8_C':sum(c['core8YearCounts']),'all_five_year_code_eligible':eligible(c)})
check('four_case_definition_no_beehive',len(X['cases'])==4 and all(c['subtype']!='벌집제거' for c in X['cases']))
yeon=next(c for c in X['cases'] if c['rawDong']=='연산동')
pool=[c for c in D['candidates'] if c['type']=='구급' and c['subtype']=='질병']
check('yeonsan_largest_repeated_disease',sum(yeon['yearCounts'])==max(sum(c['yearCounts']) for c in pool) and not eligible(yeon),{'comparison_combinations':len(pool)})
geum=next(c for c in X['cases'] if c['rawDong']=='금곡동')
pool=[c for c in D['candidates'] if c['type']=='구조' and c['subtype']=='시건개방' and (c['district'],c['rawDong'])!=('기장군','기장읍') and eligible(c)]
check('geumgok_largest_eligible_lock_opening_excluding_gijang',sum(geum['yearCounts'])==max(sum(c['yearCounts']) for c in pool),{'comparison_combinations':len(pool)})
check('paired_gijang_jeonggwan_eligible',all(eligible(c) and c['district']=='기장군' and c['type']=='구급' and c['subtype']=='질병' for c in X['cases'] if c['rawDong'] in ['기장읍','정관읍']))
e=m['case_sensitivity_input'];check('case_sensitivity_input_hash',sha(R/e['path'])==e['sha256']);original=pd.read_csv(R/e['path'],keep_default_na=False)
for c in X['cases']:
 subset=original.loc[original.CLMTY_SGG_NM.eq(c['district'])&original.CLMTY_EMD_NM.eq(c['rawDong'])&original.EMRG_RSCU_ASSRT_NM.eq(c['type'])&original.EMRG_RSCU_CLSF_NM.eq(c['subtype'])]
 for scope in ['A','B','C']:
  s=c['countsByScope'][scope]; before=[int(subset.loc[subset.year.eq(y)&subset.scope.eq(scope)&subset.stage.eq('core8'),'count'].sum()) for y in range(2020,2025)];after=[int(subset.loc[subset.year.eq(y)&subset.scope.eq(scope)&subset.stage.eq('provisional17'),'count'].sum()) for y in range(2020,2025)]
  check('case_condition_source_'+c['rawDong']+'_'+scope,s['yearCounts']==after and s['core8YearCounts']==before and s['selected17Total']==sum(after) and s['core8Total']==sum(before) and abs(s['retention']-sum(after)/sum(before))<1e-12 and s['selected17Change2024Minus2020']==after[-1]-after[0] and s['core8Change2024Minus2020']==before[-1]-before[0] and s['directionReversal']==((after[-1]-after[0])*(before[-1]-before[0])<0))
 for b in c['timebinSensitivity']:
  f=frames['caseTime'].loc[frames['caseTime'].caseIndex.eq(c['index'])&frames['caseTime'].scopeIndex.eq(scopes.index(b['scope']))];width=b['widthHours']; bins=[int(f.loc[((f.hourBandIndex*4)//width).eq(k),'count'].sum()) for k in range(24//width)]
  check('case_bin_'+c['rawDong']+'_'+b['scope']+'_'+str(width),b['counts']==bins and b['labels']==[f'{h:02d}-{h+width-1:02d}' for h in range(0,24,width)] and b['peakLabels']==[label for label,n in zip(b['labels'],bins) if n==max(bins)] and abs(b['peakShare']-max(bins)/sum(bins))<1e-12)
services=json.loads((O/'case_service_evidence.json').read_text(encoding='utf-8'))
texts={};htmls={}
for s in services['sources']:
 e=s['download'];check('service_original_hash_'+s['id'],e['status']=='downloaded' and sha(R/e['path'])==e['sha256'] and sha(R/e['textPath'])==e['textSha256'])
 texts[s['id']]=(R/e['textPath']).read_text(encoding='utf-8');htmls[s['id']]=(R/e['path']).read_text(encoding='utf-8')
 check('service_reference_date_'+s['id'],s['referenceDate'] in texts[s['id']])
check('center_hours_target_exclusions',all(t in texts['gijang_center'] for t in ['평일 9:00~17:00','12:00~13:00','주민 누구나','무료','진료·처방·예방접종','차성로 242번길 56']))
check('visit_conditions_scope',all(t in texts['gijang_visit'] for t in ['기초생활수급가구 및 차상위계층 가구 중 건강위험군','정관읍','기장읍','2025-09-03']) and all(t in htmls['gijang_visit'] for t in ['대상자 등록 동의 확인','방문약속']))
check('ems_rescue_summaries',all(t in texts['busan_ems'] for t in ['응급처치','무료','병원']) and '인명구조활동' in texts['busan_rescue'])
check('services_same_four_cases',{(c['district'],c['rawDong'],c['type'],c['subtype']) for c in services['cases']}=={(c['district'],c['rawDong'],c['type'],c['subtype']) for c in X['cases']})
check('services_2025_not_historical', '2025' in services['timeInterpretation'] and '2020' in services['timeInterpretation'] and '간주하지 않음' in services['timeInterpretation'])
check('services_js_matches_json',json.loads((W/'case-services.js').read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))==services)
check('manifest_unchanged',sha(O/'manifest.json')==frozen)
result={'status':'passed','checks':checks,'case_summary':case_notes,'manifest_sha256':frozen,'script_sha256':sha(__file__),'verification_scope':'Independent source-aggregate/marginal/case denominator and selection comparisons; reviewed timestamp parsing and scope masks in builder. Individual 704689 rows not reprocessed. Joint cells verified against independent marginal totals, not a second raw-row joint aggregation. Official service text and image-alt text reviewed; 2025 update dates are current reference, not retrospective operating evidence.','policy_interpretation':'Four cases are post-hoc explanatory contrasts, not a representative sample or policy priority ranking.'}
(O/'independent_deep_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('passed',len(checks));print(json.dumps(case_notes,ensure_ascii=False))
