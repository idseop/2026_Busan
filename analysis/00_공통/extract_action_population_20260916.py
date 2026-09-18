"""Separate all-age population candidates; never allocate receipts to candidates."""
from pathlib import Path
import json,hashlib
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/예방지원-근거분석-20260916/population'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 ap=OUT.parent/'analysis/action-patterns.json';dp=ROOT/'data/processed/최종결과-20260915/dashboard.json'
 manifest=json.loads((dp.parent/'manifest.json').read_text(encoding='utf-8'))
 assert sha(dp)==next(x['sha256'] for x in manifest['outputs'] if x['path'].endswith('/dashboard.json'))
 a=json.loads(ap.read_text(encoding='utf-8'));d=json.loads(dp.read_text(encoding='utf-8'))
 lookup={(p['year'],p['code']):p for p in d['population']};rows=[];candidates=[];checks=[]
 for case in a['profiles']:
  for link in case['populationLinks']:
   codes=link['candidateCodes']
   for code in codes:
    p=lookup.get((link['year'],code))
    if p is None:
     checks.append({'caseId':case['id'],'year':link['year'],'code':code,'status':'population_not_found'});continue
    assert len(p['ages'])==101 and sum(p['ages'])==p['total']
    meta={'caseId':case['id'],'receiptDistrict':case['district'],'receiptRawDong':case['rawDong'],'receiptSubtype':case['subtype'],'year':p['year'],'referenceDate':p['referenceDate'],'districtCode':p['districtCode'],'district':p['district'],'candidateCode':code,'candidateName':p['name'],'candidateCount':len(codes),'linkStatus':'단일 코드 후보' if len(codes)==1 else '복수 코드 후보·각각 표시','geographyConfirmed':False,'total':p['total']}
    candidates.append({**meta,'ages':p['ages'],'ageShares':[n/p['total'] for n in p['ages']]})
    for age,n in enumerate(p['ages']):rows.append({**meta,'age':age,'ageLabel':'100세 이상' if age==100 else f'{age}세','count':n,'share':n/p['total']})
    checks.append({'caseId':case['id'],'year':p['year'],'code':code,'status':'101ages_sum_matches_total'})
 pd.DataFrame(rows).to_csv(OUT/'case_population_all_101_ages.csv',index=False,encoding='utf-8-sig')
 payload={'meta':{'years':list(range(2020,2025)),'reference':'각 연도 12월31일 주민등록 연령별 인구','interpretation':'거주 주민 구성; 개별 신고자·환자 연령이 아님. 인구 비례 신고배분 및 인구대비 신고율 미계산. 복수 후보는 개별 행으로 유지하며 합산 금지.','age100':'100세 이상','source':'기존 검증 dashboard.population; 공식 전국 원본에서 추출한 부산 읍면동 인구'},'candidates':candidates}
 (OUT/'case-population.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
 plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
 selected=[]
 for name in ['기장읍','금성동']:
  p=next(x for x in candidates if x['receiptRawDong']==name and x['year']==2024 and x['candidateCount']==1)
  selected.append(p)
 fig,axes=plt.subplots(2,2,figsize=(15,9))
 for row,p in enumerate(selected):
  ages=list(range(101));n=p['ages'];shares=[100*x for x in p['ageShares']]
  for col,values in enumerate([n,shares]):
   ax=axes[row,col];ax.bar(ages,values,width=1,color='#168c93' if row==0 else '#567a9a');ax.set_xlim(-1,102)
   ax.set_xticks([0,20,40,60,80,100],['0','20','40','60','80','100+']);ax.set_xlabel('연령(세; 100+는 100세 이상)');ax.set_ylabel('주민 수(명)' if col==0 else '주민 구성비(%)')
   ax.set_title(f"{p['district']} {p['candidateName']} · 주민 {p['total']:,}명 · 2024-12-31",fontsize=12);ax.grid(axis='y',alpha=.15)
 maxshare=max(max(p['ageShares'])*100 for p in selected)*1.1
 for ax in axes[:,1]:ax.set_ylim(0,maxshare)
 fig.suptitle('같은 예방 정보를 제공하더라도 주민 구성의 규모와 분포는 다르다\n전체 101개 연령 인원과 비중 · 신고자 연령을 뜻하지 않음',fontsize=17)
 fig.text(.5,.01,'단일 코드 후보의 주민 배경을 나란히 표시. 신고 발생 위치·실제 이용 장벽·연령별 사고 위험을 입증하지 않음.',ha='center',fontsize=11)
 fig.tight_layout(rect=(0,.04,1,.92))
 for ext in ['png','svg']:fig.savefig(OUT/f'population_full_ages_2024.{ext}',dpi=150)
 plt.close(fig)
 (OUT/'validation.json').write_text(json.dumps({'status':'passed','candidateProfiles':len(candidates),'longRows':len(rows),'checks':checks,'mergedMultipleCandidates':False},ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'manifest.json').write_text(json.dumps({'script':str(Path(__file__).relative_to(ROOT)),'scriptSha256':sha(Path(__file__)),'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ap,dp]],'outputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='manifest.json']},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'candidateProfiles':len(candidates),'longRows':len(rows),'figureTotals':[(p['candidateName'],p['total']) for p in selected]},ensure_ascii=False))
if __name__=='__main__':main()
