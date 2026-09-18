"""Package source-grounded service questions and geographic limitations; no policy selection."""
from pathlib import Path
import json,hashlib
import pandas as pd
import openpyxl
from shapely.geometry import shape
R=Path(__file__).resolve().parents[2];I=R/'data/interim/최종보완근거-20260915';O=R/'data/processed/최종결과-20260915';O.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def source(id,url,file,kind,date=None):
 p=R/file;assert p.exists()
 return {'id':id,'url':url,'local_file':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size,'retrieved_at':'2026-09-15','evidence_kind':kind,'publication_date':date}
sources=[source('ansim2023','https://www.korea.kr/news/customizedNewsView.do?newsId=148923379','data/interim/최종보완근거-20260915/ansimcall-2023.html','original_official_html','2023-12-05'),
 source('ansim2024','https://www.korea.kr/news/policyNewsView.do?newsId=148935029','data/interim/최종보완근거-20260915/ansimcall-2024.html','original_official_html','2024-10-17'),
 source('multimedia2024','https://119.busan.go.kr/119total/1655842?curPage=32&srchBeginDt=2024-05-21&srchEndDt=2025-05-21&srchKey=&srchText=','data/interim/최종보완근거-20260915/web-extracted-official-sources.json','web_tool_extracted_official_page_not_original_html','2024-11-07'),
 source('emergency2026','https://119.busan.go.kr/119notice/1718927?curPage=1&srchBeginDt=&srchEndDt=&srchKey=&srchText=','data/interim/최종보완근거-20260915/busan-emergency-official-search-extract.json','official_site_search_extract_direct_download_401','2026-02-13'),
 source('sgis_request','https://sgis.mods.go.kr/view/pss/requestData','data/interim/최종보완근거-20260915/sgis-request.html','original_http_response_login_required'),
 source('receipt402','https://bigdata-119.kr/goods/goodsInfo?goods_mng_sn=402','data/interim/최종보완근거-20260915/receipt-product402.html','original_official_html'),
 source('ilgwang2022','https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000052&nttId=91305','data/interim/동연결검토-20260915/article-91305.html','official_html_acquired_earlier_same_day','2022-03-30')]
services=[
 {'id':'ansimcall','title':'119안심콜','status':'existing_service_conditions_documented','source_ids':['ansim2023','ansim2024'],'target':'중증질환자·장애인·고령자·독거노인·나홀로어린이·외국인·임산부 등을 포함한 국민과 외국인','operating_hours':{'value':None,'status':'상시 긴급신고 활용 취지는 확인했으나 등록상담창구의 구체적 운영시간은 해당 안내에서 미확인'},'access_conditions':['본인 또는 대리인의 사전 등록','등록된 전화번호로119 신고해야 사전정보 활용 가능','주소·병력·전화번호 변경 시 정보 수정 필요','등록정보는 긴급구조의 참고자료'],'coverage':'지역에 관계없는 전국 서비스 안내; 부산 동별 등록률·실제 활용범위 미확인','reference_date':'2023-12-05 및2024-10-17 공식 안내','facts':['사전 건강·연락 정보를 신고와 함께 활용하는 기존 대응이 존재한다.'],'unknowns':['2020~2024 부산 동별 적정 대상 규모와 가입·갱신·활용률','미등록 또는 정보오류가 관측 신고에 미친 영향','등록지원의 실제 운영기관·시간과 접근장벽'],'next_questions':['해당 동에서 등록안내·대리등록·정보갱신이 실제로 충분히 제공되는가?','가입자 정보가 접수 시 확인된 비율과 미활용 이유를 집계할 수 있는가?'],'proposal_status':'held_until_local_gap_verified'},
 {'id':'multimedia','title':'119다매체 신고','status':'existing_channels_documented','source_ids':['multimedia2024'],'target':'음성통화가 어려운 상황의 신고자와 청각장애인 등을 포함한 신고자','operating_hours':{'value':None,'status':'공지에 별도 채널별 운영시간·장애시간·응답목표 미기재'},'access_conditions':['119 영상통화','119 SMS/MMS로 재난 위치·내용 전달','119신고 앱 및 안내된 인터넷 신고방식','앱 위치정보 이용과 기기·통신조건은 채널별 확인 필요'],'coverage':'부산 사하소방서가 안내한119 신고 채널; 해당 게시글만으로 동별 이용가능성·실제처리성과를 확정하지 않음','reference_date':'2024-11-07','facts':['음성 외 영상·문자·앱 등 기존 신고경로 안내가 존재한다.'],'unknowns':['동별·연령별 실제 신고 접근 어려움','접수경로별 위치확인 실패·누락 원인','2020~2024 채널 변경·운영 장애 이력'],'next_questions':['분석에서 남은 접수경로 표본과 제외된 표본의 차이가 기록방식 때문인지 접근장벽 때문인지 확인할 수 있는가?','문자·영상 이용 안내의 대상과 제공방식이 실제 필요에 맞는가?'],'proposal_status':'held_until_channel_gap_verified'},
 {'id':'emergency_information','title':'부산119 구급상황관리센터 안내','status':'current_notice_only','source_ids':['emergency2026'],'target':'진료 가능 병원·의원·약국 정보와 질병상담이 필요한 이용자','operating_hours':{'value':'24시간','status':'2026-02-13 부산 공식 설연휴 공지에서 확인'},'access_conditions':['119 전화'],'coverage':'부산소방재난본부119종합상황실 구급상황관리센터 안내. 상담 처리범위·배치인원·대기시간은 미확인','reference_date':'2026-02-13 공지, 안내기간2026-02-13~18','facts':['해당 공지는 병의원·약국 안내와 질병상담,24시간 운영을 명시한다.'],'unknowns':['2020~2024 당시 운영범위·인력·대기시간','동별 정보 접근성 및 상담 수요 대비 처리 여건','현재 실제 개별 의료기관 운영 여부'],'next_questions':['신고 시간대별 정보 문의·질병상담과 응급출동이 어떻게 분리 기록되는가?','2020~2024 상담운영과 현재 운영 간 변경사항을 확보할 수 있는가?'],'proposal_status':'held_due_to_time_mismatch_and_unverified_gap'}]
