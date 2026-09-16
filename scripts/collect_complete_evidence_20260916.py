"""Public-source snapshots for the final case judgement. No agency contact."""
from pathlib import Path
import json, hashlib, urllib.request, re, html
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/통합완성-20260916/evidence'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
('water-afterclose-2026','2026 폐장 이후 수상안전 대응은 실제로 발표되었는가?','https://119.busan.go.kr/119news/1753075'),
('geumjeong-current','현재 금정산 탐방 안내 주체와 통제 정보는 무엇인가?','https://naejang.knps.or.kr/front/portal/visit/visitCourseMain.do?menuNo=7020002&parkId=122800'),
('geumjeong-heat','공식적으로 지적한 취약 구간과 이미 운영하는 대응은 무엇인가?','https://naejang.knps.or.kr/front/portal/open/pnewsDtl.do?menuNo=8000517&pnewsGrpCd=PNE01&pnewsId=PNEWSM034580&searchParkId=122800'),
('gijang-small-housing','주택 형태별 기존 시설점검 지원의 대상 조건은 무엇인가?','https://www.gijang.go.kr/board/view.gijang?boardId=BBS_0000002&dataSid=246063&menuCd=DOM_000000101001010000'),
('education-current','기존 사하 교육 기간 상충을 현재 공고가 해소했는가?','https://119edu.busan.go.kr/main/4?action=view&no=17236'),
]
rows=[]
for sid,q,url in SOURCES:
    p=OUT/(sid+'.html')
    try:
        if not p.exists():
            p.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read())
        b=p.read_bytes(); s=b.decode('utf-8',errors='replace')
        s=re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>','',s,flags=re.S|re.I)
        s=html.unescape(re.sub('<[^>]+>','\n',s))
        (OUT/(sid+'.txt')).write_text('\n'.join(x.strip() for x in s.splitlines() if x.strip()),encoding='utf-8')
        rows.append(dict(id=sid,question=q,url=url,acquired='2026-09-16',path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),status='downloaded'))
    except Exception as e: rows.append(dict(id=sid,question=q,url=url,status='failed',error=str(e)))
(OUT/'source-log.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))

REUSED={
 'temporal':'data/processed/효과근거확장-20260916/temporal/focus-summary.json',
 'outdoor':'data/processed/후속입증-20260916/outdoor/outdoor-evidence.json',
 'services':'data/processed/후속입증-20260916/services/followup-services-evidence.json',
 'traffic':'data/processed/효과근거확장-20260916/traffic/traffic-effects-extension.json',
 'traffic-current':'data/processed/고도화검증-20260916/traffic/traffic-resolution.json',
 'education-conditions':'data/processed/고도화검증-20260916/response/resolution-evidence.json',
 'education-survey':'data/processed/효과근거확장-20260916/context/chs-education-summary.json',
 'cpr':'data/processed/효과근거확장-20260916/services/prevention-effects.json',
 'housing':'data/processed/후속입증-20260916/housing/selected_housing_type_context.csv',
}
reused=[]
for key,path in REUSED.items():
 p=ROOT/path
 reused.append(dict(id=key,path=path,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),status='reused_verified_evidence',note='원문 URL과 개별 해시는 이 파일 및 같은 폴더의 원 출처 명세 참조'))
(OUT/'reused-source-log.json').write_text(json.dumps(reused,ensure_ascii=False,indent=2),encoding='utf-8')

