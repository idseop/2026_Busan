"""Attach relevant context AFTER all-subtype screening, without inventing causes."""
from pathlib import Path
import hashlib,json,datetime,warnings
import pandas as pd
from urllib.request import Request, urlopen
from urllib.error import URLError

R=Path(__file__).resolve().parents[2]
DEP=R/'data/processed/신고주민연결심화-20260917'
O=DEP/'direction-connections';O.mkdir(parents=True,exist_ok=True)
A=DEP/'direction-reassessment'
CTX=R/'data/processed/통합완성-20260916/context'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[]
def read(p,expected=None,**kw):
    h=sha(p)
    if expected:assert h==expected,p
    inputs.append({'path':p.relative_to(R).as_posix(),'sha256':h,'priorHashMatched':expected is not None})
    return pd.read_csv(p,keep_default_na=False,**kw)
def csv(name,f):f.to_csv(O/name,index=False,encoding='utf-8-sig')
def dump(name,obj):(O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
f=read(A/'all-194-names-70-subtypes.csv')
tot=f.groupby(['type','subtype']).countP.sum().nlargest(3)
assert list(tot.index)==[('구급','질병'),('구급','질병외'),('구급','부상')]
focus=f[(pd.MultiIndex.from_frame(f[['type','subtype']]).isin(tot.index))&(f.countRankWithinSubtype<=10)&(f.countP>0)].copy()
csv('major-burden-top10.csv',focus)
names=set(zip(focus.district,focus.rawDong))
pop=read(A/'all-name-population-candidates.csv',dtype={'candidateCode':str})
sp=pop[pd.MultiIndex.from_frame(pop[['district','rawDong']]).isin(names)]
csv('major-burden-population-candidates.csv',sp)

D,N,T,U,P,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
old=json.loads((R/'data/processed/신고인구특성재정립-20260917/calls/manifest.json').read_text(encoding='utf8'))
oldhash={i['path'].replace('\\','/'):i['sha256'] for i in old['inputs']}
frames=[]
for y in range(2020,2025):
    p=R/f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{y}.csv.gz'
    z=read(p,oldhash[p.relative_to(R).as_posix()],usecols=[D,N,T,U,P,DT],dtype=str)
    z=z[z[T].eq('구급')&z[U].isin(['질병','질병외','부상'])&pd.MultiIndex.from_frame(z[[D,N]]).isin(names)].copy()
    ts=pd.to_datetime(z[DT].str.strip(),format='%Y%m%d%H%M%S');assert ts.dt.year.eq(y).all()
    z['year']=y;z['month']=ts.dt.month;z['weekday']=ts.dt.dayofweek;z['hour4']=ts.dt.hour//4;z['hour6']=ts.dt.hour//6
    frames.append(z.drop(columns=DT))
raw=pd.concat(frames,ignore_index=True).rename(columns={D:'district',N:'rawDong',T:'type',U:'subtype'})
g=raw[raw[P].eq('정상')]
# For these three subtypes B=C, and none is beehive. Preserve A separately.
keys=['district','rawDong','type','subtype']
times=[];summ=[]
for (d,n,t,u),allrows in raw.groupby(keys):
    for scope,z in [('A',allrows),('P',allrows[allrows[P].eq('정상')])]:
        for y in [0,*range(2020,2025)]:
            q=z if y==0 else z[z.year==y]
            calendar=pd.date_range(f'{y or 2020}-01-01',f'{y or 2024}-12-31')
            row=dict(zip(keys,[d,n,t,u]));row.update(scope=scope,year=y,count=len(q))
            for dim,values in [('month',range(1,13)),('weekday',range(7)),('hour4',range(6)),('hour6',range(4))]:
                counts=q[dim].value_counts().reindex(values,fill_value=0)
                row[dim+'Peak']='|'.join(map(str,counts.index[counts==counts.max()])) if len(q) else ''
                for value,count in counts.items():
                    days=int((calendar.month==value).sum()) if dim=='month' else int((calendar.dayofweek==value).sum()) if dim=='weekday' else len(calendar)
                    times.append({**dict(zip(keys,[d,n,t,u])),'scope':scope,'year':y,'dimension':dim,'value':value,'count':int(count),'denominator':len(q),'sharePct':100*count/len(q) if len(q) else None,'calendarDays':days,'receiptsPerCalendarDay':count/days})
            row['night20to07Pct']=100*q.hour4.isin([0,1,5]).mean() if len(q) else None
            summ.append(row)
csv('major-burden-time-cells.csv',pd.DataFrame(times));sm=pd.DataFrame(summ);csv('major-burden-time-summary.csv',sm)
actual=g.groupby(keys).size().sort_index()
expected=f[pd.MultiIndex.from_frame(f[['district','rawDong']]).isin(names)&f.type.eq('구급')&f.subtype.isin(['질병','질병외','부상'])].set_index(keys).countP.sort_index()
assert actual.equals(expected)

# Business/visitor background belongs to broad injury/non-disease interpretation,
# not a presumed cause. Keep raw legal name and all admin candidates separate.
hashes=json.loads((CTX/'output-hashes.json').read_text(encoding='utf8'))
c=read(CTX/'commerce-all-geographies-major.csv',hashes['commerce-all-geographies-major.csv'])
c=c[(c.level=='lawDong')&pd.MultiIndex.from_frame(c[['district','lawDong']]).isin(names)]
assert c.year.between(2020,2024).all()
csv('major-burden-commerce-20quarters.csv',c)
cs=c.groupby(['district','lawDong','categoryCode','category']).agg(observedSnapshots=('snapshot','nunique'),minimumSharePct=('sharePct','min'),maximumSharePct=('sharePct','max')).reset_index()
csv('major-burden-commerce-share-range.csv',cs)
l=read(CTX/'living-all205-yearly-hour-metrics.csv',hashes['living-all205-yearly-hour-metrics.csv'],dtype={'code':str})
l=l[l.year.isin([2023,2024])]
refs=sp[sp.year.isin([2023,2024])][['district','rawDong','year','candidateCode','candidateName','candidateCount']].drop_duplicates()
lp=refs.merge(l,left_on=['year','candidateCode'],right_on=['year','code'],how='left',validate='many_to_many')
assert lp['observedMonths'].eq(12).all()
csv('major-burden-living-candidates-2023-2024.csv',lp)

# Retain object-specific building context as a SECONDARY branch, not the main lens.
h=read(DEP/'context/housing-industry-profiles.csv',dtype={'sgisCode':str})
h=h[((h.district=='해운대구')&h.name.isin(['좌1동','좌2동','좌3동','좌4동']))|((h.district=='강서구')&h.name.isin(['대저1동','대저2동','명지1동','명지2동']))]
csv('secondary-object-specific-context.csv',h)

schema=R/'data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx'
inputs.append({'path':schema.relative_to(R).as_posix(),'sha256':sha(schema)})
with warnings.catch_warnings():
    warnings.filterwarnings('ignore',message='Workbook contains no default style')
    info=pd.read_excel(schema,header=None).fillna('')
selected=info[info.astype(str).apply(lambda s:s.str.lower().str.contains('emrg_rscu_clsf_nm|emrg_rscu_assrt_nm',regex=True)).any(axis=1)]
dump('classification-definition-evidence.json',{'input':schema.relative_to(R).as_posix(),'sha256':sha(schema),'extractedRows':selected.values.tolist(),'interpretation':'종별·분류 컬럼 일반 설명. 질병외를 특정 발생 기전으로 세분하는 사전은 이 행에 없음.'})

urls=[('living-hour-definition','https://www.data.go.kr/data/15142761/fileData.do'),
 ('commerce-definition','https://www.data.go.kr/data/15083033/fileData.do'),
 ('saha-healthup-2024','https://www.busan.go.kr/jumin04/1627397'),
 ('bujeon-outreach-2026','https://www.busan.go.kr/jumin04/1728810')]
sourcefile=O/'sources.json'
cached={s['id']:s for s in json.loads(sourcefile.read_text(encoding='utf8'))} if sourcefile.exists() else {}
sources=[]
for key,url in urls:
    previous=cached.get(key)
    if previous and 'path' in previous and (R/previous['path']).exists() and sha(R/previous['path'])==previous['sha256']:
        sources.append(previous)
        continue
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
            body=r.read();status=r.status
        p=O/(key+'.html');p.write_bytes(body)
        sources.append({'id':key,'url':url,'retrievedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':p.relative_to(R).as_posix(),'sha256':sha(p),'status':status,'bodyRequiresReview':True})
    except (URLError,TimeoutError) as ex:
        sources.append({'id':key,'url':url,'error':str(ex),'bodyRequiresReview':True})
dump('sources.json',sources)
dump('specification.json',{'mainBranches':'Largest3 city subtypes first; all names tied within top10 per subtype are shown, not a weighted priority.',
 'population':'MOIS same-year end population; no pooled administrative candidates or inferred patient age.',
 'time':'Counts of current17-field selected records, A vs P only; P=B=C for these3subtypes. No claim that core8 before-selection time was verified.',
 'commerce':'2020–2024 all20snapshots; law-name context is not receipt location. Business listings are not visit counts/injury cause or manufacturing registry.',
 'living':'2023–2024 separate candidate admin profiles,12months equally weighted, telephone-derived estimates per official definition; not individual patients or count denominator.',
 'buildings':'Only E/V or object-specific fire branches; 2024statistics using2025boundary, no forced historical allocation.',
 'serviceEvidence':'Current/historical outreach confirms presence and target conditions, not effectiveness or a service gap.'})
inputs.append({'path':Path(__file__).relative_to(R).as_posix(),'sha256':sha(Path(__file__))})
dump('manifest.json',{'inputs':inputs,'major3Count':int(tot.sum()),'major3SharePct':float(100*tot.sum()/555786),'mainNames':sorted(names),'timePCount':len(g),'checks':['new primary time totals equal previously verified all-subtype counts','reused commerce/living output hashes match','no candidate population sum','2025 living excluded'],
 'outputs':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)} for p in sorted(O.glob('*')) if p.is_file() and p.name!='manifest.json'],'authorChecksOnly':True})
print(json.dumps({'major3Count':int(tot.sum()),'major3SharePct':100*tot.sum()/555786,'mainNames':len(names),'timePCount':len(g),'timeCells':len(times)},ensure_ascii=False))
