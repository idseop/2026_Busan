from pathlib import Path
import shutil, json, hashlib, zipfile
ROOT=Path(__file__).resolve().parents[1]
plan=ROOT/'docs/10-작업계획/부산 분석 작업 계획.md'
archive=plan.with_name('부산 분석 작업 계획-20260915-이력.md')
if not archive.exists(): shutil.copy2(plan,archive)
plan.write_text('''# 부산 분석 작업 계획

최신 기준: 2026-09-16. 이전 화면·방법 변경 기록은 [보존 이력](부산 분석 작업 계획-20260915-이력.md)에 둔다.

## 목표와 순서
부산 전체 신고 특성 → 동별 신고와 주민 연령 배경 → 집중 검토 조합 → 필요한 현장 자료 → 기존 대응 대조 → 근거가 있는 보완 방향 → 독립 시각화 → 결과 전달 웹.
특정 위험 지역이나 해결책을 먼저 정하지 않는다. 시각화만으로도 문제 배경부터 활용 범위까지 설명되는 결과를 우선 완성한다.

## 사용 입력과 분석 조건
2020–2024 raw/119접수 원본 5개, 같은 연도 말 raw/인구배경 인구 5개, data 루트 컬럼 설명서를 현재 입력으로 유지한다. 기존 검증 전처리 gzip 5개의 해시를 확인해 재사용했다. 2018–2019·중복 원본·과거 집계를 현재 입력에 혼합하지 않는다.
17개 선택 컬럼 중 하나라도 결측인 행을 제외한다. A 704,689건, 정상 처리 B 579,412건, 정상 처리에서 업무운행·훈련출동·구급차소독을 뺀 C 574,662건이다. 원본과 제외 기록은 보존한다. 같은 시간·위치만으로 중복 삭제하지 않는다.
완전 사례를 전체 부산 신고로 일반화하지 않는다. 8컬럼 비교 집합은 선택 영향 검토의 별도 분모로만 사용한다. 좌표 임의 대체·인구 비례 동 배정·자동 인구당 신고율을 금지한다.

## 이번에 실행한 분석
전 분류의 연도·처리조건 집계에서 출발해 예방 검토가 구체적인 심정지·주택화재·산악·수난·교통 5분류를 분석했다. 벌집제거는 심층·보완안에서 제외한다. 194개 접수 지역명×5분류=970개 조합을 공개했다.
세 처리조건에서 선택 전후 5년 반복·시작/종료연도 증감 방향이 유지되는 조합 중 분류별 두 설명 사례를 선정했다. 임의 종합점수와 위험 순위는 만들지 않았다. 10개 사례의 연도·월·요일·정확한 시각·지역 구성비·동일 분류의 나머지 부산과 비교·잔존율을 계산했다. 관측일 1,827일과 월/요일 일수를 검증해 일평균을 구분했다.
주민은 170개 사례·연도·후보별 전체101연령 인원·비중으로 유지했다. 복수 후보를 합산하지 않는다. 코드 단일 후보도 실제 신고의 행정동 배정이 확정된 것은 아니다.

## 공식 보완자료와 현재성
부산 2025 소방·교통 업무계획, 2026 자원봉사 모집계획/결과, CPR 교육·예약, 주택 소방시설 지원 자료를 질문에 맞춰 채택했다. 2025·2026 구급연보의 2024·2025 부산 실적을 별도 모집단으로 대조했다. 상권·공사·생활인구는 원인·공간 연결 근거가 없으므로 강제 결합하지 않았다.
소방청 자체평가와 시간별 신고 연구를 참고해 현장 활용·환류라는 문제 배경을 정리했다. 정부가 이미 맞춤형 예방을 한다는 반대 근거도 포함한다. 외국 연구의 효과를 부산에 전이하지 않는다.

## 결과와 보류 기준
유형별 시간 차이는 확인됐다. 모집계획과 모집결과의 차이는 확인됐으나 실제 구조인력 부족은 아니다. 자원봉사 기간 밖의 신고를 미대응으로 계산하지 않는다. 주민의 실제 서비스 미충족·시설 증설 필요·현재 동별 위험도는 확인되지 않았다.
현재 제안 범위는 지역별 반복 근거와 공식 서비스의 대상·운영 조건·이용 경로를 연결하는 결과 전달 시제품이다. 시설·인력·순찰 배치와 피해 감소 효과는 보류한다. 다음 단계는 실제 사건 위치, 당시 운영 범위·배치·수혜/탈락 기록, 이용 장벽 조사 및 시제품 이용 과제 평가다.

## 방법과 검증
기술통계·달력 일수 보정·처리조건 및 제외 전후 민감도·조건부 주민 비교·공식 운영 대조를 채택했다. LISA·시공간스캔·LCLQ·입지/예측모형은 현 질문과 공간 검증 수준에서 필요하지 않아 실행하지 않았다. 기존 논문 목록은 보존 이력과 refs/methods에서 유지한다.
작성과 독립 검증을 분리해 입력→조건→지역/유형/시간→인구→최종 표시를 대조했다. PC 1920·1600·1366, 로컬 HTTP 및 파일 직접 열기를 확인한다. 분석 기간·단위·자료 기준일·보류 범위를 수치와 함께 제공한다.

## 실행 파일과 결과
- analysis/00_공통/analyze_action_patterns_20260916.py
- analysis/00_공통/extract_action_population_20260916.py
- analysis/00_공통/analyze_current_ems_bridge_20260916.py
- analysis/00_공통/verify_action_patterns_20260916.py
- scripts/build_action_report_20260916.py
- data/processed/예방지원-근거분석-20260916/
- [종합 결과](../40-분석결과/부산-119-예방지원-종합결과-20260916.md)
- [현재 운영 대조](../40-분석결과/부산-119-현재운영대조-20260916.md)
- [연구 차별성](../40-분석결과/부산-119-연구차별성-20260916.md)
- output/부산119-예방지원-분석결과-20260916/index.html 및 web/final/results/index.html
''',encoding='utf-8')
index=ROOT/'web/final/index.html'
s=index.read_text(encoding='utf-8')
if 'href="results/index.html"' not in s:
    s=s.replace('<button id="about-open"','<a class="text-button" href="results/index.html">예방·지원 결과</a><button id="about-open"')
