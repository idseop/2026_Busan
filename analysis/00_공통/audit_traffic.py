"""Inspect complete official KoROAD downloads; preserve source rows for Busan."""
import csv
from collections import Counter
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
raw = root / 'data/raw/교통안전'
out = root / 'data/interim/교통안전'
out.mkdir(parents=True, exist_ok=True)
results = []
for item in json.loads((raw / 'manifest.json').read_text(encoding='utf-8')):
    path = root / item['file']
    with path.open(encoding='cp949', newline='') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        columns = reader.fieldnames
    busan = [r for r in rows if str(r['법정동코드']).startswith('26')]
    with (out / (item['id'] + '_부산원본행.csv')).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(busan)
    record = dict(id=item['id'], columns=columns, national_rows=len(rows), busan_rows=len(busan),
                  malformed_rows=sum(None in r or any(v is None for v in r.values()) for r in rows),
                  busan_missing={k: sum(not r[k].strip() for r in busan) for k in columns},
                  hash_matches=hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'],
                  busan_gu_codes=sorted({r['법정동코드'][:5] for r in busan}),
                  national_id_prefix_counts=dict(sorted(Counter(r['사고다발지id'][:4] for r in rows).items())),
                  busan_id_prefix_counts=dict(sorted(Counter(r['사고다발지id'][:4] for r in busan).items())),
                  busan_duplicate_fids=len(busan)-len({r['사고다발지fid'] for r in busan}),
                  busan_invalid_coordinates=sum(not (124 <= float(r['경도']) <= 132 and 33 <= float(r['위도']) <= 39) for r in busan),
                  busan_polygon_types=dict(Counter(json.loads(r['다발지역폴리곤'])['type'] for r in busan)))
    results.append(record)
(out / 'audit.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(results, ensure_ascii=False, indent=2))
