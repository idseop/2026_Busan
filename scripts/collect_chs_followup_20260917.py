"""Collect public CHS 2024 attachments through their published browser links."""
from pathlib import Path
import hashlib, json, zipfile, argparse
from datetime import datetime, timezone
from lxml import html
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/신고보건심화-20260917/sources'
OUT.mkdir(parents=True, exist_ok=True)
LANDING = 'https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do'
records = []
parser=argparse.ArgumentParser()
parser.add_argument('--year', type=int, default=2024)
parser.add_argument('--districts', nargs='+', default=['사하구','북구'])
args=parser.parse_args()
year=args.year
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
    page = browser.new_page(accept_downloads=True)
    page.goto(LANDING, timeout=60000, wait_until='load')
    page.wait_for_timeout(2000)
    body = page.evaluate("async a => (await fetch(a.url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'year='+a.year+'&ctprvn=26'})).text()", {'url':LANDING,'year':year})
    (OUT/f'chs-{year}-busan-public.html').write_text(body, encoding='utf-8')
    tree=html.fromstring(body)
    if not tree.xpath('//a[@downloadname]'):
        for checkbox in tree.xpath('//input[@name="snCheck"]'):
            gu=next((g for g in args.districts if checkbox.get('title','').startswith(g+'보건소')),None)
            if not gu: continue
            file_id=checkbox.get('value')
            rec=dict(district=gu,survey_year=year,landing=LANDING,public_file_id=file_id,retrieved_at=datetime.now(timezone.utc).isoformat(),extracted=[])
            target=OUT/f'chs{year}-{gu}.pdf'
            try:
                archive_path=OUT/f'chs{year}-{gu}.zip'
                if archive_path.exists():
                    target=archive_path
                elif not target.exists():
                    with page.expect_download(timeout=60000) as download:
                        page.evaluate('id=>absFile.fileProcess.fileDownLoad(id)',file_id)
                    download.value.save_as(target)
                if zipfile.is_zipfile(target):
                    if target!=archive_path:
                        target.rename(archive_path);target=archive_path
                    with zipfile.ZipFile(target) as archive:
                        assert archive.testzip() is None
                        for member in archive.namelist():
                            ext=Path(member).suffix.lower()
                            if ext not in ['.xlsx','.pdf']:continue
                            dest=OUT/f'chs{year}-{gu}{ext}'
                            dest.write_bytes(archive.read(member))
                            rec['extracted'].append(dict(member=member,file=str(dest.relative_to(ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
                else:
                    assert target.read_bytes()[:5]==b'%PDF-', 'Older attachment is neither PDF nor ZIP'
                rec.update(status='downloaded',file=str(target.relative_to(ROOT)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size)
            except Exception as exc:
                rec.update(status='failed',error=str(exc))
            records.append(rec)
            (OUT/f'chs{year}-download-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
            print(gu,rec['status'],rec.get('bytes'),flush=True)
    for a in tree.xpath('//a[@downloadname]'):
        name = a.get('downloadname')
        gu = next((g for g in args.districts if f'부산 {g}' in name or f'_{g}_' in name or f'_{g}.' in name), None)
        if not gu:
            continue
        assert str(year) in name
        target = OUT/f'chs{year}-{gu}.zip'
        rec = dict(district=gu, survey_year=year, name=name, url=a.get('href'), landing=LANDING, retrieved_at=datetime.now(timezone.utc).isoformat(), extracted=[])
        try:
            if not target.exists() or not zipfile.is_zipfile(target):
                with page.expect_download(timeout=60000) as download:
                    page.evaluate('u=>{const a=document.createElement("a");a.href=u;document.body.appendChild(a);a.click()}', a.get('href'))
                download.value.save_as(target)
            assert zipfile.is_zipfile(target), 'Response is not a ZIP attachment'
            rec.update(file=str(target.relative_to(ROOT)), bytes=target.stat().st_size, sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            with zipfile.ZipFile(target) as archive:
                assert archive.testzip() is None
                for name_in_zip in archive.namelist():
                    ext = Path(name_in_zip).suffix.lower()
                    if ext not in ['.xlsx','.pdf']:
                        continue
                    dest = OUT/f'chs{year}-{gu}{ext}'
                    dest.write_bytes(archive.read(name_in_zip))
                    rec['extracted'].append(dict(member=name_in_zip,file=str(dest.relative_to(ROOT)),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
            rec['status']='downloaded'
        except Exception as exc:
            rec['status']='failed';rec['error']=str(exc)
        records.append(rec)
        (OUT/f'chs{year}-download-manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        print(gu, rec['status'], rec.get('bytes'), flush=True)
    browser.close()
assert {r['district'] for r in records if r['status']=='downloaded'} == set(args.districts)
