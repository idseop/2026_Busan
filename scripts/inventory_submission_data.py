"""현재 분석·웹의 실제 활용데이터 검토 목록. 복사·압축·제출하지 않는다."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/50-제출준비'


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8-sig'))


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    rows = []
    def add(kind, file, source, role, expected=None, evidence=''):
        p = ROOT / file
        assert p.is_file(), file
        value = digest(p)
        if expected is not None:
            assert value == expected, f'기존 감사 해시 불일치: {file}'
        rows.append({'종류': kind, '경로': p.relative_to(ROOT).as_posix(),
                     'bytes': p.stat().st_size, 'sha256': value, '원출처': source,
                     '사용역할': role, '기존해시대조': '일치' if expected else '현시점 해시 기록',
                     '대조근거': evidence, '제출상태': '검토목록; 자동제출 없음'})

    receipt_audit = 'data/interim/119접수감사/audit.json'
    receipt = load(receipt_audit)['files']
    assert sorted(x['year'] for x in receipt) == list(range(2018, 2025))
    rsource = '사용자 제공 부산소방재난본부 원본; 공식 서버 해시 동일성 미확인; 컬럼 대조 https://bigdata-119.kr/goods/goodsInfo?goods_mng_sn=402'
    for r in sorted(receipt, key=lambda x: x['year']):
        add('source', r['file'], rsource, f"{r['year']}년 신고 원본; 기초분석·처리조건 비교", r['sha256'], receipt_audit)
    population_audit = 'data/interim/인구배경/audit.json'
    population = [r for r in load(population_audit)['files'] if '성연령별1인세대' not in r['file']]
    assert sorted(r['period'] for r in population) == [f'{y}-12' for y in range(2018, 2025)]
    psource = 'https://jumin.mois.go.kr/ageStatMonth.do'
    for r in sorted(population, key=lambda x: x['period']):
        add('source', r['file'], psource, f"{r['period']} 주민등록인구 원본; 전체 연령·65세 기준 배경", r['sha256'], population_audit)
    boundary_audit = 'data/interim/공간안전/manifest.json'
    boundary = load(boundary_audit)
    add('source', boundary['file'], boundary['source'], 'SGIS 배포 ZIP 원본; 내부 2025년 2분기 시군구 경계 중 부산만 지도 표시용 사용, 다른 수록 통계 미사용', boundary['sha256'], boundary_audit)

    cross_audit = 'data/processed/119기초분석/검증_manifest.json'
    cross = load(cross_audit)
    # 명시적 결과 파일 목록에서 CSV 7개만 선택한다.
    def entries(obj):
        if isinstance(obj, dict):
            if 'file' in obj and 'sha256' in obj:
                yield obj
            for value in obj.values():
                yield from entries(value)
        elif isinstance(obj, list):
            for value in obj:
                yield from entries(value)
    csvs = {r['file']: r for r in entries(cross) if r['file'].endswith('.csv') and 'processed' in r['file']}
    assert len(csvs) == 7
    for r in sorted(csvs.values(), key=lambda x: x['file']):
        add('derived', r['file'], rsource, '같은 원본 행의 차원별 교차집계; 파일 간 접수량 합산 금지', r['sha256'], cross_audit)
    condition_audit = 'data/processed/신고조건비교/manifest.json'
    condition = load(condition_audit)
    add('derived', 'data/processed/신고조건비교/연도구군_조건별접수건수_순위변화.csv', rsource,
        'A/B/C 조건별 구군 접수량·순위 민감도', condition['output_sha256'], condition_audit)
    ages_audit = 'data/processed/연령배경비교/검증_manifest.json'
    ages = [r for r in load(ages_audit)['outputs'] if r['file'].endswith('.csv')]
    assert len(ages) == 2
    for r in ages:
        add('derived', r['file'], psource, '주민등록인구 원본 1세별 합산; 신고자 연령 아님', r['sha256'], ages_audit)
    add('derived', 'web/data/dashboard.json', rsource + ' | ' + psource, '웹의 신고조건·전체연령·65세 기준 집계 표시')
    add('derived', 'web/data/busan-districts.geojson', boundary['source'], '2025년 2분기 부산 16구군 표시용 경계; EPSG:5179→4326, 과거 연도 경계 복원 아님')
    assert sum(r['종류'] == 'source' for r in rows) == 15
    assert sum(r['종류'] == 'derived' for r in rows) == 12
    assert len({r['경로'] for r in rows}) == 27
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / '실활용데이터-목록.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    total = sum(r['bytes'] for r in rows)
    (OUT / '실활용데이터-제출검토.md').write_text(
        '# 실제 활용데이터 제출 검토 목록\n\n'
        '현재 분석과 자체 웹에서 사용하는 원본 15개·파생자료 12개를 파일 실존·바이트·SHA256과 함께 목록화했다. '
        '검토 목록이며 접수·자동제출·파일 복사·압축은 수행하지 않았다.\n\n'
        f'- 목록: `실활용데이터-목록.csv` (27개, 합계 {total:,} bytes; 비압축 개별 파일 크기의 합계).\n'
        '- 원본: 119 신고 2018~2024년 7개, 같은 기간 연말 주민등록인구 7개, SGIS 배포 ZIP 1개. 기존 감사 해시와 모두 대조한다.\n'
        '- 파생자료: 119 교차 CSV 7개, 조건 비교 CSV 1개, 인구 요약 CSV 2개, 웹 JSON·GeoJSON 2개.\n'
        '- 1인세대·교통사고·지원시설·노인일자리 등 현재 분석에 사용하지 않은 후보는 포함하지 않는다. SGIS 원본 ZIP에 함께 든 다른 통계를 사용했다고 표시하지 않는다.\n'
        '- 공식 안내의 업로드 용량 제한과 큰 원본의 첨부 방식은 아직 확인되지 않았다. 목록과 실제 사용 범위·제출 권한을 검토한 뒤 최종 제출 패키지로 옮겨야 한다. 원본을 임의로 생략하거나 다른 형식 제출이 승인된 것으로 가정하지 않는다.\n'
        '- 여러 파생표는 동일 원본을 다른 차원에서 요약한 것이므로 파일 간 건수를 더하지 않는다. 원본과 파생자료를 분리해 설명한다.\n'
        '- 분석·웹 변경 후 목록을 다시 생성한다. 현재 해시는 최종 제출 완료 증빙이 아니다.\n\n'
        '재현: `.venv-check/Scripts/python.exe scripts/inventory_submission_data.py`\n\n'
        '공식 제출 요건: [대회 안내](https://www.dxchallenge.co.kr/dataanalysis-2026), [요강 정리](../00-공모요강.md).\n',
        encoding='utf-8')
    print(json.dumps({'sources': 15, 'derived': 12, 'files': len(rows), 'bytes': total, 'existingHashComparisons': sum(r['기존해시대조'] == '일치' for r in rows)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
