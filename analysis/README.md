# 분석 코드

현재 분석은 2020~2024년 부산 119 신고와 주민 배경에서 시작해 상권·생활인구·주택·현장·기존 대응 자료로 이어진다. 최신 전체 판단과 출력 목록은 [통합 보고서](../docs/40-분석결과/부산-119-지도와입증-통합보고서-20260917.md)에 있다.

| 단계 | 주요 코드 |
|---|---|
| 원본·결측·식별자 점검 | `00_공통/audit_119_receipts.cjs`, `profile_119.py` |
| 선택 필드·행 제외·동 대응 | `00_공통/complete_all_selected_20260915.py`, `validate_dong_crosswalk_20260915.py` |
| 선택 영향·처리조건 | `00_공통/assess_complete17_missingness_20260915.py`, `assess_complete17_stability_20260915.py` |
| 인구·지역 분석 | `00_공통/analyze_population_2020_2024.py`, `synthesize_prevention_2020_2024.py` |
| 상권·생활인구 확장 | `00_공통/extend_context_20260916.py` |
| 지역 프로파일·이후 기간 비교 | `00_공통/build_regional_profiles_20260916.py` |
| 지도·전체 결과·보고서 | `../scripts/build_map_3d_20260916.py`, `build_map_evidence_20260916.py`, `build_complete_results_20260916.py`, `write_map_proof_report_20260917.py` |

작성 코드와 `verify_*`·`review_*`·`check_*` 검증 코드를 구분한다. 날짜가 있는 코드는 단계별 이력이며 모든 파일을 순서 없이 일괄 실행하는 진입점이 아니다. 해당 코드의 입력 명세와 보고서의 재현 순서를 따른다.

웹과 시각화 열람에는 원자료가 필요하지 않다. 분석을 처음부터 재생성할 때는 원본·중간 산출물과 폴더 구조가 필요하며 이 자료는 원본 보호를 위해 Git에 포함하지 않는다. 공개 집계·입력 명세·출처·해시·검증 기록은 최종 ZIP에 함께 제공한다.

분석 환경에는 루트의 `requirements.txt`와 `requirements-final-delivery.txt`를 함께 설치한다. Windows에서 검증한 Python은 `.venv-check/Scripts/python.exe`다. 공통 그림 스타일은 `style.py`이며 한글 폰트를 확인한다.
