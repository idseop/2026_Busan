from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1];O=R/'data/processed/고도화검증-20260916/education'
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(13,6.7));fig.patch.set_facecolor('#f4f8f7');ax.axis('off')
fig.text(.06,.91,'교육·대여는 이름보다 이용 목적과 조건을 구분해야 합니다',fontsize=19,weight='bold',color='#153f49')
fig.text(.06,.85,'부산 공식 안내에서 확인한 조건 · 실제 예약 가능 여부·장비 재고·응급 대응 효과는 별도',fontsize=11,color='#456661')
heads=['기본 응급처치 교육','수료증 과정','동래소방서 실습 대여','기장군 실제 AED 대여']
texts=[['50–80분','12세 이상·인원 조건','평가·수료증 없음','교육 일정 사전 협의'],['240분','실습평가 80점 이상','수료증 발급 가능','담당자 사전 협의'],['7일','가족·비영리 모임 등','교육용 AED 포함','응급환자용 장비가 아님'],['최대 14일','행사·단체여행·환자 가정 등','기장 관련 대상 조건','수령·반납 시 장비 확인']]
for i,(h,ts) in enumerate(zip(heads,texts)):
 x=.065+i*.24
 fig.text(x,.72,h,fontsize=13,weight='bold',color='#145e57')
 fig.text(x,.61,ts[0],fontsize=24,weight='bold',color='#157c6f')
 for j,t in enumerate(ts[1:]):fig.text(x,.50-j*.075,t,fontsize=11,color='#173e47')
fig.text(.06,.21,'보완한 결과',fontsize=12,weight='bold',color='#153f49')
fig.text(.06,.155,'‘AED 대여’ 하나로 합치지 않고 교육용·실제 장비, 수료증 여부, 기간과 신청조건을 따로 제공합니다.',fontsize=12,color='#153f49')
fig.text(.06,.06,'출처: 부산 소방안전교육 main/25 · 대여 공고 14491 · 기장군 보건소 AED 대여 안내 / 확보 2026-09-16',fontsize=10,color='#456661')
for ext in ['png','svg']:fig.savefig(O/f'service_conditions_comparison.{ext}',dpi=165,bbox_inches='tight',facecolor=fig.get_facecolor())
plt.close(fig)
