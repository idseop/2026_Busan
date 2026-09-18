"""Official place evidence, kept separate from 119 receipt and population totals."""
from pathlib import Path
import json,hashlib,re,urllib.request,datetime,math
import pandas as pd
import pymupdf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/place'
URLS={
 'koroad-codebook.xlsx':'https://opendata.koroad.or.kr/api/down/accidenthazard_codelist_down.jsp',
 'koroad-oldman-definition.html':'https://opendata.koroad.or.kr/api/selectOldmanDataSet.do',
 'koroad-child-definition.html':'https://opendata.koroad.or.kr/api/selectChildDataSet.do',
 'mois-page.html':'https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=105248',
 'mois-20231129.pdf':'https://www.mois.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_001230687mfxIHJ&fileSn=1',
 'bdi-active-aging.pdf':'https://data.bdi.re.kr/PDF/View.do?dir=report&path=RPT_00000000001&savename=20250716143831_71613',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
 OUT.mkdir(parents=True,exist_ok=True);sources=[]
 for name,url in URLS.items():
  p=OUT/name
  if not p.exists():
   with urllib.request.urlopen(url,timeout=40) as r:p.write_bytes(r.read())
  sources.append({'file':str(p.relative_to(ROOT)),'url':url,'sha256':sha(p),'bytes':p.stat().st_size,'retrievedDate':'2026-09-16','reusedSnapshot':True})
 codebook=pd.read_excel(OUT/'koroad-codebook.xlsx',sheet_name=0,dtype=str)
 codes={str(r.iloc[2]).strip():{'dataYear':2000+int(re.match(r'(\d+)년',r.iloc[1]).group(1)),'name':r.iloc[1]} for _,r in codebook.iterrows() if re.match(r'^\d+년',str(r.iloc[1]))}
 dump('official_year_code_mapping.json',codes)
 rawmanifest=json.loads((ROOT/'data/raw/교통안전/manifest.json').read_text(encoding='utf-8'))
 target_codes={'2647010200':('연제구','연산동'),'2629010600':('남구','대연동')}
 frames=[];checks=[]
 for m in rawmanifest:
  p=ROOT/m['file'];assert sha(p)==m['sha256'];sources.append({**m,'reusedOriginalHashMatches':True})
  f=pd.read_csv(p,encoding='cp949',dtype=str);f.columns=[x.strip() for x in f.columns]
  assert f['사고다발지id'].isin(codes).all()
  f['dataYear']=f['사고다발지id'].map(lambda x:codes[x]['dataYear']);f['category']='보행노인' if m['id']=='oldman' else '보행어린이'
  f['lawCode']=f['법정동코드'].str.strip();f['fid']=f['사고다발지fid'];f['sourceId']=f['사고다발지id'];f['spotName']=f['지점명']
  for src,dest in [('사고건수','accidents'),('사망자수','deaths'),('중상자수','severeInjuries'),('사상자수','casualties'),('경도','longitude'),('위도','latitude')]:f[dest]=pd.to_numeric(f[src],errors='raise')
  busan=f[f.lawCode.str.startswith('26')&f.dataYear.between(2020,2025)].copy()
  assert busan.fid.is_unique
  assert busan.longitude.between(128.7,129.4).all() and busan.latitude.between(34.8,35.6).all()
  for _,r in busan.iterrows():
   geom=json.loads(r['다발지역폴리곤']);assert geom['type'] in ['Polygon','MultiPolygon']
   polys=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
   assert all(len(poly[0])>=4 for poly in polys)
  checks.append({'source':m['id'],'nationalRows':len(f),'busan2020to2025Rows':len(busan),'duplicateFids':int(busan.fid.duplicated().sum()),'yearMapping':'downloaded official codebook; never id-prefix assumption'})
  frames.append(busan)
 allf=pd.concat(frames,ignore_index=True)
 cols=['category','dataYear','lawCode','sourceId','fid','spotName','accidents','casualties','deaths','severeInjuries','longitude','latitude','다발지역폴리곤']
 allf[cols].to_csv(OUT/'busan_taas_designated_sites_2020_2025.csv',index=False,encoding='utf-8-sig')
 target=allf[allf.lawCode.isin(target_codes)].copy()
 target[cols].to_csv(OUT/'yeonsan_daeyeon_taas_sites.csv',index=False,encoding='utf-8-sig')
 records=[]
 for _,r in target.iterrows():
  district,dong=target_codes[r.lawCode]
  assert district in r.spotName and dong in r.spotName
  records.append({'district':district,'rawDong':dong,**{k:(int(r[k]) if k in ['dataYear','accidents','casualties','deaths','severeInjuries'] else float(r[k]) if k in ['longitude','latitude'] else str(r[k])) for k in cols if k!='다발지역폴리곤'},'geometry':json.loads(r['다발지역폴리곤']),'linkStatus':'공식 법정동코드와 지점명 구군·동 일치; 119개별접수와 연결하지 않음'})
 for r in records:
  geom=r['geometry'];ring=geom['coordinates'][0] if geom['type']=='Polygon' else geom['coordinates'][0][0]
  distances=[math.hypot((x-r['longitude'])*111320*math.cos(math.radians(r['latitude'])),(y-r['latitude'])*111320) for x,y in ring]
  r['providedPolygonDiagnostic']={'minimumVertexDistanceM':min(distances),'maximumVertexDistanceM':max(distances),'method':'소범위 평면근사, 위도111320m/도·경도cos위도 보정. 측량 정확도 아님.','spatialOverlayAllowed':False,'reason':'공식 선정 반경과 제공 폴리곤·중심점의 거리 일치 미검증. 지도에는 제공 지점만 표시하고 반경 접근성·중첩 분석에는 사용하지 않음.'}
 doc=pymupdf.open(OUT/'mois-20231129.pdf');text=doc[3].get_text()
 assert '못골사거리 부근\n0\n3\n0\n3\n0\n0' in text
 assert '대연동못골시장 부근\n1\n0\n0\n0\n0\n0' in text
 (OUT/'mois-page-4.txt').write_text(text,encoding='utf-8');doc[3].get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(OUT/'mois-page-4.png')
 bdi=pymupdf.open(OUT/'bdi-active-aging.pdf');assert '못골사거리 부근\n0\n3\n0\n3\n0\n0' in bdi[51].get_text()
 sites=[]
 for name,prev,short,traffic in [('못골사거리 부근',0,3,3),('대연동못골시장 부근',1,0,0)]:
  matched=[r for r in records if r['category']=='보행노인' and r['spotName'].endswith('('+name+')')]
  assert matched
  sites.append({'place':name,'district':'남구','lawDong':'대연동','lawCode':'2629010600','inspectionPeriod':'2023-10-25~2023-11-10','publishedDate':'2023-11-29','previouslyImproved':prev,'shortTermImprovementItems':short,'trafficSafetyFacilityItems':traffic,'longTermItems':0,'inspectionSource':URLS['mois-page.html'],'inspectionPdfPage':4,'matchedOfficialTaasSites':matched,'matchingRule':'동일 남구·법정동코드, 괄호 안 지점명 완전일치. 반경·경계의 동일성이 아니라 장소명의 연결. 조사구역 원도면 미확보.','currentCompletionStatus':'미확인; 2023년 권고안이 2026년에도 미개선이라는 뜻이 아님','claimAllowed':'2023년 합동점검 당시 개선 필요 항목 확인' if short else '2023년 표에서 기개선 항목 확인; 신규 개선 필요로 분류하지 않음'})
 # Full Busan coverage, never treating a non-designated locality as zero accidents.
 relpath=ROOT/'data/processed/동대응-전체결측제외-20260915/linkage/official_busan_relations_with_dates.csv'
 relations=pd.read_csv(relpath,dtype=str,keep_default_na=False)
 dp=ROOT/'data/processed/최종결과-20260915/dashboard.json';dashboard=json.loads(dp.read_text(encoding='utf-8'))
 sources.extend([{'file':str(p.relative_to(ROOT)),'sha256':sha(p),'role':'existing official code-name relations / verified receipt name catalogue'} for p in [relpath,dp]])
 district_codes={p['districtCode'][:5]:p['district'] for p in dashboard['population']}
 allf['districtCode']=allf.lawCode.str[:5];allf['district']=allf.districtCode.map(district_codes)
 assert allf.district.notna().all() and len(district_codes)==16
 raw_names={(r['district'],r['rawDong']) for r in dashboard['rawRegions']}
 districtrows=[]
 for y in range(2020,2026):
  for dc,dn in sorted(district_codes.items()):
   for category in ['보행노인','보행어린이']:
    f=allf[allf.dataYear.eq(y)&allf.districtCode.eq(dc)&allf.category.eq(category)]
    districtrows.append({'dataYear':y,'districtCode':dc,'district':dn,'category':category,'designatedSiteRecords':len(f),'designatedLawDongCount':int(f.lawCode.nunique()),'zeroMeaning':'목록에 지정지점 없음; 사고0건 뜻하지 않음' if len(f)==0 else '공식 지정지점 기록 수; 사고건수 합계 아님'})
 lawrows=[]
 for (y,code,category),f in allf.groupby(['dataYear','lawCode','category']):
  dn=district_codes[code[:5]];rr=relations[relations['법정동코드'].eq(code)&relations['시군구명'].eq(dn)]
  names=sorted(set(rr['동리명'])-set(['']));matched=sorted(n for n in names if (dn,n) in raw_names)
  lawrows.append({'dataYear':int(y),'district':dn,'lawCode':code,'lawNameCandidates':names,'category':category,'designatedSiteRecords':len(f),'matchedReceiptRegionNames':matched,'matchingStatus':'구군·공식 법정동명과 접수 지역명 일치; 개별119사건 연계 아님' if matched else '접수 지역명 정확대응 미확정·구군만 연결','spatialGeographyConfirmed':False})
 inspection_specs=[('남구','대연동못골시장 부근'),('남구','못골사거리 부근'),('남구','남구종합사회복지관 부근'),('남구','용호종합사회복지관 부근'),('동구','부산진시장앞교차로 부근'),('부산진구','굿모닝성모안과의원 부근'),('사하구','한비전교회 부근'),('수영구','장대골삼거리 부근'),('수영구','사도행전교회 부근'),('연제구','거제시장 부근'),('연제구','부산광역시노인종합복지관'),('영도구','남항시장사거리 부근'),('중구','남포사거리 부근'),('해운대구','반송도서관교차로 부근')]
 inspection_all=[]
 for district,name in inspection_specs:
  match=re.search(re.escape(name)+r'\n(\d+)\n(\d+)\n(\d+)\n(\d+)\n(\d+)\n(\d+)',text);assert match,(district,name)
  prev,short,road,traffic,geometry,long=map(int,match.groups());assert short==road+traffic+geometry
  matches=allf[allf.district.eq(district)&allf.spotName.str.endswith('('+name+')')]
  lawcodes=sorted(matches.lawCode.unique().tolist());law_names=sorted(set(relations[relations['법정동코드'].isin(lawcodes)]['동리명'])-set(['']))
  inspection_all.append({'district':district,'place':name,'alreadyImproved':prev,'shortTermItems':short,'roadSafetyItems':road,'trafficSafetyItems':traffic,'geometryOtherItems':geometry,'longTermItems':long,'exactNamedTaasLawCodes':lawcodes,'lawNameCandidates':law_names,'mappingStatus':'동일 구군·지점명 대응' if lawcodes else '동 위치 미확정·구군만 대응','date':'2023-11-29','currentCompletion':'이 표로 현재 미완료를 판단하지 않음','sourcePdfPage':4})
 assert len(inspection_all)==14
 inspection_df=pd.DataFrame(inspection_all);inspection_df.to_csv(OUT/'coverage_mois_all14_inspection_sites.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(districtrows).to_csv(OUT/'coverage_all16_districts_2020_2025.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame(lawrows).to_csv(OUT/'coverage_law_dong_receipt_names.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame([r for r in districtrows if r['dataYear']==2025]).to_csv(OUT/'coverage_latest2025_districts.csv',index=False,encoding='utf-8-sig')
 pd.DataFrame([r for r in lawrows if r['dataYear']==2025]).to_csv(OUT/'coverage_latest2025_law_dongs.csv',index=False,encoding='utf-8-sig')
 dsum=inspection_df.groupby('district')[['alreadyImproved','shortTermItems','roadSafetyItems','trafficSafetyItems','geometryOtherItems','longTermItems']].sum()
 dsum.to_csv(OUT/'coverage_mois_district_item_sums.csv',encoding='utf-8-sig')
 assert sum(r['designatedSiteRecords'] for r in districtrows)==len(allf)==sum(r['designatedSiteRecords'] for r in lawrows)
 coverage={'meta':{'meaning':'16구군의 전체공식목록 점검. 지정지점수와사고건수를구별, 법정동과119접수지역명을동일경계로취급하지않음. 2025자료연도별도표시.','unlisted':'공식다발지역목록미지정; 사고없음 또는안전지역판정아님','population':'인구대비위험률 미산출','inspection':'14개 부산지점은2023합동점검대상,현재완료여부별도'},'districts':districtrows,'lawDongs':lawrows,'mois14':inspection_all,'inspectionTotals':{c:int(inspection_df[c].sum()) for c in ['alreadyImproved','shortTermItems','roadSafetyItems','trafficSafetyItems','geometryOtherItems','longTermItems']},'validation':{'allDistricts':16,'districtCategoryYearRows':len(districtrows),'designatedRowsReconciled':len(allf),'inspectionRows':14,'shortTermComponentsMatchEveryRow':True}}
 dump('coverage_all_busan.json',coverage)
 latest=[r for r in records if r['category']=='보행노인' and r['dataYear']==2025]
 payload={'meta':{'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'receiptAnalysisPeriod':'2020–2024','supportDataYears':[2020,2021,2022,2023,2024,2025],'officialDataYearMeaning':'연도 코드북상 자료연도. 2021년부터 노인 다발지역은 최근3년 사망·중상사고 선정; 연도별 합산·개선 전후 단순 비교 금지. 정확한 누적 시작일은 현재 코드북 미제공.','olderDefinition':'2021년 이후 반경100m 내 65세 이상 보행노인 사망·중상 사고5건 이상. 2020년까지 1년간 반경200m내3건(사망포함2건). 서로 같은 조건의 추세 아님.','childrenDefinition':'12세 이하 보행자 대상1년간 반경200m 내3건(사망포함2건).','geometry':'TAAS 공식 집계다발구역·중심점 EPSG4326; 개별환자·신고좌표 아님','denominator':'지정지점수만 합계가능. 사고건수는 중첩반경·누적기간 때문에 지점간/연도간 합산 금지. 지정되지 않은 지점=사고0 아님.','relationTo119':'119에서 원문지역을 골라 별도의 경찰 교통사고·현장점검 자료로 세부대상을 좁힘. 119교통신고를 고령보행사고로 재분류하지 않음.'},'inputReconciliation':checks,'officialSiteRecords':records,'latestOlderSites':latest,'inspectionComparison':sites,
  'result':{'confirmedHistoricalGap':'대연동 못골사거리 부근은 2023년 공식 합동점검에서 교통안전시설 단기개선3항목이 확인됨.','confirmedCurrentEvidence':'2025자료연도 TAAS에도 동일 법정동·동일지점명 목록이 존재함. 누적 사고기간 때문에 2023년 점검 후 발생사고만 뜻하지 않음.','proposal':'못골사거리 기존3항목의 이행·현재 상태를 확인해 미완료 또는 재발 항목에 한해 보완하는 후속점검 대상으로 특정. 신규 시설종류·인력규모는 지정하지 않음.','notClaimed':['2026현재 미개선 확정','과거 개선실패 또는 효과측정','119교통사고의 노인/보행자 연령추정','동 전체 위험도','시장과 사거리 지점 자동동일시'],
   'neededForCurrentDecision':['남구 교통행정과의 2023합동점검3항목 세부조치대장·완료일·현장사진','교통안전시설 보수공사 준공 및 현장 재점검 기록','최근3년 누적TAAS 구역의 연도별 사건일·개별사고중복 제거된 집계','점검 지점도와 TAAS반경의 공간 일치 확인']},
  'domainDecision':[{'domain':'교통','status':'주요심화채택','reason':'기존 공식CSV에 법정동코드·지점명·집계구역 존재, 새 공식점검PDF가 못골사거리 개선항목 증명'},{'domain':'산악','status':'이번 추가수집보류','reason':'검색된 금정산 포괄대책은 특정 금성동/초읍동 현존 결함을 증명하지 못함; 교통 지점 연결 근거가 더 구체적'},{'domain':'수난','status':'이번 추가수집보류','reason':'다대동 CCTV·방파제관리 자료는 기존대응 존재까지 설명; 개별 수난신고 장소나 실제결함 연결 없음'}], 'sources':sources}
 dump('place-evidence.json',payload)
 plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
 fig,axes=plt.subplots(1,2,figsize=(14,6),gridspec_kw={'width_ratios':[1.4,1]})
 dd=[r for r in latest if r['rawDong']=='대연동']
 for r in dd:
  axes[0].scatter(r['longitude'],r['latitude'],color='#126774',s=24)
  label=r['spotName'].split('(')[-1].rstrip(')');axes[0].annotate(label+f"\n{r['accidents']}건",(r['longitude'],r['latitude']),xytext=(4,5),textcoords='offset points',fontsize=9)
 axes[0].set_title('대연동 공식 노인보행 사고다발지점 · 2025 자료연도');axes[0].set_xlabel('경도');axes[0].set_ylabel('위도');axes[0].ticklabel_format(useOffset=False);axes[0].grid(alpha=.15);axes[0].margins(.3);axes[0].set_aspect(1/math.cos(math.radians(35.135)))
 axes[1].bar(['못골사거리','대연동못골시장'],[3,0],label='단기개선(안)',color='#168c93');axes[1].scatter([0,1],[0,1],label='기개선 항목',color='#c48330',s=60);axes[1].set_ylabel('공식점검 항목 수');axes[1].set_title('2023년 공식점검 결과 · 현재 완료 여부 미확인');axes[1].set_ylim(0,4);axes[1].legend()
 fig.suptitle('접수 지역명에서 공식 개선 검토 지점까지: 대연동 못골사거리',fontsize=16)
 fig.text(.5,.015,'왼쪽은 119신고 위치가 아닌 TAAS공식 지점. 최근3년 누적·구역중첩 가능으로 사고건수 합산 및 개선효과 해석 금지.',ha='center',fontsize=10)
 fig.tight_layout(rect=(0,.06,1,.94))
 for ext in ['png','svg']:fig.savefig(OUT/f'daeyeon_specific_place_evidence.{ext}',dpi=150)
 plt.close(fig)
 dump('validation.json',{'status':'passed','sourceRows':checks,'targetRecords':len(records),'latestOlderSites':len(latest),'moisAndBdiTableMatch':True,'codeNameMatchAll':True,'yearsFromOfficialCodebook':True,'noIndividual119CoordinatesUsed':True,'noCombinedAccidentSum':True})
 dump('manifest.json',{'script':str(Path(__file__).relative_to(ROOT)),'scriptSha256':sha(Path(__file__)),'sources':sources,'outputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']})
 print(json.dumps({'targetRecords':len(records),'latestOlderSites':[(r['spotName'],r['accidents']) for r in latest],'inspectionSites':len(sites)},ensure_ascii=False))
if __name__=='__main__':main()
