"""Two explanatory figures from already verified aggregates; no new raw grouping."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
R=Path(__file__).resolve().parents[1];N=R/'data/processed/최종마감-20260916';O=N/'figures';O.mkdir(parents=True,exist_ok=True)
P=R/'data/processed/최종논리검증-20260916/population/prevention-population.json'
S=R/'data/processed/효과근거확장-20260916/temporal/selection_stable_temporal.json'
population=json.loads(P.read_text(encoding='utf-8'));stable=json.loads(S.read_text(encoding='utf-8'))['strata'][0]
assert stable['combinations']==325 and stable['monthSameAllFiveLeaveOut']==33 and stable['seasonSameAllFiveLeaveOut']==121
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#193d49','axes.labelcolor':'#193d49','svg.fonttype':'none','axes.unicode_minus':False})
TEAL='#147d82';NAVY='#193d49';ORANGE='#b16c34'
def save(fig,name):
 for ext in ['png','svg']:fig.savefig(O/f'{name}.{ext}',dpi=180,bbox_inches='tight',facecolor='white')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(14,9));ax.set(xlim=(0,1),ylim=(-.025,1));ax.axis('off')
def box(x,y,w,h,title,body,color=TEAL):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.009,rounding_size=.012',facecolor='#f0f6f5' if color==TEAL else '#faf3ec',edgecolor=color,lw=1.4))
 ax.text(x+.022,y+h-.018,title,fontsize=16,weight='bold',va='top',color=color)
 ax.text(x+.022,y+h-.075,body,fontsize=11.5,va='top',linespacing=1.45)
def arrow(a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',lw=1.5,color='#6a858a'))
ax.text(0,.995,'부산 전체 비교에서 설명 사례까지',fontsize=23,weight='bold',va='top')
ax.text(0,.918,'순위나 탈락표가 아니라, 비교 범위와 판단 근거를 구분한 과정',fontsize=12,va='top')
box(.20,.745,.60,.12,'970개 지역명·유형 조합','194개 신고 지역명 × 5유형 · A/B/C 조건별 비교')
box(.015,.48,.58,.19,'325개 · 선택 영향에 안정적인 조합','세 처리조건 모두에서 결측 제외 전후\n5년 반복과 2020→2024 증감 방향 유지\n전체 신고 대표성이나 모든 시간 특징의 안정성을 뜻하지 않음')
box(.66,.48,.325,.19,'광안동 교통사고','선택 안정성 미충족 · 별도 비교 사례\n현장연구와 포장사업 근거로 검토\n325개 통과 사례로 표시하지 않음',ORANGE)
arrow((.4,.745),(.30,.68));arrow((.72,.745),(.81,.68))
box(.015,.255,.58,.145,'325개 안에서 별도로 확인한 시기 민감도','한 해씩 제외한 다섯 비교에서 최고시기 집합 유지\n최고계절 121개 / 최고월 33개 · C조건 달력일수당 접수')
arrow((.30,.48),(.30,.41))
ax.text(.03,.218,'두 수치는 병렬 조건이며, 121개 → 33개의 단계별 선별이 아님',fontsize=11,color='#506c75')
box(.015,.005,.97,.16,'후속 근거를 깊게 연결한 설명 사례','연산동·심정지, 부전동·교통사고는 325개 중의 사례. 광안동은 민감한 비교 사례.\n서비스·현장 근거의 확보 수준을 함께 판단하며 위험도·정책 우선순위를 뜻하지 않음')
ax.text(.67,.35,'유형별 추가 사례도 함께 유지\n주택화재 · 산악 · 수난\n최종 보고서에서 9개 사례 설명',fontsize=12,linespacing=1.7)
save(fig,'selection-evidence-flow')

names=['연산제3동','부전제2동'];picked=[]
fig,axs=plt.subplots(2,2,figsize=(13,8.6));fig.subplots_adjust(top=.83,bottom=.18,hspace=.60,wspace=.25)
fig.suptitle('2020년보다 2024년의 고령 주민은 늘고, 비중은 낮아짐',fontsize=20,weight='bold',y=.965)
fig.text(.125,.903,'각 연도 12월 말 주민 · 인원과 비중을 함께 읽기 · 두 동은 별도 공간 단위',fontsize=12)
for i,name in enumerate(names):
 rows=sorted([r for r in population['annual'] if r['candidateName']==name],key=lambda r:r['year']);assert len(rows)==5
 picked.extend([{k:r[k] for k in ['district','candidateName','candidateCode','year','referenceDate','total','age65Plus','age65PlusShare']} for r in rows])
 for j,(field,label,color) in enumerate([('age65Plus','65세 이상 주민 (명)',TEAL),('age65PlusShare','전체 주민 중 비중 (%)',ORANGE)]):
  ax=axs[i,j];vals=[r[field]*(100 if j else 1) for r in rows]
  ax.plot([r['year'] for r in rows],vals,'o-',color=color,lw=2.5,ms=6)
  for r,value in zip(rows,vals):ax.annotate(f'{value:.2f}%' if j else f'{int(value):,}명',(r['year'],value),xytext=(0,11),textcoords='offset points',ha='center',fontsize=11,color=color)
  ax.set(xticks=range(2020,2025),title=name.replace('제','')+' · '+('인원' if j==0 else '비중'),ylabel=label,ylim=(0,max(vals)*1.28))
  ax.grid(axis='y',alpha=.15)
fig.text(.125,.10,'자료: 기존 검증 annual 집계 재사용. 비중의 분모는 해당 동의 같은 연도 전체 주민이다.',fontsize=11)
fig.text(.125,.062,'신고자·환자의 나이나 교육 수요가 아니다. 전체 연령 구성은 웹에 별도 유지하며, 신고를 이 동에 배정하지 않는다.',fontsize=11)
fig.text(.125,.025,'동일 코드·명칭의 5년 비교이며, 코드 지속만으로 경계가 변하지 않았음을 새로 입증한 것은 아니다.',fontsize=10,color='#506c75')
save(fig,'population-count-and-share')
derived={'selection':{'universe':970,'rawNames':194,'types':5,'stable':stable,'parallelComparison':'광안동 교통사고','illustrativeStable':['연산동 심정지','부전동 교통사고']},'populationAnnual':picked,'inputHashes':{str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [P,S]}}
(N/'derivedplotdata.json').write_text(json.dumps(derived,ensure_ascii=False,indent=2),encoding='utf-8')
records=[{'id':'selection-evidence-flow','title':'부산 전체 비교에서 설명 사례까지','png':'figures/selection-evidence-flow.png','svg':'figures/selection-evidence-flow.svg','question':'970개에서325개의 의미와 최종 설명 사례는 어떻게 다른가?','unit':'지역명×유형 조합','period':'2020–2024','limit':'위험 순위·미래예측 아님; 계절121과월33은 병렬 조건'}, {'id':'population-count-and-share','title':'주민 인원과 비중은 다른 방향으로 변할 수 있다','png':'figures/population-count-and-share.png','svg':'figures/population-count-and-share.svg','question':'연산3동·부전2동65세 이상 주민의 인원과 비중은 어떻게 변했는가?','unit':'명·%','period':'2020–2024 각12월말','limit':'환자 연령 아님; 전체 연령 웹자료를 대체하지 않음'}]
for rec in records:rec['sha256']={ext:hashlib.sha256((N/rec[ext]).read_bytes()).hexdigest() for ext in ['png','svg']}
(N/'additional-visuals.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('2 figures and derived data saved')