selection=[{'dataset':'2020~2024 주민등록 전체연령','adopted':'already_used','reason':'지역 주민 배경 확인에 직접 필요','period':'매년12월말','limits':'신고 대상자 연령·생활인구·연평균 아님'},
 {'dataset':'행안부 KIKmix·행정동 이력','adopted':'used_for_geographic_audit','reason':'동별 비교의 필수 연결 조건','period':'2020~2024 당시 판본 및2025-01-01말소이력 대조','limits':'관계 후보 검증이며 역사적 폴리곤·위치 확정 아님'},
 {'dataset':'상권20분기','adopted':False,'reason':'현재 질병·부상·교통사고 유형만으로 특정 업종 검토 질문이 확정되지 않음','period':'2020~2024 보유','limits':'확보했다는 이유로 결합하지 않음'},
 {'dataset':'건축행정120첨부','adopted':False,'reason':'공사 관련 구체적 사고·현장 질문이 선정되지 않음','period':'2020~2024 보유','limits':'허가·착공·준공 기록은 실제 가동 현장 전체목록 아님'},
 {'dataset':'시간·연령 생활인구','adopted':False,'reason':'주민 외 체류인구의 필요성이 확정되지 않아5년기본분석에 추가하지 않음','period':'2023~2024 목표기간 자료 보유','limits':'2020~2022 없음; 시간×연령 교차 추정 금지'},
 {'dataset':'특정 도로구간·교통안전시설','adopted':False,'reason':'교통사고 세부분류만으로 특정 구간과 원인이 확인되지 않음','period':None,'limits':'신고 위치 확정·사고상황·기존구간대응 확인 후 필요한 범위만 선택'}]
response={'schema_version':'1.0','checked_at':'2026-09-15','analysis_trigger':'확정17완전기록 내 구급 우세 및 질병·부상·교통사고 반복 질문. 부산 전체 수요 대표성이나 대상자 연령은 미확정.','services':services,'sources':sources[:4],'background_selection':selection,'policy_decision':'no_location_specific_intervention_approved','disclaimer':'기존 서비스 존재는 해당 동 대응충분성의 증명이 아니며, 신고 많음은 대응공백의 증명이 아니다. 피해감소 효과를 약속하지 않는다.'}
dump(O/'response_evidence.json',response)
# Independent use of existing geometry only; never invoke legacy stats-based builder.
mp=R/'web/data/busan-districts.geojson';ma=json.loads((R/'data/interim/웹경계검증/manifest.json').read_text(encoding='utf8'));assert sha(mp)==ma['output_sha256']
geo=json.loads(mp.read_text(encoding='utf8'));assert len(geo['features'])==16 and all(shape(f['geometry']).is_valid and not shape(f['geometry']).is_empty for f in geo['features'])
registry=pd.read_csv(R/'data/processed/동별예방분석-20260914/population/region_registry.csv',dtype=str,keep_default_na=False)
names={f['properties']['name'] for f in geo['features']}
assert all(set(registry.loc[registry.year.eq(str(y))&registry.level.eq('district'),'district_name'])==names for y in range(2020,2025))
geo['metadata']={'sourceUrl':'https://www.data.go.kr/data/15129688/fileData.do','sourceSha256':geo['metadata']['sourceSha256'],'geometryInputSha256':sha(mp),'baseDate':'2025-06-30','outputCrs':'EPSG:4326','usage':'current_reference_only','canDisplayHistoricalCounts':False,'canAssignHistoricalReceipts':False,'limitation':'2025-06-30 구군 윤곽은 위치 참고용.2020~2024 역사 경계나 신고값 지도 아님.'}
dump(O/'reference_districts.geojson',geo)
date_rows=[];input_hashes=[]
for year in range(2020,2025):
 p=R/f'data/processed/동대응-전체결측제외-20260915/completeness/complete_17_{year}.csv.gz';input_hashes.append({'year':year,'file':str(p.relative_to(R)),'sha256':sha(p)})
 manifest=json.loads((p.parent/'manifest.json').read_text(encoding='utf8'));assert sha(p)==next(x['sha256'] for x in manifest['outputs'] if x['file']==p.name)
 d=pd.read_csv(p,dtype=str,keep_default_na=False,usecols=['DCLR_DT','CLMTY_SGG_NM','CLMTY_EMD_NM'])
 d=d[d.CLMTY_SGG_NM.eq('기장군')&d.CLMTY_EMD_NM.isin(['일광면','일광읍'])].copy();d['date']=d.DCLR_DT.str.strip().str[:8]
 d['period']=d.date.map(lambda x:'before_20220401' if x<'20220401' else 'from_20220401');d['year']=year
 date_rows.extend(d.groupby(['year','CLMTY_EMD_NM','period']).size().reset_index(name='count').to_dict('records'))