DECISIONS={
 '연산동':dict(context='2024 부산 일반인 심폐소생술 시행률 13.8%는 발생지 기반 급성심장정지 조사 지표다. 연제구 교육경험률과 신고 건수는 별도 모집단이다.',existingResponse='부산 교육 예약과 실습 기자재 대여가 이미 존재한다. 연제구 AED 유지지원도 확인됐다.',confirmedGap='교육 정원 부족·실제 이용 장벽은 입증되지 않았다. 사하 공고에는 기간 및 정확히 10명일 때 조건 상충이 재확인됐으나 연산동의 운영 결함은 아니다.',proposal='연산 사례에서는 대상·사전 연락·운영 시점이 확인된 기존 교육 및 대여 경로를 제공한다. 조건이 충돌하는 프로그램은 신청 가능으로 단정하지 않는다.',status='기존 서비스 안내 보완 가능 / 교육 증설 보류',remainingEvidence=['연제구 실제 신청·수료·취소·대기 사유 및 제공 시간','실습 전후 표준화된 수행평가와 후속 유지율'],expectedEffectMeasurement='안내 전후 이용 조건 확인 정확도·완료 시간·오신청률을 비교하고, 동의 기반 교육 완료와 수행평가는 별도 평가한다. CPR 시행률 상승을 웹 효과로 약속하지 않는다.',sourceRefs=['cpr','services','education-current']),
 '부전동':dict(context='BDI 보행 실험과 동 전체 상권은 현장 배경이며 구급 교통사고 신고를 시장 조사선에 귀속하지 않는다.',existingResponse='부전역 맞이길 사업의 2026 제막식과 2025 설계 수량이 확인됐다. 보도·유도시설이 전혀 없다는 주장은 기각한다.',confirmedGap='조사 당시 보행환경 차이는 확인됐으나 현재 잔여 결함과 개선 효과는 미확인이다.',proposal='현재 사업 안내와 조사·설계·완료·효과 확인 단계를 나누어 제공하고, 동일 구간을 식별한 뒤 개선 후 보행 조건을 비교한다.',status='기존 개선사업 연결 / 추가 시설 설치 보류',remainingEvidence=['최종 준공도와 검수 수량','BDI 조사선과 사업 구간의 대응','동일 조건 전후 통행 및 장애 요소 관측'],expectedEffectMeasurement='동일 구간 보행시간·장애물·보차분리 상태를 사전 정의해 비교한다. 설계 수량을 준공 수량으로 계산하지 않는다.',sourceRefs=['traffic']),
 '광안동':dict(context='BDI 현장 표와 지도 길이 차이가 있어 원표를 유지한다. 계절 최고값은 일부 연도 제외에 민감하다.',existingResponse='2025 광안역 일원 도로정비의 기존 집행 근거가 있다.',confirmedGap='사업 시행 이전 현장 문제와 현재 미해결 문제는 같지 않다. 현재 잔여 구간은 확정하지 못했다.',proposal='특정 월 집중 정책보다 동일 조사선·준공 구간 대조와 현장 재확인 결과를 연결한다.',status='비교 사례 / 계절 집중·신규 사업 보류',remainingEvidence=['최종 도면과 BDI 조사선 일치','완료 후 같은 구간 보행환경 결과'],expectedEffectMeasurement='사전·사후 동일 구간의 노면·분리·장애 요소와 보행시간을 비교하고 조사 조건을 유지한다.',sourceRefs=['traffic']),
 '초읍동':dict(context='동 전체 산악 접수와 찬물샘 등산로 민원은 독립 자료다.',existingResponse='2025 공식 답변은 돌출 뿌리·암석 우려에 매트·편책 설치와 불필요 구역 설치 지양을 확인한다.',confirmedGap='민원 당시 보행 불편과 기존 조치가 확인된다. 현재 미조치 구간은 확정되지 않았다.',proposal='기존 정비 이력과 공식 탐방 안내를 함께 제공한다. 일괄 매트 증설이나 특정 월 위험 안내는 채택하지 않는다.',status='정비 사실 안내 / 구간 증설 보류',remainingEvidence=['신고 발생 구간의 검증된 위치','구간별 현재 노면·정비 완료·이용자 관측'],expectedEffectMeasurement='같은 구간의 걸림 요소·우천 시 상태·이용 불편을 재관측한다. 동 전체 신고 증감을 매트 효과로 보지 않는다.',sourceRefs=['outdoor','geumjeong-current']),
 '금성동':dict(context='금성동 산악 접수의 겨울 최고 양상은 금정산 전체 또는 특정 탐방로 사고 위치·원인을 확정하지 않는다.',existingResponse='2026 국립공원공단이 현재 탐방·통제 정보를 제공한다. 8/10 공고는 그늘·식수 부족 장거리 능선 23.5km를 폭염 취약 구간으로 안내하고 쉼터 3곳을 제시한다.',confirmedGap='공식적으로 지정한 폭염 취약 구간은 확인했다. 이는 과거 겨울 산악 신고 원인이나 쉼터 부족을 입증하지 않는다.',proposal='2025 안내만 고정하지 않고 현재 관리기관의 탐방로·통제·쉼터 안내로 연결한다. 계절별 공식 위험 안내와 신고 시기 관측을 별도로 표시한다.',status='최신 공식 안내로 갱신 가능 / 시설 부족 미확정',remainingEvidence=['과거 신고의 실제 탐방로 및 원인','폭염 안내 이후 실제 이용·조치 기록','현재 겨울철 구간별 안전 공고'],expectedEffectMeasurement='출발 전 통제·쉼터·경로 확인 성공률과 최신 공고 연결 오류를 측정한다. 과거 겨울 접수로 폭염 효과를 추정하지 않는다.',sourceRefs=['outdoor','geumjeong-current','geumjeong-heat']),
 '다대동':dict(context='5년 중 1년씩 제외해도 여름의 달력일수당 접수 최고가 유지된다. 해수욕장 외 수난 위치는 미확정이다.',existingResponse='2026 동·서측 운영 계획이 있고, 9/2 부산소방은 폐장 후 9/1~9/13 다대포 등 6곳 특별관리와 금·토·일 소방 순찰 및 의용소방대 연장을 발표했다.',confirmedGap='폐장 이후 안전 위험은 기관이 공식적으로 인지하고 대응을 연장했다. 대응이 없다는 공백 주장은 기각한다.',proposal='여름 전 안내와 폐장 후 실제 운영기간·입수 주의·공식 관리 정보를 구분해 제공한다. 새 야간 순찰 신설은 제안하지 않는다.',status='발표상 특별관리 9/13 종료 / 이후 운영 미확인',remainingEvidence=['동측·서측 및 해수욕장 외 접수 위치','기간별 실제 근무·구조 및 예방 계도 일지'],expectedEffectMeasurement='개장·폐장 이후 이용조건 이해도 및 잘못된 상시 안전 보장 해석의 감소를 평가한다. 신고 감소는 별도 사건·노출 자료가 있어야 평가한다.',sourceRefs=['outdoor','water-afterclose-2026']),
 '우동':dict(context='우동 수난 접수를 해운대해수욕장 전체 신고로 바꾸지 않는다.',existingResponse='2026-09-02 부산소방은 해운대 119시민수상구조대가 당초 계획대로 9/15까지 정상 운영한다고 명시했다.',confirmedGap='가을 접수가 있다는 사실만으로 8월 이후 대응 공백을 주장할 수 없다.',proposal='2026 실제 발표 운영기간과 이후 확인이 필요한 상태를 명시한 해변 안전 안내를 제공한다.',status='당초 9/15까지 운영계획 확인 / 이후 운영 미확인',remainingEvidence=['우동 접수의 실제 해변·항만·연안 구분','9/15 이후 실제 안전관리 공고·근무 자료'],expectedEffectMeasurement='기간을 잘못 이해한 응답 비율과 공식 최신 안내 확인률을 측정한다. 제공기관 활동을 웹 성과로 주장하지 않는다.',sourceRefs=['outdoor','water-afterclose-2026']),
 '기장읍':dict(context='주택형태·공동주택 설비는 주민 환경 배경이다. 해당 건물의 화재 신고 또는 시설 미작동과 직접 연결되지 않았다.',existingResponse='기장군 주택용 소방시설 보급 계획 외에 2026-05-29 공고가 비의무관리 5층 이상 아파트의 소방 등 시설 무상점검을 안내한다. 신청 6/8 마감, 점검 6~12월 예정이다.',confirmedGap='지원제도 부재는 아니다. 개별 단지 선정·점검 완료 및 미충족 가구는 확인되지 않았다.',proposal='단독·다세대와 아파트의 지원 조건을 구분하고, 마감된 공고는 현재 신청 가능한 서비스로 표시하지 않는다.',status='주택 형태별 기존 지원 구분 가능 / 지원 물량 확대 보류',remainingEvidence=['2026 지원 대상 선정 및 실제 점검 결과','가구별 설치·작동 확인의 비식별 집계','건물 유형과 신고 위치의 검증'],expectedEffectMeasurement='주택 형태별 올바른 제도 선택률·마감 프로그램 오신청 감소를 평가한다. 설비 수와 화재 감소의 인과는 별도 검증한다.',sourceRefs=['services','housing','gijang-small-housing']),
 '온천동':dict(context='아파트 설비 공시와 동 전체 주택화재 접수를 분리한다. 주민 후보 행정동은 강제 합산하지 않는다.',existingResponse='동래 소방·복지 연계 교육 및 방문 안전 확인 협력은 기존 근거로 확인된다.',confirmedGap='화재안전조사 일반 비고가 비어 있는 13행은 미조치 증거가 아니다. 온천동 주택시설 부족을 입증하지 못했다.',proposal='기존 방문 안전·교육·주택형태별 안전 안내를 연결하고 확인되지 않은 건물 결함 지도를 만들지 않는다.',status='기존 예방 서비스 안내 / 특정 건물 개선 보류',remainingEvidence=['실제 방문·설치 및 후속 작동 점검 집계','주택 유형별 접수와 점검 대상의 일치'],expectedEffectMeasurement='가구별 해당 안내 이해도 및 실제 서비스 연결 완료를 별도로 측정한다. 신고자 연령이나 특정 아파트 화재로 일반화하지 않는다.',sourceRefs=['services','housing']),
}
focus=json.loads((ROOT/REUSED['temporal']).read_text(encoding='utf-8'))
cases=[]
for f in focus:
 d=DECISIONS[f['rawDong']]
 if f['subtype']=='교통사고': d['sourceRefs'].append('traffic-current')
 if f['rawDong']=='연산동': d['sourceRefs']+=['education-conditions','education-survey']
 cases.append(dict(district=f['district'],rawDong=f['rawDong'],type=f['type'],subtype=f['subtype'],period='2020~2024',scope='C',
 observation={'count':f['count'],'yearCounts':f['yearCounts'],'topMonths':f['topMonths'],'topSeasons':f['topSeasons'],'leaveOneSeasonExact':f['leaveOneSeasonExact'],'comparison':'달력일수당 값; 1개년씩 제외한 5개 비교. 특정 연도 최고와 구분'},**d))
