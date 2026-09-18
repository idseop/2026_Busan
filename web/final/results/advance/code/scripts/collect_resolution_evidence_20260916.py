"""Public follow-up source capture; no agency contact or incident re-identification."""
from pathlib import Path
import importlib.util,json,csv,hashlib,re,html
from urllib.parse import urlencode
import zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/고도화검증-20260916/response';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('base',ROOT/'scripts/collect_dong_services_20260916.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);base.OUT=OUT
SOURCES={
'gijang-current-board':'https://119.busan.go.kr/gijang/119gijaler01',
'geumjeong-current-board':'https://119.busan.go.kr/geumjeong/119gjaler01',
'busanjin-current-board':'https://119.busan.go.kr/busanjin/119bsjaler01',
'market-aed-agreement':'https://www.busan.go.kr/nbtnewsBU/1708871',
}
def track():
 attempts=[]
 for station in ['gijang','geumjeong','busanjin']:
  for term in ['시정','재점검','행정처분','조치결과']:
   key=station+'-search-'+term;url=SOURCES[station+'-current-board']+'?'+urlencode({'srchBeginDt':'2026-09-01','srchEndDt':'2026-09-16','srchKey':'cn','srchText':term})
   try:
    if not (OUT/(key+'.html')).exists():base.fetch(key,url)
    s=(OUT/(key+'.html')).read_text(encoding='utf-8');body=(OUT/(key+'.txt')).read_text(encoding='utf-8')
    count=re.search(r'총\s*([\d,]+)\s*건',body)
    # Notices may remain pinned even when query-specific result count is zero.
    links=re.findall(r'<a href="([^"\n]*?/\d{7}[^"\n]*)"[^>]*>(.*?)</a>',s,re.S)
    entries=[{'url':html.unescape(u),'title':re.sub('<[^>]*>','',t).strip()} for u,t in links]
    attempts.append({'id':key,'url':url,'result_count':int(count[1].replace(',','')) if count else None,'visible_post_links':entries,'limitation':'게시본문 검색이며 첨부HWP내부와 비공개 조치대장은 검색대상 아님. 고정공지는 검색0건에도 표시될 수 있음.'})
   except Exception as e:attempts.append({'id':key,'url':url,'error':str(e)})
 (OUT/'official-board-searches.json').write_text(json.dumps(attempts,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{'id':r['id'],'count':r.get('result_count'),'error':r.get('error')} for r in attempts],ensure_ascii=False))
