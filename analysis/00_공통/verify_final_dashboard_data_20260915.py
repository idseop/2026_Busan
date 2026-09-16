"""Independent source-aggregate verification; does not import the dashboard builder."""
from pathlib import Path
import hashlib, json, calendar
from collections import Counter
from datetime import date, timedelta, datetime, timezone
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/최종결과-20260915'
AN=ROOT/'data/processed/동대응-전체결측제외-20260915/analysis'
BASE=AN.parent
POP=ROOT/'data/processed/컬럼선별-결측제외-20260915/population'
ST=ROOT/'data/processed/완전행-분석적합성-20260915/stability'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def csv(p): return pd.read_csv(p,keep_default_na=False)
checks=[]
def check(name,condition,detail=None):
    checks.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition: raise AssertionError(name)
manifest_path=OUT/'manifest.json'
frozen=sha(manifest_path)
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
for item in manifest['verified_aggregate_inputs']+manifest['outputs']:
    check('hash:'+item['path'],sha(ROOT/item['path'])==item['sha256'])
    if 'producerManifest' in item:
        check('producer:'+item['path'],sha(ROOT/item['producerManifest'])==item['producerManifestSha256'])
check('builder_hash',sha(ROOT/manifest['script'])==manifest['script_sha256'])
path=ROOT/'web/final/data/dashboard.json'
rawtext=path.read_text(encoding='utf-8'); data=json.loads(rawtext)
check('json_js_exact_identity',(ROOT/'web/final/data/dashboard-data.js').read_text(encoding='utf-8')=='window.BUSAN_DATA='+rawtext+';\n')
check('public_processed_identity',sha(path)==sha(OUT/'dashboard.json'))
T='EMRG_RSCU_ASSRT_NM'; S='EMRG_RSCU_CLSF_NM'; D='CLMTY_SGG_NM'; E='CLMTY_EMD_NM'
annual=csv(AN/'annual_type.csv').groupby(['year','scope',T]).receipt_count.sum().to_dict()
actual={(r['year'],r['scope'],r['type']):r['count'] for r in data['yearly']}
check('all_60_year_scope_type_counts',annual==actual and len(actual)==60)
for scope,total in [('A',704689),('B',579412),('C',574662)]:
    check('scope_total_'+scope,sum(v for (y,s,t),v in actual.items() if s==scope)==total)
timedict={(r['year'],r['scope'],r['type'],r['dimension'],r['value']):r for r in data['time']}
check('time_keys_unique',len(timedict)==len(data['time']))
seasons={1:'겨울',2:'겨울',3:'봄',4:'봄',5:'봄',6:'여름',7:'여름',8:'여름',9:'가을',10:'가을',11:'가을',12:'겨울'}
for filename,field,dim in [('month_type.csv','month','month'),('weekday_type.csv','weekday','weekday'),('hour_band_type.csv','hour_band','hourBand')]:
    source=csv(AN/filename).groupby(['year','scope',T,field]).receipt_count.sum().to_dict()
    selected={(y,s,t,v):r['count'] for (y,s,t,d,v),r in timedict.items() if d==dim}
    check('time_source_'+dim,source==selected)
seasoncounts=Counter()
for (y,s,t,dim,v),r in timedict.items():
    if dim=='month': seasoncounts[(y,s,t,seasons[v])]+=r['count']
check('season_aggregation',dict(seasoncounts)=={(y,s,t,v):r['count'] for (y,s,t,d,v),r in timedict.items() if d=='season'})
denom_ok=True
for (y,s,t,dim,v),r in timedict.items():
    if dim=='month': expected=calendar.monthrange(y,v)[1]
    elif dim=='season': expected=sum(calendar.monthrange(y,m)[1] for m in range(1,13) if seasons[m]==v)
    elif dim=='weekday': expected=sum((date(y,1,1)+timedelta(days=n)).weekday()==v for n in range(365+calendar.isleap(y)))
    else: expected=365+calendar.isleap(y)
    denom_ok &= expected==r['calendarDays']
