"""하네스 자가 점검 — `.venv/bin/python scripts/check_harness.py`

사람이 "제대로 했냐"고 물어야만 결함이 나오는 상황을 막으려고 만들었다.
지금까지 실제로 터졌던 결함들을 그대로 검사 항목으로 박아 넣었다.
"""
from __future__ import annotations
import json, os, re, subprocess, sys, tempfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
FAIL, WARN = [], []


def sh(*a) -> str:
    return subprocess.run(a, capture_output=True, text=True).stdout


def check_clone_reproducible():
    """git 이 추적하는 것만으로 필수 폴더가 재현되는가.
    실제로 터졌던 결함: `data/raw/` 를 ignore 하면 `!data/**/.gitkeep` 이 먹지 않는다."""
    tracked = set(sh("git", "ls-files").split())
    need = [
        "data/raw/00_경계", "data/raw/01_인구", "data/raw/02_의료",
        "data/raw/03_폭염", "data/raw/04_침수", "data/raw/05_대응자원",
        "data/interim/00_경계", "data/interim/05_대응자원", "data/processed",
        "analysis/00_공통", "analysis/02_의료", "analysis/03_폭염",
        "analysis/04_침수", "analysis/05_종합",
        "notebooks/00_공통", "notebooks/03_폭염", "notebooks/05_종합",
        "figures/00_공통", "figures/05_종합", "web/data", "web/assets",
    ]
    for d in need:
        if not any(t.startswith(d + "/") for t in tracked):
            FAIL.append(f"클론 재현 불가: {d}/ 가 git 에 없다 (.gitignore 확인)")


def check_real_data_ignored():
    """실데이터는 여전히 무시되는가 (폴더만 살리려다 데이터까지 커밋되면 안 된다)."""
    probe = ROOT / "data/raw/03_폭염/__probe__.csv"
    probe.write_text("x\n", encoding="utf-8")
    try:
        if "__probe__" in sh("git", "status", "--porcelain", "data/"):
            FAIL.append("실데이터가 git 에 추적된다 (.gitignore 가 너무 느슨하다)")
    finally:
        probe.unlink(missing_ok=True)


def check_import_convention():
    """analysis/ 하위 스크립트가 임의의 cwd 에서도 style.py 를 찾는가.
    실제로 터졌던 결함: sys.path.insert(0, "analysis") 는 루트에서만 동작한다."""
    d = ROOT / "analysis/03_폭염"
    d.mkdir(parents=True, exist_ok=True)
    t = d / "__probe__.py"
    t.write_text(
        "import sys, pathlib\n"
        "sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))\n"
        "import matplotlib; matplotlib.use('Agg')\n"
        "from style import setup, choropleth, save\n"
        "print('OK', setup())\n", encoding="utf-8")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run([str(ROOT / ".venv/bin/python"), str(t)],
                               cwd=tmp, capture_output=True, text=True)
        if r.returncode != 0:
            FAIL.append(f"import 규약 깨짐 (다른 cwd 에서 실패): {r.stderr.strip().splitlines()[-1:]}")
        elif "Pretendard" not in r.stdout and "Nanum" not in r.stdout and "Gothic" not in r.stdout:
            WARN.append(f"한글 폰트 미검출: {r.stdout.strip()}")
    finally:
        t.unlink(missing_ok=True)


def check_no_fabricated_figures():
    """데이터가 하나도 없는데 그림이 있으면 꾸며낸 것이다.
    실제로 터졌던 결함: 가짜 부산 구 수치로 만든 테스트 차트를 공개 저장소에 커밋했다."""
    data_files = [p for p in (ROOT / "data").rglob("*") if p.is_file() and p.name != ".gitkeep"]
    figs = [p for p in (ROOT / "figures").rglob("*") if p.is_file() and p.name != ".gitkeep"]
    if figs and not data_files:
        FAIL.append(f"데이터 0건인데 그림 {len(figs)}장 존재 → 꾸며낸 수치일 가능성: "
                    + ", ".join(p.name for p in figs[:4]))


def check_no_unsourced_numbers():
    """문서의 통계 수치에 출처가 붙어 있는가 (하드 룰 5)."""
    skip = ("refs/", "scripts/")
    for f in sh("git", "ls-files").split():
        if not f.endswith(".md") or f.startswith(skip):
            continue
        for i, line in enumerate(pathlib.Path(f).read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"\d+(\.\d+)?\s*(%|명|가구|개소)|\d{1,3}(,\d{3})+\s*건", line):
                if not re.search(r"출처|http|NN|○○|예시|플레이스홀더|10P|<", line):
                    WARN.append(f"출처 없는 수치? {f}:{i}  {line.strip()[:70]}")