payload={'asOf':'2026-09-16','purpose':'과거 신고에서 선택한 지역의 현재 예방 안내와 기존 조치 사실을 연결한다. 실제 미충족 수요와 자료 미확보는 분리한다.','cases':cases,'relatedPlaces':[
 {'place':'못골시장','finding':'2025 사업 완료와 2026 효과평가 계약 완료·대금 지급은 기존에 확인했다. 최종 평가 보고서 공개본은 이번 재검색에서도 확보하지 못했다.','proposal':'이미 평가된 사업의 최종 보고서로 사후 결과를 확인; 평가 미실시 주장 금지'},
 {'place':'신평역','finding':'기존 보행정비 근거와 BDI 실험이 있으며 동일 조사선별 개선 결과는 별도 검증 대상이다.','proposal':'기존 사업 구간과 실험선을 대조한 후 같은 조건 관측; 단순 시설 신설 보류'}],
 'newEvidenceSummary':['금정산 현재 국립공원 관리·폭염 취약 구간 및 쉼터 안내 확인','2026 폐장 후 다대포 등 안전관리 연장과 해운대 9/15 운영 확인','기장 비의무관리 5층 이상 아파트 무상 시설점검 공고 확인; 신청 마감과 점검 기간 분리','사하 교육 공고 내부 상충 지속 확인'],
 'notClaimed':['정부가 기존에 위험을 몰랐다는 주장','현재 미개선 13건','고령 주민의 사고라고 단정','웹 공개만으로 CPR·피해 감소 효과 입증','현재 실시간 사고지도']}
