"""Five-year priorities and leave-one-year-out checks from verified annual cells.

No raw receipts or population snapshots are appended or altered.
Run with .venv-check/Scripts/python.exe from the repository root.
"""
from pathlib import Path
import hashlib
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/5개년통합-지역유형-제안연결-20260917'
FIG = ROOT / 'figures/5개년통합-지역유형-제안연결-20260917'
BASE = ROOT / 'data/processed/신고주민연결심화-20260917'
GU = ROOT / 'data/processed/구군에서동심화연결-20260917'
HEALTH = ROOT / 'data/processed/신고보건심화-20260917'
YEARS = [str(y) for y in range(2020, 2025)]
KEY = ['district', 'rawDong', 'type', 'subtype']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ranked(frame, group, count='countP'):
    out = frame.copy()
    def rank(values):
        if group:
            return values.groupby([out[k] for k in group]).rank(method='min', ascending=False)
        return values.rank(method='min', ascending=False)
    out['pooledCountRank'] = rank(out[count]).where(out[count] > 0).astype('Int64')
    cols = []
    for year in YEARS:
        column = 'rankWithout' + year
        values = out[count] - out[year]
        out[column] = rank(values).where(values > 0).astype('Int64')
        cols.append(column)
    out['withoutYearBestRank'] = out[cols].min(axis=1).astype('Int64')
    out['withoutYearWorstRank'] = out[cols].max(axis=1).astype('Int64')
    out['withoutYearTop10Count'] = out[cols].le(10).fillna(False).sum(axis=1)
    out['largestYearSharePct'] = out[YEARS].max(axis=1).div(out[count].replace(0, np.nan)) * 100
    return out


