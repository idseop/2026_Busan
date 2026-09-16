"""Publication figures from verified official field-study and follow-up tables."""
from pathlib import Path
import csv,hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/후속입증-20260916/traffic'
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False,'font.size':11,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#243b4a','text.color':'#243b4a','xtick.color':'#243b4a','ytick.color':'#243b4a'})
def read(name):return list(csv.DictReader((OUT/name).open(encoding='utf-8-sig')))
def save(fig,name):
 for ext in ['png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=160,facecolor='#ffffff')
 plt.close(fig)

def main():
 rows=read('bdi-field-study-area-summary.csv');x=np.arange(4)
 fig,ax=plt.subplots(1,2,figsize=(14,7),gridspec_kw={'width_ratios':[1.35,1]})
 fig.subplots_adjust(left=.075,right=.97,bottom=.29,top=.77,wspace=.30)
 fig.suptitle('4개 현장 실험에서 체험복 착용 후 보행시간이 늘었다',x=.06,ha='left',fontsize=19,fontweight='bold',y=.96)
 fig.text(.06,.875,'2024.10.26~27 조사 · 30대 여성 조사원의 노인체험복 착용 전후 비교',fontsize=12)
 a=np.array([float(r['meanSecondsWithoutSuit']) for r in rows]);b=np.array([float(r['meanSecondsWithSuit']) for r in rows])
 for i in x:ax[0].plot([a[i],b[i]],[i,i],color='#a1b7bf',lw=5,zorder=1)
 ax[0].scatter(a,x,s=95,color='#69808b',label='미착용',zorder=2)
 ax[0].scatter(b,x,s=95,color='#057d87',label='착용',zorder=3)
 for i in x:
  ax[0].text(a[i]-4,i+.20,f'{a[i]:.1f}',ha='right',fontsize=11)
  ax[0].text(b[i]+4,i-.02,f'{b[i]:.1f}',ha='left',fontsize=11,fontweight='bold')
 ax[0].set_yticks(x,[r['area'] for r in rows]);ax[0].invert_yaxis();ax[0].set_xlim(135,330);ax[0].set_ylim(3.5,-.6)
 ax[0].set_xlabel('보고서상 구간 평균 보행시간(초)');ax[0].set_title('같은 조사지역의 실험조건 비교',loc='left',pad=18,fontweight='bold')
 ax[0].legend(loc='lower left',bbox_to_anchor=(0,-.27),ncol=2,frameon=False)
 sep=np.array([int(r['separatedSegments']) for r in rows]);un=np.array([int(r['unseparatedSegments']) for r in rows])
 ax[1].barh(x,sep,color='#218b79',height=.48,label='보차분리');ax[1].barh(x,un,left=sep,color='#dc9853',height=.48,label='보차미분리')
 for i in x:
  ax[1].text(sep[i]/2,i,str(sep[i]),ha='center',va='center',color='white',fontweight='bold')
  ax[1].text(sep[i]+un[i]/2,i,str(un[i]),ha='center',va='center',color='#243b4a',fontweight='bold')
 ax[1].set_yticks(x,[r['area'] for r in rows]);ax[1].set_ylim(3.5,-.6);ax[1].set_xlim(0,10);ax[1].set_xlabel('조사구간 수(개)');ax[1].set_title('20개 조사구간의 보행로 구분',loc='left',pad=18,fontweight='bold')
 ax[1].legend(loc='lower left',bbox_to_anchor=(0,-.27),ncol=2,frameon=False)
 fig.text(.06,.075,'실제 고령자 평균이 아닌 체험복 실험이다. 지역별 구간 길이가 달라 지역 간 시간의 단순 우열 비교는 하지 않는다.\n시간표는 횡단 대기시간이 포함된 신평 외부도로 1구간을 제외한다. 오른쪽은 제외 전 20구간의 시설 구분이다.',fontsize=10,linespacing=1.7)
 fig.text(.06,.025,'출처: 부산연구원(2025.3), 「고령자 친화적인 15분 생활권내 교통안전 확보방안」 PDF66~70쪽 · 현재 상태·119 사건과 별도',fontsize=9,color='#627580')
 save(fig,'field_study_experiment')

 road=read('bdi-field-study-roadtype-summary.csv')
 fig,ax=plt.subplots(figsize=(14,7.7));fig.subplots_adjust(left=.19,right=.96,top=.79,bottom=.22)
 fig.suptitle('부전시장 내부도로에서 체험복 착용 전후 시간 증가율이 가장 컸다',x=.05,ha='left',fontsize=18,fontweight='bold',y=.96)
 fig.text(.05,.885,'2024.10.26~27 현장 실험 · 동일 조사원 조건 비교 · 4지역 × 내·외부도로 8개 집계',fontsize=12)
 y=np.arange(8);vals=[float(r['publishedTimeChangePct']) for r in road]
 ax.barh(y,vals,height=.57,color=['#13877b' if r['roadType']=='내부도로' else '#65a5be' for r in road])
 ax.set_yticks(y,[r['area']+' · '+r['roadType'] for r in road]);ax.invert_yaxis();ax.set_xlim(0,38);ax.set_xlabel('미착용 대비 착용 후 보행시간 증가율(%) · 원 보고서의 거리·시간 합산 기준')
 for i,v in enumerate(vals):ax.text(v+.5,i,f'+{v:.1f}%',va='center',fontweight='bold')
 ax.xaxis.grid(True,alpha=.15);ax.set_axisbelow(True)
 fig.text(.05,.10,'내부도로(진한 녹색)와 외부도로(파란색)는 각 조사지역 안에서 구분한 것이다. 구간 길이와 현장 조건이 서로 다르다.\n노인체험복을 착용한 30대 조사원 실험이며, 실제 고령 주민의 평균이나 사고 원인을 입증하지 않는다.',fontsize=10,linespacing=1.7)
 fig.text(.05,.035,'출처: 부산연구원(2025.3), PDF67·70쪽 · 신평 외부도로는 횡단 대기시간 포함 1구간 제외 · 반올림 평균으로 증가율을 재계산하지 않음',fontsize=9,color='#627580')
 save(fig,'field_study_road_conditions')

 sites=read('traffic-followup-all14.csv')
 short=['사업 준공·평가 계약 완료','점검항목 완료 미확인','공식 주소 후보 확보','공식 주소 후보 확보','점검항목 완료 미확인','점검항목 완료 미확인','점검항목 완료 미확인','점검항목 완료 미확인','점검항목 완료 미확인','생활가로 계획·예산심사','공식 주소 후보 확보','점검항목 완료 미확인','주정차 CCTV 운영 확인','점검항목 완료 미확인']
 fig=plt.figure(figsize=(14,10.5));ax=fig.add_axes([.055,.16,.89,.65]);ax.axis('off')
 fig.text(.055,.945,'14개 공식 점검지점의 후속 근거를 구분했다',fontsize=21,fontweight='bold')
 fig.text(.055,.885,'2023년 점검 당시 개선안 → 2026.9.16까지 이번에 확보한 공개자료\n당시 기개선 9개·단기안 122개·중장기안 19개. 현재 미완료 건수가 아니다.',fontsize=12,linespacing=1.7)
 headers=['구·군 / 점검 지점','당시 단기 / 중장기','확보한 후속 근거']
 xx=[.01,.51,.72]
 for i,h in enumerate(headers):ax.text(xx[i],1,h,fontsize=12,fontweight='bold',transform=ax.transAxes)
 for i,r in enumerate(sites):
  yy=.947-i*.065
  ax.axhline(yy-.022,color='#e6edef',lw=.8)
  ax.text(xx[0],yy,r['district']+' · '+r['place'].replace(' 부근',''),va='center',fontsize=11,transform=ax.transAxes)
  ax.text(xx[1],yy,r['shortTermItems']+' / '+r['longTermItems']+'개',va='center',fontsize=11,transform=ax.transAxes)
  color='#087d72' if i in [0,9,12] else '#5f727a'
  ax.text(xx[2],yy,short[i],va='center',fontsize=11,color=color,transform=ax.transAxes)
 ax.set_xlim(0,1);ax.set_ylim(0,1)
 fig.text(.055,.10,'못골시장 사업·평가 완료는 개별 점검항목의 동일성을 뜻하지 않는다. 거제시장 계획과 예산심사는 시공 완료가 아니다.\n주소 후보와 CCTV 운영 확인도 점검항목의 완료 여부를 대신하지 않는다. 미확인은 미개선·서비스 부재와 다르다.',fontsize=10,linespacing=1.7)
 fig.text(.055,.035,'출처: 행정안전부 2023.11.29 점검표 + 부산시·구청·의회 공개자료 · 자세한 출처·시점·동일구간 판정은 traffic-followup-all14.csv',fontsize=9,color='#627580')
 save(fig,'traffic_followup_all14')
 inputs=['bdi-field-study-area-summary.csv','bdi-field-study-roadtype-summary.csv','traffic-followup-all14.csv']
 (OUT/'figure-manifest.json').write_text(json.dumps({'script':'scripts/plot_followup_traffic_20260916.py','inputs':{n:hashlib.sha256((OUT/n).read_bytes()).hexdigest() for n in inputs},'figures':['field_study_experiment','field_study_road_conditions','traffic_followup_all14']},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
