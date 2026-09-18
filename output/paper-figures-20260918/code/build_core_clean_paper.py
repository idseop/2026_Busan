"""Replot verified aggregates into clean and paper styles. No raw call reanalysis."""
from pathlib import Path
import csv, hashlib, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.text import Text
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/paper-figures-20260918'
BASE=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':13,'axes.unicode_minus':False,'svg.fonttype':'path','savefig.facecolor':'white','figure.facecolor':'white','xtick.labelsize':13,'ytick.labelsize':13,'axes.labelsize':14,'legend.fontsize':12.5})
SOURCES={}; CHECKS=[]; RECORDS=[]
def load(prefix):
 p=next(BASE.glob(prefix+'-*.csv'));SOURCES[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 with p.open(encoding='utf-8-sig',newline='') as h:return list(csv.DictReader(h))
def N(r,k='countP'):return int(float(r[k]))
def F(r,k):return float(r[k])
def test(k,v):CHECKS.append({'check':k,'pass':bool(v)});assert v,k
def sp(prefix):return next(BASE.glob(prefix+'-*.csv')).relative_to(ROOT).as_posix()
DIST=load('01'); TYPES=load('02'); DT=load('03'); DONG=load('07'); POP=load('08'); TIME=load('11')
P=sum(N(r) for r in DIST)
test('P district total',P==555786);test('P subtype total',sum(N(r) for r in TYPES)==P)
MANIFEST=ROOT/'data/processed/신고인구특성재정립-20260917/calls/manifest.json'
SOURCES[MANIFEST.relative_to(ROOT).as_posix()]=hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
M=json.loads(MANIFEST.read_text(encoding='utf-8')); STAGES={r['scope']:r['all'] for r in M['audit']}
STAGE_VALUES=[STAGES['A'],STAGES['B'],STAGES['C'],M['profileCount']]
test('A/B/C/P stages',STAGE_VALUES==[704689,579412,574662,555786])
def case(d,t='질병'):return next(r for r in DONG if r['rawDong']==d and r['type']=='구급' and r['subtype']==t)
def district_type(d,t):return N(next(r for r in DT if r['district']==d and r['type']=='구급' and r['subtype']==t))
def fig(h):return plt.figure(figsize=(180/25.4,h/25.4))
def axes_style(ax,style,grid='x'):
 for side in ['top','right']:ax.spines[side].set_visible(False)
 for side in ['left','bottom']:
  ax.spines[side].set_visible(style=='paper');ax.spines[side].set_color('black');ax.spines[side].set_linewidth(.8)
 ax.tick_params(axis='both',labelsize=13,width=.8,length=3 if style=='paper' else 0,color='black')
 if grid:ax.grid(axis=grid,color='#DCE1E5',lw=.45,alpha=.65);ax.set_axisbelow(True)
def save(f,folder,key,meta):
 assert not f.texts,'No figure title, subtitle, source or explanatory fig.text allowed'
 f.canvas.draw(); renderer=f.canvas.get_renderer();w,h=f.canvas.get_width_height();bad=[];fonts=[]
 for t in f.findobj(Text):
  if not t.get_visible() or not t.get_text().strip():continue
  fonts.append(t.get_fontsize()); b=t.get_window_extent(renderer)
  if b.x0<-.5 or b.y0<-.5 or b.x1>w+.5 or b.y1>h+.5:bad.append({'text':t.get_text(),'bounds':[b.x0,b.y0,b.x1,b.y1]})
 test(folder+'/'+key+' no text clipping',not bad);test(folder+'/'+key+' font minimum 12',min(fonts)>=12)
 folderp=OUT/folder;folderp.mkdir(parents=True,exist_ok=True)
 png=folderp/(key+'.png');svg=folderp/(key+'.svg')
 f.savefig(png,dpi=450);f.savefig(svg);plt.close(f)
 im=Image.open(png)
 RECORDS.append({'set':folder,'file':key,'width_mm':180,'height_mm':round(h/100*25.4,2),'minimum_font_pt':min(fonts),'png_pixels':list(im.size),'dpi':list(im.info.get('dpi',[])),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),'text_bounds_pass':not bad,**meta})

