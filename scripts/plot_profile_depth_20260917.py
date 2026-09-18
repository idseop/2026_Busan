"""Three question-specific, reproducible figures for the profile-depth report."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

R=Path(__file__).resolve().parents[1]
N=R/'data/processed/신고주민연결심화-20260917'
O=R/'figures/신고주민연결심화-20260917';O.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','figure.facecolor':'#fbfcfb','axes.facecolor':'#fbfcfb','text.color':'#183843','axes.labelcolor':'#183843','xtick.color':'#183843','ytick.color':'#183843'})
TEAL,BLUE,ORANGE,GRAY='#007f80','#23588a','#c07836','#89999c'
inputs=[];outputs=[]
def read(p):
 inputs.append({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 return pd.read_csv(p,keep_default_na=False)
def save(fig,name):
 for ext in ['png','svg']:
  p=O/(name+'.'+ext);fig.savefig(p,dpi=170,facecolor=fig.get_facecolor(),bbox_inches='tight')
  outputs.append({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 plt.close(fig)

s=read(N/'analysis/selected-name-all-types-comparison-summary.csv')
cases=[('북구','금곡동','구급'),('북구','화명동','구급'),('영도구','동삼동','구급'),('강서구','대저1동','화재'),('강서구','대저2동','화재'),('강서구','명지동','화재'),('강서구','송정동','화재'),('기장군','기장읍','구조'),('기장군','정관읍','구조')]
fig,ax=plt.subplots(figsize=(13.5,7.8));fig.subplots_adjust(left=.19,right=.83,top=.83,bottom=.19)
for i,(d,n,t) in enumerate(cases):
 q=s[(s.district==d)&(s.rawDong==n)&(s.type==t)&(s.subtype=='')].set_index('reference')
 a=int(q.loc['restBusan','aboveReference30']);b=int(q.loc['restDistrict','aboveReference30'])
 ax.plot([a,b],[i,i],color='#c8d1d3',lw=3,zorder=1)
 ax.scatter(a,i-.10,s=100,color=BLUE,zorder=3,label='나머지 부산과 비교' if i==0 else None)
 ax.scatter(b,i+.10,s=100,marker='D',color=TEAL,zorder=3,label='같은 구·군 안에서 비교' if i==0 else None)
 ax.text(31.1,i,f'{a}/30  →  {b}/30',va='center',fontsize=12,fontweight='bold' if a!=b else 'normal')
ax.set_yticks(range(len(cases)),[f'{d} {n} · {t}' for d,n,t in cases]);ax.invert_yaxis();ax.set_xlim(-1,31);ax.set_xticks(range(0,31,5));ax.grid(axis='x',alpha=.15)
ax.set_xlabel('해당 지역의 신고 구성비가 비교 지역보다 높은 조건 수 (30개 중)',labelpad=12)
ax.legend(loc='upper left',bbox_to_anchor=(-.04,1.13),frameon=False,ncol=2)
fig.suptitle('부산에서 높게 보여도, 같은 구·군 안에서는 다르다',fontsize=21,x=.04,ha='left')
fig.text(.04,.035,'2020–2024 · 결측 제외 전후 × 처리조건 3개 × 5개 연도\n30개는 독립 표본·위험 점수가 아닌 민감도 비교. 비교 집합마다 해당 지역을 뺀 나머지와 비교했다.',fontsize=11,linespacing=1.6)
save(fig,'01-비교범위에따른-지역선정')

t=read(N/'analysis/selected-name-time-cells.csv')
p=read(N/'analysis/selected-name-candidate-resident-background.csv')
fig,axs=plt.subplots(2,1,figsize=(13.5,10.5),gridspec_kw={'height_ratios':[1.05,1]});fig.subplots_adjust(left=.13,right=.97,top=.87,bottom=.17,hspace=.52)
for name,col in [('금곡동',TEAL),('화명동',ORANGE)]:
 q=t[(t.district=='북구')&(t.rawDong==name)&(t.type=='구급')&(t.subtype=='질병')&(t.year==0)&(t.dimension=='hour4')].sort_values('bin')
 assert len(q)==6
 axs[0].plot(q.bin,100*q.share,marker='o',ms=6,lw=2.6,color=col,label=f'{name} · {int(q["count"].sum()):,}건')
axs[0].set_title('① 질병으로 접수된 신고의 시간 분포 · 각 지역 질병 접수 중 비중',loc='left',fontsize=14,pad=13)
axs[0].set_ylabel('%');axs[0].set_ylim(0,30);axs[0].set_xticks(range(6),['00–03시','04–07시','08–11시','12–15시','16–19시','20–23시']);axs[0].set_xlim(-.1,5.1);axs[0].set_xlabel('동일 길이 4시간 접수 구간');axs[0].grid(alpha=.12);axs[0].legend(frameon=False,loc='upper left')
colors=['#dcad65','#74b5a7','#356e88','#253c62'];agecols=['share_0_14','share_15_39','share_40_64','share_65plus'];names=['0–14세','15–39세','40–64세','65세 이상']
q=p[(p.district=='북구')&p.rawDong.isin(['금곡동','화명동'])&p.year.eq(2024)].sort_values(['rawDong','candidateCode'])
assert len(q)==4
left=np.zeros(len(q))
for key,label,col in zip(agecols,names,colors):
 vals=q[key].astype(float).to_numpy()*100;axs[1].barh(range(len(q)),vals,left=left,color=col,label=label,height=.60)
 for i,(v,l) in enumerate(zip(vals,left)):
  axs[1].text(l+v/2,i,f'{v:.1f}',ha='center',va='center',color='#122c34' if key in agecols[:2] else 'white',fontsize=12,fontweight='bold')
 left+=vals
axs[1].set_yticks(range(len(q)),[f"{r.candidateName}\n{int(r.residentTotal):,}명" for r in q.itertuples()]);axs[1].invert_yaxis();axs[1].set_xlim(0,100);axs[1].set_xlabel('각 주민 후보 지역의 연령 비중 (%)')
axs[1].set_title('② 2024년 말 주민 구성 · 화명 후보 3개를 합산하지 않음',loc='left',fontsize=14,pad=37)
axs[1].legend(loc='lower left',bbox_to_anchor=(0,1.0),frameon=False,ncol=4,fontsize=11)
fig.suptitle('금곡·화명: 접수 시간과 주민 구성을 함께 읽기',fontsize=21,x=.04,ha='left')
fig.text(.04,.92,'금곡 질병 오전 정점은 5년 모두 유지 · 화명의 20–23시 정점은 5년 중 3년',fontsize=13)
fig.text(.04,.025,'신고 2020–2024 · 정상 처리, 운영성·벌집제거 제외 · 인구 2024-12-31\n주민은 신고자의 연령을 뜻하지 않는다. 시각 비교는 17개 컬럼 결측 제외 집합의 결과다.\n건강관리 창구의 운영시간과 응급 신고시간을 비교해 서비스 부족을 판정하지 않는다.',fontsize=11,linespacing=1.55)
save(fig,'02-금곡화명-신고시간과주민구성')

h=read(N/'context/selected-context.csv');a=read(N/'analysis/selected-name-annual-subtypes.csv')
fig,axs=plt.subplots(3,1,figsize=(13.5,14));fig.subplots_adjust(left=.15,right=.95,top=.87,bottom=.14,hspace=1.10)
rawnames=['대저1동','대저2동','명지동'];firelabels=['기타화재','대형화재(시장,공장)','일반화재(주택)','일반화재(차량)','고층건물(3층이상,아파트)','그 외 분류'];palette=['#a8b3b5','#c8944e','#008182','#749fa5','#23588a','#d4dada']
q=a[(a.CLMTY_SGG_NM=='강서구')&a.CLMTY_EMD_NM.isin(rawnames)&a.EMRG_RSCU_ASSRT_NM.eq('화재')].groupby(['CLMTY_EMD_NM','EMRG_RSCU_CLSF_NM'])['count'].sum()
left=np.zeros(3);totals=[int(q.loc[n].sum()) for n in rawnames]
for label,col in zip(firelabels,palette):
 counts=[int(q.loc[n].get(label,0)) if label!='그 외 분류' else int(q.loc[n][~q.loc[n].index.isin(firelabels[:-1])].sum()) for n in rawnames]
 vals=np.array(counts)/np.array(totals)*100;axs[0].barh(range(3),vals,left=left,color=col,height=.6,label=label)
 for i,(v,l,k) in enumerate(zip(vals,left,counts)):
  if v>=8:axs[0].text(l+v/2,i,str(k),ha='center',va='center',color='white' if col in ['#008182','#23588a'] else '#173641',fontsize=12,fontweight='bold')
 left+=vals
axs[0].set_yticks(range(3),[f'{n} · {v}접수' for n,v in zip(rawnames,totals)]);axs[0].invert_yaxis();axs[0].set_xlim(0,100);axs[0].set_xlabel('해당 지역 화재 접수 내 구성비 (%) · 막대 안은 접수 건수')
axs[0].set_title('① 같은 강서구에서도 기록된 화재 세부유형이 다르다',loc='left',fontsize=14,pad=13)
axs[0].legend(loc='upper left',bbox_to_anchor=(-.04,-.36),frameon=False,ncol=3,fontsize=10)
q=h[(h.district=='강서구')&h.name.isin(['대저1동','대저2동','명지1동','명지2동'])].sort_values('sgisCode')
y=np.arange(len(q));axs[1].barh(y-.17,q.detachedPct,height=.29,color=TEAL,label='단독주택');axs[1].barh(y+.17,q.apartmentPct,height=.29,color=BLUE,label='아파트')
for i,r in enumerate(q.itertuples()):
 axs[1].text(r.detachedPct+1,i-.17,f'{r.detachedPct:.1f}%',va='center',fontsize=11)
 axs[1].text(r.apartmentPct+1,i+.17,f'{r.apartmentPct:.1f}%',va='center',fontsize=11)
axs[1].set_yticks(y,q.name);axs[1].invert_yaxis();axs[1].set_xlim(0,112);axs[1].set_xlabel('공표된 총주택 중 해당 종류 비중 (%)');axs[1].set_title('② 대저는 단독주택, 명지 후보는 아파트 비중이 높다',loc='left',fontsize=14,pad=13);axs[1].legend(frameon=False,ncol=2,loc='upper left',bbox_to_anchor=(0,-.38))
axs[2].barh(y,q.manufacturingEstablishmentPct,color=ORANGE,height=.5)
for i,r in enumerate(q.itertuples()):axs[2].text(r.manufacturingEstablishmentPct+.7,i,f'{int(r.manufacturingEstablishments):,}개 · {r.manufacturingEstablishmentPct:.1f}%',va='center',fontsize=12)
axs[2].set_yticks(y,q.name);axs[2].invert_yaxis();axs[2].set_xlim(0,44);axs[2].set_xlabel('전체 사업체 중 제조업 사업체 비중 (%)');axs[2].set_title('③ 대저는 제조업 배경도 커, 주택 지원만으로 설명할 수 없다',loc='left',fontsize=14,pad=13)
fig.suptitle('강서구: 주택과 사업장에 필요한 대응을 구분하기',fontsize=21,x=.04,ha='left')
fig.text(.04,.925,'신고의 장소 유형 → 주택·산업 배경 → 기존 사업의 적용 대상',fontsize=13)
fig.text(.04,.025,'신고 2020–2024 · 주택·사업체 통계 2024년 / SGIS 제공 경계 2025-06-30\n명지동 신고를 명지1·2동에 나누지 않았다. 주택·사업체 수는 신고 분모나 미지원 대상 수가 아니다.\n제조업 사업체는 등록공장 수와 다르다. 비공표 값은 역산하거나 0으로 채우지 않았다.',fontsize=11,linespacing=1.55)
save(fig,'03-강서-주택과산업배경')
(O/'manifest.json').write_text(json.dumps({'inputs':inputs,'outputs':outputs,'interpretation':'비교조건 안정성·접수시간·주민/현장배경만 표시. 위험도·연령별사건·서비스부족·효과추정 안함.'},ensure_ascii=False,indent=2),encoding='utf8')
print('Created',len(outputs),'PNG/SVG artifacts')
