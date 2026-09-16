"""Render an evidence-to-action summary from the verified three case records."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
O=R/'output/부산119-쟁점해결-20260916'
C=json.loads((O/'case-selection.json').read_text(encoding='utf-8'))
plt.rcParams.update({'font.family':'Malgun Gothic','svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(15.8,7.2));fig.patch.set_facecolor('#f3f7f6');ax.set_facecolor('#f3f7f6')
ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
ax.text(.02,.98,'반복 신고를 지역별 예방·지원 안내로 연결',fontsize=22,weight='bold',color='#153e48',va='top')
ax.text(.02,.895,'신고 2020–2024 · 정상 처리·운영성 제외 · 후속 근거 확인 2026-09-16',fontsize=12,color='#47655d')
xs=[.02,.245,.493,.745]
for x,label in zip(xs,['확인한 신고','주민·현장 배경','이미 있는 대응','이번에 만든 결과']):
 ax.text(x,.795,label,fontsize=16,weight='bold',color='#146d62')
texts=[
 ['5년 접수 기록 유지\n주말/평일 비율 방향 유지','주민 후보 8곳 개별 비교\n신고자 연령으로 해석하지 않음','기본·수료증 과정\n실습 기자재 7일 대여','목적·연령별 공식 안내\n교육용/실제 AED 구분'],
 ['5년 접수 기록 유지\n주말/평일 비율 방향 유지','2024 보행환경 현장조사\n주민·생활인구 후보별 비교','2026 맞이길 제막식\n과거 조사와 동일 구간 미확정','과거 문제와 이후 사업 병기\n현재 미개선이라는 단정 제거'],
 ['5년 접수 기록 확인\n처리조건별 증감 방향 민감','2024 내부도로 조사\n주민 후보 4곳 개별 비교','2025 수영로 포장사업\n검사·준공금 지급 확인','포장과 보차분리 구분\n새 시설안은 근거 미확정']]
for i,c in enumerate(C):
 y=.69-i*.225
 ax.axhline(y+.063,xmin=.02,xmax=.99,color='#bdd6cd',lw=1)
 ax.text(xs[0],y,f"{c['rawDong']} · {c['subtype']}  {c['count']:,}건",fontsize=15,weight='bold',color='#183d46')
 ax.text(xs[0],y-.057,texts[i][0],fontsize=11.8,color='#345951',va='top',linespacing=1.7)
 for x,t in zip(xs[1:],texts[i][1:]):ax.text(x,y,t,fontsize=12.5,color='#183d46',va='top',linespacing=1.8)
ax.text(.02,.035,'완료: 근거·이용조건·사업 이력 연결     |     아직 측정하지 않은 효과: 이용 개선·사고 및 피해 감소',fontsize=12,color='#47655d')
fig.subplots_adjust(left=.015,right=.99,bottom=.03,top=.98)
for ext in ['png','svg']:fig.savefig(O/f'evidence_to_action.{ext}',dpi=160,facecolor=fig.get_facecolor())
print('evidence_to_action.png/svg')
