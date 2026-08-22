# analysis/ — 분석 스크립트

## 번호 규칙

`data/` · `analysis/` · `figures/` 가 같은 번호를 공유한다.

`data/` 는 **수집 대상**으로, `analysis/`·`figures/`·`notebooks/` 는 **분석 단계**로 나눈다.

| 번호 | `data/raw` (수집 대상) | `analysis`·`figures`·`notebooks` (분석 단계) |
|---|---|---|
| 00 | 경계 | **공통** — 경계 로드 · 행정동 기준 테이블 |
| 01 | 외국인 | **쏠림진단** — 집중도·시계열 |
| 02 | 소비 | **동네프로파일** — 동별 특성 벡터 |
| 03 | 방문 | **다음동네** — 유사도 추천 ★ |
| 04 | 숙박 | **수용력** — 혼잡·숙박 한계 |
| 05 | 상권 | **시뮬레이션** — 소비 재분배 |
| 06 | 접근성 | — |

> **두 축은 1:1 대응이 아니다.** 여러 원본이 한 분석 단계에 들어간다.
> 예: `01_쏠림진단` 은 `01_외국인` + `02_소비` + `03_방문` 을 함께 쓴다.
> 번호는 "몇 번째 단계인가"를 나타내는 순번이지 폴더 짝이 아니다.

## 스크립트 작성 규약

파일명은 폴더 안에서 `01_`, `02_` 순번을 붙인다. 예: `analysis/01_쏠림진단/01_HHI산출.py`

### style.py import — 이 3줄로 시작한다

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from style import setup, save, source, choropleth, C, SEQ
```

**`sys.path.insert(0, "analysis")` 는 쓰지 마라.** 그건 현재 작업 디렉토리가
프로젝트 루트일 때만 동작한다. 하위 폴더 스크립트를 다른 위치에서 실행하면
`ModuleNotFoundError: No module named 'style'` 로 죽는다. (실측 확인됨)

위 방식은 `__file__` 기준이라 **어디서 실행하든 동작한다.**

### 실행

```bash
.venv/bin/python analysis/01_쏠림진단/01_HHI산출.py
```

Python 은 항상 `.venv/bin/python` 으로 호출한다 (하드 룰 1).

## 데이터 경로

스크립트 안에서 경로를 쓸 때도 `__file__` 기준으로 잡는다:

```python
ROOT = pathlib.Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data/raw/02_소비/카드소비.csv", encoding="cp949")
```
