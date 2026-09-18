"""Candidate-by-candidate resident context for service information design."""
from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[2];O=R/'data/processed/최종논리검증-20260916/population';O.mkdir(parents=True,exist_ok=True)
P=R/'data/processed/최종결과-20260915/dashboard.json';read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(P);m=read(P.parent/'manifest.json');assert sha(P)==next(v['sha256'] for v in m['outputs'] if v['path'].endswith('/dashboard.json'))
groups=[('0–11세',0,12),('12–19세',12,20),('20–39세',20,40),('40–64세',40,65),('65–79세',65,80),('80세 이상',80,101)]
cases=[('연제구','연산동','심정지'),('부산진구','부전동','교통사고'),('수영구','광안동','교통사고')]
annual=[];ages=[];summ=[];links=[]
for gu,dong,kind in cases:
 refs=[next(v for v in d['rawRegions'] if v['district']==gu and v['rawDong']==dong and v['year']==y and v['scope']=='C') for y in range(2020,2025)]
 assert all(v['candidateCodes']==refs[0]['candidateCodes'] for v in refs)
 for code in refs[0]['candidateCodes']:
  pop=[next(v for v in d['population'] if v['year']==y and v['code']==code) for y in range(2020,2025)]
  assert len({v['name'] for v in pop})==1 and all(v['district']==gu for v in pop)
  records=[]
  for v in pop:
   assert len(v['ages'])==101 and sum(v['ages'])==v['total']
   rec={'district':gu,'rawDong':dong,'subtype':kind,'candidateCode':code,'candidateName':v['name'],'year':v['year'],'referenceDate':v['referenceDate'],'total':v['total'],'age12Plus':sum(v['ages'][12:]),'age65Plus':sum(v['ages'][65:])}
   rec['age12PlusShare']=rec['age12Plus']/v['total'];rec['age65PlusShare']=rec['age65Plus']/v['total']
   for label,lo,hi in groups:rec[label+'Count']=sum(v['ages'][lo:hi]);rec[label+'Share']=sum(v['ages'][lo:hi])/v['total']
   annual.append(rec);records.append(rec)
   ages.extend({'district':gu,'rawDong':dong,'candidateCode':code,'candidateName':v['name'],'year':v['year'],'age':a,'ageLabel':'100세 이상' if a==100 else str(a),'count':n,'share':n/v['total']} for a,n in enumerate(v['ages']))
  first,last=records[0],records[-1]
  summ.append({'district':gu,'rawDong':dong,'candidateCode':code,'candidateName':last['candidateName'],'total2020':first['total'],'total2024':last['total'],'totalChange':last['total']-first['total'],'age12Plus2024':last['age12Plus'],'under12_2024':last['total']-last['age12Plus'],'age65Plus2020':first['age65Plus'],'age65Plus2024':last['age65Plus'],'age65Share2020':first['age65PlusShare'],'age65Share2024':last['age65PlusShare'],'age65ShareChangePP':100*(last['age65PlusShare']-first['age65PlusShare'])})
 links.append({'district':gu,'rawDong':dong,'subtype':kind,'candidateCodes':refs[0]['candidateCodes'],'sameCodesAndNamesAcross5Years':True,'historicalBoundaryIdentityNotNewlyVerified':True,'receiptAssignmentConfirmed':False})
pd.DataFrame(annual).to_csv(O/'candidate_annual_age_bands.csv',index=False,encoding='utf-8-sig');pd.DataFrame(ages).to_csv(O/'candidate_all101ages.csv',index=False,encoding='utf-8-sig');pd.DataFrame(summ).to_csv(O/'candidate_change_2020_2024.csv',index=False,encoding='utf-8-sig')
out={'meta':{'period':'2020–2024 각12월31일','scope':'원문동 3개에 대응하는 행정동 후보14개 각각. 합산·신고 배정 없음','groups':[x[0] for x in groups],'decision':'기본 CPR 12세 이상 안내와 다른 연령의 예방교육 경로를 구분하는 주민 배경. 연령조건 충족 인원은 실제 수강 수요·접근 가능 인원·환자수가 아님','age65Meaning':'65세 이상은 전체 구성의 변화 설명용이며 교육 대상 제한이나 안내 필요성·장벽의 증거가 아님','comparison':'동일 코드와 명칭을 대조했지만 코드 지속만으로 경계 불변을 새로 입증하지 않음'},'links':links,'annual':annual,'changes':summ,'serviceRelation':[{'id':'cpr-basic','officialAgeCondition':'12세 이상','application':'후보 동별 12세 이상과 미만 주민 규모를 별도 제시; 기본 과정 조건을 전체 예방교육에 확대하지 않음','notEstablished':'개별 거주자의 수강 적합성, 실제 수요, 접근 장벽, 교육 효과'},{'id':'preschool-visit','officialAgeCondition':'미취학 아동·유치원·어린이집','application':'별도 방문교육 경로 존재를 제공','notEstablished':'나이별 주민표만으로 실제 미취학 재원 여부를 판정할 수 없어 자격인원 산출하지 않음'},{'id':'traffic-context','application':'지역 내 연령 구성이 서로 달라 단일 고령층 사고 설명으로 묶지 않음','notEstablished':'교통신고 대상자 연령, BDI 구간 이용자 연령, 현장 보행속도·시설 필요량'}]}
(O/'prevention-population.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
fig,ax=plt.subplots(figsize=(14,10));palette=['#cbd8e1','#96beca','#419b9e','#257c76','#d5a44c','#b4763f'];df=pd.DataFrame(annual)
for i,x in enumerate(summ):
 for j,y in enumerate([2020,2024]):
  v=df[(df.candidateCode==x['candidateCode'])&(df.year==y)].iloc[0];left=0
  for k,(label,lo,hi) in enumerate(groups):
   width=v[label+'Share']*100;ax.barh(i*2.5+j,width,left=left,height=.82,color=palette[k],label=label if i==0 and j==0 else None);left+=width
ax.set_yticks([i*2.5+.5 for i in range(len(summ))],[x['candidateName'] for x in summ]);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xlabel('주민 전체 연령 구성비 (%) · 각 후보 위 막대2020 / 아래 막대2024');ax.set_title('같은 원문 동명 안에서도 주민 연령 구성은 다르다',fontsize=19,pad=26);ax.legend(ncol=6,loc='upper center',bbox_to_anchor=(.5,1.04),frameon=False);ax.grid(axis='x',alpha=.15)
fig.text(.08,.025,'각 연도12월31일 주민 · 부전2·연산8·광안4 행정동 후보를 합산하지 않음\n12세 경계는 기본 CPR 안내 조건과 대조. 실제 신고자·환자 연령, 수강수요 또는 사고 위험을 뜻하지 않음.',fontsize=11);fig.tight_layout(rect=(0,.075,1,1))
for ext in ['png','svg']:fig.savefig(O/f'candidate_age_context.{ext}',dpi=170)
plt.close(fig)
(O/'manifest.json').write_text(json.dumps({'input':{'file':str(P.relative_to(R)),'sha256':sha(P),'priorManifestMatch':True},'scriptSHA256':sha(Path(__file__)),'validation':{'candidates':len(summ),'annualRows':len(annual),'ageRows':len(ages),'all101AgeSumsMatch':True,'sameCodeNameAcrossYears':True},'outputs':[{'file':p.name,'sha256':sha(p)} for p in O.iterdir() if p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summ,ensure_ascii=False))
