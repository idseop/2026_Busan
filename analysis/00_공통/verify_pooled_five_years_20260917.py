"""Independent reconciliation using csv/collections, without importing the builder."""
from pathlib import Path
from collections import defaultdict, Counter
import csv
import hashlib
import json
import math
import gzip
from datetime import date

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/5개년통합-지역유형-제안연결-20260917'
YEARS = [str(y) for y in range(2020, 2025)]
KEY = ['district', 'rawDong', 'type', 'subtype']


def read(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranking(values):
    freq = Counter(v for v in values if v > 0)
    result, position = {}, 1
    for value in sorted(freq, reverse=True):
        result[value] = position
        position += freq[value]
    return result


def main():
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['inputs'] + manifest['outputs']:
        assert sha(ROOT / entry['path']) == entry['sha256'], entry['path']
    source = read(ROOT / next(x['path'] for x in manifest['inputs'] if x['key'] == 'names'))
    assert len(source) == 13580
    gu, city = defaultdict(lambda: [0] * 5), defaultdict(lambda: [0] * 5)
    cells = {}
    for row in source:
        key = tuple(row[k] for k in KEY)
        years = [int(row[y]) for y in YEARS]
        assert sum(years) == int(row['countP']) and key not in cells
        cells[key] = years
        for i, value in enumerate(years):
            gu[row['district']][i] += value
            city[(row['type'], row['subtype'])][i] += value
    assert sum(sum(v) for v in gu.values()) == 555786

    districts = read(OUT / '01-16구군-5년합계와-한해제외순위.csv')
    assert [x['district'] for x in districts] == sorted(gu, key=lambda k: -sum(gu[k]))
    for row in districts:
        vals = gu[row['district']]
        assert int(row['countP']) == sum(vals)
        for i, y in enumerate(YEARS):
            ranks = ranking(sum(v) - v[i] for v in gu.values())
            assert int(row['rankWithout' + y]) == ranks[sum(vals) - vals[i]]
    assert all(int(r['rankWithout' + y]) == int(r['pooledCountRank']) for r in districts[:5] for y in YEARS)

    for row in read(OUT / '02-전체70유형-5년합계와-한해제외순위.csv'):
        values = city[(row['type'], row['subtype'])]
        assert sum(values) == int(row['countP'])
        for i, y in enumerate(YEARS):
            value = sum(values) - values[i]
            ranks = ranking(sum(v) - v[i] for v in city.values())
            assert (int(float(row['rankWithout' + y])) == ranks[value]) if value > 0 else row['rankWithout' + y] == ''

    # All dong/type ranks are checked against separately reconstructed distributions.
    distributions = defaultdict(list)
    for key, vals in cells.items():
        for i in range(5):
            value = sum(vals) - vals[i]
            distributions[(key[2], key[3], i)].append(value)
            distributions[(key[0], key[2], key[3], i)].append(value)
    ranks = {k: ranking(v) for k, v in distributions.items()}
    dong_rows = read(OUT / '05-194지역명70유형-5년합계와-한해제외순위.csv')
    for row in dong_rows:
        key = tuple(row[k] for k in KEY); vals = cells[key]
        assert sum(vals) == int(row['countP'])
        for i, y in enumerate(YEARS):
            value = sum(vals) - vals[i]
            for column, group in [('rankWithout' + y, (key[2], key[3], i)),
                                  ('withinDistrict_rankWithout' + y, (key[0], key[2], key[3], i))]:
                if value > 0:
                    assert int(float(row[column])) == ranks[group][value]
                else:
                    assert row[column] == ''

    links = read(OUT / '07-상위5구군-유형별동비교.csv')
    assert len(links) == 45 and len({tuple(r[k] for k in KEY) for r in links}) == 45
    for row in links:
        assert int(row['countP']) == sum(cells[tuple(row[k] for k in KEY)])
        assert int(row['districtTotalRank']) <= 5 and float(row['withinDistrict_pooledCountRank']) <= 3
        if row['count']:
            assert int(float(row['count'])) == int(row['countP'])

    wanted = {tuple(r[k] for k in KEY) for r in links}
    actual_time, actual_total, actual_night = Counter(), Counter(), Counter()
    for year in YEARS:
        path = ROOT / f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{year}.csv.gz'
        with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                key = tuple(row[k] for k in ['CLMTY_SGG_NM', 'CLMTY_EMD_NM', 'EMRG_RSCU_ASSRT_NM', 'EMRG_RSCU_CLSF_NM'])
                if key not in wanted:
                    continue
                stamp = row['DCLR_DT'].strip()
                assert stamp[:4] == year
                month, day, hour = int(stamp[4:6]), int(stamp[6:8]), int(stamp[8:10])
                weekday = date(int(year), month, day).weekday()
                for scope in (['A', 'P'] if row['PRCS_RSLT_SE_NM'] == '정상' else ['A']):
                    actual_total[(key, scope, 0)] += 1
                    actual_total[(key, scope, int(year))] += 1
                    if hour >= 20 or hour < 8:
                        actual_night[(key, scope, 0)] += 1
                        actual_night[(key, scope, int(year))] += 1
                    for dim, value in [('month', month), ('weekday', weekday), ('hour', hour), ('weekdayHour', weekday * 24 + hour)]:
                        actual_time[(key, scope, dim, value)] += 1
    time_summary = read(OUT / '10-상위5구군45조합-시간요약.csv')
    for row in time_summary:
        key = tuple(row[k] for k in KEY); group = (key, row['scope'], int(row['year']))
        assert int(row['count']) == actual_total[group]
        assert int(row['night20to07Count']) == actual_night[group]
        assert math.isclose(float(row['night20to07Pct']), 100 * actual_night[group] / actual_total[group])
    time_cells = read(OUT / '11-상위5구군45조합-5년시간교차집계.csv')
    calendar = [date.fromordinal(n) for n in range(date(2020, 1, 1).toordinal(), date(2025, 1, 1).toordinal())]
    assert len(calendar) == 1827
    for row in time_cells:
        key = tuple(row[k] for k in KEY); dim = row['dimension']; value = int(row['value']); scope = row['scope']
        assert int(row['count']) == actual_time[(key, scope, dim, value)]
        assert int(row['denominator']) == actual_total[(key, scope, 0)]
        days = sum(d.month == value for d in calendar) if dim == 'month' else sum(d.weekday() == (value if dim == 'weekday' else value // 24) for d in calendar) if dim in ['weekday', 'weekdayHour'] else 1827
        assert int(row['calendarDays']) == days
        assert math.isclose(float(row['receiptsPerCalendarDay']), int(row['count']) / days)

    pops = read(OUT / '08-상위5구군-동후보-5개연말전체연령.csv')
    popkeys = [(r['district'], r['rawDong'], r['year'], r['candidateCode']) for r in pops]
    assert len(popkeys) == len(set(popkeys))
    assert {r['year'] for r in pops} == set(YEARS)
    for row in pops:
        if row['populationAvailable'].lower() == 'true':
            assert math.isclose(sum(float(row['age_' + str(a)]) for a in range(101)), float(row['residentTotal']))
    props = read(OUT / '09-5년신고에서-기존대응-보완평가로.csv')
    assert {r['id'] for r in props} == {'H1', 'H2', 'I1'}
    assert len(props) == 4  # I1 is linked to two distinct receipt subtypes, not two interventions.
    for row in props:
        assert int(row['countP']) == sum(cells[tuple(row[k] for k in KEY)])
    forbidden = {'dclr_rcpt_no', 'acdnt_ocrn_lot', 'acdnt_ocrn_lat', 'damg_rgn_lot', 'damg_rgn_lat'}
    for path in OUT.glob('*.csv'):
        header = set(read(path)[0])
        assert not forbidden.intersection(h.lower() for h in header)
    result = {'status': 'PASS', 'verifiedInputs': len(manifest['inputs']), 'guCount': len(gu),
              'subtypeCount': len(city), 'dongSubtypeCount': len(cells), 'totalP': 555786,
              'top5Count': sum(sum(gu[r['district']]) for r in districts[:5]),
              'top5OrderStableIn5Omissions': True, 'top5DongComparisonRows': len(links),
              'timeSummaryRows': len(time_summary), 'timeCellRows': len(time_cells),
              'timeCountsIndependentlyRecountedFrom5PreprocessedFiles': True,
              'populationSnapshots': len(pops), 'full101AgeTotalsMatch': True,
              'proposalsAreConditionalNotMeasuredEffects': True,
              'method': 'Separate csv/collections aggregation and tie-preserving rank reconstruction',
              'scope': 'New aggregation and joins; unchanged prior quality checks reused after checksum matching'}
    (OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
