from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'data/processed/후속입증-20260916/analysis'
d=json.loads((B/'all-region-followup.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name(),'axes.unicode_minus':False,'font.size':11,'svg.fonttype':'none'})
def save(fig,name):
 for ext in ['png','svg']:fig.savefig(B/f'{name}.{ext}',dpi=160,bbox_inches='tight')
 plt.close(fig)
rows=[r for r in d['catalogue'] if r['scope']=='C']
districts=list(dict.fromkeys(r['district'] for r in rows));types=list(dict.fromkeys(r['subtype'] for r in rows))
counts=np.array([[sum(r['count'] for r in rows if r['district']==gu and r['subtype']==t) for t in types] for gu in districts])
den=np.array([sum(r['regionAllTypes'] for r in rows if r['district']==gu and r['subtype']==types[0]) for gu in districts])
assert sum(den)==574662
shares=counts/den[:,None]*100
fig,ax=plt.subplots(figsize=(12,9));im=ax.imshow(shares,cmap='GnBu',vmin=0,vmax=float(shares.max()),aspect='auto')
ax.set_xticks(range(5),types);ax.set_yticks(range(16),districts)
for i in range(16):
 for j in range(5):ax.text(j,i,f'{shares[i,j]:.2f}%\n{counts[i,j]:,}건',ha='center',va='center',fontsize=10,color='white' if shares[i,j]>shares.max()*.6 else '#15383f')
ax.set_title('같은 부산 안에서도 신고 유형의 구성은 다릅니다',loc='left',fontweight='bold',fontsize=19,pad=37)
fig.text(.125,.925,'2020–2024 · 정상 처리·운영성 분류 제외 · 각 구·군의 전체 선택 신고 대비 비중',fontsize=11)
fig.colorbar(im,ax=ax,label='각 구·군 선택 신고 중 구성비 (%)',fraction=.035,pad=.04)
fig.text(.125,.025,'예방 관련 5개 유형만 표시. 나머지 유형을 제외한 비중으로 재정규화하지 않았습니다. 위험도·주민당 사고율이 아닙니다.',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.92));save(fig,'district_type_composition')
s=d['stabilityAcrossScopes']['timeSensitivity'];fig,ax=plt.subplots(figsize=(11,5.5))
x=np.arange(len(s));a=np.array([r['ratioCrossesOne'] for r in s]);b=np.array([r['finiteRatioPairs'] for r in s]);c=np.array([r['ratioCrosses09and11'] for r in s])
ax.plot(x,a/b*100,'o-',color='#11796e',label='주말/평일 비율이 1배를 가로지른 조합',linewidth=2)
ax.plot(x,c/b*100,'s--',color='#d79232',label='0.9배 미만 ↔ 1.1배 초과로 바뀐 조합',linewidth=2)
for xx,aa,bb,cc in zip(x,a,b,c):
 ax.text(xx,aa/bb*100+2,f'{aa}/{bb}',ha='center')
 ax.text(xx,cc/bb*100-5,f'{cc}/{bb}',ha='center')
ax.set_xticks(x,[f'매년 {r["minimumEachYear"]}건 이상' for r in s]);ax.set_ylabel('앞·뒤 기간의 주말 양상이 달라진 조합 (%)');ax.set_ylim(0,65);ax.grid(axis='y',alpha=.2)
ax.spines[['top','right']].set_visible(False);ax.legend(loc='upper right',fontsize=10)
ax.set_title('반복 신고가 안정적이어도, 시간 전략까지 같지는 않습니다',loc='left',fontsize=17,fontweight='bold',pad=25)
fig.text(.12,.015,'2020–22 대 2023–24 · 달력 일수 보정 · 3처리조건에서 반복·증감 방향이 보존된 조합\n최소 건수와 0.9/1.1은 민감도 확인용이며 정책 선정 기준·통계적 유의성 판정이 아닙니다.',fontsize=10)
fig.tight_layout(rect=(0,.09,1,1));save(fig,'time_strategy_sensitivity')
fig,axes=plt.subplots(1,2,figsize=(12,5.8),sharey=True)
for ax,r in zip(axes,[r for r in d['buildingContext'] if r['scope']=='C']):
 ax.plot(range(2020,2025),r['beforeYearCounts'],'s--',color='#9babb2',label='제외 전 비교 집합',linewidth=2)
 ax.plot(range(2020,2025),r['yearCounts'],'o-',color='#11796e',label='17개 조건 충족 신고',linewidth=2)
 for y,n in zip(range(2020,2025),r['yearCounts']):ax.text(y,n+.7,str(n),ha='center')
 ax.set_title(r['district']+' '+r['rawDong']);ax.set_xticks(range(2020,2025));ax.grid(axis='y',alpha=.15);ax.set_ylim(0,40)
 ax.set_ylabel('접수 건수');ax.legend(fontsize=10)
fig.suptitle('고층건물 화재 분류를 별도로 확인했습니다',fontsize=19,fontweight='bold')
fig.text(.08,.035,'2020–2024 정상 처리 · 기장읍은 제외 전후 증감 방향이 반대. 온천동은 같은 증가 방향.\n이 분류는 3층 이상 건물을 포함하므로 아파트만의 신고가 아니며, 포털의 특정 건물에 배정하지 않았습니다.',fontsize=10)
fig.tight_layout(rect=(0,.12,1,.91));save(fig,'building_fire_selection')
print('3 figures saved')
