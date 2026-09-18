from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors, ticker
from matplotlib.lines import Line2D

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/journal-hwp-20260918'
FIG=OUT/'figures';FIG.mkdir(parents=True,exist_ok=True)
META=OUT/'metadata';META.mkdir(exist_ok=True)
DATA=OUT/'display-data';DATA.mkdir(exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':11.5,'axes.labelsize':12,
 'xtick.labelsize':10.5,'ytick.labelsize':11,'legend.fontsize':11,'axes.linewidth':.65,
 'axes.edgecolor':'#3D4247','text.color':'#283238','axes.labelcolor':'#283238',
 'xtick.color':'#3D4247','ytick.color':'#3D4247','axes.unicode_minus':False,
 'svg.fonttype':'path','figure.facecolor':'white','savefig.facecolor':'white'})
TEAL='#197C80';ORANGE='#CA6A38';PURPLE='#7D6B91';GRAY='#B4BCC0'
sources={};records=[]
def read(p):
 sources[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return pd.read_csv(p)
def style(ax,grid='y'):
 ax.spines[['top','right']].set_visible(False)
 ax.tick_params(length=3,width=.65,pad=4)
 if grid:ax.grid(axis=grid,color='#E7EAEB',lw=.45);ax.set_axisbelow(True)
def letter(f,s,x,y):f.text(x,y,s,fontfamily='Arial',fontsize=17,weight='bold',va='top')
def save(f,name,meta):
 assert not f._suptitle and all(not a.get_title() for a in f.axes)
 f.canvas.draw();rr=f.canvas.get_renderer();outside=[]
 for t in f.findobj(matplotlib.text.Text):
  if not t.get_visible() or not t.get_text():continue
  bb=t.get_window_extent(rr)
  if bb.width and bb.height and (bb.x0<-.5 or bb.y0<-.5 or bb.x1>f.bbox.width+.5 or bb.y1>f.bbox.height+.5):outside.append(t.get_text())
 assert not outside,(name,outside)
 f.savefig(FIG/(name+'.png'),dpi=500)
 f.savefig(FIG/(name+'.svg'))
 records.append({'figure':name,**meta,'png_sha256':hashlib.sha256((FIG/(name+'.png')).read_bytes()).hexdigest(),'text_inside_canvas':True})
 plt.close(f)

base=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
tp=next(base.glob('11-*.csv'));t=read(tp)
s=t[(t.scope=='P')&(t.type=='구급')&(t.subtype=='질병')&(t.rawDong.isin(['다대동','금곡동']))].copy()
joint=[];hour=[];month=[]
for dong,n in [('다대동',4054),('금곡동',3615)]:
 q=s[(s.rawDong==dong)&(s.dimension=='weekdayHour')].sort_values('value')
 assert len(q)==168 and q['count'].sum()==n and q.denominator.eq(n).all()
 m=q['count'].to_numpy().reshape(7,24);joint.append(m/n*100);hour.append(m.sum(axis=0)/n*100)
 mo=s[(s.rawDong==dong)&(s.dimension=='month')].sort_values('value')
 assert mo['count'].sum()==n and np.allclose(mo.receiptsPerCalendarDay,mo['count']/mo.calendarDays)
 month.append(mo.receiptsPerCalendarDay.to_numpy())
s.to_csv(DATA/'03-time-source.csv',index=False,encoding='utf-8-sig')
f=plt.figure(figsize=(7.1,8.7))
cmap=colors.LinearSegmentedColormap.from_list('teal_density',['#F7F9F9','#A7CDCE',TEAL,'#164F55'])
vmax=np.ceil(max(a.max() for a in joint)*2)/2
for i,(x,dong,n,col) in enumerate([( .10,'다대동',4054,TEAL),(.59,'금곡동',3615,ORANGE)]):
 letter(f,'ab'[i],x-.075,.973)
 top=f.add_axes([x,.889,.285,.068]);v=hour[i]
 top.fill_between(range(24),0,v,color=col,alpha=.14);top.plot(range(24),v,color=col,lw=1.3)
 top.set(xlim=(-.5,23.5),ylim=(0,8),yticks=[0,6]);top.set_xticks([]);top.set_ylabel('%',rotation=0,labelpad=6,fontsize=10.5);style(top,None)
 top.text(.5,1.15,f'{dong} · n={n:,}',transform=top.transAxes,ha='center',fontsize=12)
 ax=f.add_axes([x,.678,.285,.199]);im=ax.imshow(joint[i],aspect='auto',origin='upper',cmap=cmap,vmin=0,vmax=vmax,interpolation='nearest')
 ax.set_xticks([0,6,12,18,23],['0','6','12','18','23']);ax.set_yticks(range(7),['월','화','수','목','금','토','일'])
 ax.set_xlabel('시각 (시)',labelpad=5,fontsize=11);ax.tick_params(length=0,pad=4)
 for sp in ax.spines.values():sp.set_visible(False)
 side=f.add_axes([x+.30,.678,.055,.199]);side.barh(range(7),joint[i].sum(axis=1),color=col,height=.68)
 side.set(ylim=(6.5,-.5),xlim=(0,18),xticks=[15],yticks=[]);side.tick_params(axis='x',labelsize=9.5,length=2);side.set_xlabel('%',fontsize=10,labelpad=3)
 for sp in side.spines.values():sp.set_visible(False)
cbax=f.add_axes([.285,.594,.43,.013]);cb=f.colorbar(im,cax=cbax,orientation='horizontal',ticks=[0,.5,1,1.5])
cb.set_label('질병 접수 비중 (%)',labelpad=3,fontsize=10.5);cb.outline.set_visible(False);cb.ax.tick_params(length=2,labelsize=10)
letter(f,'c',.025,.514)
ax=f.add_axes([.11,.328,.84,.178]);xx=np.arange(24)
for vals,name,col in zip(hour,['다대동','금곡동'],[TEAL,ORANGE]):
 ax.plot(xx,vals,color=col,lw=1.8,label=name,marker='o',markevery=4,ms=4)
ax.set(xlim=(0,23),ylim=(0,8),xticks=[0,4,8,12,16,20,23],yticks=[0,2,4,6,8],ylabel='시간별 구성비 (%)',xlabel='시각 (시)')
style(ax);ax.legend(frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.5,1.15),handlelength=1.7)
letter(f,'d',.025,.238)
ax=f.add_axes([.11,.075,.84,.159])
for vals,name,col,mark in zip(month,['다대동','금곡동'],[TEAL,ORANGE],['o','s']):
 ax.plot(range(1,13),vals,color=col,lw=1.5,marker=mark,ms=4,label=name)
