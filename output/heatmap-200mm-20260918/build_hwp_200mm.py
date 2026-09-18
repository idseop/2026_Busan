"""Create a separate, single-page HWP with one 200 x 140 mm heatmap.

Reuses the verified isolated Hancom save/reopen implementation without
modifying that implementation or the earlier six-page deliverables.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import argparse
import importlib.util
import json

from lxml import etree as E
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
SOURCE = OUT / 'figures/01-time-heatmap-200x140mm.png'
BASE = '시간대별-접수비중-200mm'

spec = importlib.util.spec_from_file_location(
    'verified_hwp_builder', ROOT / 'output/journal-hwp-20260918/build_figure_hwp.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
builder.OUT = OUT
builder.ROOT = ROOT
builder.BASE = BASE


def build():
    assert SOURCE.is_file(), f'Final PNG missing: {SOURCE}'
    with Image.open(SOURCE) as im:
        assert abs(im.width / im.height - 200 / 140) < .002, 'Unexpected aspect ratio'
    package, layout = builder.build_package([SOURCE])
    with ZipFile(package) as z:
        files = {name: z.read(name) for name in z.namelist()}
    section = E.fromstring(files['Contents/section0.xml'])
    margin = section.find('.//hp:pagePr/hp:margin', builder.NS)
    margin.set('left', str(builder.hunit(5)))
    margin.set('right', str(builder.hunit(5)))
    pic = section.find('.//hp:pic', builder.NS)
    w, h = builder.hunit(200), builder.hunit(140)
    for name in ['orgSz', 'curSz', 'sz']:
        size = pic.find('hp:' + name, builder.NS)
        size.set('width', str(w))
        size.set('height', str(h))
    rot = pic.find('hp:rotationInfo', builder.NS)
    rot.set('centerX', str(w // 2))
    rot.set('centerY', str(h // 2))
    for point, (x, y) in zip(pic.find('hp:imgRect', builder.NS),
                             [(0, 0), (w, 0), (w, h), (0, h)]):
        point.set('x', str(x))
        point.set('y', str(y))
    files['Contents/section0.xml'] = builder.xml(section)
    with ZipFile(package, 'w', compression=ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data, compress_type=ZIP_STORED if name == 'mimetype' else ZIP_DEFLATED)
    layout[0].update(width_mm=round(w / 7200 * 25.4, 4),
                     height_mm=round(h / 7200 * 25.4, 4),
                     requested_width_mm=200, requested_height_mm=140,
                     hwp_width_units=w, hwp_height_units=h,
                     paper_mm=[210, 297], side_margin_mm=5)
    (OUT / 'layout-plan.json').write_text(json.dumps(layout, ensure_ascii=False, indent=2), encoding='utf-8')
    builder.package_check(package, 1)
    return package, layout


def verify_dimensions(path):
    with ZipFile(path) as z:
        sec = E.fromstring(z.read('Contents/section0.xml'))
        size = sec.find('.//hp:pic/hp:sz', builder.NS)
        page = sec.find('.//hp:pagePr', builder.NS)
        assert int(size.get('width')) == builder.hunit(200), dict(size.attrib)
        assert int(size.get('height')) == builder.hunit(140), dict(size.attrib)
        assert int(page.get('width')) == builder.hunit(210)
        assert int(page.get('height')) == builder.hunit(297)
        images = [name for name in z.namelist() if name.startswith('BinData/')]
        assert len(images) == 1 and z.read(images[0]) == SOURCE.read_bytes()
    return {'requested_mm': [200, 140], 'hwp_units': [int(size.get('width')), int(size.get('height'))],
            'paper_mm': [210, 297], 'exact_source_image_preserved': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', action='store_true')
    args = parser.parse_args()
    package, layout = build()
    print(json.dumps({'layout': layout}, ensure_ascii=False), flush=True)
    if args.save:
        audit = builder.native_save(package, 1, True)
        audit['dimension_verification'] = verify_dimensions(ROOT / (BASE + '.hwpx'))
        (OUT / 'native-build-audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(audit, ensure_ascii=False), flush=True)