(OUT/'case-assessments.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
queries=[('금정산 현재 안전·탐방 공고','국립공원공단 공고 확보'),('기장 2026 주택시설 지원','시설점검 조건 공고 확보, 선정·실적 미확보'),('연제 2025 심폐소생술 실적','이번 검색에서 동별 수요·대기·성과 원장 미확보'),('못골시장 2026 효과평가 공개','기존 계약 완료 근거 유지; 최종 평가 보고서 미확보'),('사하 2026 교육 조건 대체 공고','공식 현재 상세 재확인; 기간·10명 경계 상충 해소 근거 미확보'),('다대포 2026 안전관리','폐장 후 연장 대응 새 원문 확보'),('동래 2026 주택시설 지원','새 동별 집행·미충족 수요 자료 미확보')]
(OUT/'search-audit.json').write_text(json.dumps([dict(question=q,result=r,searchedAt='2026-09-16',method='공식 도메인 중심 공개 웹 검색; 기관 접촉 없음') for q,r in queries],ensure_ascii=False,indent=2),encoding='utf-8')
report=['# 9개 사례 예방·지원 판단 보완','',payload['purpose'],'','## 새로 확인한 내용','']+['- '+s for s in payload['newEvidenceSummary']]
report+=['','2026 수상안전 공고는 9/1을 월요일로 잘못 적었다. 실제 2026-09-01은 화요일이다. 본 결과는 명시된 날짜 범위만 사용하고 원문 요일은 재사용하지 않는다. 점검·순찰 계획 발표를 실제 근무 실적으로 바꾸지 않는다.','']
for c in cases:
 report+=['## '+c['rawDong']+' · '+c['subtype'],'',f"관측: 2020~2024 C조건 {c['observation']['count']:,}건. 연도별 {c['observation']['yearCounts']}. 최고 계절 {c['observation']['topSeasons']}; 1개년 제외 비교 {c['observation']['leaveOneSeasonExact']}/5에서 유지.",'','기존 대응: '+c['existingResponse'],'','공백 판정: '+c['confirmedGap'],'','보완 내용: '+c['proposal'],'','판단 상태: '+c['status'],'','추가 근거: '+'; '.join(c['remainingEvidence']),'','효과 측정 계획: '+c['expectedEffectMeasurement'],'']
report+=['## 차별점과 남은 범위','','차별점은 정부가 이미 제공하는 기능을 새로 발명했다는 주장이 아니다. 신고 선택 영향·시간 반복성·동 연결 범위를 확인한 뒤, 그 지역에서 현재 이용할 수 있는 기존 제도의 대상과 시점을 연결하고 완료 사업을 중복 제안에서 제외하는 것이다. 현재 확정 가능한 보완은 안내·조건 연결이며, 시설·인력의 추가 공급 필요성과 실제 피해 감소 효과는 별도 입증이 필요하다.','','출처: source-log.json은 이번 원문 확보, reused-source-log.json은 재사용 근거 파일의 현재 해시, search-audit.json은 미확보를 포함한 공개 조사 범위다.']
(OUT/'results.md').write_text('\n'.join(report),encoding='utf-8')
assert len(cases)==9 and sum(c['observation']['count'] for c in cases)==2223
source_ids={r['id'] for r in rows+reused}
assert all(set(c['sourceRefs'])<=source_ids for c in cases)
checks=[]
for name,tokens in {'geumjeong-heat':['23.5km','2026.08.10','북문탐방지원센터'],'gijang-small-housing':['2026.6.8.','5개 층 이상','6월~12월'],'water-afterclose-2026':['2026-09-02','다대포','정상 운영'],'education-current':['2026-07-31','2026-12-31','10명 이하','10명 이상']}.items():
 s=(OUT/(name+'.txt')).read_text(encoding='utf-8')
 for token in tokens:
  assert token in s,(name,token)
  checks.append({'source':name,'expectedText':token,'pass':True})
(OUT/'author-checks.json').write_text(json.dumps({'status':'PASS','scope':'원문 다운로드 본문 표식·9개 사례 원집계 복사·출처 연결 무결성; 독립 검증 아님','caseCount':len(cases),'countSum':2223,'sourceTextChecks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print('Nine case assessments written; current official snapshots and prior evidence hashes preserved.')

