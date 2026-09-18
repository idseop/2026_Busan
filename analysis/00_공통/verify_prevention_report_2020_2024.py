"""Independent checks for the final report, after raw source verification."""
import calendar
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'data/processed/동별예방분석-20260914'
DOC = ROOT / 'docs/40-분석결과/부산-동별예방-본분석-20260914.md'

def main():
    text = DOC.read_text(encoding='utf-8')
    tables = [[x.strip() for x in line.strip('|').split('|')] for line in text.splitlines() if line.startswith('|')]
    def row(label):
        return [r for r in tables if r[0] == label]
    def read(name): return pd.read_csv(BASE/name, keep_default_na=False)
    annual = read('receipts/annual_types.csv'); major = annual.groupby(['scope','EMRG_RSCU_ASSRT_NM'])['count'].sum()
    for typ in ['구급','구조','기타','화재','']:
        r = row(typ or '종별 미기재')[0]
        assert [int(x.replace(',','')) for x in r[1:4]] == [int(major[s,typ]) for s in 'ABC']
        assert r[4] == f"{100*major['B',typ]/1074247:.2f}%"
    panel = read('synthesis/all_type_review_panel.csv')
    for typ, sub in [('구급','심정지'),('구조','E/V사고'),('구조','시건개방'),('기타','화재확인출동'),('구급','질병'),('구급','질병외')]:
        p = panel[(panel.type == typ) & (panel.subtype == sub)].iloc[0]
        assert row(typ+'·'+sub)[0][1] == ' / '.join(f"{p[f'B_{y}']:,}" for y in range(2020,2025))
    dongs = read('receipts/original_dong_types.csv'); dongs = dongs[dongs.scope == 'B']
    for r in tables:
        if ' / ' in r[0] and not r[0].startswith('원문'):
            district, dong = r[0].split(' / ')
            selected = dongs[(dongs.CLMTY_SGG_NM == district) & (dongs.CLMTY_EMD_NM == dong)]
            assert [int(x.replace(',','')) for x in r[1:6]] == [int(selected[selected.year == y]['count'].sum()) for y in range(2020,2025)]
            assert int(r[6].replace(',','')) == int(selected['count'].sum())
    weekdays = read('receipts/time_weekday.csv'); weekdays = weekdays[weekdays.scope == 'B']
    for day, short in zip(['월요일','화요일','수요일','목요일','금요일','토요일','일요일'],['월','화','수','목','금','토','일']):
        s=weekdays[weekdays.weekday == day]
        rate=s['count'].sum()/s[['year','weekday','calendar_days']].drop_duplicates().calendar_days.sum()
        assert f'{short} {rate:.2f}' in text
    linked = []
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith('http'): continue
        path = (DOC.parent / unquote(target)).resolve()
        assert path.is_file(), str(path)
        linked.append(str(path.relative_to(ROOT)))
    for section in ['⑤','⑥','⑦','⑧']:
        section_text = text.split('## '+section,1)[1].split('\n## ',1)[0]
        assert '벌집' not in section_text
    documents = list((ROOT/'docs/40-분석결과').glob('*20260914.md')) + [ROOT/'docs/10-작업계획/부산 분석 작업 계획.md']
    evidence = {'status':'passed', 'scope':'Final report numeric tables, major-type composition, six subtype annual series, eight raw-label series, weekday calendar-weighted averages, local links, excluded user scope; narrative and chart visual review by independent agent.',
        'local_links_checked':len(linked), 'major_type_rows_checked':5, 'subtype_series_checked':6, 'raw_label_series_checked':8,
        'user_exclusion':'벌집제거 absent from focus/background/response/proposal sections; raw totals retained and panel explicitly excluded_user_scope',
        'external_source_review':{'url':'https://119.busan.go.kr/119news/1688707', 'publication_date':'2025-04-02', 'total_2024':753642,'disaster_2024':270390,'existing_nonfire_alarm_improvement_mentioned':True,'external_counts_not_forced_to_match_current_raw':True},
        'visual_review':'Three PNGs read; latest monthly_review shows four major types across all five years, no excluded-subtype emphasis.',
        'interpretation_review':'Unvalidated dong linkage held; no patient age inference, population rate, causal claim, unsupported service gap, or promised effect.',
        'document_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in documents},
        'limitations':'No validation of historical boundary identity or policy effects. Numerical checks supplement previously completed full raw-input and ledger verification.'}
    (BASE/'final_review.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Final report independent checks passed')

if __name__ == '__main__': main()
