"""Review the CSS-only release delta and archive chain without repeating data analysis."""
from pathlib import Path
import hashlib,json,zipfile
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'web/final'
OUT=ROOT/'data/processed/최종결과-20260915'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    prior_path=OUT/'browser_verification/result.json'
    visual_path=OUT/'browser_verification/final_visual_review.json'
    prior=json.loads(prior_path.read_text(encoding='utf-8'))
    visual=json.loads(visual_path.read_text(encoding='utf-8'))
    checks=[]
    def check(name,ok,detail=None):
        checks.append({'check':name,'passed':bool(ok),'detail':detail});assert ok,name
    check('prior_functional_evidence_passed',prior['status']=='passed')
    check('final_visual_evidence_passed',visual['status']=='passed')
    check('functional_to_visual_hash_chain',sha(prior_path)==visual['prior_functional_evidence_sha256'])
    files={str(p.relative_to(ROOT)):sha(p) for p in SITE.rglob('*') if p.is_file()}
    check('visual_evidence_matches_current_site',files==visual['site_sha256'])
    changed=[name for name,digest in files.items() if prior['site_sha256'].get(name)!=digest]
    check('only_css_and_readme_changed_since_functional_run',all(Path(name).name in {'style.css','README.md'} for name in changed),changed)
    check('javascript_and_data_unchanged',all(prior['site_sha256'].get(name)==digest for name,digest in files.items() if Path(name).suffix in {'.js','.json'}))
    archive=ROOT/visual['archive']
    check('archive_matches_final_visual_hash',sha(archive)==visual['archive_sha256'])
    with zipfile.ZipFile(archive) as z:
        check('archive_crc_passed',z.testzip() is None)
        names=z.namelist(); site_names={p.relative_to(SITE).as_posix() for p in SITE.rglob('*') if p.is_file()}
        check('archive_file_set_equals_public_site',set(names)==site_names and len(names)==len(site_names),names)
        check('archive_has_no_parent_or_absolute_paths',all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names))
        check('archive_content_hashes_equal_current_site',all(hashlib.sha256(z.read(n)).hexdigest()==sha(SITE/n) for n in names))
    layouts=[]; errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        page=browser.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto((SITE/'index.html').as_uri())
        for width in [360,390]:
            page.set_viewport_size({'width':width,'height':844})
            page.select_option('#scope','C')
            values=page.locator('.filterbar').evaluate('''e=>{
                const box=x=>{const b=x.getBoundingClientRect();return{x:b.x,y:b.y,width:b.width,height:b.height,bottom:b.bottom,display:getComputedStyle(x).display};};
                const selects=[...e.querySelectorAll('select')].map(x=>({id:x.id,...box(x)}));
                return{selects,context:box(e.querySelector('.filter-context')),overflow:document.documentElement.scrollWidth>innerWidth+1};
            }''')
            by_id={x['id']:x for x in values['selects']}
            check(f'mobile_{width}_no_horizontal_overflow',not values['overflow'])
            check(f'mobile_{width}_year_and_type_same_row',abs(by_id['year']['y']-by_id['type']['y'])<1)
            check(f'mobile_{width}_scope_own_full_row',by_id['scope']['y']>by_id['year']['bottom'] and by_id['scope']['width']>by_id['year']['width'])
            check(f'mobile_{width}_description_visible_on_following_row',values['context']['display']!='none' and values['context']['width']>0 and values['context']['y']>by_id['scope']['bottom'])
            layouts.append({'width':width,'scope':'C','measurements':values})
        check('css_delta_no_javascript_errors',not errors,errors)
        browser.close()
    report={'status':'passed','scope':'Final mobile CSS and packaging delta only; unchanged functional and data evidence reused.',
        'prior_independent_web_review':{'path':str((OUT/'independent_web_code_review.json').relative_to(ROOT)),'sha256':sha(OUT/'independent_web_code_review.json')},
        'functional_evidence':{'path':str(prior_path.relative_to(ROOT)),'sha256':sha(prior_path)},
        'final_visual_evidence':{'path':str(visual_path.relative_to(ROOT)),'sha256':sha(visual_path)},
        'checked_files':files,'changed_since_functional_check':changed,'archive':str(archive.relative_to(ROOT)),
        'archive_sha256':sha(archive),'layouts':layouts,'checks':checks,'checks_passed':len(checks),
        'resolved_finding':'Final mobile description row initially inherited display:none; display:block added and actual computed layout rechecked.',
        'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(__file__)}
    (OUT/'independent_final_release_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Final release delta checks passed:',len(checks));print('ZIP SHA256:',sha(archive))

if __name__=='__main__':main()
