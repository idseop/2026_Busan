"""Official follow-up snapshots; procurement is not completion or accident reduction."""
from pathlib import Path
import json,hashlib,re,html,subprocess,concurrent.futures,urllib.parse
R=Path(__file__).resolve().parents[1];O=R/'data/processed/고도화검증-20260916/traffic';O.mkdir(parents=True,exist_ok=True)
S=[
('bujeon-ceremony','https://www.busan.go.kr/photobodo/1717850','2026-02-05','공식 제막식 기록'),
('bujeon-field-story','https://www.busan.go.kr/news/storyreport/view?dataNo=72395','2026-02-10','부산시보 시민리포트; 정량 효과 근거 아님'),
('bujeon-finance','https://www.busan.go.kr/ghclos202609','2025 결산/2026공시','특별조정교부금 교부 목록; 공사비 집행액 아님'),
('gwangan-procurement','https://www.busan.go.kr/nbgosi/view?sno=74101','2025-09-11','포장 공사 견적공고'),
('gwangan-contract-list','https://www.busan.go.kr/depart/abcontract?curPage=56&schCtrtkindcd=1','2025-09-22 계약 검색결과; 페이지 이동가능','계약 목록'),
('sinpyeong-design','https://www.busan.go.kr/igosi/view?sno=70441','2025-02-04','공원 실시설계 용역 입찰공고'),
('gwangan-public-proposal','https://www.busan.go.kr/yesan/spiritOffer1/1715607','2026-03-31','주민제안; 기관 사실판정·채택·시행 아님'),
('nampo-cctv','https://www.bsjunggu.go.kr/board/view.junggu?boardId=BBS_0000018&dataSid=242900&menuCd=DOM_000000103002004000','2025-03-10','기존23대 운영표; 2026 갱신실적 아님'),
('gwangan-procurement-full','https://www.busan.go.kr/nbgosi/view?curPage=50&gosiGbn=A&sno=74101','2025-09-11','공고 전체 URL 재시도'),
('sinpyeong-design-full','https://www.busan.go.kr/igosi/view?conGosiGbn=&curPage=173&gosiGbn=A&sno=70441','2025-02-04','공고 전체 URL 재시도'),
('gwangan-contract-search','https://www.busan.go.kr/depart/abcontract?schCtrtkindcd=1&schKeywordB='+urllib.parse.quote('광안역'),'2026-09-16 조회','계약명 검색'),
('gwangan-contract-detail','https://www.busan.go.kr/depart/abcontract/view?schCtrtacctbookmngno=202500115392','2026-09-16 조회','공식 계약 상세'),
]
def fetch(s):
 key,url,date,kind=s;p=O/(key+'.html')
 try:
  if not p.exists():p.write_bytes(subprocess.run(['curl.exe','--fail','--location','--max-time','35','-A','Mozilla/5.0','-e','https://www.busan.go.kr/',url],check=True,capture_output=True).stdout)
  b=p.read_bytes();t=b.decode('utf-8',errors='replace');t=re.sub(r'<(script|style)\b[^>]*>.*?</\1>','',t,flags=re.S|re.I);t=html.unescape(re.sub('<[^>]+>','\n',t));t='\n'.join(x.strip() for x in t.splitlines() if x.strip());(O/(key+'.txt')).write_text(t,encoding='utf-8')
  return {'id':key,'url':url,'referenceDate':date,'sourceClass':kind,'accessed':'2026-09-16','status':'error-page' if '요청하신 페이지를 찾을 수 없거나 오류' in t else 'saved','file':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 except Exception as e:return {'id':key,'url':url,'referenceDate':date,'status':'failed','error':str(e),'accessed':'2026-09-16'}
def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:manifest=list(ex.map(fetch,S))
 (O/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 analyze(manifest)
 print(json.dumps([{k:v for k,v in x.items() if k not in ['url','file']} for x in manifest],ensure_ascii=False))

def analyze(manifest):
 get=lambda k:(O/(k+'.txt')).read_text(encoding='utf-8')
 by={r['id']:r for r in manifest};checks=[]
 for key,words in [('bujeon-ceremony',['2026-02-05','부전역 맞이길 조성사업 제막식']),('bujeon-finance',['25-3-31','25-12-10','1,257','220','부전역(고속철도) 맞이길 조성사업']),('gwangan-contract-detail',['2025-09-22','2025-11-12','20251107','48,520,000원','준공금']),('sinpyeong-design-full',['2025.02.04','100,000,000','실시설계']),('gwangan-public-proposal',['2026-03-31','광안역']),('nampo-cctv',['남포사거리','11:30~14:00','09:00~21:00'])]:
  checks.append({'name':key+' primary text','passed':all(w in get(key) for w in words)})
 facts=[
 {'id':'bujeon-2026','district':'부산진구','rawDongBackground':'부전동','place':'부전역 앞 맞이길','sourceIds':['bujeon-ceremony','bujeon-finance','bujeon-field-story'],'status':'제막식 실시 확인; 정량 효과 자료 미확보','finding':'부산시가 2026-02-05 부전역 맞이길 제막식을 기록했다. 2025 결산 교부목록에는 3/31 1,257백만원과12/10 220백만원이 별도 기재된다. 시민리포트는 정비된 접근환경을 서술한다.','comparison':'2024 BDI가 중앙대로783번길 등 접근도로를 문제구간 배경으로 다뤘어도2026 시설·운영을 그대로 미개선이라 할 수 없다.','same2023InspectionItemConfirmed':False,'sameBdiSurveySegmentConfirmed':False,'limit':'제막식·교부금은 모든 사업항목의 검수·시공범위·접근성 효과를 대신하지 않는다. 시민리포트의 주관적 평가는 공식 효과측정이 아니다.','candidate':'새 시설 설치보다 기존 맞이길의 도면·구간과 BDI 조사구간을 대조하고 현행 보행 안내에 이미 변경된 접근 환경을 반영하는 사례로 선정 가능.'},
 {'id':'gwangan-2025-payment','district':'수영구','rawDongBackground':'광안동','place':'수영로 광안역 일원','sourceIds':['gwangan-contract-detail','gwangan-procurement-full'],'status':'검사 및 준공금 지급 확인','finding':'2025-09-22 계약,2025-09-23 착공. 11/07 검사,11/12 준공금48,520,000원 지급. 최초49,625,750원에서 보험료 등 정산으로1,105,750원 감소.','comparison':'단순 입찰계획을 넘어 검사·준공금 단계가 확인된다. 그러나 수영로 포장과 주변 내부도로의 보차분리 문제는 동일 사업이 아니다.','same2023InspectionItemConfirmed':False,'sameBdiSurveySegmentConfirmed':False,'limit':'준공예정일10/20을 실제 준공일로 쓰지 않는다. 공고 A3,672㎡·L3805m·B9.6~9.8m는 기하상 정합하지 않아 길이를 확정하지 않는다. 계약 금액을 교통안전 효과나 보차분리 해결로 환산하지 않는다.','candidate':'완료 단계의 포장사업과 남아 있을 수 있는 내부도로 보행환경을 분리하는 비교 사례. 현재 미해결 보차분리 개소 수는 미확정.'},
 {'id':'sinpyeong-design','district':'사하구','rawDongBackground':'신평동','place':'신평역 광장','sourceIds':['sinpyeong-design-full'],'status':'실시설계 용역 입찰 확인','finding':'2025-02-04 공원조성 실시설계 공고의 기초금액은1억원이며 현황측량·설계·경관조감도가 대상이다.','comparison':'연구 당시 현장환경에 후속계획이 없었다는 주장을 반박하는 자료이나 공원 준공이나 외부도로 신호개선 실적은 아니다.','same2023InspectionItemConfirmed':False,'sameBdiSurveySegmentConfirmed':False,'limit':'공원 설계와 BDI 신평역 보행구간의 동일성을 확인하지 못했다.','candidate':'주 검토 후보 보류. 실시설계 도면·발주후 계약·실제 준공을 확보하기 전 공원 설치를 신규안으로 제안하지 않는다.'},
 {'id':'nampo-operating','district':'중구','rawDongBackground':'남포동5가','place':'남포사거리','sourceIds':['nampo-cctv'],'status':'기존2025 운영표 재확인','finding':'2025-03-10 자동CCTV 운영표에 남포사거리가 포함되며09~21시,11:30~14시 유예를 표기한다.','comparison':'기존 후속조사의 별도2025-11-12 게시물(dataSid250400)보다 이른 별도3/10게시물(dataSid242900)이다. 운영시간은 일치하며 최신표를 대체하지 않는다. 2026실적·2023점검 이행을 새로 증명하지 못했다.','same2023InspectionItemConfirmed':False,'sameBdiSurveySegmentConfirmed':False,'limit':'하단 웹사이트 수정일2026-09-08은 해당 운영표 작성일이 아니다. 주정차 단속 유예를 긴급구조 공백으로 해석하지 않는다.','candidate':'2026 실운영·현장조치 증거가 없어 신규 운영변경 제안 보류.'},
 {'id':'gwangan-citizen-proposal','district':'수영구','rawDongBackground':'광안동','place':'광안역 출구 안내','sourceIds':['gwangan-public-proposal'],'status':'주민제안 기록; 제안내용의 사실 미검증','finding':'2026-03-31 주민이 광안역 인근 바닥형 안내표식을 제안했다.','comparison':'공식 플랫폼 게시라는 이유로 수요규모·안내불편의 객관적 입증·사업채택으로 취급하지 않는다.','same2023InspectionItemConfirmed':False,'sameBdiSurveySegmentConfirmed':False,'limit':'주관적 주민제안과 기관의 현장검증은 별개.','candidate':'해결안 근거로 채택하지 않음. 이용자 안내 오류의 별도 검증이 먼저 필요.'},
 ]
 (O/'traffic-resolution.json').write_text(json.dumps({'accessed':'2026-09-16','facts':facts,'primaryCases':['bujeon-2026','gwangan-2025-payment'],'unresolved':['거제천로 펜스3740만원 위원회 삭감 후 최종 본회의 의결·집행','못골시장 효과평가 보고서 결론 원문; 기존계약준공은 유지','2023점검14곳의 항목별 현재상태·정확한 시공구간']},ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'author-checks.json').write_text(json.dumps({'passed':sum(c['passed'] for c in checks),'checks':checks,'independent':False},ensure_ascii=False,indent=2),encoding='utf-8');assert all(c['passed'] for c in checks)
 queries=['site.yeonje.go.kr 거제천로 펜스2025','site.bsjunggu.go.kr 남포사거리2026','site.bsnamgu.go.kr 못골시장 효과평가','site.busanjin.go.kr 부전시장 보행2025','거제천로3740 예산결산','거제천로 펜스2025','신평역 보행환경2025 2026','광안역 보행 준공','연제구255회12월19일2024','거제천로 펜스2026','부전역 맞이길 준공 site:busanjin.go.kr','호암로4.5 site:go.kr','부전시장 노점 site:go.kr2025','거제천로 펜스 예산결산특별','못골시장 효과평가2026','부전시장 정비 부산진구2025 2026','신평역 공원 준공2026','광안역 포장보수공사 계약','거제천로 무단횡단','부전역 맞이길 site:go.kr','도로관리 종합정비의날 site:go.kr','신평역 개방형 site:busan.go.kr','장대골삼거리 개선2025 2026','남항시장사거리 정비2025 2026','반송도서관교차로 개선2025']
 (O/'search-attempts.json').write_text(json.dumps({'searched':'2026-09-16','queries':queries,'failedPaths':['부산공고 sno만 전달시HTTP200 오류문서; 전체검색URL로재시도성공','최초curl UserAgent없음401;Mozilla와공식Referer로성공','계약목록56페이지는색인당시와현재다름;계약명검색으로상세ID확보'],'notAdopted':['언론의 호암로4.5톤 제한·부전역80건정비는현재공식원문미확보로채택안함','거제예산최종의결 미확보','못골평가결론원문 미확보'],'conclusion':'이번 검색 미확보는 기관의 미조치·문서 부재를 입증하지 않음.'},ensure_ascii=False,indent=2),encoding='utf-8')
 md='# 교통 후속 근거: 현재 미개선 주장을 다시 검토\n\n기준일2026-09-16. 실제 신고 지점·과거 현장조사·현재 공사는 서로 다른 공간 단위다.\n\n'
 for f in facts:
  md+='## '+f['place']+'\n\n'+f['status']+' — '+f['finding']+'\n\n'+f['comparison']+'\n\n'+f['limit']+'\n\n선정 판단: '+f['candidate']+'\n\n'+' · '.join('['+k+']('+by[k]['url']+')' for k in f['sourceIds'])+'\n\n'
 md+='## 결론\n\n부전과 광안의 후속 변화를 최종 사례의 반대 근거로 우선 채택할 수 있다. 교통14지점의 현재 미해결을 새로 확정한 사례는 없다. 거제는 기존 위원회 심사까지만 유지하고 못골은 기존 준공·평가계약을 유지한다. 기관의 현행 유지관리·완료사업을 모른 채 신규 시설을 일괄 권고하지 않는 것이 이번 후속자료의 판단 변화다.\n\n재현: `.venv-check/Scripts/python.exe scripts/collect_traffic_resolution_20260916.py`. 원문·오류문서·검색기록·SHA256은 이 폴더에 보존. 공개 결과에는 업체 대표자·주소를 재게시하지 않는다.\n'
 (O/'교통-현재조치-선정판단.md').write_text(md,encoding='utf-8')
if __name__=='__main__':main()
