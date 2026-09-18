from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'data/processed/후속입증-20260916/housing'
f=pd.read_csv(B/'busan_housing_context_2024.csv',dtype={'sgisCode':str})
plt.rcParams.update({'font.family':FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name(),'axes.unicode_minus':False,'font.size':12,'svg.fonttype':'none'})
names=['기장읍','온천1동','온천2동','온천3동'];codes=['ho_gb_003','ho_gb_002','ho_gb_001','ho_gb_004','ho_gb_005'];labels=['아파트','단독주택','다세대','연립주택','영업용 건물 내 주택'];colors=['#137f74','#528faf','#9bc5bb','#ddb25c','#cab7a1']
fig,ax=plt.subplots(figsize=(12,6.8));rows=[]
for i,name in enumerate(names):
 g=f[f.name.eq(name)];total=int(g[g.itemCode.eq('to_ho_001')].value.iloc[0]);left=0
 assert not g[g.itemCode.isin(codes)].value.isna().any()
 assert int(g[g.itemCode.isin(codes)].value.sum())==total
 for c,l,color in zip(codes,labels,colors):
  count=int(g[g.itemCode.eq(c)].value.iloc[0]);share=count/total*100
  ax.barh(i,share,left=left,color=color,label=l if i==0 else None)
  if share>=9:ax.text(left+share/2,i,f'{share:.1f}%',ha='center',va='center',color='white' if c in codes[:2] else '#153940',fontsize=12)
  rows.append({'name':name,'housingType':l,'count':count,'totalHousing':total,'share':share,'year':2024,'boundary':'2025-06-30'});left+=share
 other=int(g[g.itemCode.eq('ho_gb_006')].value.iloc[0]);ax.text(102,i,f'주택 {total:,}\n별도 거처 {other:,}',va='center',fontsize=11)
ax.set_yticks(range(4),names);ax.invert_yaxis();ax.set_xlim(0,125);ax.set_xticks([0,20,40,60,80,100]);ax.set_xlabel('총주택 중 유형 구성비 (%)');ax.spines[['top','right']].set_visible(False)
handles,legendlabels=ax.get_legend_handles_labels()
fig.legend(handles,legendlabels,loc='lower left',bbox_to_anchor=(.10,.09),ncol=3,frameon=False)
ax.set_title('아파트 안내만으로 지역의 모든 주택을 설명할 수 없습니다',loc='left',fontsize=18,fontweight='bold',pad=35)
fig.text(.125,.915,'SGIS 2024 주택통계 · 2025-06-30 경계의 별도 배경 비교',fontsize=12)
fig.text(.125,.015,'주택 이외 거처는 총주택 분모에 더하지 않았습니다. 온천동 신고를 3개 주민 지역으로 배분하지 않았습니다.\n주택 유형은 화재 원인·시설지원 미수혜·주민 위험률을 뜻하지 않습니다.',fontsize=10)
fig.tight_layout(rect=(0,.24,1,.9))
for ext in ['png','svg']:fig.savefig(B/f'housing_type_context.{ext}',dpi=160,bbox_inches='tight')
pd.DataFrame(rows).to_csv(B/'selected_housing_type_context.csv',index=False,encoding='utf-8-sig')
plt.close(fig)
