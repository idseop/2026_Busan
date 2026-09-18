"""Title-free publication figures from existing, validated aggregate results."""
from pathlib import Path
import json, hashlib, calendar
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors, ticker

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/paper-figures-20260918'
FIG=OUT/'02-paper-style'; FIG.mkdir(parents=True,exist_ok=True)
META=OUT/'metadata'; META.mkdir(exist_ok=True)
DATA=OUT/'display-data'; DATA.mkdir(exist_ok=True)
BASE=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':13,'axes.labelsize':14,
 'xtick.labelsize':13,'ytick.labelsize':13,'legend.fontsize':12.5,'axes.linewidth':.8,
 'text.color':'#222222','axes.edgecolor':'#333333','axes.labelcolor':'#222222',
 'xtick.color':'#333333','ytick.color':'#333333','axes.unicode_minus':False,
 'svg.fonttype':'path','figure.facecolor':'white','savefig.facecolor':'white'})
BLUE='#376C8A';DARK='#333333';ORANGE='#B97937';LIGHT='#CBD0D4'
sources={};checks=[];records=[]
def read(p):
 sources[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 return pd.read_csv(p)
def ck(name,ok):
 checks.append({'name':name,'pass':bool(ok)});assert ok,name
def style(ax,grid='y'):
 ax.spines[['top','right']].set_visible(False)
 ax.tick_params(length=3,width=.8,pad=6)
 if grid:ax.grid(axis=grid,lw=.45,color='#E2E2E2');ax.set_axisbelow(True)
def fig(height=125):return plt.subplots(figsize=(180/25.4,height/25.4),layout='constrained')
def save(f,name,df,caption,paths,denom):
 ck(name+' has no figure title',not f._suptitle and all(not a.get_title() for a in f.axes))
 texts=[(t.get_text(),t.get_fontsize()) for t in f.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text()]
 ck(name+' has no prose annotation',not any(len(t)>48 for t,_ in texts))
 f.savefig(FIG/(name+'.png'),dpi=450,bbox_inches='tight',pad_inches=.06)
 f.savefig(FIG/(name+'.svg'),bbox_inches='tight',pad_inches=.06)
 df.to_csv(DATA/(name+'.csv'),encoding='utf-8-sig',index=False)
 records.append({'id':name,'caption_outside_figure':caption,'sources':paths,'denominator':denom,
                 'font_sizes':sorted(set(s for _,s in texts)),'visible_labels':[t for t,_ in texts]})
 plt.close(f)

dp=next(BASE.glob('01-*.csv'));tp=next(BASE.glob('02-*.csv'));dtp=next(BASE.glob('03-*.csv'))
district=read(dp).sort_values('countP',ascending=False);types=read(tp);dt=read(dtp)
ck('district total P',district.countP.sum()==555786)
names=['질병','질병외','부상','나머지 유형']
rows=[]
for _,r in district.iterrows():
 v=dt[(dt.district==r.district)&(dt.type=='구급')].set_index('subtype').countP
 vals=[int(v[x]) for x in names[:3]];vals.append(int(r.countP)-sum(vals))
 rows.append({'district':r.district,'total':int(r.countP),**dict(zip(names,vals))})
d=pd.DataFrame(rows)
ck('all district type totals',np.all(d[names].sum(axis=1).values==d.total.values))
f,ax=fig(186);left=np.zeros(16)
for name,col,hatch in zip(names,[BLUE,DARK,ORANGE,LIGHT],['','','','']):
 vals=d[name]/d.total*100
 ax.barh(d.district,vals,left=left,height=.66,color=col,label=name,edgecolor='white',linewidth=.35)
 left+=vals
ax.invert_yaxis();ax.set(xlim=(0,100),xlabel='구·군 내 접수 비중 (%)')
ax.set_xticks([0,25,50,75,100]);style(ax,'x')
ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.43,1.01),frameon=False,columnspacing=.85,handlelength=1.2)
save(f,'11-district-type-proportions',d,'2020~2024년 주 분석 555,786건을 구·군 내 유형 비중으로 재표현했다. 구·군은 총건수순이며 위험도순이 아니다.',[dp.relative_to(ROOT).as_posix(),dtp.relative_to(ROOT).as_posix()],'각 구·군의 주 분석 전체 접수')

