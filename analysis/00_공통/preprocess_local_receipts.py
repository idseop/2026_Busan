"""로컬 신고 원본에 저장소의 선택17개·A/B/C 기준을 적용한다.

원본·기존 산출물은 덮어쓰지 않는다. 원본 필드는 문자열 그대로 보존한다.
실행: .venv/Scripts/python.exe analysis/00_공통/preprocess_local_receipts.py
"""
from pathlib import Path
from collections import Counter
from contextlib import ExitStack
from datetime import datetime
import ast
import csv
import gzip
import hashlib
import json

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'analysis/00_공통/select_complete_receipts_2020_2024.py'
POLICY = ROOT / 'analysis/00_공통/complete_all_selected_20260915.py'


def reference_constants():
    # 경로·기존 감사 파일에 의존하는 원본 프로그램을 실행하지 않고 상수만 재사용한다.
    tree = ast.parse(REFERENCE.read_text(encoding='utf-8-sig'))
    wanted = {'REQUIRED_DONG', 'AUXILIARY', 'OPERATIONS', 'WEEK', 'SEASON', 'ID'}
    env = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            names = {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            if names & wanted:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(REFERENCE), 'exec'), {'__builtins__': {}}, env)
    return env


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    ref = reference_constants()
    fields = ref['REQUIRED_DONG'] + ref['AUXILIARY'][:9]
    assert len(fields) == len(set(fields)) == 17
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out = ROOT / 'data/processed' / f'신고17개-로컬전처리-{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    prior_file = ROOT / 'data/interim/결측점검/실행기록.json'
    prior = {x['path']: x for x in json.loads(prior_file.read_text(encoding='utf-8-sig'))['files']} if prior_file.exists() else {}
    inputs = []
    for year in range(2020, 2025):
        candidates = [p for p in (ROOT / 'data').rglob(f'신고접수_{year}.csv') if not {'processed', 'interim'} & set(p.relative_to(ROOT / 'data').parts)]
        if len(candidates) != 1:
            raise ValueError(f'{year}: 원본 후보가 {len(candidates)}개입니다. 입력을 명시해야 합니다.')
        path = candidates[0]
        rel = path.relative_to(ROOT).as_posix()
        digest = sha(path)
        with path.open(encoding='utf-8-sig', newline='') as f:
            headers = next(csv.reader(f))
        normalized = [h.upper() for h in headers]
        assert len(set(normalized)) == len(normalized) == 38
        assert set(fields) <= set(normalized)
        old = prior.get(rel)
        if old:
            assert digest == old['sha256'], f'{year} 원본이 이전 점검 후 변경됐습니다.'
        inputs.append({'year': year, 'path': rel, 'sha256': digest, 'bytes': path.stat().st_size,
                       'encoding': 'utf-8-sig', 'columns': headers, 'prior_rows': old['rows'] if old else None,
                       'provider': '부산소방재난본부', 'source_url': 'https://bigdata-119.kr/goods/goodsInfo?goods_mng_sn=402',
                       'source_basis': '저장소 자료 출처와 사용자 제공 원본; 이번 실행에서 재다운로드하지 않음'})
    manifest = {'created_at': stamp, 'status': '입력 등재 완료·처리 전', 'inputs': inputs,
                'selected_columns': fields, 'reference_script_sha256': sha(REFERENCE), 'policy_script_sha256': sha(POLICY),
                'script_sha256': sha(Path(__file__)), 'output_directory': out.relative_to(ROOT).as_posix(),
                'missing_rule': '공백 제거 후 빈 문자열만 결측. NULL·0은 임의 결측 처리하지 않음.',
                'spatial_policy': '재난시도명이 부산광역시와 정확히 일치. 원문 동명 보존·행정동 배정 안 함.',
                'scope_policy': {'A': '부산 명시 및 선택17개 모두 기재', 'B': 'A 중 처리결과 정상',
                                 'C': 'B 중 분류명 업무운행·훈련출동·구급차소독 제외'},
                'duplicates': '신고접수번호 중복은 파일별 점검만 수행하며 삭제하지 않음. 사건 중복 여부와 다름.'}
    save_json(out / 'manifest.json', manifest)
    catalog = ROOT / 'docs/20-데이터카탈로그/로컬신고-전처리-입력.md'
    catalog.write_text('# 로컬 신고 원본과 전처리\n\n'
        '원본은 사용자 제공 파일이며 기존 팀원 원본 경로와 구분한다. 제공기관: 부산소방재난본부. '
        '출처: https://bigdata-119.kr/goods/goodsInfo?goods_mng_sn=402\n\n'
        f'이번 실행 명세: `{out.relative_to(ROOT).as_posix()}/manifest.json`\n\n'
        '| 연도 | 실제 원본 | SHA256 |\n|---|---|---|\n' + ''.join(
            f"| {x['year']} | {x['path']} | {x['sha256']} |\n" for x in inputs) +
        '\n2018~2019는 제외한다. 인구·상권 원본은 이번 신고 전처리의 대상이 아니다. '
        '좌표계·실제 발생위치·행정동 대응은 이 작업에서 확정하지 않는다.\n', encoding='utf-8')
    summary, missing_records, quality = [], [], []
    expected = {2020: (114236,100073,99661), 2021: (139189,113965,113037),
                2022: (158478,127241,126252), 2023: (149390,121311,120187), 2024: (143396,116822,115525)}
    for item in inputs:
        year = item['year']; path = ROOT / item['path']
        counts = Counter(); missing = Counter(); ids = set(); channels = Counter()
        cols = ['source_file','source_record_index'] + fields + ['year','month','hour','weekday','season']
        exclusion_cols = ['source_file','source_record_index','year','region_status','missing_columns']
        with ExitStack() as stack:
            handles = {s: stack.enter_context(gzip.open(out / f'{s}_{year}.csv.gz', 'wt', encoding='utf-8-sig', newline='', compresslevel=3)) for s in ['A','B','C']}
            excluded = stack.enter_context(gzip.open(out / f'제외기록_{year}.csv.gz', 'wt', encoding='utf-8-sig', newline='', compresslevel=3))
            for f in handles.values(): pd.DataFrame(columns=cols).to_csv(f, index=False)
            pd.DataFrame(columns=exclusion_cols).to_csv(excluded, index=False)
            for df in pd.read_csv(path, dtype=str, keep_default_na=False, encoding=item['encoding'], chunksize=100000):
                df.columns = df.columns.str.upper()
                n = len(df); start = counts['원본']
                df['source_file'] = item['path']; df['source_record_index'] = range(start + 1, start + n + 1)
                blank = df[fields].apply(lambda s: s.str.strip().eq(''))
                busan = df['CLMTY_CTPV_NM'].eq('부산광역시')
                a = busan & ~blank.any(axis=1)
                b = a & df['PRCS_RSLT_SE_NM'].eq('정상')
                c = b & ~df['EMRG_RSCU_CLSF_NM'].isin(ref['OPERATIONS'])
                counts.update({'원본':n, '부산명시':int(busan.sum()), 'A':int(a.sum()), 'B':int(b.sum()), 'C':int(c.sum()),
                               '부산_결측제외':int((busan & ~a).sum()), '부산미명시':int((~busan).sum())})
                dates = pd.to_datetime(df['DCLR_DT'].str.strip(), format='%Y%m%d%H%M%S', errors='coerce')
                counts['날짜이상'] += int(dates.isna().sum())
                counts['연도불일치'] += int((dates.notna() & dates.dt.year.ne(year)).sum())
                # 날짜를 추정하거나 잘못된 날짜 행을 임의로 삭제하지 않는다.
                assert dates.notna().all() and dates.dt.year.eq(year).all(), f'{year}: 날짜 검증 실패'
                df['year'] = dates.dt.year; df['month'] = dates.dt.month; df['hour'] = dates.dt.hour
                df['weekday'] = dates.dt.dayofweek.map(dict(enumerate(ref['WEEK'])))
                df['season'] = dates.dt.month.map(ref['SEASON'])
                valid_ids = df.loc[~blank['DCLR_RCPT_NO'], 'DCLR_RCPT_NO']
                current = set(valid_ids)
                counts['접수번호중복_추가행'] += len(valid_ids) - len(current - ids)
                ids.update(current)
                for col in fields: missing[col] += int(blank[col].sum())
                for scope, mask in [('A',a),('B',b),('C',c)]:
                    assert not blank.loc[mask].any().any()
                    df.loc[mask, cols].to_csv(handles[scope], index=False, header=False)
                    channels.update({(scope,k):int(v) for k,v in df.loc[mask,'RCPT_PATH_NM'].value_counts().items()})
                missnames = pd.Series('', index=df.index)
                for col in fields: missnames += blank[col].map({True:col+'|',False:''})
                df['missing_columns'] = missnames.str.rstrip('|')
                df['region_status'] = 'other_province'
                df.loc[blank['CLMTY_CTPV_NM'],'region_status'] = 'province_missing'
                df.loc[busan,'region_status'] = 'busan_explicit'
                df.loc[~a,exclusion_cols].to_csv(excluded,index=False,header=False)
                for prefix in ['ACDNT_OCRN','DAMG_RGN']:
                    lon = pd.to_numeric(df.loc[a,prefix+'_LOT'],errors='coerce')
                    lat = pd.to_numeric(df.loc[a,prefix+'_LAT'],errors='coerce')
                    bad = lon.isna() | lat.isna()
                    counts[prefix+'_숫자변환불가'] += int(bad.sum())
                    counts[prefix+'_0포함'] += int((lon.eq(0)|lat.eq(0)).sum())
                    counts[prefix+'_도단위범위밖'] += int((~bad & ~(lon.between(-180,180)&lat.between(-90,90))).sum())
        assert counts['원본'] == counts['A'] + counts['부산_결측제외'] + counts['부산미명시']
        assert counts['A'] >= counts['B'] >= counts['C']
        if item['prior_rows'] is not None: assert counts['원본'] == item['prior_rows']
        assert sha(path) == item['sha256'], '실행 중 원본 변경'
        row = {'연도':year, **counts, '기존보고서_ABC일치':tuple(counts[s] for s in ['A','B','C']) == expected[year]}
        summary.append(row)
        missing_records.extend({'연도':year,'컬럼':k,'빈칸수':v} for k,v in missing.items())
        quality.extend({'연도':year,'조건':s,'접수경로':k,'건수':v} for (s,k),v in channels.items())
        print(json.dumps(row, ensure_ascii=False), flush=True)
    for name, rows in [('연도별요약',summary),('선택컬럼결측',missing_records),('접수경로분포',quality)]:
        pd.DataFrame(rows).to_csv(out / f'{name}.csv', index=False, encoding='utf-8-sig')
    # 저장된 CSV를 다시 읽어 파일별 행 수와 포함조건을 검증한다.
    for row in summary:
        for scope in ['A','B','C']:
            actual = 0
            for df in pd.read_csv(out / f"{scope}_{row['연도']}.csv.gz",dtype=str,keep_default_na=False,chunksize=100000):
                assert df['CLMTY_CTPV_NM'].eq('부산광역시').all()
                assert not df[fields].apply(lambda s:s.str.strip().eq('')).any().any()
                if scope in ['B','C']: assert df['PRCS_RSLT_SE_NM'].eq('정상').all()
                if scope == 'C': assert not df['EMRG_RSCU_CLSF_NM'].isin(ref['OPERATIONS']).any()
                actual += len(df)
            assert actual == row[scope]
    manifest.update(status='완료·출력 재독검증 통과', year_counts=summary,
                    outputs=[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(out.iterdir()) if p.name!='manifest.json'])
    save_json(out/'manifest.json',manifest)
    lines = ['# 로컬 신고 전처리 결과\n',f'출력: `{out.relative_to(ROOT).as_posix()}`\n',
             '부산 명시·선택17개 공란 제외 기준을 원본에 직접 적용했다. 헤더 대소문자만 통일하며 값은 보존했다.\n',
             '| 연도 | 원본 | A | B | C | 기존 보고서 A/B/C 일치 |','|---|---:|---:|---:|---:|---|']
    for r in summary: lines.append(f"| {r['연도']} | {r['원본']:,} | {r['A']:,} | {r['B']:,} | {r['C']:,} | {r['기존보고서_ABC일치']} |")
    lines += ['\nA/B/C는 연도별 CSV.GZ로 저장했다. 압축 해제하거나 pandas.read_csv로 바로 읽는다.',
              '\n원본 해시 유지·행 수 대사·일시 유효성·선택17개 공란 0·B/C 포함조건·출력 재독검증을 확인했다.',
              '\n좌표 0·숫자 변환 불가·도 단위 범위 이상은 별도 집계만 하며 임의 제거하지 않았다. 세계 경위도 범위 검사는 좌표계 검증이 아니다.',
              '\n빈값 제거에 따른 접수경로·지역 선택 편향이 있으므로 부산 전체 위험도로 해석하지 않는다. 행정동 배정·인구 및 상권 결합은 수행하지 않았다.',
              '\n행별 제외 사유와 원본 행 번호는 출력 폴더에 보존했다. 접수번호·정밀좌표가 포함된 전처리 파일은 Git에 올리지 않는다.']
    (ROOT/'docs/20-데이터카탈로그/로컬신고-전처리-결과.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('완료:',out,flush=True)


if __name__ == '__main__':
    main()
