"""Standalone figures from sourced follow-up operating evidence."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/후속입증-20260916/services'
plt.rcParams.update({'font.family':font_manager.FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name(),'svg.fonttype':'none','axes.unicode_minus':False})
navy='#183c4c';teal='#168b86';amber='#cc9242';grey='#e0e9ed';bg='#f6fafb'
data=json.loads((OUT/'inspection-analysis.json').read_text(encoding='utf-8'))
assert sum(x['listed_rows'] for x in data['stations'])==132
fig=plt.figure(figsize=(14,8),facecolor=bg)
fig.text(.06,.92,'공개 조사표의 불량 판정과 비고를 구분했습니다',fontsize=24,weight='bold',color=navy)
fig.text(.06,.85,'2026년 8월 · 4개 소방서 공개 조사표 132행 / 판정 131행 / 조사 연기 1행',fontsize=15,color=navy)
ax=fig.add_axes([.06,.30,.88,.47]);ax.axis('off')
cols=['소방서','조사표 행','소방시설\n불량','피난·방화\n불량','불량 중\n현지시정 표기','불량 중\n비고 공란','조사 연기']
rows=[[s['station'],s['listed_rows'],s['fire_defect_rows'],s['escape_defect_rows'],s['any_defect_with_onsite_correction'],s['any_defect_without_correction_note'],s['deferred_rows']] for s in data['stations']]
t=ax.table(cellText=rows,colLabels=cols,cellLoc='center',colWidths=[.18,.12,.13,.13,.17,.17,.10],bbox=[0,0,1,1]);t.auto_set_font_size(False);t.set_fontsize(15)
for (r,c),cell in t.get_celld().items():
 cell.set_edgecolor(bg);cell.set_linewidth(3)
 cell.set_facecolor(navy if r==0 else ('#e6f2f0' if c==4 else '#f4e9d8' if c==5 else 'white'))
 cell.get_text().set_color('white' if r==0 else navy)
 cell.get_text().set_weight('bold' if r==0 or c==0 else 'normal')
fig.text(.06,.23,'불량이 하나라도 기록된 19행 중 6행에 현지시정이 함께 기재되어 있습니다.',fontsize=16,weight='bold',color=teal)
fig.text(.06,.18,'13행은 일반 비고란의 공란입니다. 조치완료 전용 열이 아니므로 관리공백이나 현재 미조치의 증거가 아닙니다.',fontsize=12,color=navy)
fig.text(.06,.12,'소방서 관할은 구 경계와 다릅니다. 조사대상·방법이 달라 불량률 순위를 만들 수 없으며, 같은 이름·도로번호의 복수 행은 병합하지 않았습니다.',fontsize=11,color=navy)
fig.text(.06,.08,'동래 첨부 표지 8/7 ↔ 조사 종료 8/31·게시 9/7 날짜 불일치. 표의 39행은 원문 그대로 보존했습니다.',fontsize=11,color=navy)
fig.text(.06,.035,'출처: 부산소방 4개 소방서 2026년 8월 화재안전조사 결과 HWP · 확보 2026-09-16',fontsize=11,color=navy)
for ext in ['png','svg']:fig.savefig(OUT/f'current-fire-inspection.{ext}',dpi=150)
plt.close(fig)
fig=plt.figure(figsize=(14,8),facecolor=bg)
fig.text(.06,.92,'설치 수를 넘어, 운영 정보와 실제 관리가 중요합니다',fontsize=24,weight='bold',color=navy)
fig.text(.06,.85,'부산 AED·취약주택 지원의 공식 기록 대조 · 서로 다른 시점과 범위',fontsize=15,color=navy)
items=[
 ('부산 AED 4,431대','2025년 6월 보유 현황','의무시설 3,021대 + 비의무시설 1,410대.\n시는 일부 설치정보의 행정시스템 불일치를 확인했습니다.','불일치 건수·현재 고장대수는 공개자료에서 미확인'),
 ('기존 관리·대여 운영','연제 2024 회의 / 기장 공식 대여 안내','연제는 연간 통상 4~5대 구매지원·소모품 교환을 설명했습니다.\n기장은 실제 AED 대여 시 장비 확인·반납 점검을 안내합니다.','운영 절차가 있다고 해서 모든 시설의 접근성·작동을 보증하지 않음'),
 ('주택 지원도 진행 중','기장읍 2026 계획 / 동래 2026 협업','기장읍은 취약계층 1,000세대 멀티탭 지원을 계획했습니다.\n동래는 교육·가정방문 위험점검·소방용품 지원을 연계했습니다.','계획·기관 전달을 최종 가정 설치완료 수로 바꾸지 않음')]
for i,(title,period,body,limit) in enumerate(items):
 y=.72-i*.205
 fig.text(.06,y,title,fontsize=19,weight='bold',color=teal)
 fig.text(.06,y-.046,period,fontsize=11,color=navy)
 fig.text(.35,y,body,fontsize=15,color=navy,va='top',linespacing=1.65)
 fig.text(.35,y-.125,limit,fontsize=11,color='#6a7277')
 fig.add_artist(plt.Line2D([.06,.94],[y-.15,y-.15],transform=fig.transFigure,color=grey,lw=1))
fig.text(.06,.095,'프로젝트의 역할: 반복 신고를 출발점으로 현재 운영조건·점검결과·조치 상태를 연결합니다.',fontsize=15,weight='bold',color=navy)
fig.text(.06,.04,'출처: 부산시 2025.7.31 / 연제구의회 2024.6.14 / 기장군·읍 / 신라대 수탁 복지관 2026.5.27 · 확보 2026-09-16',fontsize=10,color=navy)
for ext in ['png','svg']:fig.savefig(OUT/f'current-service-evidence.{ext}',dpi=150)
plt.close(fig)
print('2 PNG + 2 SVG generated')
