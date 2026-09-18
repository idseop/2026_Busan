"""Verify current-only report completeness, figures, links and numeric tables."""
from pathlib import Path
import csv
import hashlib
import json
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'data/processed/최신작업-문서통합-20260918'
POOL = ROOT / 'data/processed/5개년통합-지역유형-제안연결-20260917'


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def part(text, number):
    match = re.search(rf'(?ms)^## {number}\. .*?(?=^<a id="s\d+"|\Z)', text)
    assert match, number
    return match.group()


def table_rows(text, first_header):
    start = text.index(first_header)
    lines = text[start:].splitlines()
    values = []
    for line in lines[2:]:
        if not line.startswith('|'):
            break
        values.append([cell.strip() for cell in line.strip('|').split('|')])
    return values


def main():
    manifest = json.loads((AUDIT/'manifest.json').read_text(encoding='utf-8'))
    report = ROOT / manifest['report']
    raw = report.read_bytes()
    text = raw.decode('utf-8')
    assert hashlib.sha256(raw).hexdigest() == manifest['reportSha256']
    assert hashlib.sha256((ROOT/manifest['plan']).read_bytes()).hexdigest() == manifest['planSha256']
    assert b'\r' not in raw, 'CRLF duplication would split Markdown tables'
    blocks = re.findall(r'(?:^\|[^\n]*\|\n?)+', text, re.M)
    for block in blocks:
        lines = block.splitlines()
        assert len(lines) >= 2 and re.fullmatch(r'\|[|: \-]+\|', lines[1]), 'Broken Markdown table: '+lines[0]
    for name, item in manifest['inputs'].items():
        path = ROOT/name
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], name

    headings = re.findall(r'^## (\d+)\. ', text, re.M)
    assert headings == [str(i) for i in range(1,24)]
    assert len(re.findall(r'<a id="s\d+"></a>',text)) == 23
    targets = re.findall(r'!?\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)',text)
    local_links = []
    for value in targets:
        value=value.strip('<>')
        if value.startswith(('https://','http://','mailto:')):
            continue
        if value.startswith('#'):
            assert f'id="{value[1:]}"' in text
            continue
        value=unquote(value.split('#')[0])
        path=(report.parent/value).resolve()
        assert path.exists(),value
        local_links.append(path)
    assert not any(any(x in p.parts for x in ['focus-bujeon-gwangan','evidence-review','priority-proposals','logic-review']) for p in local_links)
    assert not any(s in text for s in ['TODO','TBD','{main_table}','{pop_table}','48그림','48개 시각화'])

    gu=csv_rows(POOL/'01-16구군-5년합계와-한해제외순위.csv')
    city=table_rows(part(text,6),'| 건수순 | 구·군 | 5년 접수 |')
    assert len(city)==16
    for r,display in zip(gu,city):
        assert display[0]==r['pooledCountRank'] and display[1]==r['district']
        assert int(display[2].replace(',',''))==int(r['countP'])
    annual=table_rows(part(text,6),'| 연도 | A 전체처리 |')
    assert len(annual)==5
    for year,row in zip(range(2020,2025),annual):
        assert row[0]==str(year)
        assert int(row[4].replace(',',''))==sum(int(r[str(year)]) for r in gu)
    assert [sum(int(row[i].replace(',','')) for row in annual) for i in range(1,5)]==[704689,579412,574662,555786]

    types=csv_rows(POOL/'02-전체70유형-5년합계와-한해제외순위.csv')
    displayed=table_rows(part(text,21),'| 건수순 | 종별 |')
    assert len(displayed)==len(types)==70
    assert len({(x[1],x[2]) for x in displayed})==70
    for r,v in zip(types,displayed):
        assert (v[1],v[2])==(r['type'],r['subtype'])
        assert int(v[3].replace(',',''))==int(r['countP'])
        assert v[4]==f"{float(r['citySharePct']):.3f}%"
    assert sum(int(x[3].replace(',','')) for x in displayed)==555786

    focus=csv_rows(POOL/'07-상위5구군-유형별동비교.csv')
    displayed=table_rows(part(text,22),'| 구군 | 접수 동명 | 유형 |')
    assert len(displayed)==45 and len({tuple(x[:3]) for x in displayed})==45
    for r,v in zip(focus,displayed):
        assert tuple(v[:3])==(r['district'],r['rawDong'],r['subtype'])
        assert int(v[3].replace(',',''))==int(r['countP'])
        assert v[4]==f"{float(r['shareRegionPct']):.2f}%"
        assert v[5]==r['withinDistrict_pooledCountRank']
        assert v[6]==f"{r['aboveRestBusan30']}/30 · {r['aboveRestDistrict30']}/30"
        starts=[int(x)*4 for x in r['hour4Peak'].split('|')]
        assert v[7]=='/'.join(f'{h:02d}~{h+4:02d}' for h in starts)
        assert v[8]==f"{float(r['night20to07Pct']):.2f}%"

    fields=table_rows(part(text,3),'| 컬럼 | 의미 | 사용 목적 |')
    assert len(fields)==17 and fields[0][0]=='DCLR_RCPT_NO' and fields[-1][0]=='PLCSCN_CNTR_NM'
    figure_table=table_rows(part(text,17),'| 역할 | 보여주는 결과 | 파일 |')
    assert len(figure_table)==9 and len(manifest['figures'])==9
    images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
    allowed={(ROOT/p).resolve() for p in manifest['figures']}
    assert all((report.parent/p.strip('<>')).resolve() in allowed for p in images)
    inventory=table_rows(part(text,20),'| 집계표 | 행 | 열 |')
    assert len(inventory)==manifest['csvTables']==72
    for row in inventory:
        match=re.search(r'\]\(<([^>]+)>\)',row[0])
        assert match
        records=csv_rows((report.parent/match.group(1)).resolve())
        assert int(row[1].replace(',',''))==len(records)
        assert int(row[2])==(len(records[0]) if records else 0)

    assert '2025년 신고는 제외한다' in part(text,1)
    assert '최신 웹 반영 완료' in part(text,16) and '247ad91' in part(text,16) and 'cfbdbe7' in part(text,16)
    assert '현재 시범' not in part(text,13) or '조건' in part(text,13)
    assert manifest['webUpdated'] is True and manifest['sourceFilesDeleted'] is False
    for name in ['write_current_project_report_20260918.py','verify_current_project_report_20260918.py']:
        p=ROOT/'scripts'/name
        compile(p.read_text(encoding='utf-8'),str(p),'exec')
    result={'status':'PASS','sections':23,'sourceHashesVerified':len(manifest['inputs']),
            'localLinksVerified':len(local_links),'guRowsMatched':16,'annualRowsMatched':5,
            'subtypeRowsMatched':70,'focusRowsMatched':45,'selectedColumns':17,
            'activeFigureCount':9,'csvInventoryRowsMatched':72,
            'currentOnlyScope':True,'markdownTablesContinuous':True,
            'reportSha256':manifest['reportSha256'],'planSha256':manifest['planSha256'],
            'scope':'Document, source hashes, numeric tables and local links; no new source analysis or browser test'}
    (AUDIT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
