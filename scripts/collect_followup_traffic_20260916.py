"""Official follow-up evidence, preserving non-confirmation versus non-completion.
Run: .venv-check/Scripts/python.exe scripts/collect_followup_traffic_20260916.py
Cached source files are reused; original inputs are never edited.
"""
import csv, hashlib, html, json, re, subprocess, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/후속입증-20260916/traffic'
BASE=ROOT/'data/processed/동별보완-추가근거-20260916'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES={
 'motgol-completed.html':'https://www.bsnamgu.go.kr/board/view.namgu?boardId=BBS_0000088&menuCd=DOM_000000114005000000&startPage=1&dataSid=663408',
 'nampo-crosswalk-2022.html':'https://www.busan.go.kr/nbtnewsBU/1546206',
 'nampo-camera-2025.html':'https://www.bsjunggu.go.kr/board/view.junggu?boardId=BBS_0000018&dataSid=250400&menuCd=DOM_000000103002004000&orderBy=REGISTER_DATE+DESC&paging=ok&startPage=1',
 'bdi-elder-transport.pdf':'https://data.bdi.re.kr/PDF/View.do?dir=report&path=RPT_00000000001&savename=20250715172207_54971',
 'busan-facility-addresses.html':'https://www.busan.go.kr/depart/welgrand020102?bbsNo=9&curPage=3',
 'busan-facility-addresses-yeonje.html':'https://www.busan.go.kr/depart/welgrand020102?bbsNo=9&curPage=5',
 'busan-2030-neighborhood-plan.pdf':'https://dynamice.busan.go.kr/drctDwnld/busan_2030_new_06.pdf',
 'yeonje-budget-fence-2024.html':'https://clik.nanet.go.kr/minutes/viewer.do?DOCID=CLIKC2230713265058844&collection=minutes',
}
def fetch(name,url):
 p=OUT/name
 if not p.exists():
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as r:p.write_bytes(r.read())
  except Exception:
   subprocess.run(['curl.exe','--fail','--location','--max-time','40',url,'-o',str(p)],check=True,capture_output=True)
 return p

