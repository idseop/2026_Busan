# 🤝 협업 가이드 (Contributing Guide)

> 규칙의 근거는 `CLAUDE.md`의 **하드 룰**에 있다. 충돌하면 `CLAUDE.md`가 우선한다.

## 브랜치 전략

### 브랜치 구조
```
main                   ← 최종 제출용 (직접 push 금지 · GitHub 브랜치 보호 적용됨)
└── develop            ← 통합 개발 브랜치 (PR로만 main 병합)
    ├── data/작업설명   ← 데이터 수집·실사·전처리
    ├── feat/분석주제   ← 새 분석
    ├── viz/시각화설명  ← 차트·지도
    ├── web/작업설명    ← web/ 산출물
    ├── docs/문서설명   ← 문서·보고서
    ├── fix/버그설명    ← 버그 수정
    └── harness/작업설명 ← .claude/ · scripts/ 등 하네스 변경
```

### 브랜치 네이밍
```
<타입>/<이름>-<간단한설명>

예시:
data/jaehong-sgis-boundary-check
feat/jaehong-heat-vulnerability-index
viz/jaehong-choropleth-priority-map
web/jaehong-leaflet-prototype
harness/jaehong-add-datacheck-rule
```

> `main` 은 **직접 push 가 두 겹으로 차단돼 있다** (하드 룰 12).
> - **로컬 pre-push 훅** (`.githooks/pre-push`) — push 명령 자체가 거부된다.
>   단 클론 후 `git config core.hooksPath .githooks` 를 한 번 쳐야 걸린다
> - **GitHub 브랜치 보호** — 훅을 활성화하지 않았어도 원격이 거부한다
>
> 우회하지 말고 PR 을 쓴다. 훅이 막을 때 다음에 뭘 해야 하는지 메시지로 알려준다.

## 커밋 메시지 규칙

### 형식
```
<타입>(<범위>): <한글 설명>

[선택] 본문: 변경 이유 및 상세 내용
```

### 타입
| 타입 | 설명 | 예시 |
|------|------|------|
| `data` | 데이터 수집·실사·전처리 | `data(03_폭염): 기상청 폭염일수 실사 및 카탈로그 등재` |
| `feat` | 새 분석 추가 | `feat(05_종합): 취약성 지수 합성 로직 구현` |
| `viz` | 시각화 추가·수정 | `viz(05_종합): 우선순위 단계구분도 추가` |
| `web` | 웹 산출물 | `web(data): 행정동 GeoJSON 사전계산 추가` |
| `docs` | 문서·보고서 | `docs(기획서): 분석방법 절 초안 작성` |
| `fix` | 버그 수정 | `fix(00_공통): 행정동 코드 조인 누락 수정` |
| `refactor` | 코드 정리 | `refactor(style): choropleth 범례 로직 분리` |
| `harness` | 하네스 변경 | `harness(check): 카탈로그 정합 검사 추가` |
| `chore` | 환경·기타 | `chore(deps): geopandas 추가` |

**범위(scope)는 폴더 번호를 쓴다** — `00_공통` `02_의료` `03_폭염` `04_침수` `05_종합`.

### ⚠️ 커밋 전 체크리스트
- [ ] **`.venv/bin/python scripts/check_harness.py` 가 통과하는가** ← 이것부터
- [ ] 데이터 파일이 포함되지 않았는지 (`git status` 로 확인)
- [ ] **노트북 출력을 clear** 했는지 (아래 "노트북 규칙" 참조)
- [ ] API 키·개인정보가 포함되지 않았는지
- [ ] 코드가 실제로 실행되는지 (돌려보고 커밋한다)
- [ ] **수치에 출처가 붙어 있는지** (하드 룰 5). 꾸며낸 값이 없는지 (하드 룰 6)

## Pull Request 규칙

### 절차
1. 작업 브랜치에서 완료
2. `develop` 으로 PR 생성 → 병합
3. `develop` → `main` PR 은 **의미 있는 단위가 모였을 때** 만든다
4. 병합 후 작업 브랜치 삭제 (**`develop` 은 삭제하지 않는다**)

```bash
gh pr create --base develop --head <내브랜치>
gh pr merge <번호> --squash --delete-branch          # 작업 브랜치 → develop
gh pr merge <번호> --merge  --delete-branch=false    # develop → main
```

> **`develop` → `main` 은 반드시 `--merge`(머지 커밋)를 쓴다.**
> `--squash` 를 쓰면 develop 커밋이 main 의 조상이 되지 않아 다음 PR 부터 충돌이 난다.
> 작업 브랜치 → develop 은 `--squash` 가 깔끔하다.

### PR 제목 형식
```
[타입] 간단한 설명

예시:
[data] SGIS 행정동 경계·인구 실사
[feat] 폭염 위험도 레이어 구현
```

### 리뷰
현재 GitHub 설정은 **승인 0명**(혼자서도 병합 가능). 팀원이 합류하면 1명 이상으로 올린다.

