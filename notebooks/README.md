# notebooks/ — 탐색용

## analysis/ 와의 역할 분담

| | `notebooks/` | `analysis/` |
|---|---|---|
| 목적 | **탐색·실사·시행착오** | **재현 가능한 파이프라인** |
| 언제 | 데이터를 처음 열어볼 때, 컬럼·인코딩 확인, 이것저것 해볼 때 | 방법이 굳었을 때 |
| 산출물 | 판단 근거 (이 데이터 쓸 만한가?) | `data/processed/`, `figures/`, `web/data/` |
| 실행 순서 | 자유 | 번호순으로 처음부터 끝까지 |

**규칙: 노트북에서 굳은 것만 스크립트로 옮긴다.**
최종 산출물(그림·웹 데이터)은 **반드시 `analysis/` 스크립트가 만든다.**
노트북 출력에만 있는 그림은 산출물이 아니다 — 재현이 안 되기 때문이다.

번호는 `analysis/`·`data/`·`figures/` 와 같은 체계를 쓴다
(`00_공통` `02_의료` `03_폭염` `04_침수` `05_종합`).

## 실행

```bash
.venv/bin/jupyter lab              # 브라우저에서 작업
.venv/bin/python -m nbconvert --to notebook --execute --inplace <파일>   # 일괄 실행
```

커널이 `.venv` 를 가리키는지 확인할 것. 안 잡히면:
```bash
.venv/bin/python -m ipykernel install --user --name busan-2026 --display-name "2026 부산"
```

## 노트북 첫 셀 — 이걸로 시작한다

```python
import sys, pathlib
ROOT = pathlib.Path.cwd().resolve()
while not (ROOT / "CLAUDE.md").exists():        # 어느 깊이에서 열어도 루트를 찾는다
    if ROOT.parent == ROOT:                     # 가드: 없으면 무한루프가 된다
        raise RuntimeError("프로젝트 루트를 못 찾음. 저장소 안에서 열었는지 확인")
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / "analysis"))

from style import setup, save, source, choropleth, C, SEQ
setup()

import pandas as pd, geopandas as gpd
RAW = ROOT / "data/raw"
```

`analysis/` 스크립트는 `__file__` 기준을 쓰지만, 노트북에는 `__file__` 이 없다.
그래서 `CLAUDE.md` 를 찾아 올라가는 방식을 쓴다.

## 커밋 규칙

- **출력을 남긴 채 커밋한다.** 팀원이 열지 않고도 결과를 볼 수 있어야 한다
- 단 **지도·대용량 그림이 들어간 노트북은 용량을 확인**하고, 크면 출력을 지운다
  (`--ClearOutputPreprocessor.enabled=True`)
- `.ipynb_checkpoints/` 는 git 제외돼 있다