for folder,style,c1,c2,c3 in [('01-clean-original','original','#168B8A','#17324D','#E89335'),('02-paper-style','paper','#376C8A','#333333','#B97937')]:
 gray='#BBC8D1' if style=='original' else '#C5CDD2'
 plt.rcParams.update({'text.color':c2,'axes.labelcolor':c2,'xtick.color':c2,'ytick.color':c2})
 # 01: step labels and numbers only.
 f=fig(134);ax=f.add_axes([.04,.025,.92,.95]);ax.set(xlim=(0,1),ylim=(-.18,3.7));ax.axis('off')
 labs=['A  17항목 완전 기재','B  정상 처리','C  업무성 3종 제외','P  벌집제거 제외']
 for i,(label,v) in enumerate(zip(labs,STAGE_VALUES)):
  y=3-i;fill=(c1 if i==3 else '#EDF3F6') if style=='original' else 'white';edge='none' if style=='original' else c2
  ax.add_patch(FancyBboxPatch((.012,y),.976,.62,boxstyle='round,pad=.008,rounding_size=.015' if style=='original' else 'square,pad=.008',fc=fill,ec=edge,lw=.8))
  color='white' if style=='original' and i==3 else c2
  ax.text(.04,y+.31,label,fontsize=14,va='center',color=color)
  ax.text(.96,y+.31,f'{v:,}',fontsize=20,weight='bold',ha='right',va='center',color=color)
  if i<3:
   ax.annotate('',xy=(.24,y-.31),xytext=(.24,y-.055),arrowprops={'arrowstyle':'->','lw':1.2,'color':c1})
   ax.text(.50,y-.19,f'-{v-STAGE_VALUES[i+1]:,}',fontsize=12.5,ha='center',va='center',color=c2)
 save(f,folder,'01-inclusion-flow',{'sources':[MANIFEST.relative_to(ROOT).as_posix()],'data':[{'stage':k,'count':v} for k,v in zip(['A','B','C','P'],STAGE_VALUES)],'unit':'접수 기록 건','period':'2020~2024','definition':'A 선택17항목 완전기재·부산, B 정상처리, C 업무운행·훈련출동·구급차소독 제외, P 벌집제거 제외. 각 단계는 직전 단계의 부분집합.','caution':'독립 사건·환자 수 아님. 전체 신고 대표성 미입증. 2025년 미포함.'})
 # 02: subtype bars.
 rmain=[next(r for r in TYPES if r['type']=='구급' and r['subtype']==s) for s in ['질병','질병외','부상']]
 vals=[N(r) for r in rmain];vals.append(P-sum(vals));pct=np.array(vals)/P*100
 labs=['질병','질병외','부상','그 밖의\n67유형'];f=fig(115);ax=f.add_axes([.23,.19,.53,.76])
 ax.barh(range(4),pct,color=[c1,c2,c3,gray],height=.57)
 ax.set_yticks(range(4),labs);ax.invert_yaxis();ax.set(xlim=(0,42),xticks=[0,10,20,30,40]);ax.set_xlabel('전체 접수 중 비중 (%)',labelpad=12);axes_style(ax,style)
 for i,(v,q) in enumerate(zip(vals,pct)):ax.text(q+.9,i,f'{q:.2f}%\n{v:,}건',fontsize=12,va='center')
 save(f,folder,'02-busan-type-composition',{'sources':[sp('02')],'data':[{'subtype':l.replace('\n',' '),'count':v,'share_pct':q} for l,v,q in zip(labs,vals,pct)],'period':'2020~2024','denominator':P,'unit':'P 접수 기록 건 및 구성비 %','caution':'질병·질병외·부상은 구급 세부유형. 나머지67개 종별×세부유형 합산. 신고 분류는 환자 진단·사고 원인과 다름.'})
 # 03: 16 district bars, full total labels.
 dr=sorted(DIST,key=lambda r:-N(r));ds=[]
 for r in dr:
  v={'district':r['district'],'total':N(r)}
  for t in ['질병','질병외','부상']:v[t]=district_type(r['district'],t)
  v['나머지 유형']=v['total']-sum(v[t] for t in ['질병','질병외','부상']);ds.append(v)
 f=fig(194);ax=f.add_axes([.175,.10,.665,.795]);left=np.zeros(16)
 for t,col in zip(['질병','질병외','부상','나머지 유형'],[c1,c2,c3,gray]):
  v=np.array([r[t] for r in ds]);ax.barh(range(16),v,left=left,height=.58,color=col,label=t);left+=v
 ax.set_yticks(range(16),[r['district'] for r in ds]);ax.invert_yaxis();ax.set(xlim=(0,68000),xticks=[0,20000,40000,60000]);ax.set_xticklabels(['0','20,000','40,000','60,000']);ax.set_xlabel('접수 건수 (건)',labelpad=12);axes_style(ax,style)
 for i,r in enumerate(ds):ax.text(r['total']+750,i,f"{r['total']:,}",fontsize=12,va='center')
 ax.legend(ncol=4,loc='lower left',bbox_to_anchor=(-.21,1.025),frameon=False,handlelength=1,columnspacing=.75,handletextpad=.35)
 save(f,folder,'03-district-counts-types',{'sources':[sp('01'),sp('03')],'data':ds,'period':'2020~2024','denominator':P,'unit':'P 접수 기록 건','caution':'총접수 내림차순이며 위험 순위 아님. 각 세부유형은 구급. 나머지유형은 모든 기타 종별×유형.'})
 # 04: same subtype at both spatial levels; figures show count and within-dong share.
 cs=[case(s) for s in ['부전동','우동','좌동','다대동','모라동','주례동','금곡동']]
 ds=[{'district':r['district'],'gu_disease':district_type(r['district'],'질병'),'dong':r['rawDong'],'dong_disease':N(r),'dong_total':N(r,'regionTotalP'),'dong_share_pct':F(r,'shareRegionPct')} for r in cs]
 f=fig(174);ax=f.add_axes([.395,.115,.42,.83]);ax.set_xlim(0,48)
 for i,r in enumerate(ds):
  ax.barh(i,r['dong_share_pct'],height=.56,color=c1 if r['dong'] in ['다대동','금곡동'] else gray)
  ax.text(-2,i,f"{r['district']} 질병 {r['gu_disease']:,}건\n{r['dong']}",fontsize=13,ha='right',va='center')
  ax.text(r['dong_share_pct']+1,i,f"{r['dong_share_pct']:.1f}%\n{r['dong_disease']:,}건",fontsize=12,va='center')
 ax.set_yticks([]);ax.invert_yaxis();ax.set_xticks([0,10,20,30,40]);ax.set_xlabel('동 내 질병 비중 (%)',labelpad=12);axes_style(ax,style)
 save(f,folder,'04-district-dong-disease',{'sources':[sp('03'),sp('07')],'data':ds,'period':'2020~2024','denominator':'각 접수 원문 동의 P 전체','unit':'구 질병건수/동 질병건수/동내 질병비중','caution':'구·동 모두 구급 질병. 원문동명은 행정동 확정 배정 아님. 청록/파랑은 다대·금곡 주 사례 표시. 건수·비중은 정책 우선순위가 아님.'})
 # 05: only annual lines; sensitivity prose and blocks intentionally absent.
 f=fig(128);ax=f.add_axes([.13,.14,.82,.73]);years=list(range(2020,2025));ds=[]
 for d,col,dy in [('다대동',c1,13),('금곡동',c2,-22)]:
  r=case(d);v=[N(r,str(y)) for y in years];test(d+' annual sum '+style,sum(v)==N(r))
  ax.plot(years,v,'o-',color=col,lw=1.8,ms=6,label=d)
  for x,y in zip(years,v):ax.annotate(f'{y:,}',(x,y),xytext=(0,dy),textcoords='offset points',ha='center',fontsize=12,color=col)
  ds.append({'dong':d,**{str(y):N(r,str(y)) for y in years}})
 ax.set(xlim=(2019.8,2024.25),ylim=(0,1060),xticks=years,yticks=[0,250,500,750,1000]);ax.set_xlabel('연도',labelpad=10);ax.set_ylabel('질병 접수 건수 (건)',labelpad=10);axes_style(ax,style,'y')
 ax.legend(ncol=2,loc='lower right',bbox_to_anchor=(1,1.03),frameon=False,handlelength=1.8)
 save(f,folder,'05-annual-disease-counts',{'sources':[sp('07')],'data':ds,'period':'2020~2024','denominator':'P 조건의 각 연도 질병 접수 건수','unit':'접수 기록 건','removed':'종전 그림의 한 해 제외 순위·30조건 텍스트 블록 삭제; 연도별 선그림만 유지','caution':'동일인 재신고율·미래예측·인과효과 아님. 기간에 따른 원래 집계값을 표시.'})
 # 06: heatmap axes, cell values, peak outlines and a second metric axis.
 cases=[('다대동','질병'),('금곡동','질병'),('부전동','질병외'),('부전동','부상')];arr=[];ds=[]
 for d,t in cases:
  r=case(d,t);rr=[z for z in TIME if z['rawDong']==d and z['subtype']==t and z['type']=='구급' and z['scope']=='P' and z['dimension']=='hour']
  test(d+t+' hourly count '+style,sum(N(z,'count') for z in rr)==N(r))
  bins=[sum(N(z,'count') for z in rr if j*4<=N(z,'value')<(j+1)*4) for j in range(6)];v=np.array(bins)/N(r)*100;arr.append(v)
  ds.append({'dong':d,'subtype':t,'denominator':N(r),'hour4_counts':bins,'hour4_share_pct':v.tolist(),'night_share_pct':F(r,'night20to07Pct')})
 f=fig(151);ax=f.add_axes([.20,.17,.61,.67]);cmap=colors.LinearSegmentedColormap.from_list('heat',['#F0F5F8',c1]);im=ax.imshow(arr,aspect='auto',cmap=cmap,vmin=0,vmax=30)
 cax=f.add_axes([.20,.955,.61,.018]);cb=f.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,15,30]);cb.set_label('접수 비중 (%)',fontsize=14,labelpad=3);cb.ax.tick_params(labelsize=13,length=2,width=.8);cb.outline.set_visible(False)
 ax.set_xticks(range(6),['00–04','04–08','08–12','12–16','16–20','20–24'],rotation=35,ha='right');ax.set_yticks(range(4),[d+'\n'+t for d,t in cases]);ax.set_xlabel('시간대 (시)',labelpad=13);axes_style(ax,style,None)
 for i,row in enumerate(arr):
  for j,v in enumerate(row):ax.text(j,i,f'{v:.1f}',fontsize=12,ha='center',va='center',color='white' if v>22 else c2)
  ax.add_patch(Rectangle((np.argmax(row)-.47,i-.47),.94,.94,fill=False,ec=c3,lw=2))
 ax2=f.add_axes([.84,.17,.12,.67]);ax2.set(xlim=(0,1),ylim=(3.5,-.5));ax2.set_xticks([.5],['야간\n비중 (%)']);ax2.tick_params(axis='x',length=0,pad=13,labelsize=13);ax2.set_yticks([])
 for side in ax2.spines:ax2.spines[side].set_visible(False)
 for i,r in enumerate(ds):ax2.text(.5,i,f"{r['night_share_pct']:.1f}",fontsize=12.5,weight='bold',va='center',ha='center')
 save(f,folder,'06-dong-time-patterns',{'sources':[sp('07'),sp('11')],'data':ds,'period':'2020~2024','denominator':'각 원문동×구급세부유형 P 전체','unit':'접수 구성비 %','definition':'4시간대 비율과 별도 야간20:00~익일08:00직전 12시간 비율. 주황테두리는 통합 최다4시간대.','caution':'사고 원인·매년동일정점·교육 적정시간의 증거 아님. 검증 시간별 집계를 4시간으로 합산.'})
 # 07: resident age composition; small first segments have external value labels.
 names=['다대제1동','다대제2동','금곡동','부전제1동','부전제2동'];rr=[next(r for r in POP if r['year']=='2024' and r['candidateName']==s) for s in names]
 keys=['pct_0_14','pct_15_39','pct_40_64','pct_65plus'];cats=['0–14세','15–39세','40–64세','65세 이상'];ds=[]
 for r in rr:
  test(r['candidateName']+' age sum '+style,sum(N(r,'age_'+str(a)) for a in range(101))==N(r,'residentTotal'))
  ds.append({'candidate':r['candidateName'],'resident_total':N(r,'residentTotal'),**{k:F(r,k) for k in keys}})
 f=fig(157);ax=f.add_axes([.23,.115,.73,.755]);left=np.zeros(5)
 for index,(key,cat,col) in enumerate(zip(keys,cats,[gray,c1,c2,c3])):
  v=np.array([r[key] for r in ds]);ax.barh(range(5),v,left=left,height=.48,color=col,label=cat)
  for i,(st,z) in enumerate(zip(left,v)):
   ax.text(st+z/2,i-.36 if index==0 else i,f'{z:.1f}',ha='center',va='center',fontsize=12,color=c2 if index==0 or index==3 else 'white')
  left+=v
 ax.set_yticks(range(5),[f"{r['candidate']}\n{r['resident_total']:,}명" for r in ds]);ax.set(ylim=(4.6,-.7),xlim=(0,100),xticks=[0,25,50,75,100]);ax.set_xlabel('주민 연령 구성비 (%)',labelpad=12);axes_style(ax,style,None)
 ax.legend(ncol=2,loc='lower center',bbox_to_anchor=(.40,1.015),frameon=False,handlelength=1.1,columnspacing=1.6,handletextpad=.45)
 save(f,folder,'07-resident-age-composition',{'sources':[sp('08')],'data':ds,'period':'2024-12-31','denominator':'각 행정동 후보의 연말 주민등록인구','unit':'주민 명 및 연령 구성비 %','definition':'전체101연령을0~14/15~39/40~64/65세이상 네 구간으로 집계. 첫 구간 비율은 막대 위에 표시.','caution':'환자·신고자 연령·생활인구·연평균 인구 아님. 다대·부전 원문동 접수를 행정동에 배분하지 않음. 역사적 경계 일치 미확정.'})

