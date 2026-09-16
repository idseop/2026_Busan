"""Follow-up evidence snapshots. Reuses the existing public-source collector."""
from pathlib import Path
import importlib.util,json,csv,re
import hashlib,zlib,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('collector',ROOT/'scripts/collect_dong_services_20260916.py')
collector=importlib.util.module_from_spec(spec);spec.loader.exec_module(collector)
OUT=ROOT/'data/processed/후속입증-20260916/services'; OUT.mkdir(parents=True,exist_ok=True);collector.OUT=OUT
SOURCES={
 'gijang-aed-rental':'https://www.gijang.go.kr/index.gijang?menuCd=DOM_000000402007002004',
 'yeonje-aed-council':'https://clik.nanet.go.kr/minutes/viewer.do?DOCID=CLIKC2231052549767112&collection=minutes',
 'yeonje-budget2025':'https://clik.nanet.go.kr/minutes/viewer.do?DOCID=CLIKC2230713265058844&collection=minutes',
}
def extract_hwp(key='council-aed-2026'):
 import olefile
 p=OUT/(key+'.hwp');o=olefile.OleFileIO(p);parts=[]
 compressed=bool(o.openstream('FileHeader').read()[36]&1)
 for x in o.listdir():
  if x[0]!='BodyText':continue
  b=o.openstream(x).read();b=zlib.decompress(b,-15) if compressed else b;i=0
  while i+4<=len(b):
   h=struct.unpack_from('<I',b,i)[0];i+=4;tag=h&1023;n=h>>20
   if n==4095:n=struct.unpack_from('<I',b,i)[0];i+=4
   if tag==67:parts.append(b[i:i+n].decode('utf-16-le',errors='replace'))
   i+=n
 s='\n'.join(parts);p.with_suffix('.txt').write_text(s,encoding='utf-8');print(s)
