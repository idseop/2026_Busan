"""SGIS 공식 2025 경계를 원형 보존하여 웹 표시용 경위도로 변환한다."""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import mapping, shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/raw/공간안전/국가데이터처_SGIS 행정구역 통계 및 경계.zip'
TARGET = ROOT / 'web/data/busan-districts.geojson'
AUDIT = ROOT / 'data/interim/웹경계검증/manifest.json'


def main():
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    recorded = json.loads((ROOT / 'data/interim/공간안전/manifest.json').read_text(encoding='utf-8'))
    assert source_hash == recorded['sha256']
    with zipfile.ZipFile(SOURCE) as z:
        stems = [n[:-4] for n in z.namelist() if n.endswith('bnd_sigungu_00_2025_2Q.shp')]
        assert len(stems) == 1
        stem = stems[0]
        wkt = z.read(stem + '.prj').decode('utf-8')
        source_crs = CRS.from_wkt(wkt)
        assert source_crs.to_epsg() == 5179
        forward = Transformer.from_crs(source_crs, 4326, always_xy=True)
        reverse = Transformer.from_crs(4326, source_crs, always_xy=True)
        reader = shapefile.Reader(shp=io.BytesIO(z.read(stem + '.shp')),
                                  shx=io.BytesIO(z.read(stem + '.shx')),
                                  dbf=io.BytesIO(z.read(stem + '.dbf')), encoding='utf-8')
        features, checks = [], []
        for sr in reader.iterShapeRecords():
            props = sr.record.as_dict()
            if not props['SIGUNGU_CD'].startswith('21'):
                continue
            assert props['BASE_DATE'] == '20250630'
            original = shape(sr.shape.__geo_interface__)
            assert original.is_valid and not original.is_empty and original.area > 0
            geo = transform(forward.transform, original)
            assert geo.is_valid and not geo.is_empty
            west, south, east, north = geo.bounds
            assert 128 < west <= east < 130 and 34 < south <= north < 36
            restored = transform(reverse.transform, geo)
            relative_area_error = abs(restored.area - original.area) / original.area
            max_boundary_distance = original.hausdorff_distance(restored)
            assert relative_area_error < 1e-8 and max_boundary_distance < 0.001
            features.append({'type': 'Feature', 'properties': {'name': props['SIGUNGU_NM'],
                             'sgisCode': props['SIGUNGU_CD'], 'baseDate': '2025-06-30'},
                             'geometry': mapping(geo)})
            checks.append({'name': props['SIGUNGU_NM'], 'source_area_m2': original.area,
                           'inverse_area_m2': restored.area, 'relative_area_error': relative_area_error,
                           'inverse_hausdorff_m': max_boundary_distance, 'wgs84_bounds': geo.bounds,
                           'valid_source': original.is_valid, 'valid_output': geo.is_valid,
                           'source_points': len(sr.shape.points)})
    names = {f['properties']['name'] for f in features}
    assert len(features) == len(names) == 16
    receipt_path = ROOT / 'data/processed/119기초분석/부산명시_연도구군종별분류처리결과.csv'
    population_path = ROOT / 'data/processed/연령배경비교/부산_2018-2024_시구군_65세기준요약.csv'
    with receipt_path.open(encoding='utf-8-sig', newline='') as stream:
        receipts = list(csv.DictReader(stream))
    with population_path.open(encoding='utf-8-sig', newline='') as stream:
        population = list(csv.DictReader(stream))
    for year in range(2018, 2025):
        assert names == {r['재난시군구'] for r in receipts if r['연도'] == str(year) and r['재난시군구']}
        assert names == {r['행정구역명'].removeprefix('부산광역시 ') for r in population
                         if r['연도'] == str(year) and r['공간수준'] == '구군'}
    note = '2025-06-30 경계는 구군별 값의 화면 표시용이다. 2018~2024 당시 경계를 확보하거나 과거 주소·좌표를 2025 구역으로 재집계한 것이 아니다. 구군명 대응은 연령별 신고를 생성하지 않는다.'
    result = {'type': 'FeatureCollection', 'metadata': {'sourceUrl': 'https://www.data.go.kr/data/15129688/fileData.do',
              'sourceSha256': source_hash, 'baseDate': '2025-06-30', 'sourceCrs': source_crs.to_string(),
              'outputCrs': 'EPSG:4326', 'simplified': False, 'limitation': note},
              'features': sorted(features, key=lambda f: f['properties']['name'])}
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    # 직렬화된 결과 자체의 지오메트리도 검증한다.
    saved = json.loads(TARGET.read_text(encoding='utf-8'))
    assert all(shape(f['geometry']).is_valid and not shape(f['geometry']).is_empty for f in saved['features'])
    evidence = {'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': source_hash,
                'source_member': stem, 'source_prj': wkt, 'output': str(TARGET.relative_to(ROOT)),
                'output_sha256': hashlib.sha256(TARGET.read_bytes()).hexdigest(), 'output_bytes': TARGET.stat().st_size,
                'feature_count': len(features), 'all_7years_receipt_population_names_match': True,
                'simplified': False, 'limitation': note, 'checks': checks,
                'dependencies': {'pyshp': shapefile.__version__, 'source_crs': source_crs.to_string()},
                'reproduce': '.venv-check/Scripts/python.exe analysis/00_공통/build_busan_boundary.py'}
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'features': len(features), 'bytes': TARGET.stat().st_size,
                      'max_relative_area_error': max(c['relative_area_error'] for c in checks),
                      'max_inverse_distance_m': max(c['inverse_hausdorff_m'] for c in checks)}))


if __name__ == '__main__':
    main()
