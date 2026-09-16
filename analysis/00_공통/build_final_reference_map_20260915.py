"""Render-only generalized reference outlines. Never classify or aggregate receipts."""
from pathlib import Path
import json,hashlib
from shapely.geometry import shape,mapping
from shapely.ops import transform
from pyproj import Transformer
R=Path(__file__).resolve().parents[2]
S=R/'data/processed/최종결과-20260915/reference_districts.geojson';T=R/'web/final/data/map-data.js';L=R/'data/interim/최종보완근거-20260915/map-simplification-validation.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
g=json.loads(S.read_text(encoding='utf8'));to_m=Transformer.from_crs(4326,5179,always_xy=True).transform;to_ll=Transformer.from_crs(5179,4326,always_xy=True).transform
out=[];checks=[]
for f in g['features']:
 original=transform(to_m,shape(f['geometry']));simple=original.simplify(10,preserve_topology=True);render=transform(to_ll,simple)
 assert original.is_valid and simple.is_valid and render.is_valid and not render.is_empty
 rel=abs(simple.area-original.area)/original.area;dist=original.hausdorff_distance(simple)
 assert rel<.005 and dist<=20.01,(f['properties']['name'],rel,dist)
 bounds=render.bounds;assert 128<bounds[0]<bounds[2]<130 and 34<bounds[1]<bounds[3]<36
 out.append({'type':'Feature','properties':f['properties'],'geometry':mapping(render)})
 checks.append({'name':f['properties']['name'],'valid':True,'area_before_m2':original.area,'area_after_m2':simple.area,'relative_area_error':rel,'boundary_hausdorff_m':dist,'bounds_epsg4326':list(bounds)})
result={'type':'FeatureCollection','metadata':{**g['metadata'],'renderSourceSha256':sha(S),'simplified':True,'simplificationCrs':'EPSG:5179','toleranceMetres':10,'preserveTopology':True,'renderingOnly':True,'limitation':'2025-06-30 현재참고구군윤곽의10m간소화.2020~2024사건값지도·주소/좌표배정·거리계산용아님.'},'features':out}
assert len(out)==16;T.parent.mkdir(parents=True,exist_ok=True);T.write_text('window.BUSAN_MAP = '+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
log={'source':str(S.relative_to(R)),'source_sha256':sha(S),'source_bytes':S.stat().st_size,'output':str(T.relative_to(R)),'output_sha256':sha(T),'output_bytes':T.stat().st_size,'tolerance_m':10,'metric_crs':'EPSG:5179','preserve_topology':True,'features':16,'checks':checks,'source_untouched':True,'use':'rendering reference only; no historical receipt values or geographic assignment'}
L.write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'bytes':T.stat().st_size,'max_relative_area_error':max(c['relative_area_error'] for c in checks),'max_hausdorff_m':max(c['boundary_hausdorff_m'] for c in checks)},ensure_ascii=False))
