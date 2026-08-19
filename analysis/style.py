"""발표·기획서용 차트 공통 스타일.

모든 시각화 스크립트는 그림을 그리기 전에 setup()을 호출한다.
한글 폰트가 깨진 그림은 산출물이 아니다. (CLAUDE.md 하드 룰 4)

사용법:
    import sys; sys.path.insert(0, "analysis")
    from style import setup, save, C, SEQ
    setup()
    fig, ax = plt.subplots()
    ...
    save(fig, "01_구별_폭염일수")   # → figures/01_구별_폭염일수.png (+ .svg)
"""

from __future__ import annotations

import glob
import os
import warnings

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

# ─── 팔레트 ──────────────────────────────────────────────────────────────
# 범주형: 채도를 억제한 8색. 발표 화면(프로젝터)에서 뭉개지지 않는 명도 차를 둠.
C = {
    "primary":   "#1F4E79",  # 짙은 청 — 주 계열, 강조
    "accent":    "#E8743B",  # 주황 — 대비 1개만. 남발 금지
    "teal":      "#2A9D8F",
    "gold":      "#E9C46A",
    "purple":    "#7B6D9B",
    "rose":      "#C9556E",
    "olive":     "#7F9C4A",
    "slate":     "#6C7A89",
    # 의미 고정색
    "bad":       "#C0392B",  # 악화·위험
    "good":      "#27AE60",  # 개선·안전
    "neutral":   "#95A5A6",  # 비교군·배경 계열
    "grid":      "#DCE0E4",
    "text":      "#1A1A1A",
    "subtext":   "#5A6570",
}

CAT = [C["primary"], C["accent"], C["teal"], C["gold"],
       C["purple"], C["rose"], C["olive"], C["slate"]]

# 연속형(단계구분도·히트맵). 낮음→높음.
SEQ = "YlOrRd"      # 위험·밀도·부담
SEQ_COOL = "Blues"  # 규모·수량
DIV = "RdBu_r"      # 증감·편차 (0 중심)


def _register_korean_font() -> str:
    """사용 가능한 한글 폰트를 등록하고 패밀리명을 반환."""
    candidates = [
        (os.path.expanduser("~/Library/Fonts/Pretendard-*.ttf"), "Pretendard"),
        ("/System/Library/Fonts/Supplemental/NanumGothic.ttf", "NanumGothic"),
        ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", "AppleGothic"),
    ]
    for pattern, name in candidates:
        files = sorted(glob.glob(pattern))
        if not files:
            continue
        for f in files:
            try:
                font_manager.fontManager.addfont(f)
            except Exception:
                pass
        # 실제로 등록됐는지 확인
        available = {f.name for f in font_manager.fontManager.ttflist}
        if name in available:
            return name
    warnings.warn("한글 폰트를 찾지 못했습니다. 차트의 한글이 깨질 수 있습니다.")
    return mpl.rcParams["font.family"][0]


def setup(scale: float = 1.0) -> str:
    """전역 스타일 적용. 반환값은 사용된 폰트 패밀리명.

    scale: 발표 슬라이드용으로 글자를 키우려면 1.2~1.4.
    """
    family = _register_korean_font()

    mpl.rcParams.update({
        "font.family": family,
        "axes.unicode_minus": False,      # 한글 폰트에서 음수 부호 깨짐 방지

        "figure.figsize": (9, 5.5),
        "figure.dpi": 110,
        "savefig.dpi": 200,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",

        "font.size": 11 * scale,
        "axes.titlesize": 15 * scale,
        "axes.labelsize": 11.5 * scale,
        "xtick.labelsize": 10 * scale,
        "ytick.labelsize": 10 * scale,
        "legend.fontsize": 10 * scale,

        "axes.titleweight": "bold",
        "axes.titlepad": 14,
        "axes.labelcolor": C["subtext"],
        "text.color": C["text"],
        "xtick.color": C["subtext"],
        "ytick.color": C["subtext"],

        # 군더더기 제거 — 데이터에 잉크를 몰아준다
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.edgecolor": C["grid"],
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": C["grid"],
        "grid.linewidth": 0.8,
        "grid.alpha": 1.0,
        "xtick.major.size": 0,
        "ytick.major.size": 0,

        "legend.frameon": False,
        "lines.linewidth": 2.2,
        "lines.markersize": 6,
        "axes.prop_cycle": mpl.cycler(color=CAT),
    })
    return family


