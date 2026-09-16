"""Build the evidence-first, multi-region follow-up deliverable."""
from pathlib import Path
import json,csv,html,re,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'data/processed/후속입증-20260916';OUT=ROOT/'output/부산119-전지역후속검증-20260916';OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'));esc=lambda x:html.escape(str(x))
d=read(B/'analysis/all-region-followup.json');traffic=read(B/'traffic/traffic-followup.json');field=read(B/'traffic/bdi-field-study.json');services=read(B/'services/followup-services-evidence.json');outdoor=read(B/'outdoor/outdoor-evidence.json')
S=[]
def section(title,text):S.append((title,text))
def table(headers,rows):return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def figure(stem,caption):return f'<figure><img src="{stem}.svg" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'
def receipt(district,dong,subtype):return next(r for r in d['catalogue'] if r['scope']=='C' and r['district']==district and r['rawDong']==dong and r['subtype']==subtype)
section('왜 이 분석을 했는가','''<p class="lead">지역별로 반복되는 신고를 발견하는 것만으로는 예방안이 완성되지 않습니다. 그 지역의 실제 환경, 서비스를 이용할 수 있는 조건, 이미 시행한 조치까지 확인해야 합니다.</p>
<p>이번 조사에서는 부산시가 인정한 AED 설치정보 불일치, 현장조사의 보차 미분리 구간, 2026년 소방시설 불량 기록을 확인했습니다. 동시에 시설 정비·현지시정·폐장 후 안전관리·사업 효과평가가 이미 존재한다는 근거도 확인했습니다.</p>
<p class="result">프로젝트의 문제제기는 <strong>“어디에 신고가 많은가”에서 “그 지역에서 확인된 문제와 기존 대응을 어떻게 함께 판단할 것인가”</strong>로 이어집니다. 우리의 결과물은 신고·현장·운영·조치 자료의 시점과 범위를 맞춰 보여주는 분석과 서비스 시제품입니다.</p>
<p>행정에 이런 분석이나 서비스가 전혀 없다고 주장하지 않습니다. 기존 검색·지원·평가를 재사용하면서, 지역별 근거를 비교하고 이미 조치된 사항과 추가 확인이 필요한 사항을 구분하는 것이 이번 구현의 차별점입니다. <a href="문제제기와보완논리.md">문제제기·정부 기존 업무·보완 논리 상세</a></p>''')
section('부산 전체에서 다시 출발했습니다',f'''<p>2020–2024 신고 704,689건을 유지하고, 정상 처리·운영성 분류 제외 574,662건을 중심으로 비교했습니다. 관측된 194개 지역명과 예방 관련 5개 유형의 970개 조합을 세 처리조건으로 계산했습니다. 관측 0과 비교 불가도 남겼습니다.</p>
<p>이번 추가 자료는 공식 교통 점검 14곳, 보행환경 현장연구 4지역·20구간, 소방서 4곳의 최신 조사 132행, AED 운영 및 주택지원 자료, SGIS 2024 주택구성입니다. 서로 다른 자료의 건수를 하나의 분모로 합치지 않았습니다.</p>
<p><a class="primary" href="explorer.html">194개 지역 결과 직접 탐색</a> <a href="all_194_regions_5_domains_3_scopes.csv">전체 비교표 내려받기</a></p>'''+figure('district_type_composition','각 구·군의 전체 선택 신고 대비 구성비. 사고 위험률이나 정책 우선순위가 아닙니다.'))
sens=d['stabilityAcrossScopes']['timeSensitivity']
section('반복성은 유지돼도 시간 전략은 달라집니다',f'''<p>세 처리조건 모두에서 결측 제외 전후 5년 반복성과 증감 방향이 유지된 조합은 <strong>325개</strong>였습니다. 이 중 전후 기간의 주말·평일 비율을 유한하게 비교할 수 있는 322개 중 144개는 1배 기준의 방향이 달라졌습니다.</p>
<p>작은 건수의 영향을 확인하기 위해 매년 최소 5·10·20건 조건도 비교했습니다. 매년 20건 이상인 86개에서도 32개가 방향을 바꿨고, 19개는 0.9배 미만에서 1.1배 초과 또는 그 반대로 바뀌었습니다. 이 기준은 민감도 비교용이며 후보 선정 점수가 아닙니다.</p>'''+figure('time_strategy_sensitivity','전체 5년으로 고른 사례의 기술적 민감도입니다. 미래 예측 검증·통계적 유의성·서비스 부족 판정은 아닙니다.')+table(['매년 최소 건수','대상 조합','비율 비교 가능','1배 기준 방향 변화','0.9↔1.1 기준 변화'],[[r['minimumEachYear'],r['eligibleCombinations'],r['finiteRatioPairs'],r['ratioCrossesOne'],r['ratioCrosses09and11']] for r in sens]))
newcases=[]
for gu,dong,place,reason in [('부산진구','부전동','부전시장','시장 내·외부도로의 실제 보행조건 조사'),('수영구','광안동','광안역 주변','보차 미분리 구간과 주변 보행조건 조사'),('사하구','신평동','신평역 주변','도로 조건과 횡단 대기를 구분한 현장조사'),('연제구','거제동','거제시장 주변','시설 계획과 예산심사에 나타난 구간·근거 확인'),('중구','남포동5가','남포사거리','기존 횡단보도 사업·주정차 단속 운영 확인'),('동구','범일동','부산진시장 앞','공식 점검 개선 항목과 후속 확인 범위')]:
 r=receipt(gu,dong,'교통사고');newcases.append([esc(gu+' '+dong),esc(place),f"{r['count']:,}건",' / '.join(map(str,r['yearCounts'])),f"{r['retention']:.1%}",'증감 방향 민감' if r['directionReversal'] else '이 조건에서 증감 방향 유지',esc(reason)])
