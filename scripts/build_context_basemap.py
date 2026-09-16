"""Pin rendering libraries and derive a label-free contextual vector style."""
from pathlib import Path
import json,subprocess,hashlib
R=Path(__file__).resolve().parents[1];W=R/'web/final';V=W/'assets/vendor/maplibre';V.mkdir(parents=True,exist_ok=True)
files={
 'maplibre-gl.js':'https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.js',
 'maplibre-gl.css':'https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.css',
 'LICENSE.txt':'https://unpkg.com/maplibre-gl@5.6.1/LICENSE.txt',
 'leaflet-maplibre-gl.js':'https://unpkg.com/@maplibre/maplibre-gl-leaflet@0.1.4/leaflet-maplibre-gl.js',
 'leaflet-binding-LICENSE':'https://raw.githubusercontent.com/maplibre/maplibre-gl-leaflet/main/LICENSE',
 'style-LICENSE':'https://raw.githubusercontent.com/hyperknot/openfreemap-styles/main/LICENSE.md',
}
records=[]
for name,url in files.items():
 if not (V/name).exists():subprocess.run(['curl.exe','-sSfL',url,'-o',str(V/name)],check=True)
 records.append({'file':str((V/name).relative_to(R)),'url':url,'sha256':hashlib.sha256((V/name).read_bytes()).hexdigest()})
source=R/'data/processed/지도탐색웹-20260915/context-map/liberty-source.json'
source.parent.mkdir(parents=True,exist_ok=True)
if not source.exists():
 cached=R/'.omc/liberty-source.json'
 if cached.exists():source.write_bytes(cached.read_bytes())
 else:subprocess.run(['curl.exe','-sSfL','https://tiles.openfreemap.org/styles/liberty','-o',str(source)],check=True)
style=json.loads(source.read_text(encoding='utf-8'))
style['name']='Busan context: terrain, water, built form; no road names or POIs'
style['layers']=[l for l in style['layers'] if l['type'] not in ['symbol','fill-extrusion','raster'] and not l['id'].startswith('boundary') and 'pattern' not in l['id']]
style.pop('sprite',None);style.pop('glyphs',None);style['sources'].pop('ne2_shaded',None)
for layer in style['layers']:
 p=layer.setdefault('paint',{});id=layer['id']
 if id=='background':p['background-color']='#f4f1e8'
 if id=='water':p['fill-color']='#bedfe7'
 if id=='landcover_wood':p['fill-color']='#b7d6aa';p['fill-opacity']=.72
 if id in ['landcover_grass','park']:p['fill-color']='#d3e6bd';p['fill-opacity']=.65
 if id=='landuse_residential':p['fill-color']='#e9e7de'
 if id=='building':p['fill-color']='#d4d3c9';layer['minzoom']=14
 if id.startswith(('road_','bridge_','tunnel_')):
  p['line-opacity']=.65
style['sources']['openmaptiles']['bounds']=[128.75,34.87,129.32,35.41]
(W/'data/context-style.js').write_text('window.BUSAN_CONTEXT_STYLE='+json.dumps(style,ensure_ascii=False)+';\n',encoding='utf-8')
out=R/'data/processed/지도탐색웹-20260915/context-map';out.mkdir(exist_ok=True)
(out/'sources.json').write_text(json.dumps({'libraries':records,'styleSource':'https://tiles.openfreemap.org/styles/liberty','sourceStyleSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'policy':'https://openfreemap.org/','date':'2026-09-16','symbolLayers':0,'dataAttribution':'OpenFreeMap; © OpenMapTiles; © OpenStreetMap contributors'},ensure_ascii=False,indent=2),encoding='utf-8')
