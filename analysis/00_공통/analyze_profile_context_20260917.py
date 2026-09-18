"""Independent resident/place backgrounds for the call-profile comparisons.

No call rates: housing units, establishments and workers are separate contexts.
SGIS 2024 statistics use the supplied 2025 boundary/code edition.
"""
from pathlib import Path
import io,json,hashlib,zipfile,urllib.request
from datetime import datetime,timezone
import pandas as pd
import shapefile
from lxml import etree

R=Path(__file__).resolve().parents[2]
O=R/'data/processed/신고주민연결심화-20260917/context';O.mkdir(parents=True,exist_ok=True)
SRC=R/'data/raw/공간안전/국가데이터처_SGIS 행정구역 통계 및 경계.zip'
OLD=R/'data/processed/후속입증-20260916/housing'
META=json.loads((OLD/'manifest.json').read_text(encoding='utf8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
actual=sha(SRC.read_bytes());assert actual==META['sourceSha256']
archive=zipfile.ZipFile(SRC);members=[]
def get(part,ext):
 names=[n for n in archive.namelist() if part in n and n.endswith(ext)]
 assert len(names)==1,(part,names)
 b=archive.read(names[0]);members.append({'member':names[0],'sha256':sha(b)})
 return b
def dump(name,obj):
 (O/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
def numeric(v):
 try:return int(v)
 except ValueError:return None
def pct(a,b):return 100*a/b if a is not None and b else None
codes=pd.read_excel(io.BytesIO(get('제공용 코드','.xlsx')),header=None)
section=codes[2].ffill().astype(str)
labels={}
for prefix,kind in [('cp_bnu_','establishments'),('cp_bem_','employees')]:
 block=codes[section.str.contains('2024')&section.str.contains('11차')&section.str.contains(r'분류\(대\)',regex=True)&codes[4].astype(str).str.startswith(prefix)]
 assert len(block)==19,(kind,len(block))
 labels[kind]=dict(zip(block[4],block[3]))
 assert labels[kind][prefix+'003']=='제조업'
labels['housingType']=dict(codes[codes[4].astype(str).str.startswith('ho_gb_')][[4,3]].values)
dbf=get('bnd_dong','.dbf');dongs=[r.as_dict() for r in shapefile.Reader(dbf=io.BytesIO(dbf),encoding='utf8').records() if r['ADM_CD'].startswith('21')]
dbf=get('bnd_sigungu','.dbf');districts=[r.as_dict() for r in shapefile.Reader(dbf=io.BytesIO(dbf),encoding='utf8').records() if r['SIGUNGU_CD'].startswith('21')]
assert len(dongs)==206 and len(districts)==16
districtby={r['SIGUNGU_CD']:r['SIGUNGU_NM'] for r in districts}
nameby={r['ADM_CD']:r['ADM_NM'] for r in dongs}|districtby|{'21':'부산광역시'}
rows=[]
for part,kind in [('대분류)_사업체수','establishments'),('대분류)_종사자수','employees'),('총괄사업체수','totalEstablishments'),('총괄종사자수','totalEmployees'),('주택유형별주택','housingType'),('주택총괄_총주택','totalHousing')]:
 f=pd.read_csv(io.BytesIO(get(part,'.csv')),encoding='cp949',dtype=str,keep_default_na=False)
 f=f[f['행정구역코드'].str.startswith('21')].copy()
 assert set(f['기준연도'])=={'2024'}
 assert not f.duplicated(['행정구역코드','통계항목']).any()
 for _,r in f.iterrows():
  code,item=r['행정구역코드'],r['통계항목'];v=numeric(r['통계값'])
  assert code in nameby
  rows.append({'sgisCode':code,'name':nameby[code],'district':districtby.get(code[:5],'부산광역시'),'level':'city' if len(code)==2 else 'district' if len(code)==5 else 'dong',
   'statisticsYear':2024,'boundaryReferenceDate':'2025-06-30','kind':kind,'itemCode':item,'itemLabel':labels.get(kind,{}).get(item,kind),'value':v,'rawValue':r['통계값'],'suppressedOrUnavailable':v is None})
f=pd.DataFrame(rows);f.to_csv(O/'busan-housing-industry-2024.csv',index=False,encoding='utf-8-sig')
checks=[]
# Check the reused housing aggregation against raw members, without replacing it.
old=pd.read_csv(OLD/'busan_housing_context_2024.csv',dtype={'sgisCode':str},keep_default_na=False)
new=f[f.kind.isin(['housingType','totalHousing'])].set_index(['sgisCode','itemCode']).rawValue.sort_index()
prior=old[old.kind.isin(['type','total'])].set_index(['sgisCode','itemCode']).rawValue.sort_index()
assert new.equals(prior)
checks.append({'check':'raw housing members agree with prior verified housing table','passed':True,'rows':len(new)})
values={(r['sgisCode'],r['kind'],r['itemCode']):r['value'] for r in rows}
def val(code,kind,item):return values.get((code,kind,item))
for kind,item in [('totalHousing','to_ho_001'),('totalEstablishments','to_fa_010'),('totalEmployees','to_em_020')]:
 city=val('21',kind,item)
 assert sum(val(d,kind,item) for d in districtby)==city
 checks.append({'check':kind+' 16 districts equal city','passed':True,'city':city})

summary=[]
for code in sorted(nameby):
 if not any(r['sgisCode']==code for r in rows):continue
 th=val(code,'totalHousing','to_ho_001');apt=val(code,'housingType','ho_gb_003');det=val(code,'housingType','ho_gb_002')
 te=val(code,'totalEstablishments','to_fa_010');manufacturing=val(code,'establishments','cp_bnu_003')
 tw=val(code,'totalEmployees','to_em_020');mw=val(code,'employees','cp_bem_003')
 summary.append({'sgisCode':code,'district':districtby.get(code[:5],'부산광역시'),'name':nameby[code],
  'statisticsYear':2024,'boundaryReferenceDate':'2025-06-30','totalHousing':th,'detachedHousing':det,'detachedPct':pct(det,th),'apartmentHousing':apt,'apartmentPct':pct(apt,th),
  'totalEstablishments':te,'manufacturingEstablishments':manufacturing,'manufacturingEstablishmentPct':pct(manufacturing,te),
  'totalEmployees':tw,'manufacturingEmployees':mw,'manufacturingEmployeePct':pct(mw,tw),
  'linkStatus':'SGIS 2025 지역 자체 배경; 2020~2024 신고의 위치 배정 아님',
  'areaCaution':'2025 녹산·신호 분리 범위; 2024 주민 후보와 직접 결합하지 않음' if code in ['21120561','21120562'] else '같은 명칭도 과거 신고 경계·실제 장소 일치를 보장하지 않음'})
s=pd.DataFrame(summary);s.to_csv(O/'housing-industry-profiles.csv',index=False,encoding='utf-8-sig')
focus={'북구':['금곡동','화명1동','화명2동','화명3동'],'영도구':['동삼1동','동삼2동','동삼3동'],'강서구':['대저1동','대저2동','명지1동','명지2동','녹산동','신호동'],'기장군':['기장읍','정관읍']}
selected=s[s.apply(lambda r:r['name'] in focus.get(r['district'],[]),axis=1)].copy()
assert len(selected)==sum(map(len,focus.values()))
selected.to_csv(O/'selected-context.csv',index=False,encoding='utf-8-sig')
dump('selected-context.json',selected.where(pd.notnull(selected),None).to_dict('records'))

with zipfile.ZipFile(io.BytesIO(get('statistics_guide','.hwpx'))) as guide:
 text='\n'.join(' '.join(etree.fromstring(guide.read(n)).itertext()) for n in guide.namelist() if n.startswith('Contents/section') and n.endswith('.xml'))
 (O/'sgis-guide.txt').write_text(text,encoding='utf8')
url='https://www.data.go.kr/data/15129688/fileData.do'
snapshot={'url':url,'retrievedAt':datetime.now(timezone.utc).isoformat()}
try:
 body=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read()
 (O/'official-metadata.html').write_bytes(body);snapshot.update(sha256=sha(body),saved=True)
except Exception as e:snapshot.update(saved=False,error=str(e))
dump('manifest.json',{'source':str(SRC.relative_to(R)),'sha256':actual,'priorHashMatch':True,'members':members,'metadata':snapshot,
 'question':'같은 구에서도 주택·산업 배경이 달라 기존 대응의 적용 대상을 나누어 대조할 근거가 있는가.',
 'use':'2024 주택·산업구성의 별도 배경; 제조업 사업체는 공장 등록수·신고 발생 시설 수가 아님. 종사자 수는 주민·체류인구·신고 대상자 수가 아님.',
 'geography':'2024 통계, 2025-06-30 제공 경계. 2024 MOIS 인구와 2020~2024 신고에 코드 강제 결합 안함. 특히 녹산·신호 범위 변화 별도 표기.',
 'suppression':'N/A 보존, 0 대체·잔차 역산 안함. 제조업/주택 비중은 해당 자료가 공표된 경우만 계산.',
 'selection':'기존 신고·주민 비교 후보에 필요한 주택·산업 배경. 상권목록을 제조업 모수로 대체하지 않음.',
 'labelMapping':'2024년~/11차 산업분류(대) 블록만 사용; 같은 cp 코드의 과거 분류명 미사용',
 'checks':checks,'rows':len(rows),'selectedRows':len(selected),'outputs':[{'file':p.name,'sha256':sha(p.read_bytes())} for p in O.iterdir() if p.is_file() and p.name!='manifest.json']})
print(selected[['district','name','totalHousing','detachedPct','apartmentPct','manufacturingEstablishments','manufacturingEstablishmentPct','manufacturingEmployees']].to_string(index=False))
