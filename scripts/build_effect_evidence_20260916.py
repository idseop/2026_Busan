"""Build an evidence-first report from verified aggregate inputs; no raw export."""
from pathlib import Path
import json, hashlib, shutil, html
from urllib.parse import urlencode
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

R=Path(__file__).resolve().parents[1]
N=R/'data/processed/효과근거확장-20260916'
O=R/'output/부산119-효과근거확장-20260916'
W=R/'web/final/results/effects'
O.mkdir(parents=True,exist_ok=True)
F=O/'figures';F.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)
inputs=['services/cpr-trend.json','services/prevention-effects.json','context/chs-education-summary.json','temporal/focus-summary.json','temporal/selection_stable_temporal.json','traffic/traffic-effects-extension.json']
cpr,services,chs,focus,stable,traffic=[read(N/p) for p in inputs]
education=read(R/'data/processed/고도화검증-20260916/education/service-conditions.json')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#193d49','text.color':'#193d49','axes.titleweight':'bold','figure.facecolor':'#ffffff','axes.unicode_minus':False,'svg.fonttype':'none'})
TEAL='#147d82';NAVY='#1d476a';ORANGE='#be7135';BLUE='#5795b8';LIGHT='#e5f2f1'
def save(fig,name):
    fig.savefig(F/f'{name}.png',dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(F/f'{name}.svg',bbox_inches='tight',facecolor='white');plt.close(fig)

fig,ax=plt.subplots(figsize=(11,4.8))
for region,color in [('전국',NAVY),('부산',TEAL)]:
    rows=[r for r in cpr['rows'] if r['region']==region]
    ys=[r['cpr_rate_percent'] for r in rows]
    ax.plot(range(2020,2025),ys,color=color,lw=3,marker='o',ms=7,label=region)
    for year,y in zip(range(2020,2025),ys):ax.annotate(f'{y:.1f}',(year,y),xytext=(0,10),textcoords='offset points',ha='center',color=color)
ax.set(xticks=range(2020,2025),ylim=(0,37),ylabel='일반인 심폐소생술 시행률 (%)',title='부산의 기록된 CPR 시행률은 2021년 이후 하락')
ax.grid(axis='y',alpha=.17);ax.legend(loc='lower left',ncol=2,frameon=False)
fig.text(.125,-.02,'2020–2024 급성심장정지조사 · 병원이송 환자 의무기록 기준 · 전국에 부산 포함',fontsize=10)
save(fig,'cpr-trend')

districts=['연제구','부산진구','수영구']
inds=['심폐소생술 교육 경험률','마네킹 실습 경험률','AED 실습 경험률']
fig,ax=plt.subplots(figsize=(11,4.6))
for j,(ind,color) in enumerate(zip(inds,[NAVY,TEAL,ORANGE])):
    rows=[next(r for r in chs['records'] if r['district']==d and r['subgroup']=='전체' and r['indicator']==ind) for d in districts]
    yy=np.arange(3)+(j-1)*.23
    xx=[r['crudeWeightedPercent'] for r in rows]
    ax.errorbar(xx,yy,xerr=[r['standardErrorPP'] for r in rows],fmt='o',color=color,ms=8,capsize=4,lw=2,label=ind)
    for x,y in zip(xx,yy):ax.text(x+3.1,y,f'{x:.1f}%',va='center',color=color,fontsize=11)
ax.set(yticks=range(3),yticklabels=districts,xlim=(0,39),xlabel='최근 2년 경험률 (%) · 점: 가중 조율 / 선: ±1 표준오차',title='교육 경험과 AED 실습 경험을 구분해 확인')
ax.invert_yaxis();ax.grid(axis='x',alpha=.15);ax.legend(loc='upper left',bbox_to_anchor=(0,-.19),ncol=3,frameon=False,fontsize=10)
fig.subplots_adjust(top=.88,bottom=.25)
fig.text(.125,-.02,'2024 지역사회건강조사 · 19세 이상 · 연제 n=908 / 부산진 n=903 / 수영 n=913 · 신뢰구간 아님',fontsize=10)
save(fig,'education-practice')

age_names=['19-29','30-39','40-49','50-59','60-69','70 이상']
# Use source labels, preserving all available disjoint adult age bands.
age_rows=[next(r for r in chs['records'] if r['district']=='연제구' and r['indicator']==inds[0] and r['subgroup']==age) for age in age_names]
assert len(age_rows)==6 and all(r['relativeStandardErrorPercent']<30 for r in age_rows)
fig,ax=plt.subplots(figsize=(11,4.6))
ax.errorbar(range(len(age_rows)),[r['crudeWeightedPercent'] for r in age_rows],yerr=[r['standardErrorPP'] for r in age_rows],color=TEAL,fmt='o-',ms=7,capsize=4,lw=2)
for i,r in enumerate(age_rows):ax.text(i,r['crudeWeightedPercent']+r['standardErrorPP']+2,f"{r['crudeWeightedPercent']:.1f}%",ha='center',fontsize=11)
ax.set(xticks=range(len(age_rows)),xticklabels=[r['subgroup'].replace(' 이상','세 이상')+('세' if '-' in r['subgroup'] else '') for r in age_rows],ylim=(0,65),ylabel='교육 경험률 (%)',title='연제구 주민의 교육 경험은 연령별 차이가 있음')
ax.grid(axis='y',alpha=.15)
fig.text(.125,-.02,'2024 · 최근 2년 교육 경험의 가중 조율 · ±1 표준오차 · 신고자 연령 및 교육 신청수요와 별개',fontsize=10)
save(fig,'yeonje-education-age')

for name in ['monthly_year_comparison','leave_one_season']:
    for suffix in ['png','svg']:shutil.copy2(N/f'temporal/{name}.{suffix}',F/f'{name}.{suffix}')

def table(headers,rows,cls=''):
    return '<div class="table-wrap"><table class="'+cls+'"><thead><tr>'+''.join('<th>'+h+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def figure(name,title,caption):
    return f'<figure><img src="figures/{name}.png" alt="{esc(title)}"><figcaption>{caption} <a href="figures/{name}.svg">벡터 그림</a></figcaption></figure>'
def case_link(dong,typ,district):
    return '../followup/explorer.html?'+urlencode({'district':district,'dong':dong,'type':typ,'scope':'C'})

cpr_table=table(['연도','부산 시행률','부산 CPR을 받은 환자','전국 시행률'],[[str(y),f"{next(r for r in cpr['rows'] if r['region']=='부산' and r['year']==y)['cpr_rate_percent']:.1f}%",f"{next(r for r in cpr['rows'] if r['region']=='부산' and r['year']==y)['cpr_performed_patients']:,}명",f"{next(r for r in cpr['rows'] if r['region']=='전국' and r['year']==y)['cpr_rate_percent']:.1f}%"] for y in range(2020,2025)])
chsrows=[]
for d in districts:
    rr=[next(r for r in chs['records'] if r['district']==d and r['subgroup']=='전체' and r['indicator']==i) for i in inds]
    chsrows.append([d,rr[0]['sampleN']]+[f"{r['crudeWeightedPercent']:.1f}% (SE {r['standardErrorPP']:.1f})" for r in rr])
chs_table=table(['구','표본 n','교육 경험','마네킹 실습','AED 실습'],chsrows)
temporal_rows=[]
interpretations={
 '연산동':'연중 교육·실습 안내를 유지. 특정 계절 전용 사업 근거는 아님.',
 '부전동':'겨울 전용 대책으로 제한하지 않음. 정비 전후의 같은 구간 비교가 우선.',
 '광안동':'봄 단독 집중보다 연중 비교. 처리조건에 민감한 사례라는 기존 판단 유지.',
 '초읍동':'최고계절이 자주 바뀜. 계절별 인력 배치 근거로 사용하지 않음.',
 '금성동':'겨울 결과를 단독 처방으로 확대하지 않음. 기존 정비·통제 기간 구분.',
 '다대동':'여름 안내와 기존 운영기간을 대조할 근거. 해수욕장 내 사건 또는 인력 부족 입증은 아님.',
 '우동':'최고월과 최고계절이 다름. 수난 유형·현장별 원인 및 위치는 미확정.',
 '기장읍':'최고월 5회 중 1회 유지. 특정 월 화재 예방에만 집중하지 않음.',
 '온천동':'동률 포함 최고월은 유지 안 됨. 연중 주택 예방 안내 유지.'}
for r in focus:
    temporal_rows.append([f'<a href="{case_link(r["rawDong"],r["subtype"],r["district"])}">{r["rawDong"]} · {r["subtype"]}</a>',f'{r["count"]:,}건','·'.join(str(m)+'월' for m in r['topMonths']),'/'.join(r['topSeasons']),f"{r['leaveOneMonthExact']}/5",f"{r['leaveOneSeasonExact']}/5",interpretations[r['rawDong']]])
temporal_table=table(['지역·유형','5년 접수','최고월','최고계절','월 유지','계절 유지','이번 판단'],temporal_rows)
service_rows=[]
for r in education['records'][:3]:service_rows.append([r['name'],r['target'],r['duration'],r['certificate'],r['condition']+f'<br><a href="{esc(r["url"])}">공식 이용 안내</a>'])
service_table=table(['기존 서비스','대상','시간·기간','수료증','이용 조건'],service_rows)
road_table=table(['대상','이번에 확인한 대응','현재 결론'],[
 ['부전역 맞이길','중앙대로783번길 일원 설계: 투수블록 3,222㎡, 점형 유도 88㎡·선형 138㎡. 버스표지판 4개소, 카트보관소 1·쉼터 결합형 1, 유도사인 2개소. 2026.2.5 제막식 기록.','보행 접근환경 보완이 포함된 기존 사업. 설계수량은 준공 검수수량과 다름. 2024 BDI 조사선 9개와 정확한 일치는 미확정.'],
 ['광안역 일원','BDI 지도에 조사선이 있으나 팝업 거리합 1,102.5m와 표의 조사거리 1,034.4m는 68.1m 차이. 2025 수영로 포장 검사·지급 기록 확인.','지도 경로를 실제 조사구간 원자료로 쓰지 않음. 수영로 포장과 내부도로 보차분리 개선을 구분.'],
 ['못골시장','2025 완료 발표에 더해 2026 효과평가 용역 계약·준공 기록 확인.','기존 기관도 평가를 수행함. 평가보고서 수치가 없어 사고·보행 개선효과는 미기재.'],
 ['거제천로101~121','2024.12 상임위에서 해당 구간 펜스 예산 3,740만원 삭감 논의 확인.','최종 예산·집행·현재 설치는 미확정. 현장 미조치 또는 신규 설치 필요로 확정하지 않음.']])
effect_rows=[
 ['현재 결과물','지역별 반복·시간 민감도, 주민 구성, 이용조건, 기존 사업을 함께 제공','공식 원문 일치·필터별 수치·링크·파일 실행 검증','검증 기록에 실행 결과 기재'],
 ['직접 기대효과','목적에 맞는 교육·실습 경로 선택, 지난 사업과 현재 상태의 혼동 감소','같은 과제의 정답률·중앙 소요시간·오선택률','사용자 실험 미실시. 향상률 제시 안 함'],
 ['운영 후 효과','실제 참여·수료와 술기 유지, 실제 접근·정비 개선','신청/완료/탈락 인원, 술기 평가, 동일 구간 전후 현장값','기관·참여자 동의 및 비교 설계 필요'],
 ['장기 효과','실제 CPR 수행·환자 예후·사고 피해 변화','구급·의무기록, 발생 조건 및 기록 완전성, 비교지역','본 웹의 인과효과 미입증']]
effect_table=table(['단계','보완 내용 또는 기대 경로','측정값','현재 상태'],effect_rows)
measurement=[
 {'id':'information-choice','unit':'동의한 참여자×사전 고정 과제','design':'기존 공공페이지/시제품 교차배치·순서 균형. 과제 문구와 정답을 먼저 고정. 시간만으로 성과 판정하지 않음.','primary':'과제 정답률 = 정확한 완료 과제 / 제시 과제','secondary':['완료·실패·중도탈락을 구분한 소요시간','잘못된 수료증/실제AED 선택률','출처·기준일 확인 성공률'],'status':'실험 미실시','targetEffect':None},
 {'id':'education-uptake','unit':'비식별 신청·참여자','design':'안내 노출·동의와 신청·실참여·수료·술기평가를 구분. 미참여 원인을 직접 조사.','primary':'실제 참여 / 동의한 안내 대상','secondary':['술기 평가 기준 충족 / 평가 참여','연령별 접근 방식·탈락 사유'],'status':'기관 자료 미확보','targetEffect':None},
 {'id':'road-response','unit':'같은 시작·끝점의 조사구간','design':'BDI 조사선-최종준공도면-현장좌표 확인 후 동일 요일·시간·날씨 전후 관측, 가능하면 비교구간.','primary':'구간별 보차분리·장애물 상태의 전후 일치 측정','secondary':['보행시간·대기시간·통행량','공사 완료 시점 이후 사고기록과 노출량'],'status':'도면·구간별 원자료 미확보','targetEffect':None},
 {'id':'aed-availability','unit':'등록ID가 일치하는 장비','design':'등록정보·실제 운영시간·접근 제한·점검시점 교차 확인, 임의 좌표 배정 없음.','primary':'확인한 대상 중 게시 정보와 실제 접근 조건 일치 비율','secondary':['폐쇄 시간과 운영시간의 차이','작동·소모품 확인 일자'],'status':'현장 운영·점검 이력 미확보','targetEffect':None}]
(O/'effect-measurement.json').write_text(json.dumps(measurement,ensure_ascii=False,indent=2),encoding='utf-8')

sections=[]
def section(id,title,body):sections.append(f'<section id="{id}"><div class="section-title"><span>{len(sections)+1:02}</span><h2>{title}</h2></div>{body}</section>')
section('purpose','반복 신고를 현재의 예방·지원 선택으로 연결',f'''<p class="lead">지역의 신고 건수만으로는 예방안을 고를 수 없습니다. <b>반복되는 신고 → 주민·현장 배경 → 이미 제공 중인 대응 → 지금 보완할 정보와 검증</b>을 연결했습니다.</p><div class="findings"><article><span class="tag">문제 배경</span><h3>부산 CPR 기록의 하락</h3><p>2021년 20.8%에서 2024년 13.8%. 주민 교육·실습 경험과 이용 가능한 과정을 함께 살폈습니다.</p></article><article><span class="tag">지역 판단</span><h3>반복과 계절 집중은 다름</h3><p>선택 조건에 안정적인 325개 조합 중, 한 해씩 빼도 최고계절이 모두 같은 조합은 121개였습니다.</p></article><article><span class="tag">기존 대응</span><h3>이미 한 사업까지 반영</h3><p>부전의 구체적 설계와 못골의 평가 수행을 확인했습니다. 과거 조사만으로 새 시설을 제안하지 않습니다.</p></article></div><p>공공 안전지도·교육·점검·정비는 이미 운영되고 있습니다. 이번 결과의 차별점은 이 자료들을 <b>지역별 신고의 신뢰도와 대응 시점까지 함께 비교</b>하도록 연결한 것입니다. 정부에 해당 기능이 전혀 없다는 주장은 아닙니다. <a href="https://www.mois.go.kr/frt/sub/a06/b10/safemap/screen.do">기존 생활안전지도</a></p>''')
section('cpr','부산의 초기대응을 살펴볼 근거를 추가 확인',figure('cpr-trend','부산과 전국 CPR 시행 추이','출처: 질병관리청 2024 급성심장정지조사 통계집 표42, PDF75–76쪽.')+cpr_table+'''<p>2024년 부산은 전국보다 <b>16.5%p 낮습니다.</b> 이는 기록된 초기대응 현황의 차이입니다. 교육 부족이 원인이라고 입증하거나 연산동의 시행률로 적용하지 않습니다.</p><p class="note">병원이송 급성심장정지 환자 중 의무기록조사 자료이며, 근무 중 구급대원·의료인 발견/목격 사례는 제외됩니다. 발생장소 기준이고 일부 주소 결측은 출동센터 주소로 대체됩니다. 의무기록 누락으로 실제 시행보다 낮게 집계될 수 있습니다. 정확한 분모 인원은 원표에 없어 역산하지 않았습니다.</p><p><a href="https://www.kdca.go.kr/injury/biz/injury/recsroom/statsSmMain.do">공식 통계집</a> · <a href="data/cpr-trend.csv">5년 집계 CSV</a></p>''')
section('education','주민의 교육 경험과 실제 실습 경험은 별도 지표',figure('education-practice','세 구의 교육 및 실습 경험','세 지표 모두 조사 응답자가 분모입니다. 교육 참여자 중 실습률이 아닙니다.')+chs_table+'''<p>세 구 모두 AED 실습 경험의 점추정치가 교육 경험보다 낮습니다. <b>교육 안내에 실습 내용과 준비 도구를 구분해 보여줄 이유</b>가 됩니다. 이 차이 자체를 교육 품질 부족이나 미충족 수요로 판정하지 않습니다.</p><p class="note">2024년 19세 이상 주민의 최근 2년 경험, 가중 조율. 괄호는 표준오차(SE, %p)이며 신뢰구간이 아닙니다. 구 간 순위·유의한 격차를 주장하지 않습니다. 표본 인원에 비율을 곱해 경험자 수를 추정하지 않습니다.</p>'''+figure('yeonje-education-age','연제구 연령별 CPR 교육 경험','연령별 표본의 교육 경험입니다. 119 신고자의 연령 추정에 사용하지 않았습니다.')+'''<p>연제구 19–29세 교육 경험은 48.8%(SE 5.8), 70세 이상은 7.6%(SE 2.1)였습니다. 주민 안내는 전 연령을 유지하며 교육 이력·실습 목적에 맞춰 제공하고, 실제 이용 장벽은 별도 참여 자료로 확인합니다.</p><p><a href="https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do">공식 지역사회 건강통계</a> · <a href="data/chs2024-cpr-education.csv">전체·성·연령별 99개 집계값</a></p>''')
section('yeonsan','연산동: 연중 교육·실습 안내를 구체화',f'''<div class="case-head"><strong>511건</strong><p>연산동으로 접수된 심정지 관련 신고<br>2020–2024 · 정상 처리·운영성 제외</p><a class="button" href="{case_link('연산동','심정지','연제구')}">연산동 상세 결과</a></div><p>같은 이동전화 비교집합 710건 중 511건이 남았고, 반복·증감 방향은 세 처리조건에서 유지됐습니다. 다만 최고계절은 한 해 제외 비교 5회 중 4회만 같았습니다. <b>특정 계절에만 한정하지 않는 안내</b>가 현재 근거에 맞습니다.</p><p>주민 배경은 연산1–9동 중 존재하는 8개 행정동 후보별로 제공합니다. 예를 들어 연산3동의 65세 이상 인원은 2020년 2,160명에서 2024년 2,744명으로 늘었지만, 비중은 29.11%에서 26.77%로 낮아졌습니다. 구성비만으로 주민 규모 변화를 판단하지 않도록 인원·비중을 함께 표시합니다.</p>{service_table}<div class="result"><b>보완 결과</b><p>기본 교육, 수료증 과정, 교육용 기자재 대여를 목적·시간·대상별로 연결했습니다. 교육용 AED는 환자에게 사용하는 AED와 구분했습니다. 공식 기관의 실제 재고·예약 가능을 보장하지 않습니다.</p></div><p class="note">부산 CPR 시행률, 연제구 주민 표본, 연산동 신고, 행정동 후보별 주민 통계는 서로 다른 자료입니다. 개인 단위로 결합하거나 교육 경험이 낮은 연령의 신고로 바꾸지 않았습니다.</p>''')
section('temporal','반복되는 지역이라도 최고 시기는 달라질 수 있음','''<p>194개 지역명×5유형의 <b>970개 조합</b>에 대해 전체 5년·각 연도·한 해 제외 5회, 총 11개 기간을 재계산했습니다. 월·계절의 길이가 달라 <b>해당 기간 달력일수당 접수</b>로 최고 시기를 비교했습니다.</p>'''+figure('leave_one_season','주요 사례 최고계절의 연도 제외 안정성','같은 최고계절 집합이 유지된 횟수입니다. 미래 예측 적중률이나 통계적 유의확률이 아닙니다.')+temporal_table+'''<p>기존 선택 영향 검증에서 반복·증감 방향이 유지된 325개 조합 중 최고월은 33개, 최고계절은 121개가 다섯 제외 비교 모두에서 같았습니다. 연도당 최소 20건인 86개로 좁혀도 최고계절 유지 조합은 35개였습니다.</p><p class="note">이 분석은 정상 처리·운영성 제외 자료에서 실시했습니다. 월·계절 자체의 결측 제외 전후 안정성을 검사한 것은 아닙니다. 작은 차이·동률도 최고 시기를 바꿀 수 있으므로 변동을 위험 또는 효과의 증거로 사용하지 않습니다. 겨울은 같은 연도의 1·2·12월이며 연속된 한 겨울이 아닙니다.</p><p><a href="data/stability_profiles.csv">970개 안정성 집계</a> · <a href="data/selection_stable_temporal.json">선택 조건에 안정적인 조합의 층별 결과</a></p>'''+figure('monthly_year_comparison','주요 사례의 연도별 월 분포','각 연도와 전체 기간의 달력일수당 접수 비교. 실제 주민 노출량을 분모로 한 위험률이 아닙니다.'))
section('roads','도로 분야는 기존 정비를 반영해 결론을 수정',road_table+'''<div class="result"><b>보완 결과</b><p>“과거 조사에서 문제가 있었으니 지금 같은 시설을 더 설치”하는 연결을 제거했습니다. 기존 사업의 설계·완료·평가 단계를 표시하고, 개별 조사구간이 실제로 개선됐는지는 최종 도면·현장 상태와 분리했습니다.</p></div><p>BDI 조사는 실제 고령 환자 추적이나 119 신고 지점 분석이 아닙니다. 지도 팝업의 거리·도보 예상시간을 실측값으로 복제하지 않았습니다.</p><p><a href="https://data.bdi.re.kr/PDF/View.do?dir=report&amp;path=RPT_00000000001&amp;savename=20250715172207_54971">부산연구원 원 보고서</a> · <a href="https://www.busan.go.kr/photobodo/1717850">부전역 맞이길 제막식</a> · <a href="data/traffic-effects-extension.json">사업별 근거 상태</a></p>''')
section('other','주택·산악·수난도 기존 조치와 함께 해석',table(['사례','관측·기존 대응을 함께 읽은 결과','보완 범위'],[
 ['다대동 수난 67건','여름 최고는 한 해 제외 5회 모두 유지. 기존 해수욕장 여름 운영과 비개장 관리 자료를 함께 확인.','기존 운영기간과 안전 안내를 연결. 신고가 해수욕장 안에서 발생했거나 운영 인력이 부족하다고 판정하지 않음.'],
 ['우동 수난 57건','최고월은 5월, 최고계절은 가을. 월 한 개와 계절 합계의 결과는 다름.','해변·하천·항만 등 실제 발생장소가 구분되지 않아 특정 시설 보완안은 확정하지 않음.'],
 ['초읍동 산악 64건·금성동 61건','초읍의 2025 매트·울타리, 금정산 로프·안내 정비를 반영. 최고계절은 각각 2/5·4/5 유지.','이미 시행한 정비를 신규 공백으로 제안하지 않음. 기존 코스별 안전 안내와 유효한 통제 기간을 구분.'],
 ['기장읍 주택화재 76건·온천동 53건','주택 구조·기존 예방교육 자료를 연결. 최고월은 1/5·0/5 유지.','연중 주택 예방 안내를 유지. 건축물·세대별 피해 또는 신규 소방시설 수량은 추정하지 않음.']])+'''<p>해당 수치는 2020–2024 정상 처리·운영성 제외 접수입니다. 기존의 상권·생활인구·주택·시설 자료는 각 질문에 필요한 사례에서만 사용했습니다. 벌집제거는 심층 검토와 보완안에서 제외했습니다.</p><a href="../advance/index.html">기존 전체 심층 결과·출처</a>''')
section('gaps','확인한 공백과 이번에 해결한 부분',table(['구분','확인 근거','이번 처리'],[
 ['초기대응 현황 차이','부산의 기록된 CPR 시행률 하락, 구 단위 주민 교육·실습 경험','부산 배경→연산 신고→연제 교육 경험→기존 과정으로 연결. 원인·개별 수요는 미확정.'],
 ['공개 정보의 조건 충돌','사하 공고 운영 종료 7.31·신청 종료12.31 및 10명 개설 조건 상충, 2026.9.16 재확인','시제품에서 현재 예약 가능으로 안내하지 않고 사전협의 경로를 제공. 기관 원공고 수정이나 교육 중단의 증거가 아님.'],
 ['기록을 오해한 분석 오류','13행은 조치 전용란이 아닌 일반 비고 공란','미조치 시설13곳·조치 누락률이라는 해석 삭제. 실제 명령·이행 기록과 구분.'],
 ['과거 조사와 현재 사업의 연결 부족','부전 설계 내역, 광안 거리 불일치, 못골 평가 수행','기존 대응의 구체 내용을 추가. 조사선과 최종 시공선의 정확한 일치는 미확정.'],
 ['맞춤 안내에 필요한 정보 결합','지역·시기·주민 배경·공식 서비스의 기간과 조건이 다른 자료에 존재','한 화면에서 비교하도록 결과 연결. 실제 사용자의 탐색 부담 감소는 아직 측정 안 됨.']])+'''<p class="note">자료를 확보하지 못한 상태와 실제 서비스 부재를 구분했습니다. 외부 기관에 공문·문의·예약을 보내지 않았으며 공개 자료의 확인 범위까지 반영했습니다.</p>''')
section('effects','기대효과를 측정 가능한 단계로 정리',effect_table+'''<p class="lead">가장 직접적인 기대효과는 <b>이용 목적에 맞는 경로 선택과 현재 상태의 정확한 이해</b>입니다. 이를 먼저 측정하고, 참여·술기·피해 감소는 후속 효과로 검증해야 합니다.</p><p>비교 실험은 동일 과제에서 기존 공공페이지와 시제품의 제시 순서를 균형 있게 배치하고, 정답·실패·중도탈락·시간을 모두 기록하도록 명세했습니다. 향상률이나 필요한 실험 표본 수를 결과에 맞춰 정하지 않았습니다.</p><p><a href="effect-measurement.json">효과 측정 명세</a> · <a href="보고서.md">분석·보완 보고서</a></p>''')
section('sources','데이터·코드·검증의 연결','''<p>신고 704,689건의 기존 선택 기준을 유지했습니다. 전체 처리 A 704,689건, 정상 처리 B 579,412건, 정상 처리·운영성 제외 C 574,662건입니다. 새 시간 분석의 5유형 C 합계는 41,720건입니다.</p><p>공식 통계집의 10개 CPR 값, 지역사회건강조사 99개 집계값, 시간 교차집계, 사업 설계와 기존 대응을 각각 검증했습니다. 통계표·원문·코드의 해시를 보존했고, 공개 화면에는 접수번호·개별 신고 좌표·원시설 명부를 추가하지 않았습니다.</p><p><a href="검증기록.md">독립 검증과 실행 기록</a> · <a href="data/input-manifest.json">입력 해시</a> · <a href="data/sources.json">공식 출처 목록</a></p><p class="note">2026.9.16 확보 자료 기준입니다. 현재 신고를 수신하는 실시간 서비스가 아닙니다. 과거 5년 신고와 2024 조사·2025–2026 대응을 각각의 기준일로 제공합니다.</p>''')

css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:#f4f7f6;color:#193d49;font:16px/1.75 "Malgun Gothic",sans-serif}a{color:#096e78;text-underline-offset:3px}a:hover{color:#124364}button,a:focus-visible{outline:3px solid #ba7134;outline-offset:3px}header{position:sticky;top:0;z-index:4;background:#143e4e;color:#fff;padding:12px 3vw;display:flex;align-items:center;gap:25px;box-shadow:0 2px 8px #153c4920}header strong{font-size:18px}header nav{margin-left:auto;display:flex;gap:24px}header a{color:#fff;font-size:14px}main{max-width:1380px;margin:0 auto;padding:30px 42px 70px}.intro{display:grid;grid-template-columns:1.8fr 1fr;gap:45px;padding:15px 0 28px;border-bottom:2px solid #bfd5d5}.eyebrow{font-size:14px;color:#287d80;font-weight:700;margin:0}h1{font-size:36px;line-height:1.3;margin:12px 0}h2{font-size:25px;line-height:1.45;margin:0}h3{font-size:19px;line-height:1.5;margin:8px 0}p{margin:12px 0}.intro p{font-size:18px}.intro aside{align-self:center;background:#e1efed;border-left:4px solid #1e8384;padding:18px 24px}.toc{display:flex;flex-wrap:wrap;gap:12px 24px;padding:20px 0}.toc a{font-size:14px}section{padding:34px 0;border-bottom:1px solid #cadbdc}.section-title{display:flex;gap:16px;align-items:center;margin-bottom:22px}.section-title>span{font-size:26px;font-weight:700;color:#6a9fa2}.lead{font-size:19px;line-height:1.85}.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;margin:25px 0}.findings article{border-top:3px solid #36888a;padding-top:15px}.tag{font-size:13px;font-weight:700;color:#7b593c}.note,figcaption{font-size:14px;color:#506971}.note{border-left:3px solid #b2cace;padding-left:16px}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;margin:18px 0;background:#fff}th{text-align:left;background:#e3efee;color:#214e5c;padding:12px 14px;white-space:nowrap}td{padding:12px 14px;border-bottom:1px solid #dce7e6;vertical-align:top}td:first-child{font-weight:700;min-width:95px}figure{margin:25px 0 30px;background:white;padding:18px 20px}figure img{width:100%;display:block;height:auto}figcaption{padding:12px 5px 0}.result{background:#e3eeeb;padding:18px 24px;border-left:4px solid #24837d;margin:25px 0}.result>b{font-size:18px}.case-head{display:flex;align-items:center;gap:26px;border-bottom:1px solid #cbdada;padding-bottom:18px}.case-head>strong{font-size:38px;color:#137e81}.button{display:inline-block;background:#156d78;color:#fff;border-radius:5px;padding:10px 18px;text-decoration:none;font-size:14px}.case-head .button{margin-left:auto}footer{font-size:13px;padding:20px 0;color:#5b6e75}@media(max-width:850px){main{padding:20px}.intro,.findings{grid-template-columns:1fr}.intro{gap:15px}header{position:static;flex-wrap:wrap;gap:8px}header nav{margin-left:0;gap:15px}.case-head{flex-wrap:wrap}h1{font-size:29px}figure{padding:8px}}@media print{header,.toc{display:none}body{background:white}main{padding:0}section{break-inside:auto}figure,table{break-inside:avoid}}'''
header='''<header><strong>부산 119 · 근거와 보완 결과</strong><nav><a href="../../index.html">부산 지도</a><a href="../followup/explorer.html">지역별 결과</a><a href="../advance/index.html">기존 심층 분석</a></nav></header>'''
doc='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 · 문제 배경에서 보완 결과까지</title><link rel="stylesheet" href="style.css"></head><body>'+header+'''<main><div class="intro"><div><p class="eyebrow">부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>반복 신고에서<br>현재의 예방·지원 선택까지</h1><p>2020–2024 신고 분석에 주민 교육 경험과<br>기존 대응을 더해, 보완할 범위를 구체화했습니다.</p></div><aside><b>이번 확장의 결론</b><p>교육·실습은 목적별로 연결하고,<br>예방 시기는 여러 해에서 확인하며,<br>현장 제안에는 이미 한 사업을 반영합니다.</p></aside></div><nav class="toc"><a href="#cpr">부산 초기대응</a><a href="#education">주민 교육·실습</a><a href="#yeonsan">연산동 사례</a><a href="#temporal">시기 검증</a><a href="#roads">도로 대응</a><a href="#gaps">보완한 공백</a><a href="#effects">기대효과</a></nav>'''+''.join(sections)+'<footer>2026.9.16 분석 갱신 · 공식 통계와 검증된 집계에 근거한 연구 결과</footer></main></body></html>'
(O/'style.css').write_text(css,encoding='utf-8')
(O/'index.html').write_text(doc,encoding='utf-8')

data=O/'data';data.mkdir(exist_ok=True)
for rel in ['services/cpr-trend.csv','context/chs2024-cpr-education.csv','temporal/stability_profiles.csv','temporal/selection_stable_temporal.json','traffic/traffic-effects-extension.json']:
    shutil.copy2(N/rel,data/Path(rel).name)
sources=[{'title':'급성심장정지조사2024 표42','url':cpr['source'],'landing':'https://www.kdca.go.kr/injury/biz/injury/recsroom/statsSmMain.do','referenceYear':'2020–2024','acquired':'2026-09-16'},
 {'title':'지역사회건강조사2024 지역 통계집','url':'https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do','districts':districts,'referenceYear':'2024','acquired':'2026-09-16'},
 {'title':'부산연구원 보행환경 조사','url':'https://data.bdi.re.kr/PDF/View.do?dir=report&path=RPT_00000000001&savename=20250715172207_54971','referenceYear':'2024 조사','acquired':'이전 검증 자료 재사용'},
 {'title':'부전 맞이길 공사 공고·설계','url':'https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01083291&bidPbancOrd=000&fileSeq=2&fileType=&prcmBsneSeCd=07','referenceYear':'2025 설계','acquired':'2026-09-16'},
 {'title':'부전 맞이길 시설물 설계','url':'https://www.g2b.go.kr/pn/pnp/pnpe/UntyAtchFile/downloadFile.do?bidPbancNo=R25BK01193201&bidPbancOrd=000&fileSeq=2&fileType=&prcmBsneSeCd=07','referenceYear':'2025 설계','acquired':'2026-09-16'},
 {'title':'부산소방 교육·기자재','url':'https://119edu.busan.go.kr/main/25','referenceYear':'2026 확인','acquired':'2026-09-16'},
 {'title':'부산 AED정보 확인과 관리대책','url':'https://www.busan.go.kr/nbtnewsBU/1691436','referenceYear':'2025','acquired':'2026-09-16'}]
(data/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=[{'path':str((N/rel).relative_to(R)),'sha256':sha(N/rel)} for rel in inputs]
manifest.append({'path':str((R/'data/processed/고도화검증-20260916/education/service-conditions.json').relative_to(R)),'sha256':sha(R/'data/processed/고도화검증-20260916/education/service-conditions.json')})
(data/'input-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

report='''# 부산 119: 문제 배경에서 보완 결과까지 — 효과 근거 확장

## 이번 결과의 핵심

부산의 반복 신고를 현재의 예방·지원 선택에 연결하는 것이 목적이다. 새로 확보한 공식 환자 통계와 주민 교육 경험은 문제 배경을 보강하고, 계절 민감도는 활동 시기의 과도한 단정을 줄이며, 기존 사업 원내역은 중복 시설 제안을 걸러낸다. 정부의 미대응이나 본 웹의 사고 감소를 입증한 것은 아니다.

## 새로 확인한 사실

1. 질병관리청 2024 원 통계집 표42: 부산 일반인 CPR 시행률 2020–2024 19.7/20.8/20.0/16.4/13.8%, 전국26.4/28.8/29.3/31.3/30.3%. 2024차이16.5%p. 부산 시행인원294명은 조사 환자이며 연산 신고511건과 별개다. 발생장소 기준, 주소 결측의 센터주소 대체와 의무기록 과소기록 가능성을 보존한다. 표42에 정확한 분모 수가 없어 역산하지 않았다.
2. 공식 지역사회건강조사2024의 연제/부산진/수영 교육 경험29.0/26.7/24.3%, 마네킹27.1/24.0/22.7%, AED18.5/17.2/15.6%. 모두19세 이상 최근2년 경험의 가중 조율. 분모는 해당 조사응답자이며 교육경험자 중 실습률이 아니다. SE/RSE 포함99개 셀 확보. 표준화율·신뢰구간은 추출표에 없어 비워두었다. 구 간 유의성검정이나 순위를 주장하지 않는다.
3. 연제19–29세 교육경험48.8%(SE5.8),70세 이상7.6%(SE2.1). 주민의 교육경험 차이지 환자의 나이나 미충족 수요가 아니다. 전 연령 인구배경을 유지하며 기본·수료증·실습기자재의 목적별 안내를 보완한다.
4. 검증된 전처리17컬럼 자료5년에서 970개 지역×유형을 11기간으로 집계해128,040월집계행을 산출했다. 선택 조건에 안정적인 기존325조합 중, 한 해를 빼는5번 비교에서 최고월 유지33·최고계절121이다. 연도최소20건86조합에서도 계절유지35. 최고치 차이가 작을 수 있으므로 이것은 계절 집중 전략을 확정하기 전의 민감도 확인이지 통계적 유의성이나 미래예측검증은 아니다.
5. 연산심정지511건: 최고계절5회중4회 유지. 다대수난67건: 여름5/5유지. 월/계절 최고는 달력일수당값이며, 겨울은 같은 연도1·2·12월이다. 다대 신고의 정확한 수변 장소는 미확정이므로 해수욕장 인력 수요로 전환하지 않는다.
6. 부전역 맞이길 공식 설계: 투수블록3222㎡, 점형유도88㎡·선형138㎡, 버스표지4개소·카트보관1·쉼터결합1·유도2. 제작/설치/기초 행을 중복 합산하지 않았다. 설계와 최종 검수는 별개. 2026.2.5제막식은 기존 입력 재사용. 광안 지도팝업거리1102.5m와 원표1034.4m는68.1m차이여서 그대로 선자료로 쓰지 않는다.
7. 못골시장 평가 용역의 존재는 정부가 평가하지 않았다는 주장에 반한다. 평가 수치 미확보, 거제 위원회 예산삭감은 최종 집행/현재 미설치 증거가 아니다.

## 지역 보완 방향

- 연산: 연중 심정지 관련 정보에서 기본교육(12세이상,50–80분,수료증없음)·수료증 과정(240분,평가80점)·교육용 대여(7일,실제 AED아님)를 목적별 제공. 8행정동 후보 인구는 각각 표시한다. 2024구조사 교육경험과2026이용조건의 시점은 다르다.
- 부전·광안: 기존 공사와 같은구간 확인을 우선하며 신규 동일시설 설치를 확정하지 않는다. 상권·생활인구는 지역 배경이고 연구원 구간이나 환자 노출량이 아니다.
- 다대·우동: 월/계절 결과와 기존 운영기간을 구분해 안내. 특정해변 사고/상주인력 부족 입증은 하지 않는다.
- 초읍·금성: 기존 매트·울타리·로프 정비와 통제 종료시점을 반영. 한 계절 단독배치 근거 없음.
- 기장·온천: 기존 주택·예방교육 결과를 유지하되 월최고 불안정으로 연중 안내. 건축물별 사고나 신규시설수량 미추정.

## 공백의 구분

확인된 공개 정보 문제: 사하 공고의 운영/접수종료일·정확히10명 조건 상충, 부산시가2025확인한 일부 AED정보 불일치. 전자를 교육중단으로, 후자를 현재 모든 장비 미관리로 확대하지 않는다.

분석에서 해결한 부분: 일반 비고공란13행의 미조치 해석 제거, 최고시기 민감도 추가, 실습/교육·기존공사 단계 구분, 주민 인원과비중 분리. 현장 서비스 부족은 아직 별도의 근거가 필요하다.

## 기대효과와 측정

현재 구현은 지역 근거와 유효한 이용조건을 연결하는 정보 보완이다. 직접 기대효과는 올바른 경로 선택과 상태 판단이며, 실제 개선 정도는 동일 과제의 정확도·시간·오선택률로 측정한다. 사용자 교차설계·순서균형과 실패/탈락을 포함하는 분모를 effect-measurement.json에 고정했다. 아직 사용자 실험을 하지 않았으므로 효과율·사고감소·생존향상을 약속하지 않는다.

그 다음 단계는 동의 기반 실제 신청→참여→수료→술기 유지와 동일구간 전후관측이다. 환자 예후는 의료기록과 대조설계가 있어야 한다. 전국 CPR 시행/미시행 생존차를 본 웹의 예상효과로 복사하지 않는다.

## 남은 근거와 공개 수집의 결과

BDI 개별 조사선과 최종 준공도면, 못골 최종 평가보고서, 거제 최종 집행, AED등록ID별 접근/점검기록, 연산 교육실적은 공개 검색에서 확보하지 못했다. 시도한 공식 경로와 실패/검색단서는 각분야search-audit/search-attempts에 기록했다. 원PDF가404인 동래구 색인 단서는 확정표에 넣지 않았다. CHS 첨부의 curl요청은HTML을 반환해분석에서제외하고, 정상브라우저 세션의 공개첨부로 ZIP/XLSX/PDF를 확보했다.

## 재현

프로젝트 루트 Python환경 `.venv-check/Scripts/python.exe` 사용. 원 신고 및 공식첨부는 읽기전용 유지.

1. analysis/00_공통/analyze_temporal_transfer_20260916.py
2. scripts/verify_temporal_transfer_20260916.py
3. scripts/collect_prevention_effects_20260916.py (확보한 원문 보존 및 파싱)
4. scripts/probe_chs_public_20260916.py → extract_chs_education_20260916.py → summarize_chs_education_20260916.py
5. scripts/collect_traffic_effects_20260916.py analyse (공식 첨부 보존 후)
6. scripts/build_followup_explorer_20260916.py
7. scripts/build_effect_evidence_20260916.py
8. 별도 작성자가 수행한 내용/브라우저 검증과 배포 검증

전처리 재현은 원 프로젝트 입력명세와 의존성이 필요하다. 웹 배포본에는 개인 신고·대용량 CHS 원본·시설명부를 넣지 않는다. 배포본의표·그림·탐색은 파일직접 실행가능하며, 지도는 제공된serve.py와인터넷을사용한다. 주요 의존성:pandas,numpy,matplotlib,openpyxl,xlrd,PyMuPDF,olefile,pyhwp,playwright+Chrome. 해시와 세부명령은 각분야manifest 및수집코드참조.
'''
report=report.replace('부산 시행인원294명','부산에서 일반인 CPR을 받은 환자294명').replace('SE/RSE 포함99개 셀','SE/RSE 포함99개 집계행')
(O/'보고서.md').write_text(report,encoding='utf-8')
(R/'docs/40-분석결과/부산-119-효과근거확장-20260916.md').write_text(report,encoding='utf-8')
# Preserve tested source output links for direct file use; web gets its own hierarchy.
shutil.copytree(O,W,dirs_exist_ok=True)
doc_out=doc.replace('../../index.html','../../web/final/index.html').replace('../followup/','../부산119-전지역후속검증-20260916/').replace('../advance/','../부산119-쟁점해결-20260916/')
(O/'index.html').write_text(doc_out,encoding='utf-8')
mapfile=R/'web/final/index.html';s=mapfile.read_text(encoding='utf-8')
s=s.replace('href="results/advance/index.html">최신 분석 결과','href="results/effects/index.html">최신 분석 결과')
mapfile.write_text(s,encoding='utf-8')
print(json.dumps({'reportSections':len(sections),'figures':len(list(F.glob('*.png'))),'officialSurveyValues':len(chs['records']),'outputs':[str(O),str(W)]},ensure_ascii=False))
