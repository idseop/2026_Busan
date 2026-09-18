"""Package the new research pass and its verified web results; preserve inputs."""
from pathlib import Path
import shutil,json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];B=R/'data/processed/고도화검증-20260916';O=R/'output/부산119-쟁점해결-20260916';W=R/'web/final'
plan=R/'docs/10-작업계획/부산 분석 작업 계획.md';s=plan.read_text(encoding='utf-8')
if '## 2026-09-16 선택 영향 분해와 쟁점 해결' not in s:
 s+='''
## 2026-09-16 선택 영향 분해와 쟁점 해결

부산 전체 신고에서 좁혀가는 기존 흐름을 유지하며, 후속검증의 미확인 사항을 다음과 같이 추가 검토했다.

- 같은 이동전화에서 기초8 비교집합과17개 충족 집합의 시간분포를 비교했다. 비교자료는 진단용이며 현재 입력704,689건을 교체하지 않는다.
- 거제동·범일동의 증감 반전을 전화경로 구성과 이동전화 내부 제외로 산술 분해했다. 이것은 선택성의 설명이며 인과·대표성 복구가 아니다.
- 연산동 심정지와 부전동 교통을 우선 심층 사례로, 광안동 교통을 조건 민감성을 가진 비교 사례로 정리했다. 가장 위험한 지역 순위나 임의 종합점수는 만들지 않는다.
- 부전 맞이길 제막식, 광안 포장사업 검사·준공금, 신평 공원 설계 공고를 확보하고 과거 미분리 구간과 동일한 사업인지 구분했다.
- AED 제8판 전국지침의 표출 조건과 기존 수정 절차를 반영했다. 지도 미표시는 장비 부재나 고장을 확정하지 않는다.
- 소방 불량19행을 후속 검색했으나 새로운 동일행 완료 기록은 확보하지 못했다. 현지시정6행·조치미기재13행을 유지하고 현재 미조치 목록을 생성하지 않았다.
- 예방교육·교육용 장비 대여·실제 AED 대여·수료증 조건을 구분해 웹에 연결했다. 공고의 기간·인원 상충은 실제 서비스 폐지나 수강 거부가 아닌 정보 조건으로 표시한다.
- 효과는 구현한 결과 연결과 사용자 기대효과, 실제 피해 감소를 구분한다. 참여자 사용성 실험이나 현장 효과를 실시했다고 보고하지 않는다.

최신 보고서: `../40-분석결과/부산-119-쟁점해결-20260916.md`.
추가 집계·출처·검증: `data/processed/고도화검증-20260916/`.
최신 결과 웹: `web/final/results/advance/index.html`; 지역 탐색의 추가 비교는 `web/final/results/followup/explorer.html`.
'''
 plan.write_text(s,encoding='utf-8')
run='''PC에서 index.html을 직접 여세요. 표·그래프는 인터넷 없이 표시됩니다. 공식기관 링크는 인터넷 연결이 필요합니다.

로컬 서버 실행 중 접속주소: http://127.0.0.1:8765/results/advance/
전체 지역 탐색: http://127.0.0.1:8765/results/followup/explorer.html
프로젝트 루트에서: python web/final/serve.py --no-browser
전체 웹 ZIP은 압축해제 후 index.html(지도) 또는 results/advance/index.html(최신분석)을 실행하세요.

원자료는 ZIP에 포함하지 않습니다. 보유 프로젝트 루트와 검증된 입력을 사용합니다.
신고: 2020–2024, 17개 조건 충족704689건. 비교집합은 선택영향 진단에만 사용합니다.
공식문서: 각 source-register.json 및 data/processed/고도화검증-20260916/ 하위 원문·검색 기록.
교육 문서 직접HTTP는 차단돼 웹 도구의 추출본을 보존했습니다. 추출본·지침·과거기록을 현재예약/장비상태로 간주하지 않습니다.

재현 순서(프로젝트 루트의 .venv-check/Scripts/python.exe 사용):
1. analysis/00_공통/analyze_selection_deepening_20260916.py
2a. scripts/collect_resolution_evidence_20260916.py
2b. scripts/collect_resolution_evidence_20260916.py track
2c. scripts/collect_resolution_evidence_20260916.py analyze
3. scripts/collect_traffic_resolution_20260916.py
4. scripts/analyze_prevention_service_conditions_20260916.py
5. scripts/plot_service_conditions_20260916.py
6. scripts/build_resolution_report_20260916.py
7. scripts/build_followup_explorer_20260916.py
8. scripts/connect_resolution_20260916.py
9. scripts/check_resolution_web_20260916.py
10. 고도화검증-20260916/verification/ 독립 검증 코드
11. scripts/package_resolution_20260916.py

analyze 단계는 보존된 response/aed-guideline-v8.hwpx가 필요합니다. 교육 분석은 보존된 education/web-extraction.json과 web-extra-extraction.json을 입력으로 사용합니다. 두 단계의 입력을 새로 수집했다고 간주하지 않습니다.
응답 수집기는 기존 scripts/collect_dong_services_20260916.py를 가져옵니다. 해당 도우미도 코드 묶음에 포함했습니다.
Python pandas/numpy/matplotlib/lxml, Playwright와 설치된 Chrome을 사용합니다. 그림 한글폰트는 Windows 맑은 고딕.
검증된 이전 신고·인구·후속 결과를 읽으므로 이 ZIP만으로 원자료 전체 분석을 재생성할 수 있는 것은 아닙니다.
각 수집기는 저장된 원문을 재사용하며 외부사이트는 변경/접속제한될 수 있습니다.
'''
(O/'실행방법.txt').write_text(run,encoding='utf-8')
codefiles=['analysis/00_공통/analyze_selection_deepening_20260916.py','scripts/collect_resolution_evidence_20260916.py','scripts/collect_dong_services_20260916.py','scripts/collect_traffic_resolution_20260916.py','scripts/analyze_prevention_service_conditions_20260916.py','scripts/plot_service_conditions_20260916.py','scripts/build_resolution_report_20260916.py','scripts/build_followup_explorer_20260916.py','scripts/connect_resolution_20260916.py','scripts/check_resolution_web_20260916.py','scripts/package_resolution_20260916.py']
for name in codefiles:
 p=R/name;dest=O/'code'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for p in (B/'verification').iterdir():
 if p.is_file() and p.suffix in ['.json','.md','.png','.py']:
  dest=O/'verification'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
p=B/'response/education-independent-review.json'
if p.exists():shutil.copy2(p,O/'verification'/p.name)
manifest=[{'path':str(p.relative_to(O)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.rglob('*') if p.is_file() and p.name!='delivery-manifest.json']
(O/'delivery-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for p in O.rglob('*'):
 if p.is_file():
  dest=W/'results/advance'/p.relative_to(O);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
packages=[]
for src,name in [(O,'부산119-쟁점해결-20260916.zip'),(W,'부산119-지도와쟁점분석-20260916.zip')]:
 zpath=R/'output'/name
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
  for p in src.rglob('*'):
   if p.is_file() and p.suffix not in ['.zip','.pyc'] and '__pycache__' not in p.parts:z.write(p,p.relative_to(src))
 with zipfile.ZipFile(zpath) as z:assert z.testzip() is None;entries=len(z.namelist())
 packages.append({'path':str(zpath.relative_to(R)),'bytes':zpath.stat().st_size,'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'entries':entries,'crcPassed':True})
(R/'output/부산119-쟁점해결-배포기록.json').write_text(json.dumps(packages,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(packages,ensure_ascii=False))
