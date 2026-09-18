"""Publish only aggregate, source-linked results from the additional evidence lane."""
from pathlib import Path
import csv, json, html, shutil, hashlib, zipfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'data/processed/동별보완-추가근거-20260916'
OUT=ROOT/'output/부산119-동별보완-심화결과-20260916'
OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
esc=lambda s:html.escape(str(s))
coverage=read(B/'place/coverage_all_busan.json')
time=read(B/'time/time-robustness.json')
follow=read(B/'followup/followup-evidence.json')
apt=read(B/'services/apartment-summary.json')
plt.rcParams.update({'font.family':FontProperties(fname='C:/Windows/Fonts/malgun.ttf').get_name(),'axes.unicode_minus':False,'font.size':12,'svg.fonttype':'none'})
latest=[r for r in coverage['districts'] if r['dataYear']==2025]
districts=list(dict.fromkeys(r['district'] for r in latest))
old=[next(r['designatedSiteRecords'] for r in latest if r['district']==d and r['category']=='보행노인') for d in districts]
child=[next(r['designatedSiteRecords'] for r in latest if r['district']==d and r['category']=='보행어린이') for d in districts]
assert sum(old)==49 and sum(child)==3 and len(districts)==16
fig,ax=plt.subplots(figsize=(13,7)); y=list(range(16))
ax.barh(y,old,color='#12766f',label='보행노인 지정지점')
ax.scatter(child,y,color='#dc8f26',s=55,label='보행어린이 지정지점',zorder=3)
ax.set_yticks(y,districts); ax.invert_yaxis(); ax.set_xlim(-.3,12)
for i,(a,b) in enumerate(zip(old,child)): ax.text(max(a,b)+.2,i,f'{a} / {b}',va='center')
ax.set_xlabel('공식 지정지점 기록 수 · 사고건수 또는 위험 순위가 아님')
ax.set_title('부산 16개 구·군의 보행사고 지정자료를 함께 확인했습니다',loc='left',pad=38,fontweight='bold')
ax.legend(loc='lower right'); ax.spines[['top','right']].set_visible(False)
fig.text(.125,.925,'한국도로교통공단 2025 자료연도 · 노인 49지점 / 어린이 3지점',fontsize=12)
fig.text(.125,.015,'목록에 없는 지역은 사고 0건이 아닙니다. 두 유형의 지정 기준과 집계 기간은 서로 다릅니다.',fontsize=10)
fig.tight_layout(rect=(0,.04,1,.93))
for ext in ['png','svg']:fig.savefig(OUT/f'busan_all16_coverage.{ext}',dpi=160,bbox_inches='tight')
plt.close(fig)