section('못골시장 밖으로 심층 대상을 넓혔습니다','''<p>다음 지역은 신고 건수 순위로 선정한 것이 아니라, 추가로 확보한 현장조사·공식 점검·운영 근거가 있어 검토 범위를 넓힌 사례입니다. 동 이름의 교통 신고는 배경 비교이며 해당 시장·교차로에서 발생한 사고 수가 아닙니다.</p>'''+table(['지역명','추가 확인 장소','교통 신고','2020→2024','잔존율','선택 영향','확장 이유'],newcases)+'''<p>범일동·거제동·남포동5가는 결측 제외 전후 증감 방향이 바뀝니다. 현장 근거가 있다는 이유로 신고 증가·감소 해석까지 안정적인 것으로 바꾸지 않았습니다.</p>''')
section('부전·대연·광안·신평: 실제 보행환경 조사를 대조했습니다','''<p>부산연구원 연구는 2024년 10월 26–27일 네 지역 20구간, 총 5,113.4m를 조사했습니다. 보차 분리 12구간, 미분리 8구간이 기록돼 있습니다. 부전시장 내부도로 4구간 중 2구간, 광안역 주변 내부도로 2구간 모두가 미분리로 집계됐습니다.</p>
<p>체험복 착용·미착용 조건의 평균 보행시간 비교도 공개돼 있습니다. 부전시장 내부도로의 공개 평균은 194.3초와 258.6초입니다. 실제 고령자 표본이 아니라 30대 여성 조사원의 체험복 실험이므로 고령자 평균 속도나 현재 신호시간 부족을 입증한 값으로 사용하지 않습니다.</p>'''+figure('field_study_experiment','2024 현장조사·체험복 실험. 속도표는 신평 외부도로의 횡단 대기 포함 1구간을 제외했습니다.')+figure('field_study_road_conditions','공개된 지역×내외부도로 8개 집계이며 개별 20구간의 원측정 자료가 아닙니다.')+'''<p class="result"><strong>보완 방향:</strong> 보행 안내와 현장 점검 결과를 시장 내부·접근도로·횡단 구간으로 구분해 제공할 근거가 있습니다. 특정 신호시간 변경이나 안전 경로 확정은 실제 대상 구간의 신호·횡단 자료와 현재 상태를 확인한 뒤 판단해야 합니다.</p>
<p><a href="https://data.bdi.re.kr/PDF/View.do?dir=report&amp;path=RPT_00000000001&amp;savename=20250715172207_54971">부산연구원 원문, PDF 66–71쪽</a></p>''')
section('14곳 모두 후속 자료를 추적했습니다',figure('traffic_followup_all14','2023 개선 항목과 이번에 확보한 후속 근거를 구분했습니다. 미확보를 미조치로 표시하지 않았습니다.')+table(['구·군 / 지점','당시 단기 / 중장기','추가 확인 결과'],[[esc(s['district']+' / '+s['place']),f"{s['shortTermItems']} / {s['longTermItems']}",esc(s['confirmedFollowup'])] for s in traffic['sites']])+'''<p>거제시장 주변 약 400m 생활가로는 계획입니다. 2024년 의회 심사에서는 거제천로 펜스 사업의 구간·경찰협의 근거가 논의됐고, 해당 3,740만원은 위원회 예산심사에서 전액 삭감됐습니다. 이를 2023 점검 17항목의 미이행이나 현재 펜스 부재로 해석하지 않습니다.</p>
<p>남포사거리에서는 2022년 횡단보도 시범사업과 2025년 주정차 CCTV 운영 자료를 확인했습니다. 단속시간은 09–21시, 점심 유예는 11:30–14시로 공지됐습니다. 단속 유예는 구조·구급 대응 공백을 뜻하지 않습니다.</p>
<p>못골시장 사업은 2025년 완료됐고 2026년 효과평가 계약 준공도 확인됐습니다. 기존 평가가 없다는 가설은 기각했습니다. 복지관 3곳은 공식 주소로 우암동·용호동·연산동의 지역 배경 후보를 추가했지만, 점검 구간이나 신고 지점은 확정하지 않았습니다.</p>
<p><a href="traffic-followup-all14.csv">14곳 전체 상태표</a> · <a href="search-attempts.json">교통 후속 검색 기록</a></p>''')
ins=services['inspection'];assert sum(x['any_defect_rows'] for x in ins['stations'])==19
section('2026 소방 조사: 불량 판정과 비고를 구분했습니다','''<p>기장·동래·금정·부산진소방서의 2026년 8월 조사표 132행을 추출했습니다. 판정 131행, 조사연기 1행입니다. 소방시설 또는 피난시설에 불량이 기재된 행은 19행이며, 이 중 기장 6행에는 현지시정이 함께 기재됐습니다. 나머지 13행의 일반 비고란은 공란입니다. 금정은 연기 1행을 뺀 25행, 부산진은 34행 전체의 비고가 비었습니다. 조치완료 전용 열이 없으므로 불량 13행만의 조치정보 누락이나 관리공백을 뜻하지 않습니다.</p>'''+figure('current-fire-inspection','조사표 행 기준입니다. 조사 대상·범위가 달라 소방서별 불량률이나 지역 위험 순위를 만들지 않았습니다.')+table(['소방서','조사표 행','판정 행','불량 기재','불량 중 현지시정 기재','불량 중 비고 공란','연기'],[[x['station'],x['listed_rows'],x['assessed_rows'],x['any_defect_rows'],x['any_defect_with_onsite_correction'],x['any_defect_without_correction_note'],x['deferred_rows']] for x in ins['stations']])+'''<p class="result"><strong>보완 방향:</strong> 공개표에 실제 있는 조사기간·조사범위·판정·비고를 구분해 제공합니다. 개별 지적사항·조치기한·완료일·재점검 결과는 이 공개표에서 확인되지 않습니다. 현재 미해결 시설 목록으로 공개하거나 과거 신고의 발생 건물에 배정하지 않았습니다.</p>
<p>동래 첨부 표지일은 조사기간·게시일과 불일치합니다. 동일 이름 또는 도로 건물번호를 공유하는 복수 행도 있어 132개 고유 시설로 표현하지 않았습니다. 소방서 조사범위는 구 경계와 같지 않습니다.</p>
<p>공식 원문: <a href="https://119.busan.go.kr/119total/1753023">기장</a> · <a href="https://119.busan.go.kr/119total/1753101">동래</a> · <a href="https://119.busan.go.kr/119total/1752701">금정</a> · <a href="https://119.busan.go.kr/119total/1753494">부산진</a></p>''')
section('AED: 실제 정보 불일치와 기존 지원을 함께 확인했습니다','''<p>부산시는 2025년 6월 AED 4,431대와 일부 행정시스템 설치정보 불일치 사례를 발표했습니다. 연제구의회 2024년 답변은 공개목록 미표시에 기관의 공개 거부, 구급차 구분, 좌표 오류 등이 관련된다고 설명했습니다. 목록에 보이지 않는 장비를 없는 장비로 판단할 수 없는 이유입니다.</p>
<p>연제구는 비의무기관 소모품 교환과 구매지원을 운영하고 있었고, 당시 예산 부족이 크지 않다는 답변도 확인했습니다. 기장군에는 행사·단체여행·심장질환자 가정 등을 대상으로 최장 14일의 기존 AED 대여 절차가 있습니다. 새 대여사업이나 예산 증액 필요성을 자동으로 제안하지 않습니다.</p>'''+figure('current-service-evidence','시스템 정보 불일치의 확인, 기존 지원 절차, 완료 실적이 아닌 계획을 구분했습니다.')+'''<p class="result"><strong>보완 방향:</strong> 공개 동의와 공식 운영정보를 존중하면서 고정·차량·대여 등록, 이용시간, 자료 확인일을 구분해 안내하는 것입니다. 공개하지 않은 위치를 추정해 채우지 않습니다. 실제 장비 점검·고장·이용 실적을 확보하기 전에는 환자 미이용이나 신규 설치 필요 수를 계산하지 않습니다.</p>
<p><a href="https://www.busan.go.kr/nbtnewsBU/1691436">부산시 AED 관리 발표</a> · <a href="https://clik.nanet.go.kr/minutes/viewer.do?DOCID=CLIKC2231052549767112&amp;collection=minutes">연제구의회 답변</a> · <a href="https://www.gijang.go.kr/index.gijang?menuCd=DOM_000000402007002004">기장군 대여 절차</a></p>''')
section('주택: 신고 분류와 실제 주택구성을 다시 맞췄습니다','''<p>아파트 시설정보를 일반주택 화재에 바로 연결하지 않고 ‘고층건물(3층이상,아파트)’ 분류를 추가 계산했습니다. 정상 처리 조건에서 기장읍 56건, 온천동 76건입니다. 기장읍은 제외 전 비교 집합에서 17→14건인데 분석 대상에서는 11→13건으로 증감 방향이 바뀝니다.</p>'''+figure('building_fire_selection','고층건물 분류는 아파트만의 신고가 아닙니다. 추가 조회한 아파트 포털 건물에 신고를 배정하지 않았습니다.')+'''<p>보유 SGIS 자료의 주택구성도 새로 분석했습니다. 기장읍 총주택 19,738 중 아파트는 14,146이며 나머지 주택 유형도 있습니다. 온천1·2·3동은 아파트 구성비가 서로 다릅니다. 같은 동명으로 접수된 신고를 이들 행정동에 배분하지 않았습니다.</p>'''+figure('housing_type_context','SGIS 2024 통계·2025-06-30 경계의 별도 주택 배경. 주택 이외 거처와 비공표 셀을 따로 관리했습니다.')+'''<p class="result"><strong>보완 방향:</strong> 아파트 주민에게는 기존 건물별 피난정보, 일반주택에는 기존 감지기·소화용품 지원조건을 구분해 연결합니다. 기장읍 2026년 1,000세대 멀티탭 지원은 계획이며, 최종 보급 완료나 미지원 세대 수로 표시하지 않았습니다.</p>
<p><a href="https://www.data.go.kr/data/15129688/fileData.do">SGIS 공식 제공자료</a> · <a href="busan_housing_context_2024.csv">부산 주택 전체 집계</a></p>''')
section('산악·수난: 기존 정비와 비개장 대응도 반영했습니다',table(['지역 배경','확인한 기존 대응','시점·근거 수준','보완 방향'],[[esc(x['case']),esc(x['finding']),esc(x['period']+' / '+x['status']),esc(x['candidate'])+f'<br><a href="{esc(x["sourceUrl"])}">공식 근거</a>'] for x in outdoor])+'''<p>초읍 찬물샘 정비에는 보행 우려뿐 아니라 흙길 이용 의견도 반영됐습니다. 금정산은 로프·표찰 정비 완료 발표가 있습니다. 해수욕장은 폐장 후 지속 대응 계획이 있어 비개장 신고를 미대응으로 계산하지 않았습니다. 사하구 야간관리 인력은 문서 버전별 수치가 달라 실제 배치 수로 확정하지 않았습니다.</p>''')
commerce=B/'commerce/commerce-context.json'
if commerce.exists():
 com=read(commerce)
 section('상권은 원인이 아닌 현장 배경으로 적용했습니다','''<p>2024년 10월 보행환경 조사와 가까운 2024년 9월 말 부산 143,964업소를 사용했습니다. 부전동·대연동·광안동·신평동 전체의 업종 구성을 비교하며, 실제 시장 구간이나 역 주변 500m 범위로 임의 배정하지 않았습니다.</p>'''+figure('commerce_four_area_context','소상공인시장진흥공단 2024년 9월 말 목록의 동 전체 배경. 시장·역 이용자나 보행량이 아닙니다.')+table(['구·동','등록업소','음식','소매','음식+소매 구성비'],[[esc(p['district']+' '+p['rawDong']),f"{p['shops']:,}",f"{p['foodShops']:,}",f"{p['retailShops']:,}",f"{p['foodRetailSharePct']:.1f}%"] for p in com['profiles']])+'''<p>부전동의 소매 비중은 31.4%, 대연동·광안동의 음식 비중은 36.9%·37.9%입니다. 네 지역 모두 같은 해 네 분기에서 음식·소매 합계가 과반을 유지했습니다. 분기별 등록업소 총수 변화를 실제 신규 개업이나 사고 노출 증가로 해석하지 않았습니다.</p><p>업소 수는 보행자·방문객 수나 사고 노출량이 아닙니다. 현장 안내와 주변 상업공간의 배경을 설명하는 데 사용하고, 상권 때문에 사고가 발생했다는 인과관계로 해석하지 않았습니다.</p><p><a href="https://www.data.go.kr/data/15083033/fileData.do">공식 상권자료</a> · <a href="four-law-dong-categories.csv">4개 동 업종 전체</a> · <a href="all16-district-categories.csv">16구·군 업종 비교</a> · <a href="quarter-sensitivity.csv">분기별 비교</a></p>''')
