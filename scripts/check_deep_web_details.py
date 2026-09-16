"""Targeted checks for monthly charts, case subtypes and resident summary."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'web/final';OUT=ROOT/'data/processed/심층분석-20260915/browser_verification'

def main():
    deep=json.loads((SITE/'data/deep-data.json').read_text(encoding='utf-8'))
    base=json.loads((SITE/'data/dashboard.json').read_text(encoding='utf-8'))
    monthly=defaultdict(lambda:[0]*12);hours=defaultdict(lambda:[0]*6)
    for r,y,s,t,m,n in deep['month']:
        reg=deep['regions'][r]
        for yy in ['all',str(y)]:
            for tt in ['all',deep['meta']['types'][t]]:monthly[(yy,deep['meta']['scopes'][s],tt,reg['district'],reg['rawDong'])][m-1]+=n
    for c,y,s,w,h,n in deep['caseTime']:hours[(c,deep['meta']['scopes'][s])][h]+=n
    checks=[];cases=[];errors=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        p=b.new_page(viewport={'width':1600,'height':1100});p.on('pageerror',lambda e:errors.append(str(e)))
        p.goto((SITE/'index.html').as_uri());p.add_style_tag(content='html{scroll-behavior:auto!important}*{transition:none!important}')
        def values(selector):
            titles=p.locator(selector+' rect title').all_text_contents()
            return [int(re.search(r':\s*([\d,]+)건',t).group(1).replace(',','')) for t in titles]
        for yy in ['all','2020','2021','2022','2023','2024']:
            p.select_option('#year',yy)
            for s in ['A','B','C']:
                p.select_option('#scope',s)
                for t in ['all',*deep['meta']['types']]:
                    p.select_option('#type',t)
                    ds=p.locator('#local-metrics').evaluate('(e)=>({...e.dataset})')
                    key=tuple(ds[k] for k in ['year','scope','type','district','rawDong'])
                    v=values('#local-month');assert v==monthly[key],(key,v,monthly[key])
                    assert sum(v)==int(ds['total']);checks.append({'key':key,'count':sum(v)})
        for case in deep['cases']:
            p.select_option('#year','2024');p.select_option('#type','all');p.select_option('#district',case['district'])
            opts=p.locator('#raw-dong option').evaluate_all('es=>es.map(e=>({v:e.value,t:e.textContent}))')
            p.select_option('#raw-dong',next(o['v'] for o in opts if case['rawDong'] in o['t']))
            p.select_option('#type',case['type'])
            for s in ['A','B','C']:
                p.select_option('#scope',s)
                v=values(f'#case-hours-{case["index"]}');assert v==hours[(case['index'],s)]
                assert '2020–2024' in p.locator('.case-time-insight').inner_text()
                cases.append({'case':case['id'],'globalYear':'2024','caseYears':'2020–2024','scope':s,'count':sum(v)})
        # All years view remains a single 2024 resident background, never 5-year summed population.
        p.select_option('#type','all');p.select_option('#district','기장군');p.select_option('#year','all')
        opts=p.locator('#raw-dong option').evaluate_all('es=>es.map(e=>({v:e.value,t:e.textContent}))')
        p.select_option('#raw-dong',next(o['v'] for o in opts if '기장읍' in o['t']))
        if p.locator('#local-population-summary').count():
            text=p.locator('#local-population-summary').inner_text()
            assert '51,101' in text and '2024' in text,text
            assert '13,189' in text,text
        p.locator('#population-search').fill('ZZZZ_NONE');assert p.locator('#age-chart').inner_text()
        assert p.locator('#age-detail tbody tr').count()==0
        p.locator('#population-search').fill('')
        assert not errors,errors
        b.close()
    result={'status':'passed','monthly_filter_checks':checks,'case_subtype_hour_checks':cases,'page_errors':errors,'site_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.rglob('*') if p.is_file()}}
    (OUT/'details_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS {len(checks)} monthly filters x12 months; {len(cases)} subtype cases x6 hours')

if __name__=='__main__':main()