## 충돌(Conflict) 방지 규칙

### 🚨 반드시 지켜야 할 것

1. **작업 시작 전 항상 최신 develop 를 받는다**
   ```bash
   git switch develop
   git pull origin develop
   git switch -c data/내이름-작업설명
   ```

2. **파일 담당 구역을 나눈다** — 폴더 번호로 나누면 겹치지 않는다
   - `02_의료` `03_폭염` `04_침수` 를 사람별로 배정
   - **공용 파일은 수정 전 알린다**: `analysis/style.py`, `CLAUDE.md`,
     `.claude/**`, `scripts/check_harness.py`

3. **자주 커밋, 자주 푸시** — 작업 단위를 작게 유지한다

4. **큰 구조 변경은 사전 공유** — 폴더 체계나 하네스 변경은 팀 채널에 먼저 알린다

5. **노트북 충돌 방지** — 아래 규칙 참조

### 충돌 발생 시
```bash
git fetch origin
git rebase origin/develop
# 충돌 마커 <<<< ==== >>>> 해결
git add .
git rebase --continue
git push --force-with-lease origin <내브랜치>
```

> ⚠️ **`main`, `develop` 에는 절대 `--force` 푸시하지 않는다.**

## 노트북 규칙

`notebooks/` 는 **탐색용**이고, 최종 산출물은 `analysis/` 스크립트가 만든다 (하드 룰 4).

1. **출력(output)을 clear 하고 커밋한다.**
   노트북 출력은 거대한 JSON 덩어리라 충돌의 주범이고, 지도·이미지가 들어가면 용량도 커진다.
   ```bash
   .venv/bin/python -m nbconvert --clear-output --inplace notebooks/**/*.ipynb
   ```
   결과를 공유해야 하면 **노트북 출력이 아니라 `figures/` 의 그림**으로 공유한다.

2. **파일명에 본인 이름을 넣는다** — `notebooks/03_폭염/01_폭염일수_재홍.ipynb`

3. **하나의 노트북을 두 명이 동시에 고치지 않는다**

4. 첫 셀 보일러플레이트는 `notebooks/README.md` 참조

## 데이터 관리 규칙

1. **`data/raw/` · `data/interim/` 은 Git 에 올리지 않는다** (폴더 구조만 추적된다)

2. **데이터는 파일이 아니라 `docs/20-데이터카탈로그/INDEX.md` 로 공유한다.**
   출처 URL·기간·입도·실사일이 적혀 있으므로 누구나 같은 데이터를 다시 받을 수 있다.
   **받은 데이터는 반드시 등재한다** (하드 룰 3). 등재 안 된 데이터로 만든 분석은 무효다.

3. **`data/raw/` 안의 파일은 수정하지 않는다** (하드 룰 2).
   가공은 `data/interim/` → `data/processed/` 로만 한다.

4. 용량이 크거나 재배포가 안 되는 데이터는 팀 공유 드라이브에 두고,
   카탈로그에 그 위치를 적는다.

## 환경 설정

```bash
# 1. 가상환경 (최초 1회)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2. git 훅 활성화 (최초 1회) — main 직접 push 를 로컬에서 막아준다
git config core.hooksPath .githooks

# 3. 작업 브랜치
git switch develop
```

> `.git/hooks/` 는 클론에 따라오지 않는다. 그래서 훅을 버전 관리되는 `.githooks/` 에 두고
> `core.hooksPath` 로 연결한다. **클론 후 위 명령을 한 번 쳐야 로컬 차단이 걸린다.**
> 안 쳐도 GitHub 쪽 브랜치 보호는 그대로 동작한다.

### ⚠️ Python 실행 규칙
```bash
.venv/bin/python analysis/03_폭염/01_폭염일수.py     # ✅
python analysis/...                                 # ❌ 시스템 파이썬이 잡힌다
```

사람이 터미널에서 `source .venv/bin/activate` 를 쓰는 건 무방하다.
다만 **Claude Code 로 작업할 때는 반드시 절대·상대 경로로 호출한다** (하드 룰 1) —
Bash 도구는 셸 상태를 유지하지 않아 `activate` 가 다음 명령에서 사라진다.

### 패키지 추가
```bash
.venv/bin/python -m pip install <패키지>
```
그리고 **`requirements.txt` 에 패키지명만 직접 추가한다.**
`pip freeze` 는 쓰지 않는다 — 전이 의존성까지 수백 줄이 박혀 유지가 안 된다.

## 하네스 자가 점검

커밋·PR 전에 돌린다. 구조가 깨졌는지 사람이 눈으로 찾지 않아도 된다.

```bash
.venv/bin/python scripts/check_harness.py
```

클론 재현성 · import 규약 · 꾸며낸 그림 · 출처 없는 수치 · 경로 참조 ·
하네스 파일 무결성 · 카탈로그 정합 · 브랜치를 검사한다.
**결함(✗)이 있으면 커밋하지 않는다.**
