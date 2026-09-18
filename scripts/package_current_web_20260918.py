"""Package only the active two-page site and its runtime assets."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import re,json,hashlib
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web/submission'
AUDIT=ROOT/'data/processed/최신웹연결-20260918'
out=ROOT/'output/부산119-최신지도와분석결과-20260918.zip'
files={WEB/x for x in ['index.html','serve.py','실행.cmd','README.md']}
html=(WEB/'index.html').read_text(encoding='utf-8')
for path in re.findall(r'(?:src|href)="([^"]+)"',html):
    if path.startswith(('assets/','data/')):files.add(WEB/path)
files.add(WEB/'data/fire-stations.json')
files.update(p for p in (WEB/'assets/vendor').rglob('*') if p.is_file())
files.update(p for p in (WEB/'analysis').rglob('*') if p.is_file())
assert all(p.is_file() for p in files)
with ZipFile(out,'w',ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,p.relative_to(WEB).as_posix())
with ZipFile(out) as z:
    assert z.testzip() is None
    for p in files:assert z.read(p.relative_to(WEB).as_posix())==p.read_bytes()
result=dict(path=out.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),files=len(files),bytes=out.stat().st_size,
    runtimeHashes={p.relative_to(WEB).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)},
    oldPagePayloadsIncluded=False,rawCallsIncluded=False)
(AUDIT/'package.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='runtimeHashes'},ensure_ascii=False))
