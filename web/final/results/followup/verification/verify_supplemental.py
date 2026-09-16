"""Independent raw-table checks of other authors' traffic, housing and services."""
from pathlib import Path
import json,csv,hashlib,zipfile,io,struct,zlib,re
import pandas as pd
import olefile
ROOT=Path(__file__).resolve().parents[4];BASE=ROOT/'data/processed/후속입증-20260916';OUT=Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
checks=[]
def ck(n,ok):checks.append({'name':n,'passed':bool(ok)})
def rows(p):return list(csv.DictReader(p.open(encoding='utf-8-sig')))
T=BASE/'traffic';H=BASE/'housing';S=BASE/'services'
for r in load(S/'snapshot-hashes.json'):ck('service source '+r['file'],hashlib.sha256((S/r['file']).read_bytes()).hexdigest()==r['sha256'])
for r in load(T/'source-manifest.json'):
 if 'file' in r:ck('traffic source '+Path(r['file']).name,hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256'])
matrix=load(T/'traffic-followup.json')['sites'];old=rows(ROOT/'data/processed/동별보완-추가근거-20260916/place/coverage_mois_all14_inspection_sites.csv')
ck('14 sites',len(matrix)==14)
for r,b in zip(matrix,old):
 for k,v in b.items():ck('inspection preserved '+r['place']+k,r[k]==v)
 ck('no current defect assertion '+r['place'],not r['currentlyUnimprovedConfirmed'] and not r['sameInterventionConfirmed'])
ck('122 short / 19 long',sum(int(r['shortTermItems']) for r in matrix)==122 and sum(int(r['longTermItems']) for r in matrix)==19)
# Manually transcribed from inspected official PDF67 and70, independently of author constants.
expected=[(9,1663.3,6,3,175.3,215.0,1.05,.86),(4,1104.4,3,1,208.1,231.5,1.33,1.19),(3,1034.4,1,2,278.2,305.,1.24,1.13),(4,1311.3,2,2,260.5,282.2,1.20,1.11)]
field=load(T/'bdi-field-study.json')
for r,e in zip(field['areas'],expected):
 got=tuple(r[k] for k in ['surveySegments','surveyLengthM','separatedSegments','unseparatedSegments','meanSecondsWithoutSuit','meanSecondsWithSuit','meanMetersPerSecondWithoutSuit','meanMetersPerSecondWithSuit'])
 ck('BDI table '+r['area'],got==e)
ck('BDI sample limitation','체험복' in field['sampleLimit'] and not field['causalClaimAllowed'] and not field['current2026ConditionConfirmed'])
clock=(T/'nampo-camera-2025.txt').read_text(encoding='utf-8')
ck('camera exact timing','09:00~21:00' in clock and '11:30~14:00' in clock and '남포사거리' in clock)
geo=load(T/'geoje-budget-evidence.json');geotext=(T/'yeonje-budget-fence-2024.txt').read_text(encoding='utf-8')
ck('geoje committee actual motion','무단횡단 방지 펜스 설치 3740만 원을 전액 삭감' in geotext and geo['committeeBudgetReductionWon']==37400000)
ck('geoje uncertain location retained',not geo['placementCertain'] and not geo['matches2023InspectionItems'])
manifest=load(H/'manifest.json');z=zipfile.ZipFile(ROOT/manifest['source']);ck('housing source hash',hashlib.sha256((ROOT/manifest['source']).read_bytes()).hexdigest()==manifest['sourceSha256'])
housing=pd.read_csv(H/'busan_housing_context_2024.csv',dtype=str,keep_default_na=False).set_index(['sgisCode','itemCode'])
for r in manifest['members']:
 b=z.read(r['member']);ck('zip member '+Path(r['member']).name,hashlib.sha256(b).hexdigest()==r['sha256'])
 if not r['member'].endswith('.csv'):continue
 raw=pd.read_csv(io.BytesIO(b),encoding='cp949',dtype=str,keep_default_na=False);raw=raw[raw['행정구역코드'].str.startswith('21')]
 for _,x in raw.iterrows():
  out=housing.loc[(x['행정구역코드'],x['통계항목'])]
  ck('housing raw cell '+x['행정구역코드']+x['통계항목'],out.rawValue==x['통계값'])
  number=pd.to_numeric(x['통계값'],errors='coerce');ck('housing null/numeric '+x['행정구역코드']+x['통계항목'],out.value=='' if pd.isna(number) else float(out.value)==float(number))
ck('housing separate metadata',manifest['statisticsYear']==2024 and manifest['boundaryDate']=='2025-06-30' and manifest['dongRows']==206)
audit=pd.read_csv(H/'housing_sum_audit.csv',dtype={'sgisCode':str});hv=housing.reset_index();hv['num']=pd.to_numeric(hv.value,errors='coerce')
for _,r in audit.iterrows():
 subset=hv[hv.sgisCode==r.sgisCode];types=subset[(subset.kind=='type')&(subset.itemCode!='ho_gb_006')];years=subset[subset.kind=='constructionYear']
 ck('housing published sum '+r.sgisCode,abs(types.num.sum()-r.housingTypesPublishedSum)<.01 and abs(years.num.sum()-r.constructionPublishedSum)<.01)
 ck('housing missing retained '+r.sgisCode,types.num.isna().sum()==r.missingHousingTypeCells and years.num.isna().sum()==r.missingConstructionCells)
# Extract HWP binary records afresh, comparing exact record sequence to saved text.
stationkeys={'기장소방서':'gijang','동래소방서':'dongnae','금정소방서':'geumjeong','부산진소방서':'busanjin'}
inspection=rows(S/'inspection-internal-rows.csv');summary=load(S/'inspection-analysis.json')
for station,key in stationkeys.items():
 path=S/(key+'-inspection202608.hwp');ole=olefile.OleFileIO(path);compressed=bool(ole.openstream('FileHeader').read()[36]&1);para=[]
 for name in ole.listdir():
  if name[0]!='BodyText':continue
  blob=ole.openstream(name).read();blob=zlib.decompress(blob,-15) if compressed else blob;pos=0
  while pos+4<=len(blob):
   header=int.from_bytes(blob[pos:pos+4],'little');pos+=4;n=header>>20
   if n==4095:n=int.from_bytes(blob[pos:pos+4],'little');pos+=4
   if header&1023==67:para.append(blob[pos:pos+n].decode('utf-16-le',errors='replace'))
   pos+=n
 text='\n'.join(para);saved=(S/(key+'-inspection202608.txt')).read_text(encoding='utf-8')
 # Windows write_text expanded source CR + joined LF into CRCRLF: compare
 # nonblank lines, retaining every actual cell and control character.
 ck('HWP independent extraction '+key,[s for s in text.splitlines() if s.strip()]==[s for s in saved.splitlines() if s.strip()])
 cells=[s.strip() for s in text.split('화재안전조사 결과 세부내역',1)[1].splitlines() if s.strip()]
 starts=[i for i,x in enumerate(cells) if x.isdigit()];rs=[r for r in inspection if r['station']==station]
 ck('HWP table rows '+key,len(starts)==len(rs))
 for i,r in enumerate(rs):
  chunk=cells[starts[i]+1:starts[i+1] if i+1<len(starts) else len(cells)];flags=[x for x in chunk if x in ['양호','불량','-']]
  ck('HWP statuses '+key+str(i),flags[:2]==[r['fire_facility_result'],r['escape_firewall_result']])
  ck('HWP correction '+key+str(i),('현지시정' in ' '.join(chunk))==(r['onsite_correction_recorded']=='True'))
  if r['dong_match']=='조사표 주소에 동명 명시':ck('dong in address '+key+str(i),r['dong'] in r['address_internal'])
  elif r['dong_match']=='조사표 대상명에 동명 명시':ck('dong in name '+key+str(i),r['dong'] in r['target_name'])
  else:ck('unconnected or explicit official '+key+str(i),not r['dong'] or bool(r['dong_match_source']))
  ck('no assumed correction completion '+key+str(i),r['correction_completion_verified']=='')
 sm=next(r for r in summary['stations'] if r['station']==station)
 bad=[r for r in rs if r['fire_facility_result']=='불량' or r['escape_firewall_result']=='불량']
 for field,value in [('listed_rows',len(rs)),('assessed_rows',sum(r['fire_facility_result']!='-' for r in rs)),('any_defect_rows',len(bad)),('any_defect_with_onsite_correction',sum(r['onsite_correction_recorded']=='True' for r in bad))]:ck('station '+key+field,sm[field]==value)
ck('inspection 132 /19 / 6 connected',len(inspection)==132 and sum(r['fire_facility_result']=='불량' or r['escape_firewall_result']=='불량' for r in inspection)==19 and sum(bool(r['dong']) for r in inspection)==6)
ananti=(S/'ananti-address.txt').read_text(encoding='utf-8')
ck('Ananti exact official address section','아난티 앳 부산 코브\n주소 : 부산광역시 기장군 기장읍 기장해안로 268-32' in ananti)
gijang=[r for r in inspection if r['dong']=='기장읍']
ck('Ananti inspection exact matching address',len(gijang)==1 and '268-32' in gijang[0]['address_internal'] and '아난티' in gijang[0]['target_name'])
ck('matched public table 6 rows 5 dong names',len(rows(S/'inspection-public-matched-dongs.csv'))==5 and sum(int(r['matched_inspection_rows']) for r in rows(S/'inspection-public-matched-dongs.csv'))==6)
result={'passed':sum(x['passed'] for x in checks),'failed':[x for x in checks if not x['passed']],'checks':checks,'scope':'원 HWP·주택 ZIP·교통 원표/해시 검토. outdoor 본인 작성분 제외. 현장 재조사 아님.'}
(OUT/'supplemental-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False));assert not result['failed']
