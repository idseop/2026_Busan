from pathlib import Path
import fitz,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'data/processed/예방지원-근거분석-20260916/yearbooks';O.mkdir(parents=True,exist_ok=True)
index=[]
for p in (R/'data/raw/보완자료').glob('*구급서비스통계연보*.pdf'):
 doc=fitz.open(p);year=p.stem[-4:];folder=O/year;folder.mkdir(exist_ok=True)
 for i,page in enumerate(doc):
  t=page.get_text()
  if '부산' in t:
   (folder/f'page-{i+1:03d}.txt').write_text(t,encoding='utf8')
   index.append({'edition':year,'pdfPage':i+1,'heading':t[:160].replace('\n',' '),'busanSnippet':t[max(0,t.find('부산')-100):t.find('부산')+220].replace('\n',' ')})
print(json.dumps(index[:45],ensure_ascii=False,indent=2))
(O/'page-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf8')