def main():
 sources=[]
 for name,url in SOURCES.items():
  try:
   p=fetch(name,url)
   sources.append({'file':str(p.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
   if p.suffix=='.html':
    t=re.sub(r'(?is)<(script|style)\b.*?</\1>','',p.read_text(encoding='utf-8',errors='replace'))
    (OUT/(p.stem+'.txt')).write_text(html.unescape(re.sub('<[^>]+>','\n',t)),encoding='utf-8')
  except Exception as e:sources.append({'url':url,'error':str(e)})
 for term in ['효과평가','못골사거리','남구종합사회복지관','용호종합사회복지관']:
  url='https://www.bsnamgu.go.kr/index.namgu?menuCd=DOM_000000112000000000&searchTerm='+urllib.parse.quote(term)
  try:
   p=fetch('search-'+term+'.html',url)
   sources.append({'file':str(p.relative_to(ROOT)),'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'kind':'official_search_snapshot'})
  except Exception as e:sources.append({'url':url,'error':str(e)})
 (OUT/'source-manifest.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
 build_outputs(sources)
 print('Saved official follow-up matrix, field-study tables, sources and search log.')

def dump(name,obj):
 (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csvout(name,rows):
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def build_outputs(sources):
 inp=BASE/'place/coverage_mois_all14_inspection_sites.csv'
 rows=list(csv.DictReader(inp.open(encoding='utf-8-sig')))
 queries=[
  ['"못골시장" "효과평가"','"못골시장" "과업"','"못골시장" "효과" site:bsnamgu.go.kr'],
  ['"못골사거리" "개선" "남구"','"못골사거리" site:bsnamgu.go.kr'],
  ['"남구종합사회복지관" "교통" "개선"','"남구종합사회복지관" "부산" "우암"'],
  ['"용호종합사회복지관" "보행" "개선"','"용호종합사회복지관" "주소"'],
  ['"부산진시장앞교차로" "개선"','"부산진시장" "보행" site:bsdonggu.go.kr','"부산진시장" "교차로" "개선" site:busan.go.kr'],
  ['"굿모닝성모안과" "보행" 부산','"굿모닝성모안과" site:busanjin.go.kr'],
  ['"한비전교회" "교통" 부산','"한비전교회" site:saha.go.kr'],
  ['"장대골삼거리" "개선"','"장대골삼거리" site:suyeong.go.kr','"장대골" "교통" "2025"'],
  ['"사도행전교회" 부산 "개선"','"사도행전교회" "보행" site:go.kr'],
  ['"거제시장" "개선" site:yeonje.go.kr','"거제시장" "정비" "연제구"','"거제시장" "교통안전" "연제"'],
  ['"부산광역시노인종합복지관" "보호구역"','"부산광역시노인종합복지관" "연산동" site:busan.go.kr'],
  ['부산 "남항시장사거리" "개선"','"남항시장" "교통" "개선" site:yeongdo.go.kr','"남항시장" "보행환경" site:yeongdo.go.kr'],
  ['부산 "남포사거리" "개선"','"남포사거리" "2025" site:go.kr'],
  ['"반송도서관교차로" "개선"','"반송도서관" "교차로" site:haeundae.go.kr','"반송도서관" "안전" site:council.haeundae.go.kr'],
 ]
 extra={
  0:('주변 사업 준공·평가 계약 완료 확인; 평가 결과 미확보','못골시장 일원 사업 2025.2 전체 준공, 2026.5.20 효과평가 계약상 완료. 원 2023 기개선 1항목과 사업 항목의 동일성은 별도 미확인.','motgol-completed.html; data/processed/동별보완-추가근거-20260916/followup/namgu-investment-2025.pdf; data/processed/동별보완-추가근거-20260916/followup/evaluation-detail.json','2026 최종 효과평가 보고서·과업지시서·2024 발언의 8건 민원 원장 및 종결조치'),
  2:('공식 시설 주소 확보; 조치 완료 미확인','부산시 공식 시설 목록: 동제당로 258 (우암동). 현재 공개 목록으로 2023 점검 범위는 확정하지 않음.','busan-facility-addresses.html','2023 점검 상세 위치도와 교통시설 2항목·중장기 1항목 조치대장'),
  3:('공식 시설 주소 확보; 조치 완료 미확인','부산시 공식 시설 목록: 이기대공원로 7 (용호동). 현재 공개 목록으로 2023 점검 범위는 확정하지 않음.','busan-facility-addresses.html','2023 점검 상세 위치도와 교통시설 14항목·중장기 1항목 조치대장'),
  9:('생활권 계획·주변 펜스 예산심사 확인; 점검항목 완료 미확인','2030 계획 PDF13쪽에 거제시장 인근 근린생활가로 약400m. 2024.12.12 연제구의회는 거제천로101~121 펜스 논의 후 주민참여 펜스 예산3740만원 전액삭감. 발언자도 정확한 위치를 재확인하려 했으며 2023 점검 구역과 동일성 미확인.','busan-2030-neighborhood-plan.pdf; yeonje-budget-fence-2024.html','2023 단기17·중장기3항목 조치대장, 펜스 제안구간 위치도·경찰협의서·2025 최종예산 및 추경·시공 여부'),
  10:('공식 시설 주소 후보 확보; 조치 완료 미확인','부산시 공식 목록의 부산시노인종합복지관: 거제천로230번길18(연산동). 명칭 축약의 동일기관 후보이며 2023 점검 구간은 미확정.','busan-facility-addresses-yeonje.html','2023 점검 위치도·시설명 동일성 및 도로시설 9항목·중장기 1항목 조치대장'),
  12:('주정차 단속 운영 확인; 점검항목 완료 미확인','2025.11.12 중구 공개 현황에 남포사거리 자동형 주정차 CCTV 포함. 09~21시 운영, 11:30~14시 단속 유예. 2022 횡단보도 시범사업 발표도 있으나 2023 점검 6항목 완료 증거는 아님.','nampo-camera-2025.html; nampo-crosswalk-2022.html','2023 단기 6·중장기 4항목 조치대장, 현재 카메라별 시행시간·예외·가동기록'),
 }
 matrix=[];search=[]
 for i,r in enumerate(rows):
  status,fact,source,need=extra.get(i,('개별 조치 완료 근거 미확보','2023 점검 이후 해당 항목의 완료·미완료를 판정할 후속 원문을 이번 검색에서 확보하지 못함.','coverage_mois_all14_inspection_sites.csv','2023 점검 세부 항목별 위치·조치일·준공 검수 및 사후 평가자료'))
  matrix.append({**r,'followupStatus':status,'confirmedFollowup':fact,'followupSources':source,'remainingEvidence':need,'sameInterventionConfirmed':False,'currentlyUnimprovedConfirmed':False,'searchCount':len(queries[i]),'searchDate':'2026-09-16'})
  search.append({'site':r['place'],'district':r['district'],'queries':queries[i],'method':'웹 검색 인덱스; 남구 4개 명칭·효과평가는 공식 통합검색도 확인','result':status,'limits':'사이트 전체 전수검토 아님. 검색 무응답은 사업 부재 증거 아님.'})
 assert len(matrix)==14 and sum(int(r['shortTermItems']) for r in matrix)==122
 assert sum(int(r['longTermItems']) for r in matrix)==19
 csvout('traffic-followup-all14.csv',matrix)
 dump('traffic-followup.json',{'asOf':'2026-09-16','inspectionDate':'2023-10-25~2023-11-10','publicationDate':'2023-11-29','sites':matrix,'totals':{'sites':14,'shortTermInspectionItems':122,'longTermInspectionItems':19},'interpretation':'당시 개선안 수이며 현재 미완료 건수 아님. 119 지역 신고와 해당 지점 사고를 동일 사건으로 연결하지 않음.','rejectedClaims':['못골시장 사업 미완료','못골시장 효과평가 미실시','공개 보고서 검색 실패는 사업 부재','남포사거리 점심 단속 유예는 긴급 대응 부재','2023 시설 점검항목이 현재도 미개선']})
 dump('search-attempts.json',{'date':'2026-09-16','sites':search,'excludedFalseMatches':['대구 남구종합사회복지관 경사로 사업','경남 거제시장(시장직)·거제시 예산','부산시청 공통 하단 주소를 부산광역시노인종합복지관 주소로 오인','BDI 양정·명지 횡단보도 현장 관찰을 남포사거리 관찰로 오인']})
 field_study()
 addresses=[{'inspectionPlace':'남구종합사회복지관 부근','officialFacilityName':'남구종합사회복지관','district':'남구','address':'동제당로 258 (우암동)','rawDongCandidate':'우암동','sourceFile':'busan-facility-addresses.html'}, {'inspectionPlace':'용호종합사회복지관 부근','officialFacilityName':'용호종합사회복지관','district':'남구','address':'이기대공원로 7 (용호동)','rawDongCandidate':'용호동','sourceFile':'busan-facility-addresses.html'}, {'inspectionPlace':'부산광역시노인종합복지관','officialFacilityName':'부산시노인종합복지관','district':'연제구','address':'거제천로230번길 18 (연산동)','rawDongCandidate':'연산동','sourceFile':'busan-facility-addresses-yeonje.html'}]
 for a in addresses:a.update({'pageUpdateLabel':'2022-11-02','retrieved':'2026-09-16','matchScope':'공식 시설 주소로 찾은 동명 배경 후보. 2023 점검 구간 및 개별119 신고 위치 확정 아님.'})
 csvout('facility-address-candidates.csv',addresses)
 (OUT/'README.md').write_text('''# 교통 지점 후속 근거

2023년 공식 점검 부산 14곳을 모두 조회했다. `traffic-followup-all14.csv`는 당시 항목 수와 이번에 확보한 후속 자료를 분리한다. 검색한 곳에서 자료를 얻지 못했다는 사실은 사업이 없거나 아직 미완료라는 뜻이 아니다.

- 못골시장: 기존 검증의 2025년 사업 준공과 2026년 평가 계약 완료를 유지했다. 최종 평가보고서·과업지시서·민원 조치 원장은 확보하지 못했다.
- 남포사거리: 2025년 주정차 CCTV 운영시간을 확인했다. 2023년 개선항목 완료 여부는 별개다.
- 거제시장: 2030 정비기본계획 PDF13쪽(인쇄105)에 약400m 근린생활가로가 표시된다. 시공 완료 근거가 아니다.
- 세 복지관: 부산시 주소목록으로 우암동·용호동·연산동 배경 후보를 확보했다. 점검구간이나 신고 위치를 확정하지 않는다.

## 새 현장 연구

부산연구원 정책연구2025-03-244(2025년3월 발행)의 2024년10월26~27일 현장조사표를 재구조화했다. 부전시장·못골시장·광안역·신평역의 총20구간 중 보차분리는12, 미분리는8구간이었다. 구간 선택은 사고다발지역3곳과 임의 비교1곳으로 부산 전체 표본이 아니다.

보행시간은 30대 여성 조사원의 노인체험복 착용 전후 실험이다. 실제 고령 주민 평균이나 119 신고자의 연령·피해·인과로 해석하지 않는다. 속도표는 신평 외부도로의 횡단대기시간 포함1구간을 제외하므로 조사거리표와 속도표의 분모가 다르다. 2024년 결과를 2026년 현장 상태로 옮기지 않는다.

`bdi-field-study-area-summary.csv`는4지역, `bdi-field-study-roadtype-summary.csv`는8개 지역×도로유형 집계다. 개별20구간 원자료는 보고서 공개표에 없다. 원PDF67·70쪽 이미지와 직접 대조했다. 발표 증감률은 원문이 사용하는 거리·시간 합산 기준을 보존했다.

## 재현

프로젝트 루트에서 `.venv-check/Scripts/python.exe scripts/collect_followup_traffic_20260916.py` 실행. Python 표준 라이브러리·PyMuPDF를 사용한다. 저장된 원문은 재사용하며 기존 입력은 수정하지 않는다. `source-manifest.json`의URL·해시와 `input-reuse.json`으로 출처를 추적한다. `search-attempts.json`은 실제 검색어와 제외한 동명이의 자료를 기록한다.
''',encoding='utf-8')
 dump('input-reuse.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [inp,BASE/'followup/evaluation-detail.json',BASE/'followup/namgu-investment-2025.pdf']])
 dump('geoje-budget-evidence.json',{'source':SOURCES['yeonje-budget-fence-2024.html'],'meetingDate':'2024-12-12','meeting':'제255회 연제구의회 안전환경위원회 제4차','proposalAddressAsSpoken':'거제천로 101~121','fenceSpans':200,'approxLengthMAsSpoken':300,'committeeBudgetReductionWon':37400000,'adoptedDecisionScope':'2025 예산안 위원회 예비심사에서 해당 주민참여 펜스예산 전액삭감','placementCertain':False,'policeConsultationDocumentObtained':False,'matches2023InspectionItems':False,'interpretation':'예산심사 사실이며 현재 미설치·지원부족·사고 인과 또는 다른 교통시설 사업 취소를 뜻하지 않음.'})

def field_study():
 import pymupdf
 p=OUT/'bdi-elder-transport.pdf';d=pymupdf.open(p)
 for page in [66,67,68,69,70,82]:
  (OUT/f'bdi-page-{page}.txt').write_text(d[page-1].get_text(),encoding='utf-8')
  if page in [67,70]:d[page-1].get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).save(OUT/f'bdi-page-{page}.png')
 values=[('부전시장','부산진구','부전동',9,1663.3,6,3,175.3,215.0,1.05,.86,22.7,-18.5),('못골시장','남구','대연동',4,1104.4,3,1,208.1,231.5,1.33,1.19,11.2,-10.1),('광안역 주변','수영구','광안동',3,1034.4,1,2,278.2,305.0,1.24,1.13,9.6,-8.8),('신평역 주변','사하구','신평동',4,1311.3,2,2,260.5,282.2,1.20,1.11,8.3,-7.7)]
 fields=['area','district','placeNameDongContext','surveySegments','surveyLengthM','separatedSegments','unseparatedSegments','meanSecondsWithoutSuit','meanSecondsWithSuit','meanMetersPerSecondWithoutSuit','meanMetersPerSecondWithSuit','publishedTimeChangePct','publishedSpeedChangePct']
 rows=[dict(zip(fields,v)) for v in values]
 for r in rows:r.update({'surveyDate':'2024-10-26~2024-10-27','sourcePages':'PDF 66~70 / 인쇄 50~54','observation':'30대 여성 조사원 노인체험복 착용·미착용 비교. 실제 고령자 모집단의 보행속도 아님.','segmentDenominatorNote':'조사지점 20개 구간. 속도표는 횡단대기시간 포함 1구간 제외(신평 외부도로). 개별 20행 원자료 미제공.','spatialJoin':'조사지역 이름 배경 연결만 허용; 2023 점검 지점·119 사건 귀속 불가'})
 assert sum(r['surveySegments'] for r in rows)==20
 assert sum(r['separatedSegments'] for r in rows)==12
 assert sum(r['unseparatedSegments'] for r in rows)==8
 assert abs(sum(r['surveyLengthM'] for r in rows)-5113.4)<.01
 csvout('bdi-field-study-area-summary.csv',rows)
 segments=[
 ('부전시장','내부도로',4,792.9,2,2,198.2,194.3,258.6,1.02,.77,33.1,-24.9),('부전시장','외부도로',5,870.4,4,1,174.1,160.1,180.1,1.09,.97,12.5,-11.1),
 ('못골시장','내부도로',1,362.0,0,1,362.0,319.5,343.0,1.13,1.06,7.4,-6.9),('못골시장','외부도로',3,742.4,3,0,247.5,171.0,194.3,1.45,1.27,13.6,-12.0),
 ('광안역 주변','내부도로',2,772.4,0,2,386.2,310.0,330.3,1.25,1.17,6.5,-6.1),('광안역 주변','외부도로',1,262.0,1,0,262.0,214.5,254.5,1.22,1.03,18.6,-15.7),
 ('신평역 주변','내부도로',2,656.5,0,2,328.3,290.0,309.8,1.13,1.06,6.8,-6.4),('신평역 주변','외부도로',2,654.8,2,0,282.2,201.5,227.0,1.40,1.24,12.7,-11.2)]
 sf=['area','roadType','surveySegments','surveyLengthM','separatedSegments','unseparatedSegments','speedTableMeanDistanceM','meanSecondsWithoutSuit','meanSecondsWithSuit','meanMetersPerSecondWithoutSuit','meanMetersPerSecondWithSuit','publishedTimeChangePct','publishedSpeedChangePct']
 sr=[dict(zip(sf,v)) for v in segments]
 for r in sr:r.update({'speedTableExcludesWaitingSegment':r['area']=='신평역 주변' and r['roadType']=='외부도로','sourcePages':'PDF67·70 / 인쇄51·54','surveyDate':'2024-10-26~2024-10-27','observationalUnit':'지역×내외부도로 집계. 개별 구간 측정 원자료 아님.'})
 csvout('bdi-field-study-roadtype-summary.csv',sr)
 assert sum(r['surveySegments'] for r in sr)==20
 dump('bdi-field-study.json',{'sourceUrl':SOURCES['bdi-elder-transport.pdf'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'surveyDate':'2024-10-26~2024-10-27','areas':rows,'sampleLimit':'비고령 조사원 체험복 실험이며 표본이 충분하지 않아 보고서도 보조자료로 한정','rawIndividualSegmentsAvailable':False,'causalClaimAllowed':False,'current2026ConditionConfirmed':False,'separationSegments':{'total':20,'separated':12,'unseparated':8},'limitations':['개별 20구간별 수치 공개표 아님; 지역×내외부도로 집계','2024 관찰을 2026 현재 결함으로 표현하지 않음','2025.2 못골사업 준공 및 2026 평가 완료 이후 결과 아님','시간 증감률은 원 보고서 구간거리·시간 합산 기준; 반올림 평균을 이용해 재계산하지 않음']})
if __name__=='__main__':main()