workbook=R/'data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx'
wb=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
fields=['acdnt_ocrn_lot','acdnt_ocrn_lat','damg_rgn_lot','damg_rgn_lat','clmty_emd_nm']
defs=[{'column':r[1],'name':r[4],'description':r[5]} for r in wb.active.values if len(r)>5 and r[1] in fields];wb.close()
geographic={'schema_version':'1.0','checked_at':'2026-09-15','historical_boundary_status':{'years':[2020,2021,2022,2023,2024],'acquired':False,'request_status':'login_required','source_id':'sgis_request','attempt_count_this_pass':1,'fallback':'continue_nonspatial_analysis_without_assignment'},'coordinate_definition_status':{'source_file':str(workbook.relative_to(R)),'sha256':sha(workbook),'definitions':defs,'CRS_verified':False,'precision_verified':False,'source_field_admin_vs_legal_verified':False,'replacement_between_coordinate_pairs':False},'ilgwang_date_audit':{'official_change_date':'2022-04-01','source_id':'ilgwang2022','input':'fixed complete17 records; all processing outcomes','input_hashes':input_hashes,'rows':date_rows,'finding':'2022년 개편일 이후에도 일광면314건,2023년에도4건 기록.날짜만으로 원문지역을 자동치환하지 않음.','classification':'record_name_date_inconsistency_not_proven_location_error'},'map_reference':{'geojson_path':str((O/'reference_districts.geojson').relative_to(R)),'sha256':sha(O/'reference_districts.geojson'),'input_geometry_sha256':sha(mp),'reference_date':'2025-06-30','usage':'current_reference_only','features':16,'all_geometries_valid':True,'district_names_match_2020_2024_registry':True,'historical_value_fill_allowed':False,'historical_point_assignment_allowed':False},'sources':sources[4:],'held_cards':[{'id':'historical_dong_map','status':'held','reason':'당시 경계와 위치 의미 검증 미완료','next_question':'정식 SGIS 신청으로 당시 경계·기준일·코드 대응을 확보할 수 있는가?'},{'id':'ilgwang_linkage','status':'held','reason':'공식 개편일 후 구명칭 잔존','next_question':'기관의 지역명 갱신 규칙과 당시 정확한 발생주소로314건의 지역을 검증할 수 있는가?'},{'id':'local_prevention_policy','status':'held','reason':'동 총량·현장원인·기존서비스 잔여공백 미확인','next_question':'검증된 신고 특성과 실제 대상·운영시간·활용률을 대조했을 때 어떤 보완이 필요한가?'}]}
render_log=I/'map-simplification-validation.json'
if render_log.exists():
 render=json.loads(render_log.read_text(encoding='utf8'));render_path=R/render['output'];assert sha(render_path)==render['output_sha256']
 geographic['map_reference']['render_js']=render['output'];geographic['map_reference']['render_sha256']=render['output_sha256'];geographic['map_reference']['render_tolerance_m']=render['tolerance_m'];geographic['map_reference']['render_validation_file']=str(render_log.relative_to(R))
dump(O/'geographic_evidence.json',geographic)
dump(I/'source-manifest.json',{'sources':sources,'download_failures':[{'url':u,'result':'HTTP401','raw_html_acquired':False} for u in ['https://www.busan.go.kr/nbnews/1710051','https://119.busan.go.kr/119total/1655842','https://www.busan.go.kr/nbnews/1718927','https://119.busan.go.kr/119notice/1718927?curPage=1&srchBeginDt=&srchEndDt=&srchKey=&srchText=']],'note':'부산 공지의 웹 추출·검색 추출을 원본HTML 다운로드로 표시하지 않음. 로그인 우회·대외신청·등록 실행 안 함.'})
print(json.dumps({'services':len(services),'map_features':16,'ilgwang_audit':date_rows},ensure_ascii=False,indent=2))
