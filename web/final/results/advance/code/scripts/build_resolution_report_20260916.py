"""An evidence-led shortlist and updated result report. No raw incident export."""
from pathlib import Path
import json,csv,html,re,shutil,hashlib
R=Path(__file__).resolve().parents[1];B=R/'data/processed/고도화검증-20260916';O=R/'output/부산119-쟁점해결-20260916';O.mkdir(parents=True,exist_ok=True)
load=lambda p:json.loads(p.read_text(encoding='utf-8'));esc=lambda s:html.escape(str(s))
sel=load(B/'selection/selection-deepening.json');resp=load(B/'response/resolution-evidence.json');traf=load(B/'traffic/traffic-resolution.json');edu=load(B/'education/service-conditions.json');sources=load(B/'traffic/source-manifest.json')
old=load(R/'data/processed/후속입증-20260916/analysis/all-region-followup.json')
def metric(gu,dong,kind):return next(x for x in sel['scopeCComparisons'] if x['CLMTY_SGG_NM']==gu and x['CLMTY_EMD_NM']==dong and x['EMRG_RSCU_CLSF_NM']==kind)
cases=[]
for gu,dong,kind,level,reason,action in [
 ('연제구','연산동','심정지','우선 심층 사례','5년 반복과 같은 이동전화의 주말·평일 방향이 유지되고, AED·실습대여의 공식 이용조건이 확인됨','등록 AED 조회, 실제 장비 대여, 교육용 기자재, 수료증 과정을 목적별로 분리해 안내'),
 ('부산진구','부전동','교통사고','우선 심층 사례','5년 반복과 같은 이동전화의 주말·평일 방향이 유지되고, 과거 보행조사 이후 맞이길 사업 기록이 확인됨','2024 조사와 2026 사업을 병렬 표시해 과거 문제를 현재 미개선으로 소개하지 않음'),
 ('수영구','광안동','교통사고','비교 사례','C 조건의 반복은 확인되나 모든 처리조건의 증감 방향이 안정적이지 않음. 포장사업 검사·지급은 별도로 확인됨','수영로 포장사업과 내부도로 보차분리 문제를 구분; 증가·감소 근거로 사업 우선순위를 정하지 않음')]:
 m=metric(gu,dong,kind);r=next(x for x in old['catalogue'] if x['scope']=='C' and x['district']==gu and x['rawDong']==dong and x['subtype']==kind)
 cases.append({'district':gu,'rawDong':dong,'subtype':kind,'status':level,'reason':reason,'action':action,'count':r['count'],'yearCounts':r['yearCounts'],'selection':m,'actualDongConfirmed':False,'effectsMeasured':False})