def grid_x_only(ax) -> None:
    """세로 막대그래프용: 가로 격자선만 남긴다."""
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", visible=True)


def grid_y_only(ax) -> None:
    """가로 막대그래프용: 세로 격자선만 남긴다."""
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)


def source(ax, text: str) -> None:
    """출처 표기. 모든 차트에 붙인다 (CLAUDE.md 하드 룰 5)."""
    ax.figure.text(0.005, -0.02, f"출처: {text}",
                   ha="left", va="top", fontsize=8.5, color=C["subtext"])


FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")


def save(fig, name: str, svg: bool = True) -> str:
    """figures/ 에 저장. 발표용 벡터(svg)도 함께 남긴다."""
    os.makedirs(FIG_DIR, exist_ok=True)
    png = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(png)
    if svg:
        fig.savefig(os.path.join(FIG_DIR, f"{name}.svg"))
    return png


def choropleth(gdf, column, *, ax=None, cmap=SEQ, k=5, scheme="quantiles",
               label_col=None, legend_title=None, fmt="{:,.1f}", unit="",
               figsize=(9, 7.5)):
    """단계구분도 표준 그리기.

    직접 gdf.plot(legend=True) 하면 세 가지가 깨진다 — 실측으로 확인한 문제들:
      1) 범례가 지도 위를 덮어 지역 라벨을 가린다  → 범례를 축 바깥으로 뺀다
      2) 범례가 "10.00, 21.10" 처럼 나온다        → "10.0 ~ 21.1" 구간 표기로 바꾼다
      3) 어두운 폴리곤 위 검은 글씨가 안 읽힌다    → 밝기 계산해 흰/검정 자동 선택

    label_col: 폴리곤 위에 표시할 지역명 컬럼 (없으면 라벨 생략)
    반환: (ax, classifier)
    """
    import mapclassify
    import numpy as np
    from matplotlib import colormaps
    from matplotlib.patches import Patch

    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    vals = gdf[column].astype(float)
    cls = mapclassify.classify(vals.values, scheme, k=k)
    cmap_obj = colormaps[cmap] if isinstance(cmap, str) else cmap

    gdf.plot(column=column, cmap=cmap, scheme=scheme, k=k, ax=ax,
             edgecolor="white", linewidth=0.6, legend=False)

    # ── 범례: 축 바깥 + 구간 표기 ──
    edges = [vals.min()] + list(cls.bins)
    handles = [
        Patch(facecolor=cmap_obj((i + 0.5) / cls.k), edgecolor="white",
              label=f"{fmt.format(edges[i])} ~ {fmt.format(edges[i+1])}{unit}")
        for i in range(cls.k)
    ]
    ax.legend(handles=handles, title=legend_title or column,
              loc="center left", bbox_to_anchor=(1.01, 0.5),
              frameon=False, fontsize=9.5, title_fontsize=10.5,
              labelspacing=0.7, handlelength=1.4)

    # ── 지역 라벨: 배경 밝기에 따라 글자색 자동 ──
    if label_col:
        for _, r in gdf.iterrows():
            rgba = cmap_obj((cls.yb[gdf.index.get_loc(_)] + 0.5) / cls.k)
            lum = 0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]
            c = r.geometry.representative_point()
            ax.annotate(str(r[label_col]), (c.x, c.y), ha="center", va="center",
                        fontsize=9, color="white" if lum < 0.55 else C["text"])

    ax.set_axis_off()
    return ax, cls
