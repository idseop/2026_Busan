"""Check frozen figure artifacts and pack only deliverables and provenance."""
from pathlib import Path
import json, hashlib, zipfile
from PIL import Image
import fitz

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/paper-figures-20260918'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))

core=read('core-01-07-metadata.json')
support=read('support-metadata/support-figure-manifest.json')
additional=read('metadata/additional-figures.json')
inputs={**core['sources'],**additional['sources']}
inputs.update({r['path']:r['sha256'] for r in support['sources']})
for name,expected in inputs.items():
    assert sha(ROOT/name)==expected, ('input changed',name)
assert all(r['pass'] for r in core['checks'])
assert all(r['pass'] for r in additional['checks'])
assert support['health_rows_exact'] and support['unmet_rows_exact']

for r in core['outputs']:
    for ext in ['png','svg']:
        assert sha(OUT/r['set']/(r['file']+'.'+ext))==r[ext+'_sha256']
for r in support['figures']:
    assert sha(OUT/r['png'])==r['png_sha256']

images=[]
for folder,n in [('01-clean-original',10),('02-paper-style',16)]:
    assert len(list((OUT/folder).glob('*.png')))==n
    assert len(list((OUT/folder).glob('*.svg')))==n
    for p in sorted((OUT/folder).glob('*.png')):
        with Image.open(p) as im:
            assert abs(im.info['dpi'][0]-450)<1
            assert im.width>=3000
            im.load()
            images.append({'file':p.relative_to(OUT).as_posix(),'pixels':list(im.size),'dpi':im.info['dpi'],'sha256':sha(p)})

pdfs=read('metadata/pdf-generation.json')
for r in pdfs:
    p=OUT/r['file'];assert sha(p)==r['sha256']
    with fitz.open(p) as doc: assert len(doc)==r['count']
    folder='01-clean-original' if r['count']==10 else '02-paper-style'
    for page in r['pages']:
        assert sha(OUT/folder/(page['figure']+'.svg'))==page['svg_sha256']

preserved={
 '2026년 Big Data 활용 대회 작성 서식 (2).hwp':'54aaf652073b07e7b88198466c372f3267af3339f48644612c8fee3ae27f22b6',
 'output/report-visual-edit-20260918/deliverables/2026-BigData-보고서-시각화편집본.hwpx':'0ae54c12f233dd68bbf308e421b3f2b6aca48e579c8bb17dbd778e7fcb18dba4',
 'output/report-visual-edit-20260918/deliverables/2026-BigData-보고서-시각화편집본.pdf':'3d1eb2cba914d430bfff4ec2a73a6eb490e9589d4c9a621951b61396edc6b996',
}
for name,expected in preserved.items():assert sha(ROOT/name)==expected, ('original changed',name)

reviews=['metadata/final-visual-review.md','metadata/final-data-review.md']
for name in reviews:assert (OUT/name).is_file(),('review pending',name)
record={'status':'PASS','date':'2026-09-18','input_files_unchanged':len(inputs),'original_files_unchanged':preserved,
 'png_count':26,'svg_count':26,'pdf_count':2,'pdf_pages':[10,16],'images':images,
 'pdfs':[{'file':r['file'],'sha256':r['sha256']} for r in pdfs],'independent_reviews':reviews}
(OUT/'metadata/final-package-check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')

target=ROOT/'output/2026-BigData-그림만-논문형시각화.zip'
included=[]
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(OUT.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(OUT)
        if rel.parts[0]=='pdf-rendered' or '__pycache__' in rel.parts:continue
        assert p.suffix.lower() not in ['.hwp','.hwpx'], 'unexpected report file'
        z.write(p,Path(OUT.name)/rel);included.append(rel.as_posix())
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    assert len([n for n in z.namelist() if n.endswith('.png')])==26
    assert len([n for n in z.namelist() if n.endswith('.svg')])==26
    assert len([n for n in z.namelist() if n.endswith('.pdf')])==2
summary={'zip':str(target),'sha256':sha(target),'bytes':target.stat().st_size,'files':len(included),
 'png_count':26,'svg_count':26,'pdf_pages':[10,16],'status':'PASS'}
(ROOT/'output/2026-BigData-그림만-논문형시각화-검증.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