data={'asOf':'2026-09-16','period':'2020–2024','scope':'C 정상 처리·운영성 제외','cases':cases,'selection':sel['scopeCComparisons'],'selectionSummary':sel['summary'],'traffic':traf,'response':resp,'education':edu,'trafficSources':sources}
(O/'resolution-data.js').write_text('window.RESOLUTION='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
(O/'case-selection.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
S=[]
def sec(title,body):S.append((title,body))
def table(head,rows):return '<div class="tablewrap"><table><thead><tr>'+''.join('<th>'+esc(v)+'</th>' for v in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def fig(stem,caption):return f'<figure><img src="{stem}.svg" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'
def tlinks(f):
 labels={'bujeon-ceremony':'제막식 기록','bujeon-finance':'교부금 내역','bujeon-field-story':'시보 시민리포트','gwangan-contract-detail':'계약·지급 내역','gwangan-procurement-full':'입찰 공고'}
 return ' · '.join(f'<a href="{esc(s["url"])}">{esc(labels.get(s["id"],"공식 원문"))}</a>' for s in sources if s['id'] in f['sourceIds'])
sec('문제제기에서 해결 범위까지','''<p class="lead">같은 신고 증가라도 전화경로의 구성 변화인지, 결측 제외의 영향인지에 따라 판단이 달라집니다. 과거 현장에서 문제를 찾았더라도 이후 정비와 기존 서비스까지 확인해야 지금 필요한 보완을 정할 수 있습니다.</p><p>이번 단계는 부산 전체 비교를 다시 확대하는 대신, 선택 영향을 분해하고 실제 조치·이용조건을 추적해 <strong>연산동 심정지·부전동 교통을 우선 심층 사례, 광안동 교통을 비교 사례</strong>로 좁혔습니다. ‘부산에서 가장 위험한 3곳’이라는 선정은 아닙니다.</p><p>완료한 보완은 결과의 오해를 막는 판정과 공식 이용경로 연결입니다. 실제 시설의 보수나 기관 대장 수정까지 우리가 시행한 것은 아닙니다.</p>''')
sec('부산 전체에서 세 사례로 좁힌 근거','''<p>194개 신고 지역명×5유형의 970개 조합을 비교하고, 세 처리조건에서 제외 전후 5년 반복·증감 방향이 유지된 325개를 시간조건까지 재검토했습니다. 현장·운영자료로 독립적으로 확인되는 근거와 실제로 구현할 보완 내용이 있는 사례를 골랐습니다.</p><p>325개는 시간 전략이나 실제 동 위치까지 검증됐다는 뜻이 아닙니다. 광안동은 모든 처리조건의 안정성을 충족한 사례가 아니라, 기존 사업을 대조할 수 있는 별도 비교 사례입니다.</p>'''+table(['지역·유형','5년 선택 신고','판정','선정 근거','이번 보완'],[[esc(c['rawDong']+' · '+c['subtype']),f"{c['count']:,}건",esc(c['status']),esc(c['reason']),esc(c['action'])] for c in cases])+'''<p>거제동·범일동은 증감 방향이 뒤집히는 단계를 설명하는 진단 사례로 남겼습니다. 13개 소방 불량 조사행은 현재 조치가 확인되지 않아 ‘현재 미조치 시설’ 우선목록에서 제외했습니다. 이는 문제가 해결됐다는 판정이 아닙니다.</p>''')
sec('선택 영향: 전화경로와 이동전화 내부 제외를 분리했습니다','''<p>기존 기초 8개 조건의 비교 집합과 17개 충족 집합을 같은 이동전화 안에서 비교했습니다. 현재 분석 입력을 바꾸거나 제외 신고에 가중치를 주지 않았습니다.</p><p><strong>거제동 교통</strong>의 2024−2020 변화는 전체 경로 +14건 → 이동전화 −3건 → 17개 충족 이동전화 −6건입니다. <strong>범일동 교통</strong>은 −9건 → −7건 → +1건으로, 반전되는 단계가 다릅니다. 이는 건수의 산술 분해이며 결측 발생 원인이나 정책 효과의 인과 분석은 아닙니다.</p>'''+fig('channel_decomposition','서로 다른 경로의 제외와 같은 이동전화 내부 제외를 분리한 비교.')+table(['사례','제외 전 전체','제외 전 이동전화','17개 충족 이동전화','이동전화 잔존율'],[[esc(c['rawDong']+' '+c['subtype']),f"{c['selection']['beforeAll']:,}",f"{c['selection']['beforeMobile']:,}",f"{c['selection']['afterMobile']:,}",f"{c['selection']['mobileRetention']:.1%}"] for c in cases]))
sec('반복성이 유지돼도 시간 조건은 별도 검증했습니다','''<p>반복 유지 325개 중 같은 이동전화의 결측 제외 전후 주말/평일 하루 평균 비율이 1배를 넘나드는 조합은 33개였습니다. 0.9배 미만↔1.1배 초과로 바뀐 것은 2개이며, 매년 잔존 5건 이상 조건에서는 0개였습니다. 작은 건수와 1배 근처의 변동을 큰 변화로 확대하지 않았습니다.</p><p>연산동 심정지는 1.079→1.171배, 부전동 교통은 1.094→1.072배로 방향이 유지됩니다. 이 사실만으로 주말 인력 증원이나 주말 예방 효과를 주장하지 않습니다. 시간자료는 접수 시각입니다.</p>'''+fig('same_mobile_weekend','2020–2024 동일 기간·동일 이동전화의 선택 전후. 이전 보고서의 2020–22 대 2023–24 비교와 다른 질문입니다.')+table(['매년 잔존 최소','비교 조합','1배 경계 반전','0.9↔1.1 반전'],[[x['minimumMobileAfterEachYear'],x['combinations'],x['weekendDirectionReversed'],x['weekendBeyond09_11']] for x in sel['summary']]))
sec('연산동: AED가 있다는 정보에서 이용 목적까지','''<p>연산동 심정지 신고 511건은 지역 배경입니다. 주민의 연령을 환자의 연령으로 추정하거나 신고를 특정 장비 주변 사건에 배정하지 않았습니다.</p><p>2026년 3월 보건복지부 지침은 배터리·패치 유효기간 초과, 위치좌표 미설정 등의 외부표출 제한과 보건소·설치기관의 수정 절차를 설명합니다. 따라서 공개 목록은 전체 장비의 무작위 표본이 아니며, ‘지도에 없음=설치되지 않음’이나 ‘신규 관리절차 필요’라는 판단은 성립하지 않습니다.</p><p>연산동에 소재한 동래소방서의 실습 기자재 대여는 7일이며 <strong>교육용 AED</strong>가 포함됩니다. 기장군의 실제 AED 대여와 다른 서비스입니다. 기본 응급처치교육과 수료증 과정도 분리했습니다.</p>'''+fig('service_conditions_comparison','새로운 대여사업을 제안하는 대신 기존 과정·장비의 목적과 신청조건을 구분했습니다.')+'''<p class="result">구현한 보완: 심정지 결과에서 기본 교육·수료증·실습 대여·기존 AED 안내의 공식 경로를 목적별로 제공합니다. 공개 목록의 선택성을 표시하며 실제 작동상태나 예약 재고를 만들지 않습니다.</p><p><a href="https://www.daedeok.go.kr/board/binary/CHC_000005/2111958.hwpx">보건복지부 제8판 지침(공식 구청 배포본)</a> · <a href="https://119edu.busan.go.kr/main/4?action=view&amp;no=14491">동래소방서 실습 대여</a> · <a href="https://119edu.busan.go.kr/main/25">응급처치교육 조건</a></p>''')
sec('부전·광안: 과거 문제와 이후 정비를 나눴습니다',table(['장소','새로 확인한 단계','현재 판단','출처'],[[esc(f['place']),esc(f['finding']),esc(f['limit']),tlinks(f)] for f in traf['facts'] if f['id'] in traf['primaryCases']])+'''<p>부전역 앞 맞이길의 제막식 기록은 2026년 변화가 있음을 보여줍니다. 광안역 수영로는 2025년 11월 검사·준공금 지급까지 확인했습니다. 다만 이 사업들이 BDI의 개별 조사구간이나 보차 미분리 문제와 정확히 일치한다는 증거는 확보하지 못했습니다.</p><p class="result">구현한 보완: 과거 조사·현재 사업·동일 구간 확인 여부를 함께 표시합니다. ‘여전히 미개선’과 ‘전부 해결’이라는 양쪽 단정을 모두 제거했습니다. 동일 구간의 최신 도면·현장 상태와 기존 평가를 확보한 뒤 시설 변경을 판단하는 것이 다음 운영 단계입니다.</p><p>신평역 공원은 실시설계 입찰 단계만 확인돼 준공으로 표시하지 않습니다. 광안역 주민제안은 객관적 수요·사업 채택 근거로 사용하지 않았습니다.</p>''')
sec('조치 미기재 13행을 다시 추적한 결과','''<p>기장·금정·부산진의 공식 게시판에서 시정·재점검·조치결과·행정처분을 추가 검색했습니다. 이번 검색에서 기존 19개 불량 조사행과 일치하는 새로운 후속 완료 기록은 확보하지 못했습니다. 별도 데이터센터의 향후 점검 공고는 대상·시점이 달라 제외했습니다.</p><p><strong>기장 6행의 현지시정은 유지하고, 나머지 13행의 현재 조치 상태는 미확정으로 유지합니다.</strong> 검색은 게시본문 중심이며 비공개 대장이나 모든 첨부·개별시설 전수조사를 대신하지 않습니다.</p><p class="result">보완한 결과 구조: 불량 발견·현지시정 기재·후속 공개기록·현재 확인 상태를 다른 필드로 관리합니다. 조치 기록 부재를 미조치 시설 수나 위험 순위로 계산하는 오류를 막았습니다.</p>''')
sec('기존 교육도 접수 표기만으로 안내하지 않습니다','''<p>확보한 사하소방서 공고 17236에는 ‘접수중’, 운영기간 종료 2026-07-31, 신청기간 종료 2026-12-31이 함께 기재돼 있습니다. 정확히 10명인 경우에는 ‘10명 이하 폐강’과 ‘10명 이상 운영’이라는 문장이 상충합니다.</p><p>이는 확보한 게시내용의 조건 불일치이며 실제 교육 취소·수강 거부를 입증하지 않습니다. 직접 HTTP 요청은 차단돼 웹 열람 추출본을 보존했으며, 최신 실운영 확인을 했다고 표현하지 않습니다.</p><p class="result">시제품에서는 ‘현재 신청 가능’ 버튼 대신 공고 조건과 공식 확인 경로를 표시합니다. 원 기관 페이지를 수정한 것은 아닙니다. 교육이 존재하지 않는다는 주장도 하지 않습니다.</p>'''+table(['확인한 서비스','대상·목적','기간·시간','이용조건'],[[f'<a href="{esc(x["url"])}">{esc(x["name"])}</a>',esc(x['target']),esc(x['duration']),esc(x['condition'])] for x in edu['records']])+'''<p><a href="https://119edu.busan.go.kr/main/4?action=view&amp;no=17236">사하소방서 공고 원문</a></p>''')
sec('보완한 공백과 기대효과의 범위',table(['문제','완료한 결과·기능','기대할 수 있는 변화','아직 검증하지 않은 효과'],[
 ['선택 영향이 다른 증가·감소를 같은 결론으로 설명','경로 구성과 이동전화 내부 제외를 분해해 표시','근거가 약한 시간·증감 전략을 구별','정책 판단 오류 감소율'],
 ['과거 조사 뒤의 정비가 누락된 설명','부전·광안 사업의 확인 단계와 출처 연결','완료 사업을 중복 제안하거나 전부 해결로 오인하는 설명 감소','실제 중복예산 절감·사고 감소'],
 ['교육·실제 장비·수료증 조건 혼동 가능','목적별 이용조건과 공식 신청·조회 경로 연결','필요한 과정과 장비를 정확히 찾을 가능성','사용자 탐색시간·신청 성공률·생존율'],
 ['점검 결과와 조치 상태의 혼동','불량 발견과 시정·미확정 상태를 분리','조치 미기재를 현재 미조치로 오인하는 표시 방지','시설 시정 완료율·화재 피해 감소']])+'''<p>사용자 효과 평가는 동일한 정보찾기 과제를 기존 공식 경로와 시제품에서 수행하도록 순서를 교차 배정하고, 정답률·탐색시간·잘못된 현재상태 판단을 비교하는 방식으로 설계했습니다. 아직 참여자를 대상으로 실행하지 않았으므로 개선율을 제시하지 않습니다. 사고 감소는 별도의 장기·현장 평가가 필요합니다.</p><p>이번 결과의 공백 보완은 <strong>우리 분석과 결과 전달에서 빠졌던 선택 영향·시행 단계·이용조건을 연결한 것</strong>입니다. 기관 내부에 해당 업무가 없었다거나 주민의 모든 미충족 수요를 해결했다는 뜻은 아닙니다.</p>''')
sec('남은 판단과 다음 자료',table(['대상','필요한 구체적 근거','그 자료가 결정할 내용'],[
 ['부전·광안 보행 환경','BDI 조사구간 좌표·사업 준공도면·현재 보차분리/횡단 상태','이미 바뀐 구간과 추가 시설 검토 구간의 분리'],
 ['소방 불량 조사행','동일 조사행의 조치기한·이행·재점검 비식별 결과','현재 미조치인지 여부'],
 ['AED','공개 동의된 등록 ID별 최신 점검·운영시간·수정 이력','정보 불일치가 실제로 정정됐는지와 현재 이용조건'],
 ['못골·거제','못골 효과평가 원문·거제 최종 의결 및 집행','기존 평가 결과 반영·위원회 단계 이후 판단'],
 ['교육','운영기관이 확인한 최신 기간·인원 조건','공고의 상충을 해소한 실제 신청 안내']])+'''<p>기관에 자료 요청이나 예약을 보내지는 않았습니다. 웹 결과와 코드·집계·출처는 제공하며, 위 자료를 확보하지 않은 상태의 운영 효과는 채워 넣지 않았습니다.</p><p><a href="source-register.json">출처와 입력 기록</a> · <a href="service-conditions.csv">서비스 조건표</a> · <a href="annual_direction_channel_decomposition.csv">증감 단계 분해</a> · <a href="same_mobile_comparison.csv">동일 이동전화 비교</a></p>''')
css='''*{box-sizing:border-box}body{margin:0;background:#f3f7f6;color:#163d46;font:17px/1.8 system-ui,"Malgun Gothic",sans-serif}nav{position:sticky;top:0;background:white;border-bottom:1px solid #c6dcd5;padding:14px 5%;display:flex;gap:25px;z-index:5}a{color:#077a6b}main{max-width:1250px;margin:auto;padding:20px 35px}header{padding:30px 0}h1{font-size:34px;line-height:1.35}h2{font-size:25px}section{padding:32px 0;border-top:1px solid #b9d3ca;scroll-margin-top:70px}.lead{font-size:21px}.result{border-left:4px solid #158773;padding:12px 20px;background:#e8f2ed}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:12px;text-align:left;border-bottom:1px solid #cbded7;vertical-align:top}th{background:#e4efeb}.tablewrap{overflow:auto}figure{margin:28px 0}img{width:100%;height:auto}figcaption{font-size:14px;color:#4e6b66}button:focus-visible,a:focus-visible{outline:3px solid #bd7a23;outline-offset:3px}'''
css+='th:first-child,td:first-child{min-width:135px}td,th{word-break:keep-all;overflow-wrap:anywhere}'
page='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 · 쟁점에서 보완 결과까지</title><style>'+css+'</style><nav><a href="#s0">문제와 결과</a><a href="#s1">사례 선정</a><a href="#s4">지역별 보완</a><a href="#s8">기대효과</a></nav><main><header><p>부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>반복 신고에서 실제 이용조건과<br>개선 상태까지 좁혀봤습니다</h1><p>2020–2024 신고 분석 · 후속 근거 확인 2026-09-16</p></header>'+''.join(f'<section id="s{i}"><h2>{esc(t)}</h2>{b}</section>' for i,(t,b) in enumerate(S))+'</main></html>'
(O/'index.html').write_text(page,encoding='utf-8')
def mdtable(m):
 rows=[]
 for row in re.findall(r'<tr>(.*?)</tr>',m.group(),re.S):rows.append('| '+' | '.join(re.sub('<[^>]+>','',x) for x in re.findall(r'<t[hd]>(.*?)</t[hd]>',row,re.S))+' |')
 if rows:rows.insert(1,'| '+' | '.join(['---']*rows[0].count(' |'))+' |')
 return '\n\n'+'\n'.join(rows)+'\n\n'
md='# 부산 119 쟁점 해결과 심층 사례\n\n'
for title,body in S:
 body=re.sub(r'<table>.*?</table>',mdtable,body,flags=re.S);body=re.sub(r'<img src="([^"]+)" alt="([^"]+)">',r'![\2](\1)',body);body=re.sub(r'<a href="([^"]+)">(.*?)</a>',r'[\2](\1)',body);body=re.sub(r'</(?:p|figure|figcaption)>','\n\n',body);body=re.sub('<[^>]+>','',body)
 md+='## '+title+'\n\n'+html.unescape(body)+'\n\n'
(O/'보고서.md').write_text(md,encoding='utf-8')
docmd=re.sub(r'\]\((?!https?://)([^)]+)\)',r'](../../output/부산119-쟁점해결-20260916/\1)',md)
(R/'docs/40-분석결과/부산-119-쟁점해결-20260916.md').write_text(docmd,encoding='utf-8')
for folder in ['selection','education']:
 for p in (B/folder).iterdir():
  if p.suffix in ['.svg','.png','.csv']:shutil.copy2(p,O/p.name)
reg={'selection':load(B/'selection/manifest.json'),'traffic':sources,'response':load(B/'response/manifest.json'),'education':edu['sources']}
(O/'source-register.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf-8')
W=R/'web/final/results/advance';W.mkdir(parents=True,exist_ok=True)
for p in O.iterdir():
 if p.is_file():shutil.copy2(p,W/p.name)
print('Built',len(S),'sections and',len(cases),'case decisions')