index.write_text(s,encoding='utf-8')
out=ROOT/'output/부산119-예방지원-분석결과-20260916'
for name in ['부산-119-현재운영대조-20260916.md','부산-119-연구차별성-20260916.md']:
    shutil.copy2(ROOT/'docs/40-분석결과'/name,out/name)
shutil.copy2(ROOT/'data/processed/예방지원-근거분석-20260916/verification/independent_review.md',out/'독립검증.md')
(out/'실행방법.txt').write_text('index.html을 PC 브라우저에서 여세요. 인터넷 없이 시각화와 지역 사례를 볼 수 있습니다. 공식 출처 링크는 인터넷이 필요합니다. 지도는 별도 전체 웹 ZIP의 실행.cmd로 실행합니다.\n',encoding='utf-8')
for f in out.iterdir():
    if f.suffix in ['.md','.txt']: shutil.copy2(f,ROOT/'web/final/results'/f.name)
for folder in [out,ROOT/'web/final/results']:
    manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file() and f.name!='manifest.json'}
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for folder,target in [(out,out.with_suffix('.zip')),(ROOT/'web/final',ROOT/'output/부산119-지도와분석결과-20260916.zip')]:
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob('*'):
            if f.is_file() and '__pycache__' not in f.parts: z.write(f,f.relative_to(folder))
    with zipfile.ZipFile(target) as z: assert z.testzip() is None
print('Plan, result link, standalone and web ZIP updated')
