# 2026 Big Data 활용 대회 — Track 1

부산시 공공데이터로 지역 현안을 분석·시각화해 정책 개선안을 제안하는 공모전 출품 프로젝트.
**접수 마감 2026-09-18 (금) 17:00**

## 팀원용 빠른 시작

```bash
# 1. 분석 환경 (최초 1회)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2. git 훅 활성화 (최초 1회) — main 직접 push 차단
git config core.hooksPath .githooks

# 3. 작업 브랜치로 이동  (main 은 백업이라 직접 push 금지)
git switch develop

# 3. Claude Code 실행 — CLAUDE.md가 자동 로드된다
claude
```

## 어디에 뭐가 있나

| 경로 | 내용 |
|---|---|
| `CLAUDE.md` | **프로젝트 규칙. 작업 전 필독** |
| `CONTRIBUTING.md` | **협업 규칙 — 브랜치·커밋·PR·충돌 방지** |
| `docs/00-공모요강.md` | 대회 요강 + 아직 확인 못 한 것들 |
| `docs/20-데이터카탈로그/` | 첫 데이터를 받을 때 INDEX.md 가 생긴다 |
| `docs/30-아이디어/SHORTLIST.md` | 아이디어 후보와 점수 |
| `figures/` | 발표·기획서용 차트 |

## Claude Code 명령

| 명령 | 하는 일 |
|---|---|
| `/standup` | 지금 어디까지 왔고 D-day 며칠이고 뭘 해야 하는지 |
| `/datacheck <아이디어>` | 데이터가 실재하는지 실사 → GO/NO 판정 |
| `/review [파일]` | 심사위원 3인 관점으로 기획서 비평 |

## 하네스 자가 점검

커밋·PR 전에 돌린다. 구조가 깨졌는지 사람이 눈으로 찾지 않아도 된다.

```bash
.venv/bin/python scripts/check_harness.py
```

클론 재현성 · import 규약 · 꾸며낸 그림 · 출처 없는 수치 · 경로 참조 · 카탈로그 정합 검사.

## 규칙 3줄 요약

1. Python은 `.venv/bin/python`으로 실행 (셸 상태가 유지되지 않음)
2. 데이터 실사(`/datacheck`) 없이 아이디어를 확정하지 않는다
3. 모든 수치에 `[출처: 기관, 연도, URL]`

## 브랜치 전략

- **`main`** — 백업. **직접 push 금지** (GitHub 브랜치 보호로 차단됨)
- **`develop`** — 기본 작업 브랜치. 여기서 개발한다

main 반영은 PR 로만:
```bash
gh pr create --base main --head develop
gh pr merge <번호> --merge --delete-branch=false   # squash 아님 (develop 유지)
```

## 지금 상태

- 주제: 의료·폭염·침수 취약지역 우선순위 시각화 (**데이터 실사 전 = 미확정**)
- 제출물: **보고서 10P 이하** + 웹 산출물. 서식은 `refs/2026-공모-작성서식.hwpx`
- 다음 할 일: 데이터 실사 (`/datacheck`)
