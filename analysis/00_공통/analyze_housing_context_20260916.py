"""Inspect and summarize existing SGIS housing context, with suppression retained."""
from pathlib import Path
import zipfile,io,json,hashlib
import pandas as pd
import shapefile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/후속입증-20260916/housing';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'data/raw/공간안전/국가데이터처_SGIS 행정구역 통계 및 경계.zip'
z=zipfile.ZipFile(source);sha=lambda b:hashlib.sha256(b).hexdigest()
names=z.namelist();inputs=[]
def get(part,suffix):
 n=next(n for n in names if part in n and n.endswith(suffix));b=z.read(n)
 inputs.append({'member':n,'sha256':sha(b)});return b
types=pd.read_csv(io.BytesIO(get('주택유형별주택','.csv')),encoding='cp949',dtype=str,keep_default_na=False)
years=pd.read_csv(io.BytesIO(get('건축년도별주택','.csv')),encoding='cp949',dtype=str,keep_default_na=False)
totals=pd.read_csv(io.BytesIO(get('주택총괄_총주택','.csv')),encoding='cp949',dtype=str,keep_default_na=False)
codes=pd.read_excel(io.BytesIO(get('제공용 코드','.xlsx')),header=None)
typemap=dict(codes[codes[4].astype(str).str.startswith('ho_gb_')][[4,3]].values)
starts=codes.index[codes[4].eq('ho_yr_001')].tolist();assert len(starts)==2
yrblock=codes.iloc[starts[1]:];yrblock=yrblock[yrblock[4].astype(str).str.startswith('ho_yr_')]
yearmap=dict(yrblock[[4,3]].values);assert yearmap['ho_yr_020']=='2024년'
def dbf(part):return [r.as_dict() for r in shapefile.Reader(dbf=io.BytesIO(get(part,'.dbf')),encoding='utf-8').records()]
dong=[r for r in dbf('bnd_dong') if r['ADM_CD'].startswith('21')]
district=[{'ADM_CD':r['SIGUNGU_CD'],'ADM_NM':r['SIGUNGU_NM']} for r in dbf('bnd_sigungu') if r['SIGUNGU_CD'].startswith('21')]
print('boundaries',len(dong),len(district))
nameby={r['ADM_CD']:r['ADM_NM'] for r in dong+district};nameby['21']='부산광역시'
districtby={r['ADM_CD']:r['ADM_NM'] for r in district}
frames=[]
for kind,f,labels in [('type',types,typemap),('constructionYear',years,yearmap),('total',totals,{'to_ho_001':'총주택(거처)수'})]:
 f=f[f['행정구역코드'].str.startswith('21')].copy();assert set(f['기준연도'])=={'2024'}
 assert not f.duplicated(['행정구역코드','통계항목']).any()
 for _,r in f.iterrows():
  code=r['행정구역코드'];item=r['통계항목'];v=pd.to_numeric(r['통계값'],errors='coerce')
  frames.append({'statisticsYear':2024,'boundaryDate':'2025-06-30','sgisCode':code,'district':districtby.get(code[:5],'부산광역시' if code=='21' else ''),'name':nameby.get(code,''),'level':'city' if len(code)==2 else 'district' if len(code)==5 else 'dong','kind':kind,'itemCode':item,'itemLabel':labels.get(item,'코드 미확인'),'value':None if pd.isna(v) else int(v),'rawValue':r['통계값'],'missing':bool(pd.isna(v))})
f=pd.DataFrame(frames)
print(f[f.sgisCode.eq('21')][['kind','itemCode','itemLabel','value']].to_string(index=False))
summary=[]
for code,g in f.groupby('sgisCode'):
 total=g[g.kind.eq('total')].iloc[0]['value'] if len(g[g.kind.eq('total')]) else None
 tt=g[g.kind.eq('type')];yy=g[g.kind.eq('constructionYear')]
 houses=tt[tt.itemCode.ne('ho_gb_006')];other=tt[tt.itemCode.eq('ho_gb_006')].value.iloc[0]
 summary.append({'sgisCode':code,'district':g.iloc[0]['district'],'name':g.iloc[0]['name'],'level':g.iloc[0]['level'],'total':total,'housingTypesPublishedSum':houses.value.sum(min_count=1),'otherLivingQuarters':other,'missingHousingTypeCells':int(houses.missing.sum()),'constructionPublishedSum':yy.value.sum(min_count=1),'missingConstructionCells':int(yy.missing.sum()),'housingTypesDifference':houses.value.sum(min_count=1)-total if total is not None else None})
f.to_csv(OUT/'busan_housing_context_2024.csv',index=False,encoding='utf-8-sig')
pd.DataFrame(summary).to_csv(OUT/'housing_sum_audit.csv',index=False,encoding='utf-8-sig')
assert sha(source.read_bytes())=='f1cf0f9de453ac7eaacb273f39cee52851183372b9ddfda428a967c3a670b2c6'
city=next(r for r in summary if r['level']=='city');assert city['housingTypesPublishedSum']==city['constructionPublishedSum']==city['total']==1227697
meta={'source':str(source.relative_to(ROOT)),'sourceUrl':'https://www.data.go.kr/data/15129688/fileData.do','sourceSha256':sha(source.read_bytes()),'priorHashMatched':True,'members':inputs,'statisticsYear':2024,'boundaryDate':'2025-06-30','dongRows':len(dong),'districtRows':len(district),'yearCodeHeading':str(codes.iloc[starts[1],2]),'yearCodeHeadingNote':'기간 제목은 2015~2023으로 남아 있으나 같은 블록에 2024년 코드 ho_yr_020 포함. 2010년용 중복 코드 블록을 사용하지 않음.','adoption':'2024 주택구성의 별도 배경. 2020~2024 개별 화재 건물·시설지원 수혜·위험률로 연결하지 않음.','missing':'원본 N/A 등 비수치 셀을 0으로 채우지 않음. 비공표값을 역산하지 않음. 공표된 동별 값의 단순합과 상위합계가 다를 수 있음.','denominator':'아파트·다세대·단독·연립·영업용건물내 주택 5유형의 부산 합계는 공표 총주택과 일치. 주택이외 거처는 별도 표시하고 주택 총계에 합산하지 않음.'}
(OUT/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
