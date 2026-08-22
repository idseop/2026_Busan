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
(`00_공통` `01_쏠림진단` `02_동네프로파일` `03_다음동네` `04_수용력` `05_시뮬레이션`).

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

- **출력(output)을 clear 하고 커밋한다.**
  노트북 출력은 거대한 JSON 덩어리라 충돌의 주범이고, 지도·이미지가 들어가면 용량도 커진다.
  ```bash
  .venv/bin/python -m nbconvert --clear-output --inplace notebooks/01_쏠림진단/x.ipynb
  ```
- 결과를 공유해야 하면 **노트북 출력이 아니라 `figures/` 의 그림**으로 공유한다.
  최종 산출물은 `analysis/` 스크립트가 만든다 (하드 룰 4)
- **파일명에 본인 이름을 넣는다** — `01_HHI산출_재홍.ipynb` (동시 수정 충돌 방지)
- `.ipynb_checkpoints/` 는 git 제외돼 있다

자세한 협업 규칙은 `CONTRIBUTING.md` 참조.