def binary(key,url):
 p=OUT/(key+'.hwp')
 if not p.exists():subprocess.run(['curl.exe','-L','--fail','--max-time','45','-A','Mozilla/5.0','-e','https://119.busan.go.kr/',url,'-o',str(p)],check=True)
 entry={'id':key,'url':url,'accessed_date':'2026-09-16','snapshot':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
 with (OUT/'binary-manifest.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry,ensure_ascii=False)+'\n')
 extract_hwp(key)
def analyze():
 from collections import Counter
 stations={'gijang':('기장소방서',33,1753023),'dongnae':('동래소방서',39,1753101),'geumjeong':('금정소방서',26,1752701),'busanjin':('부산진소방서',34,1753494)}
 rows=[];summaries=[]
 aeds=json.loads((ROOT/'data/processed/동별보완-추가근거-20260916/services/aed-facilities.json').read_text(encoding='utf-8'))
 apts=json.loads((ROOT/'data/processed/동별보완-추가근거-20260916/services/apartment-inventory.json').read_text(encoding='utf-8'))
 norm=lambda s:re.sub(r'\s+','',s)
 for key,(station,n,sid) in stations.items():
  text=(OUT/(key+'-inspection202608.txt')).read_text(encoding='utf-8').split('화재안전조사 결과 세부내역',1)[1]
  lines=[x.strip() for x in text.splitlines() if x.strip()]
  starts=[i for i,x in enumerate(lines) if x.isdigit()]
  assert [int(lines[i]) for i in starts]==list(range(1,n+1)),(station,starts)
  local=[]
  for ix,start in enumerate(starts):
   part=lines[start+1:starts[ix+1] if ix+1<len(starts) else len(lines)]
   end=next(i for i,x in enumerate(part) if x in ['양호','불량','-']);pre=part[:end]
   assert len(pre)>=2,(key,part)
   name=' '.join(pre[:-1]);address=pre[-1];fire,escape=part[end:end+2]
   assert escape in ['양호','불량','-']
   tail=part[end+2:];stop=next((i for i,x in enumerate(tail) if x.startswith(('※','연번','화재안전조사 결과','\x0b'))),len(tail));note=' '.join(tail[:stop])
   dong='';match='미연결';matchsource=''
   explicit=re.search(r'\(([^()]+동)\)',address)
   if explicit:dong=explicit[1];match='조사표 주소에 동명 명시';matchsource=f'https://119.busan.go.kr/119total/{sid}'
   elif '연산동' in name:dong='연산동';match='조사표 대상명에 동명 명시';matchsource=f'https://119.busan.go.kr/119total/{sid}'
   # Reuse only exact full road-number correspondence in verified official AED addresses.
   matches=[a for a in aeds if norm(address) and norm(address)==norm(re.sub(r'^부산광역시\s+\S+\s+(?:기장읍\s+)?','',a['address']).split(',')[0])]
   if not dong and len(set(a['region'] for a in matches))==1:
    dong=matches[0]['region'];match='E-GEN 공식 주소의 도로명·건물번호 일치';matchsource=matches[0]['source_url']
   matches=[a for a in apts if norm(a['apt_nm'])==norm(name)]
   if not dong and len(matches)==1:dong=matches[0]['apt_dong'];match='소방 아파트 포털 공식 단지명 일치';matchsource='https://119.busan.go.kr/safeapt/search/view?aptIdx='+str(matches[0]['idx'])
   if key=='gijang' and norm(name)=='아난티앳부산코브' and norm(address)=='기장해안로268-32':
    assert '기장군 기장읍 기장해안로 268-32' in (OUT/'ananti-address.txt').read_text(encoding='utf-8')
    dong='기장읍';match='시설 운영자 공식 주소의 명칭·도로명·건물번호 일치';matchsource='https://ananti.kr/ko/board/addressAndCall'
   row={'station':station,'period':'2026-08','source_row':int(lines[start]),'target_name':name,'address_internal':address,'fire_facility_result':fire,'escape_firewall_result':escape,'remark':note,'onsite_correction_recorded':'현지시정' in note,'correction_completion_verified':None,'dong':dong,'dong_match':match,'dong_match_source':matchsource,'source_url':f'https://119.busan.go.kr/119total/{sid}'}
   local.append(row);rows.append(row)
  bad=[r for r in local if '불량' in [r['fire_facility_result'],r['escape_firewall_result']]]
  summaries.append({'station':station,'period':'2026-08','listed_rows':n,'assessed_rows':sum(r['fire_facility_result']!='-' for r in local),'fire_defect_rows':sum(r['fire_facility_result']=='불량' for r in local),'escape_defect_rows':sum(r['escape_firewall_result']=='불량' for r in local),'any_defect_rows':len(bad),'any_defect_with_onsite_correction':sum(r['onsite_correction_recorded'] for r in bad),'any_defect_without_correction_note':sum(not r['onsite_correction_recorded'] for r in bad),'all_rows_with_onsite_correction':sum(r['onsite_correction_recorded'] for r in local),'deferred_rows':sum(r['fire_facility_result']=='-' for r in local),'source_url':f'https://119.busan.go.kr/119total/{sid}'})
 def csvwrite(name,data):
  with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 csvwrite('inspection-internal-rows.csv',rows);csvwrite('inspection-public-summary.csv',summaries)
 public=[]
 for dong in sorted(set(r['dong'] for r in rows if r['dong'])):
  subset=[r for r in rows if r['dong']==dong];public.append({'dong':dong,'matched_inspection_rows':len(subset),'fire_defect_rows':sum(r['fire_facility_result']=='불량' for r in subset),'escape_defect_rows':sum(r['escape_firewall_result']=='불량' for r in subset),'onsite_correction_rows':sum(r['onsite_correction_recorded'] for r in subset),'scope':'공식 주소/단지명으로 연결된 조사표 일부; 해당 동 전체 조사 결과 아님'})
 csvwrite('inspection-public-matched-dongs.csv',public)
 (OUT/'inspection-analysis.json').write_text(json.dumps({'period':'2026-08','total_rows':len(rows),'stations':summaries,'matched_dongs':public,'unmatched_rows':sum(not r['dong'] for r in rows),'limitations':['행정구역 통계가 아닌 소방서 조사대상 목록. 표본선정과 종합/부분 조사범위가 달라 소방서별 불량률 순위 금지.','기장 현지시정 기재는 유지관리 실태의 불량 표기와 별도 보존; 현재 불량 지속이나 개선효과로 해석하지 않음.','범용 비고란은 조치완료 전용 열이 아니다. 금정 판정25행과 부산진34행 전체 비고가 비어 있으며 불량13행만의 조치정보 누락이나 관리공백을 뜻하지 않는다.','동래 첨부의 표지일 2026.8.7은 조사기간 8.3~8.31 및 게시일9.7과 불일치한다. 유락여자중학교가 서로 다른 주소로 두 번 기재되어 조사표 행 단위 유지.','부산진의 유사 이름 두 양호행은 같은 도로 건물번호이나 한 행에 층 정보가 추가되어 고유시설로 강제 병합하지 않는다.','과거 신고의 발생건물로 배정하지 않으며 현재 조사대상에 신고 감소효과를 연결하지 않는다.']},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(summaries,ensure_ascii=False));print(json.dumps(public,ensure_ascii=False))
def report():
 facts=[
 {'id':'city-aed-stock','region':'부산 전체','period':'2025-06','status':'공식 보유대수','metric':'AED 설치','value':4431,'unit':'대','denominator':None,'source':'busan-aed-management.pdf','url':'https://www.busan.go.kr/nbtnewsBU/1691436','result':'의무시설3021대+비의무1410대=4431대. 일부 행정시스템 설치정보 불일치 사례를 시가 확인했다. 불일치 건수와 점검불량 수는 미제시.','current_gap_proved':False},
 {'id':'city-aed-inspection','region':'부산 전체','period':'2026-09-04','status':'시의원 관리강화 제안','metric':'장비 불량 실적','value':None,'unit':'대','denominator':None,'source':'council-aed-2026.hwp','url':'https://council.busan.go.kr/choyongwoo/news/view?boardId=NEWS&curPage=1&dataSid=32502','result':'전수점검·통합관리·배터리 및 작동상태 모니터링을 제안. 점검 완료대수나 불량대수 표는 아니다.','current_gap_proved':False},
 {'id':'yeonje-register','region':'연제구 전체','period':'2024-06-14','status':'보건행정과장 회의 답변','metric':'지원 구매','value':None,'unit':'대/년','denominator':None,'source':'yeonje-aed-council.html','url':SOURCES['yeonje-aed-council'],'result':'통상 연4~5대 구매지원 및 비의무기관 소모품 교환 운영. 당시 예산 부족이 크지 않다고 답변. 지도 미표시에는 구급차 제외, 기관 공개거부, 좌표오류가 있다고 설명. 과거 사용신고 이력없음은 실제사용0의 확정증거가 아니다.','current_gap_proved':False},
 {'id':'gijang-rental','region':'기장군 전체','period':'웹 최종수정2024-08-01;확보2026-09-16','status':'공식 운영 절차','metric':'실제 AED 최대 대여기간','value':14,'unit':'일(휴일 포함)','denominator':None,'source':'gijang-aed-rental.html','url':SOURCES['gijang-aed-rental'],'result':'연중 소규모행사·단체여행·심장질환자 가정 대상, 기장 행사 또는 기장 참여자 조건. 방문수령 시 사용법·장비체크, 반납 시 점검. 실제대여/고장/수리 실적은 미확인.','current_gap_proved':False},
 {'id':'gijang-fire2026','region':'기장읍','period':'2026계획(2025-11-26보고)','status':'계획','metric':'화재방지 멀티탭 배부대상','value':1000,'unit':'세대','denominator':None,'source':'gijang-eup-audit2025.html','url':'https://clik.nanet.go.kr/minutes/viewer.do?DOCID=CLIKC5783520197560206&collection=minutes','result':'장애인·독거노인·한부모 등 재난취약계층1000세대,5000만원 주민자치 참여예산. 보급완료나 잔여세대 수가 아니다.','current_gap_proved':False},
 {'id':'dongnae-fire2026','region':'동래소방서·동래/사직복지관 사업','period':'2026-05-21행사;05-27게시','status':'기관 전달과 방문점검 수행, 가정 보급예정','metric':'가정 보급완료','value':None,'unit':'세대','denominator':None,'source':'dongnae-fire-welfare2026.html','url':'https://www.silla.ac.kr/cyber/index.php?idx=2171&mode=view&pCode=sillanews&pg=4','result':'직원 교육→사회복지사 가정방문 위험점검→소방용품 지원의 기존 협업이 확인된다. 단독주택 취약계층 우선배부 예정. 최종 보급세대·온천동별 수혜·잔여 미지원 수치 없음.','current_gap_proved':False}
 ]
 for fact in facts:
  p=OUT/fact['source'];assert p.exists();fact['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 inspection=json.loads((OUT/'inspection-analysis.json').read_text(encoding='utf-8'))
 evidence={'accessed_date':'2026-09-16','facts':facts,'inspection':inspection,'conclusion':'현재 관리점검에서 시설불량이 기록된 사례와 정부의 기존 시정·지원 체계를 함께 확인했다. 공개자료만으로 해당 동 주민의 현재 미지원·접근실패를 확정하지 못했다.','service_direction':'과거 반복신고를 계기로 현재 시설조건과 점검·조치 상태를 구분하여 보여주는 지역 결과 서비스. 시설 신규확충의 필요나 정부 미대응을 전제하지 않는다.','missing':['기장읍·연산동 AED별 실제 출입성·고장·점검일·수리완료 기록','2025 기장군 24000여세대 사업 최종보급·잔여 수혜 집계','동래/온천동 최종 설치완료·적격 미지원 수혜 집계','금정/부산진 2026.8 지적사항 이후 시정완료 기록']}
 (OUT/'followup-services-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
 with (OUT/'operating-evidence.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(facts[0]));w.writeheader();w.writerows(facts)
 lines=['# 현재 운영·점검 후속 근거','',evidence['conclusion'],'','## 2026년 8월 화재안전조사','', '|소방서|조사표 행|판정 행|소방시설 불량|피난·방화 불량|조사 연기|불량 중 현지시정 표기|','|---|---:|---:|---:|---:|---:|---:|']
 for r in inspection['stations']:lines.append(f"|{r['station']}|{r['listed_rows']}|{r['assessed_rows']}|{r['fire_defect_rows']}|{r['escape_defect_rows']}|{r['deferred_rows']}|{r['any_defect_with_onsite_correction']}|")
 lines+=['','132행 중131행 판정, 불량이 하나라도 기록된19행. 기장6행은 현지시정이 함께 기록되어 있고, 금정3·부산진10개 불량행은 일반 비고란이 공란이다. 금정은 연기1행을 뺀25행과 부산진34행 전체가 비어 있어 불량행만의 정보 누락이 아니다. 조치완료 전용 항목이 없으므로 후속조치 누락으로 판단하지 않는다. 비고 공란은 미조치 증거가 아니다.','']+['- '+x for x in inspection['limitations']]
 lines+=['','## AED·취약주택 운영 확인','']
 for r in facts:lines+=['### '+r['region']+' · '+r['status'],'',r['result']+' ['+r['period']+']','',f"[원문]({r['url']}) · `{r['source']}`",'']
 lines+=['## 활용과 남은 범위','',evidence['service_direction'],'','시설 불량 기록은 현재 예방점검의 필요성이 실제 관측된 현장 근거다. 그러나 산악신고와 초읍 상가의 시설불량처럼 유형이 다른 사실은 하나의 원인·해결 관계로 묶지 않는다. 조사대상 건물에 과거 신고를 배정하지 않는다.','', '동 대응은 원문에 동명이 있거나 검증된 공식 보조자료와 정확히 맞는 항목만 연결했다. 기장읍 도로주소의 다수 항목은 동 생략으로 연결을 보류하였다. 검색에 나타난 비공식 주소만으로 강제 배정하지 않았다.','', '웹에는 `inspection-public-summary.csv`와 `inspection-public-matched-dongs.csv`만 사용한다. `inspection-internal-rows.csv`의 개인명의 건물명·주소는 공개하지 않는다.','','### 미확인']+['- '+x for x in evidence['missing']]+['','## 재현','', '`python scripts/collect_followup_services_20260916.py analyze` 후 `... report`. HWP 추출은 olefile, PDF 추출은 pymupdf. 원문 HWP의 제어코드 잔재를 제거해 행번호1..N·양호/불량 열을 대조한다. 다운로드는 공개 HTTPS이며 기관 연락을 하지 않았다.']
 (OUT/'후속운영-분석.md').write_text('\n'.join(lines),encoding='utf-8')
 paths=[p for p in OUT.iterdir() if p.suffix in ['.html','.hwp','.pdf']]
 (OUT/'snapshot-hashes.json').write_text(json.dumps([{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],ensure_ascii=False,indent=2),encoding='utf-8')
 annexes=[('busan-aed-management.pdf','https://www.busan.go.kr/comm/getFile?srvcId=BBSTY3&upperNo=1691436&fileTy=ATTACH&fileNo=1'),('council-aed-2026.hwp','https://council.busan.go.kr/comm/getFile?srvcId=NEWS&upperNo=32502&fileTy=ATTACH&fileNo=1')]+[(k+'-inspection202608.hwp',f'https://119.busan.go.kr/comm/getFile?srvcId=BBSTY1&upperNo={sid}&fileTy=ATTACH&fileNo=1') for k,sid in [('gijang',1753023),('dongnae',1753101),('geumjeong',1752701),('busanjin',1753494)]]
 (OUT/'attachment-manifest.json').write_text(json.dumps([{'file':name,'url':url,'accessed_date':'2026-09-16','sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name,url in annexes],ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'search-attempts.json').write_text(json.dumps({'accessed_date':'2026-09-16','queries':['site.busan.go.kr 2026 자동심장충격기 점검 4431','site.gijang.go.kr 2026 소방시설 보급 24000 완료','site.dongnae.go.kr 2025 소방시설 지원 가구 실적','기장군 2026 소방시설 지원 완료','부산 자동심장충격기 점검 불량 2025 2026','동래소방서 2025 보급 가구','기장군 소방시설 2026','부산 AED 점검결과','site.119.busan.go.kr 동래소방서 8월 2026 결과','site:119.busan.go.kr 2026년 8월 금정소방서 결과','site:119.busan.go.kr 2026년 8월 부산진소방서 결과'],'adopted':'공식 시·구·군·의회·소방서 원문과 실제 사업운영 대학의 복지관 게시. 새 전국 타지역 자료와 검색결과만 있는 시설주소는 배제.','not_obtained':['부산전체·기장읍·연산동 AED 장비별 점검결함/수리완료 실적표','2025기장24000여세대 지원 최종완료/잔여 대상표','온천동별 최종소방용품 수혜대장'],'access_issues':[{'url':'https://119.busan.go.kr/dongnae/119dongaler01','result':'HTTP200이나 오류HTML2167B; 채택제외, 소방통합 공지 실제문서1753101로 대체'},{'url':annexes[0][1],'result':'최초curl401, 공식게시페이지Referer와MozillaUserAgent추가후정상PDF취득'},{'url':'https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01440836&bidPbancOrd=000','result':'후보 URL만 확보. 이번 실제 원문 다운로드·검수 미실행, 분석표 채택 안 함.'}]},ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('key',nargs='?',default='all');p.add_argument('url',nargs='?');a=p.parse_args()
 if a.key=='extract-hwp':extract_hwp(a.url or 'council-aed-2026');raise SystemExit
 if a.key.startswith('binary:'):binary(a.key.split(':',1)[1],a.url);raise SystemExit
 if a.key=='analyze':analyze();raise SystemExit
 if a.key=='report':report();raise SystemExit
 for key,url in (SOURCES.items() if a.key=='all' else [(a.key,a.url or SOURCES[a.key])]):
  if not (OUT/(key+'.html')).exists():collector.fetch(key,url)