years=list(range(2020,2025));rows=[];f,ax=fig(124)
for name,col,marker in zip(names[:3],[BLUE,DARK,ORANGE],['o','s','^']):
 r=types[(types.type=='구급')&(types.subtype==name)].iloc[0]
 vals=[int(r[str(y)]) for y in years];ck(name+' annual sum',sum(vals)==int(r.countP))
 ax.plot(years,vals,color=col,marker=marker,markersize=6,lw=1.6,label=name)
 rows.extend([{'year':y,'subtype':name,'count':v} for y,v in zip(years,vals)])
ax.set(xlabel='연도',ylabel='접수 건수 (건)',ylim=(0,50000),xticks=years)
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'));style(ax)
ax.legend(ncol=3,loc='lower center',bbox_to_anchor=(.5,1.01),frameon=False)
save(f,'12-annual-receipts-by-type',pd.DataFrame(rows),'주 분석 조건의 2020~2024년 연도별 접수다. 결측 제외와 접수경로 구성의 영향을 받으므로 부산 전체 사고·환자 수의 변화로 확대하지 않는다.',[tp.relative_to(ROOT).as_posix()],'각 연도, 선택 17항목 완전 기재·정상·업무성 기록·벌집제거 제외 접수')

tim=next(BASE.glob('11-*.csv'));t=read(tim)
s=t[(t.scope=='P')&(t.dimension=='weekdayHour')&(t.type=='구급')&(t.subtype=='질병')&(t.rawDong.isin(['다대동','금곡동']))].copy()
cases=['다대동','금곡동'];matrices=[]
for name,expected in zip(cases,[4054,3615]):
 ss=s[s.rawDong==name].sort_values('value');ck(name+' weekdayHour cells',len(ss)==168 and ss.value.nunique()==168)
 ck(name+' weekdayHour count',ss['count'].sum()==expected and ss.denominator.eq(expected).all())
 ck(name+' weekdayHour shares',np.allclose(ss.sharePct,100*ss['count']/ss.denominator))
 matrices.append(ss.sharePct.to_numpy().reshape(7,24))
cmap=colors.LinearSegmentedColormap.from_list('paperblue',['#F6F8FA','#B8CDD9',BLUE,'#173C52'])
f,axes=plt.subplots(2,1,figsize=(180/25.4,177/25.4),layout='constrained')
vmax=max(float(a.max()) for a in matrices)
for ax,m,name in zip(axes,matrices,cases):
 im=ax.imshow(m,aspect='auto',cmap=cmap,vmin=0,vmax=vmax,interpolation='nearest')
 ax.set_yticks(range(7),['월','화','수','목','금','토','일'])
 ax.set_xticks([0,4,8,12,16,20,23]);ax.set(xlabel='시간 (시)',ylabel=name+' · 질병')
 ax.tick_params(length=0,pad=6)
 for sp in ax.spines.values():sp.set_visible(False)
cbar=f.colorbar(im,ax=axes,shrink=.87,pad=.025,aspect=35);cbar.set_label('접수 비중 (%)',fontsize=14)
save(f,'13-weekday-hour-disease',s,'2020~2024년 다대·금곡 질병 접수의 요일×시각 구성이다. 두 패널에 동일 색상 척도를 적용했다. 신고 시각은 예방교육의 적정 운영시간을 뜻하지 않는다.',[tim.relative_to(ROOT).as_posix()],'다대동 질병 4,054건 / 금곡동 질병 3,615건, 각각 전체 168셀 합계 100%')

