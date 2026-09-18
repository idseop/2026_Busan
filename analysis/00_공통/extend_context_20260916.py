"""Extend verified commerce snapshots and living-population backgrounds, without causal joins."""
from pathlib import Path
import json,hashlib,zipfile,io
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];O=R/'data/processed/통합완성-20260916/context';O.mkdir(parents=True,exist_ok=True)
def dump(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csv(n,f):f.to_csv(O/n,index=False,encoding='utf-8-sig')
dump('specification.json',{'fixedBeforeAggregation':'2026-09-16','commerce':'2020–24全20分기 부산/16구군/모든법정동. 필수식별·지역·분류공란행만분리. 원ZIP멤버검산. 업소ID중복자동삭제금지. 코드+명칭대중분류사전해시가동일할때만동일버전추세. 분류변경임의매핑금지. 업소목록변화≠개폐업.','living':'2023–24 24개월 공통코드 검증. 주거/직장/방문각각 월원값/동일가중연평균. 시간/연령파일교차안함.2025별도현재배경이며119기간연장금지.','geography':'법정동상권과행정동생활인구를직접합치지않음. 기존신고명후보코드만개별연결.','questions':['상권구성은분기선택에따라얼마나달라지는가','같은신고동명후보들의생활인구정점은2023/24에도다른가','2025배경변화가과거신고추세의증거가아님을어떻게표시할까']})
audits=[];major=[];totals=[];dictionaries=[];previous=None;idchanges=[]
required=['상가업소번호','시도코드','시군구코드','시군구명','법정동코드','법정동명','상권업종대분류코드','상권업종대분류명','상권업종중분류코드','상권업종중분류명']
files=sorted((R/'data/raw/상권과거').glob('*.csv'));assert len(files)==20
for p in files:
 date=p.name[:8];f=pd.read_csv(p,dtype=str,keep_default_na=False)
 miss=f[required].apply(lambda x:x.str.strip().eq('')).any(axis=1);outside=f['시도코드'].ne('26');use=f.loc[~miss&~outside].copy()
 duplicate=int(use['상가업소번호'].duplicated().sum());assert duplicate==0
 assert use['시군구코드'].nunique()==16 and (use['법정동코드'].str[:5]==use['시군구코드']).all()
 dictionary=sorted(map(tuple,use[required[6:]].drop_duplicates().values.tolist()))
 sig=hashlib.sha256(json.dumps(dictionary,ensure_ascii=False).encode()).hexdigest()[:12]
 zp=p.parent/f'SEMAS_shops_{date}_original.zip'
 def find_member(blob,prefix=''):
  with zipfile.ZipFile(blob) as z:
   for n in z.namelist():
    try:display=n.encode('cp437').decode('cp949')
    except (UnicodeError,LookupError):display=n
    if n.endswith('.csv') and '부산' in display:return prefix+display,hashlib.sha256(z.read(n)).hexdigest()
   for n in z.namelist():
    if n.endswith('.zip'):
     found=find_member(io.BytesIO(z.read(n)),prefix+n+'::')
     if found:return found
 member,inner=find_member(zp)
 assert inner==sha(p)
 audits.append(dict(snapshot=date,input=str(p.relative_to(R)),sha256=sha(p),zipMember=member,zipMemberSha256=inner,rows=len(f),included=len(use),missingRequired=int(miss.sum()),outsideBusan=int(outside.sum()),excluded=int((miss|outside).sum()),duplicateIds=duplicate,districts=16,lawDongs=use['법정동코드'].nunique(),observedDictionarySignature=sig,columns=list(f.columns)))
 dictionaries.extend([dict(snapshot=date,signature=sig,majorCode=a,majorName=b,middleCode=c,middleName=d) for a,b,c,d in dictionary])
 for level,keys in [('busan',[]),('district',['시군구코드','시군구명']),('lawDong',['시군구코드','시군구명','법정동코드','법정동명'])]:
  groups=[((),use)] if not keys else use.groupby(keys,dropna=False)
  for key,g in groups:
   attrs=dict(zip(['districtCode','district','lawDongCode','lawDong'],key)) if keys else {}
   row={'snapshot':date,'year':int(date[:4]),'quarter':int(date[4:6])//3,'level':level,'dictionarySignature':sig,**attrs,'shops':len(g)};totals.append(row)
   for (code,name),n in g.groupby(['상권업종대분류코드','상권업종대분류명']).size().items():major.append({**row,'categoryCode':code,'category':name,'shops':int(n),'denominatorShops':len(g),'sharePct':100*n/len(g)})
 ids=set(use['상가업소번호'])
 if previous:idchanges.append(dict(previous=previous[0],snapshot=date,intersection=len(ids&previous[1]),newToFile=len(ids-previous[1]),absentFromFile=len(previous[1]-ids),meaning='등록목록ID출현차이; 실제개업폐업아님'))
 previous=(date,ids);print(date,len(use),sig,flush=True)
t=pd.DataFrame(totals);m=pd.DataFrame(major);csv('commerce-all-geographies-total.csv',t);csv('commerce-all-geographies-major.csv',m);csv('commerce-observed-classification.csv',pd.DataFrame(dictionaries));csv('commerce-id-snapshot-differences.csv',pd.DataFrame(idchanges));dump('commerce-audit.json',audits)
for a in audits:
 for level in ['busan','district','lawDong']:assert int(m.loc[(m.snapshot==a['snapshot'])&(m.level==level),'shops'].sum())==a['included']
 assert a['rows']==a['included']+a['excluded']
# Comparisons preserve observed dictionaries instead of inventing a crosswalk.
comparisons=[]
for level in ['busan','district','lawDong']:
 x=t[t.level==level].copy();x['geo']=x.lawDongCode.fillna(x.districtCode).fillna('26');lookup={(z.geo,z.year,z.quarter):z for z in x.itertuples()}
 for z in x.itertuples():
  old=lookup.get((z.geo,z.year-1,z.quarter))
  if old is not None:comparisons.append(dict(level=level,geo=z.geo,snapshot=z.snapshot,previousSnapshot=old.snapshot,shops=z.shops,previousShops=old.shops,difference=z.shops-old.shops,sameObservedDictionary=z.dictionarySignature==old.dictionarySignature,meaning='같은분기목록규모비교; 개폐업아님'))
csv('commerce-same-quarter-year-comparison.csv',pd.DataFrame(comparisons))
den=t[['snapshot','level','districtCode','shops']].copy()
bus=m[m.level=='busan'][['snapshot','categoryCode','sharePct']].rename(columns={'sharePct':'busanSharePct'})
dist=m[m.level=='district'][['snapshot','districtCode','categoryCode','sharePct']].rename(columns={'sharePct':'districtSharePct'})
law=m[m.level=='lawDong'].merge(bus,on=['snapshot','categoryCode']).merge(dist,on=['snapshot','districtCode','categoryCode']);law['differenceFromBusanPP']=law.sharePct-law.busanSharePct;law['differenceFromDistrictPP']=law.sharePct-law.districtSharePct
csv('commerce-law-dong-comparisons.csv',law)
sens=law.groupby(['year','dictionarySignature','districtCode','district','lawDongCode','lawDong','categoryCode','category']).agg(quarters=('quarter','nunique'),minSharePct=('sharePct','min'),maxSharePct=('sharePct','max')).reset_index();sens['spreadPP']=sens.maxSharePct-sens.minSharePct;csv('commerce-quarter-sensitivity.csv',sens)

V=['평균주거인구수','평균직장인구수','평균방문인구수'];living=[];annual={};monthly={}
for code,kind,key,n in [('LP00003','hour','시간대',24),('LP00002','age','나이대',6)]:
 p=next((R/'data/raw/공간인구보완').glob(f'*{code}*.xlsx'));f=pd.read_excel(p,dtype=str);f['year']=f['기준년월'].str[:4].astype(int)
 assert not f.duplicated(['기준년월','행정동코드',key]).any() and not f.isna().any().any()
 for col in V:f[col]=pd.to_numeric(f[col]);assert (f[col]>=0).all()
 assert f.groupby(['기준년월','행정동코드']).size().eq(n).all()
 codesets={y:set(g['행정동코드']) for y,g in f.groupby('year')};assert len(codesets[2023]&codesets[2024])==205 and codesets[2023]==codesets[2024]
 for y in [2023,2024,2025]:assert f[f.year==y]['기준년월'].nunique()==12
 groupkeys=['year','행정동코드','행정동명',key]
 ann=f.groupby(groupkeys,as_index=False)[V].mean().merge(f.groupby(groupkeys,as_index=False)['기준년월'].nunique().rename(columns={'기준년월':'observedMonths'}),on=groupkeys)
 ann['nameMissing']=ann['행정동명'].str.strip().eq('');annual[kind]=ann;monthly[kind]=f
 csv(f'living-{kind}-2023-2024-monthly.csv',f[f.year<=2024]);csv(f'living-{kind}-2025-separate-background.csv',f[f.year==2025]);csv(f'living-{kind}-annual-equal-month-means.csv',ann)
 living.append(dict(file=str(p.relative_to(R)),sha256=sha(p),rows=len(f),months=int(f['기준년월'].nunique()),common2023and2024Codes=205,rows2023=int((f.year==2023).sum()),rows2024=int((f.year==2024).sum()),rows2025=int((f.year==2025).sum()),missingNumericRows=0,blankNameRows=int(f['행정동명'].str.strip().eq('').sum()),codesByYear={str(y):len(c) for y,c in codesets.items()},partialYearCodes=ann.loc[ann.observedMonths.lt(12),['year','행정동코드','행정동명','observedMonths']].drop_duplicates().to_dict('records'),duplicateKeys=0))
metrics=[]
for (year,code,name),g in annual['hour'].groupby(['year','행정동코드','행정동명']):
 for col in V:
  maximum=float(g[col].max());peaks=g.loc[g[col]==maximum,'시간대'].tolist();mid=float(g.loc[g['시간대']=='00시',col].iloc[0]);noon=float(g.loc[g['시간대']=='12시',col].iloc[0]);metrics.append(dict(year=int(year),code=code,name=name,populationType=col,observedMonths=int(g.observedMonths.iloc[0]),nameMissing=bool(g.nameMissing.iloc[0]),peakHours='|'.join(peaks),maximum=maximum,midnight=mid,noon=noon,noonToMidnight=noon/mid if mid else None))
metrics=pd.DataFrame(metrics);csv('living-all205-yearly-hour-metrics.csv',metrics)
met=metrics[metrics.year==2024].merge(metrics[metrics.year==2023],on=['code','name','populationType'],suffixes=('2024','2023'));met['peakSetSame']=met.peakHours2024==met.peakHours2023;met['noonChange']=met.noon2024-met.noon2023;csv('living-2023-2024-comparison.csv',met)
db=json.loads((R/'web/final/data/dashboard.json').read_text(encoding='utf-8'));links=[]
for row in db['rawRegions']:
 if row['year'] not in [2023,2024] or row['scope']!='C':continue
 for code in row['candidateCodes']:links.append(dict(year=row['year'],district=row['district'],rawDong=row['rawDong'],candidateCode=code,candidateCount=len(row['candidateCodes']),livingAvailable=code in set(annual['hour']['행정동코드']),receiptLocationConfirmed=False))
csv('living-raw-name-candidate-links.csv',pd.DataFrame(links))

plt.rcParams.update({'font.family':'Malgun Gothic','font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False})
def plot_save(fig,name):
 for e in ['png','svg']:fig.savefig(O/f'{name}.{e}',dpi=170,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(13,8));fig.subplots_adjust(hspace=.45,bottom=.15)
for ax,dong in zip(axs.flat,['부전동','대연동','광안동','신평동']):
 g=t[(t.level=='lawDong')&(t.lawDong==dong)].sort_values('snapshot');ax.plot(range(len(g)),g.shops,'o-',color='#147d82');ax.set_title(dong+' · 분기 등록목록');ax.set_xticks([0,4,8,12,16,19],['20.03','21.03','22.03','23.03','24.03','24.12']);ax.set_ylabel('업소 등록행');ax.grid(alpha=.15)
fig.suptitle('상권 배경의 20개 분기: 목록 규모 변화는 개폐업 실적이 아니다',fontsize=17);fig.text(.12,.04,'각 분기는 별도 목록이다. 동일 업소를 기간 간 합산하지 않으며 조사구간의 업소수로 배정하지 않는다.',fontsize=10);plot_save(fig,'commerce-20quarter-background')
fig,axs=plt.subplots(1,2,figsize=(12,5));fig.subplots_adjust(bottom=.25,top=.79)
for ax,name in zip(axs,['부산진구 부전1동','부산진구 부전2동']):
 for y,color in [(2023,'#193d49'),(2024,'#147d82'),(2025,'#be7135')]:
  g=annual['hour'][(annual['hour'].year==y)&(annual['hour']['행정동명']==name)].sort_values('시간대');assert len(g)==24;ax.plot(range(24),g['평균방문인구수'],label=str(y)+(' 별도 배경' if y==2025 else ''),color=color)
 ax.set_title(name);ax.set_xticks([0,6,12,18,23]);ax.set_ylabel('명 · 월별 일평균의 12개월 평균');ax.grid(alpha=.15)
axs[0].legend(fontsize=9);fig.suptitle('같은 부전동 명칭 안의 서로 다른 시간별 방문 배경',fontsize=17);fig.text(.1,.05,'행정동 후보 개별 비교 · 2025는 신고 분석기간 밖의 배경 · 방문자는 신고 대상자·시장 이용자 수가 아니다.',fontsize=10);plot_save(fig,'living-hour-years')
fig,axs=plt.subplots(1,2,figsize=(12,5));fig.subplots_adjust(bottom=.25,top=.79)
for ax,name in zip(axs,['부산진구 부전1동','부산진구 부전2동']):
 g=monthly['hour'][(monthly['hour']['행정동명']==name)&(monthly['hour']['시간대']=='12시')].sort_values('기준년월');ax.plot(range(36),g['평균방문인구수'],color='#147d82');ax.axvspan(23.5,35.5,color='#be7135',alpha=.12);ax.set_title(name+' · 12시 방문 배경');ax.set_xticks([0,6,12,18,24,30,35],['23.01','23.07','24.01','24.07','25.01','25.07','25.12']);ax.grid(alpha=.15)
fig.suptitle('월별 배경을 보존해 연평균에 가려진 변동을 확인',fontsize=17);fig.text(.1,.05,'단위: 제공 월별 일평균 명 · 음영은 2025 별도 배경 · 전월 산정 정의로 신고월과 완전 동시성을 주장하지 않는다.',fontsize=10);plot_save(fig,'living-monthly-background')
profiles=metrics[metrics.name.isin(['부산진구 부전1동','부산진구 부전2동']) & metrics.populationType.eq('평균방문인구수')].to_dict('records')
summary={'period':'상권2020–24 20분기; 생활2023–24+2025별도','commerceAudit':audits,'observedClassificationSignatures':sorted(set(a['observedDictionarySignature'] for a in audits)),'dictionaryCaution':'관측코드·이름 사전 동일성일 뿐 과거분류제도 불변을 입증하지 않음. 원파일 제공분류 그대로 사용.','livingAudit':living,'livingExampleProfiles':profiles,'livingPeakSetStableCounts':met.groupby('populationType').peakSetSame.sum().astype(int).to_dict(),'candidateLinks':len(links),'limits':['업소변화≠개폐업·보행량','원문신고를법정/행정동내특정구간으로배정안함','생활인구는월일평균동일가중;24시간·3유형합산안함','2025는배경만;사건추세연장안함','2025신규코드2644059000은이름공란·10개월;observedMonths별도제공','시간×연령교차없음'],'sourceMetadataReuse':['data/processed/후속입증-20260916/commerce/semas-official-metadata.html','data/processed/후속입증-20260916/living/official-hour-metadata.json','data/processed/후속입증-20260916/living/official-age-metadata.json']}
dump('summary.json',summary);dump('validation.json',{'pass':True,'commerceSnapshots':20,'ledgerAndAllGeographyTotalsMatch':True,'zipMemberHashMatches':True,'shopIdUniqueness':True,'livingCommon2023and2024Codes':205,'livingNoMissingNumericOrDuplicate':True,'living2025BlankNameCode':'2644059000','living2025PartialYearMonths':10,'noHoursOrPopulationTypesSummed':True})
print(json.dumps(profiles,ensure_ascii=False));print('complete',flush=True)

# Post-aggregation evidence and documentation, reproducible from exported tables.
ag=pd.read_csv(O/'living-age-annual-equal-month-means.csv',dtype={'행정동코드':str})
ad=ag[ag.year==2024].merge(ag[ag.year==2023],on=['행정동코드','행정동명','나이대'],suffixes=('2024','2023'))
for v in V:ad[v+'差']=ad[v+'2024']-ad[v+'2023']
csv('living-age-2023-2024-comparison.csv',ad)
assert len(ad)==205*6
su=json.loads((O/'summary.json').read_text(encoding='utf-8'))
met=pd.read_csv(O/'living-2023-2024-comparison.csv');assert len(met)==205*3
su['conclusions']=['보유20분기의 관측 대·중분류 코드/명칭 사전은 동일하다. 파일에 없는 개편을 가정해 강제변환하지 않았고 실제 과거 제도불변도 주장하지 않는다.','부전1동 방문 정점14시와 부전2동19시는2023·2024 모두 유지. 같은 신고동명을 단일 활동시간으로 정하는 대신 행정동 후보별 배경을 분리할 근거가 강화됐다.','2024.9→12 부산목록143964→161440은 같은분류에서도목록규모가크게바뀜을 보여준다. 시장 이용량 또는 창폐업으로 환산하지 않는다.','2025곡선은 현재배경으로만따로제시하며2020–24신고추세와연장결합하지 않는다.']
su['metadataHashes']={s:sha(R/s) for s in su['sourceMetadataReuse'] if (R/s).exists()}
dump('summary.json',su)
(O/'results.md').write_text('''# 상권·생활인구 시계열 확장 결과

## 새로 확인한 내용

보유한 상권2020~2024년20분기 전체를 읽어 부산,16구·군,파일에 등장하는 모든 법정동의 업소 수와 대분류 구성을 계산했다. 법정동별 업종 비중은 같은 분기의 소속 구와 부산 비중에 비교했다. 동일 분기의 전년 비교와 같은 해 분기별 구성비 범위도 제공한다.

이번 입력20개에서 실제 관측된 대·중분류 코드·명칭 사전은 모두 동일했다. 초기 과거ZIP은 중첩ZIP이고 일부ZIP파일명은CP437/CP949해석이 필요했다. 내부 부산CSV까지 찾아 현재CSV와SHA256이 일치함을 검증했다. 따라서 파일 밖의 분류 개편을 임의로 적용하지 않았다. 다만 관측 사전이 같다고 실제 과거 분류제도와 등록범위가 불변이었다는 뜻은 아니다. 코드를 다른 분류에 강제 매핑하지 않았다.

부산 목록은2020년3월144,753행,2024년9월143,964행,12월161,440행이다. 2024년9→12월은 기존ID135,896개가 함께 나타나고,새 파일에25,544개가 나타나며8,068개가 사라졌다. 이는 파일 사이 등록ID출현 차이일 뿐 실제 개업·폐업이 아니다. 같은분류체계에서도 목록 변화가 크므로 한 분기의 업소 수를 현재 보행량·사고 노출량으로 쓰지 않는다.

생활인구는2023·2024년205개 행정동 코드가 모두 일치하며 시간24개·연령6개 키와 월12개를 각각 확인했다.2025는 별도 배경으로 저장했다.2023~24시간원값118,080행,연령29,520행,2025시간59,280행·연령14,820행이다.2025년1~2월205코드,3~12월206코드이며 새 코드2644059000은 제공 명칭이 공란이고10개월만 관측된다. 명칭을 임의로 채우거나 기존 신고동 후보에 연결하지 않았다. 각 유형의 연간 값은 실제 관측월 동일가중 평균이며 observedMonths를 함께 제공한다.2023~24모든코드와 그림의 부전1·2동은12개월,2025신규코드만10개월이다. 시간과 연령파일을 교차하지 않았다.

부전1동 방문 곡선의 정점14시와 부전2동19시는2023·2024에 공통이다.12시/00시 비율은 부전1동3.10→3.33,부전2동1.29→1.35다. 기존2024한해 결과가2023에도 같은 정점을 보이므로, 같은 ‘부전동’ 접수명에 단일 시간 배경을 적용하면 안 된다는 판단이 강화된다. 이는 교육·안전 안내에서 후보 행정동별 현장 맥락을 분리할 이유이며, 신고 발생시간의 원인 또는 인력 배치시간의 답은 아니다.

## 서비스 판단에 반영할 범위

- 상권은 단일분기 수치만 제시하지 않고 같은 분기·다른 분기의 범위를 함께 제공할 수 있다. 법정동전체 목록을 특정 시장·정비구간 업소로 표시하지 않는다.
- 주민등록 배경만으로 보이지 않는 주거·직장·방문 시간 차이는 후보행정동별로 유지한다. 부전1·2동의 서로 다른 정점이 두 해에서 반복되므로 두 후보를 합쳐 하나의 방문곡선으로 안내하지 않는다.
-2025자료가 있어도 신고 분석을2025년으로 연장하거나 현재사고 상황처럼 보이지 않게 한다. 기존 사업2025~26의 맥락을 읽는 별도 배경이다.
- 등록업소·생활인구와 신고의 동반 양상만으로 시설 부족·인과·피해 감소를 주장하지 않는다. 실제 보행량·동일구간·이용실적이 필요한 판단은 기존 보류를 유지한다.

## 출력과 재현

`commerce-all-geographies-total.csv`, `commerce-all-geographies-major.csv`는 전체 공간단위 집계다. `commerce-law-dong-comparisons.csv`에는 해당 분모·구와부산구성비·차이(%p)가 있다. `commerce-same-quarter-year-comparison.csv`와 `commerce-quarter-sensitivity.csv`는 연도·분기 민감도다. 업소ID는 원자료감사에만 사용하며 공개 집계에 실지 않는다.

`living-*-2023-2024-monthly.csv`는 월원값, `living-*-2025-separate-background.csv`는 별도2025배경, `living-*-annual-equal-month-means.csv`는 동일가중 연간곡선이다. `living-2023-2024-comparison.csv`는205동×3유형의시간정점·정오배경비교, `living-age-2023-2024-comparison.csv`는205동×6연령대의각유형비교다. 후보코드는 `living-raw-name-candidate-links.csv`에 개별 보존하며 신고를 배분하지 않았다.

기본코드: `analysis/00_공통/extend_context_20260916.py`. 원본 수정 없음. 원시집계와ZIP해시·분모·결측·중복·합계 검산은 `commerce-audit.json`, `summary.json`, `validation.json`에 있다. 공식 설명은 기존에 확보한 소상공인시장진흥공단15083033 및 부산광역시 생활인구15142760·15142761 메타를 재사용했다. 확보본해시는summary의metadataHashes에 기록했다.

이름 공란은 수치 결측과 별개로 기록했다. 2025 신규 코드의 10개월 평균을 12개월 평균과 동일 관측기간처럼 비교하지 않는다. 시간평균은 연간 실인원·일수가중 연평균이 아니다. 세 인구유형과24시간을 합산하지 않았다. 공식 전월 산정 정의로 신고월과 완전 동시라고 하지 않는다. 코드 일치는 경계 불변이나 추정오차 부재의 입증이 아니다.
''',encoding='utf-8')
dump('output-hashes.json',{p.name:sha(p) for p in O.iterdir() if p.is_file() and p.name!='output-hashes.json'})
