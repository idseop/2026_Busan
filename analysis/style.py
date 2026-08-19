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
