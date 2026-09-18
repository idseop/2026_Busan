"""Screen every receipt subtype before choosing resident/place explanatory data.

Counts order analytical workload within the SAME subtype. They are not severity,
patient age, incident risk, or intervention priority. No weighted score is made.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[2]
PRE = R / 'data/processed/신고인구특성재정립-20260917'
DEP = R / 'data/processed/신고주민연결심화-20260917'
O = DEP / 'direction-reassessment'
O.mkdir(parents=True, exist_ok=True)
D,N,T,U = 'CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM'
years = list(range(2020,2025))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[]
def read(p, expected=None):
    h=sha(p)
    if expected is not None: assert h==expected, p
    inputs.append({'path':p.relative_to(R).as_posix(),'sha256':h,'priorHashMatched':expected is not None})
    return pd.read_csv(p,keep_default_na=False)
def csv(name,frame):
    frame.to_csv(O/name,index=False,encoding='utf-8-sig')
def dump(name,obj):
    (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

manifest=json.loads((PRE/'calls/manifest.json').read_text(encoding='utf8'))
oldhash={i['path'].replace('\\','/'):i['sha256'] for i in manifest['inputs']}
p=R/'data/processed/동대응-전체결측제외-20260915/completeness/original_region_classification.csv'
c=read(p,oldhash[p.relative_to(R).as_posix()])
c=c[c.stage.isin(['core8','provisional17']) & c[U].ne('벌집제거')].copy()
c['stage']=c.stage.replace({'provisional17':'complete17'})
primary=c[(c.stage=='complete17')&(c.scope=='C')]
names=pd.MultiIndex.from_frame(primary[[D,N]].drop_duplicates().sort_values([D,N]))
cats=pd.MultiIndex.from_frame(primary[[T,U]].drop_duplicates().sort_values([T,U]))
assert len(names)==194 and len(cats)==70 and primary['count'].sum()==555786
annual=read(PRE/'calls/region-all-subtypes-by-year.csv')
assert primary.groupby(['year',D,N,T,U])['count'].sum().sort_index().equals(annual.groupby(['year',D,N,T,U])['count'].sum().sort_index())
def div(a,b):
    return np.divide(a,b,out=np.full(np.broadcast_shapes(a.shape,b.shape),np.nan),where=b!=0)
def matrix(z):
    return z.groupby([D,N,T,U])['count'].sum().unstack([T,U],fill_value=0).reindex(index=names,columns=cats,fill_value=0).to_numpy(dtype=int)
def denoms(z):
    n=z.groupby([D,N])['count'].sum().reindex(names,fill_value=0).to_numpy(dtype=int)
    m=z.groupby([D,N,T])['count'].sum().unstack(T,fill_value=0).reindex(index=names,fill_value=0)
    return n,np.column_stack([m[t].to_numpy() for t,u in cats])
districts=names.get_level_values(0).to_numpy()
same=(districts[:,None]==districts[None,:]).astype(int)
shape=(len(names),len(cats))
fields={k:np.zeros(shape,dtype=int) for k in ['aboveRestBusan30','aboveRestDistrict30','withinMajorAboveRestBusan30','comparableRestBusan30','comparableRestDistrict30','withinMajorComparable30']}
pa=[];ca=[];annualranks=[]
for stage in ['core8','complete17']:
    for scope in 'ABC':
        for y in years:
            z=c[(c.stage==stage)&(c.scope==scope)&(c.year==y)]
            a=matrix(z);n,m=denoms(z)
            sh=div(a,n[:,None]); rest=div(a.sum(axis=0)[None,:]-a,(n.sum()-n)[:,None]); dr=div(same@a-a,(same@n-n)[:,None])
            wsh=div(a,m);wr=div(m*0+a.sum(axis=0)[None,:]-a,m.sum(axis=0)[None,:]-m)
            for key,l,r in [('aboveRestBusan30',sh,rest),('aboveRestDistrict30',sh,dr),('withinMajorAboveRestBusan30',wsh,wr)]: fields[key]+=(l>r)
            fields['comparableRestBusan30']+=np.isfinite(sh)&np.isfinite(rest)
            fields['comparableRestDistrict30']+=np.isfinite(sh)&np.isfinite(dr)
            fields['withinMajorComparable30']+=np.isfinite(wsh)&np.isfinite(wr)
            if scope=='C':
                if stage=='complete17':
                    pa.append(a)
                    annualranks.append(pd.DataFrame(a).rank(axis=0,method='min',ascending=False).to_numpy())
                else: ca.append(a)
pa=np.stack(pa);ca=np.stack(ca);ar=np.stack(annualranks)
a=pa.sum(axis=0); b=ca.sum(axis=0); n,m=denoms(primary)
sh=div(a,n[:,None]); rest=div(a.sum(axis=0)[None,:]-a,(n.sum()-n)[:,None]); dr=div(same@a-a,(same@n-n)[:,None])
rank=pd.DataFrame(a).rank(axis=0,method='min',ascending=False).to_numpy(dtype=int)
records=[]
for i,(d,name) in enumerate(names):
    for j,(t,u) in enumerate(cats):
        record={'district':d,'rawDong':name,'type':t,'subtype':u,'countP':int(a[i,j]),'regionTotalP':int(n[i]),'majorTotalP':int(m[i,j]),
          'shareRegionPct':100*sh[i,j],'shareWithinMajorPct':100*a[i,j]/m[i,j] if m[i,j] else None,
          'citySubtypeCount':int(a[:,j].sum()),'shareCitySubtypePct':100*a[i,j]/a[:,j].sum(),
          'countRankWithinSubtype':int(rank[i,j]),'restBusanSharePct':100*rest[i,j],'restDistrictSharePct':100*dr[i,j],
          'observedYears':int((pa[:,i,j]>0).sum()),'minimumAnnualCount':int(pa[:,i,j].min()),'maximumAnnualCount':int(pa[:,i,j].max()),
          'annualTop10Years':int(((ar[:,i,j]<=10)&(pa[:,i,j]>0)).sum()),
          'retentionPct':100*a[i,j]/b[i,j] if b[i,j] else None,
          'direction2024vs2020P':int(np.sign(pa[-1,i,j]-pa[0,i,j])),
          'direction2024vs2020Core8':int(np.sign(ca[-1,i,j]-ca[0,i,j])),
          **{k:int(v[i,j]) for k,v in fields.items()},
          **{str(y):int(pa[yi,i,j]) for yi,y in enumerate(years)}}
        records.append(record)
f=pd.DataFrame(records)
csv('all-194-names-70-subtypes.csv',f)
csv('within-subtype-top10.csv',f[(f.countP>0)&(f.countRankWithinSubtype<=10)].sort_values(['type','subtype','countRankWithinSubtype','district','rawDong']))
coverage=[]
for (t,u),g in f.groupby(['type','subtype']):
    for k in [5,10,20]:
        q=g[(g.countP>0)&(g.countRankWithinSubtype<=k)]
        coverage.append({'type':t,'subtype':u,'cutoffRank':k,'namesWithTies':len(q),'countP':int(q.countP.sum()),'citySubtypeCount':int(g.countP.sum()),'coveragePct':100*q.countP.sum()/g.countP.sum(),'topFiveYearRepeatedNames':int(q.observedYears.eq(5).sum())})
csv('top5-top10-top20-coverage.csv',pd.DataFrame(coverage))
city=primary.groupby([T,U,'year'])['count'].sum().reset_index().rename(columns={T:'type',U:'subtype'})
csv('city-annual-all-subtypes.csv',city)
district=primary.groupby([D,T,U])['count'].sum().reset_index().rename(columns={D:'district',T:'type',U:'subtype'})
district['countRankWithinSubtype']=district.groupby(['type','subtype'])['count'].rank(method='min',ascending=False).astype(int)
csv('district-all-subtypes-count-order.csv',district)

# Join ALL raw names to their candidate resident profiles before selecting context.
dashboard=R/'web/final/data/dashboard.json'
pm=json.loads((PRE/'population/manifest.json').read_text(encoding='utf8'))
assert sha(dashboard)==pm['dashboard']['sha256']
inputs.append({'path':dashboard.relative_to(R).as_posix(),'sha256':sha(dashboard),'priorHashMatched':True})
db=json.loads(dashboard.read_text(encoding='utf8'))
pop={(p['year'],p['code']):p for p in db['population']}
links={(p['year'],p['district'],p['rawDong']):p for p in db['rawRegions'] if p['scope']=='C'}
year_name_totals=primary.groupby(['year',D,N])['count'].sum().to_dict()
pr=[];lr=[]
for d,name in names:
    for y in years:
        link=links.get((y,d,name));codes=link['candidateCodes'] if link else []
        count_y=int(year_name_totals.get((y,d,name),0))
        lr.append({'district':d,'rawDong':name,'year':y,'receiptCountP':count_y,'observedPrimaryYear':count_y>0,'candidateCount':len(codes),'candidateCodes':'|'.join(codes),'linkStatus':link['linkStatus'] if link else 'no_link_record','geographyConfirmed':False})
        for code in codes:
            p=pop.get((y,code))
            if not p:
                pr.append({'district':d,'rawDong':name,'year':y,'candidateCode':code,'populationAvailable':False});continue
            assert p['district']==d and sum(p['ages'])==p['total'] and len(p['ages'])==101
            row={'district':d,'rawDong':name,'year':y,'candidateCode':code,'candidateName':p['name'],'populationAvailable':True,'candidateCount':len(codes),'residentTotal':p['total'],'geographyConfirmed':False}
            for band,lo,hi in [('0_14',0,15),('15_39',15,40),('40_64',40,65),('65plus',65,101)]:
                count=sum(p['ages'][lo:hi]);row['residents_'+band]=count;row['pct_'+band]=100*count/p['total']
            row.update({f'age_{age}':count for age,count in enumerate(p['ages'])})
            pr.append(row)
csv('all-name-population-candidates.csv',pd.DataFrame(pr))
csv('all-name-link-status.csv',pd.DataFrame(lr))
dump('specification.json',{'mainScope':'P=normal C without beehives; 2020–2024;555786 receipts',
 'selectionOrder':'All70 subtypes and194 raw region names first, resident background for every name second, question-specific context after that.',
 'largeProblem':'Observed receipt burden by SAME subtype; not injury severity or population risk. Within-subtype counts, repetition, share, selection sensitivity are parallel, no combined score.',
 'topLists':'Top5/10/20 incl ties are presentation/coverage checks, not policy eligibility thresholds. Tiny categories remain in full CSV but are not made central merely for distinct composition.',
 'comparisons':'2 selection sets×3 handling scopes×5 years, regional denominator and within-major denominator, rest of Busan and rest of same district.30 cells are overlapping descriptions, not independent statistical replications.',
 'population':'All101 ages preserved. Candidate areas kept separate, no age attribution, no population rates, no raw-name forced allocation.',
 'contextStatus':'Housing/industry only relevant to the corresponding receipt detail and target object; health/activity/building/outdoor context must follow subtype evidence.',
 'severityMissing':'No verified linked deaths/injury severity/loss/response delays; do not label count order high-risk or most severe.'})
inputs.append({'path':Path(__file__).relative_to(R).as_posix(),'sha256':sha(Path(__file__)),'priorHashMatched':False})
dump('manifest.json',{'inputs':inputs,'countP':int(a.sum()),'names':194,'subtypes':70,'summaryRows':len(f),'comparisonCells':int(np.prod(shape)*30),'allPopulationCandidateRows':len(pr),
 'checks':['current cache hash agrees with prior raw-verified input','all annual primary counts match prior all-subtype aggregation','all101 ages reconcile for every candidate','no shared candidate populations are summed'],
 'outputs':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)} for p in sorted(O.glob('*')) if p.is_file() and p.name!='manifest.json'],
 'execution':'Single main agent; author checks; separate verification pass will be recorded separately.'})
print(json.dumps({'countP':int(a.sum()),'names':194,'subtypes':70,'summaryRows':len(f),'populationCandidateRows':len(pr)},ensure_ascii=False))
