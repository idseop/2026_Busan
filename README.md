# 부산 신고 데이터를 활용한 지역 맞춤 정책제안

2026 Big Data 활용 대회 Track 1 — 분석·시각화 프로젝트.

**현행 기준은 [실행계획](docs/30-아이디어/신고데이터-정책제안-실행계획.md)이다.** 주제는 확정했으며 데이터 실사는 아직 완료하지 않았다.

| 분석 축 | 내용 |
|---|---|
| 1. 신고 시공간 × 연령 구성 | 위경도로 행정동을 정하고 발생일시로 시간·계절 특성을 분석한 뒤 동별 연령 구성과 비교 |
| 2. 상권 × 신고 특성 | 동별 업종 구성·상권 규모와 신고 유형·시간 특성을 비교 |

두 축의 결과를 지역·시기·유형에 맞는 정책 검토로 연결한다. **동별 연령은 신고 당사자의 나이가 아니며, 상권과 신고의 관계는 인과효과가 아니다.** 인력 배치·동선·미래 예측은 필수 범위가 아니다.

## 웹페이지 사용 흐름

**부산 전체 동 지도 → 동 클릭 → 신고 유형·시간·계절 → 인구 연령·상권 특성 → 정책 후보와 검토 근거**.
한 페이지에서 지도를 유지하며 동 상세를 갱신한다. 정책 연결 사례와 추가 확인 항목은 [웹페이지 설계](web/README.md)에 정리했다. 현재는 설계이며 실제 데이터 기반 웹 구현은 아직 진행하지 않았다.

## 작업 시작

1. [CONTRIBUTING.md](CONTRIBUTING.md)와 [CLAUDE.md](CLAUDE.md)를 읽는다.
2. `git config core.hooksPath .githooks`로 main 직접 push 차단 훅을 활성화한다.
3. 최신 develop에서 작업 브랜치를 만들고 완료 후 develop PR 절차를 따른다.
4. 가상환경을 만들고 의존성을 설치한다.

macOS/Linux:
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/check_harness.py
```

Windows PowerShell:
```powershell
py -3 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/check_harness.py
```

## 파일 안내

| 경로 | 내용 |
|---|---|
| `docs/30-아이디어/신고데이터-정책제안-실행계획.md` | 질문·두 분석 축·데이터 요구사항·해석·완료 기준 |
| `docs/30-아이디어/SHORTLIST.md` | 현행 안내와 과거 후보 보관 위치 |
| `docs/00-공모요강.md` | 대회 요강·서식·작업 가정 |
| `docs/20-데이터카탈로그/` | 원본 최초 확보 시 INDEX.md 생성; 수집 계획과 구분 |
| `analysis/README.md` | 단계별 입력·출력·스크립트 실행 규약 |
| `data/raw/` · `data/interim/` | 경계·신고·연령인구·상권·정책자원; 실제 파일은 Git 제외 |
| `notebooks/` · `analysis/` · `figures/` | 탐색 → 재현 가능한 분석 → 검증된 그림 |
| `web/data/` | 공개 가능한 지역 집계 |

## 명령과 검증

- `/standup`: 실제 파일을 확인한 진행 상황.
- `/datacheck`: 신고 원본부터 실사하고 축별 진행·조건부·보류 판정.
- `/idea`: 현행 주제 안에서 구체화하거나 범위 변경 대안 제시.
- `/review`: 기획·데이터·정책·시각화 검토.

커밋·PR 전에 `scripts/check_harness.py`를 가상환경 Python으로 실행한다. 새 폴더는 Git 스테이징 후 검사해야 클론 재현성 확인에 포함된다.
`main` 직접 push와 공유 브랜치 강제 push는 금지한다. 원시 신고 좌표·내용·개인정보는 커밋하지 않는다.

## 다음 작업

신고자료의 실제 위경도·발생일시·유형, 전체 기간·행 수·부산 전역 포함 여부를 확인한다. 경계·연령인구·상권과 같은 지역·시점으로 연결할 수 있는지 검증한다. 이번 하네스 정비는 데이터 확보나 분석 완료를 의미하지 않는다.