def check_path_references():
    """문서가 존재하지 않는 경로를 가리키는가."""
    for f in sh("git", "ls-files").split():
        if not f.endswith(".md"):
            continue
        s = pathlib.Path(f).read_text(encoding="utf-8")
        for m in set(re.findall(r"`((?:docs|analysis|data|figures|web|refs|notebooks|scripts)/[^`\s]+)`", s)):
            base = m.rstrip("/")
            if not (ROOT / base).exists() and not (ROOT / base).parent.exists():
                FAIL.append(f"없는 경로 참조: {f} → {m}")


def check_harness_files():
    """스킬·에이전트·커맨드 프론트매터와 settings JSON."""
    import glob
    for f in glob.glob(".claude/skills/*/SKILL.md") + glob.glob(".claude/agents/*.md") + glob.glob(".claude/commands/*.md"):
        head = pathlib.Path(f).read_text(encoding="utf-8")
        if not head.startswith("---\n"):
            FAIL.append(f"프론트매터 없음: {f}")
        name = re.search(r"^name:\s*(\S+)", head, re.M)
        if "/skills/" in f and name and name.group(1) != pathlib.Path(f).parent.name:
            FAIL.append(f"스킬 name 불일치: {f} ({name.group(1)})")
    for f in [".claude/settings.json", ".claude/settings.local.json"]:
        if pathlib.Path(f).exists():
            try:
                json.load(open(f, encoding="utf-8"))
            except Exception as e:
                FAIL.append(f"JSON 오류 {f}: {e}")
    if pathlib.Path(".claude/settings.json").exists():
        if "/Users/" in pathlib.Path(".claude/settings.json").read_text(encoding="utf-8"):
            FAIL.append("settings.json 에 홈 경로 노출 (settings.local.json 으로 옮길 것)")


def check_catalog_matches_data():
    """받은 데이터가 카탈로그에 등재돼 있는가 (하드 룰 3)."""
    files = [p for p in (ROOT / "data/raw").rglob("*") if p.is_file() and p.name != ".gitkeep"]
    if not files:
        return
    idx = ROOT / "docs/20-데이터카탈로그/INDEX.md"
    if not idx.exists():
        FAIL.append(f"데이터 {len(files)}건을 받았는데 카탈로그가 없다 (하드 룰 3)")
        return
    cat = idx.read_text(encoding="utf-8")
    for p in files:
        if p.stem not in cat and p.name not in cat:
            WARN.append(f"카탈로그 미등재 데이터: {p.relative_to(ROOT)} (하드 룰 3)")


def check_branch():
    b = sh("git", "branch", "--show-current").strip()
    if b == "main":
        WARN.append("현재 브랜치가 main 이다. 작업은 develop 에서 한다 (하드 룰 11)")


CHECKS = [
    ("클론 재현성", check_clone_reproducible),
    ("실데이터 무시", check_real_data_ignored),
    ("import 규약", check_import_convention),
    ("꾸며낸 그림", check_no_fabricated_figures),
    ("출처 없는 수치", check_no_unsourced_numbers),
    ("경로 참조", check_path_references),
    ("하네스 파일", check_harness_files),
    ("카탈로그 정합", check_catalog_matches_data),
    ("브랜치", check_branch),
]

if __name__ == "__main__":
    print(f"하네스 점검 — {ROOT.name}\n")
    for label, fn in CHECKS:
        before = len(FAIL), len(WARN)
        try:
            fn()
        except Exception as e:
            FAIL.append(f"[{label}] 점검 자체가 실패: {type(e).__name__}: {e}")
        f, w = len(FAIL) - before[0], len(WARN) - before[1]
        mark = "✗" if f else ("!" if w else "✓")
        print(f"  {mark} {label}" + (f"   결함 {f}" if f else "") + (f"   경고 {w}" if w else ""))

    if FAIL:
        print("\n■ 결함")
        for x in FAIL: print("  ✗", x)
    if WARN:
        print("\n■ 경고 (판단 필요)")
        for x in WARN: print("  !", x)
    if not FAIL and not WARN:
        print("\n이상 없음.")
    print()
    sys.exit(1 if FAIL else 0)
