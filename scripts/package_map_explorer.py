"""Check frozen public inputs and package the tested map application."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    freeze=json.loads((OUT/'input_freeze.json').read_text(encoding='utf-8'))
    for item in freeze['files']:
        p=ROOT/item['path'];assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],str(p)
    browser=json.loads((OUT/'browser/result.json').read_text(encoding='utf-8'))
    assert browser['status']=='passed'
    current={str(p.relative_to(ROOT)):sha(p) for p in SITE.rglob('*') if p.is_file()}
    assert current==browser['site_sha256'],'Changed website requires verification before packaging.'
    pc_path=OUT/'pc-refinement/result.json'
    pc=json.loads(pc_path.read_text(encoding='utf-8'))
    assert pc['status']=='passed' and current==pc['site_sha256'],'PC refinement must pass on the packaged website.'
    archive=ROOT/'output/부산119-지도탐색웹-20260915.zip';archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SITE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(SITE).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members=z.namelist()
        for name in members:assert hashlib.sha256(z.read(name)).hexdigest()==sha(SITE/name)
    result={'status':'passed','frozen_public_inputs':len(freeze['files']),'freeze_sha256':sha(OUT/'input_freeze.json'),'browser_evidence_sha256':sha(OUT/'browser/result.json'),'site_sha256':current,'archive':str(archive.relative_to(ROOT)),'archive_sha256':sha(archive),'archive_members':members,'archive_crc_and_all_member_hashes':True}
    result['pc_evidence_sha256']=sha(pc_path)
    (OUT/'delivery.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(members)} files; {len(freeze["files"])} unchanged public data files; {archive.name}')

if __name__=='__main__':main()
