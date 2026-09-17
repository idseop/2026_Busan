"""전처리 출력의 원본 행 추적·집합 포함·제외 기록을 독립 검산한다."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    out = ROOT / sys.argv[1]
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    results = []
    for item, totals in zip(manifest['inputs'], manifest['year_counts'], strict=True):
        year = item['year']
        a = pd.read_csv(out / f'A_{year}.csv.gz', dtype=str, keep_default_na=False)
        a_ids = a.source_record_index.astype(int).to_numpy()
        coverage = np.zeros(totals['원본'], dtype=np.uint8)
        assert len(np.unique(a_ids)) == len(a_ids)
        coverage[a_ids - 1] += 1
        for df in pd.read_csv(out / f'제외기록_{year}.csv.gz', dtype=str, keep_default_na=False, chunksize=100000):
            positions = df.source_record_index.astype(int).to_numpy()
            assert len(np.unique(positions)) == len(positions)
            coverage[positions - 1] += 1
            assert (df.region_status.ne('busan_explicit') | df.missing_columns.ne('')).all()
        assert (coverage == 1).all(), '원본 행에 누락·중복 분류가 있습니다.'
        previous = set(a_ids)
        for scope in ['B', 'C']:
            current = set(pd.read_csv(out / f'{scope}_{year}.csv.gz', usecols=['source_record_index']).source_record_index)
            assert current <= previous and len(current) == totals[scope]
            previous = current
        # 원본의 17개 값을 연도별 처음·중간·마지막 포함 9행에서 그대로 보존했는지 확인.
        sample = a.iloc[np.linspace(0, len(a)-1, 9, dtype=int)].copy()
        sample.index = sample.source_record_index.astype(int)
        wanted = set(sample.index)
        matched = 0; offset = 0
        for df in pd.read_csv(ROOT / item['path'], dtype=str, keep_default_na=False, encoding=item['encoding'], chunksize=100000):
            df.columns = df.columns.str.upper()
            indexes = sorted(i for i in wanted if offset < i <= offset + len(df))
            if indexes:
                source = df.iloc[[i-offset-1 for i in indexes]][manifest['selected_columns']]
                target = sample.loc[indexes, manifest['selected_columns']]
                assert source.to_numpy().tolist() == target.to_numpy().tolist()
                matched += len(indexes)
            offset += len(df)
        assert matched == 9
        results.append({'year':year,'all_source_rows_partitioned_once':True,'C_subset_B_subset_A':True,'raw_value_samples_matched':matched})
        print(year, '원본 행 전체 분할·A/B/C 포함관계·원문 표본 보존 통과', flush=True)
    (out / '독립검증.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
