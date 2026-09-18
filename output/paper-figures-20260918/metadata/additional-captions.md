# 추가 그림 11~15의 외부 캡션과 출처

그림 내부에는 제목·설명·출처를 넣지 않았다. 아래 문구는 보고서의 외부 캡션과 근거 확인에 사용한다.

## 11-district-type-proportions

2020~2024년 주 분석 555,786건을 구·군 내 유형 비중으로 재표현했다. 구·군은 총건수순이며 위험도순이 아니다.

- 분모: 각 구·군의 주 분석 전체 접수
- 표시 데이터: `display-data/11-district-type-proportions.csv`
- 입력:
  - `data/processed/5개년통합-지역유형-제안연결-20260917/01-16구군-5년합계와-한해제외순위.csv`
  - `data/processed/5개년통합-지역유형-제안연결-20260917/03-구군별70유형-동일유형연결.csv`

## 12-annual-receipts-by-type

주 분석 조건의 2020~2024년 연도별 접수다. 결측 제외와 접수경로 구성의 영향을 받으므로 부산 전체 사고·환자 수의 변화로 확대하지 않는다.

- 분모: 각 연도, 선택 17항목 완전 기재·정상·업무성 기록·벌집제거 제외 접수
- 표시 데이터: `display-data/12-annual-receipts-by-type.csv`
- 입력:
  - `data/processed/5개년통합-지역유형-제안연결-20260917/02-전체70유형-5년합계와-한해제외순위.csv`

## 13-weekday-hour-disease

2020~2024년 다대·금곡 질병 접수의 요일×시각 구성이다. 두 패널에 동일 색상 척도를 적용했다. 신고 시각은 예방교육의 적정 운영시간을 뜻하지 않는다.

- 분모: 다대동 질병 4,054건 / 금곡동 질병 3,615건, 각각 전체 168셀 합계 100%
- 표시 데이터: `display-data/13-weekday-hour-disease.csv`
- 입력:
  - `data/processed/5개년통합-지역유형-제안연결-20260917/11-상위5구군45조합-5년시간교차집계.csv`

## 14-bujeon-commerce-quarterly

2020~2024년 분기별 부전동 음식·소매 상가 비중이다. 각 분기 상가 명부의 스냅숏 비중이며 실제 방문자나 특정 사고 원인의 측정값이 아니다. 선그래프 세로축은 29~36%로 표시했으므로 0% 기준 높이로 비교하지 않는다.

- 분모: 각 분기 부전동 전체 상가 수
- 표시 데이터: `display-data/14-bujeon-commerce-quarterly.csv`
- 입력:
  - `data/processed/신고주민연결심화-20260917/direction-connections/major-burden-commerce-20quarters.csv`

## 15-bujeon-hourly-visiting-population

2023·2024년 각 12개월의 시간별 평균방문인구를 월 동일 가중 평균한 값이다. 행정동 후보인 부전1·2동을 별도로 표시했으며 신고자·실인원·연간 방문자 수로 해석하지 않는다. 2025년 행은 제외했다.

- 분모: 해당 연도의 12개 월별 시간대 평균방문인구 추정값의 산술평균
- 표시 데이터: `display-data/15-bujeon-hourly-visiting-population.csv`
- 입력:
  - `data/processed/통합완성-20260916/context/living-hour-annual-equal-month-means.csv`
  - `data/processed/신고주민연결심화-20260917/direction-connections/major-burden-living-candidates-2023-2024.csv`
