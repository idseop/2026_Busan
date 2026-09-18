"""Reproducible district-to-name comparisons; calls and resident context stay separate."""
from pathlib import Path
import hashlib
import json
import calendar
import pandas as pd

R = Path(__file__).resolve().parents[2]
O = R / 'data/processed/신고주민연결심화-20260917/analysis'
O.mkdir(parents=True, exist_ok=True)
B = R / 'data/processed/동대응-전체결측제외-20260915/completeness'
PRE = R / 'data/processed/신고인구특성재정립-20260917'
D, N, T, U, P, DT = ('CLMTY_SGG_NM', 'CLMTY_EMD_NM', 'EMRG_RSCU_ASSRT_NM',
                      'EMRG_RSCU_CLSF_NM', 'PRCS_RSLT_SE_NM', 'DCLR_DT')
YEARS = range(2020, 2025)
TYPES = ['구급', '구조', '화재', '기타']
STAGES = ['core8', 'complete17']
CASES = [('북구','금곡동'), ('북구','화명동'), ('영도구','동삼동'),
         ('강서구','대저1동'), ('강서구','대저2동'), ('강서구','명지동'),
         ('강서구','송정동'), ('기장군','기장읍'), ('기장군','정관읍')]
inputs = []
checks = []
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
prior = json.loads((PRE/'calls/manifest.json').read_text(encoding='utf8'))
oldhash = {x['path'].replace('\\', '/'): x['sha256'] for x in prior['inputs']}

def checked(path, require_prior=False):
    h = sha(path)
    rel = path.relative_to(R).as_posix()
    match = h == oldhash[rel] if rel in oldhash else None
    if require_prior:
        assert match, rel
    inputs.append({'path': rel, 'sha256': h, 'priorInputHashMatch': match})
    return path

def csv(name, records):
    f = records if isinstance(records, pd.DataFrame) else pd.DataFrame(records)
    f.to_csv(O/name, index=False, encoding='utf-8-sig')
    return f