metadata={'scope':'Verified aggregates re-expression; no raw call analysis; PNG/SVG only','font':'Malgun Gothic','width_mm':180,'requested_dpi':450,'fonts_pt':{'tick':13,'axis':14,'legend':12.5,'value_min':12},'sources':SOURCES,'checks':CHECKS,'outputs':RECORDS,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'visual_review':'pending'}
(OUT/'core-01-07-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# 01~07 그래프 전용판·논문 스타일판의 출처와 해석','','그림 안에는 단계 라벨·축·범례·수치만 남겼다. 제목·부제·설명·출처 문장을 포함하지 않는다. 폭180mm, PNG450dpi와 글자를 경로로 보존한 SVG. PDF는 생성하지 않았다.','', 'A: `01-clean-original/`. B: `02-paper-style/`. 각 폴더 동일 번호7장. A팔레트는 기존 청록·남색·주황, B팔레트는 #376C8A/#333333/#B97937이며 흰 배경·검정0.8pt 축·최소 그리드다.','']
for r in RECORDS[:7]:
 md += [f"## {r['file']}",'',f"- 기간: {r['period']}",f"- 단위: {r['unit']}",f"- 분모: {r.get('denominator','단계별 포함조건의 접수 합계')}",f"- 정의: {r.get('definition','같은 검증 집계의 범주·수치를 표시')}",f"- 해석상 주의: {r['caution']}",'- 원본: '+', '.join('`'+v+'`' for v in r['sources']),'']
