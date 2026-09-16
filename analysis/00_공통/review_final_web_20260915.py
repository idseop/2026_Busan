"""Independent functional review of the final UI; no product-file mutations."""
from pathlib import Path
import hashlib,json,re
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
WEB=ROOT/'web/final'; OUT=ROOT/'data/processed/최종결과-20260915'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    data=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'))
    evidence=[]; errors=[]
    def check(name,condition,detail=None):
        evidence.append({'check':name,'passed':bool(condition),'detail':detail})
        assert condition,name
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        context=browser.new_context(viewport={'width':1440,'height':1000})
        context.set_offline(True)
        page=context.new_page(); page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((WEB/'index.html').as_uri()); page.wait_for_selector('#dashboard:not([hidden])')
        check('file_offline_initial_704689',page.locator('#metric-total').inner_text()=='704,689')
        check('reference_map_16_regions',page.locator('#district-map path.map-region').count()==16)
        check('reference_map_date_visible','2025-06-30' in page.locator('#map-source').inner_text())
        observed=[]
        for year in data['meta']['years']:
            page.select_option('#year',str(year))
            for scope in data['meta']['scopes']:
                page.select_option('#scope',scope)
                for typ in data['meta']['types']:
                    page.select_option('#type',typ)
                    expected=sum(r['count'] for r in data['yearly'] if r['year']==year and r['scope']==scope and r['type']==typ)
                    actual=int(page.locator('#metric-total').inner_text().replace(',',''))
                    check(f'filter_{year}_{scope}_{typ}',actual==expected)
                    observed.append(actual)
        page.select_option('#year','all'); page.select_option('#scope','A'); page.select_option('#type','all')
        page.locator('[data-dimension="season"]').click()
        check('time_active_class_tracks_click',page.locator('[data-dimension="season"]').get_attribute('class')=='selected' and page.locator('[data-dimension="month"]').get_attribute('class')!='selected')
        page.locator('#daily-rate').check()
        titles=page.locator('#time-chart rect title').all_text_contents()
        for season in ['봄','여름','가을','겨울']:
            rows=[r for r in data['time'] if r['scope']=='A' and r['dimension']=='season' and r['value']==season]
            days={r['year']:r['calendarDays'] for r in rows}; expected=sum(r['count'] for r in rows)/sum(days.values())
            title=next(x for x in titles if x.startswith(season+':'))
            actual=float(re.search(r': ([\d,.]+)',title).group(1).replace(',',''))
            check(f'calendar_days_deduplicated_across_types_{season}',abs(actual-expected)<=.051)
        time_before=page.locator('#time-chart').inner_html()
        page.select_option('#district','기장군'); page.fill('#region-search','일광면')
        check('raw_region_does_not_filter_city_time',page.locator('#time-chart').inner_html()==time_before)
        check('no_2023_code_fallback_to_2024',page.locator('#region-detail [data-pop]').count()==0)
        check('population_single_year_when_all_receipt_years','2024년' in page.locator('#population-context').inner_text())
        original_pop=page.locator('#population-stats').inner_text()
        page.select_option('#scope','C'); page.select_option('#type','화재')
        check('population_unchanged_by_receipt_scope_type',page.locator('#population-stats').inner_text()==original_pop)
        page.fill('#population-search','검색결과가없어야함_xyz')
        check('empty_population_search_clears_101_age_rows',page.locator('#age-detail tbody tr').count()==0)
        page.fill('#population-search',''); page.locator('[data-age-mode="count"]').click()
        check('age_active_class_tracks_click',page.locator('[data-age-mode="count"]').get_attribute('class')=='selected')
        check('all_101_ages_visible',page.locator('#age-detail tbody tr').count()==101)
        page.select_option('#district','all'); page.select_option('#type','all'); page.fill('#region-search','')
        for threshold in [1,5,10,20]:
            page.select_option('#candidate-min',str(threshold))
            expected=sum(c['minAnnualCount']>=threshold for c in data['candidates'])
            actual=int(re.search(r'([\d,]+)개 관측',page.locator('#candidate-count').inner_text()).group(1).replace(',',''))
            check(f'exploration_threshold_{threshold}',actual==expected)
        check('candidates_not_policy_threshold','정책 후보 통과선이 아닙니다' in page.locator('#candidate-controls').inner_text())
        check('official_services_readable_no_raw_json',page.locator('.response-evidence .candidate').count()==3 and page.locator('.response-evidence pre').count()==0)
        check('percent_not_duplicated','%%' not in page.locator('.metrics').inner_text())
        check('live_page_no_javascript_errors',not errors,errors)
        # These mutations exist only in fresh browser contexts, never in delivered files.
        bad=context.new_page()
        bad.add_init_script("Object.defineProperty(window,'BUSAN_DATA',{configurable:true,set(v){this.__bad={yearly:[],population:[]};},get(){return this.__bad;}});")
        bad.goto((WEB/'index.html').as_uri())
        check('malformed_dataset_shows_load_error',bad.locator('#load-error').is_visible() and bad.locator('#dashboard').is_hidden())
        fallback=context.new_page()
        fallback.add_init_script("Object.defineProperty(window,'BUSAN_MAP',{configurable:true,set(v){},get(){return undefined;}});")
        fallback.goto((WEB/'index.html').as_uri()); fallback.wait_for_selector('#dashboard:not([hidden])')
        check('missing_map_falls_back_to_16_district_buttons',fallback.locator('#district-map button[data-district]').count()==16)
        injected=context.new_page()
        injected.add_init_script("Object.defineProperty(window,'BUSAN_DATA',{configurable:true,set(v){v.candidates[0].receiptEvidence='<img id=review-injected src=x onerror=window.__reviewXss=1>';this.__reviewData=v;},get(){return this.__reviewData;}});")
        injected.goto((WEB/'index.html').as_uri()); injected.wait_for_selector('#dashboard:not([hidden])')
        check('candidate_text_html_escaped',injected.locator('#review-injected').count()==0 and injected.evaluate('window.__reviewXss') is None)
        check('injected_text_is_shown_as_text','<img id=review-injected' in injected.locator('#candidate-cards').inner_text())
        links=page.locator('a[href]').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))')
        check('no_javascript_or_data_source_links',not any(x.lower().startswith(('javascript:','data:')) for x in links))
        browser.close()
    forbidden={'DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT','source_record_index'}
    def bad_keys(v):
        if isinstance(v,dict): return set(v).intersection(forbidden)|set().union(*(bad_keys(x) for x in v.values()))
        if isinstance(v,list): return set().union(*(bad_keys(x) for x in v))
        return set()
    check('no_individual_receipt_or_coordinate_keys_in_public_payload',not bad_keys(data))
    files=[WEB/'index.html',WEB/'assets/app.js',WEB/'assets/style.css',WEB/'data/dashboard-data.js',WEB/'data/map-data.js']
    report={'status':'passed','reviewer_role':'Independent UI reviewer; UI authored by another agent.',
        'checks':evidence,'checks_passed':len(evidence),'javascript_errors':errors,
        'fixed_findings':['Cross-year population-code fallback removed','Empty population search removes stale 101-age table',
            'Duplicate percent removed','Required dataset schema guard added','Segmented active style follows actual state','Map metadata date rendered'],
        'limitations':'Local Chrome functional review; not a claim of support for every browser or arbitrary corrupted schema. References and input geography remain subject to the documented analysis limits.',
        'verified_files':[{'path':str(f.relative_to(ROOT)),'sha256':sha(f)} for f in files],
        'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(__file__)}
    (OUT/'independent_web_code_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Independent UI checks passed:',len(evidence))

if __name__=='__main__': main()
