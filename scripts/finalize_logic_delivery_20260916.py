"""Package this review's real deliverables without copying private source forms."""
from pathlib import Path
import json,hashlib,shutil,zipfile
R=Path(__file__).resolve().parents[1]
N=R/'data/processed/최종논리검증-20260916'
O=R/'output/부산119-쟁점해결-20260916'
W=R/'web/final'
D=R/'output/부산119-최종검토-20260916'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))

base=read(N/'evaluation/baseline-results.json');current=read(N/'evaluation/current-results.json')
keyboard=read(N/'evaluation/keyboard-independent.json');browser=read(N/'evaluation/revised-browser.json')
assert base['passed']==9 and base['total']==12
assert current['passed']==11 and current['total']==12
assert all(x['pass'] for x in keyboard['checks'])
assert all(x['pass'] for x in browser['checks']) and not browser['missingLocal'] and not browser['pageErrors']
verify=O/'검증기록.md';s=verify.read_text(encoding='utf-8')
marker='\n## 최종 실행 결과\n'
if marker in s:s=s.split(marker)[0]
s+=marker+f'''
- 고정한 정적 검사: 수정 전 {base['passed']}/{base['total']}, 수정 후 {current['passed']}/{current['total']}.
- 남은 정적 검출 실패 Q10은 동적으로 생성한 연령표 속성을 소스 문자열 검색이 찾지 못한 경우다. 검사 조건은 바꾸지 않았다. 실제 DOM에서 101연령 인원·비중과 키보드 조작을 별도로 확인했다.
- 실제 웹 키보드·수치 대조: {len(keyboard['checks'])}/{len(keyboard['checks'])} 통과.
- 1920×1080·1600×900·1366×768, 13개 절·5개 그림·지역 바로가기·파일 직접 실행·로컬 링크: {len(browser['checks'])}/{len(browser['checks'])} 통과. 누락 로컬 링크와 JavaScript 실행 오류는 확인되지 않았다.
- 내용 독립 검토에서는 13행의 의미, 주민 인원·비중, 사례 선정, 기존 대응과 실제 효과의 구분을 확인했다.

이는 결과물의 기술·내용 검증이다. 사용자의 이해도 개선이나 예방 효과를 검증한 것이 아니다. 외부기관 링크의 현재 예약 가능 여부는 이 검사에 포함되지 않는다.
'''
verify.write_text(s,encoding='utf-8')
for folder in [W/'results/advance',W/'results/followup',R/'output/부산119-전지역후속검증-20260916']:
 shutil.copy2(verify,folder/verify.name)

plan=R/'docs/10-작업계획/부산 분석 작업 계획.md';s=plan.read_text(encoding='utf-8')
mark='## 2026-09-16 최종 논리·주민 연결·결과 전달 재검토'
if mark not in s:
 s+='\n\n'+mark+'''

핵심 질문은 지역별 반복 신고를 주민·현장 배경과 기존 대응에 연결해 예방·지원 안내 및 보완 범위를 구체화하는 것이다. 신고 규모를 위험도나 증설 필요성으로 바꾸지 않는다.

- 불량 표기19행 중 비고 공란13행을 원 HWP 표 셀·전월 원문·서식 절차로 재검토했다. 조치 전용 필드가 아니므로 관리공백·미조치율·공시 누락 근거에서 제외했다. 숫자19/6/13은 유지한다.
- 연산8·부전2·광안4 행정동 후보의5년101연령을 개별 분석했다. 인원과 비중의 반대 방향을 실제 수치로 보여주고 교육 연령·목적별 안내에 연결한다. 후보 합산·환자 나이·교육수요 추정은 하지 않는다.
- 970비교조합→325반복유지→연산·부전 심층 및 광안 별도비교의 선정 논리를 분리했다. 주택화재·산악·수난의 기존 결과도 최신 보고서에 연결한다.
- 24시간·101연령의 마우스 의존 수치를 키보드 표로 제공하고 사례 URL을 구현했다.
- 수정 전 파일 해시와12개 고정 과제로 비교했다. 정적9→11개 충족, 동적연령표는 실제DOM·키보드검사로 별도 확인했다. 사용자실험·사고감소 효과와 구분한다.

최신 결과: `../40-분석결과/부산-119-최종논리검토-20260916.md`와 쟁점해결 보고서.
신규 입력·집계·검증: `data/processed/최종논리검증-20260916/`.
우선 후속 측정: 도로 조사구간-준공구간 동일성, AED 최신 접근·점검 이력, 실제 교육 운영 조건, 사용자 과제 정확도·시간. 공개 검색 미확보를 실제 미조치로 바꾸지 않는다.
'''
 plan.write_text(s,encoding='utf-8')