def analyze():
 src=ROOT/'data/processed/후속입증-20260916/services/inspection-internal-rows.csv'
 rows=list(csv.DictReader(src.open(encoding='utf-8-sig')));bad=[r for r in rows if '불량' in (r['fire_facility_result'],r['escape_firewall_result'])];assert len(bad)==19
 stationkey={'기장소방서':'gijang','금정소방서':'geumjeong','부산진소방서':'busanjin'}
 records=[]
 for r in bad:
  # No target name/address in the new data; the prior source-row is the internal join key.
  records.append({'station':r['station'],'source_row':r['source_row'],'source_url':r['source_url'],'onsite_correction_in_original':r['onsite_correction_recorded']=='True','new_correction_completion_confirmed':False,'current_unresolved_defect_confirmed':False,'tracking_scope':'공식 게시본문4어휘 검색·최신 공지목록·일부 공개사업체명 웹검색','tracking_sources':'|'.join(stationkey[r['station']]+'-search-'+x for x in ['시정','재점검','행정처분','조치결과']),'new_match_url':'','status':'원문 현지시정 유지; 이후 재확인 미확보' if r['onsite_correction_recorded']=='True' else '후속시정 여부 공개자료로 확정 불가'})
 with (OUT/'resolution-trace-internal.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 p=OUT/'aed-guideline-v8.hwpx';z=zipfile.ZipFile(p)
 paragraphs=[]
 for name in z.namelist():
  if name.startswith('Contents/section'):
   e=ET.fromstring(z.read(name));paragraphs.extend(''.join(x.itertext()) for x in e.iter() if x.tag.endswith('}p'))
 (OUT/'aed-guideline-v8-paragraphs.txt').write_text('\n'.join(paragraphs),encoding='utf-8')
 text='\n'.join(paragraphs)
 for token in ['제8판','2026. 3.','외부 표출','배터리(패치) 유효기간 초과','위치 정보(좌표)가 없을 경우','장비 사용 가능시간 확인']:assert token in text,token
 facts=[
 {'id':'aed-display-selection','source':'https://www.daedeok.go.kr/board/binary/CHC_000005/2111958.hwpx','issuer':'보건복지부','period':'제8판2026.3','source_location':'붙임18 응급의료정보제공 웹사이트/앱 외부표출 FAQ','finding':'배터리·패치 유효기간 초과 또는 위치좌표 미설정은 외부표출 제한 사유로 안내된다. 보건소 정보수정 및 설치기관 월점검으로 수정하는 경로가 제시된다.','implication':'공개 E-GEN 목록은 등록장비 전체의 무작위표본이 아니다. 공개된172등록의 시간조건을 분석할 수 있지만 미표출·고장 장비 전체를 집계할 수 없다.','not_proved':'부산에서 각 제한사유별 몇 대가 누락됐는지, 현재 누락정보가 모두 잘못됐는지'},
 {'id':'aed-hours-meaning','source':'https://www.daedeok.go.kr/board/binary/CHC_000005/2111958.hwpx','issuer':'보건복지부','period':'제8판2026.3','source_location':'붙임18 점검일지등록 장비사용가능시간 확인','finding':'사용가능시간은 설치기관 운영시간 즉 장비 접근 및 사용 가능한 시간으로 설명된다. 장비교체 등 일시사용불가, 설치위치·좌표, 최근 점검정보를 관리하는 항목이 있다.','implication':'공개시간표와 실제현장 확인을 분리한다. 시간표의 빈값·요일주차 누락을 항상개방이나 미운영으로 채우지 않고 원기록의 확인범위를 전달한다.','not_proved':'지침이 존재한다는 사실만으로 현재 등록시간과 물리적 출입상태 일치 보증'},
 {'id':'aed-existing-update','source':'https://www.daedeok.go.kr/board/binary/CHC_000005/2111958.hwpx','issuer':'보건복지부','period':'제8판2026.3','source_location':'붙임18 관리자변경·점검정보수정 FAQ','finding':'관리책임자 변경은 보건소 통보·정보전송 이후 월점검에서 변경확인 절차를 거친다. 점검일지는 점검이력에서 수정하는 경로가 제공된다.','implication':'새로운 관리대장·갱신절차가 전혀 없다고 주장하지 않는다. 운영 제안은 기존 절차와 공개 결과표시의 연결로 제한한다.','not_proved':'부산의 실제 월점검수행률·정정완료율·작동실패율'},
 {'id':'sasang-existing-signage','source':'https://www.sasang.go.kr/board/view.do?boardId=BBS_0000080&dataSid=546419&menuCd=DOM_000000406001000000&startPage=5','issuer':'부산 사상구보건소','period':'2025-08-05게시','source_location':'본문 안내표지판 안내','finding':'건물입구 및 내부 유도표지판, E-GEN 표준양식 조회·다운로드를 이미 안내한다.','implication':'표지판 안내 자체를 우리서비스 최초기능으로 제안하지 않는다.','not_proved':'개별시설 표지판 실제부착 완료율. 페이지 공통최종수정일을 게시내용 개정일로 쓰지 않음'},
 {'id':'market-agreement','source':'https://www.busan.go.kr/nbtnewsBU/1708871','issuer':'부산시','period':'2025-12-04','source_location':'보도자료 요약','finding':'전통시장 응급대응을 위한 AED 보급확대 업무협약을 발표했다.','implication':'상권배경에 대응하는 기존 AED 사업이 전혀없다는 주장을 기각한다.','not_proved':'특정시장 설치완료·이용·생존효과 또는2025정보불일치 정비성과'},
 ]
 with (OUT/'aed-procedure-evidence.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(facts[0]));w.writeheader();w.writerows(facts)
 summary={'asof':'2026-09-16','prior_input':str(src.relative_to(ROOT)),'prior_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'prior_defect_rows':19,'prior_onsite_correction_rows':6,'prior_no_correction_note_rows':13,'new_completion_matches':0,'confirmed_current_unresolved_defects':None,'interpretation':'신규시정완료매칭0은 미조치0/19 또는시정실적0이 아니라 이번 공개검색에서 후속기록을 확보하지 못한 수치.','followup_search_period':'2026-09-01~2026-09-16 게시본문','source_limit':'첨부문서 전체·비공개조치대장·전기관전수검색 아님.19행은동일관할추적을공유하며모든시설개별웹검색을실시했다고주장하지않음.','rejected_result':{'url':'https://119.busan.go.kr/busanjin/119bsjaler01/1753487','reason':'9/22예정 KT Cloud범일 별도 데이터센터 조사.8월19불량행의시정실적아님.'},'aed_evidence':facts,'recommendation':{'priority_case':'기장읍·연산동 AED 시간조건과 공식 표출기준을 함께 읽는 결과 제공','concrete_action':'비차량등록92/70건과24시간명시42/41건을 구별하고 사용시간·조회일·공식상세링크를 제시. 정보 불명확은 사실대로 표시. 오류신고 자동전송이나실시간작동표시를 구현하지 않음.','existing_process':'보건소 및 설치기관의기존월점검·수정절차활용','decision_not_justified':'특정동 AED 추가설치수량·고장시설명단·관리불이행기관순위','fire_conclusion':'기장6행현지시정기재는 유지. 다른13행은현재미조치로발표하지않고최근공식조사결과로만표시.'}}
 (OUT/'resolution-evidence.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'guideline-manifest.json').write_text(json.dumps({'file':p.name,'url':facts[0]['source'],'official_mirror_notice':'https://www.daedeok.go.kr/cmm/boardViewPopup.do?boardId=CHC_000005&ntatcSeq=1105181458&pageIndex=1','issuer':'보건복지부','version':'2026.3 제8판','sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'acquired':'2026-09-16','scope':'전국공통 관리기준만 채택. 대덕구 실적을 부산자료로 사용하지 않음'},ensure_ascii=False,indent=2),encoding='utf-8')
 md=['# 소방 불량기록 후속시정과 AED 공개기준 재검토','','2026-09-16 기준. 원자료를 반복집계하지 않고 미확인 후속조치와 공개정보의 의미를 추가 확인했다.','','## 결과','','- 기존불량19행: 현지시정기재6·조치미기재13 유지. 새 시정완료·재점검결과와 일치하는 공개기록은 확보하지 못했다. 현재불량지속19행이라는뜻이 아니다.','- 공식3서게시본문에서9/1~16 시정·재점검·행정처분·조치결과를검색했다.12검색중10개0건,2개는동일 데이터센터 사전계획1건이었다. 직접원문을열어9/22예정 별도조사임을확인하고제외했다.','- 개별민감시설명·개인명의건물주소를새공개목록으로만들지않았다. 내부연결키는소방서+원문행번호다. 첨부전체·비공개대장·기관전체를검색했다고주장하지않는다.','','## 새로 확인된 AED 결과','','보건복지부2026.3 제8판을 공식구청배포 HWPX로확보했다. 부산운영실적이아니라전국공통 관리·외부표출 정의에만쓴다.']
 for f in facts:md+=['',f"### {f['id']}",'',f['finding'],'',f['implication'],'','확정하지않은것: '+f['not_proved'],'',f"[원문]({f['source']}) · {f['period']} · {f['source_location']}"]
 md+=['','## 가장 근거가 강한 적용 사례','','기장읍·연산동의 과거 심정지관련 신고에서 현재 AED 등록목록을 연결할 수 있다. 이번 지침으로 장비시간표의 뜻과 공개목록의 선택조건을 더정확히 설명할 수 있게됐다. 화면에는 비차량등록건수와 모든요일24시간명시건수, 상세이용시간·확인일·공식조회경로를구분한다. 이용자가시간조건을찾는지사용성평가할수있다.','','이는 장비위치 신규검색이나관리시스템을처음만드는사업이아니다. 지침에이미있는 보건소·설치기관월점검수정절차를사용한다. 제안범위는반복신고결과에서정확한이용조건까지도달시키는 결과서비스다. 실제접근실패·추가설치필요·생존율효과는이번에도미입증이다.','','화재는19행미조치해결사례로선정할수없다. 원문현지시정과그이후미확인을구분한점검결과를제공하고, 현재지속불량을입증한것처럼시정정책을붙이지않는다.','','## 코드·검증','','`scripts/collect_resolution_evidence_20260916.py track`은공식본문검색저장, `analyze`는기존19행추적표·신규지침근거표·요약을생성한다. HWPX 원본과추출문단·해시를보존했다. 관리포털로그인·기관연락은수행하지않았다.']
 (OUT/'후속시정-AED기준.md').write_text('\n'.join(md),encoding='utf-8')
 print('19 source rows traced; 5 procedure facts; no new completion matches')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('key',nargs='?',default='all');p.add_argument('url',nargs='?');a=p.parse_args()
 if a.key=='track':track();raise SystemExit
 if a.key=='analyze':analyze();raise SystemExit
 for key,url in (SOURCES.items() if a.key=='all' else [(a.key,a.url or SOURCES[a.key])]):
  if not (OUT/(key+'.html')).exists():base.fetch(key,url)