check('all_calendar_denominators',denom_ok,'Weekday counts per calendar weekday; winter Jan/Feb/Dec of same calendar year.')
time_totals=Counter()
for (y,s,t,d,v),r in timedict.items(): time_totals[(y,s,t,d)]+=r['count']
check('all_time_dimension_totals',all(time_totals[(y,s,t,d)]==n for (y,s,t),n in actual.items() for d in ['month','season','weekday','hourBand']))
region=csv(AN/'original_region_type.csv').groupby(['year','scope',D,E,T]).receipt_count.sum().to_dict()
core=csv(BASE/'completeness/original_region_classification.csv')
core=core.loc[core.stage.eq('core8')].groupby(['year','scope',D,E,T])['count'].sum().to_dict()
cross=pd.read_csv(BASE/'linkage/all_raw_names_year_crosswalk.csv',dtype=str,keep_default_na=False)
cross={(int(r.year),r.district_name,r.raw_dong_name):r for r in cross.itertuples(index=False)}
ok=True; rrset=set()
for r in data['rawRegions']:
    key=(r['year'],r['scope'],r['district'],r['rawDong']); rrset.add(key)
    for t,n in r['typeCounts'].items(): ok &= n==region.get((*key,t),0) and r['core8TypeCounts'][t]==core.get((*key,t),0)
    ok &= r['total']==sum(r['typeCounts'].values()) and r['core8Total']==sum(r['core8TypeCounts'].values())
    c=cross[(key[0],key[2],key[3])]
    ok &= r['linkStatus']==c.status and r['candidateCodes']==[v for v in c.candidate_codes.split('|') if v]
    ok &= r['uniqueCode']==(c.unique_code or None) and r['codeLevelEligible']==(c.code_level_population_join_eligible.lower()=='true') and r['geographyConfirmed'] is False
check('raw_region_counts_core8_and_linkage',ok and len(rrset)==len(data['rawRegions'])==2901)
check('raw_region_coverage',rrset=={k[:4] for k in region})
pop=pd.read_csv(POP/'complete_population_dong.csv',dtype=str,keep_default_na=False)
pop={(int(r['year']),r['admin_dong_code']):r for r in pop.to_dict('records')}
ok=True
for r in data['population']:
    p=pop[(r['year'],r['code'])]
    ok &= r['ages']==[int(p[f'age_{a}']) for a in range(101)] and sum(r['ages'])==r['total']==int(p['population'])
    ok &= r['referenceDate']==p['population_reference_date']==f"{r['year']}-12-31" and r['districtCode']==p['district_code'] and r['district']==p['district_name'] and r['name']==p['admin_dong_name']
check('population_all_103525_age_cells_and_reference',ok and len(data['population'])==len(pop)==1025)
check('population_205_each_year',all(sum(r['year']==y for r in data['population'])==205 for y in range(2020,2025)))
st=csv(ST/'all_original_dong_subtype_sensitivity.csv')
st=st.loc[st.scope.eq('C')&st[S].ne('벌집제거')&st[[f'complete17_{y}' for y in range(2020,2025)]].gt(0).all(axis=1)]
expected={(r[D],r[E],r[T],r[S]):r for r in st.to_dict('records')}
ok=True; ids=set(); candidatekeys=set()
for r in data['candidates']:
    key=(r['district'],r['rawDong'],r['type'],r['subtype']); candidatekeys.add(key); ids.add(r['id']); p=expected[key]
    before=[int(p[f'core8_{y}']) for y in range(2020,2025)]; after=[int(p[f'complete17_{y}']) for y in range(2020,2025)]
    ok &= r['yearCounts']==after and r['core8YearCounts']==before and r['minAnnualCount']==min(after)
    ok &= r['thresholdPass']=={str(k):min(after)>=k for k in [1,5,10,20]}
    ok &= r['directionReversal']==((before[-1]-before[0])*(after[-1]-after[0])<0) and abs(r['retention']-sum(after)/sum(before))<1e-12 and r['scope']=='C'
