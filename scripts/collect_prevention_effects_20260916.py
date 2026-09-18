"""Official evidence capture; no agency messages, reservations or microdata join."""
from pathlib import Path
import subprocess,hashlib,json,zipfile,re,csv
import fitz
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/services';O.mkdir(parents=True,exist_ok=True)
SOURCES={
 'kdca-stats-index.html':'https://www.kdca.go.kr/injury/biz/injury/recsroom/statsSmMain.do',
 'kdca-2024-statistics.zip':'https://is.kdca.go.kr/cscdfile2/biz/ip/filecmmn/ipFileDown.do?fileId=19cf94826232',
 'district-aed-correction.pdf':'https://clik.nanet.go.kr/clikr-collection/bill/051007/9/2025/CLIKC7981918852981599_1.pdf',
 'kdca-2024-release.pdf':'https://kdca.go.kr/bbs/kdca/42/240821/download.do',
 'kdca-regional-cpr.pdf':'https://www.kdca.go.kr/bbs/chungcheong/141/309625/download.do',
 'busan-aed-2025.html':'https://www.busan.go.kr/eng/ai-translated-press-releases/1691467',
 'kdca-study-definition.html':'https://www.kdca.go.kr/kdca/3377/subview.do',
 'busan-aed-korean.html':'https://www.busan.go.kr/nbtnewsBU/1691436',
}
def build_results():
 doc=fitz.open(O/'kdca-2024-statistics.pdf')
 # Printed table 42, PDF75-76. Parse the original row, not rounded-rate division.
 def row(page,start,end):
  t=doc[page-1].get_text().split(start,1)[1].split(end,1)[0]
  counts=[int(s.replace(',','')) for s in t.splitlines() if re.fullmatch(r'[\d,]+',s.strip())]
  rates=[float(s) for s in re.findall(r'\(([\d.]+)\)',t)]
  assert len(counts)==len(rates)==11,(counts,rates)
  return counts[-5:],rates[-5:]
 rows=[]
 for region,page,start,end in [('전국',75,'\n전체\n','\n성별\n'),('부산',76,' 부산',' 대구')]:
  counts,rates=row(page,start,end)
  for year,count,rate in zip(range(2020,2025),counts,rates):
   rows.append(dict(region=region,year=year,cpr_performed_patients=count,cpr_rate_percent=rate,denominator_patients=None,denominator_status='표42의 정확한 분모 수 미제시; 반올림 비율 역산 안 함',source_pdf_page=page,source_printed_page=page-24,source_table='42',source_row='전체' if region=='전국' else '시·도 > 부산'))
 assert [r['cpr_rate_percent'] for r in rows if r['region']=='부산']==[19.7,20.8,20.0,16.4,13.8]
 assert [r['cpr_rate_percent'] for r in rows if r['region']=='전국']==[26.4,28.8,29.3,31.3,30.3]
 meta={
 'title':'2020~2024 부산·전국 일반인 심폐소생술 시행 추이',
 'source':SOURCES['kdca-2024-statistics.zip'],'source_file':'kdca-2024-statistics.pdf',
 'population':'119구급대가 병원으로 이송한 급성심장정지 환자 중 의무기록조사가 완료된 자료. 발견·목격자가 근무 중 구급대원·의료인인 경우 제외(통계집 PDF8쪽 변경 기준).',
 'region_definition':'환자 발생장소 주소 기준. 주소 정보가 없으면 출동한 119안전센터 주소를 사용한 경우가 있음(PDF6쪽). 거주지 기준 아님.',
 'recording_limit':'병원 의무기록 내용으로 산출하므로 실제 일반인 심폐소생술 시행률보다 과소 추정될 수 있음(PDF7쪽).',
 'denominator_limit':'표42에는 시행 인원과 반올림 시행률만 제시. 연도별 정확한 분모 수는 미확보로 null 유지. 294/13.8 등 역산 금지.',
 'comparison_limit':'전국에는 부산 포함. 부산의 비율은 연산동이나 교육대상별 비율이 아니며 이 프로젝트의 신고 건수와 합산·접수번호 연결하지 않음.',
 'interpretation':'부산의 기록된 시행률은 2021년 이후 하락했으며 2024년 전국보다 16.5%p 낮다. 교육 부족의 원인 입증이나 웹의 향상 효과 추정은 아니다.',
 'rows':rows}
 (O/'cpr-trend.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
 with (O/'cpr-trend.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
 for pg in [6,7,8,36,75,76]:doc[pg-1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(O/f'original-page-{pg}.png')
 source_checks={'source_pdf_sha256':hashlib.sha256((O/'kdca-2024-statistics.pdf').read_bytes()).hexdigest(),'source_pdf_pages':len(doc),'table_rows':10,'assertions_passed':2,'exact_denominators_reconstructed':False,'capture_pages':[6,7,8,36,75,76]}
 (O/'cpr-extraction-checks.json').write_text(json.dumps(source_checks,ensure_ascii=False,indent=2),encoding='utf-8')
 previous=R/'data/processed/후속입증-20260916/services/followup-services-evidence.json'
 old=json.loads(previous.read_text(encoding='utf-8'))
 selected=[v for v in old['facts'] if v['id'] in ['city-aed-stock','city-aed-inspection','yeonje-register']]
 claims=[
  {'id':'busan-cpr-recorded','status':'확인','claim':'2024년 부산의 기록된 일반인 심폐소생술 시행률은 13.8%, 전국은 30.3%. 부산은 2021년 20.8% 이후 3년 연속 하락했다.','source':'kdca-2024-statistics.pdf','pages':[6,7,8,75,76],'use':'교육과 초기대응 정보를 주민이 이용하기 쉽게 연결할 필요를 검토하는 부산 단위 문제 배경','not_proven':'특정 동 교육 부족, 미참여 원인, 실제 미실시 전체 규모, 웹의 생존 개선 효과'},
  {'id':'national-cpr-outcomes','status':'확인','claim':'2024년 전국 조사에서 일반인 심폐소생술 시행군 생존율 14.4%, 미시행군 6.1%; 뇌기능회복률은 각각 11.4%, 3.5%.','source':'kdca-2024-statistics.pdf','pages':[3],'use':'초기대응의 중요성을 뒷받침하는 전국 관측 결과','not_proven':'무작위 실험 인과효과가 아니며 부산 또는 본 웹 도입 후의 예상 향상률로 전용 불가'},
  {'id':'city-aed-correction','status':'일부 확인·후속 정량 결과 미확보','claim':'부산시는 2025년 일부 AED 설치정보와 행정정보 불일치를 확인했다. 불일치 건수·전수점검 결과·이후 정정률을 명시한 후속 원자료는 이번 공개 검색에서 확보하지 못했다.','source':'busan-aed-korean.html','url':SOURCES['busan-aed-korean.html'],'use':'일정·주소·표시 여부를 실제 작동 및 접근성과 구분해 안내','not_proven':'전체 장비 불량, 미점검 지속, 연산동 미지원'},
  {'id':'yeonje-existing-support','status':'기존 근거 재사용','claim':'2024년 연제구 회의록은 장비 구매 및 비의무기관 소모품 지원 운영과 공개 거부·구급차 제외·좌표 오류 등 지도 미표출 사유를 설명한다.','source':'followup-services-evidence.json#yeonje-register','use':'장비 수만으로 관리 공백을 만들지 않고 현행 지원을 안내','not_proven':'연산동 이용률·교육 성취도·장비 실제 가용률'},
  {'id':'saha-notice-still-inconsistent','status':'공개 화면 확인','claim':'2026-09-16 확인한 사하소방서 공고는 운영 종료 7월31일·신청 종료12월31일 및 정확히10명일 때 개설 기준이 서로 다르게 남아 있다. 공개 검색에서 이를 해소하는 동일 사업의 새 공고는 확보하지 못했다.','source':'education-current-web-capture.json','url':'https://119edu.busan.go.kr/main/4?action=view&no=17236','use':'신청 가능 조건을 자동 확정하지 않고 기관의 사전협의 안내를 연결','not_proven':'교육 중단·실제 폐강 실적·이용자 피해'},
  {'id':'dongnae-aed-search-lead','status':'보류: 검색 색인만 확인·원 PDF404','claim':'동래구 2024 감사 처리결과 검색 색인에 132개소173대 점검과 시스템 현황 정비 완료가 나타난다. 원문 다운로드 실패로 확정 결과표에 채택하지 않았다.','source':SOURCES['district-aed-correction.pdf'],'use':'전혀 정정하지 않았다는 주장에 반하는 추가 확인 단서','not_proven':'부산2025 발표 이후 전역 정정 완료·연제구 정정 완료'},
 ]
 result={'asOf':'2026-09-16','claims':claims,'cprTrendFile':'cpr-trend.json','reusedFacts':selected,'reusedInput':{'path':str(previous.relative_to(R)),'sha256':hashlib.sha256(previous.read_bytes()).hexdigest()},
 'effectPath':[
 {'step':1,'name':'지역 결과와 유효한 교육·AED 정보 함께 표시','state':'프로젝트 구현 결과','metric':'표시 정보의 공식 출처·기간·대상 조건 일치율'},
 {'step':2,'name':'조건을 맞추는 데 걸리는 탐색 부담 감소','state':'기대 경로·실제 효과 미측정','metric':'기존 공공페이지 대비 과제 성공률·소요시간·잘못된 신청 선택률'},
 {'step':3,'name':'교육 신청·참여·술기 유지','state':'기관 협력·후속 관찰 필요','metric':'동의 기반 신청 전환·수료·술기 수행 평가, 분모와 탈락 포함'},
 {'step':4,'name':'실제 상황에서 일반인 CPR/AED 수행과 환자 예후','state':'현재 웹 효과로 입증 불가','metric':'의료·구급 조사 연결 및 대조 설계 필요; 지역 기록 완전성 함께 검토'}],
 'conclusion':'부산 단위 CPR 시행 기록의 하락을 추가로 확인했다. 본 서비스는 반복 신고 지역에서 현재 이용 가능한 예방 정보를 연결한다. 서비스 부족의 원인을 입증하거나 임상적 효과를 달성한 것은 아니다.',
 'excludedClaims':['AED 지도 미표출=장비 없음/불량','부산 13.8%=연산동 시행률','19 불량 중 시정 미기재13=현재 미시정13','전국 생존율 차이=본 웹 기대 효과','공고조건 상충=실제 교육 중단']}
 (O/'prevention-effects.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 searches=[
 {'topic':'부산2025 AED 불일치 이후 조치','queries':['부산 자동심장충격기 2025 설치정보 불일치 점검 결과','부산 자동심장충격기 2026 정정 점검 실적'],'result':'2025 한글 보도자료 및 기존2026의원 제안 확인. 공개 정정 실적 미확보'},
 {'topic':'연제·연산 교육 성과','queries':['site.yeonje.go.kr 2025 심폐소생술 명','연제구 자동심장충격기 교육 실적 행정사무감사 2025','연산동 심폐소생술 교육 결과'],'result':'기존2024의회 지원 답변 재사용. 지역별 수료·술기·실제 사용 결과표 미확보. 비공식 행사 기사로 효과 대체 안 함'},
 {'topic':'사하 신규 공고','queries':['site.119edu.busan.go.kr 사하소방서 2026 하반기','사하소방서 2026 소방안전교육 2026-08'],'result':'동일 공고17236 공개 화면 재확인. 대체 공고 미확보'},
 {'topic':'동래 정정 반대근거','queries':['site.dongnae.go.kr 173 자동심장충격기','2024년도행정사무감사처리결과보고의건 자동심장충격기 132 173'],'result':'국회도서관 공식 PDF 색인 확인. 직접 다운로드404로 채택 보류'},
 {'topic':'공식 CPR 통계','queries':['2024 급성심장정지조사 통계 부산 13.8','KDCA 2024 통계집 일반인 심폐소생술'],'result':'보도자료→충청권 통계→국가손상정보포털 원 통계집까지 확보. 원표42 우선 사용'}]
 (O/'search-audit.json').write_text(json.dumps({'date':'2026-09-16','searchScope':'공개 웹·기존 보유 공식 자료; 기관 문의 발송 안 함','searches':searches},ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'summary.md').write_text('''# 심폐소생술·AED 효과 근거 확장

부산의 일반인 심폐소생술 시행 기록은 2021년20.8%에서2024년13.8%로 낮아졌다. 같은2024년 전국은30.3%다. 국가손상정보포털 원 통계집 표42를 추출했으며, 신고접수 데이터와 다른 환자 조사다. 발생장소 주소가 지역 기준이고, 의무기록 누락에 따른 과소 추정 가능성이 있다. 정확한 연도별 분모 수는 원표에 없어 역산하지 않았다.

이 결과는 초기대응 관련 정보 제공의 부산 단위 배경을 강화한다. 하지만 연산동 교육이 부족하다거나 교육 안내 웹을 만들면 시행률·생존율이 일정 수치만큼 상승한다는 증거는 아니다. 전국 시행·미시행군의 생존율14.4%·6.1%는 초기대응의 중요성을 보여주는 관측값이며 웹 효과가 아니다.

부산2025 AED 행정정보 불일치는 확인됐으나 전역 정정 실적은 미확보다. 기존 연제구 지원 운영 및 미표출 사유를 유지했다. 동래173대 정비 완료 검색 단서는 원문404로 확정 결과에서 보류했다. 사하 공고의 날짜·10명 기준 상충은 공개 화면에서 계속 확인됐으나 교육 중단으로 해석하지 않는다.

서비스의 검증 가능한 첫 기대효과는 필요한 예방정보를 정확하게 찾는 과정의 개선이다. 기존 페이지와 비교하는 탐색시간·조건판단 정확도 실험이 먼저 필요하다. 교육 참여·술기 향상과 실제 환자 예후는 그 뒤의 별도 평가 단계다. 현재 이 이용효과 실험은 수행하지 않았다.

## 산출물과 재현

- `cpr-trend.csv/json`: 2020~2024 부산·전국 원표10행, 인원·공식 분율·원쪽수
- `prevention-effects.json`: 확인·보류 주장과 효과 경로
- `search-audit.json`: 질문별 검색범위 및 미확보 사항
- `source-manifest.json`: 원문 URL·해시·접근 실패 기록
- `original-page-*.png`: 원 표·정의 검토용 캡처
- 실행: `.venv-check/Scripts/python.exe scripts/collect_prevention_effects_20260916.py`
''',encoding='utf-8')
def main():
 manifest=[]
 for name,url in SOURCES.items():
  p=O/name
  try:
   if not p.exists():p.write_bytes(subprocess.run(['curl.exe','--fail','--location','--max-time','45','-A','Mozilla/5.0',url],check=True,capture_output=True).stdout)
   if p.suffix=='.zip':
    with zipfile.ZipFile(p) as z:
     members=[n for n in z.namelist() if n.endswith('.pdf')];assert len(members)==1
     target=O/'kdca-2024-statistics.pdf';target.write_bytes(z.read(members[0]));doc=fitz.open(target);(O/'kdca-2024-statistics.txt').write_text('\n'.join(f'\n===PDF PAGE {i+1}===\n'+pg.get_text() for i,pg in enumerate(doc)),encoding='utf-8')
   if p.suffix=='.pdf':
    doc=fitz.open(p);(O/(p.stem+'.txt')).write_text('\n'.join(f'\n===PDF PAGE {i+1}===\n'+pg.get_text() for i,pg in enumerate(doc)),encoding='utf-8')
   manifest.append({'file':name,'url':url,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'status':'saved','acquired':'2026-09-16'})
  except Exception as e:manifest.append({'file':name,'url':url,'status':'failed','error':str(e)})
 extracted=O/'kdca-2024-statistics.pdf'
 if extracted.exists():manifest.append({'file':extracted.name,'url':SOURCES['kdca-2024-statistics.zip'],'sha256':hashlib.sha256(extracted.read_bytes()).hexdigest(),'status':'extracted from official ZIP','bytes':extracted.stat().st_size})
 capture=O/'education-current-web-capture.json'
 if capture.exists():manifest.append({'file':capture.name,'url':'https://119edu.busan.go.kr/main/4?action=view&no=17236','sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),'status':'web tool text capture; includes second URL timeout','acquired':'2026-09-16'})
 (O/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');build_results()
 outputs=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(O.iterdir()) if p.is_file() and p.name!='output-manifest.json']
 (O/'output-manifest.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2),encoding='utf-8');print(f'{len(manifest)} source records; {len(outputs)} hashed files')
if __name__=='__main__':main()
