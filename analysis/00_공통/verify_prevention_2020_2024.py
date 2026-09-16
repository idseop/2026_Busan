"""Independent raw-input verification; never imports author analysis modules."""
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/동별예방분석-20260914'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()

def read(path):
    return pd.read_csv(path, encoding='utf-8-sig', keep_default_na=False, dtype=str)

def verify_synthesis():
    evidence_path = OUT / 'independent_verification.json'
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    annual = read(OUT / 'receipts/annual_types.csv')
    panel = read(OUT / 'synthesis/all_type_review_panel.csv')
    assert len(panel) == len(set(zip(annual.EMRG_RSCU_ASSRT_NM, annual.EMRG_RSCU_CLSF_NM)))
    for _, row in panel.iterrows():
        selected = annual[(annual.EMRG_RSCU_ASSRT_NM == row.type) & (annual.EMRG_RSCU_CLSF_NM == row.subtype)]
        for scope in 'ABC':
            expected = selected[selected.scope == scope]['count'].astype(int).sum()
            assert int(row[scope + '_count']) == expected
        for year in range(2020, 2025):
            assert int(row[f'B_{year}']) == selected[(selected.scope == 'B') & (selected.year == str(year))]['count'].astype(int).sum()
        assert row.dong_selection_status == ('excluded_user_scope' if row.subtype == '벌집제거' else 'held_unvalidated_linkage')
        if row.subtype == '벌집제거': assert '사용자 지정' in row.selection_reason
    mapped = json.loads((OUT/'synthesis/map_population_records.json').read_text(encoding='utf-8'))
    assert len(mapped) == len({(r['year'], r['admin_dong_code']) for r in mapped}) == 1025
    assert all(r['receipt_metrics'] is None and r['boundary_version'] is None and r['linkage_status'] == 'not_validated' and r['proposal_candidate'] is None for r in mapped)
    hashes = {}
    for section in ['population', 'receipts', 'synthesis']:
        manifest = json.loads((OUT / section / 'manifest.json').read_text(encoding='utf-8'))
        for output in manifest['outputs']:
            p = ROOT/output['file'] if output['file'].startswith('data/') else OUT/section/output['file']
            assert sha(p) == output['sha256'], str(p)
        hashes[section] = sha(OUT / section / 'manifest.json')
    evidence['synthesis'] = {'status':'passed', 'panel_rows':len(panel), 'all_joint_labels_and_annual_scope_counts_match':True, 'map_records':len(mapped), 'all_spatial_metrics_unavailable_as_null':True, 'all_three_manifests_output_hashes_match':True, 'manifest_sha256':hashes}
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2),encoding='utf-8')
    print('synthesis independent checks passed', flush=True)