cp=ROOT/'data/processed/신고주민연결심화-20260917/direction-connections/major-burden-commerce-20quarters.csv'
c=read(cp);s=c[(c.level=='lawDong')&(c.district=='부산진구')&(c.lawDong=='부전동')&(c.category.isin(['음식','소매']))].sort_values(['category','snapshot']).copy()
ck('Bujeon commerce 20 quarters per category',s.groupby('category').snapshot.nunique().eq(20).all() and len(s)==40)
ck('commerce definition unchanged in selected rows',s.dictionarySignature.nunique()==1)
ck('commerce share denominator',np.allclose(s.sharePct,100*s.shops/s.denominatorShops))
s['quarter_index']=(s.year-2020)*4+(s.quarter-1)
f,ax=fig(123)
for name,col,marker in zip(['음식','소매'],[BLUE,ORANGE],['o','s']):
 v=s[s.category==name];ax.plot(v.quarter_index,v.sharePct,color=col,marker=marker,markersize=4.8,lw=1.6,label=name)
ax.set(xlabel='연도·분기',ylabel='부전동 업종 구성비 (%)',ylim=(29,36))
ax.set_xticks([0,4,8,12,16,19],['2020\n1분기','2021\n1분기','2022\n1분기','2023\n1분기','2024\n1분기','2024\n4분기'])
style(ax);ax.legend(ncol=2,loc='lower center',bbox_to_anchor=(.5,1.01),frameon=False)
save(f,'14-bujeon-commerce-quarterly',s,'2020~2024년 분기별 부전동 음식·소매 상가 비중이다. 각 분기 상가 명부의 스냅숏 비중이며 실제 방문자나 특정 사고 원인의 측정값이 아니다. 선그래프 세로축은 29~36%로 표시했으므로 0% 기준 높이로 비교하지 않는다.',[cp.relative_to(ROOT).as_posix()],'각 분기 부전동 전체 상가 수')

lp=ROOT/'data/processed/통합완성-20260916/context/living-hour-annual-equal-month-means.csv'
kp=ROOT/'data/processed/신고주민연결심화-20260917/direction-connections/major-burden-living-candidates-2023-2024.csv'
l=read(lp);k=read(kp)
s=l[l.year.isin([2023,2024])&l['행정동코드'].isin([2623051000,2623052000])].copy()
s['hour']=s['시간대'].str.replace('시','').astype(int);s=s.sort_values(['행정동코드','year','hour'])
ck('living selected 96 rows',len(s)==96 and s.observedMonths.eq(12).all() and s.nameMissing.eq(False).all())
f,ax=fig(125)
for code,name,col in [(2623051000,'부전1동',BLUE),(2623052000,'부전2동',ORANGE)]:
 for year,ls,mark in [(2023,'--','o'),(2024,'-','s')]:
  sub=s[(s['행정동코드']==code)&(s.year==year)]
  key=k[(k.candidateCode==code)&(k.year==year)&(k.populationType=='평균방문인구수')].iloc[0]
  ck(name+str(year)+' summary matches',np.isclose(sub['평균방문인구수'].max(),key.maximum) and np.isclose(sub.iloc[0]['평균방문인구수'],key.midnight) and np.isclose(sub[sub.hour==12]['평균방문인구수'].iloc[0],key.noon))
  ax.plot(sub.hour,sub['평균방문인구수'],color=col,ls=ls,lw=1.55,marker=mark,markevery=4,markersize=5,label=f'{name} · {year}',mfc='white' if year==2023 else col)
ax.set(xlabel='시간 (시)',ylabel='방문인구 추정값 (명)',ylim=(0,35000),xlim=(-.35,23.35))
ax.set_xticks([0,4,8,12,16,20,23]);ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'));style(ax)
ax.legend(ncol=2,loc='lower center',bbox_to_anchor=(.5,1.01),frameon=False,columnspacing=1.2)
save(f,'15-bujeon-hourly-visiting-population',s,'2023·2024년 각 12개월의 시간별 평균방문인구를 월 동일 가중 평균한 값이다. 행정동 후보인 부전1·2동을 별도로 표시했으며 신고자·실인원·연간 방문자 수로 해석하지 않는다. 2025년 행은 제외했다.',[lp.relative_to(ROOT).as_posix(),kp.relative_to(ROOT).as_posix()],'해당 연도의 12개 월별 시간대 평균방문인구 추정값의 산술평균')

record={'sources':sources,'checks':checks,'figures':records,'status':'PASS'}
(META/'additional-figures.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':len(records),'checks':len(checks),'output':str(FIG)},ensure_ascii=False))
