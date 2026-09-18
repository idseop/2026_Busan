"""Build immutable reviewed 2026-09-17 analysis/map packages."""
from pathlib import Path
import json,hashlib,shutil
from package_complete_delivery_20260916 import make_zip,standalone_html
R=Path(__file__).resolve().parents[1];N=R/'data/processed/지도입증확장-20260916';W=R/'web/final';P=W/'results/complete';O=R/'output'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=R/'docs/40-분석결과/부산-119-지도와입증-통합보고서-20260917.md'
def main():
 records=[];reviewed={};superseded=[]
 for name in ['profiles-independent','effect-protocol-independent','map-independent','regional-ui-independent','report-browser-independent','report-independent','navigation-independent','final-delta-independent','drilldown-independent']:
  p=N/'verification'/f'{name}.json';j=read(p);assert j['status'].lower()=='pass',(name,j['status'])
  for rel,digest in j.get('hashes',{}).items():
   rel=Path(rel).as_posix()
   if rel in reviewed and reviewed[rel]['sha256']!=digest:
    superseded.append({'path':rel,'previousReview':reviewed[rel]['record'],'currentReview':name})
   reviewed[rel]={'sha256':digest,'record':name}
  records.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p)})
 # Prior immutable reviews remain evidence for unchanged functions. Every changed
 # digest needs a later independent review of that exact file, not a hash refresh.
 for rel,evidence in reviewed.items():
  f=R/rel;assert f.exists() and sha(f)==evidence['sha256'],('review hash changed',rel,evidence['record'])
 assert read(N/'benchmark/results.json')['status']=='PASS'
 assert len(read(P/'figure-catalogue.json'))==48 and len(read(P/'table-catalogue.json'))==73
 common={'전체결과보고서.md':report.read_bytes(),'부산 분석 작업 계획.md':(R/'docs/10-작업계획/부산 분석 작업 계획.md').read_bytes(),'효과검증-사전계획.md':(R/'docs/10-작업계획/지도와효과-확장검증계획-20260916.md').read_bytes(),'requirements-final-delivery.txt':(R/'requirements-final-delivery.txt').read_bytes()}
 for folder in [R/'analysis/00_공통',R/'scripts']:
  for p in folder.iterdir():
   if p.is_file() and p.suffix in {'.py','.js','.cjs','.ps1','.txt'}:common['재현코드/'+p.relative_to(R).as_posix()]=p.read_bytes()
 for root,label in [(R/'data/processed/통합완성-20260916','이전통합근거'),(N,'새분석검증')]:
  for p in root.rglob('*'):
   if any(x in p.parts for x in ['baseline','package-check','previous-final-pages']):continue
   if p.is_file() and p.suffix in {'.json','.md','.py'} and not p.name.startswith('package-independent'):
    common[label+'/'+p.relative_to(root).as_posix()]=p.read_bytes()
 for rel in ['map/commerce-3d-1600.png','map/sea-3d-1600.png','map/mountain-2d-1600.png','map/focus-background-3d-1600.png','verification/sequential-1600-step1.png','verification/sequential-1600-step2.png','verification/sequential-1600-step3.png','verification/sequential-1600-step4.png','verification/report-independent-pc1366.png']:
  p=N/rel;common['대표화면/'+p.name]=p.read_bytes()
 for p in (N/'delivery-screens').glob('*.png'):common['대표화면/'+p.name]=p.read_bytes()
 web=dict(common)
 for p in W.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.zip','.pyc'}:web[p.relative_to(W).as_posix()]=p.read_bytes()
 web['결과보기.html']=b'<!doctype html><html lang="ko"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=results/complete/index.html"><a href="results/complete/index.html">Open results</a></html>'
 web['실행방법.txt']='''부산 119 지역별 결과·2D/3D 지도 (2026-09-17)

ZIP을 완전히 풀고 Python 3이 설치된 PC에서 실행.cmd를 실행하세요.
또는 해당 폴더에서 python serve.py
지도: http://127.0.0.1:8765/
통합 결과: http://127.0.0.1:8765/results/complete/
포트 충돌 시 python serve.py --port 8766

2D 기본 → 지역 선택 → 3D/회전/북쪽/확대.
높이가 기재된 건물은 확대 수준13 이상에서 입체로 보입니다. 전체 건물의 높이를 제공하는 자료는 아닙니다.
지역 결과 탭: 194개 지역명·5유형의 5년 심층 기준, 주민/생활/주택/상권,9사례 대응·보완·출처.
신고 특징 → 주민·지역 배경 → 기존 대응 → 보완 결과의 네 단계와 이전·다음으로 읽습니다.
배경 위치 보기: 선택한 주민 후보의 공식 대표 위치이며 실제 신고 위치가 아닙니다.
지도 연도·처리조건과 별도 기준인 곳은 해당 숫자 옆에 표시합니다.

전체48시각화·73집계표·23절 단일보고서·상세계획·코드·독립검증 포함.
결과·그림·표·지역 상세는 파일 직접 열기도 됩니다. 배경 타일과 공식 출처는 인터넷 필요.
실시간 사고나 개인 이동을 표시하지 않으며, OSM 높이는 독립 실측 값이 아닙니다.
개별 신고번호·정밀 신고좌표는 배포하지 않습니다. 건물 윤곽/높이는 공개 OSM 배경자료입니다.
전체 원자료 재분석에는 원프로젝트 입력과 폴더 구조가 필요합니다.
'''.encode('utf8')
 analysis=dict(common)
 for p in P.rglob('*'):
  if p.is_file():
   rel=p.relative_to(P).as_posix();blob=p.read_bytes()
   if p.suffix=='.html' and '/' not in rel:
    text=standalone_html(blob).decode('utf8').replace('report.html#part-12','report.html#part-19').replace('>부산 2D·3D 지도 열기 →<','>지도 기능·실행 안내 →<');blob=text.encode('utf8')
   analysis[rel]=blob
 analysis['읽는방법.txt']='''부산 119 전체 분석·시각화 (2026-09-17)

압축을 완전히 풀고 index.html을 여세요. 인터넷·Python 없이 결과를 읽을 수 있습니다.
gallery.html: 전체48그림 PNG/SVG, 확대·분류·저장
data.html: 73개 전체CSV와 미리보기
report.html 또는 전체결과보고서.md: 목적·배경·모든자료·지역사례·시간검증·효과입증범위·3D·검증
부산 분석 작업 계획.md / 효과검증-사전계획.md: 기준과 현재 판단
재현코드/ / 새분석검증/ / 이전통합근거/: 코드·해시·출처·작성자와 독립검증

지도 조작과194지역 필터는 별도의 2D3D지도웹 ZIP에서 실행합니다.
이 ZIP의 지도/지역 이동 안내는 보고서의 해당 설명으로 연결됩니다.
시민 효과나 피해 감소를 실제 측정한 결과는 아닙니다. 분석·정확성·화면 기능 결과를 구분합니다.
'''.encode('utf8')
 packages=[make_zip('부산119-전체분석-시각화-20260917.zip',analysis),make_zip('부산119-2D3D지도웹-20260917.zip',web)]
 dest=O/'부산119-전체결과보고서-20260917.md';shutil.copy2(report,dest)
 result={'packages':packages,'report':{'path':dest.relative_to(R).as_posix(),'sha256':sha(dest)},'reviewRecords':records,'supersededFileReviews':superseded,'figures':48,'tables':73,'regions':194,'knownHeightBuildings':1081,'implemented3D':True,'measuredHumanOrSafetyEffect':False}
 (O/'부산119-지도입증확장-배포기록-20260917.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
