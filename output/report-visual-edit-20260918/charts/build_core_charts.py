"""Report figures only: re-express verified aggregate CSV; never read raw calls."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
from matplotlib.patches import FancyBboxPatch,Rectangle,Patch

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
NAVY='#17324D'; TEAL='#168B8A'; ORANGE='#E89335'; GRAY='#BBC8D1'; PALE='#EAF2F5'
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':10,'axes.unicode_minus':False,'text.color':NAVY,'axes.labelcolor':NAVY,'xtick.color':NAVY,'ytick.color':NAVY,'svg.fonttype':'path','savefig.facecolor':'white'})
sources={}; checks=[]; charts=[]
def read(prefix):
 p=next(BASE.glob(prefix+'-*.csv')); sources[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def num(r,k):return float(r[k])
def n(r,k='countP'):return int(float(r[k]))
def check(label,ok):
 checks.append({'check':label,'pass':bool(ok)})
 assert ok,label
def frame(height,title,subtitle):
 f=plt.figure(figsize=(165/25.4,height/25.4));f.text(.045,.965,title,fontsize=13,weight='bold',va='top');f.text(.045,.892,subtitle,fontsize=9,va='top');return f
def footer(f,text,y=.035):f.text(.045,y,text,fontsize=8.5,va='bottom',linespacing=1.4)
def clean(ax,grid=True):
 for s in ax.spines.values():s.set_visible(False)
 ax.tick_params(axis='both',length=0)
 if grid:ax.grid(axis='x',color='#DBE3E9',lw=.6);ax.set_axisbelow(True)
def save(f,key,title,caption,rows,source_ids,denominator):
 f.savefig(OUT/(key+'.png'),dpi=300);f.savefig(OUT/(key+'.svg'));plt.close(f)
 with (OUT/(key+'.csv')).open('w',encoding='utf-8-sig',newline='') as h:
  w=csv.DictWriter(h,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 charts.append({'id':key,'title':title,'caption':caption,'sources':source_ids,'denominator':denominator,'width_mm':165,'png_dpi':300})

district=read('01'); types=read('02'); dt=read('03'); dong=read('07'); pop=read('08'); times=read('11')
P=sum(n(r) for r in district)
check('16 districts = 555786',P==555786);check('70 types = P',sum(n(r) for r in types)==P)
def type_n(d,t):return n(next(r for r in dt if r['district']==d and r['type']=='구급' and r['subtype']==t))
def case(d,t='질병'):return next(r for r in dong if r['rawDong']==d and r['type']=='구급' and r['subtype']==t)
def source(prefix):return str(next(BASE.glob(prefix+'-*.csv')).relative_to(ROOT)).replace('\\','/')

# 01: nested inclusion conditions, not a population representativeness claim.
mp=ROOT/'data/processed/신고인구특성재정립-20260917/calls/manifest.json';m=json.loads(mp.read_text(encoding='utf-8'))
sources[str(mp.relative_to(ROOT))]=hashlib.sha256(mp.read_bytes()).hexdigest()
audit={r['scope']:r['all'] for r in m['audit']}; vals=[audit['A'],audit['B'],audit['C'],m['profileCount']]
check('A B C P verified stages',vals==[704689,579412,574662,555786])
f=frame(104,'분석 조건을 맞춘 555,786건을 비교','2020~2024년 부산 119 신고접수 기록 · 단위: 건')
ax=f.add_axes([.045,.19,.91,.61]);ax.axis('off')
labels=['A  선택 17항목 완전 기재','B  정상 처리','C  업무성 기록 3종 제외','P  벌집제거 제외 · 주 분석']
for i,(v,l) in enumerate(zip(vals,labels)):
 y=3-i; col=TEAL if i==3 else NAVY
 ax.add_patch(FancyBboxPatch((0,y),1,.63,boxstyle='round,pad=0.02,rounding_size=.03',fc=col if i==3 else PALE,ec='none'))
 ax.text(.025,y+.315,l,va='center',fontsize=10,color='white' if i==3 else NAVY)
 ax.text(.97,y+.315,f'{v:,}',va='center',ha='right',fontsize=14,weight='bold',color='white' if i==3 else NAVY)
 if i<3:ax.text(.5,y-.19,f'↓ {v-vals[i+1]:,}건 제외',ha='center',va='center',fontsize=9,color=TEAL)
ax.set(xlim=(-.01,1.01),ylim=(-.1,3.72))
footer(f,'업무성 3종: 업무운행·훈련출동·구급차소독. 단위는 접수 기록이며 환자 수가 아님.')
save(f,'01-inclusion-flow','분석 포함·제외 조건','17항목 완전 기재 A에서 처리·업무성·벌집제거 조건을 순차 적용해 P 555,786건을 확보했다. 단계마다 분모가 다르다.',[{'stage':l,'count':v,'excluded_from_previous':0 if i==0 else vals[i-1]-v} for i,(l,v) in enumerate(zip(labels,vals))],[str(mp.relative_to(ROOT))],'각 단계는 직전 단계의 부분집합; 전체 모집단 대비 비율 미산출')

# 02: major subtypes and the remaining 67 subtype keys.
main=[next(r for r in types if r['type']=='구급' and r['subtype']==t) for t in ['질병','질병외','부상']]
rows=[{'type':r['type'],'subtype':r['subtype'],'count':n(r),'share_pct':100*n(r)/P} for r in main]
rows.append({'type':'합산','subtype':'그 밖의 67유형','count':P-sum(r['count'] for r in rows),'share_pct':100*(P-sum(r['count'] for r in rows))/P})
check('type chart composition 100%',abs(sum(r['share_pct'] for r in rows)-100)<1e-9)
f=frame(93,'질병·질병외·부상이 전체의 75.94%','2020~2024년 · 주 분석 P=555,786건 · 세부유형은 종별과 함께 구분')
ax=f.add_axes([.19,.26,.60,.52]);vals2=[r['share_pct'] for r in rows]
ax.barh(range(4),vals2,color=[TEAL,NAVY,ORANGE,GRAY],height=.6)
ax.set_yticks(range(4),[r['subtype'] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,42);ax.set_xticks([0,10,20,30,40],['0','10','20','30','40%']);clean(ax)
for i,r in enumerate(rows):ax.text(r['share_pct']+.8,i,f"{r['share_pct']:.2f}%  ({r['count']:,}건)",va='center',fontsize=9.5)
footer(f,'분모: 모든 P 유형 555,786건. 접수 유형은 환자 진단명·사고 원인과 다름.')
save(f,'02-busan-type-composition','부산 전체 주요 유형', '질병 190,682건(34.31%), 질병외 188,863건(33.98%), 부상 42,522건(7.65%)이다. 나머지는 종별·세부유형 키 67개의 합계다.',rows,[source('02')],'P 전체 555786건')

# 03: all districts, counts descending; direct total labels.
district.sort(key=lambda r:-n(r));rows=[]
for r in district:
 x={'district':r['district'],'total':n(r)}
 for t in ['질병','질병외','부상']:x[t]=type_n(r['district'],t)
 x['기타유형']=x['total']-sum(x[t] for t in ['질병','질병외','부상']);rows.append(x)
check('district type segments reconcile',all(sum(r[t] for t in ['질병','질병외','부상','기타유형'])==r['total'] for r in rows))
f=frame(151,'16개 구·군의 접수 규모와 유형 구성','2020~2024년 · P=555,786건 · 총 접수 건수순이며 위험 순위가 아님')
ax=f.add_axes([.17,.17,.70,.63]);left=np.zeros(16)
for k,c in zip(['질병','질병외','부상','기타유형'],[TEAL,NAVY,ORANGE,GRAY]):
 v=np.array([r[k] for r in rows]);ax.barh(range(16),v,left=left,height=.62,color=c,label=k);left+=v
ax.set_yticks(range(16),[r['district'] for r in rows]);ax.invert_yaxis();ax.set_xlim(0,68000);ax.set_xticks([0,20000,40000,60000],['0','2만','4만','6만 건']);clean(ax)
for i,r in enumerate(rows):ax.text(r['total']+650,i,f"{r['total']:,}",va='center',fontsize=9)
ax.legend(ncol=4,loc='lower left',bbox_to_anchor=(-.15,1.025),frameon=False,fontsize=9,handlelength=1,columnspacing=1.1)
footer(f,'상위 5개 구 합계 252,014건(45.34%). 한 해씩 제외해도 이 5개 구의 순서는 유지.')
save(f,'03-district-counts-types','16개 구·군 비교','동일한 P 조건에서 총 접수 건수순으로 정렬했다. 질병·질병외·부상과 나머지 유형을 구분하며, 막대의 길이를 지역 위험이나 대응 부족으로 해석하지 않는다.',rows,[source('01'),source('03')],'건수 막대; 유형별 합계=해당 구군 P 전체')

# 04: same disease subtype at district and raw-dong level.
cs=[case(s) for s in ['부전동','우동','좌동','다대동','모라동','주례동','금곡동']]
rows=[{'district':r['district'],'district_disease_count':type_n(r['district'],'질병'),'raw_dong':r['rawDong'],'dong_disease_count':n(r),'dong_P_total':n(r,'regionTotalP'),'dong_disease_pct':num(r,'shareRegionPct')} for r in cs]
check('dong proportions recomputed',all(abs(100*r['dong_disease_count']/r['dong_P_total']-r['dong_disease_pct'])<1e-8 for r in rows))
f=frame(123,'구의 질병 유형을 같은 유형의 동에서 확인','2020~2024년 · 주 분석 P · 동은 접수 원문 명칭')
ax=f.add_axes([.37,.22,.42,.57]);ax.set_xlim(0,47)
for i,r in enumerate(rows):
 col=TEAL if r['raw_dong'] in ['다대동','금곡동'] else GRAY
 ax.barh(i,r['dong_disease_pct'],height=.57,color=col)
 ax.text(-2,i,f"{r['district']} 질병 {r['district_disease_count']:,}건\n{r['raw_dong']}",ha='right',va='center',fontsize=9.5)
 ax.text(r['dong_disease_pct']+.7,i,f"{r['dong_disease_pct']:.1f}%\n{r['dong_disease_count']:,}건",va='center',fontsize=9.5)
ax.set_yticks([]);ax.invert_yaxis();ax.set_xticks([0,10,20,30,40],['0','10','20','30','40%']);clean(ax)
footer(f,'막대 분모: 해당 원문 동의 모든 P 유형. 청록색은 주 사례이며 행정동 확정 배정이 아님.')
save(f,'04-district-dong-disease','구에서 동으로 이어지는 동일 유형 비교','구에서 질병을 선택한 뒤 동에서도 질병을 유지했다. 다대 4,054건/10,952건(37.0%), 금곡 3,615건/9,293건(38.9%)이며 주민·보건·기존 대응과 연결해 심화한다.',rows,[source('03'),source('07')],'각 원문 동의 P 전체. 구 질병 건수는 비교 경로를 나타내는 별도 규모')

# 05: annual counts with year-omission and composition sensitivity summaries.
cs=[case('다대동'),case('금곡동')];f=frame(124,'다대·금곡의 질병 특성은 기간 변경에도 확인','2020~2024년 · P 조건 연도별 질병 접수 · 단위: 건')
ax=f.add_axes([.12,.42,.80,.38]);ys=list(range(2020,2025));rows=[]
for r,c,dy in zip(cs,[TEAL,NAVY],[22,-35]):
 v=[n(r,str(y)) for y in ys];ax.plot(ys,v,'o-',lw=2,color=c,label=r['rawDong'])
 for y,z in zip(ys,v):ax.annotate(f'{z:,}',(y,z),xytext=(0,10 if dy>0 else -16),textcoords='offset points',ha='center',fontsize=9,color=c)
 rows.append({'raw_dong':r['rawDong'],**{str(y):n(r,str(y)) for y in ys},'pooled_total':n(r),'gu_rank_best_without_year':n(r,'withinDistrict_withoutYearBestRank'),'gu_rank_worst_without_year':n(r,'withinDistrict_withoutYearWorstRank'),'city_rank_best_without_year':n(r,'withoutYearBestRank'),'city_rank_worst_without_year':n(r,'withoutYearWorstRank'),'above_rest_busan_conditions':n(r,'aboveRestBusan30'),'above_rest_gu_conditions':n(r,'aboveRestDistrict30'),'comparable_conditions':30})
check('case annual sums match totals',all(sum(r[str(y)] for y in ys)==r['pooled_total'] for r in rows))
ax.set(xlim=(2019.85,2024.2),ylim=(0,1030),xticks=ys,yticks=[0,250,500,750,1000]);clean(ax,False);ax.grid(axis='y',color='#DBE3E9',lw=.6);ax.legend(ncol=2,loc='upper right',bbox_to_anchor=(1,1.19),frameon=False,fontsize=10)
f.text(.06,.32,'한 해 제외 시 구내 질병 건수순',fontsize=9.5);f.text(.61,.32,'다대 1위 · 금곡 1위',fontsize=10,weight='bold')
f.text(.06,.265,'한 해 제외 시 부산 동명 간 건수순',fontsize=9.5);f.text(.61,.265,'다대 4~6위 · 금곡 8~10위',fontsize=9.5)
f.text(.06,.21,'두 동 모두 비교집단보다 구성비 높음',fontsize=9.5);f.text(.68,.21,'부산·구 각각 30/30',fontsize=9.5,weight='bold',color=TEAL)
footer(f,'30조건 = 결측조건 2개 × 처리조건 3개 × 5개년. 독립검정 30회나 재신고율이 아님.')
save(f,'05-recurrence-sensitivity','다대·금곡의 연도별 접수와 민감도','다대·금곡은 모든 연도에 질병 접수가 관측되고 한 해를 제외해도 구내 질병 접수 1위를 유지한다. 구성비의 방향은 두 비교집단에서 각각 30조건 모두 유지된다. 이는 독립 검정이나 미래 예측이 아니다.',rows,[source('07')],'연도별 P 질병 건수; 30조건=core8/complete17 × A/B/C ×5년 (각 조건 벌집제거 제외)')

# 06: equal 4-hour bins from verified hourly aggregates.
cases=[('다대동','질병'),('금곡동','질병'),('부전동','질병외'),('부전동','부상')];data=[];rows=[]
for d,t in cases:
 r=case(d,t);rr=[x for x in times if x['rawDong']==d and x['subtype']==t and x['type']=='구급' and x['scope']=='P' and x['dimension']=='hour'];check(f'{d} {t} hourly sum',sum(n(x,'count') for x in rr)==n(r))
 bins=[sum(n(x,'count') for x in rr if j*4<=n(x,'value')<(j+1)*4) for j in range(6)];pct=[v*100/n(r) for v in bins];data.append(pct)
 check(f'{d} {t} peak matches',int(np.argmax(bins))==n(r,'hour4Peak'))
 for j,(v,p) in enumerate(zip(bins,pct)):rows.append({'raw_dong':d,'subtype':t,'hours':f'{j*4:02d}-{(j+1)*4:02d}','count':v,'denominator':n(r),'share_pct':p,'night_20to08_pct':num(r,'night20to07Pct')})
f=frame(108,'질병과 대조 유형의 최다 시간대는 다르다','2020~2024년 P · 셀은 해당 동·유형 전체 접수 중 4시간대 비율(%)')
ax=f.add_axes([.23,.28,.58,.49]);cmap=colors.LinearSegmentedColormap.from_list('teal',['#F1F7F7',TEAL]);ax.imshow(data,aspect='auto',cmap=cmap,vmin=0,vmax=30)
ax.set_xticks(range(6),['00~04','04~08','08~12','12~16','16~20','20~24'],fontsize=9);ax.set_yticks(range(4),[f'{d}\n{t}' for d,t in cases],fontsize=10);clean(ax,False)
for i,row in enumerate(data):
 for j,v in enumerate(row):ax.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=10,color='white' if v>19 else NAVY)
 ax.add_patch(Rectangle((np.argmax(row)-.47,i-.47),.94,.94,fill=False,ec=ORANGE,lw=2.4))
 r=case(*cases[i]);ax.text(6.0,i,f"{num(r,'night20to07Pct'):.1f}%",va='center',fontsize=10,weight='bold')
ax.text(6,.5,'',transform=ax.transAxes)
f.text(.885,.81,'야간 비중',fontsize=9,ha='center');f.text(.885,.77,'20~익일08시',fontsize=8,ha='center')
footer(f,'주황 테두리: 통합 최다 4시간대. 야간은 12시간이며 사고 원인·적정 운영시간을 뜻하지 않음.')
save(f,'06-dong-time-patterns','동·유형별 4시간대 접수 구성','다대·금곡 질병은 08~12시, 부전 질병외·부상은 20~24시에 통합 접수가 가장 많다. 부전 야간 비중은 질병외 47.76%, 부상 55.09%로 구별된다.',rows,[source('07'),source('11')],'각 원문 동×유형의 5년 P 접수 합계; 동일 길이 4시간 구간')

# 07: resident background, never patient ages or raw-dong allocation.
names=['다대제1동','다대제2동','금곡동','부전제1동','부전제2동'];rr=[next(r for r in pop if r['year']=='2024' and r['candidateName']==s) for s in names]
keys=['pct_0_14','pct_15_39','pct_40_64','pct_65plus'];cats=['0~14세','15~39세','40~64세','65세 이상'];cols=[GRAY,TEAL,NAVY,ORANGE]
rows=[{'candidate':r['candidateName'],'raw_dong':r['rawDong'],'resident_total':n(r,'residentTotal'),**{k:num(r,k) for k in keys}} for r in rr]
check('resident shares sum100',all(abs(sum(r[k] for k in keys)-100)<1e-8 for r in rows))
check('resident whole-age counts match',all(sum(n(r,'age_'+str(a)) for a in range(101))==n(r,'residentTotal') for r in rr))
f=frame(104,'주민 연령은 지역 배경으로 비교','2024년 12월 31일 · 주민 행정동 후보별 연령 구성(%)')
ax=f.add_axes([.20,.28,.73,.47]);left=np.zeros(5)
for key,cat,col in zip(keys,cats,cols):
 v=np.array([r[key] for r in rows]);ax.barh(range(5),v,left=left,height=.58,color=col,label=cat)
 for i,(st,z) in enumerate(zip(left,v)):ax.text(st+z/2,i,f'{z:.1f}',ha='center',va='center',fontsize=9,color='white' if col in [TEAL,NAVY] else NAVY)
 left+=v
ax.set_yticks(range(5),[f"{r['candidate']}\n{r['resident_total']:,}명" for r in rows],fontsize=9.5);ax.invert_yaxis();ax.set_xlim(0,100);ax.set_xticks([0,25,50,75,100],['0','25','50','75','100%']);clean(ax,False)
ax.legend(ncol=4,loc='lower left',bbox_to_anchor=(-.15,1.055),frameon=False,fontsize=9,handlelength=1,columnspacing=1.4)
footer(f,'분모: 각 후보의 연말 주민. 신고자·환자 연령이 아니며 다대동 접수를 다대1·2에 배분하지 않음.')
save(f,'07-resident-age-composition','주 사례와 대조 사례의 주민 구성','다대1·2와 금곡은 주민 연령 배경을, 부전1·2는 다른 연령 구성의 대조를 보여준다. 101개 연령을 네 구간으로 표시한 것으로 신고 당사자의 연령을 뜻하지 않는다.',rows,[source('08')],'2024-12-31 각 후보 주민 수; 101연령 집계; 시구 합계 중복 제외')

validation={'status':'PASS','scope':'verified aggregates re-expression only; no raw-call analysis','sources':sources,'checks':checks,'charts':charts,'render_review':'pending visual review','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'core-chart-verification.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# 보고서 삽입용 핵심 분석 차트 01~07','', '폭 165mm, 맑은 고딕, 본문 9~10pt·제목 13pt. PNG 300dpi와 글자를 경로로 보존한 SVG. PDF는 생성하지 않았다. 기존 검증 집계를 재표현했으며 원시 신고를 재분석하지 않았다.','']
for ch in charts:
 md += [f"## {ch['id']} · {ch['title']}",'',ch['caption'],'',f"- 삽입 파일: `{ch['id']}.png` / `{ch['id']}.svg`",f"- 표시용 집계: `{ch['id']}.csv`",f"- 분모·정의: {ch['denominator']}",'- 원본: '+', '.join('`'+s+'`' for s in ch['sources']),'']
md += ['## 공통 편집 메모','','PNG는 폭165mm로 삽입하고 가로·세로 비율을 유지한다. 그림의 제목·주석이 포함되므로 같은 내용을 본문에서 반복하지 않아도 된다. 16구 비교 그림03의 높이는151mm로 다른 그림보다 크다. 실제 문서에 삽입한 뒤 쪽 나눔과 인쇄 가독성은 별도 확인해야 한다.','', '색상: 남색 #17324D, 청록 #168B8A, 주황 #E89335, 보조 회색 #BBC8D1.','', '검증: core-chart-verification.json에 입력 SHA-256, 합계·비중·시간·주민 연령 검산을 기록했다. 시각 검토 결과는 별도 추가한다.']
(OUT/'core-chart-captions.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':'PASS','figures':len(charts),'checks':len(checks),'output':str(OUT)},ensure_ascii=False))
