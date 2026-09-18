from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'web/final/assets/app.js';s=p.read_text(encoding='utf-8')
s=s.replace('도로·지명은 OpenStreetMap 배경지도에 표시됩니다.','산림·수역·시가지·도로 형태는 OpenFreeMap의 OpenStreetMap 기반 벡터 자료로 표시합니다. 도로명·시설명은 숨기고 구·군·동 지명은 보유 SGIS 경계 내부 위치로 표시합니다.')
s=s.replace('면색은 선택 강조에만 사용합니다.','신고 분포는 구·군 이름 옆의 비중으로 표시하며 과거 신고를 현재 경계의 면적별 위험도로 색칠하지 않습니다. 심층 분석 지역의 강조는 고정 검토 대상 안내입니다.')
p.write_text(s,encoding='utf-8')
p=R/'web/final/README.md'
p.write_text('''# 부산 신고 지도 · 상세 지형과 분석 결과

2026-09-16 갱신. 부산만 탐색하며 산림·수역·해안·시가지·도로 형태를 유지한다. 도로명·시설명·큰 숫자 기호는 숨긴다. 현재 경계를 과거 신고의 정확한 위치나 면적별 위험도처럼 표현하지 않는다.

## PC 실행

`실행.cmd` 실행 후 http://127.0.0.1:8765/ . 별도 ZIP 실행에는 Python 3 필요. 다른 환경은 `python serve.py` 또는 `python serve.py --port 8766`. 서버는 로컬 127.0.0.1에만 연결한다.

상세 지리 배경에는 인터넷이 필요하다. 연결 실패 또는 파일 직접 열기에서는 지역 경계와 기존 분석 결과를 계속 제공하고 배경 로딩 상태를 표시한다. 실시간 재난 서비스가 아니다.

## 화면 읽기

- 지도 주제: 지형·지역 / 신고 분포 / 심층 분석 지역.
- 신고 분포는 선택한 조건의 부산 신고 중 각 구·군 이름별 접수 비중이다. 위험도나 주민당 발생률이 아니다. 합계 0이면 자료 없음을 표시한다.
- 심층 분석 지역은 고정된 네 지역·유형 사례를 검토한 구·군 안내다. 현재 연도나 종별의 위험 순위가 아니다.
- 왼쪽 심층 분석 버튼은 해당 지역과 종별을 선택한다. 연도·처리조건은 유지한다.
- 상세 첫 화면은 선택 지역과 나머지 부산의 유형 구성비·시간대를 비교하고 반복성·주민·기존 서비스·보완안 상태를 연결한다.
- 구·군·동 지명은 SGIS 2025-06-30 지도 안내용이다. 현재 206개 읍면동과 과거 인구 자료 205개 동을 강제 결합하지 않는다. 원문 동 검색 결과의 지도 강조는 소속 구·군까지다.

## 지도 제공과 이용 조건

MapLibre GL JS 5.6.1 (BSD-3-Clause), Leaflet 1.9.4 (BSD-2-Clause), MapLibre GL Leaflet 0.1.4 (ISC), OpenFreeMap Liberty 파생 스타일. 해당 라이선스 파일은 assets/vendor에 보존한다. API 키는 없다. 화면에 필요한 벡터 타일을 요청하며 타일을 ZIP에 저장하거나 재배포하지 않는다.

배경 출처: OpenFreeMap / © OpenMapTiles / © OpenStreetMap contributors. 화면의 출처 표시를 유지한다. 지도 제공에는 서비스 수준 보장이 없다.

- https://openfreemap.org/
- https://openfreemap.org/quick_start/
- https://www.data.go.kr/data/15129688/fileData.do

## 재현 및 검증

scripts/build_context_basemap.py: 지도 라이브러리·스타일과 출처 기록.
scripts/build_place_labels.py: 공식 경계 내부 지명 위치 생성·검증.
scripts/check_result_map.py: 전체 조작·집계·지도 실패 대처·변경 웹 파일 해시.
scripts/check_context_results.py: 별도 작성자가 수행한 비교 수치·바로가기 검증.
scripts/view_result_map.py: 실제 PC 지도와 결과 화면 확인.
scripts/package_result_map.py: 검증 후 ZIP 해시 대조.

기존 분석 데이터 7개 파일의 해시는 유지한다. 공개 데이터에 개별 접수번호·정밀 신고 위치를 추가하지 않는다. 공식 지도 비교 기록과 상세 검증은 프로젝트 docs/40-분석결과 및 data/processed/지도탐색웹-20260915/context-map에 있다.
''',encoding='utf-8')
