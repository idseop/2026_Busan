"""Build cartographic dong name anchors from the archived official SGIS polygons.

Run with a Python environment containing pyshp, shapely and pyproj.
These anchors describe the 2025-06-30 reference geography only.
"""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import warnings

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import Point, shape


ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'data/raw/공간안전/국가데이터처_SGIS 행정구역 통계 및 경계.zip'
    interim = ROOT / 'data/interim/공간안전'
    manifest = json.loads((interim / 'manifest.json').read_text(encoding='utf-8'))
    audit = json.loads((interim / 'boundary-audit.json').read_text(encoding='utf-8'))
    digest = hashlib.file_digest(source.open('rb'), 'sha256').hexdigest()
    assert digest == manifest['sha256'], 'Archived source hash changed'
    map_path = ROOT / 'web/final/data/map-data.js'
    map_data = json.loads(map_path.read_text(encoding='utf-8').split('=', 1)[1].strip().removesuffix(';'))
    assert map_data['metadata']['sourceSha256'] == digest
    districts = {f['properties']['sgisCode']: f['properties']['name'] for f in map_data['features']}
    layer = 'bnd_dong_00_2025_2Q'
    expected = {r['ADM_CD']: r for r in audit[layer]['busan_rows']}
    places, valid_codes = [], []
    with zipfile.ZipFile(source) as archive:
        def member(ext):
            return next(n for n in archive.namelist() if n.endswith(layer + '.' + ext))
        crs = CRS.from_wkt(archive.read(member('prj')).decode())
        # SGIS uses ESRI datum names, so compare the full projected parameters.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            assert crs.to_dict() == CRS.from_epsg(5179).to_dict()
        transform = Transformer.from_crs(crs, 4326, always_xy=True)
        inverse = Transformer.from_crs(4326, crs, always_xy=True)
        encoding = archive.read(member('cpg')).decode().strip()
        reader = shapefile.Reader(**{ext: io.BytesIO(archive.read(member(ext))) for ext in ('shp', 'shx', 'dbf')}, encoding=encoding)
        for item in reader.iterShapeRecords():
            row = item.record.as_dict()
            code = row['ADM_CD']
            if not code.startswith('21'):
                continue
            assert row == expected[code], f'Attribute audit mismatch: {code}'
            assert row['BASE_DATE'] == '20250630'
            geom = shape(item.shape.__geo_interface__)
            assert geom.is_valid and not geom.is_empty, f'Invalid source polygon: {code}'
            polygon = max(geom.geoms, key=lambda p: p.area) if geom.geom_type == 'MultiPolygon' else geom
            anchor = polygon.representative_point()
            lng, lat = transform.transform(anchor.x, anchor.y)
            lat, lng = round(lat, 7), round(lng, 7)
            assert polygon.covers(Point(*inverse.transform(lng, lat))), f'Rounded anchor outside: {code}'
            assert 34.8 < lat < 35.5 and 128.7 < lng < 129.4
            places.append(dict(name=row['ADM_NM'], district=districts[code[:5]], code=code, lat=lat, lng=lng))
            valid_codes.append(code)
    assert len(set(valid_codes)) == len(valid_codes) == len(expected) == audit[layer]['busan_records']
    assert set(valid_codes) == set(expected)
    places.sort(key=lambda p: p['code'])
    metadata = dict(sourceUrl=manifest['source'], sourceSha256=digest,
                    baseDate='2025-06-30', sourceLayer=layer, outputCrs='EPSG:4326',
                    usage='cartographic_reference_labels_only', renderingOnly=True,
                    canAssignHistoricalReceipts=False, canDisplayHistoricalCounts=False,
                    pointMethod='representative_point_of_largest_polygon_in_EPSG5179',
                    placeCount=len(places),
                    limitation='2025-06-30 행정동·읍면 이름을 표시하는 참고 위치. 과거 신고 배정 및 사건 위치가 아님.')
    output = ROOT / 'web/final/data/place-labels.js'
    output.write_text('window.BUSAN_PLACE_LABELS = ' + json.dumps(dict(metadata=metadata, places=places), ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    report = dict(metadata=metadata, sourceHashMatchesManifest=True,
                  sourceHashMatchesMap=True, allAttributesMatchAudit=True,
                  sourceGeometryValidCount=len(valid_codes),
                  roundedAnchorsInsideLargestPolygonCount=len(valid_codes),
                  uniqueCodeCount=len(set(valid_codes)), districtCount=len({p['district'] for p in places}),
                  outputSha256=hashlib.sha256(output.read_bytes()).hexdigest(),
                  countsByDistrict={d: sum(p['district'] == d for p in places) for d in sorted(districts.values())})
    validation = ROOT / 'data/processed/지도탐색웹-20260915/place-labels-validation.json'
    validation.parent.mkdir(parents=True, exist_ok=True)
    validation.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
