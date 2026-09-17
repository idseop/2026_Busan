"""생성 CSV 간 분모 보존 및 해시 불변성을 별도로 검증한다."""
from pathlib import Path
import json
import hashlib
import pandas as pd
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/부산진구-중구-1차분석'
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
for group in ['inputs_sha256','outputs_sha256']:
    for name,h in m[group].items(): assert sha(ROOT/name)==h,name
def read(name): return pd.read_csv(OUT/(name+'.csv'))
base=read('01_조건별_신고수')
all_c=base[(base['조건']=='C')&(base['지역']=='부산 전체')]['신고건수'].sum()
assert read('01_부산전체_구군비교')['C신고건수'].sum()==all_c
for region in ['부산진구','중구']:
    total=base[(base['조건']=='C')&(base['지역']==region)]['신고건수'].sum()
    for name,key in [('03_원문동_분포','지역'),('02_월별_신고','지역'),('01_세부유형_연도','CLMTY_SGG_NM'),('05_기록상센터_구성','CLMTY_SGG_NM')]:
        d=read(name); assert d.loc[d[key]==region,'신고건수'].sum()==total,(name,region)
    heat=read('02_'+region+'_요일시간_건수')
    assert heat.iloc[:,1:].to_numpy().sum()==total
    p=read('06_구별인구와_신고'); p=p[p['지역']==region]
    assert ((p['85세이상']<=p['75세이상'])&(p['75세이상']<=p['65세이상'])&(p['65세이상']<=p['연말인구'])).all()
# XLSX를 표준 XML로 읽어 집계 키의 원문 정의 확인 (원본 변경 없음).
book=ROOT/'data/부산소방재난본부_119신고접수 현황_컬럼 정보 데이터.xlsx'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with ZipFile(book) as z:
    strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
    rows=[]
    for sheet in [n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]:
        for row in ET.fromstring(z.read(sheet)).findall('.//s:row',ns):
            vals=[]
            for cell in row.findall('s:c',ns):
                v=cell.find('s:v',ns)
                vals.append(strings[int(v.text)] if cell.get('t')=='s' and v is not None else ''.join(cell.itertext()))
            if any(any(k in v.upper() for k in ['PLCSCN_CNTR_NM','DCLR_DT','CLMTY_SGG_NM']) for v in vals): rows.append(vals)
assert len(rows)==3, '사용한 컬럼의 원문 정의를 확인해야 함'
result={'status':'통과','input_hashes_verified':len(m['inputs_sha256']),'output_hashes_verified':len(m['outputs_sha256']),'mass_balance':'구·동·유형·월·요일시간·기록상센터 합계 일치','columnbook_sha256':sha(book),'column_definitions':rows}
(OUT/'독립검증.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
