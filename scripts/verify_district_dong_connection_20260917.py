"""Separate verification pass; does not import the report writer."""
from pathlib import Path
import hashlib
import json
import re
import pandas as pd

root = Path(__file__).resolve().parents[1]
out = root / 'data/processed/구군에서동심화연결-20260917'
source = root / 'data/processed/신고주민연결심화-20260917/direction-reassessment'
checks = []


def check(name, condition):
    checks.append({'check': name, 'pass': bool(condition)})


manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
for item in manifest['inputs'] + manifest['contextFiles'] + manifest['outputs']:
    path = root / item['path']
    check('hash:' + item['path'], hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'])

names = pd.read_csv(source / 'all-194-names-70-subtypes.csv')
districts = pd.read_csv(out / '16구군-동일조건-전체비교.csv')
basic = pd.read_csv(out / '구군-전체70유형-동별기본연결.csv').fillna('')
core = pd.read_csv(out / '주요3유형-상위규모와구성유지-핵심연결.csv')
links = pd.read_csv(out / '구군-동-유형-연결근거.csv')
pop = pd.read_csv(out / '연결지역-2024주민후보-전체연령.csv')
sensitivity = pd.read_csv(out / '선정범위-상위5-10-20-민감도.csv')
metric_ranks = pd.read_csv(out / '구군-지표별-건수순위와구성비순위.csv').fillna({'subtype': ''})
overview = pd.read_csv(out / '16구군-건수순-주요유형요약.csv')
check('all16 total555786', len(districts) == 16 and districts.callCount2020To2024.sum() == 555786)
check('all16 population3266598', districts.total.sum() == 3266598)
check('countOrder only', districts.district.head(5).tolist() == ['부산진구', '해운대구', '사하구', '사상구', '북구'])
check('same70types for every district', len(basic) == 1120 and all(basic.groupby('district').size() == 70))
check('overview preserves all16 count order', overview.district.tolist() == districts.district.tolist())
check('all74metrics16districts', len(metric_ranks) == 1184 and metric_ranks.groupby(['level', 'type', 'subtype']).size().eq(16).all())
totals = districts.set_index('district').callCount2020To2024
major_counts = names.groupby(['district', 'type']).countP.sum()
sub_counts = names.groupby(['district', 'type', 'subtype']).countP.sum()
metric_counts_ok = []
for _, r in metric_ranks.iterrows():
    expected_count = major_counts.loc[(r.district, r.type)] if r.level == '종별' else sub_counts.loc[(r.district, r.type, r.subtype)]
    metric_counts_ok.append(r['count'] == expected_count and r.denominator == totals[r.district]
                            and abs(r.sharePct - 100 * expected_count / totals[r.district]) < 1e-9)
check('all1184 counts and shares from unchanged name aggregates', all(metric_counts_ok))
for key, rows in metric_ranks.groupby(['level', 'type', 'subtype']):
    expected_count_rank = rows['count'].rank(method='min', ascending=False).where(rows['count'] > 0)
    expected_share_rank = rows.sharePct.rank(method='min', ascending=False).where(rows['count'] > 0)
    check('count-rank:' + str(key), rows.typeCountRank.equals(expected_count_rank))
    check('share-rank:' + str(key), rows.typeShareRank.equals(expected_share_rank))
check('subtype ties and top-count overview', all(
    int(r['count']) == int(names[names.district == r.district].groupby(['type', 'subtype']).countP.sum().max())
    for _, r in overview.iterrows()))
check('top5 gu retained in connection order', list(dict.fromkeys(links.district))[:5] == districts.district.head(5).tolist())

for _, r in basic.iterrows():
    children = names[(names.district == r.district) & (names.type == r.type) & (names.subtype == r.subtype)]
    key = f'{r.district}/{r.type}/{r.subtype}'
    maximum = children.countP.max()
    expected = set(children.loc[children.countP == maximum, 'rawDong']) if maximum else set()
    actual = set(r.largestRawNames.split(' / ')) if r.largestRawNames else set()
    check('same-type-child-sum:' + key, children.countP.sum() == r['count'])
    check('largest-all-ties:' + key, actual == expected and r.largestRawNameCount == maximum)

triples = names[(names.type == '구급') & names.subtype.isin(['질병', '질병외', '부상'])]
expected = triples[(triples.countRankWithinSubtype <= 10) & (triples.aboveRestBusan30 == 30) & (triples.aboveRestDistrict30 == 30)]
identity = ['district', 'rawDong', 'type', 'subtype']
check('exact8 candidates no omissions', set(map(tuple, core[identity].values)) == set(map(tuple, expected[identity].values)) and len(core) == 8)
check('5district5names', core.district.nunique() == 5 and len(core[['district', 'rawDong']].drop_duplicates()) == 5)
for _, r in sensitivity.iterrows():
    s = triples[(triples.countRankWithinSubtype <= r.withinTypeCountLimit) & (triples.aboveRestBusan30 == 30) & (triples.aboveRestDistrict30 == 30)]
    check('sensitivity:' + str(r.withinTypeCountLimit), len(s) == r.combinations and s.district.nunique() == r.districtCount)
for _, r in links.iterrows():
    a = names[(names.district == r.district) & (names.rawDong == r.rawDong) & (names.type == r.type) & (names.subtype == r.subtype)].iloc[0]
    check('connection:' + '/'.join(str(r[x]) for x in identity), a.countP == r.countP and abs(a.shareRegionPct - r.shareRegionPct) < 1e-9)
    check('annual-total:' + '/'.join(str(r[x]) for x in identity), sum(r[str(y)] for y in range(2020, 2025)) == r.countP)
check('101ages sum', (pop[[f'age_{i}' for i in range(101)]].sum(axis=1) == pop.residentTotal).all())
check('2024 only population', set(pop.year) == {2024})
check('no duplicate population candidates per rawname', not pop.duplicated(['district', 'rawDong', 'candidateCode']).any())
check('no beehive candidates', not core.subtype.str.contains('벌집').any())
for file in out.glob('*.csv'):
    columns = pd.read_csv(file, nrows=0).columns
    check('no receipt IDs or precise locations:' + file.name, not any(c in columns for c in ['DCLR_RCPT_NO', 'ACDNT_OCRN_LOT', 'ACDNT_OCRN_LAT', 'DAMG_RGN_LOT', 'DAMG_RGN_LAT']))

report = root / 'docs/40-분석결과/부산-119-구군전체에서-동별심화로-연결정리-20260917.md'
text = report.read_text(encoding='utf-8')
for target in re.findall(r'\]\(([^)]+)\)', text):
    if not target.startswith('http'):
        check('report-link:' + target, (report.parent / target).exists())
check('facility denominator limitation retained', 'completeInventory: false' in text and '관할' in text)
check('code order clarified and indicator ranks separated', '구군 코드순 정렬이었다' in text and '유형별 건수 순위와 구성비 순위' in text)
check('same-type and no composite interpretation', '구의 종별을 동의 다른 유형으로 바꾸지 않는다' in text and '종합순위를 만들지는 않는다' in text)
result = {'status': 'PASS' if all(c['pass'] for c in checks) else 'FAIL', 'checks': len(checks), 'failed': [c for c in checks if not c['pass']], 'details': checks, 'scope': 'Separate verification of new report tables against preserved verified aggregates; not a new representativeness or intervention-effect validation.'}
(out / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
(out / 'verification.md').write_text(f'# 구·군→동 연결표 검증\n\n결과: {result["status"]}; {len(checks)}개 대조, 실패 {len(result["failed"])}개.\n\n기존 검증 집계의 입력·출력 해시,16구 총량,70유형×16구의 동일 유형 연결과 동률,선정8조합,상위5/10/20 민감도,인구101연령,출처 링크를 작성 코드와 별도 명령에서 대조했다. 원본 재검산이나 정책 효과 검증을 의미하지 않는다.\n', encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'details'}, ensure_ascii=False))
raise SystemExit(0 if result['status'] == 'PASS' else 1)
