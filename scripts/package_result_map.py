from pathlib import Path
import hashlib,json,zipfile,base64
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915/result-map'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
test=json.loads((OUT/'result.json').read_text(encoding='utf-8'));assert test['status']=='passed'
current={str(p.relative_to(ROOT)):sha(p) for p in sorted(WEB.rglob('*')) if p.is_file()}
assert current==test['site_sha256'],'Website changed after tests'
freeze=json.loads((OUT.parent/'input_freeze.json').read_text(encoding='utf-8'))
for item in freeze['files']:assert sha(ROOT/item['path'])==item['sha256']
vendor={}
for name,expected in [('leaflet.js','20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='),('leaflet.css','p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=')]:
 p=WEB/'assets/vendor/leaflet'/name;actual=base64.b64encode(hashlib.sha256(p.read_bytes()).digest()).decode();assert actual==expected;vendor[name]=actual
live=json.loads((OUT/'live/live-verification.json').read_text(encoding='utf-8'));assert live['state']['contextReady'] and not live['errors'];assert all(r['referer'].startswith('http://127.0.0.1:8765/') for r in live['requests'])
independent=json.loads((OUT.parent/'context-map/independent-result.json').read_text(encoding='utf-8'));assert independent['status']=='passed'
for path,digest in independent['files'].items():assert sha(ROOT/path)==digest,'Independent data verification changed'
sources=json.loads((OUT.parent/'context-map/sources.json').read_text(encoding='utf-8'))
for item in sources['libraries']:assert sha(ROOT/item['file'])==item['sha256'],'Library changed after provenance capture'
archive=ROOT/'output/부산119-지도결과웹-20260915.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(WEB.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(WEB).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==sha(WEB/name)
 members=z.namelist()
(OUT/'delivery.json').write_text(json.dumps({'status':'passed','archive':str(archive.relative_to(ROOT)),'sha256':sha(archive),'members':members,'site_sha256':current,'immutable_data_files':len(freeze['files']),'official_leaflet_hashes':vendor,'test_checks':len(test['checks']),'live_tiles':live['state']['loadedTiles'],'no_tile_archive':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(f'PASS: {len(members)} files; official Leaflet hashes; immutable data; live map and ZIP verified')
