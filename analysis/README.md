# analysis/ — 분석 스크립트

## 번호 규칙

`data/` · `analysis/` · `figures/` 가 같은 번호를 공유한다.

| 번호 | data/raw | analysis | figures |
|---|---|---|---|
| 00 | 경계 | **공통** — 경계 로드 + 인구 결합 | 공통 |
| 01 | 인구 | *(없음 — 00에서 처리)* | *(없음)* |
| 02 | 의료 | 의료 접근성 | 의료 |
| 03 | 폭염 | 폭염 위험 | 폭염 |
| 04 | 침수 | 침수 위험 | 침수 |
| 05 | 대응자원 | **종합** — 지수 합성·우선순위 | 종합 |

> **01이 analysis·figures에 없는 것은 의도된 공백이다.**
> 인구는 독립 분석 대상이 아니라 세 도메인의 공통 분모라 `00_공통`에서 함께 처리한다.
> `05`는 raw에서는 "대응자원"(보건소·소방서), analysis에서는 "종합"이다 —
> 대응자원이 종합 단계에서 쓰이기 때문이다.

## 스크립트 작성 규약

파일명은 폴더 안에서 `01_`, `02_` 순번을 붙인다. 예: `analysis/03_폭염/01_폭염일수.py`

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
.venv/bin/python analysis/03_폭염/01_폭염일수.py
```

Python 은 항상 `.venv/bin/python` 으로 호출한다 (하드 룰 1).

## 데이터 경로

스크립트 안에서 경로를 쓸 때도 `__file__` 기준으로 잡는다:

```python
ROOT = pathlib.Path(__file__).resolve().parents[2]
df = pd.read_csv(ROOT / "data/raw/03_폭염/관측자료.csv", encoding="cp949")
```