def main():
    evidence = {'reviewer': 'independent verifier agent', 'status': 'running', 'population': [], 'receipts': []}
    summary = read(OUT / 'population/population_summary.csv')
    singles = read(OUT / 'population/dong_single_age.csv')
    for year in range(2020, 2025):
        source = ROOT / f'data/raw/인구배경/MOIS_{year}12_연령별인구_부산전체읍면동.csv'
        with source.open(encoding='cp949', newline='') as f:
            raw = list(csv.DictReader(f))
        total = 0
        dong_count = 0
        for row in raw:
            code = re.search(r'\((\d+)\)', row['행정구역']).group(1)
            ages = [int(row[f'{year}년12월_계_{age}세'].replace(',', '')) for age in range(100)]
            ages.append(int(row[f'{year}년12월_계_100세 이상'].replace(',', '')))
            expected = sum(ages)
            saved = summary[(summary.year == str(year)) & (summary.admin_code == code)]
            assert len(saved) == 1
            s = saved.iloc[0]
            assert int(s.population) == expected == int(row[f'{year}년12월_계_총인구수'].replace(',', ''))
            for group, values in [('0~14', ages[:15]), ('15~64', ages[15:65]), ('65+', ages[65:])]:
                assert int(s['age_' + group]) == sum(values)
                assert abs(float(s['share_' + group + '_pct']) - 100 * sum(values) / expected) < 1e-10
            if s.level == 'dong':
                dong_count += 1
                total += expected
                saved_ages = singles[(singles.year == str(year)) & (singles.admin_code == code)].copy()
                saved_ages['age'] = saved_ages.age.astype(int)
                assert saved_ages.sort_values('age').age_population.astype(int).tolist() == ages
        city = summary[(summary.year == str(year)) & (summary.level == 'city')].iloc[0]
        assert total == int(city.population) and dong_count == 205 and len(raw) == 222
        evidence['population'].append({'year': year, 'source_sha256': sha(source), 'dong_count': dong_count, 'dong_sum_equals_city': total, 'all_single_ages_and_support_groups_match_raw': True})
        print(f'population {year}: passed', flush=True)
    manifest = json.loads((ROOT / 'data/interim/분석입력-2020-2024/manifest.json').read_text(encoding='utf-8-sig'))
    annual = read(OUT / 'receipts/annual_types.csv')
    months = read(OUT / 'receipts/time_month.csv')
    dong = read(OUT / 'receipts/original_dong_types.csv')
    assert sorted(e['year'] for e in manifest['reports']) == list(range(2020, 2025))
    for entry in manifest['reports']:
        year = entry['year']; source = ROOT / entry['file']
        assert source.is_relative_to(ROOT / 'data/raw/119접수')
        digest = sha(source); assert digest == entry['sha256']
        cols = ['CLMTY_CTPV_NM','CLMTY_SGG_NM','CLMTY_EMD_NM','PRCS_RSLT_SE_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','DCLR_DT']
        counts = Counter(); month_counts = Counter(); dong_counts = Counter(); regions = Counter(); n = 0
        for frame in pd.read_csv(source, encoding=entry['encoding'], dtype=str, keep_default_na=False, usecols=lambda c:c.upper() in cols, chunksize=100000):
            frame.columns = frame.columns.str.upper()
            n += len(frame); regions.update(frame.CLMTY_CTPV_NM)
            for r in frame.itertuples(index=False, name=None):
                values = dict(zip(frame.columns, r))
                if values['CLMTY_CTPV_NM'] != '부산광역시': continue
                typ, sub, result = (values[k] for k in ['EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM'])
                scopes = ['A']
                if result == '정상':
                    scopes.append('B')
                    if sub not in {'업무운행','훈련출동','구급차소독'}: scopes.append('C')
                for scope in scopes:
                    counts[scope,typ,sub,result] += 1
                    month_counts[scope,typ,sub,int(values['DCLR_DT'][4:6])] += 1
                    dong_counts[scope,values['CLMTY_SGG_NM'],values['CLMTY_EMD_NM'],typ,sub,result] += 1
        for table, keys, expected in [(annual,['scope','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM'],counts),(months,['scope','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','month'],month_counts),(dong,['scope','CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_ASSRT_NM','EMRG_RSCU_CLSF_NM','PRCS_RSLT_SE_NM'],dong_counts)]:
            actual = Counter()
            for _, row in table[table.year == str(year)].iterrows():
                key = tuple(int(row[k]) if k == 'month' else row[k] for k in keys)
                actual[key] += int(row['count'])
            assert actual == expected, (year, keys, list((actual-expected).items())[:3])
        assert n == entry['rowsFromPriorFullAudit']
        ledger_rows = 0; ledger_scopes = Counter()
        for ledger in pd.read_csv(OUT / f'receipts/ledger_{year}.csv.gz', dtype=str, keep_default_na=False, chunksize=100000):
            assert ledger.csv_record_index.astype(int).tolist() == list(range(ledger_rows + 1, ledger_rows + len(ledger) + 1))
            assert ledger.source_file.eq(entry['file']).all() and ledger.year.eq(str(year)).all()
            assert ledger.spatial_join_status.eq('unverified_administrative_dong').all()
            assert ledger.spatial_unlinked_reason.ne('').all()
            for scope in 'ABC': ledger_scopes[scope] += int(ledger['include_' + scope].eq('True').sum())
            ledger_rows += len(ledger)
        assert ledger_rows == n
        assert all(ledger_scopes[s] == sum(v for k,v in counts.items() if k[0] == s) for s in 'ABC')
        evidence['receipts'].append({'year': year, 'source_sha256': digest, 'raw_rows': n, 'raw_province_labels': dict(regions), 'scope_counts': dict(ledger_scopes), 'all_annual_type_month_original_dong_cells_match_independent_raw_counts': True, 'ledger_complete_unique_sequential_source_records': True, 'all_ledger_rows_explicitly_spatial_unverified_with_reason': True})
        print(f'receipts {year}: passed', flush=True)
    evidence['status'] = 'passed'
    evidence['scope'] = 'All 5 raw population and 5 raw receipt sources; full independent population single-age/support comparison, all receipt annual-type/month/original-dong cells. Narrative and subsequent synthesis reviewed separately.'
    evidence['verified_artifact_hashes'] = {str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in [OUT/'population/population_summary.csv',OUT/'population/dong_single_age.csv',OUT/'receipts/annual_types.csv',OUT/'receipts/time_month.csv',OUT/'receipts/original_dong_types.csv']}
    (OUT / 'independent_verification.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    verify_synthesis() if '--synthesis' in sys.argv else main()
