"""SEMAS 2024 quarterly background for four BDI field-study areas.
No receipt/location inference and no arbitrary market/station radius.
"""
from pathlib import Path
import csv,hashlib,json,urllib.request,zipfile
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw/상권과거';OUT=ROOT/'data/processed/후속입증-20260916/commerce'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE='https://www.data.go.kr/data/15083033/fileData.do'
CASES=[('부전시장','부산진구','부전동'),('못골시장','남구','대연동'),('광안역 주변','수영구','광안동'),('신평역 주변','사하구','신평동')]
CAT='상권업종대분류명';MID='상권업종중분류명'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 inv=[]
 for p in sorted(RAW.glob('*.csv')):
  cols=pd.read_csv(p,nrows=0).columns.tolist()
  inv.append({'file':str(p.relative_to(ROOT)),'snapshot':p.name[:8],'bytes':p.stat().st_size,'columns':cols,'selected':p.name.startswith('2024'),'reason':'2024 현장조사 배경과 분기 민감도' if p.name.startswith('2024') else '보유 확인. 분류체계 시점 차이 및 현장조사 질문에 직접 불필요하여 이번 집계 제외'})
 dump('inventory.json',inv)
 sourceFile=OUT/'semas-official-metadata.html'
 if not sourceFile.exists():
  with urllib.request.urlopen(urllib.request.Request(SOURCE,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:sourceFile.write_bytes(r.read())
 audits=[];district_rows=[];local_rows=[];middle_rows=[];all_rows=[];profiles=[]
 for p in sorted(RAW.glob('2024*.csv')):
  date=p.name[:8];digest=sha(p);zipPath=RAW/f'SEMAS_shops_{date}_original.zip'
  with zipfile.ZipFile(zipPath) as z:
   name=next(n for n in z.namelist() if f'_부산_{date[:6]}.csv' in n)
   inner=hashlib.sha256(z.read(name)).hexdigest()
  assert digest==inner,'CSV does not match original ZIP member'
  f=pd.read_csv(p,dtype=str,keep_default_na=False)
  required=['상가업소번호','시도코드','시군구코드','시군구명','법정동코드','법정동명','상권업종대분류코드',CAT,'상권업종중분류코드',MID]
  missing=f[required].apply(lambda s:s.str.strip().eq('')).any(axis=1)
  invalidProvince=f['시도코드'].ne('26')
  dup=int(f['상가업소번호'].duplicated().sum())
  assert dup==0,'Duplicate shop identifier needs investigation, not automatic deletion'
  use=f[~missing & ~invalidProvince].copy()
  assert use['시군구코드'].nunique()==16
  assert not (use['법정동코드'].str[:5]!=use['시군구코드']).any()
  cats=sorted(use[CAT].unique())
  assert len(cats)==10
  audit={'snapshot':date,'file':str(p.relative_to(ROOT)),'sha256':digest,'zip':str(zipPath.relative_to(ROOT)),'zipMember':name,'zipMemberSha256':inner,'originalRows':len(f),'includedRows':len(use),'missingRequiredRows':int(missing.sum()),'outsideBusanRows':int(invalidProvince.sum()),'excludedUnionRows':int((missing|invalidProvince).sum()),'duplicateShopIds':dup,'districtCount':16,'categoryNames':cats,'coordinateUse':'좌표는 읽었으나 공간분석 미사용. 공란 여부를 분석포함조건으로 사용하지 않음.','buildingIdentifierUse':'건물관리번호는 업소ID가 아님. 같은건물에 여러업소 유지.'}
  audits.append(audit)
  for category,n in use[CAT].value_counts().items():all_rows.append({'snapshot':date,'category':category,'shops':int(n),'denominatorShops':len(use),'sharePct':100*n/len(use)})
  for (code,district,category),g in use.groupby(['시군구코드','시군구명',CAT]):
   den=int((use['시군구코드']==code).sum());district_rows.append({'snapshot':date,'districtCode':code,'district':district,'category':category,'shops':len(g),'denominatorShops':den,'sharePct':100*len(g)/den})
  for area,dist,dong in CASES:
   g=use[(use['시군구명']==dist)&(use['법정동명']==dong)]
   codes=g['법정동코드'].unique().tolist();assert len(codes)==1
   for category in cats:
    n=int((g[CAT]==category).sum());b=int((use[CAT]==category).sum())
    local_rows.append({'snapshot':date,'fieldStudyArea':area,'district':dist,'lawDong':dong,'lawDongCode':codes[0],'category':category,'shops':n,'denominatorShops':len(g),'sharePct':100*n/len(g),'busanSameSnapshotSharePct':100*b/len(use),'differenceFromBusanPercentagePoints':100*n/len(g)-100*b/len(use)})
   for (code,name),n in g.groupby(['상권업종중분류코드',MID]).size().items():middle_rows.append({'snapshot':date,'fieldStudyArea':area,'district':dist,'lawDong':dong,'categoryCode':code,'category':name,'shops':int(n),'denominatorShops':len(g),'sharePct':100*n/len(g)})
   profiles.append({'snapshot':date,'fieldStudyArea':area,'district':dist,'rawDong':dong,'lawDongCode':codes[0],'shops':len(g),'foodShops':int((g[CAT]=='음식').sum()),'retailShops':int((g[CAT]=='소매').sum()),'foodRetailSharePct':100*g[CAT].isin(['음식','소매']).sum()/len(g),'interpretation':'동 전체 등록업소 구성. 해당 시장·역 조사구간의 업소·이용자 수가 아니며 119 접수 위치와 결합하지 않음.'})
 for name,rows in [('all-busan-categories.csv',all_rows),('all16-district-categories.csv',district_rows),('four-law-dong-categories.csv',local_rows),('four-law-dong-middle-categories.csv',middle_rows),('four-area-snapshot-summary.csv',profiles)]:pd.DataFrame(rows).to_csv(OUT/name,index=False,encoding='utf-8-sig')
 for a in audits:
  assert sum(r['shops'] for r in district_rows if r['snapshot']==a['snapshot'])==a['includedRows']
  assert a['originalRows']==a['includedRows']+a['excludedUnionRows']
  assert sum(r['shops'] for r in all_rows if r['snapshot']==a['snapshot'])==a['includedRows']
 primary=[r for r in profiles if r['snapshot']=='20240930']
 sensitivity=[]
 for area,dist,dong in CASES:
  q=[r for r in profiles if r['rawDong']==dong]
  sensitivity.append({'fieldStudyArea':area,'district':dist,'rawDong':dong,'minQuarterShops':min(r['shops'] for r in q),'maxQuarterShops':max(r['shops'] for r in q),'minFoodRetailSharePct':min(r['foodRetailSharePct'] for r in q),'maxFoodRetailSharePct':max(r['foodRetailSharePct'] for r in q),'interpretation':'파일에 등록된 업소구성 민감도. 실개업·폐업 변화를 입증하지 않음.'})
 pd.DataFrame(sensitivity).to_csv(OUT/'quarter-sensitivity.csv',index=False,encoding='utf-8-sig')
 summary={'question':'독립 현장조사 4지역을 포함한 동 전체에서 어떤 업종이 주를 이루는가?','whyAdopted':'보행환경 연구가 조사한 상업·주거 혼재 배경을 공식 상가 목록으로 구체화. 서비스 접근/보행로 관리의 현장 맥락이며 인과 검정 아님.','primarySnapshot':'20240930','fieldStudyDate':'2024-10-26~2024-10-27','selectionReason':'현장조사 직전 가장 가까운 보유 분기. 2024.3·6·12는 구성 민감도 확인용.','sourceUrl':SOURCE,'metadataRetrieved':'2026-09-16','metadataSnapshotNote':'공식 설명 페이지는 현재2026자료 설명이며2024파일 날짜를 이 페이지 게시일로 대체하지 않음.','spatialUnit':'소상공인시장진흥공단 제공 법정동코드+구군+법정동명. 동 전체 배경. 시장/역 반경 생성 없음.','profiles':primary,'quarterlyProfiles':profiles,'primaryBusanShops':next(a['includedRows'] for a in audits if a['snapshot']=='20240930'),'audits':audits,'limits':['업소수는 유동인구·방문량·보행량·사고노출량이 아님','같은 건물의 여러 업소를 중복 삭제하지 않음','분기 업소수를 합쳐 고유업소 수로 만들지 않음','파일별 분류·목록 범위의 시점 차이를 확인해야 하므로 장기 업종 추세는 이번 질문에서 제외','2024년 상권배경을2026현재영업현황으로 표시하지 않음','동 배경으로 개별119 신고 원인·보행자 연령·시장별 위험을 추정하지 않음']}
 summary['quarterSensitivity']=sensitivity
 summary['coverageChangeCaution']='부산 등록목록143,964(9월)→161,440(12월). 목록수 변화만으로 신규개업·보행량 증가를 해석하지 않음.'
 dump('commerce-context.json',summary);dump('validation.json',{'checks':'원ZIP부산멤버 해시일치/ID유일/16구군/동코드구군일치/분류10종/포함제외/전시와구군합계','pass':True,'audits':audits})
 dump('source-manifest.json',{'officialMetadata':{'url':SOURCE,'file':str(sourceFile.relative_to(ROOT)),'sha256':sha(sourceFile)},'selectedInputs':audits})
 plot(local_rows,all_rows,primary)
 (OUT/'README.md').write_text('''# 상권 자료를 채택한 이유와 결과

보행 현장연구4지역의 동 전체 업종 배경을 확인하려고 보유 소상공인시장진흥공단 자료를 재사용했다. 현장조사(2024.10.26~27) 직전인2024.9말을 주 기준으로, 같은해 다른3분기를 민감도 비교에 사용한다. 2020~2024년20분기 파일의 헤더와 목록은 확인했지만, 다른시기의 분류를 임의로 연결한 장기 업종 추세는 만들지 않았다.

2024.9말 부산 목록143,964업소, 부전동6,216·대연동4,314·광안동3,203·신평동1,081업소다. 부전동은 소매31.4%로 부산25.4%보다 높고, 대연동·광안동은 음식36.9%·37.9%다. 이는 해당 시장 안의 특성이나 그곳을 이용하는 주민 수가 아니다.

이 자료는 ‘접수 건수만 보면 다른 현장을 같은 지역문제로 다룰 수 있다’는 문제제기에 상업환경의 차이를 보탠다. BDI가 직접 관찰한 보행로 점유·보차분리와 별도로 읽을 수 있으며, 업소수만으로 보행장애·특정 업종의 과실·안전시설 부족을 결론 내리지 않는다. 119 원문 지역이 동일명이어도 신고를 특정 시장이나 점포에 귀속시키지 않는다.

네 지역의 음식+소매 비중은2024년4분기 모두 과반이다. 다만9월~12월 부산 목록총수는143,964→161,440로 달라지므로 이를 신규개업·유동인구 증가로 설명하지 않는다. 분기 자료는 서로 합산하지 않는다.

## 전처리와 검산

상가업소번호는 파일 내 유일하여 중복 삭제를 하지 않았다. 건물관리번호가 같은 업소도 유지한다. 구군·법정동코드/명과 업종명으로 집계하며 필요한 필드 결측 및 부산외 행을 별도 점검했다. 위치반경·좌표공간결합은 시행하지 않았다. 선택4개 CSV는 보유 전국배포ZIP의 부산 멤버와SHA256이 일치한다.16구군 업종 합계와 부산합계가 일치한다. 공개산출물에는 업소ID·상호·주소·좌표를 포함하지 않았다.

공식출처: https://www.data.go.kr/data/15083033/fileData.do (확보2026.9.16). 현재페이지2026설명과 실제채택2024파일시점을 구분한다. 실행: `.venv-check/Scripts/python.exe analysis/00_공통/analyze_commerce_context_20260916.py`.
''',encoding='utf-8')
 print(json.dumps(primary,ensure_ascii=False,indent=2))

def plot(local_rows,all_rows,profiles):
 plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'svg.fonttype':'none','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#203c4c'})
 # Preserve all ten official categories; no after-the-fact category amalgamation.
 cats=[r['category'] for r in sorted([r for r in all_rows if r['snapshot']=='20240930'],key=lambda r:-r['shops'])]
 fig,ax=plt.subplots(figsize=(14,7.2));fig.subplots_adjust(left=.13,right=.97,bottom=.34,top=.77)
 fig.suptitle('같은 보행 현장 연구라도 동 전체의 업종 구성은 다르다',x=.045,ha='left',fontsize=20,fontweight='bold',y=.96)
 fig.text(.045,.88,'2024년 9월 말 등록 상가업소 · 법정동 전체 구성비 · 시장·역 조사구간과 구분',fontsize=12)
 labels=['부산 전체']+[p['rawDong'] for p in profiles];den=[next(r['denominatorShops'] for r in all_rows if r['snapshot']=='20240930')]+[p['shops'] for p in profiles]
 colors=['#137d82','#dea45d','#779b76','#8fa9bd','#b77e63','#667c95','#aac4b0','#c5b592','#6d99a2','#b2b9c2']
 left=np.zeros(5)
 for j,cat in enumerate(cats):
  vals=[next(r['sharePct'] for r in all_rows if r['snapshot']=='20240930' and r['category']==cat)]+[next(r['sharePct'] for r in local_rows if r['snapshot']=='20240930' and r['lawDong']==p['rawDong'] and r['category']==cat) for p in profiles]
  ax.barh(range(5),vals,left=left,height=.53,label=cat,color=colors[j])
  for i,v in enumerate(vals):
   if v>=12:ax.text(left[i]+v/2,i,f'{v:.1f}%',ha='center',va='center',fontsize=11,color='white' if j==0 else '#183c45',fontweight='bold')
  left+=vals
 ax.set_yticks(range(5),[f'{lab}\n{n:,}업소' for lab,n in zip(labels,den)]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('해당 지역의 등록 상가업소 구성비(%)');ax.legend(ncol=5,loc='upper center',bbox_to_anchor=(.5,-.18),frameon=False,fontsize=10)
 fig.text(.045,.075,'부전동·대연동·광안동·신평동은 각각 부전시장·못골시장·광안역·신평역 연구의 동 전체 배경이다.\n업소수는 실제 이용자·보행량·사고 노출량이 아니다. 서로 다른 공간 단위의 119 접수나 현장 결함과 직접 결합하지 않았다.',fontsize=10,linespacing=1.6)
 fig.text(.045,.02,'출처: 소상공인시장진흥공단 상가(상권)정보 부산202409, 보유 공식ZIP의 부산CSV와해시대조 · 2024년4분기별 비교표 별도',fontsize=9,color='#617783')
 for ext in ['png','svg']:fig.savefig(OUT/f'commerce_four_area_context.{ext}',dpi=160,facecolor='white')
 plt.close(fig)
if __name__=='__main__':main()
