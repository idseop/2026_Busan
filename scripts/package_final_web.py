"""Refresh final visual evidence and package only the verified public website."""
from pathlib import Path
import hashlib
import json
import zipfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'web/final'
OUT = ROOT / 'data/processed/최종결과-20260915/browser_verification'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    previous = json.loads((OUT / 'result.json').read_text(encoding='utf-8'))
    assert previous['status'] == 'passed'
    current = {str(p.relative_to(ROOT)): sha(p) for p in SITE.rglob('*') if p.is_file()}
    changed = [p for p, value in current.items() if previous['site_sha256'].get(p) != value]
    assert all(Path(p).name in {'style.css', 'README.md'} for p in changed), changed
    errors = []
    layouts = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        page = browser.new_page(viewport={'width':1600, 'height':1100}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto((SITE / 'index.html').as_uri(), wait_until='load')
        assert page.locator('#metric-total').inner_text() == '704,689'
        page.screenshot(path=str(OUT / 'desktop-overview.png'))
        page.screenshot(path=str(OUT / 'desktop-full.png'), full_page=True)
        page.locator('#regions').scroll_into_view_if_needed()
        page.screenshot(path=str(OUT / 'desktop-regions.png'))
        for width in (360, 390):
            page.set_viewport_size({'width':width, 'height':844})
            page.evaluate('window.scrollTo(0,0)')
            page.wait_for_timeout(400)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            sizes = page.locator('.filterbar select').evaluate_all('els => els.map(e => ({id:e.id,width:e.clientWidth,text:e.selectedOptions[0].textContent}))')
            layouts.append({'width':width,'selects':sizes,'horizontalOverflow':False})
            page.screenshot(path=str(OUT / f'mobile-{width}.png'))
            if width == 390:
                page.screenshot(path=str(OUT / 'mobile-overview.png'))
                page.screenshot(path=str(OUT / 'mobile-full.png'), full_page=True)
        assert not errors, errors
        browser.close()
    delivery = ROOT / 'output'
    delivery.mkdir(exist_ok=True)
    archive = delivery / '부산119-최종웹-20260915.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SITE.rglob('*')):
            if p.is_file():
                z.write(p, p.relative_to(SITE).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert 'index.html' in z.namelist()
        for name in z.namelist():
            assert hashlib.sha256(z.read(name)).hexdigest() == sha(SITE / name)
    result = {'status':'passed','prior_functional_evidence_sha256':sha(OUT/'result.json'),
              'changed_since_functional_check':changed,'layouts':layouts,'page_errors':errors,
              'site_sha256':current,'archive':str(archive.relative_to(ROOT)),
              'archive_sha256':sha(archive),'archive_crc_and_content_hashes_passed':True}
    (OUT / 'final_visual_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'passed','layouts':layouts,'archive':str(archive)},ensure_ascii=False))

if __name__ == '__main__':
    main()
