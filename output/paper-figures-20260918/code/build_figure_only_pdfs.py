"""Preserve figure-only SVG pages in two PDFs; no cover, header or caption."""
from pathlib import Path
import json,hashlib
import sys
import fitz
OUT=Path(__file__).resolve().parents[1]
DEST=OUT/'pdf';DEST.mkdir(exist_ok=True)
records=[]
existing_path=OUT/'metadata/pdf-generation.json'
existing=json.loads(existing_path.read_text(encoding='utf-8')) if existing_path.exists() else []
for folder,count,name in [
 ('01-clean-original',10,'01-기존도표-글자확대-그림만.pdf'),
 ('02-paper-style',16,'02-논문형도표-추가포함-그림만.pdf')]:
 if '--paper-only' in sys.argv and folder=='01-clean-original':
  records.append(next(r for r in existing if r['file']=='pdf/'+name))
  continue
 paths=sorted((OUT/folder).glob('*.svg'));assert len(paths)==count
 merged=fitz.open();pages=[]
 for p in paths:
  svg=fitz.open(stream=p.read_bytes(),filetype='svg')
  sub=fitz.open(stream=svg.convert_to_pdf(),filetype='pdf')
  merged.insert_pdf(sub)
  pages.append({'figure':p.stem,'svg_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 merged.set_metadata({'title':name[:-4],'subject':'Figure-only pages; captions and sources supplied separately','creator':'Matplotlib / SVG conversion'})
 target=DEST/name;merged.save(target,garbage=4,deflate=True);merged.close()
 doc=fitz.open(target);render=OUT/'pdf-rendered'/folder;render.mkdir(parents=True,exist_ok=True)
 for i,page in enumerate(doc):
  page.get_pixmap(matrix=fitz.Matrix(1.6,1.6),alpha=False).save(render/f'{i+1:02d}.png')
  pages[i]['pdf_size_pt']=[page.rect.width,page.rect.height]
 records.append({'file':target.relative_to(OUT).as_posix(),'count':len(doc),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pages':pages})
(OUT/'metadata/pdf-generation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{'file':r['file'],'pages':r['count'],'sha256':r['sha256']} for r in records],ensure_ascii=False,indent=2))
