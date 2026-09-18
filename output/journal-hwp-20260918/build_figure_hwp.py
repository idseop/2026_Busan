"""Build a figures-only native HWP/HWPX using an isolated Hancom instance.

Default: validate inputs and construct an intermediate HWPX package only.
Use --save only after the final figure set is ready; --qa-pdf renders an
internal PDF for visual inspection. Existing user documents are not opened.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree as E
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
TEMPLATE = ROOT / 'output/report-visual-edit-20260918/image-sample.hwpx'
BASE = '2026-BigData-논문형시각화'
NS = {k: 'http://www.hancom.co.kr/hwpml/2011/' + v for k, v in
      [('hp', 'paragraph'), ('hc', 'core'), ('hh', 'head')]}
NS.update(opf='http://www.idpf.org/2007/opf/',
          config='urn:oasis:names:tc:opendocument:xmlns:config:1.0')


def tag(prefix, name):
    return '{' + NS[prefix] + '}' + name


def hunit(mm):
    return round(mm / 25.4 * 7200)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xml(element):
    return E.tostring(element, encoding='UTF-8', xml_declaration=True,
                      standalone=True)


def inputs(expected):
    figures = sorted(p for p in (OUT / 'figures').glob('*.png')
                     if re.match(r'^\d{2}[-_]', p.name))
    assert len(figures) == expected, f'Expected {expected} final PNGs, found {len(figures)}'
    assert [int(p.name[:2]) for p in figures] == list(range(1, expected + 1)), \
        'Figure numbers must be unique and consecutive from 01.'
    return figures


def build_package(figures):
    with ZipFile(TEMPLATE) as z:
        files = {name: z.read(name) for name in z.namelist()}
    old = E.fromstring(files['Contents/section0.xml'])
    section = E.Element(old.tag, nsmap=old.nsmap)
    header = E.fromstring(files['Contents/header.xml'])
    manifest = E.fromstring(files['Contents/content.hpf'])
    base_pic = old.find('.//hp:pic', NS)
    secpr = deepcopy(old.find('.//hp:secPr', NS))
    column = deepcopy(old.find('.//hp:ctrl', NS))
    assert base_pic is not None and secpr is not None
    page = secpr.find('hp:pagePr', NS)
    page.set('width', str(hunit(210)))
    page.set('height', str(hunit(297)))
    margin = page.find('hp:margin', NS)
    for key in ['left', 'right', 'top', 'bottom']:
        margin.set(key, str(hunit(15)))
    for key in ['header', 'footer', 'gutter']:
        margin.set(key, '0')
    visibility = secpr.find('hp:visibility', NS)
    visibility.set('hideFirstHeader', '1')
    visibility.set('hideFirstFooter', '1')
    visibility.set('hideFirstPageNum', '1')
    paragraph = header.find('.//hh:paraPr[@id="0"]', NS)
    paragraph.find('hh:align', NS).set('horizontal', 'CENTER')
    paragraph.find('hh:lineSpacing', NS).set('value', '100')
    for item in paragraph.find('hh:margin', NS):
        item.set('value', '0')
    header.find('.//hh:charPr[@id="0"]', NS).set('height', '100')
    items = manifest.find('opf:manifest', NS)
    for item in list(items):
        if (item.get('href') or '').startswith('BinData/'):
            items.remove(item)
    for name in list(files):
        if name.startswith('BinData/') or name.startswith('Preview/'):
            del files[name]
    for item in manifest.find('opf:metadata', NS):
        if E.QName(item).localname != 'language':
            item.text = None

    layout = []
    for number, path in enumerate(figures, 1):
        with Image.open(path) as im:
            pxw, pxh = im.size
            dpi = im.info.get('dpi')
        scale = min(180 / pxw, 230 / pxh)
        width, height = hunit(pxw * scale), hunit(pxh * scale)
        pic = deepcopy(base_pic)
        pic.set('id', str(300000000 + number))
        pic.set('instid', str(400000000 + number))
        pic.set('zOrder', '0')
        for name in ['orgSz', 'curSz', 'sz']:
            size = pic.find('hp:' + name, NS)
            size.set('width', str(width))
            size.set('height', str(height))
        for key in ['x', 'y']:
            pic.find('hp:offset', NS).set(key, '0')
        rot = pic.find('hp:rotationInfo', NS)
        rot.set('centerX', str(width // 2))
        rot.set('centerY', str(height // 2))
        for mat in pic.find('hp:renderingInfo', NS):
            for key, value in dict(e1=1, e2=0, e3=0, e4=0, e5=1, e6=0).items():
                mat.set(key, str(value))
        for point, (x, y) in zip(pic.find('hp:imgRect', NS),
                                 [(0, 0), (width, 0), (width, height), (0, height)]):
            point.set('x', str(x))
            point.set('y', str(y))
        for name in ['imgClip', 'inMargin', 'outMargin']:
            for side in ['left', 'right', 'top', 'bottom']:
                pic.find('hp:' + name, NS).set(side, '0')
        pos = pic.find('hp:pos', NS)
        for key, value in dict(treatAsChar=0, affectLSpacing=0, flowWithText=0,
                               allowOverlap=0, holdAnchorAndSO=1,
                               vertRelTo='PAPER', horzRelTo='PAPER',
                               vertAlign='CENTER', horzAlign='CENTER',
                               vertOffset=0, horzOffset=0).items():
            pos.set(key, str(value))
        bid = f'figure{number:02d}'
        pic.find('hc:img', NS).set('binaryItemIDRef', bid)
        pic.find('hp:shapeComment', NS).text = ''
        files[f'BinData/{bid}.png'] = path.read_bytes()
        E.SubElement(items, tag('opf', 'item'), id=bid,
                     href=f'BinData/{bid}.png', **{'media-type': 'image/png', 'isEmbeded': '1'})
        p = E.SubElement(section, tag('hp', 'p'), id=str(500000000 + number),
                         paraPrIDRef='0', styleIDRef='0',
                         pageBreak='0' if number == 1 else '1', columnBreak='0', merged='0')
        run = E.SubElement(p, tag('hp', 'run'), charPrIDRef='0')
        if number == 1:
            run.append(secpr)
            run.append(column)
        run.append(pic)
        E.SubElement(run, tag('hp', 't'))
        layout.append(dict(page=number, figure=path.name, source_sha256=sha(path),
                           pixels=[pxw, pxh], dpi=dpi,
                           width_mm=round(width / 7200 * 25.4, 3),
                           height_mm=round(height / 7200 * 25.4, 3),
                           position='page centered; preserve aspect ratio'))

    settings = E.fromstring(files['settings.xml'])
    for old_setting in settings.findall('config:config-item-set', NS):
        settings.remove(old_setting)
    print_info = E.SubElement(settings, tag('config', 'config-item-set'), name='PrintInfo')
    for name, typ, value in [('PrintAutoFootNote', 'boolean', 'false'),
                             ('PrintAutoHeadNote', 'boolean', 'false'),
                             ('PrintMethod', 'short', '0'), ('ZoomX', 'short', '100'),
                             ('ZoomY', 'short', '100')]:
        E.SubElement(print_info, tag('config', 'config-item'), name=name, type=typ).text = value
    files['Contents/section0.xml'] = xml(section)
    files['Contents/header.xml'] = xml(header)
    files['Contents/content.hpf'] = xml(manifest)
    files['settings.xml'] = xml(settings)
    files['Preview/PrvText.txt'] = b''
    package = OUT / 'figure-pages-intermediate.hwpx'
    with ZipFile(package, 'w', compression=ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data, compress_type=ZIP_STORED if name == 'mimetype' else ZIP_DEFLATED)
    (OUT / 'layout-plan.json').write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding='utf-8')
    return package, layout


def package_check(path, expected):
    with ZipFile(path) as z:
        root = E.fromstring(z.read('Contents/section0.xml'))
        check = dict(pictures=len(root.findall('.//hp:pic', NS)),
                     image_files=len([n for n in z.namelist() if n.startswith('BinData/')]),
                     visible_text=''.join(root.xpath('.//hp:t/text()', namespaces=NS)),
                     headers=len(root.findall('.//hp:header', NS)),
                     footers=len(root.findall('.//hp:footer', NS)),
                     page_numbers=len(root.findall('.//hp:pageNum', NS)))
    assert check['pictures'] == expected and check['image_files'] == expected, check
    assert not check['visible_text'].strip() and not any(check[k] for k in ['headers', 'footers', 'page_numbers']), check
    return check


def native_save(package, expected, qa_pdf):
    import win32com.client
    import win32process
    targets = {fmt: ROOT / (BASE + '.' + fmt.lower()) for fmt in ['HWP', 'HWPX']}
    assert not any(p.exists() for p in targets.values()), 'A final named output already exists; preserve it and resolve explicitly.'
    old = {int(s) for s in subprocess.run(
        ['powershell', '-NoProfile', '-Command', '(Get-Process hwp -ErrorAction SilentlyContinue).Id'],
        capture_output=True, text=True).stdout.split()}
    h = win32com.client.DispatchEx('HWPFrame.HwpObject')
    pid = win32process.GetWindowThreadProcessId(int(h.XHwpWindows.Item(0).WindowHandle))[1]
    if pid in old:
        raise RuntimeError('Hancom did not create an independent process; no document operations attempted.')
    h.XHwpWindows.Item(0).Visible = False
    audit = dict(own_pid=pid, existing_pids=sorted(old), expected_pages=expected)
    pdf = OUT / 'qa-figure-pages.pdf'
    try:
        assert h.Open(str(package), '', '')
        audit['hwp_pages_before_save'] = h.PageCount
        assert h.PageCount == expected, audit
        for fmt, target in targets.items():
            assert h.SaveAs(str(target), fmt, '')
        h.Clear(1)
        assert h.Open(str(targets['HWP']), '', '')
        audit['native_hwp_reopened_pages'] = h.PageCount
        assert h.PageCount == expected, audit
        page_text = [h.GetPageText(i, 0xffffffff) for i in range(h.PageCount)]
        audit['native_page_text_lengths'] = [len(t or '') for t in page_text]
        assert not any(any(c.isalnum() for c in (t or '')) for t in page_text), 'Unexpected visible document text'
        if qa_pdf:
            assert h.SaveAs(str(pdf), 'PDF', '')
    finally:
        # Only the verified new instance is closed; pre-existing HWP processes are untouched.
        h.Clear(1)
        h.Quit()
    assert targets['HWP'].read_bytes()[:8] == bytes.fromhex('D0CF11E0A1B11AE1')
    audit['hwpx_structure'] = package_check(targets['HWPX'], expected)
    audit['outputs'] = [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in targets.values()]
    if qa_pdf:
        import fitz
        doc = fitz.open(pdf)
        audit['qa_pdf_pages'] = len(doc)
        assert len(doc) == expected
        rendered = OUT / 'rendered'
        rendered.mkdir(exist_ok=True)
        for i, page in enumerate(doc, 1):
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(rendered / f'figure-{i:02d}.png')
        audit['qa_pdf_sha256'] = sha(pdf)
    (OUT / 'native-build-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', type=int, default=6)
    parser.add_argument('--save', action='store_true')
    parser.add_argument('--qa-pdf', action='store_true')
    args = parser.parse_args()
    package, layout = build_package(inputs(args.expected))
    check = package_check(package, args.expected)
    print(json.dumps({'package': str(package), 'layout': layout, 'structure': check}, ensure_ascii=False), flush=True)
    if args.save:
        print(json.dumps(native_save(package, args.expected, args.qa_pdf), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
