from pathlib import Path
import shutil,json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/부산119-동별보완-심화결과-20260916'
V=ROOT/'data/processed/동별보완-추가근거-20260916/verification'
result=json.loads((V/'additional-evidence-verification.json').read_text(encoding='utf-8'))
browser=json.loads((V/'deepening-browser.json').read_text(encoding='utf-8'))
assert result['status']=='passed' and not browser['errors']
instructions='''부산119 동별 보완 심화 결과

1. 이 폴더의 index.html을 PC Chrome에서 열면 추가 분석과 그림을 볼 수 있습니다.
2. 그림은 PNG 및 SVG이며, 표는 CSV로 제공됩니다. 인터넷 없이 열 수 있습니다.
3. 공식 출처 링크를 여는 경우 인터넷이 필요합니다.
4. 전체 지도 웹 ZIP은 별도 제공됩니다. 압축 해제 후 Python이 있으면
   python serve.py --no-browser
   를 실행하고 http://127.0.0.1:8765/results/deepening/ 으로 접속하세요.
5. 신고 분석 기간은 2020–2024이며 보완자료는 각 자료연도·기준일이 다릅니다.
6. 신고·인구 기초 분석은 전체 웹 ZIP의 results/index.html에 보존돼 있습니다.
'''
(OUT/'실행방법.txt').write_text(instructions,encoding='utf-8')
for name in ['추가근거-독립검토.md','deepening-browser.json']:
 shutil.copy2(V/name,OUT/name)
for name in ['deepening-1600.png','deepening-s3.png','deepening-s4.png','deepening-s5.png']:
 shutil.copy2(V/name,OUT/name)
record=f'''# 동별 보완 결과 전달 검증 · 2026-09-16

추가 원문 및 계산은 별도 검증자가 `{result['checksCount']:,}`개 대조를 통과시켰다. 검사 수는 정책 효과나 표본 대표성을 뜻하지 않는다.

시간표 주차 예외, 아파트 옵션 개행 누락, 대여 AED의 단위 문제를 수정했다. 신규 보고서 수치와 현재 공백·인과 과장 여부도 별도로 검토했다.

PC 1920×1080, 1600×900, 1366×768에서 그림 6개 로딩, 9개 결과 영역, 가로 넘침, 지역 사례 앵커, 로컬 파일 직접 열기, 지도에서 신규 결과 이동을 실행했다. 브라우저 오류는 없었다. 주요 캡처를 직접 확인했다.

원문에는 공개 계약 상대방 정보 등이 포함되지만 웹에는 복사하지 않았다. 공개 결과 텍스트에서 개별 접수번호·정밀 신고 좌표 필드가 없음을 확인했다.

기존 지도 필터와 집계 코드는 변경하지 않았다. 이번 지도 변경은 추가 결과 링크이며 새 신고 지도나 현재 위험 지도를 만든 것은 아니다.

현재 추가 확인 항목: 못골시장 효과평가 보고서 본문, 못골사거리 3항목별 이행 증빙, 준공 이후 넘어짐 기록, AED 실제 출입·점검, 건물별 자료 기준일. 공개 자료에서 확인되지 않은 사실을 완료로 표시하지 않았다.
'''
(ROOT/'docs/40-분석결과/부산-119-동별보완-전달검증-20260916.md').write_text(record,encoding='utf-8')
(OUT/'검증요약.md').write_text(record,encoding='utf-8')
web=ROOT/'web/final/results/deepening'
for p in OUT.iterdir():
 if p.is_file() and p.name!='manifest.json':shutil.copy2(p,web/p.name)
manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
manifest['outputs']=[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json']
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copy2(OUT/'manifest.json',web/'manifest.json')
for folder,target in [(OUT,OUT.with_suffix('.zip')),(ROOT/'web/final',ROOT/'output/부산119-지도와심화분석-20260916.zip')]:
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(folder))
 with zipfile.ZipFile(target) as z:assert z.testzip() is None
 print(str(target),target.stat().st_size)