check('all_repeated_observation_records',ok and candidatekeys==set(expected) and len(ids)==len(expected)==2325)
check('beehive_absent_candidates',all(r['subtype']!='벌집제거' for r in data['candidates']))
thresholds={str(k):sum(r['thresholdPass'][str(k)] for r in data['candidates']) for k in [1,5,10,20]}
check('candidate_threshold_counts',thresholds=={'1':2325,'5':1180,'10':838,'20':526})
def normalized(frame): return json.loads(frame.to_json(orient='records',force_ascii=False))
for key,file in [('annual','annual_retention.csv'),('repetitionThresholds','five_year_repetition_threshold_sensitivity.csv')]:
    check('sensitivity_source_'+key,data['sensitivity'][key]==normalized(csv(ST/file)))
missing=ST.parent/'missingness'
check('mobile_sensitivity_source',data['sensitivity']['mobileShifts']==normalized(csv(missing/'mobile_composition_shift_summary.csv')))
channels=csv(missing/'channel_retention_counts_retention.csv')
channels=channels.loc[channels.scope.eq('A')].groupby('RCPT_PATH_NM',as_index=False)[['core8','selected17']].sum().rename(columns={'RCPT_PATH_NM':'name','selected17':'complete17'})
check('channel_sensitivity_source',data['sensitivity']['channels']==normalized(channels))
for source in data['sources']: check('public_source_hash:'+source['id'],sha(ROOT/source['path'])==source['sha256'])
for key,file in [('responseEvidence','response_evidence.json'),('geographicEvidence','geographic_evidence.json')]:
    check('evidence_packaging_identity_'+key,data[key]==json.loads((OUT/file).read_text(encoding='utf-8')),'Content reviewed separately by parent; this check only verifies packaging identity.')
forbidden={'DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT','receipt_id','source_record_index'}
def forbidden_keys(value):
    if isinstance(value,dict): return [k for k in value if k in forbidden]+[k for v in value.values() for k in forbidden_keys(v)]
    if isinstance(value,list): return [k for v in value for k in forbidden_keys(v)]
    return []
check('no_individual_identifier_coordinate_fields',not forbidden_keys(data),'Official reference map geometry is a separate permitted geographic artifact; aggregate candidate hash IDs are not receipt IDs.')
report_path=ROOT/'docs/40-분석결과/부산-119-최종결과-20260915.md'
plan_path=ROOT/'docs/10-작업계획/부산 분석 작업 계획.md'
report=report_path.read_text(encoding='utf-8'); plan=plan_path.read_text(encoding='utf-8')
population_summary={y:{'total':sum(r['total'] for r in data['population'] if r['year']==y),'older65':sum(sum(r['ages'][65:]) for r in data['population'] if r['year']==y)} for y in [2020,2024]}
check('report_population_values',all(f"{p['total']:,}" in report and f"{100*p['older65']/p['total']:.2f}%" in report for p in population_summary.values()))
check('report_scope_type_values',all(f'{n:,}' in report for n in [704689,579412,574662,549789,474392,80591,62014,40272,32016,27266,34037,10990]))
check('report_plan_scope_limitations',all(s in report for s in ['원문','조건부','2020~2024','2026','부산 전체','벌집제거']) and '최종 분석·시각화·웹 결과물' in plan[:1000] and '704,689' in plan)
check('immutable_manifest_during_verification',sha(manifest_path)==frozen)
result={'status':'passed','verified_at':datetime.now(timezone.utc).isoformat(),'manifest_sha256':frozen,'dashboard_sha256':sha(path),'verifier_script_sha256':sha(__file__),'independent_of_builder':True,'raw_receipts_reread':False,'checks':checks,'summary':{'year_scope_type_cells':len(actual),'time_cells':len(timedict),'raw_region_year_scope_rows':len(rrset),'population_rows':len(pop),'age_cells':1025*101,'repeated_rows':len(expected),'threshold_counts':thresholds},'review_boundary':'Source aggregate arithmetic and package consistency independently verified. Official evidence content and webpage rendering reviewed by other agents. This is not approval of administrative-dong assignment or whole-Busan generalization.'}
(OUT/'independent_final_data_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result['summary'],ensure_ascii=False)); print('Checks passed:',len(checks))
