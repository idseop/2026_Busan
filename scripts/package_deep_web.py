"""Package the current verified website and capture final map-first screens."""
from pathlib import Path
import hashlib
import json
import zipfile
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'web/final';OUT=ROOT/'data/processed/심층분석-20260915/browser_verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    detail=json.loads((OUT/'details_result.json').read_text(encoding='utf-8'))
    base=json.loads((OUT/'result.json').read_text(encoding='utf-8'))
    assert detail['status']==base['status']=='passed'
    current={str(p.relative_to(ROOT)):sha(p) for p in SITE.rglob('*') if p.is_file()}
    assert current==detail['site_sha256'],'Website changed after final detail validation; verify the change first.'
    errors=[]
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True)
        p=b.new_page(viewport={'width':1600,'height':1100});p.on('pageerror',lambda e:errors.append(str(e)))
        p.goto((SITE/'index.html').as_uri());p.add_style_tag(content='html{scroll-behavior:auto!important}*{transition:none!important}')
        assert p.locator('#metric-total').inner_text()=='704,689'
        p.screenshot(path=str(OUT/'desktop-overview.png'))
        p.locator('#regions').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'desktop-map.png'))
        p.select_option('#district','기장군');p.select_option('#scope','C');p.select_option('#type','구급')
        opts=p.locator('#raw-dong option').evaluate_all('es=>es.map(e=>({value:e.value,text:e.textContent}))')
        p.select_option('#raw-dong',next(o['value'] for o in opts if '기장읍' in o['text']))
        p.locator('#regions').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'desktop-selected-map.png'))
        p.locator('#region-analysis').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'desktop-local.png'))
        p.locator('#local-cases').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'desktop-case.png'))
        p.screenshot(path=str(OUT/'desktop-full.png'),full_page=True)
        for width in [390,360]:
            p.set_viewport_size({'width':width,'height':844});p.locator('#map-reset').click()
            p.locator('#district-map').scroll_into_view_if_needed()
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            p.screenshot(path=str(OUT/f'mobile-map-{width}.png'))
            p.locator('#region-analysis').scroll_into_view_if_needed();p.screenshot(path=str(OUT/f'mobile-local-{width}.png'))
        assert not errors,errors;b.close()
    archive=ROOT/'output/부산119-지도심층분석-20260915.zip';archive.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SITE.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(SITE).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name in z.namelist():assert hashlib.sha256(z.read(name)).hexdigest()==sha(SITE/name)
        members=z.namelist()
    evidence={'status':'passed','site_sha256':current,'base_browser_result_sha256':sha(OUT/'result.json'),'detail_browser_result_sha256':sha(OUT/'details_result.json'),'archive':str(archive.relative_to(ROOT)),'archive_sha256':sha(archive),'archive_members':members,'archive_crc_and_each_member_sha256':True,'page_errors':errors,'screenshots':{p.name:sha(p) for p in OUT.glob('*.png')}}
    (OUT/'delivery.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'PASS: {len(members)} website files, verified archive {archive.name}')

if __name__=='__main__':main()
