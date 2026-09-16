from pathlib import Path
import pymupdf as fitz
import zipfile,pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/context'
for gu in ['연제구','부산진구','수영구']:
 with zipfile.ZipFile(O/f'chs-browser-{gu}.bin') as z:
  for n in z.namelist():
   if n.endswith('.xlsx'):(O/f'chs-{gu}-tables.xlsx').write_bytes(z.read(n))
 book=pd.ExcelFile(O/f'chs-{gu}-tables.xlsx')
 print(gu,book.sheet_names[-12:])
 path=O/f'chs-browser-{gu}-1.pdf';doc=fitz.open(path)
 selected=[]
 for i,page in enumerate(doc):
  text=page.get_text()
  if '교육 경험률' in text or '교육경험률' in text:
   selected.append(f'\n=== PDF page {i+1} ===\n'+text)
   if i>150 and i<240:page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(O/f'chs-{gu}-page{i+1}.png')
 (O/f'chs-{gu}-education-pages.txt').write_text(''.join(selected),encoding='utf-8')
 print(gu,len(doc),[(i+1) for i,p in enumerate(doc) if '교육 경험률' in p.get_text() or '교육경험률' in p.get_text()])
 for n in [94,95,206,207,248,249,250]:
  if n<=len(doc):
   doc[n-1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(O/f'chs-{gu}-page{n}.png')
   (O/f'chs-{gu}-page{n}.txt').write_text(doc[n-1].get_text(),encoding='utf-8')