md += ['## 공통 출처·제작 범위','','01~06 원자료는 부산소방재난본부2020~2024 신고접수자료이며 위의 검증 집계파일만 읽었다. 07은 행정안전부2024년12월말 주민등록인구의 기존 검증 집계다. P는 선택17항목 완전기재·부산·정상처리에서 업무운행/훈련출동/구급차소독/벌집제거를 제외한555,786건이다. 2025년은 포함하지 않았다. 모든 비율은 동일 기간 분자합계/분모합계다.','','05에서는 사용자 요청대로 기존 기간민감도·30조건 설명 블록을 삭제하고 연도별 선그림만 유지했다. 관련 분석 자체를 취소하거나 재계산한 것이 아니다.','','원본 기존PNG·HWP·PDF는 수정하지 않았다. 그림 안의 문장을 빼면서 빠진 분모·제외조건·주의사항은 본 문서와JSON에 보존한다. 실제 제출용 사용 시 필요한 설명을 그림 밖 캡션에 배치해야 한다.','','자동 검사: 표시 수치·연도합계·시간합계·101연령합계, 모든 글자12pt이상, 캔버스 밖 글자없음. 실제PNG 시각검토는 후속 기록한다.']
(OUT/'core-01-07-sources-and-captions.md').write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'status':'PASS','figures':len(RECORDS),'checks':len(CHECKS),'output':str(OUT)},ensure_ascii=False))