section('생활인구: 같은 동명 안에서도 활동시간이 다릅니다','''<p>2024년 205개 행정동의 12개월×24시간 자료 59,040행을 분석했습니다. 주거·직장·방문 값을 각각 비교했고, 다른 시간이나 범주의 인구를 합쳐 실제 이용자 수로 만들지 않았습니다.</p><p>부전1동의 방문 값은 00시 5,326.3명, 12시 17,718.2명으로 3.33배입니다. 부전2동은 각각 16,318.9명과 21,994.5명으로 1.35배입니다. 두 동 모두 12개월 각각 정오 값이 자정 값보다 높지만, 12개 기준월 평균곡선의 정점은 각각 14시와 19시로 다릅니다.</p>'''+figure('living_hour_context','통신 기지국 기반 월별 일평균의 12개 기준월 동일가중 평균. 연간 실인원이나 주민등록인구가 아닙니다.')+'''<p class="result">주민 규모만으로 안내 시간과 이용 환경을 정하기 어렵다는 배경을 확인했습니다. 같은 ‘부전동’ 신고명에도 서로 다른 활동 배경이 존재하므로 단일 시간전략을 곧바로 적용하지 않았습니다. 이 생활인구를 신고율 분모·환자 수·시장 이용자나 등산객 수로 해석하지 않습니다.</p><p><a href="https://www.data.go.kr/data/15142761/fileData.do">공식 시간 생활인구 정의</a> · <a href="all205-noon-midnight-comparison.csv">205개 동 시간 비교</a> · <a href="보조자료선택판단.md">전체 보조자료의 채택·불채택 이유</a></p>''')
section('예방·지원 보완 결과와 적용 범위',table(['보완 대상','확인된 근거','결과에 반영한 내용','운영 변경의 판단 범위'],[
 ['보행 지역','공식 점검·보차분리 현장조사·기존 사업','시장 내부·접근도로·횡단 구간과 사업 시점을 분리해 표시','신호·시설 변경은 동일 구간의 현재 상태·설계·경찰 협의 필요'],
 ['소방 점검','불량 19행·현지시정 6행·비고 공란 13행','조사 판정과 일반 비고를 구분한 결과표','비고 공란을 관리공백이나 미완료로 판단하지 않음'],
 ['AED 안내','행정정보 불일치·공개 제한·시간표·기존 대여','등록 유형·이용시간·기준일·공식 이용 절차를 구분','실제 접근·작동·사용 실적 없이 신규 설치 수 산정 안 함'],
 ['주택 안내','주택 유형 차이·기존 시설정보·지원 계획','아파트 피난정보와 일반주택 지원조건을 구분','미지원 가구 수·설치 효과 미확정'],
 ['산악·수난','반복 시기·기존 정비·통제·폐장 후 관리','출발 시 확인할 공식 운영·통제 정보와 정비 이력을 연결','확인되지 않은 인력 증원·전면 시설 설치 제안 안 함']])+'''<p class="lead">완성한 결과는 전 지역 신고 비교, 현장·운영 근거의 대조, 그리고 이를 이용자가 확인할 수 있는 결과 서비스입니다.</p><p>이 웹 시제품을 사용해 실제 예방효과가 생겼다는 평가는 아직 수행하지 않았습니다. 이번에 입증한 현장 사실과 정보 조건을 근거로 결과 구조를 만들었으며, 효과와 현재 미충족 수요를 상상으로 채우지 않았습니다.</p>''')
