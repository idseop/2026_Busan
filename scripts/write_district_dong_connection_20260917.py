"""Reorganize verified district results and dong cases without changing selection rules."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/신고주민연결심화-20260917'
DIST = ROOT / 'data/processed/신고인구특성재정립-20260917/tables'
OUT = ROOT / 'data/processed/구군에서동심화연결-20260917'
REPORT = ROOT / 'docs/40-분석결과/부산-119-구군전체에서-동별심화로-연결정리-20260917.md'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [DIST / '구군별-신고특성과-2024주민구성.csv',
              DIST / '구군별-전체70유형-반복과선택영향.csv',
              BASE / 'direction-reassessment/all-194-names-70-subtypes.csv',
              BASE / 'direction-reassessment/all-name-population-candidates.csv']
    previous = {}
    for path in [DIST / 'manifest.json', BASE / 'direction-reassessment/manifest.json']:
        for item in json.loads(path.read_text(encoding='utf-8-sig'))['outputs']:
            previous[(ROOT / item['path']).resolve()] = item['sha256']
    for path in inputs:
        assert sha(path) == previous[path.resolve()], f'Previously verified output changed: {path}'
    districts, subtypes, names, population = [pd.read_csv(p) for p in inputs]
    assert len(districts) == 16 and districts.district.nunique() == 16
    assert len(names) == 194 * 70
    assert int(names.countP.sum()) == int(districts.callCount2020To2024.sum()) == 555786
    assert names.groupby('district').countP.sum().sort_index().equals(
        districts.set_index('district').callCount2020To2024.sort_index())
    assert names[[str(y) for y in range(2020, 2025)]].sum(axis=1).equals(names.countP)

    # Display order is explicitly a count order, never a policy or risk ranking.
    district_table = districts.sort_values('callCount2020To2024', ascending=False).copy()
    district_table.insert(0, 'countOrder', range(1, 17))
    district_table.to_csv(OUT / '16구군-동일조건-전체비교.csv', index=False, encoding='utf-8-sig')
    total_rank = district_table.set_index('district').countOrder.to_dict()

    # Keep count ranks and composition ranks as different columns, with ties retained.
    metrics = []
    for _, r in districts.iterrows():
        for kind in ['구급', '구조', '화재', '기타']:
            metrics.append({'level': '종별', 'type': kind, 'subtype': '', 'district': r.district,
                            'count': int(r[kind + 'Count']), 'denominator': int(r.callCount2020To2024),
                            'sharePct': r[kind + 'Pct'], 'aboveRestConditions': int(r[kind + 'AboveRestConditions']),
                            'aboveRestYears': int(r[kind + 'AboveRestYears'])})
    for _, r in subtypes.iterrows():
        metrics.append({'level': '세부유형', 'type': r.type, 'subtype': r.subtype, 'district': r.district,
                        'count': int(r['count']), 'denominator': int(r.districtDenominator),
                        'sharePct': r.pctDistrict, 'aboveRestConditions': int(r.aboveRestConditions),
                        'aboveRestYears': int(r.aboveRestYears)})
    ranks = pd.DataFrame(metrics)
    group = ranks.groupby(['level', 'type', 'subtype'])
    ranks['typeCountRank'] = group['count'].rank(method='min', ascending=False).astype('Int64')
    ranks['typeShareRank'] = group.sharePct.rank(method='min', ascending=False).astype('Int64')
    ranks.loc[ranks['count'] == 0, ['typeCountRank', 'typeShareRank']] = pd.NA
    ranks['districtTotalCountRank'] = ranks.district.map(total_rank)
    ranks = ranks.sort_values(['level', 'type', 'subtype', 'typeShareRank', 'districtTotalCountRank'])
    ranks.to_csv(OUT / '구군-지표별-건수순위와구성비순위.csv', index=False, encoding='utf-8-sig')

    top_type = subtypes.sort_values(['count', 'type', 'subtype'], ascending=[False, True, True]).groupby('district', sort=False).head(1)
    overview = district_table[['countOrder', 'district', 'callCount2020To2024', 'total', 'pct_65_plus']].merge(
        top_type[['district', 'type', 'subtype', 'count', 'pctDistrict']], on='district', validate='one_to_one')
    overview = overview.sort_values('countOrder')
    overview.to_csv(OUT / '16구군-건수순-주요유형요약.csv', index=False, encoding='utf-8-sig')

    # Preserve the type at both levels, including all non-focus types and zero groups.
    ranked_gu = subtypes.copy()
    ranked_gu['districtTypeCountRank'] = ranked_gu.groupby(['type', 'subtype'])['count'].rank(method='min', ascending=False).astype(int)
    basic = []
    for _, r in ranked_gu.iterrows():
        children = names[(names.district == r.district) & (names.type == r.type) & (names.subtype == r.subtype)]
        assert int(children.countP.sum()) == int(r['count'])
        largest = int(children.countP.max())
        row = r.to_dict()
        row['largestRawNames'] = ' / '.join(children.loc[children.countP == largest, 'rawDong']) if largest else ''
        row['largestRawNameCount'] = largest
        row['childState'] = '선택 조건 접수 있음' if largest else '선택 조건 접수 0건'
        basic.append(row)
    pd.DataFrame(basic).to_csv(OUT / '구군-전체70유형-동별기본연결.csv', index=False, encoding='utf-8-sig')

    # Reuse existing within-type count ranks and sensitivity fields; no composite score.
    major = names[(names.type == '구급') & names.subtype.isin(['질병', '질병외', '부상'])].copy()
    stable = (major.aboveRestBusan30 == 30) & (major.aboveRestDistrict30 == 30)
    core = major[stable & (major.countRankWithinSubtype <= 10)].copy()
    core = core.merge(ranked_gu[['district', 'type', 'subtype', 'count', 'pctDistrict', 'districtTypeCountRank']],
                      on=['district', 'type', 'subtype'], validate='many_to_one').rename(
                          columns={'count': 'districtSubtypeCount', 'pctDistrict': 'districtSubtypePct'})
    core['displayRole'] = core.countRankWithinSubtype.map(lambda rank: '좁은 상위5에서도 유지' if rank <= 5 else '상위10 비교 확대')
    core['districtTotalCountRank'] = core.district.map(total_rank)
    core = core.sort_values(['districtTotalCountRank', 'countP'], ascending=[True, False])
    core.to_csv(OUT / '주요3유형-상위규모와구성유지-핵심연결.csv', index=False, encoding='utf-8-sig')
    sensitivities = []
    for limit in [5, 10, 20]:
        s = major[stable & (major.countRankWithinSubtype <= limit)]
        sensitivities.append({'withinTypeCountLimit': limit, 'combinations': len(s),
                              'districtCount': s.district.nunique(), 'districts': ' / '.join(sorted(s.district.unique())),
                              'rawNameCount': len(s[['district', 'rawDong']].drop_duplicates())})
    pd.DataFrame(sensitivities).to_csv(OUT / '선정범위-상위5-10-20-민감도.csv', index=False, encoding='utf-8-sig')

    selected = [
        ('부산진구', '부전동', '구급', '질병외', '기존 심화'),
        ('부산진구', '부전동', '구급', '부상', '기존 심화'),
        ('해운대구', '좌동', '구급', '질병', '기존 비교'),
        ('사하구', '다대동', '구급', '질병', '기존 심화'),
        ('사하구', '다대동', '구급', '질병외', '동일 분류의 추가 연결'),
        ('북구', '금곡동', '구급', '질병', '기존 심화'),
        ('남구', '용호동', '구급', '질병', '기존 비교'),
        ('남구', '용호동', '구급', '부상', '기존 비교'),
        ('중구', '남포동6가', '구급', '질병외', '구 내부 차이 비교'),
        ('중구', '남포동5가', '구급', '질병외', '구 내부 차이 비교'),
        ('중구', '남포동5가', '구급', '부상', '구 내부 차이 비교'),
        ('중구', '동광동5가', '구급', '질병', '구 내부 차이 비교'),
        ('사상구', '모라동', '구급', '질병', '규모 상위 구의 비교 유지'),
        ('사상구', '괘법동', '구급', '부상', '상위20까지 넓혔을 때의 같은 유형 비교'),
        ('영도구', '동삼동', '구급', '질병', '다른 주민 배경 비교 유지'),
        ('연제구', '연산동', '구급', '질병', '큰 지역명 총량 기준'),
        ('강서구', '송정동', '화재', '대형화재(시장,공장)', '대상물 관련 별도 분기'),
        ('강서구', '대저2동', '화재', '일반화재(주택)', '대상물 관련 별도 분기'),
    ]
    records = []
    for gu, dong, kind, subtype, role in selected:
        source = names[(names.district == gu) & (names.rawDong == dong)
                       & (names.type == kind) & (names.subtype == subtype)]
        assert len(source) == 1
        row = source.iloc[0].to_dict()
        parent = subtypes[(subtypes.district == gu) & (subtypes.type == kind)
                          & (subtypes.subtype == subtype)].iloc[0]
        row.update(role=role, districtSubtypeCount=int(parent['count']),
                   districtTotal=int(parent.districtDenominator),
                   districtSubtypeSharePct=float(parent.pctDistrict),
                   districtAboveRestConditions=int(parent.aboveRestConditions),
                   districtAboveRestYears=int(parent.aboveRestYears))
        records.append(row)
    connections = pd.DataFrame(records)
    connections['districtTotalCountRank'] = connections.district.map(total_rank)
    connections = connections.sort_values(['districtTotalCountRank', 'countP'], ascending=[True, False])
    connections.to_csv(OUT / '구군-동-유형-연결근거.csv', index=False, encoding='utf-8-sig')
    keys = connections[['district', 'rawDong']].drop_duplicates()
    pops = population[population.year == 2024].merge(keys, on=['district', 'rawDong'], validate='many_to_one')
    pops.to_csv(OUT / '연결지역-2024주민후보-전체연령.csv', index=False, encoding='utf-8-sig')

    lines = ['# 부산 119: 구·군 전체 결과에서 동별 심화로 연결한 결과', '',
             '작성일 2026-09-17. 신고 2020~2024년, 주민 배경 2024년 12월 말. 기존 검증 집계를 재배치하고 구·군과 동의 근거를 대조한 보고서다.', '',
             '## 1. 선정 설명의 정정과 분석 흐름', '',
             '앞서 제시한 사하·북·부산진·해운대·남구 5곳은 이미 심화한 3곳과 비교 후보 2곳이었다. 이를 구·군 전체의 상위 5곳처럼 제시한 것은 서로 다른 선정 단계를 섞은 설명이었다. 그 순서를 구·군 종합순위로 사용하지 않는다. 중구를 분석에서 제외한 것도 아니다.', '',
             '기존 16구·군 표에서 중구가 첫 줄이었던 이유는 구군 코드순 정렬이었다. 이번 표는 **전체 건수 내림차순**으로 바꾸고, **유형별 건수 순위와 구성비 순위**를 별도로 계산해 표시한다. 피해 심각도 점수나 인구 대비 신고율은 만들지 않는다.', '',
             '**부산 16구·군의 규모·유형·주민 구성 → 각 구 내부 동별 차이 → 연도·포함조건에 따른 유지 여부 → 해당 유형에 필요한 추가 자료 → 기존 대응과 조건부 보완안**으로 연결한다.', '',
             '구·군을 먼저 비교하되 총량 상위 구만 남기지 않는다. 구 평균에 가려진 동별 특성이 있을 수 있기 때문이다. 구 전체의 특성을 그 안의 모든 동에 동일하게 적용하지 않는다.', '',
             '## 2. 숲: 16개 구·군 전체 비교', '',
             '현재 17개 컬럼 결측 없는 704,689접수 중 정상 처리·운영성 3분류 제외·벌집제거 제외 조건의 **555,786접수**다. 아래 순서는 이 조건의 접수 건수순이며 위험·피해·정책 우선순위가 아니다. 전체 신고의 대표성이 입증됐다는 뜻도 아니다.', '',
             '| 전체 건수순 | 구·군 | 5년 접수 | 구 안에서 가장 큰 세부유형 | 해당 유형 접수 | 해당 구 신고 중 비중 | 주민 65세 이상 % |',
             '|---:|---|---:|---|---:|---:|---:|']
    for _, r in overview.iterrows():
        lines.append(f'| {r.countOrder} | {r.district} | {r.callCount2020To2024:,} | {r.type}·{r.subtype} | {r["count"]:,} | {r.pctDistrict:.1f}% | {r.pct_65_plus:.1f} |')
    lines += ['', '건수 상위 5곳은 **부산진·해운대·사하·사상·북구**다. 앞선 심화 후보 5곳과 다른 이유는 앞선 표가 건수순 표가 아니었기 때문이다. 한편 북구의 질병 비중, 강서·기장의 구조·화재 비중처럼 총량과 별개인 유형 차이도 유지한다.', '',
              '중구는 선택 신고 총량14,460건이며, 아래 지표별 비교에서 부상 구성비가8.29%로 가장 높다. 이 결과는 원래 코드순 표의 첫 줄과 구분해야 하는 별도 지표다. 모든 구의 최대 세부유형은 구급이지만 강서·기장의 구조·화재처럼 총량 외의 상대적 특성은 다음 표에서 함께 읽는다.', '',
              '## 3. 나무: 구의 특징을 확인한 뒤 어떤 동을 더 봤는가', '',
              '다음 표는 기존 심화·비교 사례와 중구 내부 비교를 연결한다. 각 비중의 분모는 해당 구 또는 해당 지역명으로 접수된 선택 신고 전체다.', '',
              '| 구·군 전체에서 확인 | 동에서 별도로 확인 | 연결한 주민·지역 배경 | 현재 결과의 역할 |',
              '|---|---|---|---|',
              '| 부산진구: 64,059접수, 질병외 35.00% | 부전동 질병외 4,625건·38.40%, 부상 1,178건·9.78%; 두 유형 모두 매년 동일 유형 건수 상위10 | 부전1·2동 주민 후보 15~39세 45.90%·46.32%; 음식·소매 상권, 서로 다른 방문 시간, 부상 야간 55.09% | 큰 질병외·부상 집합에서 실제 기전과 발생 장소로 좁히는 기존 심화 |',
              '| 해운대구: 56,927접수, 질병 35.11% | 좌동 질병 3,593건·36.59%; 연도별 상위10 4/5년 | 좌1~4동 후보의 주민 분포와 주거 배경. 승강기 관련 기록은 별도 유형 분기 | 금곡·다대와 같은 질병 특성의 주민 배경 비교 |',
              '| 사하구: 48,076접수, 질병 34.41%; 구의 비중 우세는 6조건 중5·5년 중2 | 다대동 질병 4,054건·37.02%; 매년 상위10, 부산·구 내부 비교30조건 모두 우세 | 다대1·2 후보 65세 이상 23.27%·27.02%; 구 건강조사, 다대 건강생활지원센터 | 구 평균만으로 보이지 않는 동의 특성을 확인한 기존 심화; 조건부 교육 연결안 |',
              '| 사상구: 41,747접수, 질병14,336건·질병외14,284건으로 큰 두 분류 | 모라동 질병2,839건·37.77%, 부산·구내 우세27/30·28/30. 괘법동 부상632건은 상위20 확장에서30/30·30/30 | 모라1·3동 주민 후보65세 이상26.29%·43.83%; 괘법동 주민15~39세38.02% | 건수4위 자리를 유지한다. 조건 영향과 동별 주민 차이가 있어 다른 구 보완안 복사 없이 같은 유형의 추가 연결을 검토 |',
              '| 북구: 41,205접수, 질병 36.25%; 6조건·5년 모두 우세 | 금곡동 질병 3,615건·38.90%; 부산·구 내부 비교30조건 모두 우세 | 금곡 주민 34,752명, 65세 이상29.38%; 북구 건강조사·금곡 마을건강센터 | 구와 동 양쪽에서 유지되는 질병 특성; 조건부 교육 연결안 |',
              '| 남구: 36,320접수, 질병35.45%·부상7.85%; 각각6조건·5년 우세 | 용호동 질병3,524건·37.14%, 부상786건·8.28%; 각각 부산·구 내부30조건 우세 | 용호1~4동 후보의 서로 다른 주민 구성 | 질병과 부상을 분리해서 보는 비교 사례; 다른 구 보완안을 복사하지 않음 |',
              '| 중구: 14,460접수, 질병30.44%·질병외34.55%·부상8.29% | 남포동6가 질병외484건·42.05%; 남포동5가 부상98건·12.45%; 동광동5가 질병256건·42.11% | 남포동·동광동 주민 후보와 신고 명칭의 범위 구분 | 구 전체를 고령·질병 지역 하나로 묶지 않는 내부 대비 사례; 현재 특정 예방안 확정 없음 |', '',
              '**남겨둔 다른 비교도 있다.** 건수 4위 사상구의 모라동 질병은2,839건·37.77%지만 부산·구내 비교 우세가27/30·28/30으로 조건 영향을 받는다. 영도 동삼동 질병3,166건·36.71%는 다른 고령 주민 배경을 비교할 후보다. 연산동 질병7,588건은 큰 명칭의 총량 기준으로 보존한다. 강서 송정동의 시장/공장 화재 분류90건, 대저2동의 주택 화재 분류41건과 기장군 구조·화재 특성은 대상물 관련 별도 분기로 유지한다.', '',
              '이들을 비교·별도 분기로 둔 것이 문제가 없다는 판정은 아니다. 기존 자료로 충분히 심화한 정도와 실제 중요도를 혼동하지 않는다.', '',
              '## 4. 중구 안에서도 서로 다른 특성이 확인된다', '',
              '| 신고 지역명·유형 | 5년 접수 | 해당 지역 비중 | 연도별 접수(2020→2024) | 부산 나머지·중구 나머지 대비 비중 우세 |',
              '|---|---:|---:|---|---|']
    for _, r in connections[connections.district == '중구'].iterrows():
        annual = ' → '.join(str(int(r[str(y)])) for y in range(2020, 2025))
        lines.append(f'| {r.rawDong}·{r.subtype} | {r.countP:,} | {r.shareRegionPct:.2f}% | {annual} | {r.aboveRestBusan30}/30 · {r.aboveRestDistrict30}/30 |')
    lines += ['', '중구 전체 질병 비중은30.44%로 나머지 부산보다 낮지만, 동광동5가의 질병 비중은42.11%이며 비교30조건 모두 높다. 남포동5·6가는 질병외, 남포동5가는 부상 비중의 차이가 유지된다. **같은 구 안에서도 심화해야 할 신고 분류가 달라진다.**', '',
              '이는 현재 집합의 구성 차이다. 남포동5가 부상은5년98접수, 연간12~33접수로, 그 비중만으로 부산의 가장 심각한 문제나 보완 효과를 입증하지 않는다. 영주동은 중구 내 질병567건·질병외574건으로 두 분류의 건수 최다이므로 총량과 대비할 기준으로도 남긴다. 서로 다른 동·유형을 합쳐 표본을 부풀리지 않는다.', '',
              '남포동1~6가에는 동일한 남포동 주민 후보799명이 반복 연결된다. 이를 여섯 번 합산하거나 남포동5·6가 신고의 위험률 분모로 쓰지 않는다. 동광동5가에는 동광동 주민 후보2,342명이 연결되지만, 그 인구가 동광동5가만의 주민 수라는 뜻은 아니다. 후보가 하나라는 사실과 신고 위치가 확정됐다는 사실은 다르다.', '',
              '## 5. 추가 자료가 실제 보완안으로 이어진 범위', '',
              '| 기존 심화 | 신고·주민에서 추가 자료로 연결 | 기존 대응 확인 | 현재 보완 수준과 평가 |',
              '|---|---|---|---|',
              '| 북구→금곡 | 구급 질병 특성→구 건강조사: 2024 진료 필요자 중 미이용13.7%, 30세 이상 고혈압 진단자 관리교육 경험4.7% | 금곡 마을건강센터의 상담·교육, 북구 등록관리·문자안내가 이미 존재 | 기존 상담에서 희망 적격자의 교육 예약·첫 참여 완료를 연결하는 조건부 시범안. 현재 절차가 이미 같은 기능을 하면 중복 도입하지 않음 |',
              '| 사하구→다대 | 다대 질병 구성→구 건강조사: 미이용4.9%, 고혈압 교육4.6%, 당뇨교육5.5% | 다대 건강생활지원센터와 질환교실·생활터 교육이 존재 | 치료기관 부족으로 단정하지 않고 기존 상담→교육 연결을 점검하는 조건부 시범안. 다대1·2 실제 이용·완료를 따로 측정 |',
              '| 부산진구→부전 | 질병외·부상과 야간 특성→2020~24 상권20분기, 2023~24 생활인구로 활동 배경 확인 | 주거취약계층 상담 기록은 존재하나 부전 방문객의 손상 예방 대응과 동일하지 않음 | 특정 사고 기전·실제 장소가 아직 연결되지 않아 시설·순찰·도로정비 등 특정 예방안은 확정하지 않음 |', '',
              '건강조사는 구 단위 성인 표본조사이므로 비율을 금곡·다대 주민이나 신고자에게 적용하지 않는다. 질병 분류가 고혈압·당뇨라는 증거도 아니다. 기존 사업 운영은2025~2026 공개 안내를 확인했으며, 모든 운영조건을2020~2024에 소급하지 않는다.', '',
              '두 교육 연결안의 기대 경로는 안내가 실제 참여로 이어지는지 확인하는 것이다. 평가안은 교육 희망 적격자 중30일 내 첫 교육 완료율과90일 후 추적이며, 현행 절차와 비교한다. 30·90일은 설계 제안이다. 건강 개선·119 신고 감소·효과 크기를 이번 자료로 입증하지 않았다.', '',
              '## 6. 발표에서 사용할 연결 문장', '',
              '> 부산 5년 신고를 비교하니 지역마다 주요 신고 구성과 주민 배경이 달랐다. 구 전체 결과에서 각 구 안의 동별 차이를 다시 확인한 결과, 다대·금곡에서는 질병 신고의 상대적 비중이 유지됐고 부전에서는 질병외·부상 특성이 반복됐다. 중구 역시 하나의 고령 지역으로 설명되지 않고 남포와 동광의 유형 구성이 달랐다. 이에 유형별로 건강이용·상권·생활인구 등 필요한 자료를 추가하고 기존 서비스를 대조했다. 현재는 금곡·다대의 기존 교육 연결을 점검하는 조건부 시범안까지 구체화했으며, 지역별 실제 누락과 효과는 참여·완료 자료로 검증하도록 분리했다.', '',
              '우리의 차별점은 구의 총량을 동의 위험으로 옮기지 않고, 동의 신고 구성·주민 배경·추가 근거·기존 대응을 같은 흐름으로 연결한 데 있다. 정부가 놓친 서비스 공백을 모두 입증했다는 주장은 하지 않는다.', '',
              '## 7. 비교 정의·출처·재현', '',
              '- 6조건: 결측 제외 전후 두 집합 × 전체처리·정상처리·정상/운영성제외 세 조건. 벌집제거는 집중 비교에서 제외.',
              '- 30조건: 같은6조건 × 2020~2024년. 해당 지역을 뺀 부산과 해당 구의 나머지를 각각 비교. 우세 횟수는 유의성이나 대표성 점수가 아니다.',
              '- 구성비·건수·주민 비중은 서로 다른 지표다. 주민 전체101연령은 CSV에 보존하고 표에서 요약한 특정 연령을 신고자 연령으로 해석하지 않는다.',
              '- [구군 전체 재분석](부산-119-신고특성과인구구성-재분석-20260917.md)',
              '- [전체 유형에서 동 선정으로 연결한 분석](부산-119-방향재검토와-유형별연결-20260917.md)',
              '- [공식 건강조사·기존 서비스·조건부 보완안](부산-119-신고인구에서-보건이용과-보완으로-20260917.md)',
              '- [16구군 비교표](../../data/processed/구군에서동심화연결-20260917/16구군-동일조건-전체비교.csv)',
              '- [16구군 건수순 주요유형 요약](../../data/processed/구군에서동심화연결-20260917/16구군-건수순-주요유형요약.csv)',
              '- [지표별 건수·구성비 순위](../../data/processed/구군에서동심화연결-20260917/구군-지표별-건수순위와구성비순위.csv)',
              '- [구군-동-유형 연결 근거](../../data/processed/구군에서동심화연결-20260917/구군-동-유형-연결근거.csv)',
              '- [핵심8조합의 동일 유형 연결](../../data/processed/구군에서동심화연결-20260917/주요3유형-상위규모와구성유지-핵심연결.csv)',
              '- [모든16구·70유형 기본 연결](../../data/processed/구군에서동심화연결-20260917/구군-전체70유형-동별기본연결.csv)',
              '- [상위 범위에 따른 후보 변화](../../data/processed/구군에서동심화연결-20260917/선정범위-상위5-10-20-민감도.csv)',
              '- [주민 후보 전체연령](../../data/processed/구군에서동심화연결-20260917/연결지역-2024주민후보-전체연령.csv)',
              '- [입력 해시](../../data/processed/구군에서동심화연결-20260917/manifest.json)',
              '- 재생성: `.venv-check/Scripts/python.exe scripts/write_district_dong_connection_20260917.py`', '',
              '- 별도 검증: `.venv-check/Scripts/python.exe scripts/verify_district_dong_connection_20260917.py`; 결과는 동일 산출물 폴더의 `verification.md`, `verification.json`.', '',
              '이번 작업은 기존 검증 집계4개의 과거 해시 일치를 확인해 재사용했다. 원본 전수 재처리·신규 외부자료 수집·웹 변경은 하지 않았다. 중구 및 구·동 연결표는 기존 전체 비교표에서 추출한 결과다.', '']

    type_lines = ['## 2-1. 유형별로 건수가 많은 곳과 구성비가 높은 곳을 분리', '',
        '앞 표는 전체 접수 규모순이다. 아래 왼쪽은 해당 유형의 건수순, 오른쪽은 각 구의 전체 선택 신고 중 해당 유형 비중순이다. 두 지표를 더하거나 가중해 하나의 순위로 만들지 않는다. 4종별·70세부유형 전체1,184행의 순위도 CSV에 보존했다.', '',
        '| 비교 유형 | 해당 유형 건수 상위3 | 해당 유형 구성비 상위3 |',
        '|---|---|---|']
    for level, kind, subtype in [('세부유형', '구급', '질병'), ('세부유형', '구급', '질병외'),
                                  ('세부유형', '구급', '부상'), ('종별', '구조', ''), ('종별', '화재', '')]:
        s = ranks[(ranks.level == level) & (ranks.type == kind) & (ranks.subtype == subtype)]
        count_order = s.sort_values(['typeCountRank', 'districtTotalCountRank']).head(3)
        share_order = s.sort_values(['typeShareRank', 'districtTotalCountRank']).head(3)
        counts = ' → '.join(f'{r.district} {r["count"]:,}건' for _, r in count_order.iterrows())
        shares = ' → '.join(f'{r.district} {r.sharePct:.2f}%' for _, r in share_order.iterrows())
        type_lines.append(f'| {kind + "·" + subtype if subtype else kind} | {counts} | {shares} |')
    type_lines += ['', '비중 순위는 반올림 전 값을 정렬했으며 차이의 유의성을 뜻하지 않는다. 질병 비중은 영도36.2551%·북구36.2505%로 매우 가깝다. 영도를 북구보다 더 심각하다고 해석하지 않는다. 중구의 부상 비중 우세는6조건·5년 중4년에서, 강서의 부상 비중 우세는2/6조건에서 확인된다. 현재 비중 상위라는 사실과 조건에 안정적인 특성은 다르다.', '',
        '강서·기장의 구조·화재 비중 우세는 각각6조건·5년 모두 유지됐다. 구급 질병 사례에 건강서비스를 연결하는 것과 별개로, 이 유형에는 실제 대상물·활동·예방점검 자료를 연결한다. 중구의 부상·질병외 역시 해당 유형을 유지해 남포의 결과로 이어간다.', '']
    lines[lines.index('## 3. 나무: 구의 특징을 확인한 뒤 어떤 동을 더 봤는가'):lines.index('## 3. 나무: 구의 특징을 확인한 뒤 어떤 동을 더 봤는가')] = type_lines

    priority_lines = ['## 3-1. 같은 유형을 유지하면서 규모 상위 사례를 좁힌 결과', '',
        '구급 질병·질병외·부상은 선택 신고의75.94%다. 우선 이 세 분류의 기존 동일 유형 건수 상위10 안에서, 부산 나머지 및 구 내부 나머지와 비교한 구성비 우세가30/30에서 유지되는 조합을 추렸다. 이는 현재 핵심 설명 후보를 정리하는 규칙이며, 위험 순위를 새로 만든 것이 아니다. 구의 종별을 동의 다른 유형으로 바꾸지 않는다.', '',
        '| 분류 | 구 전체 해당 유형 건수(구군 건수순) | 같은 구의 동명·해당 유형 | 동명 건수순 | 구성비 | 상위5 범위에서도 유지 |',
        '|---|---|---|---:|---:|---|']
    for _, r in core.iterrows():
        priority_lines.append(f'| {r.subtype} | {r.district} {r.districtSubtypeCount:,}건({r.districtTypeCountRank}위) | {r.rawDong} {r.countP:,}건 | {r.countRankWithinSubtype}위 | {r.shareRegionPct:.2f}% | {"유지" if r.countRankWithinSubtype <= 5 else "상위10에서 포함"} |')
    priority_lines += ['', '**좁은 상위5 범위까지 줄여도 남는 첫 핵심은 부산진구→부전동(질병외·부상), 사하구→다대동(질병)**이다. 상위10까지 넓히면 북구→금곡동, 해운대구→좌동, 남구→용호동이 포함되어5개 구·5개 지역명·8유형 조합이 된다. 서로 다른 유형 건수를 더해 다섯 구의 종합순위를 만들지는 않는다.', '',
        '조건을 바꿔 보면 상위5는2개 구·3조합, 상위10은5개 구·8조합, 상위20은6개 구·12조합이다. 상위20에서는 사상구 괘법동 부상과 해운대 반여동 질병·반송동 질병/질병외가 추가된다. 따라서5개 구가 유일한 정답이라는 주장은 하지 않는다. 상위 범위는 설명의 깊이를 배분하는 기준이다.', '',
        '연산동·기장읍처럼 총량이 더 큰 지역은 표에서 제거하지 않았다. 구성비 차이의 안정성이 위 조건에 미치지 않아 규모 비교 역할과 심화 역할을 나눴다. 지역명마다 포괄하는 행정동·법정동 범위가 다르므로 이 건수순을 동일 크기 동의 위험 순위로 바꾸지 않는다.', '',
        '모든16개 구·70유형은 `구군-전체70유형-동별기본연결.csv` 1,120행에 같은 분류의 구 집계와 구 안의 최대 건수 동명을 연결했다. 동률은 모두 보존하고, 해당 조건0건에는 임의의 대표 동을 붙이지 않았다. 이는 모든 유형에 보완안을 확정했다는 뜻은 아니다.', '']
    insert_at = lines.index('## 4. 중구 안에서도 서로 다른 특성이 확인된다')
    lines[insert_at:insert_at] = priority_lines

    capacity_lines = ['## 5-1. 센터 수와 고령 주민을 제안으로 연결할 때의 실제 검토', '',
        '**센터 수 대비 신고가 많다 → 센터 부족 → 다른 수단으로 대체**를 현재 결과로 확정하지 않는다. 기존 지도용 시설파일은 `completeInventory: false`이며47안전센터·2소방서만 주소 대조한 표시점이다. 이 부분 목록을 분모로 나누면 구별 시설 수를 잘못 비교할 수 있다. 양정센터의 관할에 연제구 동이 포함되는 등 소재 구와 서비스 관할도 일치하지 않는다.', '',
        '부산진구에서 실제 대응 여력이 부족한지 판단하려면 해당 기간 전체 명부·관할, 구급차/대원/교대별 가용량, 중복·동시출동, 요청→현장 도착시간, 타 관할 지원을 같은 신고 종류·기간으로 연결해야 한다. 확인된 병목이 출동 가용량이면 배치·공동대응 문제이고, 이용 연결이면 보건·예방 안내 문제다. 보건교육을 응급 출동 능력의 대체재로 주장하지 않는다.', '',
        '**질병 신고 특성 → 고령 주민 배경 → 고령층 서비스 검토**는 대상 적합성을 살펴볼 논리다. 실제 고령 질병 신고·돌봄 공백·신규 일자리 필요를 입증하려면 환자 연령·증상과 적격자의 이용/미이용 사유·현재 서비스 범위가 추가되어야 한다. 현재 보건 근거는 구의 성인 조사이며 교육 대상도 실제 진단·필요·희망으로 정한다. 중구를 바로 노인 일자리 또는 신규 보건소 제안으로 연결하지 않는다.', '',
        '기존 공식 자료에서 다대·금곡의 관련 센터와 교육이 이미 확인됐으므로, 현재 제안은 신설보다 기존 연결 과정의 적용 여부를 검토하는 조건부 시범으로 한정했다. 자료가 부족한 부분을 다른 종류의 사업으로 채우지 않는 것이 유형 연결을 유지하는 기준이다.', '']
    insert_at = lines.index('## 6. 발표에서 사용할 연결 문장')
    lines[insert_at:insert_at] = capacity_lines
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    manifest = {'period': '2020-2024', 'populationDate': '2024-12-31', 'countP': 555786,
                'selection': 'Existing deep and comparison cases reconnected to all16 districts; not a top5 risk ranking.',
                'inputs': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p), 'priorOutputHashMatches': True} for p in inputs],
                'contextFiles': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in [
                    ROOT / 'data/processed/지역중점제안-20260917/facilities/verified-facilities.geojson',
                    ROOT / 'data/processed/지역중점제안-20260917/services/facilities.json',
                    ROOT / 'docs/40-분석결과/부산-119-신고인구에서-보건이용과-보완으로-20260917.md',
                    ROOT / 'scripts/write_district_dong_connection_20260917.py',
                    ROOT / 'scripts/verify_district_dong_connection_20260917.py']],
                'outputs': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
                            for p in [REPORT, *sorted(OUT.glob('*.csv'))]]}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'districts': len(district_table), 'connectionRows': len(connections),
                      'populationCandidateRows': len(pops), 'report': REPORT.relative_to(ROOT).as_posix()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
