"""Inventory every current analysis figure and public aggregate before integration."""
from pathlib import Path
import hashlib,json,re,shutil
R=Path(__file__).resolve().parents[1]; W=R/'web/final'; N=R/'data/processed/통합완성-20260916'
N.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')

# Explicit titles and interpretation for previously omitted analysis outputs.
META={
'case_hour_profiles':('신고·시간','10개 초기 사례의 요일·시간','2020–2024 · C조건','접수 건수','시간대별 기록이며 고정된 미래 집중 시각을 뜻하지 않는다.'),
'domain_trends_seasons':('신고·시간','다섯 유형의 연도·계절 차이','2020–2024 · C조건','접수 건수·일수당 비교','종별 차이와 계절을 각각의 분모로 비교한다.'),
'selection_retention':('선택 영향','초기 사례의 결측 제외 영향','2020–2024','선택 신고 / 제외 전 비교 신고','전체 신고 대표성이 아닌 사례별 선택 영향이다.'),
'water_calendar_comparison':('기존 대응','수난 기록과 현재 활동기간 비교','신고2020–2024 · 운영자료2026','연도별 접수·7/4~8/30과 나머지 날짜의 달력일당 접수','자원봉사 활동기간을 전체 수상안전 운영기간으로 바꾸지 않는다.'),
'current-ems-bridge':('문제 배경','과거 접수와 최근 구급 출동의 구분','접수2020–2024 · 출동2024–2025','접수·출동 각각의 건수','다른 사건 단위의 자료를 하나의 시계열로 합치지 않는다.'),
'population_full_ages_2024':('주민 배경','초기 설명 사례의 전체 주민 연령','2024년 말','연령별 주민 인원·구성','어린이부터 최고 연령까지 유지하며 신고자 나이를 추정하지 않는다.'),
'aed-operating-hours':('기존 대응','AED 등록과 24시간 명시 조건','공식 목록 확인2026-09-16','주소 확인 후 차량 제외 등록 건수','기장92·연산70 중 모든 요일 24시간 명시42·41. 미명시를 고장·미운영으로 판정하지 않는다.'),
'apartment-sprinkler-conditions':('주택·시설','아파트 포털의 건물별 소방시설 조건','공식 포털 확인2026-09-16','등록 동 항목','기장137·온천165항목. 가구·건물 전체 설치율이나 법 위반률이 아니다.'),
'busan_all16_coverage':('현장·사업','부산 16구군의 공식 보행사고 지정기록','2025 자료연도','지정기록 수','119 신고와 별도 자료이며 중복되는 지점의 사고 수를 합산하지 않는다.'),
'daeyeon_specific_place_evidence':('현장·사업','대연동 지정지점과 공식 개선 항목','지정2022–2025 · 점검2023','지정기록·개선 항목','못골시장과 못골사거리의 대상·시점을 구분한다. 현재 미해결 건수가 아니다.'),
'motgol_followup_timeline':('현장·사업','못골시장 정비와 기존 효과평가','2024–2026','사업 단계·공식 기록','2025준공과2026평가 수행이 확인된다. 효과평가가 없다는 가설은 채택하지 않는다.'),
'period_weekend_comparison':('신고·시간','10개 사례의 전후 기간 주말 양상','2020–2022 / 2023–2024','주말/평일 일평균 접수비','전체기간 양상과 전후기간 양상을 구별한다.'),
'building_fire_selection':('주택·시설','고층건물 신고의 선택 영향','2020–2024 · B조건','선택 전후 신고 건수','고층건물과 일반주택 화재 분류를 혼합하지 않는다.'),
'commerce_four_area_context':('상권','네 동의 업종 구성과 부산 비교','2024년9월 말','등록 업소·구성비','시장 구간의 점포수가 아닌 법정동 전체 업종 구성이다.'),
'current-fire-inspection':('주택·시설','공식 소방 조사표의 판정과 비고','2026년8월','조사표132행','불량19행 중 현지시정6·비고공란13. 공란은 미조치 증거가 아니다.'),
'current-service-evidence':('기존 대응','장비 관리와 취약주택 지원의 기존 대응','각 공식 기록2024–2026','공식 발표·운영 조건','기존 지원·대여를 반영하고 계획을 보급완료로 바꾸지 않는다.'),
'district_type_composition':('신고·시간','16구군의 다섯 유형 구성','2020–2024 · C조건','선택 신고 중 구성비','주민 위험률이나 위험 순위가 아니다.'),
'field_study_experiment':('현장·사업','보행 현장연구의 도로 조건별 실험','2024년10월26–27일','공표 집계·체험복 전후 비교','30대 조사원의 실험이며 실제 고령자 표본·사업 효과가 아니다.'),
'housing_type_context':('주택·시설','기장·온천의 주택유형 차이','2024통계 · 2025-06-30 경계','총주택 대비 유형별 구성','온천1·2·3동을 합치지 않고, 신고 발생 건물을 추정하지 않는다.'),
'living_hour_context':('생활인구','주거·직장·방문 배경의 24시간 차이','2024 기준월12개 동일가중 평균','공표 월별 일평균 값의 평균','행정동 후보별 배경. 시간과 세 인구 유형을 합산하지 않는다.'),
'time_strategy_sensitivity':('선택 영향','연간 건수 기준에 따른 시간 양상','2020–2024','반복 조합·전후기간 비율','최소 건수 기준은 민감도 비교이며 우선순위 점수가 아니다.'),
'traffic_followup_all14':('현장·사업','공식 교통 점검 14곳의 후속 확인','점검2023 · 후속2024–2026','당시 개선항목·후속 기록','과거 개선항목을 현재 미조치 수로 해석하지 않는다.'),
'01_yearly_scopes':('신고·시간','5개년 처리조건별 신고 규모','2020–2024','접수 건수','세 처리조건의 분모를 구분한다.'),
'02_channel_selection':('선택 영향','전화 접수경로의 선택 영향','2020–2024','접수경로별 잔존','일반전화 등의 전부 제외를 숨기지 않는다.'),
'03_repetition_sensitivity':('선택 영향','반복 관측의 제외 전후 비교','2020–2024','비교 조합','기초 품질 진단. 이후 970개 심층 비교와 모집단이 다를 수 있다.'),
'04_population_age_composition':('주민 배경','초기 후보의 주민 연령 구성','연말 주민 통계','주민 연령 구성비','별도 기준의 주민 배경으로 읽는다.'),
'core8_vs_complete17':('선택 영향','비교집합과 17개 조건 충족 집합','2020–2024','접수 건수·잔존율','비교집합은 선택 진단에만 사용하고 현재 신고에 합산하지 않는다.'),
'01_case_trends':('신고·시간','기존 심층 사례의 5년 변화','2020–2024','접수 건수','초기 사례의 기술통계이며 최종 선정과 구분한다.'),
'02_case_weekday_hour':('신고·시간','기존 심층 사례의 요일×시간','2020–2024','접수 건수','관측 집합 내 시간 특징이며 위험률이 아니다.'),
}
KIND={'문제 배경':'문제 배경','주민 조사':'주민 배경','주민 배경':'주민 배경','선택 영향':'선택 영향','시기 안정성':'선택 영향','시기 비교':'신고·시간','기존 대응':'기존 대응','현장 배경':'현장·사업','결과 연결':'결과 연결','사례 선정':'선택 영향'}
def main():
 rows=[];seen={}; dispositions=[]
 def add(p,m):
  h=sha(p); rel=p.relative_to(R).as_posix()
  if h in seen:dispositions.append({'path':rel,'status':'동일 그림 통합','canonical':seen[h],'sha256':h});return
  seen[h]=rel; m.update(path=rel,sha256=h,id=f'figure-{len(rows)+1:02d}')
  alt=p.with_suffix('.svg');m['svg']=alt.relative_to(R).as_posix() if alt.exists() else None
  rows.append(m);dispositions.append({'path':rel,'status':'수록','sha256':h,'id':m['id']})
 for v in read(W/'results/final/visual-catalogue.json'):
  add(R/v['path'],{'title':v['title'],'kind':KIND.get(v['kind'],v['kind']),'period':v['period'],'unit':v['unit'],'finding':v['coreFinding'],'source':v['source'],'reportLink':v['reportLink']})
 scan=list((W/'results').rglob('*.png'))
 for sub in ['최종결과-20260915/figures','심층분석-20260915/figures','동대응-전체결측제외-20260915/analysis']:
  scan+=list((R/'data/processed'/sub).glob('*.png'))
 for p in sorted(scan):
  rel=p.relative_to(R).as_posix()
  if '/complete/' in rel:continue
  if p.is_relative_to(W/'results') and ('verification' in p.parts or 'final' in p.relative_to(W/'results').parts):
   # Copies in the previous gallery were already indexed by their original hash.
   if sha(p) in seen:dispositions.append({'path':rel,'status':'동일 그림 통합','canonical':seen[sha(p)],'sha256':sha(p)})
   else:dispositions.append({'path':rel,'status':'화면 검증 캡처','sha256':sha(p)})
   continue
  if p.stem in META:
   k,t,period,unit,f=META[p.stem]
   add(p,dict(title=t,kind=k,period=period,unit=unit,finding=f,source='원 집계·공식 출처: '+rel,reportLink=str(p.parent.relative_to(R)/'index.html').replace('\\','/') if (p.parent/'index.html').exists() else ''))
  elif sha(p) in seen:dispositions.append({'path':rel,'status':'동일 그림 통합','canonical':seen[sha(p)],'sha256':sha(p)})
  elif re.fullmatch(r'deepening-(1600|s[345])|explorer-living-1600',p.stem):dispositions.append({'path':rel,'status':'화면 검증 캡처','sha256':sha(p)})
  elif p.stem=='plan-contact':dispositions.append({'path':rel,'status':'공식 도면 열람 이미지; 파생 시각화와 분리','sha256':sha(p)})
  else:dispositions.append({'path':rel,'status':'확인 필요','sha256':sha(p)})
 dump(N/'figure-inventory.json',{'figures':rows,'dispositions':dispositions})
 # Public exports: preserve all current distinct aggregate CSVs, keeping duplicate aliases explicit.
 exports=[]; hashes={}
 for p in sorted((W/'results').rglob('*.csv')):
  if '/complete/' in p.as_posix():continue
  h=sha(p);rel=p.relative_to(R).as_posix()
  if h in hashes:continue
  hashes[h]=rel
  exports.append({'path':rel,'name':p.name,'sha256':h,'bytes':p.stat().st_size})
 dump(N/'aggregate-inventory.json',exports)
 print(json.dumps({'figures':len(rows),'publicAggregates':len(exports),'unresolved':[x['path'] for x in dispositions if x['status']=='확인 필요']},ensure_ascii=False))
if __name__=='__main__':main()