section('검증·출처·재현','''<p>기존 원본과 전처리본은 유지했습니다. 5년 전처리본 해시, 기존 제외 전후 집계, 새 지역×유형×시간 합계, 공식 문서의 숫자·시점·분류를 독립적으로 대조했습니다. 132개 소방 조사행과 131개 판정행, 시설명 중복, 주택 비공표값, 체험복 실험의 제외 구간도 구분했습니다.</p><p>자료 수집 범위와 미확보 항목은 결과표 및 검색 기록에 남겼습니다. 원문을 확인하지 못한 결론은 확정값으로 표시하지 않았습니다. 기관에 자료 요청을 발송하거나 비공개 기록에 접근하지 않았습니다.</p>
<p><a href="보고서.md">전체 보고서</a> · <a href="실행방법.txt">실행 방법</a> · <a href="source-register.json">수집 출처 목록</a> · <a href="pending-evidence.csv">후속 확인 대상과 필요한 기록</a></p>''')
css='''*{box-sizing:border-box}body{margin:0;color:#173b45;background:#f3f7f6;font:17px/1.8 system-ui,"Malgun Gothic",sans-serif}header{background:#123e49;color:white;padding:34px max(5vw,24px)}header>div{max-width:1160px;margin:auto}h1{font-size:37px;line-height:1.35;margin:14px 0}header p{color:#c9e5df}nav{position:sticky;top:0;z-index:4;padding:12px 5vw;background:white;border-bottom:1px solid #d5e5df}nav a{margin-right:24px}main{max-width:1240px;margin:auto;padding:0 34px}section{padding:38px 0;border-bottom:1px solid #c8dcd5;scroll-margin-top:65px}h2{font-size:28px;line-height:1.45}.lead{font-size:22px;font-weight:650}.result{border-left:4px solid #177f6b;padding:16px 22px;background:#e0eee8}a{color:#087467;text-underline-offset:4px}.primary{display:inline-block;background:#176f60;color:white;padding:10px 18px;border-radius:5px;margin-right:15px}figure{margin:28px 0}img{width:100%;height:auto;background:white}figcaption{font-size:14px;color:#526f68;margin-top:8px}table{width:100%;border-collapse:collapse;background:white;font-size:15px}th,td{padding:12px;border-bottom:1px solid #dbe6e1;text-align:left;vertical-align:top}th{background:#e1ede7}.tablewrap{overflow:auto}footer{text-align:center;padding:30px}@media(max-width:800px){main{padding:0 18px}h1{font-size:27px}h2{font-size:23px}nav{position:static}}'''
body=''.join(f'<section id="s{i}"><h2>{esc(t)}</h2>{b}</section>' for i,(t,b) in enumerate(S))
page=f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 · 전 지역 후속검증 결과</title><style>{css}</style><header><div><p>부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>지역의 반복 신고에서<br>현장 문제와 기존 조치까지</h1><p>신고 2020–2024 · 현장·운영 자료는 각 기준일 표시 · 추가 확인 2026-09-16</p></div></header><nav><a href="#s0">문제와 배경</a><a href="#s3">확장 지역</a><a href="#s6">현재 점검</a><a href="explorer.html">194개 지역 탐색</a></nav><main>{body}</main><footer>원문·집계·비교·해석 범위를 연결한 후속 분석 결과</footer></html>'
(OUT/'index.html').write_text(page,encoding='utf-8')
def mdtable(m):
 rr=[]
 for row in re.findall(r'<tr>(.*?)</tr>',m.group(0),re.S):
  cells=re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',row,re.S);rr.append('| '+' | '.join(re.sub('<[^>]+>',' ',c) for c in cells)+' |')
 if rr:rr.insert(1,'| '+' | '.join('---' for _ in re.findall(r'<th[ >]',m.group(0)))+' |')
 return '\n\n'+'\n'.join(rr)+'\n\n'
