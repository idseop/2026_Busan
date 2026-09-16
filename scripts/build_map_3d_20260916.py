"""Fetch bounded OSM height-tagged footprints once; never invent building heights."""
from pathlib import Path
import json,re,hashlib,urllib.request,urllib.parse,datetime
from shapely.geometry import shape,Polygon,mapping
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1];N=R/'data/processed/지도입증확장-20260916/map';N.mkdir(parents=True,exist_ok=True);W=R/'web/final'
readjs=lambda p:json.loads(p.read_text(encoding='utf-8').split('=',1)[1].rstrip(';\n'))
districts=readjs(W/'data/map-data.js');boundary=unary_union([shape(x['geometry']) for x in districts['features']])
west,south,east,north=boundary.bounds
query=f'[out:json][timeout:90];way["building"]["height"]({south},{west},{north},{east});out tags geom;'
raw=N/'osm-height-ways.json';url='https://overpass-api.de/api/interpreter'
if not raw.exists():
 req=urllib.request.Request(url,data=urllib.parse.urlencode({'data':query}).encode(),headers={'User-Agent':'Busan119ResearchMap/1.0 (bounded academic map height inspection)'})
 with urllib.request.urlopen(req,timeout=110) as response:raw.write_bytes(response.read())
d=json.loads(raw.read_text(encoding='utf-8'));features=[];excluded=[]
for x in d.get('elements',[]):
 reason='';tag=x.get('tags',{}).get('height','').strip();match=re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:m)?',tag)
 ring=[[v['lon'],v['lat']] for v in x.get('geometry',[])];height=float(match[1]) if match else None
 if not match or height<=0:reason='height is not an explicit positive metre number'
 elif len(ring)<4 or ring[0]!=ring[-1]:reason='not a closed polygon way'
 else:
  p=Polygon(ring)
  if not p.is_valid:reason='invalid footprint'
  elif not boundary.covers(p):reason='footprint not fully inside verified Busan polygon'
 if reason:excluded.append({'osmWay':x['id'],'reason':reason});continue
 features.append({'type':'Feature','id':x['id'],'properties':{'osmWay':x['id'],'height':height,'rawHeight':tag,'name':x.get('tags',{}).get('name',''),'source':'OSM explicit height tag; not survey-verified'},'geometry':mapping(p)})
geo={'type':'FeatureCollection','features':features}
(W/'data/osm-height-buildings.js').write_text('window.BUSAN_HEIGHT_BUILDINGS='+json.dumps(geo,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
(N/'osm-height-buildings.geojson').write_text(json.dumps(geo,ensure_ascii=False),encoding='utf-8')
(N/'excluded-buildings.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2),encoding='utf-8')
manifest={'query':query,'url':url,'acquired':datetime.datetime.fromtimestamp(raw.stat().st_mtime,datetime.timezone.utc).isoformat(),'acquiredBasis':'Cached raw file download modification time; rebuilding does not imply refetch','osmBaseTimestamp':d.get('osm3s',{}).get('timestamp_osm_base'),'rawSha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'selected':len(features),'excluded':len(excluded),'heightDefinition':'Only explicit positive numeric OSM height (metres); no render_height, storey multiplier or default height. OSM tag is not independently surveyed. Unknown building height remains 2D.','coverage':'Closed building ways only, entire polygon covered by reused Busan geometry. Relations/parts and untagged heights omitted. No 119 incident positions joined.','attribution':'© OpenStreetMap contributors (ODbL). OpenFreeMap / OpenMapTiles source attribution retained separately.'}
(N/'building-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
world=Polygon([[-180,-85],[180,-85],[180,85],[-180,85],[-180,-85]])
outside={'type':'Feature','properties':{},'geometry':mapping(world.difference(boundary))}
(W/'data/busan-outside-mask.js').write_text('window.BUSAN_OUTSIDE_MASK='+json.dumps(outside,separators=(',',':'))+';',encoding='utf-8')
index=W/'index.html'
if not (N/'before-index.html').exists():(N/'before-index.html').write_bytes(index.read_bytes())
html=index.read_text(encoding='utf-8')
if 'rel="icon"' not in html:html=html.replace('</head>','<link rel="icon" href="data:,"></head>')
if 'assets/map-engine-3d.css' not in html:html=html.replace('</head>','<link rel="stylesheet" href="assets/map-engine-3d.css"></head>')
if 'assets/map-engine-3d.js' not in html:html=html.replace('<script defer src="assets/basemap.js"></script>','<script defer src="assets/basemap.js"></script><script defer src="data/osm-height-buildings.js"></script><script defer src="data/busan-outside-mask.js"></script><script defer src="assets/map-engine-3d.js"></script>')
if 'assets/regional-evidence.css' not in html:html=html.replace('</head>','<link rel="stylesheet" href="assets/regional-evidence.css"></head>')
if 'assets/regional-evidence.js' not in html:html=html.replace('<script defer src="assets/app.js">','<script defer src="data/regional-evidence.js"></script><script defer src="assets/regional-evidence.js"></script><script defer src="assets/app.js">')
index.write_text(html,encoding='utf-8')
print('height footprints',len(features),'excluded',len(excluded))
