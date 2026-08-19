# 2026 Big Data 활용 대회 — Track 1

부산시 공공데이터로 지역 현안을 분석·시각화해 정책 개선안을 제안하는 공모전 출품 프로젝트.
**접수 마감 2026-09-18 (금) 17:00**

## 팀원용 빠른 시작

```bash
# 1. 분석 환경 (최초 1회)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2. Claude Code 실행 — CLAUDE.md가 자동 로드된다
claude
```

## 어디에 뭐가 있나

| 경로 | 내용 |
|---|---|
| `CLAUDE.md` | **프로젝트 규칙. 작업 전 필독** |
| `docs/00-공모요강.md` | 대회 요강 + 아직 확인 못 한 것들 |
| `docs/01-작전계획.md` | 주차별 목표. 지금 뭘 해야 하는지 |
| `docs/20-데이터카탈로그/INDEX.md` | 실사 완료 데이터 목록 (단일 진실 원천) |
| `docs/30-아이디어/SHORTLIST.md` | 아이디어 후보와 점수 |
| `figures/` | 발표·기획서용 차트 |

## Claude Code 명령

| 명령 | 하는 일 |
|---|---|
| `/standup` | 지금 어디까지 왔고 D-day 며칠이고 뭘 해야 하는지 |
| `/idea [영역]` | 아이디어 생성·채점 → 숏리스트 갱신 |
| `/datacheck <아이디어>` | 데이터가 실재하는지 실사 → GO/NO 판정 |
| `/review [파일]` | 심사위원 3인 관점으로 기획서 비평 |

## 규칙 3줄 요약

1. Python은 `.venv/bin/python`으로 실행 (셸 상태가 유지되지 않음)
2. 데이터 실사(`/datacheck`) 없이 아이디어를 확정하지 않는다
3. 모든 수치에 `[출처: 기관, 연도, URL]`