md='# 부산 119 전 지역 후속검증 결과\n\n'
for title,b in S:
 b=re.sub(r'<table>.*?</table>',mdtable,b,flags=re.S);b=re.sub(r'<img[^>]+>','',b);b=re.sub(r'</(?:p|li|figure|figcaption)>','\n\n',b);b=re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',r'[\2](\1)',b);b=re.sub('<[^>]+>','',b)
 md+='## '+title+'\n\n'+html.unescape(b)+'\n\n'
(OUT/'보고서.md').write_text(md,encoding='utf-8')
(ROOT/'docs/40-분석결과/부산-119-전지역후속검증-20260916.md').write_text(md,encoding='utf-8')
for folder in ['analysis','traffic','services','housing','commerce','living']:
 for ext in ['png','svg']:
  for p in (B/folder).glob('*.'+ext):
   if not any(x in p.name for x in ['page','capture']):shutil.copy2(p,OUT/p.name)
for folder,patterns in [('analysis',['all_194_regions_5_domains_3_scopes.csv','time_threshold_sensitivity.csv','building_type_comparison.csv']),('traffic',['traffic-followup-all14.csv','search-attempts.json','bdi-field-study-area-summary.csv','bdi-field-study-roadtype-summary.csv','facility-address-candidates.csv']),('services',['inspection-public-summary.csv','inspection-public-matched-dongs.csv','operating-evidence.csv']),('housing',['busan_housing_context_2024.csv','housing_sum_audit.csv','selected_housing_type_context.csv'])]:
 for name in patterns:shutil.copy2(B/folder/name,OUT/name)
