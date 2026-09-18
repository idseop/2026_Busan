"""원본 행에서 만든 교차집계의 처리조건 민감도. 위험순위가 아니다."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'data/processed/119기초분석/부산명시_연도구군종별분류처리결과.csv'
OUT = ROOT / 'data/processed/신고조건비교'
DOC = ROOT / 'docs/40-분석결과/신고-조건별-지역비교.md'
YEARS = [str(y) for y in range(2018, 2025)]
EXCLUDED = ('업무운행', '훈련출동', '구급차소독')


def main():
    groups = defaultdict(Counter)
    excluded = defaultdict(Counter)
    direct_totals = defaultdict(Counter)
    with SOURCE.open(encoding='utf-8-sig', newline='') as stream:
        for r in csv.DictReader(stream):
            year, district = r['연도'], r['재난시군구']
            assert year in YEARS
            count = int(r['접수행수'])
            assert count > 0
            selected = ['A']
            if r['처리결과'] == '정상':
                selected.append('B')
                if r['긴급구조분류'] not in EXCLUDED:
                    selected.append('C')
                else:
                    excluded[year][r['긴급구조분류']] += count
            for scenario in selected:
                groups[year, district][scenario] += count
                groups['7년합계', district][scenario] += count
                direct_totals[year][scenario] += count
    audit = json.loads((ROOT / 'data/interim/119접수감사/audit.json').read_text(encoding='utf-8-sig'))
    expected = {str(f['year']): f['busan']['rows'] for f in audit['files']}
    assert {y: direct_totals[y]['A'] for y in YEARS} == expected
    reference_districts = {d for y, d in groups if y == '2018'}
    assert len(reference_districts) == 17 and '' in reference_districts
    output, summaries = [], []
    for year in YEARS + ['7년합계']:
        districts = {d: c for (y, d), c in groups.items() if y == year}
        assert set(districts) == reference_districts
        ranks = {s: {d: 1 + sum(other[s] > c[s] for od, other in districts.items() if od)
                     for d, c in districts.items() if d} for s in 'ABC'}
        for district, c in sorted(districts.items()):
            assert c['A'] >= c['B'] >= c['C'] >= 0
            output.append({'기간': year, '재난시군구': district,
                           'A_모든처리': c['A'], 'B_정상': c['B'], 'C_정상_3분류제외': c['C'],
                           'A에서B_제외행': c['A'] - c['B'], 'B에서C_제외행': c['B'] - c['C'],
                           **{f'{s}_건수순위': ranks[s].get(district, '') for s in 'ABC'},
                           'A대비B_순위상승': ranks['A'][district] - ranks['B'][district] if district else '',
                           'B대비C_순위상승': ranks['B'][district] - ranks['C'][district] if district else '',
                           'A대비C_순위상승': ranks['A'][district] - ranks['C'][district] if district else ''})
        total = {s: sum(c[s] for c in districts.values()) for s in 'ABC'}
        direct = {s: direct_totals[year][s] if year in YEARS else sum(direct_totals[y][s] for y in YEARS) for s in 'ABC'}
        assert total == direct
        removed = {t: excluded[year][t] if year in YEARS else sum(excluded[y][t] for y in YEARS) for t in EXCLUDED}
        assert total['B'] - total['C'] == sum(removed.values())
        summaries.append({'기간': year, **total, 'B에서C_제외내역': removed})
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / '연도구군_조건별접수건수_순위변화.csv'
    with target.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=output[0].keys())
        writer.writeheader()
        writer.writerows(output)
    manifest = {'source': str(SOURCE.relative_to(ROOT)),
                'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'conditions': {'A': '모든 처리결과', 'B': '처리결과 원문 정확히 정상',
                               'C': 'B 중 긴급구조분류 원문이 업무운행·훈련출동·구급차소독인 행만 제외'},
                'excluded_exact_values': EXCLUDED, 'years': YEARS, 'rows': len(output),
                'rank_rule': '구군별 접수 건수 내림차순, 동률 min, 지역 빈값 순위 제외; 상승값=이전순위-이후순위',
                'checks': {'year_A_matches_original_audit': True, 'same_16_districts_plus_blank_each_year': True,
                           'A_greater_equal_B_greater_equal_C': True, 'district_sums_match_direct_scenario_sums': True,
                           'B_minus_C_matches_exact_exclusion_counts': True},
                'limitations': ['접수 건수의 조건 민감도이며 실제 사고·환자 수 또는 최종 위험·지원 우선순위 아님',
                                '원본 연령 없음; 연령 추정·대입하지 않음', '확인출동·순찰출동을 일괄 제외하지 않음',
                                '동일신고 제외만으로 고유 사고를 식별하지 않음'], 'summaries': summaries}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 신고 처리조건에 따른 지역 비교 — 2018~2024년', '',
             '**부산 전체 16구군의 접수 건수 순서가 필터에 따라 얼마나 달라지는지 확인한다. 최종 위험순위나 지원 우선순위가 아니다.**', '',
             '모집단은 재난시도명에 부산광역시가 명시된 신고 접수다. 같은 원본 행의 지역·종별·분류·처리결과 교차집계를 사용했다. 연령 변수는 없어 연령별 선별·추정을 하지 않았다.', '',
             '| 조건 | 정확한 범위 |', '|---|---|', '| A | 모든 처리결과 |',
             '| B | 처리결과가 정확히 `정상` |',
             '| C | B에서 세부분류가 정확히 `업무운행`, `훈련출동`, `구급차소독`인 행만 제외 |', '',
             'C는 명시된 운영활동 3개만 제외한 보수적 비교 시나리오다. 실제 사고만 남았다는 뜻이 아니다. 확인출동·순찰출동이나 그 밖의 분류를 임의로 일괄 제외하지 않았다. 동일신고 제외만으로 사고 중복 제거가 완료되는 것도 아니다.', '',
             '## 연도별 조건 합계', '', '| 기간 | A | B | C | B→C 제외 |', '|---|---:|---:|---:|---:|']
    for r in summaries:
        lines.append(f"| {r['기간']} | {r['A']:,} | {r['B']:,} | {r['C']:,} | {r['B']-r['C']:,} |")
    for period in ['2024', '7년합계']:
        lines += ['', f'## {period} 전체 구군 비교', '',
                  '가나다순이며 미기재는 별도 표시한다. 순위는 해당 기간·조건의 접수 건수 내림차순(동률 최소순위)이다. 인구나 시설 규모를 보정한 위험도가 아니다.', '',
                  '| 구군 | A | B | C | A순위 | B순위 | C순위 |', '|---|---:|---:|---:|---:|---:|---:|']
        subset = [r for r in output if r['기간'] == period]
        for r in subset:
            lines.append('| ' + ' | '.join([r['재난시군구'] or '미기재'] +
                         [f"{r[k]:,}" for k in ['A_모든처리', 'B_정상', 'C_정상_3분류제외']] +
                         [str(r[f'{s}_건수순위']) or '—' for s in 'ABC']) + ' |')
        changes = [r for r in subset if r['재난시군구'] and r['A대비C_순위상승']]
        lines += ['', f'A→C에서 건수 순위가 달라진 구군은 {len(changes)}개다. ' +
                  ('; '.join(f"{r['재난시군구']} {r['A_건수순위']}→{r['C_건수순위']}" for r in changes) if changes else '변동 없음.')]
    lines += ['', '## 해석과 검증', '',
              '- 7개 연도 모두 16구군과 지역 미기재를 유지했다. 미기재를 다른 구군에 배분하지 않았고 순위에서만 제외했다.',
              '- 모든 연도의 A 합계를 기존 원본 전수감사와 대조했다. 각 지역 A≥B≥C, 직접 조건집계와 지역합, B−C와 3분류 제외 합계가 모두 일치한다.',
              '- 7년 합계 순위는 누적 접수량의 조건 비교다. 연도별 변화는 CSV의 119개 연도·지역행에서 별도로 확인해야 한다. CSV에는 7년 합계 17행도 포함한다.',
              '- 조건을 바꿔도 남는 다른 운영활동, 분류 기록 변화, 반복 접수, 지역별 규모 차이가 있어 이 결과만으로 정책 대상이나 효과를 확정하지 않는다.', '',
              '원본 교차집계: `data/processed/119기초분석/부산명시_연도구군종별분류처리결과.csv`.',
              '결과와 출처 해시·제외내역·검증: `data/processed/신고조건비교/연도구군_조건별접수건수_순위변화.csv`, 같은 폴더 `manifest.json`.',
              '재현: `.venv-check/Scripts/python.exe analysis/00_공통/compare_receipt_conditions.py`.', '']
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'rows': len(output), 'summaries': summaries}, ensure_ascii=True))


if __name__ == '__main__':
    main()
