from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web/final/index.html';s=p.read_text(encoding='utf-8')
anchor='<a class="text-button" href="results/deepening/index.html">동별 심화 결과</a>'
if anchor not in s:s=s.replace('<button id="about-open"',anchor+'<button id="about-open"')
p.write_text(s,encoding='utf-8')
p=ROOT/'web/final/results/index.html';s=p.read_text(encoding='utf-8')
anchor='<p style="padding:16px;background:#e0eeea"><a href="deepening/index.html">추가 분석: 구·동별 실제 지점과 기존 개선 결과 보기</a> · 이 페이지는 추가 조사 전 기초 분석입니다.</p>'
if anchor not in s:s=s.replace('<body>','<body>'+anchor)
p.write_text(s,encoding='utf-8')
p=ROOT/'docs/10-작업계획/부산 분석 작업 계획.md';s=p.read_text(encoding='utf-8')
append='''

## 2026-09-16 동별 보완 심화 반영

기초 신고·인구 집계 이후 공식 지점 및 운영 조건 분석을 추가했다. 최신 판단은 `../40-분석결과/부산-119-동별보완-심화결과-20260916.md`와 `data/processed/동별보완-추가근거-20260916/`에 기록한다.

- 16개 구·군의 공식 보행사고 지정기록 301행 및 부산 현장점검 14지점을 점검했다. 신고 분석 기간 2020–2024는 유지하며 지정자료 2025는 별도 자료연도로 표시한다.
- 대연동 못골사거리의 2023 개선 3항목과 못골시장 일원의 2025 사업 완료·2026 효과평가 준공을 구분한다. 실제 서비스 공백과 기존 평가 부재를 임의로 주장하지 않는다.
- AED 차량 제외 등록의 시간표, 아파트 포털의 등록 동 항목별 시설 조건을 수집했다. AED 대여 등록과 아파트 내 오피스텔 표기도 유지한다. 신고 발생 건물에 배정하지 않는다.
- 10개 사례의 전후 기간 및 연도 제외 민감도를 추가했다. 기간에 따라 뒤집히는 양상에 고정된 시간 전략을 제안하지 않는다.
- 보완 우선순위는 기존 점검 항목·실제 이용 조건·이미 수행한 평가와 연결 가능한 정도로 판단한다. 위험 순위·임의 종합점수는 만들지 않는다.
- 추가 결과 웹은 `web/final/results/deepening/index.html`. 기존 지도에 연결하고 개별 신고·정밀 위치를 공개하지 않는다.
'''
if '## 2026-09-16 동별 보완 심화 반영' not in s:s+=append
p.write_text(s,encoding='utf-8')
