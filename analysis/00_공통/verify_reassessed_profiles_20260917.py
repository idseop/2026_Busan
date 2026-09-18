"""Separate check pass, no import of author code, run by the main agent."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[2]
N=R/'data/processed/신고주민연결심화-20260917'
A=N/'direction-reassessment';B=N/'direction-connections'
O=N/'direction-verification';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    assert ok,name
for folder in [A,B]:
    m=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    for rec in m['inputs']+m['outputs']: check('sha256 '+rec['path'],sha(R/rec['path'])==rec['sha256'])
f=pd.read_csv(A/'all-194-names-70-subtypes.csv')
keys=['district','rawDong','type','subtype']
cols={'CLMTY_SGG_NM':'district','CLMTY_EMD_NM':'rawDong','EMRG_RSCU_ASSRT_NM':'type','EMRG_RSCU_CLSF_NM':'subtype'}
old=pd.read_csv(R/'data/processed/동대응-전체결측제외-20260915/completeness/original_region_classification.csv',keep_default_na=False).rename(columns=cols)
old=old[old.stage.isin(['core8','provisional17'])&old.subtype.ne('벌집제거')]
ref=old[(old.stage=='provisional17')&(old.scope=='C')].groupby(keys)['count'].sum()
got=f.set_index(keys).countP
check('13580 region/type combinations including zeros',len(f)==194*70 and not f.duplicated(keys).any())
check('all P counts direct cached groupby',got.equals(ref.reindex(got.index,fill_value=0)))
check('P total',got.sum()==555786)
annual=old[(old.stage=='provisional17')&(old.scope=='C')].pivot_table(index=keys,columns='year',values='count',aggfunc='sum',fill_value=0)
for y in range(2020,2025):check('annual '+str(y),f.set_index(keys)[str(y)].equals(annual[y].reindex(got.index,fill_value=0)))
check('count rank',f.countRankWithinSubtype.equals(f.groupby(['type','subtype']).countP.rank(method='min',ascending=False).astype(int)))
check('observed years',f.observedYears.equals(f[[str(y) for y in range(2020,2025)]].gt(0).sum(axis=1)))
check('all regional totals',f.regionTotalP.equals(f.groupby(['district','rawDong']).countP.transform('sum')))
check('all major totals',f.majorTotalP.equals(f.groupby(['district','rawDong','type']).countP.transform('sum')))
check('regional share pct',np.allclose(f.shareRegionPct,100*f.countP/f.regionTotalP))
check('within major pct',np.allclose(f.shareWithinMajorPct,100*f.countP/f.majorTotalP.replace(0,np.nan),equal_nan=True))
annual_top=pd.Series(0,index=f.index)
for y in range(2020,2025):
    rank=f.groupby(['type','subtype'])[str(y)].rank(method='min',ascending=False)
    annual_top+=((rank<=10)&(f[str(y)]>0)).astype(int)
check('annualTop10Years',f.annualTop10Years.equals(annual_top))
before=old[(old.stage=='core8')&(old.scope=='C')].groupby(keys)['count'].sum().reindex(got.index,fill_value=0).to_numpy()
check('retention percent',np.allclose(f.retentionPct,100*f.countP/pd.Series(before).replace(0,np.nan),equal_nan=True))

# Different implementation: join groupby lookup columns onto all 13580 rows.
acc=pd.DataFrame(0,index=f.index,columns=['aboveRestBusan30','aboveRestDistrict30','withinMajorAboveRestBusan30','comparableRestBusan30','comparableRestDistrict30','withinMajorComparable30'])
for (stage,scope,y),z in old.groupby(['stage','scope','year']):
    x=f[keys].merge(z.groupby(keys)['count'].sum().rename('localCount').reset_index(),on=keys,how='left').fillna({'localCount':0})
    for on,new in [(['district','rawDong'],'localTotal'),(['district'],'districtTotal'),(['district','type','subtype'],'districtCount'),(['type','subtype'],'busanCount'),(['district','rawDong','type'],'localMajor'),(['type'],'busanMajor')]:
        x=x.merge(z.groupby(on)['count'].sum().rename(new).reset_index(),on=on,how='left').fillna({new:0})
    alln=z['count'].sum()
    local=x.localCount/x.localTotal.replace(0,np.nan)
    rest=(x.busanCount-x.localCount)/(alln-x.localTotal).replace(0,np.nan)
    district=(x.districtCount-x.localCount)/(x.districtTotal-x.localTotal).replace(0,np.nan)
    within=x.localCount/x.localMajor.replace(0,np.nan)
    restwithin=(x.busanCount-x.localCount)/(x.busanMajor-x.localMajor).replace(0,np.nan)
    acc['aboveRestBusan30']+=(local>rest).astype(int)
    acc['aboveRestDistrict30']+=(local>district).astype(int)
    acc['withinMajorAboveRestBusan30']+=(within>restwithin).astype(int)
    acc['comparableRestBusan30']+=(local.notna()&rest.notna()).astype(int)
    acc['comparableRestDistrict30']+=(local.notna()&district.notna()).astype(int)
    acc['withinMajorComparable30']+=(within.notna()&restwithin.notna()).astype(int)
for k in acc:check(k+' all407400 cells',np.array_equal(acc[k],f[k]))

# Cross-check new time bins against current selected records; no public identifiers.
times=pd.read_csv(B/'major-burden-time-cells.csv')
scopeNames=set(zip(times.district,times.rawDong))
raws=[]
for y in range(2020,2025):
    p=R/f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{y}.csv.gz'
    z=pd.read_csv(p,usecols=[*cols,'PRCS_RSLT_SE_NM','DCLR_DT'],dtype=str).rename(columns=cols)
    z=z[z.type.eq('구급')&z.subtype.isin(['질병','질병외','부상'])&pd.MultiIndex.from_frame(z[['district','rawDong']]).isin(scopeNames)].copy()
    d=pd.to_datetime(z.DCLR_DT.str.strip(),format='%Y%m%d%H%M%S')
    z['year']=d.dt.year;z['month']=d.dt.month;z['weekday']=d.dt.dayofweek;z['hour4']=d.dt.hour//4;z['hour6']=d.dt.hour//6
    raws.append(z)
z=pd.concat(raws,ignore_index=True)
for scope,raw in [('A',z),('P',z[z.PRCS_RSLT_SE_NM=='정상'])]:
    for dim in ['month','weekday','hour4','hour6']:
        both=pd.concat([raw,raw.assign(year=0)])
        want=both.groupby(keys+['year',dim]).size()
        q=times[(times.scope==scope)&(times.dimension==dim)].rename(columns={'value':dim}).set_index(keys+['year',dim])['count']
        check('time '+scope+' '+dim,q.equals(want.reindex(q.index,fill_value=0)))
        check('time denominator '+scope+' '+dim,times[(times.scope==scope)&(times.dimension==dim)].groupby(keys+['year'])['count'].sum().equals(both.groupby(keys+['year']).size()))

db=json.loads((R/'web/final/data/dashboard.json').read_text(encoding='utf8'))
pop={(p['year'],p['code']):p for p in db['population']}
pops=pd.read_csv(A/'all-name-population-candidates.csv',dtype={'candidateCode':str})
for _,p in pops[pops.populationAvailable].iterrows():
    r=pop[p.year,p.candidateCode]
    check('all101 '+str(p.year)+' '+p.rawDong+' '+p.candidateCode,list(p[[f'age_{a}' for a in range(101)]].astype(int))==r['ages'])
    for band,lo,hi in [('0_14',0,15),('15_39',15,40),('40_64',40,65),('65plus',65,101)]:
        check('age band '+str(p.year)+' '+p.rawDong+' '+p.candidateCode+' '+band,p['residents_'+band]==sum(r['ages'][lo:hi]) and np.isclose(p['pct_'+band],100*sum(r['ages'][lo:hi])/r['total']))
check('no beehive focus',not f.subtype.eq('벌집제거').any())
check('top3 C count',int(f[(f.type=='구급')&f.subtype.isin(['질병','질병외','부상'])].countP.sum())==422067)
newp=pd.read_csv(B/'major-burden-living-candidates-2023-2024.csv')
check('living only2023/24',set(newp.year)=={2023,2024} and newp.observedMonths.eq(12).all())
for s in json.loads((B/'sources.json').read_text(encoding='utf8')):
    check('source acquired '+s['id'],'path' in s and (R/s['path']).exists())
    if 'path' in s:check('source hash '+s['id'],sha(R/s['path'])==s['sha256'])
check('Saha source relevant text','65세' in (B/'saha-healthup-2024.html').read_text(encoding='utf8') and '다대1동' in (B/'saha-healthup-2024.html').read_text(encoding='utf8'))
check('Bujeon source relevant text','2026-04-15' in (B/'bujeon-outreach-2026.html').read_text(encoding='utf8') and '중·장년' in (B/'bujeon-outreach-2026.html').read_text(encoding='utf8'))
for folder in [A,B]:
    for p in folder.glob('*.csv'):
        header=pd.read_csv(p,nrows=0).columns
        check('public aggregate headers '+p.name,not any(c in header for c in ['DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT']))
result={'status':'PASS','failed':sum(not c['passed'] for c in checks),'checkGroups':len(checks),'reviewMode':'Single main agent, separate verifier code/pass, not a new independent agent review','scope':'13580 rows;407400 annual-condition comparisons;12528 time cells;candidate101age values;prior hashes;new official source content','checks':checks}
(O/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(O/'validation.md').write_text('# 방향 재검토 후 별도 검산\n\n주 실행자가 작성 코드와 분리한 검산 코드로 직접 실행했다. 새 독립 에이전트를 사용하지 않았다.\n\n'+f"- 결과: PASS, {len(checks)}개 검사그룹, 실패0\n- 전체 지역명194×세부유형70=13,580행과30조건407,400셀 대조\n- 새 시간표12,528셀은17개 완전행에서 별도로 재집계하여 일치\n- 전체 주민 후보101연령과 입력·출력·공식출처 해시 대조\n- 현재 결함·개별 피해자 연령·정책효과를 검증한 결과는 아님\n",encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False))
