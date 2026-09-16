"""Independent stdlib verification of the new monthly/leave-one-year aggregates."""
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from datetime import date
import csv,gzip,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/temporal';V=O.parent/'verification';V.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
d=load(O/'temporal-transfer.json');cat=load(R/'data/processed/후속입증-20260916/analysis/all-region-followup.json')['catalogue']
key=lambda r:(r['district'],r['rawDong'],r['type'],r['subtype'])
crows={key(r):r for r in cat if r['scope']=='C'}
cnt=Counter();ledger=Counter();domains={(r['type'],r['subtype']) for r in crows.values()}
for y in range(2020,2025):
 p=R/f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{y}.csv.gz'
 with gzip.open(p,'rt',encoding='utf-8-sig',newline='') as f:
  for r in csv.DictReader(f):
   ledger['complete']+=1
   if r['PRCS_RSLT_SE_NM']!='정상' or r['EMRG_RSCU_CLSF_NM'] in ['업무운행','훈련출동','구급차소독']:continue
   ledger['C']+=1
   k=(r['CLMTY_SGG_NM'],r['CLMTY_EMD_NM'],r['EMRG_RSCU_ASSRT_NM'],r['EMRG_RSCU_CLSF_NM'])
   if k[2:] not in domains:continue
   assert k in crows
   t=r['DCLR_DT'].strip();assert int(t[:4])==y
   cnt[k+(y,int(t[4:6]))]+=1;ledger['focus']+=1
assert dict(ledger)=={'complete':704689,'C':574662,'focus':41720}
def days(y,m):return (date(y+(m==12),m%12+1,1)-date(y,m,1)).days
def maxima(ns,ds):
 if not sum(ns):return []
 rates=[Fraction(n,dd) for n,dd in zip(ns,ds)];return [i for i,x in enumerate(rates) if x==max(rates)]
checks=0
for r in d['profiles']:
 k=key(r)
 for w in r['windows']:
  ns=[sum(cnt[k+(y,m)] for y in w['years']) for m in range(1,13)]
  ds=[sum(days(y,m) for y in w['years']) for m in range(1,13)]
  assert ns==w['monthCounts'] and ds==w['monthCalendarDays']
  assert all(abs(n/dd-a)<1e-12 for n,dd,a in zip(ns,ds,w['monthPerCalendarDay']))
  assert [i+1 for i in maxima(ns,ds)]==w['topMonths']
  seasons={'봄':[3,4,5],'여름':[6,7,8],'가을':[9,10,11],'겨울':[1,2,12]}
  sn=[sum(ns[m-1] for m in months) for months in seasons.values()];sd=[sum(ds[m-1] for m in months) for months in seasons.values()]
  assert sn==w['seasonCounts'] and sd==w['seasonCalendarDays']
  assert [list(seasons)[i] for i in maxima(sn,sd)]==w['topSeasons'];checks+=1
 assert r['leaveOneMonthExact']==sum(w['topMonths']==r['topMonths'] and bool(r['topMonths']) for w in r['windows'][6:])
 assert r['leaveOneSeasonExact']==sum(w['topSeasons']==r['topSeasons'] and bool(r['topSeasons']) for w in r['windows'][6:])
group=defaultdict(list)
for r in cat:group[key(r)].append(r)
stable={k for k,rr in group.items() if len(rr)==3 and all(x['repeatedBefore'] and x['repeatedAfter'] and not x['directionReversal'] for x in rr)}
assert len(stable)==325
strata=[]
for threshold in [1,5,10,20]:
 pp=[r for r in d['profiles'] if key(r) in stable and r['minimumAnnual']>=threshold]
 strata.append({'minimumAnnual':threshold,'combinations':len(pp),'monthSameAllFiveLeaveOut':sum(r['leaveOneMonthExact']==5 for r in pp),'seasonSameAllFiveLeaveOut':sum(r['leaveOneSeasonExact']==5 for r in pp)})
(O/'selection_stable_temporal.json').write_text(json.dumps({'population':'previous 325 selection-stable combinations, C-scope temporal profiles','notClaimed':'Month/season selection-before-after robustness; future prediction or causal effect','strata':strata},ensure_ascii=False,indent=2),encoding='utf-8')
out={'status':'pass','method':'independent csv/gzip streaming and datetime month lengths; exact rational maxima','ledger':dict(ledger),'verifiedWindows':checks,'profiles':len(d['profiles']),'newMonthlyInputSHA256':hashlib.sha256((O/'temporal-transfer.json').read_bytes()).hexdigest(),'selectionStableStrata':strata}
(V/'temporal-independent.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