def top5_time(keys, inputs):
    """Fill the previously unavailable time profiles for the 45 selected pairs."""
    mapping = {'CLMTY_SGG_NM': 'district', 'CLMTY_EMD_NM': 'rawDong',
               'EMRG_RSCU_ASSRT_NM': 'type', 'EMRG_RSCU_CLSF_NM': 'subtype'}
    # All selected pairs are the three major EMS subtypes, so normal=B=C=P here.
    assert set(keys.type) == {'구급'} and set(keys.subtype) <= {'질병', '질병외', '부상'}
    old = json.loads((BASE / 'direction-connections/manifest.json').read_text(encoding='utf-8'))
    hashes = {r['path']: r['sha256'] for r in old['inputs']}
    frames = []
    for year in YEARS:
        path = ROOT / f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{year}.csv.gz'
        rel = path.relative_to(ROOT).as_posix()
        assert digest(path) == hashes[rel]
        inputs.append({'key': 'timeInput' + year, 'path': rel, 'sha256': hashes[rel], 'priorHashMatched': True})
        frame = pd.read_csv(path, usecols=list(mapping) + ['DCLR_DT', 'PRCS_RSLT_SE_NM'], dtype=str).rename(columns=mapping)
        frame = frame.merge(keys, on=KEY, how='inner', validate='many_to_one')
        stamp = pd.to_datetime(frame.DCLR_DT.str.strip(), format='%Y%m%d%H%M%S', errors='raise')
        assert stamp.dt.year.eq(int(year)).all()
        frame['year'] = int(year); frame['month'] = stamp.dt.month
        frame['weekday'] = stamp.dt.dayofweek; frame['hour'] = stamp.dt.hour
        frame['hour4'] = stamp.dt.hour // 4
        frame['weekdayHour'] = frame.weekday * 24 + frame.hour
        frames.append(frame.drop(columns='DCLR_DT'))
    frame = pd.concat(frames, ignore_index=True)
    summaries, cells = [], []
    calendar = pd.date_range('2020-01-01', '2024-12-31')
    dimensions = {'month': range(1, 13), 'weekday': range(7), 'hour': range(24), 'weekdayHour': range(168)}
    for key, allrows in frame.groupby(KEY):
        for scope, rows in [('A', allrows), ('P', allrows[allrows.PRCS_RSLT_SE_NM.eq('정상')])]:
            for year in [0, *map(int, YEARS)]:
                part = rows if year == 0 else rows[rows.year == year]
                record = dict(zip(KEY, key)); record.update(scope=scope, year=year, count=len(part))
                for dim in ['month', 'weekday', 'hour4']:
                    counts = part[dim].value_counts()
                    record[dim + 'Peak'] = '|'.join(str(x) for x in sorted(counts[counts == counts.max()].index)) if len(part) else ''
                night = int(((part.hour >= 20) | (part.hour < 8)).sum())
                record.update(night20to07Count=night, night20to07Pct=100 * night / len(part) if len(part) else None)
                summaries.append(record)
            for dimension, values in dimensions.items():
                counts = rows[dimension].value_counts().reindex(values, fill_value=0)
                for value, count in counts.items():
                    days = int((calendar.month == value).sum()) if dimension == 'month' else int((calendar.dayofweek == (value if dimension == 'weekday' else value // 24)).sum()) if dimension in ['weekday', 'weekdayHour'] else len(calendar)
                    cells.append({**dict(zip(KEY, key)), 'scope': scope, 'dimension': dimension, 'value': value,
                                  'count': int(count), 'denominator': len(rows), 'sharePct': 100 * count / len(rows) if len(rows) else None,
                                  'calendarDays': days, 'receiptsPerCalendarDay': count / days})
    return pd.DataFrame(summaries), pd.DataFrame(cells)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    paths = {
        'names': BASE / 'direction-reassessment/all-194-names-70-subtypes.csv',
        'district': GU / '16구군-동일조건-전체비교.csv',
        'subtypes': GU / '구군-전체70유형-동별기본연결.csv',
        'population': BASE / 'direction-reassessment/all-name-population-candidates.csv',
        'time': BASE / 'direction-connections/major-burden-time-summary.csv',
        'timeCells': BASE / 'direction-connections/major-burden-time-cells.csv',
        'proposals': HEALTH / 'regional-improvement-and-evaluation.csv',
        'healthLinks': HEALTH / 'selected-region-evidence-links.csv',
    }
    recorded = {}
    for path in [GU / 'manifest.json', BASE / 'direction-reassessment/manifest.json',
                 BASE / 'direction-connections/manifest.json', HEALTH / 'delivery-manifest.json']:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        for item in (data if isinstance(data, list) else data.get('outputs', [])):
            recorded[item.get('path', item.get('file'))] = item['sha256']
    inputs = []
    for key, path in paths.items():
        rel = path.relative_to(ROOT).as_posix()
        assert rel in recorded, f'Prior checksum unavailable: {rel}'
        assert digest(path) == recorded[rel], f'Prior checksum changed: {rel}'
        inputs.append({'key': key, 'path': rel, 'sha256': digest(path), 'priorHashMatched': True})
    data = {key: pd.read_csv(path) for key, path in paths.items()}
    names = data['names']
    assert len(names) == 194 * 70 and names.countP.sum() == 555786
    assert (names[YEARS].sum(axis=1) == names.countP).all()
    assert not names.duplicated(KEY).any()

    outputs = []
    def save(df, name):
        path = OUT / name
        df.to_csv(path, index=False, encoding='utf-8-sig')
        outputs.append(path)
        return df

    district = names.groupby('district', as_index=False)[YEARS + ['countP']].sum()
    district = ranked(district, []).sort_values(['pooledCountRank', 'district'])
    district['citySharePct'] = district.countP / names.countP.sum() * 100
    population_cols = ['district', 'total', 'pct_0_14', 'pct_15_39', 'pct_40_64', 'pct_65_plus',
                       'retentionPct', 'referenceDate']
    district = district.merge(data['district'][population_cols], on='district', validate='one_to_one')
    district_rank = district.set_index('district').pooledCountRank.to_dict()
    save(district, '01-16구군-5년합계와-한해제외순위.csv')

    city = names.groupby(['type', 'subtype'], as_index=False)[YEARS + ['countP']].sum()
    city = ranked(city, []).sort_values(['pooledCountRank', 'type', 'subtype'])
    city['citySharePct'] = city.countP / names.countP.sum() * 100
    save(city, '02-전체70유형-5년합계와-한해제외순위.csv')

    subtypes = data['subtypes'].rename(columns={'count': 'countP'}).copy()
    subtypes['districtTotalRank'] = subtypes.district.map(district_rank)
    subtypes = ranked(subtypes, ['district'])
    subtypes['typeCountRankAcrossDistricts'] = subtypes.groupby(['type', 'subtype']).countP.rank(method='min', ascending=False).where(subtypes.countP > 0).astype('Int64')
    subtypes = subtypes.sort_values(['districtTotalRank', 'pooledCountRank', 'type', 'subtype'])
    save(subtypes, '03-구군별70유형-동일유형연결.csv')
    leading = subtypes[subtypes.pooledCountRank <= 3].copy()
    save(leading, '04-구군별-주요3유형.csv')

    dong = ranked(names, ['type', 'subtype'])
    within = ranked(names, ['district', 'type', 'subtype'])
    rankcols = [x for x in within if x.startswith('rankWithout') or x in ('pooledCountRank', 'withoutYearBestRank', 'withoutYearWorstRank')]
    for col in rankcols:
        dong['withinDistrict_' + col] = within[col]
    dong['districtTotalRank'] = dong.district.map(district_rank)
    dong['withinDistrictSubtypeSharePct'] = dong.countP.div(dong.groupby(['district', 'type', 'subtype']).countP.transform('sum').replace(0, np.nan)) * 100
    save(dong, '05-194지역명70유형-5년합계와-한해제외순위.csv')
    linked = dong.merge(leading[['district', 'type', 'subtype', 'pooledCountRank']],
                        on=['district', 'type', 'subtype'], suffixes=('', '_guType'), validate='many_to_one')
    linked = linked[(linked.withinDistrict_pooledCountRank <= 3) & (linked.countP > 0)]
    linked = linked.sort_values(['districtTotalRank', 'pooledCountRank_guType', 'withinDistrict_pooledCountRank', 'rawDong'])
    time = data['time'].query("scope == 'P' and year == 0")
    linked = linked.merge(time[KEY + ['count', 'monthPeak', 'weekdayPeak', 'hour4Peak', 'hour6Peak', 'night20to07Pct']],
                          on=KEY, how='left', validate='one_to_one')
    assert (linked.loc[linked['count'].notna(), 'countP'] == linked.loc[linked['count'].notna(), 'count']).all()
    linked['timeDataState'] = np.where(linked['count'].notna(), '기존 시간집계 연결', '현재 심층 시간표 대상 밖')
    linked['compositionState'] = np.where((linked.aboveRestBusan30 == 30) & (linked.aboveRestDistrict30 == 30),
                                         '기존30조건 모두 구성비 우세', '구성비 우세가 조건에 따라 다름')
    save(linked, '06-구군주요유형에서-동별상위3-연결.csv')
    top5 = linked[linked.districtTotalRank <= 5].copy()
    times, timecells = top5_time(top5[KEY], inputs)
    save(times, '10-상위5구군45조합-시간요약.csv')
    save(timecells, '11-상위5구군45조합-5년시간교차집계.csv')
    top5 = top5.drop(columns=['count', 'monthPeak', 'weekdayPeak', 'hour4Peak', 'hour6Peak', 'night20to07Pct', 'timeDataState'])
    top5 = top5.merge(times.query("scope == 'P' and year == 0").drop(columns=['scope', 'year']), on=KEY, validate='one_to_one')
    assert top5['count'].eq(top5.countP).all()
    top5['timeDataState'] = '5년 통합 및 연도별 시간집계 완료'
    save(top5, '07-상위5구군-유형별동비교.csv')

    chosen_keys = top5[['district', 'rawDong']].drop_duplicates()
    pop = data['population'].merge(chosen_keys, on=['district', 'rawDong'], validate='many_to_one')
    # Keep every age and all five annual snapshots; never sum population across years/candidates.
    save(pop, '08-상위5구군-동후보-5개연말전체연령.csv')

    proposals = data['proposals'].merge(data['healthLinks'], on=['district', 'rawDong'], validate='one_to_many')
    proposals['districtTotalRank'] = proposals.district.map(district_rank)
    proposals = proposals.sort_values(['districtTotalRank', 'subtype'])
    save(proposals, '09-5년신고에서-기존대응-보완평가로.csv')

    summary = {
        'period': '2020-01-01/2024-12-31', 'excludedYear': 2025,
        'complete17Count': 704689, 'countP': int(names.countP.sum()),
        'scope': '정상 처리, 운영성 3분류와 벌집제거 제외(P); 기존 정의 유지',
        'top5Districts': district.head(5).district.tolist(),
        'top5Count': int(district.head(5).countP.sum()),
        'top5SharePct': float(district.head(5).citySharePct.sum()),
        'top5OrderStableAfterAnyOneYearRemoved': bool((district.head(5)[['rankWithout' + y for y in YEARS]].eq(district.head(5).pooledCountRank, axis=0)).all().all()),
        'major3Count': int(city.head(3).countP.sum()),
        'major3SharePct': float(city.head(3).citySharePct.sum()),
        'districtTypeRows': len(subtypes), 'dongTypeRows': len(dong),
        'leadingDongRows': len(linked), 'top5DongRows': len(top5),
        'top5TimeSummaryRows': len(times), 'top5TimeCellRows': len(timecells),
        'timeScope': '45조합의 현재17개 조건 내 A(전체처리)와 P(정상)를 비교. 제외 전 core8의 시간분포를 재현한 것은 아님',
        'oneYearOmissionMeaning': '기존5년 중 한 해씩 제외한 4년 합계. 독립 표본·신뢰구간·미래 검증이 아님',
        'rankMeaning': '선택된 접수 건수순; 피해 심각성이나 종합 위험 순위가 아님',
        'ratioRule': '5년 분자 합계 / 5년 분모 합계. 연도별 비율의 단순평균을 사용하지 않음',
        'populationRule': '각 연말 주민 수와 비중; 5년 주민 수를 누적하지 않음',
        'proposalMeaning': '기존 근거의 조건부 시범 2곳(금곡·다대); 효과 측정 미실시',
    }
    (OUT / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    outputs.append(OUT / 'summary.json')
    plot(district, subtypes, city)
    plot_time(timecells, top5)
    outputs += sorted(FIG.glob('*'))
    manifest = {'inputs': inputs, 'outputs': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': digest(p)} for p in outputs],
                'code': {'path': Path(__file__).relative_to(ROOT).as_posix(), 'sha256': digest(Path(__file__))}}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def plot(district, subtypes, city):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False, 'font.size': 12,
                         'axes.spines.top': False, 'axes.spines.right': False})
    colors = {'질병': '#0b7285', '질병외': '#e49b36', '부상': '#416aaf', '나머지': '#c8d1d6'}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(17, 9), gridspec_kw={'width_ratios': [1.9, 1]}, facecolor='#fbfcfc')
    totals = district.set_index('district').countP
    tbl = subtypes.pivot_table(index='district', columns='subtype', values='countP', aggfunc='sum').reindex(totals.index)
    tbl['나머지'] = totals - tbl[['질병', '질병외', '부상']].sum(axis=1)
    bottom = np.zeros(len(tbl))
    for name, color in colors.items():
        ax.barh(np.arange(len(tbl)), tbl[name], left=bottom, color=color, label=name, height=.66)
        bottom += tbl[name].values
    for i, n in enumerate(totals):
        ax.text(n + 650, i, f'{n:,}', va='center', fontsize=11, color='#193442')
    ax.set_yticks(range(len(tbl)), [f'{i+1:02d}  {name}' for i, name in enumerate(tbl.index)])
    ax.invert_yaxis(); ax.set_xlim(0, 74000); ax.set_xlabel('2020~2024년 합계 접수 건수')
    ax.set_title('상위 5개 구·군에 선택 접수의 45.3%', loc='left', fontsize=18, pad=20, fontweight='bold')
    ax.legend(loc='lower right', frameon=False); ax.grid(axis='x', alpha=.14); ax.set_axisbelow(True)
    heads = city.head(3).set_index('subtype')
    for name in ['질병', '질병외', '부상']:
        bx.plot(range(5), heads.loc[name, YEARS], marker='o', color=colors[name], linewidth=2.5, label=name)
        bx.text(4.1, heads.loc[name, '2024'], name, va='center', color=colors[name], fontsize=12)
    bx.set_xticks(range(5), YEARS); bx.set_xlim(-.15, 5.1); bx.set_ylim(0, 52000)
    bx.set_ylabel('연간 선택 접수 건수'); bx.grid(axis='y', alpha=.14)
    bx.set_title('질병·질병외의 순서는 기간에 민감', loc='left', fontsize=16, pad=20, fontweight='bold')
    fig.text(.06, .965, '부산 신고 특성: 5년을 합쳐 대상을 정하고, 연도별로 지속성을 확인', fontsize=22, fontweight='bold', color='#193442')
    fig.text(.06, .045, '전체 555,786건 · 정상 처리 / 운영성 3분류·벌집제거 제외 · 건수순은 위험 순위가 아닙니다.', fontsize=12, color='#475b65')
    fig.text(.06, .016, '한 해씩 제외한 5가지 비교에서도 상위 5개 구·군의 순서가 유지됩니다. 인구는 연말별 배경으로 별도 연결합니다.', fontsize=12, color='#475b65')
    fig.subplots_adjust(left=.1, right=.97, top=.87, bottom=.15, wspace=.26)
    fig.savefig(FIG / '01-5년통합-지역규모와유형.png', dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(FIG / '01-5년통합-지역규모와유형.svg', facecolor=fig.get_facecolor())
    plt.close(fig)


def plot_time(cells, cases):
    import matplotlib.pyplot as plt
    selection = [('부산진구', '부전동', '질병외'), ('부산진구', '부전동', '부상'),
                 ('해운대구', '우동', '질병'), ('해운대구', '좌동', '질병'),
                 ('사하구', '다대동', '질병'), ('북구', '금곡동', '질병'),
                 ('사상구', '모라동', '질병'), ('사상구', '주례동', '질병')]
    grids = []
    for district, dong, subtype in selection:
        mask = (cells.district == district) & (cells.rawDong == dong) & (cells.subtype == subtype) & (cells.scope == 'P') & (cells.dimension == 'weekdayHour')
        rows = cells.loc[mask].sort_values('value')
        assert len(rows) == 168
        grids.append(rows.sharePct.to_numpy().reshape(7, 24))
    maximum = max(float(x.max()) for x in grids)
    fig, axes = plt.subplots(4, 2, figsize=(16, 12), facecolor='#fbfcfc')
    for ax, key, matrix in zip(axes.flat, selection, grids):
        row = cases[(cases.district == key[0]) & (cases.rawDong == key[1]) & (cases.subtype == key[2])].iloc[0]
        im = ax.imshow(matrix, aspect='auto', vmin=0, vmax=maximum, cmap='YlGnBu')
        ax.set_yticks(range(7), list('월화수목금토일')); ax.set_xticks([0, 6, 12, 18, 23], ['00시', '06시', '12시', '18시', '23시'])
        ax.tick_params(length=0, labelsize=11)
        ax.set_title(f'{key[0]} {key[1]} · {key[2]}  {int(row.countP):,}건', loc='left', fontsize=14, pad=9)
    fig.text(.06, .965, '지역과 유형이 다르면 신고의 시간대도 달라집니다', fontsize=24, weight='bold', color='#193442')
    fig.text(.06, .927, '2020~2024년 통합 · 각 지역·유형의 전체 접수를 100%로 본 요일×시간 구성비', fontsize=14, color='#475b65')
    fig.subplots_adjust(left=.07, right=.91, bottom=.1, top=.88, hspace=.58, wspace=.18)
    color_ax = fig.add_axes([.935, .22, .013, .57])
    fig.colorbar(im, cax=color_ax, label='해당 조합 접수 중 비중(%)')
    fig.text(.06, .04, '정상 처리(P) · 각 요일 261일 · 색은 시간 구성비이며 지역 위험도가 아닙니다. 동명 기준 접수로 비교합니다.', fontsize=12, color='#475b65')
    fig.savefig(FIG / '02-지역유형별-5년통합시간.png', dpi=140, facecolor=fig.get_facecolor())
    fig.savefig(FIG / '02-지역유형별-5년통합시간.svg', facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == '__main__':
    main()
