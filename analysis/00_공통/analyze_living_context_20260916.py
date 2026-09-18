"""Separate administrative-dong living-population background; no event allocation."""
from pathlib import Path
import hashlib,json,urllib.request
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2];RAW=ROOT/'data/raw/공간인구보완';OUT=ROOT/'data/processed/후속입증-20260916/living'
OUT.mkdir(parents=True,exist_ok=True)
VALUES=['평균주거인구수','평균직장인구수','평균방문인구수']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,o):(OUT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 sources=[]
 fullurl='https://www.data.go.kr/data/15142761/fileData.do'
 fullpage=OUT/'official-hour-page.html'
 if not fullpage.exists():
  with urllib.request.urlopen(urllib.request.Request(fullurl,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:fullpage.write_bytes(r.read())
 sources.append({'url':fullurl,'path':str(fullpage.relative_to(ROOT)),'sha256':sha(fullpage),'definitionLocation':'데이터 한계: 주거지와 직장지가 같은 경우 주거지로 판단'})
 for id,kind in [('15142761','hour'),('15142760','age')]:
  url=f'https://www.data.go.kr/catalog/{id}/fileData.json';p=OUT/f'official-{kind}-metadata.json'
  if not p.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:p.write_bytes(r.read())
  sources.append({'url':url,'path':str(p.relative_to(ROOT)),'sha256':sha(p)})
 frames={};audits=[];meanframes={}
 for code,kind,key,expected in [('LP00003','hour','시간대',24),('LP00002','age','나이대',6)]:
  p=next(RAW.glob(f'*{code}*.xlsx'));f=pd.read_excel(p,dtype=str)
  m=f['기준년월'].astype(str).str.startswith('2024');use=f[m].copy()
  assert not use.duplicated(['기준년월','행정동코드',key]).any()
  assert not use.isna().any().any()
  for v in VALUES:use[v]=pd.to_numeric(use[v],errors='raise');assert (use[v]>=0).all()
  assert use.groupby(['기준년월','행정동코드']).size().eq(expected).all()
  assert use['행정동코드'].nunique()==205 and use['기준년월'].nunique()==12
  mean=use.groupby(['행정동코드','행정동명',key],as_index=False)[VALUES].mean()
  mean['aggregation']='2024 기준년월12개의 월별일평균 값을 동일 가중 평균';mean['months']=12
  mean.to_csv(OUT/f'all205-{kind}-monthly-mean.csv',index=False,encoding='utf-8-sig')
  use.to_csv(OUT/f'all205-{kind}-2024-monthly.csv',index=False,encoding='utf-8-sig')
  frames[kind]=use;meanframes[kind]=mean
  audits.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'allRows':len(f),'availableMonths':sorted(f['기준년월'].unique().tolist()),'selectedRows':len(use),'outside2024Rows':int((~m).sum()),'selectedDongCount':205,'selectedMonthCount':12,'valuesPerDongMonth':expected,'uniqueKeys':True,'missingSelectedRows':0,'omission':'2023·2025는 이번2024배경 밖으로 분리; 원본보존'})
  assert len(f)==len(use)+int((~m).sum())
 h=meanframes['hour'];stats=[]
 for (code,name),g in h.groupby(['행정동코드','행정동명']):
  r={'code':code,'name':name}
  for v,label in zip(VALUES,['residential','workplace','visitor']):
   z=float(g.loc[g['시간대']=='00시',v].iloc[0]);n=float(g.loc[g['시간대']=='12시',v].iloc[0]);r.update({label+'00':z,label+'12':n,label+'NoonMidnightRatio':n/z if z else None,label+'PeakHour':str(g.loc[g[v].idxmax(),'시간대'])})
  monthly=frames['hour'][frames['hour']['행정동코드']==code].pivot(index='기준년월',columns='시간대',values='평균방문인구수')
  r['visitorNoonAboveMidnightMonths']=int((monthly['12시']>monthly['00시']).sum());stats.append(r)
 pd.DataFrame(stats).to_csv(OUT/'all205-noon-midnight-comparison.csv',index=False,encoding='utf-8-sig')
 dashboard=ROOT/'web/final/data/dashboard.json';db=json.loads(dashboard.read_text(encoding='utf-8'))
 links=[]
 for r in db['rawRegions']:
  if r['year']!=2024 or r['scope']!='C':continue
  for code in r['candidateCodes']:
   match=next((s for s in stats if s['code']==code),None)
   links.append({'district':r['district'],'rawDong':r['rawDong'],'candidateCode':code,'candidateCount':len(r['candidateCodes']),'originalLinkStatus':r['linkStatus'],'livingName':match['name'] if match else None,'available':match is not None,'geographyConfirmed':False,'joiningRule':'기존 후보코드에 생활인구를 개별 연결. 후보 합산·119 사건 배분 없음'})
 pd.DataFrame(links).to_csv(OUT/'raw-dong-candidate-links.csv',index=False,encoding='utf-8-sig')
 selected=['부산진구 부전1동','부산진구 부전2동','남구 대연1동','남구 대연5동','금정구 금성동','기장군 기장읍']
 summary={'question':'주민등록인구만으로 보이지 않는 시간별 주거·직장·방문 배경은 어떻게 다른가?','period':'파일의 기준년월2024.1~12','aggregation':'각 기준월의 일평균 값을12개월 동일가중 평균. 연간 실인원·일수 가중 연평균이 아님.','sourceMeaning':'통신사 기지국 신호 기반 월별일평균. 주거: 전월00~06최다체류동; 직장:평일09~18의30%이상체류중최다동; 그외방문. 주거·직장 동일시 주거로 분류.','dateCaution':'공식설명은 전월 산정이라고 명시. 파일 기준년월과119 관측월이 완전히 일치한다고 주장하지 않음.','unit':'명(제공 월별일평균 값의12기준월 평균)','figuresSelectedBy':'기존 부전·대연 심층지역의 복수행정동을 분리해 보이고 금성동·기장읍은 기존검토지역의 다른 배경으로 비교. 위험순위 아님.','profiles':[s for s in stats if s['name'] in selected],'allDongProfiles':stats,'audits':audits,'sources':sources,'reuseDashboard':{'path':str(dashboard.relative_to(ROOT)),'sha256':sha(dashboard)},'limits':['주거·직장·방문 세열을 합산한 총량을 만들지 않음','24시간 인구를 합산하지 않음;한사람이 여러시간에관측가능','12시/00시 비교는 시간차이지 요일별 비교 아님','연령자료는6개제공연령대유지. 시간자료와교차해시간별특정연령 추정금지','직장인구는취업자수·방문인구는등산객/관광객수가 아님','행정동전체 배경이므로 특정시장·산길·개별119 신고의노출분모로 사용하지 않음','통신사별모집단확대·세부추정오차는 공개설명에서확정하지못함']}
 summary['limits'].append('직장 산정에서 운송·택배·물류 등 한 곳에 오래 체류하지 않는 직업군은 제외될 수 있음(공식 설명).')
 dump('living-context.json',summary);dump('validation.json',{'pass':True,'audits':audits,'numericSumAcrossCategoriesOrHoursPerformed':False,'candidateLinks':len(links)})
 plot(h,selected)
 (OUT/'README.md').write_text('''# 생활인구 배경 분석

주민등록인구만으로 설명되지 않는 시간별 체류 구성을 확인했다. 보유 파일은2023.1~2025.12의36개 기준월이며 이번 비교는2024년12개 기준월을 사용했다. 시간자료59,040행(205행정동×12월×24시간), 연령자료14,760행(205×12×6연령대)을 보존하고 집계했다.

각 기준월에 제공된 일평균 값을 동일가중 평균했다. 연간 고유인원이나 일수 가중 연평균을 뜻하지 않는다. 공식 설명의 전월 산정 기준 때문에 신고 관측월과 완전히 동시라고 주장하지 않는다.

부전1동 방문 값은00시5,326.3에서12시17,718.2로3.33배, 부전2동은16,318.9에서21,994.5로1.35배였다. 두 행정동 모두12개 기준월에서12시 값이00시보다 높았지만, 평균곡선의 방문 최대시간은 각각14시·19시로 달랐다. 같은 부전동이라는 신고 지역명만으로 활동시간을 하나로 정하는 것은 적절하지 않다.

금성동은 같은 비교에서6.77배지만 방문자를 등산객으로 간주할 수 없다. 기장읍 역시 방문·직장 값은 주민등록 인구와 다른 배경이며 특정 시설 이용량이나 신고의 분모가 아니다. 세 인구유형·24시간을 더한 총량은 만들지 않았다. 연령과 시간 파일은 교차집계가 아니므로 특정 시간의 고령 방문자를 추정하지 않는다.

`all205-hour-2024-monthly.csv`와`all205-age-2024-monthly.csv`는 선택 기간 원값, `all205-*-monthly-mean.csv`는12기준월 평균이다. `raw-dong-candidate-links.csv`는 기존2024 후보코드를 보존한 배경 연결로 후보 합산·119 사건 배분은 하지 않는다. 미확정 지리는 그대로 유지했다.

공식 정의: 공공데이터포털15142761(시간),15142760(연령), 제공기관부산광역시. 시간자료는 통신사기지국신호 기반으로 주거·직장·방문을 분류한다. 통신사포괄범위·추정오차의 세부정보는 별도 확인이 필요하다. 공식메타JSON·입력SHA256·선택제외 건수는living-context.json과validation.json에 기록했다.

실행: `.venv-check/Scripts/python.exe analysis/00_공통/analyze_living_context_20260916.py`. 의존성:pandas,openpyxl(원본읽기),matplotlib.
''',encoding='utf-8')
 print(json.dumps(summary['profiles'],ensure_ascii=False,indent=2))

def plot(h,selected):
 plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'svg.fonttype':'none','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#233e49'})
 fig,axes=plt.subplots(2,3,figsize=(15,9));fig.subplots_adjust(left=.07,right=.97,top=.78,bottom=.19,hspace=.48,wspace=.3)
 fig.suptitle('주거·직장·방문 배경은 같은 지역명 안에서도 다르다',x=.05,ha='left',fontsize=21,fontweight='bold',y=.96)
 fig.text(.05,.89,'2024 기준월12개의 월별 일평균을 동일가중 평균 · 행정동별 표시 · 각 패널 세로축 범위가 다름',fontsize=12)
 for ax,name in zip(axes.flat,selected):
  g=h[h['행정동명']==name].sort_values('시간대')
  for v,label,color in zip(VALUES,['주거','직장','방문'],['#277b77','#d9954d','#467fac']):ax.plot(range(24),g[v],label=label,lw=2.3,color=color)
  ax.set_title(name,loc='left',fontweight='bold',fontsize=12);ax.set_xticks([0,6,12,18,23],['00','06','12','18','23시']);ax.set_ylim(bottom=0);ax.yaxis.grid(True,alpha=.15);ax.set_ylabel('명 · 평균값');ax.ticklabel_format(axis='y',style='plain')
 axes[0,0].legend(frameon=False,ncol=3,loc='upper left',bbox_to_anchor=(0,1.27))
 fig.text(.05,.095,'주민등록인구·연간 방문자 수가 아니다. 세 유형과24시간을 합산하지 않았다. 복수 행정동은 개별 표시했다.\n방문인구를 등산객·특정 시설 이용자 또는119 신고 대상자로 바꾸어 해석하지 않는다. 기준년월과 신고일의 완전 일치를 주장하지 않는다.',fontsize=10,linespacing=1.7)
 fig.text(.05,.03,'출처: 부산광역시 PD_LP00003 / 공공데이터포털15142761 · 보유자료2023~25 중2024선택 · 통신사 기지국신호 기반 추정',fontsize=9,color='#617682')
 for ext in ['png','svg']:fig.savefig(OUT/f'living_hour_context.{ext}',dpi=160,facecolor='white')
 plt.close(fig)
if __name__=='__main__':main()
