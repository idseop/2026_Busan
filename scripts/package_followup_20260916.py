"""Connect and package the verified follow-up, preserving earlier results."""
from pathlib import Path
import json, hashlib, shutil, zipfile
R=Path(__file__).resolve().parents[1]
O=R/'output/부산119-전지역후속검증-20260916'
W=R/'web/final'
V=R/'data/processed/후속입증-20260916/verification'
p=W/'index.html'
s=p.read_text(encoding='utf-8').replace('href="results/deepening/index.html">동별 심화 결과','href="results/followup/index.html">후속검증 결과')
p.write_text(s,encoding='utf-8')
plan=R/'docs/10-작업계획/부산 분석 작업 계획.md'
s=plan.read_text(encoding='utf-8')
marker='## 2026-09-16 전 지역 후속검증과 보조자료 확장'
if marker not in s:
 s+='''
## 2026-09-16 전 지역 후속검증과 보조자료 확장

상권을 유일한 설명 변수로 삼지 않는다. 신고의 반복·시간 특성에 따라 보행환경, 주택 유형·건축시기, 생활인구, 장비 이용조건, 점검·시정, 산악·해변 정비와 사업 후속 상태를 각각 대조한다.

- 검증된 2020–2024 신고 704,689건을 유지하며 194개 신고 지역명×5유형×3처리조건 2,910개 집계와 시간 교차표를 추가했다. 194개 신고 지역명을 205개 행정동과 동일시하지 않는다.
- 2023 공식 교통 점검 14곳 전부의 후속 근거를 검색했다. 부전·광안·신평 등 추가 지역을 현장연구·운영근거로 심층 검토하고, 과거 개선항목 수를 현재 미해결 건수로 바꾸지 않는다.
- 최신 소방 조사 132행의 판정·시정 기재, AED 정보 불일치와 기존 지원, 주택통계 2024 및 2025 경계기준, 생활인구 2024의 205동 시간·연령 배경을 별도로 분석했다.
- 생활인구는 월별 일평균의 12개 기준월 동일가중 평균이며 신고율 분모·연간 실인원이 아니다. 복수 행정동 후보를 합산하지 않는다.
- 상권은 2024년 9월 말 4개 동 업종 구성과 같은 해 분기 민감도에 사용했다. 건축행정 등 보유 자료도 점검했지만 현재 질문에 맞지 않는 결합은 수행하지 않는다. 채택·불채택 이유를 별도 문서에 기록했다.
- 사업 완료·현지시정·기존 대여·폐장 후 대응의 반대 근거를 반영한다. 웹의 차별점은 신고·현장·운영·조치의 시점과 근거를 함께 보여주는 것이며, 기존 행정의 부재나 예방효과를 주장하지 않는다.

최신 결과: `../40-분석결과/부산-119-전지역후속검증-20260916.md`

자료 선택: `../40-분석결과/부산-119-보조자료선택판단-20260916.md`

코드·검증: `data/processed/후속입증-20260916/`, `analysis/00_공통/analyze_busan_followup_20260916.py` 및 각 보조자료 코드.

결과 웹: `web/final/results/followup/index.html`, 지역 탐색: `explorer.html`.
'''
 plan.write_text(s,encoding='utf-8')
for p in V.glob('*'):
 if p.is_file() and p.suffix in ['.json','.md','.png','.py']:
  dest=O/'verification'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
for p in O.rglob('*'):
 if p.is_file():
  dest=W/'results/followup'/p.relative_to(O);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
records=[]
for source,name in [(O,'부산119-전지역후속검증-20260916.zip'),(W,'부산119-지도와전지역분석-20260916.zip')]:
 target=R/'output'/name
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in source.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.zip']:
    z.write(p,p.relative_to(source))
 with zipfile.ZipFile(target) as z:
  assert z.testzip() is None
  count=len(z.namelist())
 records.append({'file':str(target.relative_to(R)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'entries':count,'crcPassed':True})
(R/'output/부산119-전지역후속검증-배포기록.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(records,ensure_ascii=False))