def dump(name, obj):
    (O/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')

spec = {
    'period': list(YEARS), 'unit': '신고 접수 기록',
    'primary': '17개 완전행, 정상 처리, 업무운행·훈련출동·구급차소독 및 벌집제거 제외',
    'comparisons': 'core8/provisional17(여기서는 complete17) × A/B/C × 2020–2024; 각 조건 벌집제거 제외',
    'denominator': '유형 비중은 해당 지역의 전체 포함 신고가 분모. 비교는 해당 지역을 뺀 부산 또는 같은 구군.',
    'cells': '30셀은 독립표본이나 통계검정이 아님. 연도와 포함조건을 바꾼 기술적 민감도 검사.',
    'criteria': 'strictly greater 구성비; 0건 유형은 명시적 0. 분모0은 비교불가. 통계적 유의성·위험·인과 판정 아님.',
    'selection': '9개 사례는 이전 탐색 결과에 따른 사후 심화대상. 30/30은 위험점수·선정문턱·독립 재현횟수가 아니며 반증도 함께 보존.',
    'scope': '16구군 모든 70 종별×세부유형과 194원문지역명 모든4종별; 선정9원문지역은 구내 비교와 시간 심화.',
    'time': '관측기간 달력일수 보정, 토·일 주말; 공휴일 별도 구분 안함. 4시간/6시간 bin은 동일 길이.',
    'population': '동명 후보별 같은 연도12월말 전체101연령. 단일후보도 실제 사건위치 확정 아님. 복수후보 합산 금지.',
    'interpretation': '주민연령으로 신고자 연령·환자수 추정하지 않음. 주민분모 신고율·임의점수·인과효과 없음.',
}
dump('specification.json', spec)
c = pd.read_csv(checked(B/'original_region_classification.csv', True), keep_default_na=False)
c = c[c.stage.isin(['core8','provisional17'])].copy()
c['stage'] = c.stage.replace({'provisional17':'complete17'})
c = c[c[U].ne('벌집제거')].copy()
frames=[]
for y in YEARS:
    f=pd.read_csv(checked(B/f'complete_17_{y}.csv.gz', True), usecols=[D,N,T,U,P,DT], dtype=str, keep_default_na=False)
    ts=pd.to_datetime(f[DT].str.strip(), format='%Y%m%d%H%M%S', errors='raise')
    assert ts.dt.year.eq(y).all()
    f['year']=y; f['month']=ts.dt.month; f['weekday']=ts.dt.dayofweek; f['hour']=ts.dt.hour
    frames.append(f.drop(columns=DT))
f=pd.concat(frames, ignore_index=True)
assert len(f)==704689
mask=f[P].eq('정상')&~f[U].isin(['업무운행','훈련출동','구급차소독','벌집제거'])
x=f[mask].copy(); assert len(x)==555786
actual=x.groupby(['year',D,N,T,U]).size().sort_index()
expected=c[(c.stage=='complete17')&(c.scope=='C')].groupby(['year',D,N,T,U])['count'].sum().sort_index()
assert actual.equals(expected)
oldreg=pd.read_csv(checked(PRE/'calls/region-all-subtypes-by-year.csv'))
assert actual.equals(oldreg.set_index(['year',D,N,T,U])['count'].sort_index())
checks.append('P555786, 모든 year×district×rawName×type×subtype 집계가 기존 검산 집계와 일치')

districts=sorted(x[D].unique()); names=sorted(set(zip(x[D],x[N])))
subtypes=sorted(set(zip(x[T],x[U])))
assert len(districts)==16 and len(names)==194 and len(subtypes)==70
csv('comparison-before-only-names.csv', c[(c.stage=='core8')&~pd.MultiIndex.from_frame(c[[D,N]]).isin(names)].groupby([D,N,'scope'])['count'].sum().reset_index())

# Aggregation dictionaries avoid repeated scanning and retain explicit zero cells.
alltime=c.copy(); alltime['year']=0
z=pd.concat([c,alltime], ignore_index=True)
base=['stage','scope','year']
alln=z.groupby(base)['count'].sum().to_dict()
alltype=z.groupby(base+[T])['count'].sum().to_dict()
allsub=z.groupby(base+[T,U])['count'].sum().to_dict()
dn=z.groupby(base+[D])['count'].sum().to_dict()
dty=z.groupby(base+[D,T])['count'].sum().to_dict()
dsub=z.groupby(base+[D,T,U])['count'].sum().to_dict()
rn=z.groupby(base+[D,N])['count'].sum().to_dict()
rty=z.groupby(base+[D,N,T])['count'].sum().to_dict()
rsub=z.groupby(base+[D,N,T,U])['count'].sum().to_dict()

def comparison(level, region, t, u, reference, stage, scope, y):
    b=(stage,scope,y); district=region[0]; name=region[1] if len(region)>1 else ''
    suffix=(t,) if u=='' else (t,u)
    numerator=(dty if u=='' else dsub) if level=='district' else (rty if u=='' else rsub)
    denominator=dn if level=='district' else rn
    count=int(numerator.get(b+region+suffix,0)); n=int(denominator.get(b+region,0))
    refnum=alltype if u=='' else allsub
    if reference=='restBusan':
        refn=int(alln[b])-n; refcount=int(refnum.get(b+suffix,0))-count
    else:
        refn=int(dn[b+(district,)])-n
        refcount=int((dty if u=='' else dsub).get(b+(district,)+suffix,0))-count
    share=count/n if n else None; refshare=refcount/refn if refn else None
    return {'level':level,'district':district,'rawDong':name,'type':t,'subtype':u,'reference':reference,
            'stage':stage,'scope':scope,'year':y,'count':count,'denominator':n,
            'referenceCount':refcount,'referenceDenominator':refn,'share':share,'referenceShare':refshare,
            'differencePp':100*(share-refshare) if share is not None and refshare is not None else None,
            'aboveReference':share>refshare if share is not None and refshare is not None else None}

def calculate(level, regions, categories, references):
    records=[]
    for region in regions:
        for t,u in categories:
            for reference in references:
                for stage in STAGES:
                    for scope in 'ABC':
                        for y in [0,*YEARS]:
                            records.append(comparison(level,region,t,u,reference,stage,scope,y))
    result=pd.DataFrame(records)
    keys=['level','district','rawDong','type','subtype','reference']
    summaries=[]
    for key,g in result.groupby(keys,dropna=False):
        annual=g[g.year.ne(0)]; five=g[g.year.eq(0)]; primary=g[(g.stage=='complete17')&(g.scope=='C')]
        main=primary[primary.year.eq(0)].iloc[0]
        item=dict(zip(keys,key)); item.update({
            'countP':int(main['count']),'denominatorP':int(main.denominator),'shareP':main.share,
            'referenceShareP':main.referenceShare,'differencePpP':main.differencePp,
            'aboveReference30':int(annual.aboveReference.sum()),'comparableCells30':int(annual.aboveReference.notna().sum()),
            'aboveReference6':int(five.aboveReference.sum()),'comparableCells6':int(five.aboveReference.notna().sum()),
            'aboveReferencePrimaryYears':int(primary[primary.year.ne(0)].aboveReference.sum()),
            'minimumDifferencePp30':annual.differencePp.min(),'maximumDifferencePp30':annual.differencePp.max(),
            'observedPrimaryYears':int((primary[primary.year.ne(0)]['count']>0).sum())})
        summaries.append(item)
    return result,pd.DataFrame(summaries)

for name,level,regions,cats,refs in [
    ('district-all-types','district',[(d,) for d in districts],[(t,'') for t in TYPES]+subtypes,['restBusan']),
    ('raw-name-major-types','rawName',names,[(t,'') for t in TYPES],['restBusan','restDistrict']),
    ('selected-name-all-types','rawName',CASES,[(t,'') for t in TYPES]+subtypes,['restBusan','restDistrict'])]:
    cells,summary=calculate(level,regions,cats,refs)
    csv(name+'-comparison-cells.csv',cells); csv(name+'-comparison-summary.csv',summary)
    checks.append(f'{name}: {len(cells)} cells, {len(summary)} summaries; explicit zeros retained')
    print(name,len(cells),flush=True)

direct=[]
for (ld,ln),(rd,rn_name) in [(('북구','금곡동'),('북구','화명동')),
                              (('기장군','기장읍'),('기장군','정관읍'))]:
    for t,u in [('구급',''),('구급','질병'),('구급','질병외'),('구급','부상'),('구급','심정지')]:
        for denominator_mode in (['allCalls','withinType'] if u else ['allCalls']):
            for stage in STAGES:
                for scope in 'ABC':
                    for y in [0,*YEARS]:
                        b=(stage,scope,y)
                        lkey=b+(ld,ln); rkey=b+(rd,rn_name)
                        counts=rty if not u else rsub
                        suffix=(t,) if not u else (t,u)
                        lc=int(counts.get(lkey+suffix,0)); rc=int(counts.get(rkey+suffix,0))
                        lden=int(rn[lkey] if denominator_mode=='allCalls' else rty.get(lkey+(t,),0))
                        rden=int(rn[rkey] if denominator_mode=='allCalls' else rty.get(rkey+(t,),0))
                        ls=lc/lden if lden else None; rs=rc/rden if rden else None
                        direct.append({'leftDistrict':ld,'leftName':ln,'rightDistrict':rd,'rightName':rn_name,
                            'type':t,'subtype':u,'denominatorMode':denominator_mode,'stage':stage,'scope':scope,'year':y,
                            'leftCount':lc,'leftDenominator':lden,'leftShare':ls,'rightCount':rc,'rightDenominator':rden,'rightShare':rs,
                            'leftHigher':ls>rs if ls is not None and rs is not None else None,
                            'differencePp':100*(ls-rs) if ls is not None and rs is not None else None})
direct_df=csv('direct-pair-comparison-cells.csv',direct)
direct_s=[]
pairkeys=['leftDistrict','leftName','rightDistrict','rightName','type','subtype','denominatorMode']
for key,g in direct_df.groupby(pairkeys,dropna=False):
    a=g[g.year.ne(0)]; p=g[(g.stage=='complete17')&(g.scope=='C')&(g.year==0)].iloc[0]
    direct_s.append({**dict(zip(pairkeys,key)),'leftHigher30':int(a.leftHigher.sum()),'comparableCells30':int(a.leftHigher.notna().sum()),
        'minimumDifferencePp30':a.differencePp.min(),'maximumDifferencePp30':a.differencePp.max(),
        'leftCountP':int(p.leftCount),'leftDenominatorP':int(p.leftDenominator),'leftShareP':p.leftShare,
        'rightCountP':int(p.rightCount),'rightDenominatorP':int(p.rightDenominator),'rightShareP':p.rightShare,
        'differencePpP':p.differencePp})
csv('direct-pair-comparison-summary.csv',direct_s)

selected=x[pd.MultiIndex.from_frame(x[[D,N]]).isin(CASES)].copy()
csv('selected-name-annual-subtypes.csv',selected.groupby([D,N,'year',T,U]).size().rename('count').reset_index())
cal={}
for y in [0,*YEARS]:
    days=pd.date_range(f'{y or 2020}-01-01',f'{y or 2024}-12-31')
    cal[y]={'days':len(days),'weekend':int((days.dayofweek>=5).sum()),'weekday':int((days.dayofweek<5).sum()),
            'month':{m:int((days.month==m).sum()) for m in range(1,13)},
            'weekdays':{w:int((days.dayofweek==w).sum()) for w in range(7)}}
timecells=[]; timesummary=[]
for (district,name),g in selected.groupby([D,N]):
    selectors=[('전체','',g)]+[(t,'',q) for t,q in g.groupby(T)]+[(t,u,q) for (t,u),q in g.groupby([T,U])]
    for t,u,q in selectors:
        for y in [0,*YEARS]:
            v=q if y==0 else q[q.year.eq(y)]
            n=len(v)
            if n==0:
                continue
            k={'district':district,'rawDong':name,'type':t,'subtype':u,'year':y}
            for dim,series,levels in [('month',v.month,range(1,13)),('weekday',v.weekday,range(7)),
                                      ('hour4',v.hour//4,range(6)),('hour6',v.hour//6,range(4)),
                                      ('weekdayHour4',v.weekday*6+v.hour//4,range(42))]:
                counts=series.value_counts().reindex(levels,fill_value=0)
                assert counts.sum()==n
                for idx,count in counts.items():
                    days=cal[y]['month'][idx] if dim=='month' else cal[y]['weekdays'][idx] if dim=='weekday' else cal[y]['weekdays'][idx//6] if dim=='weekdayHour4' else cal[y]['days']
                    timecells.append({**k,'dimension':dim,'bin':idx,'count':int(count),'denominator':n,'share':count/n,'calendarDays':days,'countPerDay':count/days})
            we=int(v.weekday.ge(5).sum()); wd=n-we
            h4=(v.hour//4).value_counts().reindex(range(6),fill_value=0)
            h6=(v.hour//6).value_counts().reindex(range(4),fill_value=0)
            peak4=list(h4[h4.eq(h4.max())].index); peak6=list(h6[h6.eq(h6.max())].index)
            shared=set().union(*(set(range(i*4,i*4+4)) for i in peak4)) & set().union(*(set(range(i*6,i*6+6)) for i in peak6))
            timesummary.append({**k,'count':n,'peak4hBins':'|'.join(map(str,peak4)),'peak6hBins':'|'.join(map(str,peak6)),
                'peakWindowsHaveOverlap':bool(shared),'daytime08to19Count':int(v.hour.between(8,19).sum()),
                'daytime08to19Share':float(v.hour.between(8,19).mean()),
                'night20to07Count':int((~v.hour.between(8,19)).sum()),
                'night20to07Share':float((~v.hour.between(8,19)).mean()),'weekendCount':we,'weekdayCount':wd,
                'weekendDays':cal[y]['weekend'],'weekdayDays':cal[y]['weekday'],
                'weekendPerDay':we/cal[y]['weekend'],'weekdayPerDay':wd/cal[y]['weekday'],
                'weekendWeekdayDailyRatio':(we/cal[y]['weekend'])/(wd/cal[y]['weekday']) if wd else None})
csv('selected-name-time-cells.csv',timecells)
time_df=csv('selected-name-time-summary.csv',timesummary)
peak_stability=[]
parse_bins=lambda value: set(int(z) for z in str(value).split('|'))
for key,g in time_df.groupby(['district','rawDong','type','subtype'],dropna=False):
    p=g[g.year.eq(0)].iloc[0]; a=g[g.year.ne(0)]
    p4=parse_bins(p.peak4hBins); p6=parse_bins(p.peak6hBins)
    h4=set().union(*(set(range(i*4,i*4+4)) for i in p4))
    h6=set().union(*(set(range(i*6,i*6+6)) for i in p6))
    peak_stability.append({**dict(zip(['district','rawDong','type','subtype'],key)),
        'count':int(p['count']),'observedYears':len(a),'overallPeak4hBins':p.peak4hBins,'overallPeak6hBins':p.peak6hBins,
        'yearsIncludingOverallPeak4h':sum(bool(parse_bins(v)&p4) for v in a.peak4hBins),
        'yearsIncludingOverallPeak6h':sum(bool(parse_bins(v)&p6) for v in a.peak6hBins),
        'yearsWithExactlySame4hPeakSet':sum(parse_bins(v)==p4 for v in a.peak4hBins),
        'yearsWithExactlySame6hPeakSet':sum(parse_bins(v)==p6 for v in a.peak6hBins),
        'commonPeakHours4h6h':'|'.join(map(str,sorted(h4&h6))),
        'years4h6hPeakHaveAnyOverlap':int(a.peakWindowsHaveOverlap.sum()),
        'interpretation':'정점 포함 횟수는 동률 포함; 완전히 동일한 최다 구간 집합 횟수를 별도 제공'})
csv('selected-name-time-peak-stability.csv',peak_stability)
print('time',len(timecells),flush=True)

# Complete-17 time sensitivity to processing conditions is separately identified;
# no claim is made that excluded records' time patterns have been verified here.
processing_time=[]
selected_all=f[pd.MultiIndex.from_frame(f[[D,N]]).isin(CASES)&f[U].ne('벌집제거')]
for scope in 'ABC':
    selected_scope=selected_all if scope=='A' else selected_all[selected_all[P].eq('정상')]
    if scope=='C':
        selected_scope=selected_scope[~selected_scope[U].isin(['업무운행','훈련출동','구급차소독'])]
    for (district,name),g in selected_scope.groupby([D,N]):
        selectors=[('전체','',g)]+[(t,'',q) for t,q in g.groupby(T)]+[(t,u,q) for (t,u),q in g.groupby([T,U])]
        for t,u,q in selectors:
            for y in [0,*YEARS]:
                v=q if y==0 else q[q.year.eq(y)]
                if len(v)==0:
                    continue
                h4=(v.hour//4).value_counts().reindex(range(6),fill_value=0)
                h6=(v.hour//6).value_counts().reindex(range(4),fill_value=0)
                processing_time.append({'district':district,'rawDong':name,'type':t,'subtype':u,
                    'stage':'complete17','scope':scope,'year':y,'count':len(v),
                    'peak4hBins':'|'.join(map(str,h4[h4.eq(h4.max())].index)),
                    'peak6hBins':'|'.join(map(str,h6[h6.eq(h6.max())].index)),
                    'morning08to11Count':int(v.hour.between(8,11).sum()),
                    'morning08to11Share':float(v.hour.between(8,11).mean()),
                    'evening20to23Count':int(v.hour.between(20,23).sum()),
                    'evening20to23Share':float(v.hour.between(20,23).mean()),
                    'daytime08to19Share':float(v.hour.between(8,19).mean())})
csv('selected-name-time-processing-sensitivity.csv',processing_time)

dashboardpath=checked(R/'web/final/data/dashboard.json')
pop_manifest_path=checked(PRE/'population/manifest.json')
pop_manifest=json.loads(pop_manifest_path.read_text(encoding='utf8'))
assert sha(dashboardpath)==pop_manifest['dashboard']['sha256']
checks.append('dashboard population hash matches prior all101-age MOIS verification manifest')
dashboard=json.loads(dashboardpath.read_text(encoding='utf8'))
pop={ (int(p['year']),p['code']):p for p in dashboard['population'] }
links={(int(p['year']),p['district'],p['rawDong']):p for p in dashboard['rawRegions'] if p['scope']=='C'}
poprows=[]; ages=[]; linkrows=[]
for district,name in CASES:
    for y in YEARS:
        link=links.get((y,district,name))
        assert link is not None, (district,name,y)
        codes=link['candidateCodes']
        linkrows.append({'district':district,'rawDong':name,'year':y,'candidateCount':len(codes),
            'candidateCodes':'|'.join(codes),'linkStatus':link['linkStatus'],'geographyConfirmed':link['geographyConfirmed']})
        for code in codes:
            p=pop.get((y,code))
            if p is None:
                poprows.append({'district':district,'rawDong':name,'year':y,'candidateCode':code,'populationAvailable':False})
                continue
            assert p['district']==district and sum(p['ages'])==p['total'] and len(p['ages'])==101
            row={'district':district,'rawDong':name,'year':y,'candidateCode':code,'candidateName':p['name'],
                 'candidateCount':len(codes),'populationAvailable':True,'geographyConfirmed':False,
                 'referenceDate':p['referenceDate'],'residentTotal':p['total']}
            for band,lo,hi in [('0_14',0,15),('15_39',15,40),('40_64',40,65),('65plus',65,101)]:
                count=sum(p['ages'][lo:hi]); row['residents_'+band]=count; row['share_'+band]=count/p['total']
            poprows.append(row)
            for age,count in enumerate(p['ages']):
                ages.append({'district':district,'rawDong':name,'year':y,'candidateCode':code,'candidateName':p['name'],
                    'age':age,'age100Means':'100세 이상' if age==100 else '', 'count':count,'residentTotal':p['total'],
                    'share':count/p['total'],'geographyConfirmed':False})
csv('selected-name-population-links.csv',linkrows)
csv('selected-name-candidate-resident-background.csv',poprows)
csv('selected-name-candidate-all101ages.csv',ages)
checks.append('Selected-name candidate population: all101 ages sum to official resident totals; candidate populations never pooled')
inputs.append({'path':Path(__file__).relative_to(R).as_posix(),'sha256':sha(Path(__file__)),'priorInputHashMatch':None})
outputs=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(O.glob('*')) if p.name!='manifest.json']
dump('manifest.json',{'inputs':inputs,'primaryCount':len(x),'allComplete17':len(f),'districts':16,'rawNames':194,
     'typeSubtypeCombinations':70,'selectedNames':CASES,'checks':checks,'outputs':outputs,'pandasVersion':pd.__version__,
     'authorChecksOnly':True,'independentVerification':'Separate verifier required; not claimed by this script.'})
print('COMPLETE',O,flush=True)