ax.set(xlim=(.7,12.3),xticks=list(range(1,13)),xlabel='월',ylabel='일평균 접수 (건/일)',ylim=(0,3.1),yticks=[0,1,2,3]);style(ax)
save(f,'03-temporal-joint-profile',{'period':'2020–2024','type':'구급/질병','denominators':{'다대동':4054,'금곡동':3615},'panels':{'a_b':'168셀 공동분포 및 동일 분모의 시간·요일 주변분포; 공통 색상 범위','c':'질병접수의 시간별 구성비','d':'해당 달의 5개년 접수/해당 달의 실제 달력일수'},'cautions':['접수시각은 교육 적정시간이나 사고 발생시각의 증거가 아님','원문동명 집계, 행정동 임의배분 없음','추세·공동분포에 확률분포 추정이나 가짜 신뢰구간 없음']})

cp=ROOT/'data/processed/신고주민연결심화-20260917/direction-connections/major-burden-commerce-20quarters.csv'
c=read(cp);q=c[(c.level=='lawDong')&(c.district=='부산진구')&(c.lawDong=='부전동')].copy()
assert len(q)==200 and q.snapshot.nunique()==20 and q.category.nunique()==10 and q.dictionarySignature.nunique()==1
assert np.allclose(q.sharePct,q.shops/q.denominatorShops*100)
snaps=sorted(q.snapshot.unique());order=q[q.snapshot==snaps[-1]].sort_values('sharePct',ascending=False).category.tolist()
wide=q.pivot(index='category',columns='snapshot',values='sharePct').loc[order,snaps]
delta=wide.subtract(wide.iloc[:,0],axis=0)
q.to_csv(DATA/'06-commerce-source.csv',index=False,encoding='utf-8-sig')
delta.to_csv(DATA/'06-commerce-change-pp.csv',encoding='utf-8-sig')
lp=ROOT/'data/processed/통합완성-20260916/context/living-hour-annual-equal-month-means.csv'
l=read(lp);v=l[l.year.isin([2023,2024])&l['행정동코드'].isin([2623051000,2623052000])].copy()
v['hour']=v['시간대'].str.replace('시','').astype(int);v=v.sort_values(['행정동코드','year','hour'])
assert len(v)==96 and v.observedMonths.eq(12).all() and v.nameMissing.eq(False).all()
v.to_csv(DATA/'06-visitors-source.csv',index=False,encoding='utf-8-sig')
f=plt.figure(figsize=(7.1,8.7));letter(f,'a',.025,.972)
ax=f.add_axes([.20,.634,.56,.314]);lim=max(abs(delta.to_numpy()).max(),.1)
cmap=colors.LinearSegmentedColormap.from_list('diverging',[TEAL,'#F8F8F6',ORANGE])
im=ax.imshow(delta,aspect='auto',cmap=cmap,norm=colors.TwoSlopeNorm(0,-lim,lim),interpolation='nearest')
ax.set_yticks(range(10),order);ax.tick_params(length=0,pad=4,labelsize=10.5)
ax.set_xticks([0,4,8,12,16,19],['2020\nQ1','2021\nQ1','2022\nQ1','2023\nQ1','2024\nQ1','Q4'])
ax.set_xticks(np.arange(-.5,20,1),minor=True);ax.set_yticks(np.arange(-.5,10,1),minor=True);ax.grid(which='minor',color='white',lw=.6);ax.tick_params(which='minor',length=0)
for sp in ax.spines.values():sp.set_visible(False)
right=f.add_axes([.802,.634,.158,.314]);yy=np.arange(10);vals=wide.iloc[:,-1].to_numpy()
right.hlines(yy,0,vals,color='#D6DDE0',lw=2);right.scatter(vals,yy,s=25,color=TEAL,zorder=3)
right.set(ylim=(9.5,-.5),xlim=(0,36),xticks=[0,15,30],yticks=[])
right.set_xlabel('2024 Q4\n구성비 (%)',fontsize=10.5,labelpad=5);style(right,'x');right.spines['left'].set_visible(False)
cbax=f.add_axes([.24,.536,.48,.013]);cb=f.colorbar(im,cax=cbax,orientation='horizontal',ticks=[-1,0,1]);cb.set_label('2020 Q1 대비 상가 구성비 차이 (%p)',labelpad=4,fontsize=11);cb.outline.set_visible(False);cb.ax.tick_params(labelsize=10,length=2)
letter(f,'b',.025,.452);letter(f,'c',.51,.452)
for i,(code,name,col) in enumerate([(2623051000,'부전1동',TEAL),(2623052000,'부전2동',PURPLE)]):
 x=.11 if i==0 else .60
 ax=f.add_axes([x,.233,.355,.199]);diffax=f.add_axes([x,.079,.355,.087])
 ys=[]
 for year,ls,mark in [(2023,'--','o'),(2024,'-','s')]:
  z=v[(v['행정동코드']==code)&(v.year==year)].sort_values('hour');y=z['평균방문인구수'].to_numpy();ys.append(y)
  ax.plot(range(24),y/1000,color=col,ls=ls,lw=1.5,marker=mark,markevery=6,ms=3.5,mfc='white' if year==2023 else col)
  peak=np.argmax(y);ax.scatter([peak],[y[peak]/1000],s=40,facecolors='white',edgecolors=col,zorder=5)
 ax.set(xlim=(0,23),ylim=(0,35),xticks=[0,6,12,18,23],yticks=[0,10,20,30],ylabel='방문인구 추정값 (천 명)' if i==0 else None)
 ax.text(.5,1.075,name,transform=ax.transAxes,ha='center',color=col,fontsize=12)
 style(ax);ax.set_xticklabels([])
 delta=(ys[1]-ys[0])/1000
 diffax.axhline(0,color='#6C7478',lw=.75)
 diffax.fill_between(range(24),0,delta,where=delta>=0,color=ORANGE,alpha=.7,interpolate=True)
 diffax.fill_between(range(24),0,delta,where=delta<0,color=TEAL,alpha=.65,interpolate=True)
 diffax.plot(range(24),delta,color='#4B555B',lw=.7)
 diffax.set(xlim=(0,23),ylim=(-1.5,1),yticks=[-1,0,1],xticks=[0,6,12,18,23],xlabel='시각 (시)',ylabel='2024–2023\n차이 (천 명)' if i==0 else None);style(diffax,None)