for p in (B/'commerce').glob('*.csv'):shutil.copy2(p,OUT/p.name)
for p in (B/'living').glob('*.csv'):shutil.copy2(p,OUT/p.name)
for name in ['inspection-meaning-erratum.json','13행-의미재검토.md']:
 shutil.copy2(ROOT/'data/processed/최종논리검증-20260916/inspection'/name,OUT/name)
shutil.copy2(ROOT/'docs/40-분석결과/부산-119-보조자료선택판단-20260916.md',OUT/'보조자료선택판단.md')
shutil.copy2(ROOT/'docs/40-분석결과/부산-119-문제제기와보완논리-20260916.md',OUT/'문제제기와보완논리.md')
pending=[]
for s in traffic['sites']:pending.append({'category':'교통','place':s['district']+' '+s['place'],'confirmed':s['confirmedFollowup'],'needed':s['remainingEvidence'],'status':'공개 원문에서 항목별 현 상태 확정 못함','requestSent':False})
pending.extend([{'category':'AED','place':'부산·연제·기장','confirmed':'정보불일치/등록시간/기존지원','needed':'공개 동의된 등록 ID별 점검일·실내 출입·고장 조치·운영시간 갱신·실제 이용 집계','status':'행정대장·실태 자료 필요','requestSent':False},{'category':'소방 점검','place':'불량 기재 19조사행','confirmed':'6행 현지시정,13행 비고 공란','needed':'동일 조사행의 지적 항목·조치기한·이행·재점검 비식별 기록','status':'비고 공란은 전용 조치항목 결측이 아님; 현재 미조치 시설 수 미확정','requestSent':False},{'category':'주택 지원','place':'기장읍·동래 사업','confirmed':'2026지원계획·협업','needed':'대상·신청·완료·중복수혜·미지원 사유의 동별 비식별 집계','status':'최종 보급·잔여 실적 미확보','requestSent':False},{'category':'산악·수난','place':'초읍·금성·다대·우동 배경','confirmed':'정비·개장 및 폐장후 운영계획','needed':'2026현재 구간별 통제와 실근무·점검·구조 일지 및 실제 사건구간','status':'과거 계획을 현재 근무실적으로 변환 안 함','requestSent':False}])
with (OUT/'pending-evidence.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(pending[0]));w.writeheader();w.writerows(pending)
register={}
for folder,name in [('traffic','source-manifest.json'),('services','source-manifest.json'),('outdoor','source-manifest.json'),('housing','manifest.json'),('commerce','source-manifest.json')]:
 p=B/folder/name
 if p.exists():register[folder]=read(p)
register['services']={name:read(B/'services'/name) for name in ['attachment-manifest.json','snapshot-hashes.json','followup-services-evidence.json'] if (B/'services'/name).exists()}
register['living']={name:read(B/'living'/name) for name in ['official-hour-metadata.json','official-age-metadata.json','validation.json','living-context.json']}
(OUT/'source-register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'실행방법.txt').write_text('''PC 결과 열기: index.html. 지역 탐색: explorer.html. 인터넷 없이도 표·그래프·검색 가능.
공식 출처 링크에는 인터넷이 필요합니다.

프로젝트 루트 .venv-check/Scripts/python.exe 로 실행:
analysis/00_공통/analyze_busan_followup_20260916.py
analysis/00_공통/analyze_housing_context_20260916.py
scripts/collect_followup_traffic_20260916.py
scripts/collect_followup_services_20260916.py
scripts/collect_followup_services_20260916.py analyze
scripts/collect_followup_services_20260916.py report
scripts/collect_followup_outdoor_20260916.py
analysis/00_공통/analyze_commerce_context_20260916.py
analysis/00_공통/analyze_living_context_20260916.py
scripts/plot_busan_followup_20260916.py
scripts/plot_housing_context_20260916.py
scripts/plot_followup_traffic_20260916.py
scripts/plot_followup_services_20260916.py
scripts/build_followup_explorer_20260916.py
scripts/build_followup_report_20260916.py

원문은 프로젝트 data/raw 및 data/processed에 보존합니다. 수집은 원문 변경·네트워크에 영향을 받습니다.
Python pandas, matplotlib, openpyxl, pyshp, PyMuPDF, HWP 추출에 사용하는 olefile/pyhwp 환경과 curl을 사용합니다.
웹을 서버로 열려면 python web/final/serve.py --no-browser 실행 후
http://127.0.0.1:8765/results/followup/ 접속.
''',encoding='utf-8')
web=ROOT/'web/final/results/followup';web.mkdir(parents=True,exist_ok=True)
for p in OUT.iterdir():
 if p.is_file():shutil.copy2(p,web/p.name)
print('Report sections',len(S))
