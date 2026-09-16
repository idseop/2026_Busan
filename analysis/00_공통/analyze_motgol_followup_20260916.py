"""Separate historical diagnoses, completion, and evaluation evidence on a local project timeline."""
from pathlib import Path
import json,hashlib
import pymupdf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/followup'
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
for s in manifest['sources']:
    if s['status']=='downloaded':assert hashlib.sha256((ROOT/s['localFile']).read_bytes()).hexdigest()==s['sha256']
page=pymupdf.open(OUT/'namgu-investment-2025.pdf')[14].get_text()
assert '100%' in page and '전체 사업 완료' in page and '2025.' in page
speech=(OUT/'namgu-council-motgol-20241111.txt').read_text(encoding='utf-8')
assert all(t in speech for t in ['8건','5cm','3cm','2024-11-11'])
contract=json.loads((OUT/'evaluation-detail.json').read_text(encoding='utf-8'))
c=contract['data'];pay=contract['data1']
assert c['ctrtYmd']=='20260114' and c['compltYmd']=='20260520'
assert pay['total']==c['ctrtAmt'] and pay['balance']==0
result={'region':'남구 대연동','place':'못골시장 일원','project':'못골시장 일원 보행환경개선사업','receiptCaseId':'action-10',
 'relationship':'동일 동의 후속 현장사업 사례. 119 교통 신고 736건을 이 시장 사고 또는 보행 전도사고로 배정하지 않음.',
 'construction':{'completionMonth':'2025-02','progressPercent':100,'roads':5,'lengthKmPublished':1.3,'status':'공식 재정공시상 전체 사업 완료','source':'https://www.bsnamgu.go.kr/open/2025/2en_1105/19.pdf','pdfPage':15},
 'councilIssue':{'statementDate':'2024-11-11','reportedReceivedAccidents':8,'issue':'경계석 걸림·미끄러짐에 관한 민원 지속 발언','priorChangeCm':[5,3],'evidenceLevel':'의원이 보고받은 문서를 인용한 공식 발언; 해당 접수 원장 미확보','excludedClaim':'추정 30건 이상 및 인과관계 단정은 프로젝트의 확인 사실로 채택하지 않음','source':'https://council.bsnamgu.go.kr/record/main?uid=11054'},
 'evaluation':{'contractDate':c['ctrtYmd'],'contractStart':c['ctrtStartYmd'],'contractEnd':c['ctrtEndYmd'],'completionDateField':c['compltYmd'],'inspectionDateField':c['inspYmd'] or None,'amountWon':int(c['ctrtAmt']),'paidWon':int(pay['total']),'balanceWon':int(pay['balance']),'status':'공식 계약에 효과평가용역 준공일·전액 지급 기재','reportObtained':False,'findingsKnown':False,'source':'http://contract.bsnamgu.go.kr/basis/situationView.do?ctrtAcctBookMngNo=202600210161'},
 'conclusion':{'confirmed':'사업이 없던 곳이 아니라, 현장 문제 제기 이후 준공과 효과평가까지 진행된 지역이다.','notConfirmed':['2026년에도 같은 민원이 남아 있다는 주장','못골사거리 단기 3항목이 이 시장사업으로 해소됐다는 주장','공사로 인한 사고의 인과효과','효과평가 자체가 없다는 주장'],
 'improvementCandidate':'이미 수행된 효과평가의 대상 구간·평가항목·결과와 과거 경계석 민원 조치를 지점별로 대조해, 교통 충돌과 걸림·미끄러짐을 나눠 결과와 잔여 조치를 제공한다. 중복 시설 설치나 새 평가용역 발주는 제안하지 않는다.',
 'nextExactEvidence':['2026 효과평가용역 최종보고서·과업지시서 및 구간 도면','2023 못골사거리 단기개선 3항목의 항목별 조치일·위치·완료 증빙','2024 경계석 민원 8건의 비식별 집계·조치 결과와 준공 이후 재접수 여부']},
 'collectionAttempt':{'evaluationReport':'공식 계약의 존재·준공·대금까지 확인. 계약 공개 목록·상세에 최종보고서 첨부를 확인하지 못함. 보고서 미공개 또는 미작성이라고 단정하지 않음.'}}
(OUT/'followup-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic'
fig,ax=plt.subplots(figsize=(14,6.7));ax.axis('off')
events=[('2023.05','1차 공사 준공','2025 재정공시','#146e82'),('2024.11','경계석 민원 지속 발언','보고 문서상 8건 · 원장 미확보','#b77720'),('2025.02','전체 공사 완료','공식 공정률 100%','#146e82'),('2026.05','효과평가용역 준공 기재','계약 1,898만 원 · 전액 지급','#146e82')]
ax.plot([.1,.9],[.51,.51],color='#c0cfd0',lw=3,transform=ax.transAxes)
for i,(d,t,desc,color) in enumerate(events):
    x=.11+i*.26
    ax.scatter([x],[.51],s=120,color=color,transform=ax.transAxes,zorder=3)
    ax.text(x,.67,d,ha='center',fontsize=18,fontweight='bold',transform=ax.transAxes,color=color)
    ax.text(x,.39,t,ha='center',fontsize=15,fontweight='bold',transform=ax.transAxes)
    ax.text(x,.25,desc.replace(' · ','\n'),ha='center',fontsize=12,transform=ax.transAxes,color='#52646b')
fig.suptitle('대연동 못골시장: 사업의 존재보다 개선 후 상태를 추적해야 합니다',fontsize=20,x=.5,y=.96)
fig.text(.045,.055,'2024 민원 내용은 의원의 공식 발언에 근거하며 인과효과를 입증하지 않음.\n2026 효과평가 결과 원문은 미확보 · 못골사거리의 별도 개선 3항목과 자동 병합하지 않음.',fontsize=12,color='#52646b')
fig.subplots_adjust(left=.02,right=.98,bottom=.16,top=.88)
for ext in ['png','svg']:fig.savefig(OUT/f'motgol_followup_timeline.{ext}',dpi=180)
plt.close(fig)
print(json.dumps(result['evaluation'],ensure_ascii=False))