handles=[Line2D([0],[0],color='#4B555B',ls='--',marker='o',mfc='white',ms=4,label='2023'),Line2D([0],[0],color='#4B555B',ls='-',marker='s',ms=4,label='2024')]
f.legend(handles=handles,frameon=False,ncol=2,loc='center',bbox_to_anchor=(.53,.477),fontsize=11,handlelength=2.1,columnspacing=1.5)
save(f,'06-commerce-visitation-profile',{'periods':{'commerce':'2020Q1–2024Q4','visitors':'2023/2024, 각각 12개월 동일가중평균'},'panels':{'a':'법정동 부전동 10업종: 각 분기 비중-2020Q1 비중(%p), 우측 2024Q4 비중','b_c':'부전1·2 행정동 후보별 시간당 방문인구 추정 월평균. 큰 빈 원은 각 연도 시간대 정점, 하단은 2024-2023 평균값 차이'},'cautions':['행정동 방문인구를 법정동 신고의 당사자수로 해석하지 않음','상가 단면 스냅숏으로 업소 패널 아님','차이 채색은 불확실성 구간이 아님','2025 제외']})
(META/'time-context.json').write_text(json.dumps({'sources':sources,'figures':records,'status':'PASS'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':len(records),'files':[r['figure'] for r in records]},ensure_ascii=False))
