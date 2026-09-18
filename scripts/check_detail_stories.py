"""Independently reconcile story time summaries with public region totals."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web/final'
OUT=ROOT/'data/processed/지도탐색웹-20260915/service-stories'

def main():
    data=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'))
    expected={}
    for row in data['rawRegions']:
        for year in ['all',str(row['year'])]:
            for kind,name in [('district',row['district']),('raw',row['rawDong'])]:
                for typ,count in [('all',row['total']),*row['typeCounts'].items()]:
                    key=(kind,row['district'],name,year,row['scope'],typ)
                    expected[key]=expected.get(key,0)+count
    checks=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        page=browser.new_page()
        page.goto((WEB/'index.html').as_uri())
        if not page.evaluate('typeof window.BUSAN_DETAIL_MODEL === "function"'):
            page.add_script_tag(path=str(WEB/'assets/detail-extension.js'))
        selections=[{'kind':'district','district':d} for d in sorted({r['district'] for r in data['rawRegions']})]
        selections += [{'kind':'raw','district':d,'rawDong':r} for d,r in [('기장군','기장읍'),('기장군','정관읍'),('연제구','연산동'),('북구','금곡동')]]
        configs=[{'selection':s,'year':y,'scope':sc,'type':t} for s in selections for y in ['all',*map(str,range(2020,2025))] for sc in ['A','B','C'] for t in ['all',*data['meta']['types']]]
        actual=page.evaluate('''configs=>configs.map(c=>{const m=BUSAN_DETAIL_MODEL({...c,data:BUSAN_DATA,deep:BUSAN_DEEP,services:BUSAN_CASE_SERVICES});return {total:m.total,hours:m.timing.hours.reduce((a,b)=>a+b,0),weekdays:m.timing.weekdays.reduce((a,b)=>a+b,0),months:m.timing.months.reduce((a,b)=>a+b,0),cases:m.cases.map(x=>({type:x.type,district:x.district,rawDong:x.rawDong}))}})''',configs)
        for c,a in zip(configs,actual):
            s=c['selection'];key=(s['kind'],s['district'],s.get('rawDong',s['district']),c['year'],c['scope'],c['type'])
            wanted=expected.get(key,0)
            assert all(a[k]==wanted for k in ['total','hours','weekdays','months']),(c,a,wanted)
            assert all(x['district']==s['district'] and (s['kind']=='district' or x['rawDong']==s['rawDong']) and (c['type']=='all' or c['type']==x['type']) for x in a['cases'])
            checks.append({'selection':s,'year':c['year'],'scope':c['scope'],'type':c['type'],'count':wanted})
        browser.close()
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'model-validation.json').write_text(json.dumps({'status':'passed','checks':checks,'method':'Story total, month, weekday and hour marginals reconciled independently against frozen rawRegions counts; case locality/type checked.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(checks)} story summaries reconciled with region totals')
if __name__=='__main__':main()
