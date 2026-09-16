"""Validate named district summaries and reference-label points, not historical areas."""
from pathlib import Path
import json,hashlib
from collections import Counter
import pandas as pd
from shapely.geometry import shape
from shapely.ops import transform
from pyproj import Transformer
R=Path(__file__).resolve().parents[2]; O=R/'data/processed/심층분석-20260915';O.mkdir(parents=True,exist_ok=True)
G=R/'web/final/data/map-data.js';D=R/'web/final/data/dashboard.json';P=R/'data/processed/컬럼선별-결측제외-20260915/population/complete_population_dong.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
geo=json.loads(G.read_text(encoding='utf-8').split('=',1)[1].strip().removesuffix(';'))
data=json.loads(D.read_text(encoding='utf-8')); pop=pd.read_csv(P,dtype=str,keep_default_na=False)
labels={};rows=[]
forward=Transformer.from_crs(4326,5179,always_xy=True).transform;inverse=Transformer.from_crs(5179,4326,always_xy=True).transform
for f in geo['features']:
    g=shape(f['geometry']); metric=transform(forward,g); point=metric.representative_point(); ll=transform(inverse,point)
    assert g.is_valid and metric.contains(point) and g.contains(ll)
    name=f['properties']['name'];labels[name]=[ll.x,ll.y]
    rows.append({'district':name,'longitude':ll.x,'latitude':ll.y,'within_reference_geometry':True,'reference_area_km2':metric.area/1e6,'point_method':'EPSG5179 representative_point, transformed to EPSG4326','meaning':'label/symbol anchor; not a receipt location or facility'})
assert len(labels)==16
registry={y:dict(pop.loc[pop.year.eq(str(y)),['district_name','district_code']].drop_duplicates().values) for y in range(2020,2025)}
assert all(set(v)==set(labels) and len(v)==16 for v in registry.values())
assert all(v==registry[2020] for v in registry.values())
counts=Counter();minor=Counter()
for r in data['rawRegions']:
    assert r['district'] in labels
    for typ,n in r['typeCounts'].items():counts[(r['year'],r['scope'],r['district'],typ)]+=n;minor[(r['year'],r['scope'],typ)]+=n
assert all(minor[(r['year'],r['scope'],r['type'])]==r['count'] for r in data['yearly'])
for s,total in [('A',704689),('B',579412),('C',574662)]:assert sum(n for (y,scope,d,t),n in counts.items() if scope==s)==total
table=[{'year':y,'scope':s,'district':d,'district_code':registry[y][d],'type':t,'count':n,'geographic_assignment':False,'aggregation_basis':'recorded CLMTY_SGG_NM'} for (y,s,d,t),n in sorted(counts.items())]
pd.DataFrame(table).to_csv(O/'district_symbol_counts.csv',index=False,encoding='utf-8-sig')
(O/'district_label_points.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
L=R/'web/final/data/map-labels.js';L.write_text('window.BUSAN_MAP_LABELS='+json.dumps(labels,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
law=O/'official_district_change_web_extract.json'
result={'status':'conditional_symbol_map_allowed','checked_at':'2026-09-15','decision':{'recorded_district_aggregate_symbols':True,'historical_same_boundary_choropleth':False,'historical_receipt_point_assignment':False,'administrative_dong_assignment':False},'reason':'Recorded district labels match all 16 official year-end district name/code pairs in all five years, so named-entity receipt totals can be displayed as symbols. Stable district codes do not prove stable boundaries. An official within-period district-boundary change disproves the unchanged-boundary premise.','law_counterexample':{'title':'부산광역시 해운대구와 금정구의 관할구역 변경에 관한 규정','promulgation_number':'대통령령 제30671호','promulgation_date':'2020-05-12','effective_date':'2020-06-12','from_district':'금정구','to_district':'해운대구','parcels':['금사동 62의 1번지','금사동 62의 13번지'],'annex_note':'해당 필지는 본문에 직접 열거되어 있다. 별표 첨부의 필지라고 표현하지 않는다.','url':'https://www.law.go.kr/lsInfoP.do?lsiSeq=217917&efYd=20200612','local_evidence':str(law.relative_to(R)),'sha256':sha(law),'evidence_format':'Official web/search extracted text, not original HTML','not_exhaustive_change_history':True},'label_required':['2020~2024 선택17 완전행의 원문 구군별 신고접수 집계','2025-06-30 윤곽은 현재 위치 참고용; 기호는 구군 대표 위치이며 실제 신고 위치가 아님','부산 전체 신고의 대표 건수·위험률·고정경계별 비교가 아님','2020-06-12 금정구 일부필지의 해운대구 편입; 원문 구군명 유지, 과거경계 재배정 없음'],'symbol_encoding':'Circle AREA, not radius, proportional to count; identical scale within an active filter; distinguish zero from missing; keep fill of reference polygons neutral. Number labels and keyboard-accessible tooltips show exact selected counts.','callout_recommendation':['중구','동구','서구','연제구','수영구'],'label_points':{'count':16,'all_inside_reference_polygon':True,'crs':'EPSG4326','js':str(L.relative_to(R)),'sha256':sha(L)},'reconciliation':{'year_scope_type_cells':len(minor),'district_year_scope_type_cells':len(table),'A':704689,'B':579412,'C':574662,'all_60_cells_reconcile':True,'all_five_year_district_name_code_sets_equal':True,'geometries_not_compared_to_historical_boundaries':True},'input_hashes':{str(p.relative_to(R)):sha(p) for p in [G,D,P]},'output_hashes':{str(p.relative_to(R)):sha(p) for p in [L,O/'district_symbol_counts.csv',O/'district_label_points.json']},'script_sha256':sha(Path(__file__))}
(O/'map_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result['reconciliation'],ensure_ascii=False));print('labels:',len(labels))
