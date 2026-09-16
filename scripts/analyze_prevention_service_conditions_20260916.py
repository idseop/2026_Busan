"""Structure observed public service conditions; never submit reservations."""
from pathlib import Path
import hashlib,json,csv
from datetime import date
R=Path(__file__).resolve().parents[1];O=R/'data/processed/고도화검증-20260916/education'
load=lambda p:json.loads(p.read_text(encoding='utf-8'))
raw=load(O/'web-extraction.json');extra=load(O/'web-extra-extraction.json')
assert all(x in raw for x in ['2026-07-31','2026-12-31','10명 이하','10명 이상','50 ~ 80분','240분'])
assert all(x in extra for x in ['no=14491','교육용 자동심장충격기','대여기간 : 7일','3~7 세','30 ~ 40분'])
records=[
 {'id':'cpr-basic','name':'응급처치 기본교육','area':'부산','type':'심정지','target':'12세 이상 개인(10명 이상) 또는 단체로 안내','duration':'50–80분','certificate':'평가·수료증 발급 없음','condition':'담당 소방서와 교육 일정 협의','status':'공식 일반 안내','url':'https://119edu.busan.go.kr/main/25','equipment':'교육 과정','benefit':'단순 체험과 수료증 목적을 구분'},
 {'id':'cpr-certificate','name':'응급처치 수료증 과정','area':'부산','type':'심정지','target':'수료증 발급 희망 대상자','duration':'240분','certificate':'실습평가 80점 이상 시 발급 가능','condition':'담당자와 사전 연락·일정 협의','status':'공식 일반 안내','url':'https://119edu.busan.go.kr/main/25','equipment':'교육 과정','benefit':'기본 과정 이수만으로 수료증 발급을 기대하는 오류 방지'},
 {'id':'dongnae-training-rental','name':'동래소방서 CPR 실습 기자재 대여','area':'연산동 소재 동래소방서','type':'심정지','target':'가족·비영리단체·동호회 등 일반인; 영리 목적 제외','duration':'7일','certificate':'대여만으로 수료증 발급 보장 안 함','condition':'유선 문의 → 온라인 신청 → 신분증 지참 방문수령 → 반납','status':'2026.1.1–12.31 운영 안내; 실제 재고는 미확인','url':'https://119edu.busan.go.kr/main/4?action=view&no=14491','equipment':'마네킹·교육용 AED·기도폐쇄 실습조끼(응급환자용 AED 아님)','benefit':'실제 AED 대여와 교육 장비 대여를 목적별로 구분'},
 {'id':'saha-fire2026','name':'사하소방서 소방안전교육','area':'사하구','type':'일반화재(주택)','target':'어린이·청소년·노인·장애인·성인 등','duration':'협의','certificate':'이 공고로 확정하지 않음','condition':'운영·신청기간 및 정확히 10명일 때 개설 조건이 서로 달라 담당자 확인 필요','status':'확보한 공고의 기간·인원 조건 상충; 현재 접수 가능 확정 안 함','url':'https://119edu.busan.go.kr/main/4?action=view&no=17236','equipment':'교육 과정','benefit':'접수중 표기만으로 현재 이용 가능을 자동 안내하지 않음'},
 {'id':'preschool-visit','name':'미취학 아동 소방서 방문교육','area':'부산','type':'일반화재(주택)','target':'유치원·어린이집 등 미취학 아동','duration':'30–40분','certificate':'확인된 발급 조건 없음','condition':'관할 소방서 문의·일정 협의','status':'공식 일반 안내','url':'https://119edu.busan.go.kr/main/35','equipment':'견학·체험','benefit':'12세 이상 응급처치 과정의 연령 조건을 모든 예방교육에 확대하지 않음'}
]
period={'id':'saha-fire2026','operatingStart':'2026-01-01','operatingEnd':'2026-07-31','applicationEnd':'2026-12-31','observedLabel':'접수중','asOf':'2026-09-16','minimumStatements':['10명 이하 폐강','10명 이상 운영 가능; 10명 미만 폐강'],'atExactlyTen':'문장 간 판정 상충','derivedStatus':'게시 조건 재확인','actualServiceCancelled':False,'actualUserDenied':False,'retrieval':'검색·웹 열람 추출본; 직접 HTTP는 서버가 요청 차단. 최신 현장 운영 확인 아님'}
assert date.fromisoformat(period['operatingEnd'])<date.fromisoformat(period['asOf'])<date.fromisoformat(period['applicationEnd'])
out={'question':'기존 교육·대여의 대상·목적·유효기간을 구분하면 어떤 잘못된 안내를 막을 수 있는가?','asOf':'2026-09-16','records':records,'publicationConflict':period,'implementedScope':'시제품의 조건 구분과 공식 이용경로 연결. 기관 정보 자체를 수정하거나 예약하지 않음.','expectedEffect':'이용조건 오해·종료 공고 오인·교육용 장비와 실제 장비 혼동 감소를 기대. 이용자 실험과 서비스 실적 검증은 미실시.','sources':[{'file':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieval':'웹 검색·열람 도구 추출본'} for p in [O/'web-extraction.json',O/'web-extra-extraction.json']]}
(O/'service-conditions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
with (O/'service-conditions.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print('Five service condition records; one publication conflict, not a proven service denial.')