sections=[]
def add(title,body): sections.append((title,body))
add('신고 통계에서 실제 지점과 운영 조건까지', '''<p class="lead">같은 신고 유형이라도 지역의 반복 시기와 기존 시설의 이용 조건은 다릅니다. 이번 분석은 5년 신고에서 출발해 공식 현장점검, 시설 운영정보, 사업 완료와 효과평가까지 연결했습니다.</p>
<div class="flow"><span>2020–2024 신고 패턴</span><b>→</b><span>동별 시간·유형 비교</span><b>→</b><span>공식 지점·시설 확인</span><b>→</b><span>기존 개선과 후속 결과</span></div>
<p>신고 분석은 선택한 704,689건을 유지합니다. 주된 사례 비교는 정상 처리·운영성 분류 제외 574,662건에서 선정한 10개 지역·유형 조합입니다. 공식 보완자료는 별도 모집단으로 비교하며 신고에 합산하지 않았습니다.</p>''')
rows=''.join(f'<tr><td>{esc(d)}</td><td>{a}</td><td>{b}</td></tr>' for d,a,b in zip(districts,old,child))
inspection_rows=''.join('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in [r['district'],' / '.join(r['lawNameCandidates']) or '동 미확정',r['place'],r['shortTermItems'],r['longTermItems']])+'</tr>' for r in coverage['mois14'])
add('부산 전체 점검 → 근거가 있는 지점으로 좁혔습니다',f'''<p>16개 구·군의 2020–2025 보행사고 지정기록 301행을 검산했습니다. 2023년 행정안전부 부산 현장점검 14지점에는 단기 개선 122항목과 중장기 개선 19항목이 기록돼 있습니다. 이는 당시의 개선 항목 수이며 현재 미해결 건수가 아닙니다.</p>
<img src="busan_all16_coverage.svg" alt="16개 구군별 2025 보행사고 지정지점 기록 수"><p>다음 표는 2025 자료연도 지정기록입니다.</p><div class="tablewrap"><table><thead><tr><th>구·군</th><th>노인 지정지점</th><th>어린이 지정지점</th></tr></thead><tbody>{rows}</tbody></table></div>
<h3>실제 개선 항목이 기록된 부산 현장점검 14곳</h3><p>2023년 점검표의 개선 항목입니다. 지점명과 공식 법정동 코드 대응 범위만 표시하며, 현재 조치 완료 여부는 별도 확인 대상입니다.</p>
<div class="tablewrap"><table><thead><tr><th>구·군</th><th>대응 동명</th><th>점검 지점</th><th>단기 항목</th><th>중장기 항목</th></tr></thead><tbody>{inspection_rows}</tbody></table></div>
<p><a href="coverage_latest2025_law_dongs.csv">동별 지정자료</a> · <a href="coverage_mois_all14_inspection_sites.csv">공식 현장점검 14곳</a> · <a href="coverage_law_dong_receipt_names.csv">신고 지역명과의 대응 기록</a></p>''')
add('대연동: 반복 지정과 실제 현장 개선 항목을 확인했습니다','''<p>못골사거리는 2022–2025 자료연도에 같은 구·법정동 코드·지점명으로 반복 지정됐습니다. 2023년 공식 점검은 교통안전시설 관련 단기 개선 3항목을 기록했습니다. 인구 비중으로 피해자 나이를 추정한 결과가 아니라, 별도 보행노인 사고자료와 현장점검에서 확인한 결과입니다.</p>
<img src="daeyeon_specific_place_evidence.svg" alt="대연동 보행사고 지정지점과 2023 공식 점검 근거">
<p>대연동 교통 신고 736건을 이 지점의 사고로 배정하지 않았습니다. 지정지역별 사고 수는 기간과 영역이 겹칠 수 있어 서로 합산하지 않습니다. 못골시장과 못골사거리도 구분했습니다.</p>
<p><a href="https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&amp;nttId=105248">행정안전부 2023 현장점검</a></p>''')
add('못골시장: 개선사업과 효과평가가 이미 있었습니다','''<p>2024년 11월 구의회 발언은 공사 단계 중 턱 걸림·미끄러짐 문제와 의원이 받은 보고문서상 접수 8건을 제시했습니다. 1차 공사는 완료됐지만 전체 사업 준공 전입니다. 개별 사고 원장은 확보하지 않았으며 발언의 추정 30건 이상은 분석 수치로 채택하지 않았습니다.</p>
<p>전체 보행환경 개선사업은 2025년 2월 완료됐습니다. 2026년 효과평가 용역은 공식 계약 자료에 5월 20일 준공일과 1,898만원 전액 지급이 기록돼 있습니다. 효과평가가 없다고 주장하거나 새 평가를 중복 제안할 근거는 없습니다.</p>
<img src="motgol_followup_timeline.svg" alt="못골시장 개선과 의회 지적, 사업 준공, 효과평가 계약의 시간 흐름">
<p class="result"><strong>보완 방향:</strong> 기존 효과평가 결과에 교통 충돌과 보행 중 넘어짐을 구분해 연결하고, 실제 점검 항목별 조치와 이후 결과를 함께 공개하는 방식입니다. 현재 개선 효과와 잔여 위험은 평가 보고서 본문으로 확인할 단계입니다.</p>
<p><a href="https://www.bsnamgu.go.kr/open/2025/2en_1105/19.pdf">2025 사업 완료 공시, PDF 15쪽</a> · <a href="https://council.bsnamgu.go.kr/record/main?uid=11054">2024년 의회 발언</a> · <a href="http://contract.bsnamgu.go.kr/basis/situationView.do?ctrtAcctBookMngNo=202600210161">2026 효과평가 계약</a></p>''')
add('기장읍·연산동: AED는 등록 수와 이용시간이 다릅니다','''<p>주소 확인 등록 중 차량 등록을 제외한 AED 등록은 기장읍 92건, 연산동 70건입니다. 모든 요일·공휴일 24시간을 명시한 등록은 각각 42건, 41건입니다. 동일 건물에 여러 등록이 있을 수 있으므로 건물 수로 해석하지 않습니다.</p>
<img src="aed-operating-hours.svg" alt="차량등록을 제외한 AED 등록 중 모든 요일 24시간 명시 여부">
<p class="result"><strong>보완 방향:</strong> 반복 심정지 신고 지역의 서비스 화면에서 설치 개수보다 이용시간·고정 또는 이동 여부·공식 조회 경로를 함께 제공할 근거가 있습니다. 실내 출입 가능 여부와 작동 상태까지 확인한 뒤 운영시간 조정이나 실외 이전을 판단해야 합니다.</p>
<p>2020–2024 심정지 신고는 기장읍 360건, 연산동 511건입니다. 현재 등록시간과 과거 신고를 비교한 결과가 AED 미이용 환자 수나 신규 설치 필요 수를 뜻하지 않습니다. <a href="https://www.e-gen.or.kr/egen/search_aed.do">국립중앙의료원 E-GEN</a></p>''')
add('기장읍·온천동: 건물별 피난 조건을 추가 확인했습니다','''<p>부산소방 공식 포털의 기장읍 27단지·137개 등록 동 항목, 온천동 44단지·165개 등록 동 항목을 실제 조회했습니다. 온천동 목록에는 오피스텔 표기 1항목이 포함됩니다. 전층 스프링클러 표기는 각각 41항목과 94항목이며, 부분층 설치와 없음 표기를 구분했습니다.</p>
<img src="apartment-sprinkler-conditions.svg" alt="공식 포털 등록 동 항목별 스프링클러 조건">
<p class="result"><strong>보완 방향:</strong> 모든 건물에 동일한 피난 안내를 보여주기보다 공식 건물별 피난정보로 연결하는 방식입니다. 포털은 이미 운영 중이므로 새 시설 목록을 만드는 것보다 지역 분석 결과에서 기존 정보를 찾도록 연결하는 데 의미가 있습니다.</p>
<p>이는 동 내부의 별도 건축물 조건 조사입니다. 일반화재(주택)와 고층건물 화재는 신고 분류가 다르므로 주택화재 76·53건의 발생 건물 근거로 결합하지 않았습니다. 미설치 표기를 법 위반이나 미지원 가구 수로 해석하지 않습니다. <a href="https://119.busan.go.kr/safeapt/index">부산소방 아파트 화재안전</a></p>''')
tr=[]
for p in time['cases']:
 c=p['scopes']['C']; a,b=c['periods']
 tr.append(f"<tr><td>{esc(p['district']+' '+p['rawDong'])}</td><td>{esc(p['subtype'])}</td><td>{a['weekendRatio']:.2f}</td><td>{b['weekendRatio']:.2f}</td><td>{c['weekendHigherYears']}/5년</td></tr>")
add('시간 전략은 5년 합계만으로 정하지 않았습니다','''<p>초읍동 산악 신고의 주말 일평균 비율은 전기 2.29배, 후기 2.00배였습니다. 반면 기장읍 주택화재는 1.44배에서 0.52배로 방향이 바뀌었고, 다대동 수난은 2.50배에서 1.04배로 약해졌습니다. 따라서 모든 사례에 같은 주말 중심 대응을 제안하지 않습니다.</p>
<img src="period_weekend_comparison.svg" alt="10개 지역 유형 사례의 전후 기간 주말 대 평일 일평균 비교">
<p>토·일 신고 수와 월~금 신고 수를 각 달력 일수로 나눴습니다. 5년 자료로 선정한 사례의 민감도 비교이며 미래 예측 검증은 아닙니다.</p>
<div class="tablewrap"><table><thead><tr><th>지역</th><th>유형</th><th>2020–22 배율</th><th>2023–24 배율</th><th>주말 일평균이 높은 해</th></tr></thead><tbody>'''+''.join(tr)+'''</tbody></table></div>''')
add('이번 결과로 구체화한 차별점','''<p>정부는 이미 사고다발지 점검, 아파트 피난정보, AED 검색과 보행사업 효과평가를 수행합니다. 이번 프로젝트의 차별점은 이를 없던 서비스처럼 다시 만드는 데 있지 않습니다.</p>
<p class="lead">신고가 반복되는 지역과 시기를 찾고, 그 지역의 실제 이용 조건과 기존 개선 결과를 같은 흐름에서 보여주는 것입니다.</p>
<ul><li>교통: 당시 개선 항목 → 사업 범위 → 준공 → 기존 효과평가를 구분해 결과 연결.</li><li>심정지: AED 등록 수 → 요일별 이용시간 → 공식 조회로 연결.</li><li>화재: 지역 신고와 별개로 확인한 건물별 피난 조건 → 기존 공식 정보로 연결.</li><li>산악·수난: 시기별 반복성 변화까지 반영해 획일적인 시간 전략을 방지.</li></ul>
<p>현재 확정한 시설 증설·인력 증원안은 없습니다. 이는 결과를 비워 둔 것이 아니라, 이미 시행된 사업과 아직 확인되지 않은 이용 실태를 구분한 판단입니다. 정보 연결 보완 후보와 실제 운영 변경안은 근거 수준을 나눠 제시합니다.</p>''')
add('자료와 재현 방법','''<p>신고 2020–2024와 연말 주민 구성은 기존 검증 결과를 재사용했습니다. 이번에는 16개 구·군 보행사고 지정자료, 14곳 공식 점검, AED 시간표, 아파트 건물 조건, 못골시장 후속 사업 기록을 추가했습니다. 보완자료 확보일은 2026-09-16이며 현재 운영 자료를 과거 신고 당시 상태로 취급하지 않습니다.</p>
<p>선택한 신고는 부산 전체 신고의 대표 표본으로 검증되지 않았습니다. 주민 연령은 신고자 연령이 아니며, 위치 미확정 동명은 실제 행정동에 강제 배정하지 않았습니다. 이번 보행노인 피해자 연령 근거는 별도 공식 사고자료입니다.</p>
<p><a href="보고서.md">보고서와 추가 확인 항목</a> · <a href="time-robustness.csv">기간·처리조건별 비교</a> · <a href="coverage_all16_districts_2020_2025.csv">16개 구·군 전체 지정자료</a></p>''')
css='''*{box-sizing:border-box}body{margin:0;color:#193d49;background:#f2f6f5;font:17px/1.75 system-ui,"Malgun Gothic",sans-serif}header{background:#123e49;color:white;padding:40px max(5vw,24px)}h1{font-size:36px;line-height:1.35;max-width:1050px;margin:10px auto}header p{max-width:1050px;margin:auto;color:#cde8e6}nav{position:sticky;top:0;background:#fff;border-bottom:1px solid #d1e1df;padding:12px 5vw;z-index:3}nav a{margin-right:24px}main{max-width:1200px;padding:0 34px;margin:auto}section{padding:44px 0;border-bottom:1px solid #cbdcd9;scroll-margin-top:70px}h2{font-size:27px;line-height:1.45}p{max-width:1000px}a{color:#086f70;text-underline-offset:4px}img{display:block;width:100%;height:auto;background:white;margin:28px 0}.lead{font-size:22px;font-weight:600}.result{background:#e0eeea;border-left:4px solid #13776d;padding:20px}.flow{display:flex;gap:18px;align-items:center;flex-wrap:wrap;color:#086b65;font-weight:bold;padding:24px 0}table{border-collapse:collapse;width:100%;background:#fff;font-size:16px}td,th{text-align:left;padding:9px 14px;border-bottom:1px solid #dde6e4}th{background:#e2eeeb}.tablewrap{overflow:auto}footer{padding:35px;text-align:center}@media(max-width:700px){h1{font-size:27px}main{padding:0 18px}h2{font-size:23px}}'''
body=''.join(f'<section id="s{i}"><h2>{title}</h2>{text}</section>' for i,(title,text) in enumerate(sections))
page=f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 · 동별 근거 심화 결과</title><style>{css}</style><header><p>부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>반복된 신고에서<br>실제 지점과 기존 개선 결과까지</h1><p>신고 2020–2024 · 추가 공식자료 확인 2026-09-16</p></header><nav><a href="#s1">부산 전체</a><a href="#s2">대연동</a><a href="#s4">AED</a><a href="#s5">피난 조건</a><a href="#s6">시간 비교</a><a href="#s7">보완 결과</a></nav><main>{body}</main><footer>확인된 사실과 운영 보완 후보를 구분한 분석 결과</footer></html>'
(OUT/'index.html').write_text(page,encoding='utf-8')
import re
def markdown_table(match):
 rows=[]
 for row in re.findall(r'<tr>(.*?)</tr>',match.group(0),re.S):
  cells=re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',row,re.S)
  rows.append('| '+' | '.join(re.sub('<[^>]+>','',c) for c in cells)+' |')
 if rows:rows.insert(1,'| '+' | '.join('---' for _ in re.findall(r'<th[ >]',match.group(0)))+' |')
 return '\n\n'+'\n'.join(rows)+'\n\n'
md='# 부산 119 동별 보완 심화 결과\n\n'
for title,text in sections:
 clean=re.sub(r'<table>.*?</table>',markdown_table,text,flags=re.S)
 clean=re.sub(r'<img[^>]+>','',clean); clean=re.sub(r'</(?:p|li|tr)>','\n\n',clean); clean=re.sub(r'<a href="([^"]+)">(.*?)</a>',r'[\2](\1)',clean); clean=re.sub(r'<[^>]+>','',clean)
 md+='## '+title+'\n\n'+html.unescape(clean)+'\n\n'
md+='''## 내부 후속 확인 항목과 채택 판단

- 못골시장: 2026 효과평가 최종보고서·과업범위·구간도, 2024 접수 8건의 비식별 사고유형·조치·준공 이후 재발 자료. 계약 준공과 전액 지급까지 확인했으나 보고서 본문 미확보. 평가가 없다는 주장은 기각한다.
- 못골사거리: 2023 교통안전시설 단기 3항목의 정확한 위치·항목·완료일·완료 증빙. 시장 사업 완료를 사거리 항목 완료로 대체하지 않는다.
- AED: 등록별 실내 출입·실제 운영시간·점검일·고장·패드 및 배터리 만료. 등록시간 불명확은 이용 불가를 뜻하지 않는다.
- 아파트: 조사 기준일·건물 및 라인별 최신 조건. 주택화재와 고층건물 유형이 다르므로 기존 일반주택 신고의 발생건물 분석으로 채택하지 않았다.
- 건축 허가와 상권 전체 자료는 위 질문의 실제 답을 제공하지 않아 이번 결합에서 제외했다. 생활인구를 주민 인구나 환자 수의 대체 분모로 사용하지 않았다.
- 기관에 자료 요청을 발송하지 않았다. 공개자료 수집과 분석만 수행했다.

## 재현 순서

기존 검증 집계 후 아래 코드를 프로젝트 루트의 Python 환경에서 실행한다. 수집은 네트워크가 필요하며 공개 원문이 바뀌면 기존 해시와 비교한다.

1. `scripts/collect_dong_place_20260916.py`
2. `scripts/collect_dong_services_20260916.py aed` 및 `scripts/collect_dong_services_20260916.py apartments`
3. `scripts/collect_motgol_followup_20260916.py`
4. `analysis/00_공통/analyze_case_time_robustness_20260916.py`
5. `analysis/00_공통/analyze_motgol_followup_20260916.py`
6. `scripts/collect_dong_services_20260916.py figures`
7. `scripts/build_dong_deepening_report_20260916.py`
8. `scripts/connect_dong_deepening_20260916.py`
9. `scripts/check_dong_deepening_report_20260916.py` (로컬 서버 실행 후)

필요 환경: Python, pandas, matplotlib, PyMuPDF, openpyxl, curl 및 Windows 맑은 고딕. 화면 검증은 Playwright와 Chrome을 사용한다. 공개 웹에는 집계 결과만 넣고 개별 신고·정밀 위치·계약 상대방 개인정보는 넣지 않는다.
'''
(OUT/'보고서.md').write_text(md,encoding='utf-8')
(ROOT/'docs/40-분석결과/부산-119-동별보완-심화결과-20260916.md').write_text(md,encoding='utf-8')
for folder,stem in [('time','period_weekend_comparison'),('place','daeyeon_specific_place_evidence'),('followup','motgol_followup_timeline'),('services','aed-operating-hours'),('services','apartment-sprinkler-conditions')]:
 for ext in ['png','svg']:
  p=B/folder/f'{stem}.{ext}'
  if p.exists():shutil.copy2(p,OUT/p.name)
for p in (B/'place').glob('coverage_*.csv'):shutil.copy2(p,OUT/p.name)
shutil.copy2(B/'time/time-robustness.csv',OUT/'time-robustness.csv')
web=ROOT/'web/final/results/deepening';web.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
 if p.is_file():shutil.copy2(p,web/p.name)
manifest={'generated':'2026-09-16','inputs':[],'outputs':[]}
for p in [B/'place/coverage_all_busan.json',B/'time/time-robustness.json',B/'followup/followup-evidence.json',B/'services/apartment-summary.json',B/'services/aed-summary.json']:
 manifest['inputs'].append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for p in OUT.iterdir():
 if p.is_file() and p.name!='manifest.json':manifest['outputs'].append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.iterdir():
  if p.is_file():z.write(p,p.name)
 assert z.testzip() is None
print(OUT)