summary='''# 부산 119 최종 논리 검토와 보완 결과

## 우리가 보려는 것

지역마다 반복되는 신고가 어떤 차이를 보이며, 주민·현장 배경과 기존 서비스를 함께 읽을 때 예방·지원 안내를 어떻게 구체화할 수 있는지 확인한다. 신고가 많은 지역을 위험순위로 만들거나 근거 없이 시설을 늘리는 제안은 하지 않는다.

## 출발 배경과 차별점

부산시의 AED 설치정보 불일치 발표, 부산연구원의 실제 보행환경 조사와 기존 운영·정비 사업을 확인했다. 정부에 해당 업무가 없다는 주장이 아니다. 지역별 신고의 선택 영향, 주민 후보별 차이, 서비스의 목적·이용조건, 과거 조사 이후 사업을 한 흐름으로 묶어 판단할 수 있게 한 것이 이번 분석과 웹의 기여다.

## 이번에 바꾼 결과

1. 조치 미기재13행을 **불량 표기 중 일반 비고란 공란13행**으로 교정했다. 원 HWP4개 재구성 결과132조사행·131판정행·19불량·6현지시정·13공란은 맞다. 금정25행·부산진34행 전체 비고가 비어 있어 관리공백 지표로 사용할 수 없다. 금정7월61행과8월26행의 동일 명칭·주소 일치도0이라 조치 이력을 강제 연결하지 않았다.
2. 14행정동 후보×5년×101연령7,070행을 추가 분석했다. 연산3동65세 이상은2,160→2,744명인데29.11→26.77%, 부전2동은1,366→1,599명인데13.78→13.10%다. 인원 증가와 비중 하락이 함께 나타나므로 구성비만으로 주민 감소를 설명할 수 없다.
3. 연산동 심정지511건, 부전동 교통723건의 반복·선택 영향과 공식 대응을 심층 사례로 연결했다. 광안동 교통611건은 처리조건에 민감한 별도 비교 사례로 유지했다. 셋은 정상 처리·운영성 제외의5년 접수 건수이지 개별 환자·특정 지점 사고 수가 아니다.
4. 주택화재·산악·수난의 기존 결과를 최신 보고서에도 유지했다. 새로운 시설·인력 증설안이 없다는 이유로 기존 조사 결과를 지우지 않았다.
5. 시간24개·연령101개의 수치표를 키보드로 열고 읽도록 구현했다. 세 사례 바로가기, 현재 조건과 결과 요약의 동기화, 후보별 주민 변화도 연결했다.

## 실제 보완과 기대효과

- 연산: 기본 교육·수료증·교육용 기자재·실제 AED를 목적과 이용조건별로 구분했다. 주민 연령은 그 안내의 배경이며 실제 환자 나이·교육수요·장벽이 아니다.
- 부전·광안: 2024조사와2025~2026사업 기록을 함께 표시했다. 과거 문제를 현재도 그대로인 것으로 소개하거나 포장 완료를 보차분리 완료로 바꾸지 않는다.
- 점검표: 불량 발견과 현지시정 기재·비고 공란을 구분했다.13행을 정책 필요성이나 미조치 시설 수로 사용하는 오류를 제거했다.

목적에 맞는 정보 탐색과 현재 상태 판단을 돕는 효과를 기대할 수 있다. 실제 탐색시간 단축·신청 성공률·사고 및 피해 감소는 아직 측정하지 않았다. 이번 웹 개선은 운영기관의 시설 보수나 공식대장 정정과 다르다.

## 다음 판단에 필요한 핵심 자료

| 대상 | 아직 없는 근거 | 확보하면 가능한 판단 |
|---|---|---|
| 부전·광안 | BDI 개별 구간과 사업 준공도면·현재 현장 상태 | 이미 개선된 구간과 새 시설 검토 구간 분리 |
| AED | 동의된 등록ID별 최신 운영·실제 접근·점검 이력 | 정보 불일치와 실제 이용 제한 구분 |
| 예방교육 | 운영기관의 최신 기간·인원 조건, 이용·신청 결과 | 상충 공고 정리와 실제 장벽 판정 |
| 소방 점검 | 개별 조치명령·이행·재점검 비식별 기록 | 실제 미조치 여부·기한 판단 |
| 서비스 시제품 | 같은 과제의 사용자 정답·시간·오판 기록 | 실제 전달 개선 여부 측정 |

공개 검색으로 확보하지 못한 행정 내부 자료는 없다고 단정하지 않는다. 승인 없이 기관에 메시지나 자료 요청을 발송하지 않았다.

## 결과 위치

- 최신 결과 웹: `web/final/results/advance/index.html`
- 지역 탐색: `web/final/results/followup/explorer.html`
- 상세 보고서: `docs/40-분석결과/부산-119-쟁점해결-20260916.md`
- 입력·집계·출처·독립검증: `data/processed/최종논리검증-20260916/`
- 새 배포: `output/부산119-최종검토-20260916.zip`
'''
(R/'docs/40-분석결과/부산-119-최종논리검토-20260916.md').write_text(summary,encoding='utf-8')
D.mkdir(parents=True,exist_ok=True)
# Preserve the tested website hierarchy. Only public aggregate assets live here.
shutil.copytree(W,D,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.zip'))
(D/'결과보기.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=results/advance/index.html"><a href="results/advance/index.html">분석 결과 열기</a>',encoding='utf-8')
(D/'이번작업-보고서.md').write_text(summary,encoding='utf-8')
(D/'실행방법.txt').write_text('''압축을 푼 뒤 결과보기.html을 여세요. 최신 분석 결과와 지역 탐색은 파일 직접 실행이 됩니다.
지도는 터미널에서 python serve.py --no-browser 실행 후 http://127.0.0.1:8765/ 로 여세요.
이미 서버가 실행 중이면 같은 포트를 다시 실행하지 말고 기존 주소를 여세요.
최신 분석: http://127.0.0.1:8765/results/advance/
지역 탐색: http://127.0.0.1:8765/results/followup/explorer.html
공식기관 링크와 외부 배경지도는 인터넷이 필요합니다. 실시간 사건 지도는 아닙니다.

재현은 원 프로젝트의 검증된 신고·인구·후속자료가 필요합니다. 이 배포본에 개인별 신고와 시설 원본을 포함하지 않았습니다.
Python 환경: pandas, numpy, matplotlib, olefile 및 기존 pyhwp 환경, 브라우저검증 Playwright+Chrome. Windows 맑은 고딕.
실행 순서(프로젝트 루트에서 .venv-check/Scripts/python.exe 사용):
1 analysis/00_공통/analyze_prevention_population_20260916.py
2 scripts/audit_inspection_meaning_20260916.py (원 HWP와 보존 법령·추가 원문 사용)
3 scripts/plot_followup_services_20260916.py
4 scripts/build_followup_report_20260916.py
5 scripts/build_followup_explorer_20260916.py
6 scripts/plot_evidence_story_20260916.py (기존 검증 case-selection.json 사용)
7 scripts/build_resolution_report_20260916.py
8 scripts/connect_resolution_20260916.py
9 scripts/check_resolution_web_20260916.py
10 data/processed/최종논리검증-20260916/evaluation/ 독립검증 스크립트
11 scripts/finalize_logic_delivery_20260916.py
검증기록.md와 사전에 보존한 baseline 및 원본 manifest가 필요합니다. 외부기관 자료는 변경될 수 있습니다.
정적검사 Q10의 검출 한계와 실제 DOM 확인은 검증/revised-review.md에 구분합니다.
''',encoding='utf-8')
codes=['analysis/00_공통/analyze_prevention_population_20260916.py','scripts/audit_inspection_meaning_20260916.py','scripts/plot_evidence_story_20260916.py','scripts/build_followup_explorer_20260916.py','scripts/build_resolution_report_20260916.py','scripts/connect_resolution_20260916.py','scripts/check_resolution_web_20260916.py','scripts/finalize_logic_delivery_20260916.py','scripts/correct_inspection_copy_20260916.py']
for rel in codes:
 p=R/rel;target=D/'재현코드'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for p in (N/'evaluation').iterdir():
 if p.is_file() and p.suffix in ['.json','.md','.png','.py']:
  dst=D/'검증'/p.name;dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst)
for name in ['form-summary.json','form-summary.csv','form-header-cells.json','inspection-meaning-erratum.json','original-hashes.json','prior-month-comparison.json','additional-source-manifest.json','13행-의미재검토.md']:
 dst=D/'검증/inspection'/name;dst.parent.mkdir(exist_ok=True);shutil.copy2(N/'inspection'/name,dst)
shutil.copy2(N/'population/manifest.json',D/'검증/population-manifest.json')
shutil.copy2(plan,D/'분석계획.md')
# Entry files are an intentionally complete website; project-only paths in code need the original inputs.
manifest=[{'path':str(p.relative_to(D)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='배포명세.json']
(D/'배포명세.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
zpath=D.with_suffix('.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
 for p in D.rglob('*'):
  if p.is_file() and p.suffix not in ['.zip','.pyc'] and '__pycache__' not in p.parts:z.write(p,p.relative_to(D))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 entries=len(z.namelist())
record={'path':str(zpath.relative_to(R)),'bytes':zpath.stat().st_size,'sha256':sha(zpath),'entries':entries,'crcPassed':True,'rawIncidentExport':False,'includesOriginalFacilityForms':False}
(R/'output/부산119-최종검토-배포기록.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False))
