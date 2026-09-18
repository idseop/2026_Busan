"""Independent reaggregation. Does not import the analysis author's implementation."""
from pathlib import Path
import hashlib,json,calendar,sys
import re as regex
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/예방지원-근거분석-20260916/verification'
AUTHOR=OUT.parent/'analysis'
BASE=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'
D,N,T,U,R,DT='CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM','DCLR_DT'
YEARS=list(range(2020,2025))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True); checks=[]; sources=[]
 def ck(name,actual,expected):
  ok=actual==expected if not isinstance(expected,float) else abs(actual-expected)<1e-10
  checks.append({'check':name,'passed':bool(ok),'actual':actual,'expected':expected})
 p=AUTHOR/'action-patterns.json';a=json.loads(p.read_text(encoding='utf-8'));sources.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
 previous=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
 hashes={i['file']:i['sha256'] for i in previous['outputs']}
 fs=[]
 for y in YEARS:
  f=BASE/f'complete_17_{y}.csv.gz';ck(f'hash/{y}',sha(f),hashes[f.name]);sources.append({'path':str(f.relative_to(ROOT)),'sha256':sha(f)})
  x=pd.read_csv(f,usecols=[D,N,T,U,R,DT],dtype=str,keep_default_na=False)
  stamp=pd.to_datetime(x[DT].str.strip(),format='%Y%m%d%H%M%S',errors='raise');ck(f'year/{y}',bool(stamp.dt.year.eq(y).all()),True)
  x['year']=stamp.dt.year;x['hour']=stamp.dt.hour;x['weekday']=stamp.dt.dayofweek;x['month']=stamp.dt.month;x['date']=stamp.dt.normalize();fs.append(x.drop(columns=DT))
 f=pd.concat(fs,ignore_index=True)
 scopes={'A':f,'B':f.loc[f[R]=='정상'],'C':f.loc[(f[R]=='정상') & ~f[U].isin(['업무운행','훈련출동','구급차소독'])]}
 for s,g in scopes.items():ck(f'total/{s}',len(g),{'A':704689,'B':579412,'C':574662}[s]);ck(f'author_total/{s}',a['summary']['scopeTotals'][s],len(g))
 for row in a.get('domainProfiles',[]):
  g=scopes[row['scope']];available=pd.DatetimeIndex(g.date.unique());sub=g[(g[T]==row['type'])&(g[U]==row['subtype'])]
  prefix='domain/'+row['scope']+'/'+row['subtype']+'/'
  ck(prefix+'count',row['count'],len(sub));ck(prefix+'weekend_per_day',row['weekendPerObservedDay'],int(sub.weekday.ge(5).sum())/int((available.dayofweek>=5).sum()));ck(prefix+'weekday_per_day',row['weekdayPerObservedDay'],int(sub.weekday.lt(5).sum())/int((available.dayofweek<5).sum()))
 stpath=ROOT/'data/processed/완전행-분석적합성-20260915/stability/all_original_dong_subtype_sensitivity.csv';st=pd.read_csv(stpath);sources.append({'path':str(stpath.relative_to(ROOT)),'sha256':sha(stpath)})
 cross=pd.read_csv(AUTHOR/'selected_case_year_weekday_exact_hour.csv')
 annual=pd.read_csv(AUTHOR/'all_subtype_annual_scopes.csv')
 for s,g in scopes.items():
  re=g.groupby(['year',T,U]).size().rename('count').reset_index();old=annual[annual.scope==s].drop(columns='scope')
  key=['year',T,U];ck('annual_all_subtypes/'+s,re.sort_values(key).reset_index(drop=True).to_dict('records'),old.sort_values(key).reset_index(drop=True).to_dict('records'))
 for p in a['profiles']:
  ck(p['id']+'/not_beehive','벌집' in p['subtype'],False)
  for s,g in scopes.items():
   m=p['scopeProfiles'][s];local=(g[D]==p['district'])&(g[N]==p['rawDong']);typ=(g[T]==p['type'])&(g[U]==p['subtype']);sub=g[local&typ];rest=g[~local&typ]
   prefix=p['id']+'/'+s+'/'
   available=pd.DatetimeIndex(sorted(g.date.unique()))
   for group,got,tag in [(sub,m,''),(rest,m['restSameSubtype'],'rest/')]:
    vals={'count':len(group),'yearCounts':[int((group.year==y).sum()) for y in YEARS]}
    for col,field,ran in [('hour','hourCounts24',range(24)),('weekday','weekdayCounts7',range(7)),('month','monthlyCounts12',range(1,13))]:vals[field]=[int((group[col]==v).sum()) for v in ran]
    vals.update(weekendCount=int(group.weekday.ge(5).sum()),night22to06Count=int(((group.hour>=22)|(group.hour<6)).sum()),observedDays=len(available),calendarDays=sum(366 if calendar.isleap(y) else 365 for y in YEARS),weekdayDays7=[int((available.weekday==v).sum()) for v in range(7)],monthDays12=[int((available.month==v).sum()) for v in range(1,13)])
    for field,val in vals.items():ck(prefix+tag+field,got[field],val)
    for field,num in [('weekendShare',vals['weekendCount']),('night22to06Share',vals['night22to06Count'])]:ck(prefix+tag+field,got[field],num/len(group))
    for field,nums,dens in [('weekdayPerObservedDay7',vals['weekdayCounts7'],vals['weekdayDays7']),('monthPerObservedDay12',vals['monthlyCounts12'],vals['monthDays12'])]:
     for i,(num,den) in enumerate(zip(nums,dens)):ck(prefix+tag+field+str(i),got[field][i],num/den)
    ck(prefix+tag+'weekendPerObservedDay',got['weekendPerObservedDay'],vals['weekendCount']/sum(vals['weekdayDays7'][5:]))
    ck(prefix+tag+'weekdayPerObservedDay',got['weekdayPerObservedDay'],(len(group)-vals['weekendCount'])/sum(vals['weekdayDays7'][:5]))
   ck(prefix+'regionAllTypesCount',m['regionAllTypesCount'],int(local.sum()));ck(prefix+'regionSubtypeShare',m['regionSubtypeShare'],len(sub)/int(local.sum()))
   ck(prefix+'restAllTypesCount',m['restAllTypesCount'],int((~local).sum()));ck(prefix+'restRegionSubtypeShare',m['restRegionSubtypeShare'],len(rest)/int((~local).sum()))
   old=st.loc[(st.scope==s)&(st[D]==p['district'])&(st[N]==p['rawDong'])&(st[T]==p['type'])&(st[U]==p['subtype'])].iloc[0]
   stab=p['stability'][s];before=[int(old[f'core8_{y}']) for y in YEARS];after=[int(old[f'complete17_{y}']) for y in YEARS]
   ck(prefix+'before_counts',stab['core8YearCounts'],before);ck(prefix+'after_counts',stab['selected17YearCounts'],after);ck(prefix+'retention',stab['retention'],sum(after)/sum(before))
   ck(prefix+'directionReversal',stab['directionReversal'],bool((before[-1]-before[0])*(after[-1]-after[0])<0))
   ck(prefix+'repeat_before',stab['repeatsBefore'],all(v>0 for v in before));ck(prefix+'repeat_after',stab['repeatsAfter'],all(v>0 for v in after))
   ck(prefix+'eligible_repeat_direction',all(v>0 for v in before+after) and (before[-1]-before[0])*(after[-1]-after[0])>=0,True)
   obs=cross[(cross.caseId==p['id'])&(cross.scope==s)].drop(columns=['caseId','scope']);keys=['year','weekday','hour']
   rec=sub.groupby(keys).size().rename('count').reset_index();ck(prefix+'full_hour_cross',obs.sort_values(keys).reset_index(drop=True).to_dict('records'),rec.sort_values(keys).reset_index(drop=True).to_dict('records'))
 water_scopes={s:g[(g[T]=='구조')&(g[U]=='수난사고')] for s,g in scopes.items()}
 for row in a.get('waterCalendarComparison',[]):
  g=water_scopes[row['scope']]
  if row['region']!='부산':
   district,dong=row['region'].split('|');g=g[(g[D]==district)&(g[N]==dong)]
  years=YEARS if str(row['year'])=='all' else [int(row['year'])]
  g=g[g.year.isin(years)];inside=((g.month==7)&(g.date.dt.day>=4))|((g.month==8)&(g.date.dt.day<=30))
  ndays=sum(366 if calendar.isleap(y) else 365 for y in years);win=58*len(years)
  prefix='water/'+row['scope']+'/'+row['region']+'/'+str(row['year'])+'/'
  for k,v in {'count':len(g),'withinCurrentSummerWindow':int(inside.sum()),'outsideCurrentSummerWindow':int((~inside).sum()),'julyAugustCount':int(g.month.isin([7,8]).sum()),'withinWindowCalendarDays':win,'outsideWindowCalendarDays':ndays-win,'withinPerCalendarDay':int(inside.sum())/win,'outsidePerCalendarDay':int((~inside).sum())/(ndays-win)}.items():ck(prefix+k,row[k],v)
 catpath=AUTHOR/'all_region_prevention_catalogue.json'
 if catpath.exists():
  catalogue=json.loads(catpath.read_text(encoding='utf-8'))
  catalogue_counts=scopes['C'].groupby([D,N,T,U]).size().to_dict()
  for row in catalogue:
   n=int(catalogue_counts.get((row['district'],row['rawDong'],row['type'],row['subtype']),0))
   ck('catalogue/'+row['district']+'/'+row['rawDong']+'/'+row['subtype'],row['countC'],n)
 bridgepath=OUT.parent/'yearbooks/current-ems-bridge.json'
 if bridgepath.exists():
  import fitz
  bridge=json.loads(bridgepath.read_text(encoding='utf-8'));sources.append({'path':str(bridgepath.relative_to(ROOT)),'sha256':sha(bridgepath)})
  # Values separately read from the original rendered full-page tables by verifier.
  expected={2024:{'dispatches':190032,'transports':100869,'patients':101371,'severePatients':7428,'cardiacArrestPatients':2426},2025:{'dispatches':188760,'transports':97086,'patients':97470,'severePatients':7324,'cardiacArrestPatients':2334}}
  for row in bridge['rows']:
   for k,v in expected[row['year']].items():ck('yearbook/'+str(row['year'])+'/'+k,row[k],v)
  for item in bridge['evidence']:
   pdf=ROOT/f"data/raw/보완자료/소방청_119구급서비스통계연보_{item['edition']}.pdf";ck('yearbook/source/'+str(item['edition']),sha(pdf),item['sourceSha256'])
   with fitz.open(pdf) as doc:
    tokens=doc[item['pdfPage']-1].get_text().splitlines();start=tokens.index('부산')+1;end=tokens.index('대구',start)
    nums=[int(t.replace(',','')) for t in tokens[start:end] if regex.fullmatch(r'[0-9,]+',t.strip())]
    ck('yearbook/original/'+str(item['edition'])+'/'+item['kind'],item['busanValues'],nums)
   ck('yearbook/coverage/'+str(item['edition']),item['coverageYear'],item['edition']-1)
  ck('yearbook/separate_population','17컬럼 신고 집합과 다른 모집단' in bridge['scope'],True)
 responsepath=OUT.parent/'response/official-response.json'
 if responsepath.exists():
  response=json.loads(responsepath.read_text(encoding='utf-8'));sources.append({'path':str(responsepath.relative_to(ROOT)),'sha256':sha(responsepath)})
  official={v['id']:v for v in response['sources']}
  for sid,key,n in [('water_2026_plan','plannedVolunteers',250),('water_2026_result','recruitedVolunteers',191)]:
   src=official[sid];ck('official/'+sid+'/'+key,src['numbers'][key],n)
   plain=(responsepath.parent/(sid+'.txt')).read_text(encoding='utf-8');ck('official/saved_text/'+sid,bool(regex.search(r'\b'+str(n)+r'(?![0-9])',plain)),True)
   ck('official/no_service_gap/'+sid,src['confirmedGap'],False)
  ck('official/plan_year','2026' in official['water_2026_plan']['referenceDate'],True)
  ck('official/recruit_year','2026' in official['water_2026_result']['referenceDate'],True)
  ck('official/not_total_staff','전체 배치인원이 아님' in official['water_2026_result']['conditions'],True)
 poppath=OUT.parent/'population/case-population.json'
 if poppath.exists():
  pp=json.loads(poppath.read_text(encoding='utf-8'));dashboard=json.loads((ROOT/'data/processed/최종결과-20260915/dashboard.json').read_text(encoding='utf-8'))
  originals={(r['year'],r['code']):r for r in dashboard['population']};seen=set();profs={p['id']:p for p in a['profiles']}
  for row in pp['candidates']:
   prefix='population/'+row['caseId']+'/'+str(row['year'])+'/'+row['candidateCode']+'/'
   key=(row['caseId'],row['year'],row['candidateCode']);ck(prefix+'unique_case_year_code',key in seen,False);seen.add(key)
   old=originals[(row['year'],row['candidateCode'])];ck(prefix+'ages',row['ages'],old['ages']);ck(prefix+'all_ages',len(row['ages']),101);ck(prefix+'sum',sum(row['ages']),row['total']);ck(prefix+'source_total',row['total'],old['total'])
   ck(prefix+'year_end',row['referenceDate'],str(row['year'])+'-12-31');ck(prefix+'geography_not_confirmed',row['geographyConfirmed'],False)
   ck(prefix+'age_shares',all(abs(num/row['total']-share)<1e-10 for num,share in zip(row['ages'],row['ageShares'])),True)
   link=next(x for x in profs[row['caseId']]['populationLinks'] if x['year']==row['year']);ck(prefix+'correct_candidate',row['candidateCode'] in link['candidateCodes'],True);ck(prefix+'candidate_count',row['candidateCount'],len(link['candidateCodes']))
  manifest=json.loads((poppath.parent/'manifest.json').read_text(encoding='utf-8'))
  for item in manifest['outputs']:ck('population/hash/'+Path(item['path']).name,sha(ROOT/item['path']),item['sha256'])
 author_manifest=json.loads((AUTHOR/'manifest.json').read_text(encoding='utf-8'))
 for item in author_manifest['outputs']:
  path=ROOT/item['path'];ck('author_output_hash/'+path.name,sha(path),item['sha256'])
 ck('author_script_hash',sha(ROOT/author_manifest['script']),author_manifest['scriptSha256'])
 # Avoid huge duplicate output: retain dimensions and hashes for table equality checks.
 for c in checks:
  for key in ['actual','expected']:
   if isinstance(c[key],list) and len(c[key])>100:c[key]={'rows':len(c[key]),'sha256':hashlib.sha256(json.dumps(c[key],sort_keys=True,ensure_ascii=False).encode()).hexdigest()}
 result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checksCount':len(checks),'checks':checks,'inputs':sources,'verifierScriptSha256':sha(Path(__file__)),'authorCodeImported':False,'scope':'Independent selected-receipt reaggregation, not evidence of population risk or service unmet demand.'}
 (OUT/'independent_counts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['status'],len(checks))
 if result['status']!='passed':raise SystemExit(1)
def report_review():
 from html.parser import HTMLParser
 class Node:
  def __init__(self,tag,attrs=None):self.tag=tag;self.attrs=dict(attrs or []);self.children=[]
  def __getitem__(self,k):return self.attrs[k]
  def get_text(self,sep=' ',strip=False):return sep.join(c if isinstance(c,str) else c.get_text(sep,strip) for c in self.children)
  def find_all(self,tag=None,**attrs):
   found=[]
   for c in self.children:
    if isinstance(c,str):continue
    if (tag is None or c.tag==tag) and all(k in c.attrs if v is True else c.attrs.get(k)==v for k,v in attrs.items()):found.append(c)
    found.extend(c.find_all(tag,**attrs))
   return found
  def find(self,tag=None,**attrs):return next(iter(self.find_all(tag,**attrs)),None)
 class Parser(HTMLParser):
  def __init__(self):super().__init__();self.root=Node('root');self.stack=[self.root]
  def handle_starttag(self,tag,attrs):
   node=Node(tag,attrs);self.stack[-1].children.append(node)
   if tag not in ['meta','img','br','link','input','hr']:self.stack.append(node)
  def handle_endtag(self,tag):
   for i in range(len(self.stack)-1,0,-1):
    if self.stack[i].tag==tag:self.stack=self.stack[:i];break
  def handle_data(self,text):self.stack[-1].children.append(text)
 out=ROOT/'output/부산119-예방지원-분석결과-20260916';web=ROOT/'web/final/results'
 page=(out/'index.html').read_text(encoding='utf-8');md=(out/'분석결과.md').read_text(encoding='utf-8');parser=Parser();parser.feed(page);soup=parser.root;checks=[]
 def ck(name,ok):checks.append({'check':name,'passed':bool(ok)})
 a=json.loads((AUTHOR/'action-patterns.json').read_text(encoding='utf-8'))
 for p in a['profiles']:
  node=soup.find(id=p['id']);ck(p['id']+'/present',node is not None)
  text=node.get_text(' ',strip=True);c=p['scopeProfiles']['C']
  ck(p['id']+'/district_dong',p['district'] in text and p['rawDong'] in text)
  ck(p['id']+'/count',f"{c['count']:,}" in text)
  ck(p['id']+'/composition',f"{c['regionSubtypeShare']:.1%}" in text)
  ck(p['id']+'/weekend_difference_pp',f"{c['weekendShareDifferencePP']:+.1f}%p" in text)
  ck(p['id']+'/weekend_ratio',f"{c['weekendPerObservedDay']/c['weekdayPerObservedDay']:.2f}배" in text)
  ck(p['id']+'/retention',f"{p['stability']['C']['retention']:.1%}" in text)
  ck(p['id']+'/not_gap',any(s in text for s in ['미확인','확정하지 않았습니다']))
  ck(p['id']+'/service_jurisdiction','사상소방서 주택용 소방시설 원스톱 지원' not in text or p['district']=='사상구')
 for img in soup.find_all('img'):
  path=out/img['src'];ck('image/'+img['src'],path.exists())
 ck('six_figures',len(soup.find_all('img'))==6)
 for f in out.iterdir():
  if not f.is_file():continue
  if f.name=='index.html':
   webtext=(web/f.name).read_text(encoding='utf-8').replace('<a href="../index.html">지도 탐색</a>','<a href="분석결과.md">분석 보고서</a>');ck('web_copy/index_except_expected_navigation',webtext==page)
  elif f.name=='manifest.json':
   for folder in [out,web]:
    for name,h in json.loads((folder/f.name).read_text(encoding='utf-8')).items():ck('manifest/'+folder.name+'/'+name,sha(folder/name)==h)
  else:ck('web_copy/'+f.name,(web/f.name).exists() and sha(f)==sha(web/f.name))
 for link in soup.find_all('a',href=True):
  target=link['href']
  if target.startswith('#'):ck('anchor/'+target,soup.find(id=target[1:]) is not None)
  elif not regex.match(r'^https?://',target):ck('local_link/'+target,(out/target).exists())
 ck('no_raw_none',not regex.search(r'\bNone\b',soup.get_text()+' '+md))
 ck('correct_yearbook_edition','2025년 공식 연보의 부산 구급 출동은 188,760' not in md)
 ck('misleading_difference_pct_removed','차이는 59명, 계획 대비 76.4%' not in md)
 ck('not_busan_servicegap', '현재 자료로 확정한 주민의 서비스 미충족은 없습니다' in soup.get_text())
 ck('water_volunteer_period','자원봉사 활동기간이며 전체 수상구조 운영기간이 아닙니다' in soup.get_text())
 ck('not_risk','부산 전체 사건 위험률은 아닙니다' in soup.get_text())
 result={'status':'passed' if all(c['passed'] for c in checks) else 'failed','checksCount':len(checks),'checks':checks,'reportSha256':sha(out/'index.html'),'markdownSha256':sha(out/'분석결과.md'),'scope':'Independent content/number/link/copy review. Browser screenshots reviewed separately by root.'}
 OUT.mkdir(exist_ok=True,parents=True);(OUT/'report-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['status'],len(checks));print([c['check'] for c in checks if not c['passed']])
 if result['status']!='passed':raise SystemExit(1)
if __name__=='__main__':
 if '--report-only' in sys.argv:report_review()
 else:main()
