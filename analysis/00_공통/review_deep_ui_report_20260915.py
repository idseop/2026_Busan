"""Independent new regional UI/report review; aggregate inputs only, no product edits."""
from pathlib import Path
import json, hashlib, calendar
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/심층분석-20260915'
WEB=ROOT/'web/final'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    d=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'))
    deep=json.loads((OUT/'deep-data.json').read_text(encoding='utf-8'))
    findings=json.loads((OUT/'case_findings.json').read_text(encoding='utf-8'))
    checks=[];errors=[]
    def check(name,ok,detail=None): checks.append(dict(check=name,passed=bool(ok),detail=detail))
    for c,f in zip(deep['cases'],findings):
        check(c['id']+'_report_counts',f['total']==sum(c['yearCounts']) and f['core8Total']==sum(c['core8YearCounts']))
        check(c['id']+'_report_time',sum(f['monthCounts'])==f['total'] and sum(f['weekdayCounts'])==f['total'])
        for month in range(1,13):
            days=sum(calendar.monthrange(y,month)[1] for y in deep['meta']['years'])
            check(c['id']+f'_month_{month}',abs(f['monthPerCalendarDay'][str(month)]-f['monthCounts'][month-1]/days)<1e-12)
        p=f['population2024']
        if p:
            original=next(x for x in d['population'] if x['year']==2024 and x['code']==p['code'])
            check(c['id']+'_population',p['total']==original['total'] and p['age65plus']==sum(original['ages'][65:]) and p['age0to14']==sum(original['ages'][:15]))
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000});page.context.set_offline(True)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((WEB/'index.html').as_uri());page.wait_for_selector('#local-metrics')
        for c in deep['cases']:
            page.locator(f'[data-case-id="{c["id"]}"]').click()
            check(c['id']+'_shortcut',page.locator('#raw-dong').input_value()==f'{c["district"]}|{c["rawDong"]}' and page.locator('#scope').input_value()=='C')
            for scope in ['A','B','C']:
                page.select_option('#scope',scope)
                for year in ['all',2020,2024]:
                    page.select_option('#year',str(year))
                    rows=[r for r in d['rawRegions'] if r['scope']==scope and r['district']==c['district'] and r['rawDong']==c['rawDong'] and (year=='all' or r['year']==year)]
                    total=sum(r['typeCounts'][c['type']] for r in rows)
                    cells=page.locator('#local-heatmap .heat-cell').evaluate_all('(els)=>els.map(e=>Number(e.dataset.count))')
                    metric=int(page.locator('#local-metrics').get_attribute('data-total'))
                    check(f'{c["id"]}_{scope}_{year}_heatmetric',sum(cells)==total==metric)
                    table=page.locator('.local-case tbody tr').first.locator('td').all_text_contents()
                    check(f'{c["id"]}_{scope}_{year}_case_scope', [int(x.replace(',','')) for x in table[1:]]==c['countsByScope'][scope]['yearCounts'])
                    symbols=page.locator('.map-symbol').evaluate_all('(els)=>els.map(e=>Number(e.dataset.count))')
                    global_total=sum(r['count'] for r in d['yearly'] if r['scope']==scope and r['type']==c['type'] and (year=='all' or r['year']==year))
                    check(f'{c["id"]}_{scope}_{year}_map',sum(symbols)==global_total and len(symbols)==16)
            page.select_option('#year','2024')
            if c['rawDong']!='연산동':
                page.locator('#region-detail details summary').click()
                page.locator('#region-detail [data-pop]').first.click()
                expected=next(x for x in c['populationLinks'] if x['year']==2024)['uniqueCode']
                check(c['id']+'_conditional_population',page.locator('#population-dong').input_value()==expected and '미확정' in page.locator('#population-link-note').inner_text())
        page.locator('#region-search').fill('존재하지않는지역XYZ')
        check('empty_region_hides_previous_analysis',page.locator('#region-analysis').is_hidden())
        page.locator('#population-search').fill('존재하지않는지역XYZ')
        check('empty_population_clears_detail',page.locator('#population-stats').inner_text()=='' and page.locator('#age-detail').inner_text()=='')
        check('no_browser_errors',not errors,errors)
        browser.close()
    fm=json.loads((OUT/'figure_manifest.json').read_text(encoding='utf-8'))
    check('figure_deep_input_hash',fm['inputSha256']==sha(OUT/'deep-data.json'))
    for item in fm['outputs']: check('figure_output_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
    paths=[WEB/'assets/app.js',WEB/'assets/style.css',WEB/'index.html',ROOT/'docs/40-분석결과/부산-119-지도와-심층사례-20260915.md',ROOT/'analysis/00_공통/report_deep_analysis_20260915.py',OUT/'deep-data.json',OUT/'case_findings.json']
    result={'passed':all(c['passed'] for c in checks),'checks':checks,'inputHashes':{str(p.relative_to(ROOT)):sha(p) for p in paths},'scope':'Independent aggregate arithmetic, offline browser regional/map/case/population filters, report calculation review. Official service facts use parent supplied evidence; no new external verification.'}
    (OUT/'independent_deep_ui_report_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))
if __name__=='__main__':main()
