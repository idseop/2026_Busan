"""Prepare final current plan, reproducibility guide and two review-gated packages."""
from pathlib import Path
import json,hashlib,shutil,zipfile,sys,importlib.metadata
R=Path(__file__).resolve().parents[1];N=R/'data/processed/최종마감-20260916';W=R/'web/final';F=W/'results/final'
D=R/'output/부산119-최종완성본-20260916';V=R/'output/부산119-최종시각화-20260916'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=R/'docs/40-분석결과/부산-119-최종통합보고서-20260916.md'

def prepare():
    plan=R/'docs/10-작업계획/부산 분석 작업 계획.md'
    old=plan.with_name('부산 분석 작업 계획-20260916-마감전.md')
    if not old.exists():shutil.copy2(plan,old)
    plan.write_text('''# 부산 분석 작업 계획 — 최종 결과 기준

최종 정리: 2026-09-16. 단계별 판단 이력은 [마감 전 계획](부산 분석 작업 계획-20260916-마감전.md)에 보존한다. 현재 결론은 [최종 통합 보고서](../40-분석결과/부산-119-최종통합보고서-20260916.md)를 따른다.

## 목표와 유지한 흐름

부산 전체 신고 특성 → 지역별 신고와 주민 연령 구성 → 집중 검토 대상 → 필요한 현장 자료 → 기존 대응 비교 → 근거에 맞는 예방·지원 보완 → 독립 시각화 → 결과 웹.

건수가 많은 곳을 위험 순위로 만들지 않는다. 시설·인력·순찰·돌봄을 먼저 정하지 않는다. 벌집제거는 전체 검산에만 보존하고 심층 검토와 제안에서 제외한다.

## 입력과 포함 조건

- 신고: `data/raw/119접수/`의 2020–2024년 CSV 5개.
- 주민 배경: `data/raw/인구배경/`의 같은 5개년 12월 말 읍면동 연령 인구. 205개 읍면동을 사용하고 시·구군 합계를 중복 합산하지 않는다.
- 컬럼 정의: `data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx`.
- 공식 보완자료: 질문에 필요한 통계·교육·AED·주택·생활인구·상권·현장 조사·정비와 평가 자료. 각각 적용 기간·공간 단위·출처를 유지한다.

선택한 17개 신고 컬럼 중 하나라도 결측이면 해당 행을 제외한다. 원본은 수정하지 않고 전처리·제외·미연결 기록을 분리한다. 같은 위치·시간만으로 중복 제거하지 않는다.

| 조건 | 현재 신고접수 |
|---|---:|
| A: 17개 컬럼 모두 기재 | 704,689건 |
| B: A 중 정상 처리 | 579,412건 |
| C: B 중 업무운행·훈련출동·구급차소독 제외 | 574,662건 |
| C 중 심층 5유형 | 41,720건 |

완전한 행이라는 이유로 부산 전체 대표성을 인정하지 않는다. 일반전화 등 제외와 이동전화 내부 잔존율 차이는 별도 비교집합으로 진단했다. 비교집합을 현재 신고 집합에 섞지 않는다.

## 완료한 분석과 현재 판단

1. 전체 신고의 연도·유형·시간·처리조건을 비교했다. 194개 신고 지역명×5유형의 970개 조합을 A/B/C별 2,910개 집계로 제공한다.
2. 세 조건에서 결측 제외 전후 5년 반복·증감 방향이 유지되는 325개를 확인했다. 대표성이나 모든 시간 양상의 안정성을 뜻하지 않는다.
3. 970개 조합에서 전체 기간·각 연도·한 해 제외의 11개 기간을 비교했다. 325개 중 최고월 유지 33개, 최고계절 유지 121개다. 임의 점수·유의성·예측 성능으로 바꾸지 않는다.
4. 연산동 심정지·부전동 구급 교통사고는 기존 대응을 깊게 연결한 설명 사례다. 광안동은 처리조건 민감성이 있는 별도 비교 사례다. 주택·산악·수난을 포함한 9개 최종 설명 사례를 유지한다.
5. 주민은 같은 연도 말 전체 연령 인원·비중을 각각 제공한다. 복수 행정동 후보를 합산하지 않고, 연산3동·부전2동의 인원과 비중 방향 차이를 별도 그림으로 설명한다.
6. 공식 CPR 환자 통계와 2024년 3개 구 주민 교육·실습 조사 99개 집계행을 추가했다. 환자·신고·주민 표본·행정동 인구를 구분하고 인과관계나 미충족 수요로 전환하지 않는다.
7. 부전 설계, 광안 포장 검사·지급, 못골 효과평가 수행, 산악 정비와 해변 관리 등 이미 이뤄진 대응을 반영했다. 조사선·준공선이 같은지 미확정이면 해당 개선효과를 확정하지 않는다.
8. 일반 비고 공란 13행을 미조치 시설 13곳으로 해석하지 않도록 교정했다. 실제 조치명령·이행 이력은 별도 근거가 필요하다.

## 최종 서비스와 시각화

- `web/final/results/final/index.html`: 최종 핵심 결론·9개 사례·보완 범위.
- `web/final/index.html`: 부산 지도·검색·연도·종별·처리조건. 검증된 사례를 정확한 동·유형의 심층 결과로 연결한다.
- `web/final/results/followup/explorer.html`: 전 지역 상세, 시간과 선택 영향, 주민 후보, 서비스 이용조건.
- `web/final/results/final/gallery.html`: 핵심 13종 PNG·SVG, 결론·단위·기간·출처, 키보드 확대·저장.
- `web/final/results/final/report.html`: 통합 MD의 웹 보기·다운로드·인쇄.
- `web/final/results/effects/index.html`: 새 공식 통계·시기 분석·사업 내역의 상세 근거.

지도는 검증된 구·군 집계를 사용한다. 동 위치가 미확정이면 소속 구·군을 강조한다. 상세한 배경지도를 신고 위치의 정확도로 오해시키거나 미연결을 0건으로 표시하지 않는다. 고정 5년 C조건 심층 결과는 지도 필터와 다른 기준임을 링크 옆에 표시한다.

## 채택한 방법과 검증

기술통계, 달력 일수당 비교, 처리조건·결측 제외·기간 민감도, 조건부 주민 비교와 공식 대응 대조를 사용한다. LISA·스캔·LCLQ·입지·예측은 현재 판단에 필요하지 않아 실행하지 않았다.

기존 검증은 현재 파일 해시와 대조해 재사용했다. 새 설명 그림은 검증된 원 집계와 별도 대조한다. 분석 작성과 내용·브라우저·배포 검증을 분리하고, PC 1920×1080·1600×900·1366×768에서 지도 선택·필터·수치·키보드·빈 결과·파일 직접 실행을 확인한다.

## 현재 보완 범위와 후속 측정

구현 결과는 지역 근거와 서비스 이용조건·사업 상태의 연결이다. 직접 기대효과는 올바른 경로 선택과 과거·현재 상태의 혼동 감소이며, 동일 과제의 정확도·시간·오선택률로 측정하도록 명세했다. 실제 참여·술기 향상·사고·피해 감소는 미측정이다.

후속 판단에는 검증된 발생 주소·당시 경계, 비식별 교육 신청·참여·거절 기록, 등록ID별 AED 접근·점검 이력, BDI 조사선·최종 준공도면·평가 본문, 실제 조치명령과 이행 자료가 필요하다. 공개 검색에서 미확보한 사실을 기관의 미대응으로 바꾸지 않는다.

## 재현과 전달

최종 마감 기록: `data/processed/최종마감-20260916/`. 이전 분석 입력과 코드는 해당 manifest를 유지한다.

표현·연결의 재현: `plot_final_story_20260916.py` → `build_followup_explorer_20260916.py` → `connect_final_navigation_20260916.py` → `build_final_delivery_20260916.py` → 독립 내용·PC 검증 → `package_final_completion_20260916.py --package`.

실행 환경은 `requirements-final-delivery.txt`와 마감 기록의 environment.json에 기록한다. 웹 ZIP과 시각화 ZIP은 원신고·시설 원명부·대용량 CHS 원본을 제외한 집계·결과 전달물이다. 실제 배포 명세와 독립 검사 기록을 함께 제공한다.
''',encoding='utf-8')
    env={'python':sys.version,'packages':{p:importlib.metadata.version(p) for p in ['pandas','numpy','matplotlib','openpyxl','xlrd','PyMuPDF','olefile','mistune','playwright']},'platform':'Windows / Malgun Gothic / locally installed Chrome','purpose':'Recorded working analysis and final rendering environment; web viewers need no Python except local map server'}
    (N/'environment.json').write_text(json.dumps(env,ensure_ascii=False,indent=2),encoding='utf-8')
    (R/'requirements-final-delivery.txt').write_text('# Verified environment for final rendering and browser checks.\n'+'\n'.join(f'{k}=={v}' for k,v in env['packages'].items())+'\n',encoding='utf-8')
    catalogue=read(F/'visual-catalogue.json')
    artifact='''# 최종 전달물과 사용 순서

이 자료의 중심 질문은 부산의 반복 신고를 주민·현장 배경과 기존 대응에 연결할 때 어떤 예방·지원 정보를 구체화할 수 있는가이다.

## 권장 읽기 순서

1. 최종 결과 페이지: 배경·핵심 결론·9개 사례·보완 범위.
2. 부산 지도와 지역 상세: 지역을 선택하고 신고·주민·기존 대응을 확인.
3. 시각화 모음: 발표·공유에 필요한 PNG/SVG와 해석.
4. 최종 통합 보고서: 선정 기준·자료·공백·차별점·효과와 미확정 사항.

## 시각화별 핵심 내용

| 번호 | 그림 | 전달하는 결과 | 기간·단위 |
|---|---|---|---|
'''
    for v in catalogue:artifact+=f"| {v['number']:02d} | {v['title']} | {v['coreFinding']} | {v['period']} · {v['unit']} |\n"
    artifact+='''
## 실제 구현 개선

- 최종 결과·부산 지도·지역 상세·시각화·MD를 같은 탐색 흐름에 연결했다.
- 지도에서 9개 설명 사례를 선택하면 해당 동·유형의 고정 5년 C조건 결과로 이동한다. 지도 연도 필터와 혼동하지 않도록 조건을 바로 옆에 적었다.
- 사례는 유형별, 시각화는 목적별로 골라 볼 수 있다. 그림 확대는 Enter·Esc와 초점 복귀를 지원한다.
- MD를 HTML로 읽고 원본 저장·인쇄할 수 있다. 기술적 검증은 별도 페이지로 분리했다.
- 모든 수치가 나온 기간·분모를 유지하고, 소속 구·군만 확정된 동을 가짜 위치에 배정하지 않는다.

기존 신고 집계는 바꾸지 않았다. 새로운 통계 효과를 계산한 것이 아니라 이미 검증한 결과의 전달과 탐색을 완성한 단계다. 기대효과는 정확한 서비스 선택·사업 상태 이해이며 사용자 실험·교육 참여·피해 감소는 아직 측정하지 않았다.
'''
    (R/'docs/40-분석결과/부산-119-최종전달물-안내-20260916.md').write_text(artifact,encoding='utf-8')
    (N/'deliverable-guide.md').write_text(artifact,encoding='utf-8')

def createzip(folder):
    manifest=[{'path':p.relative_to(folder).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='배포명세.json']
    (folder/'배포명세.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    zpath=folder.with_suffix('.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in folder.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(folder))
    with zipfile.ZipFile(zpath) as z:assert z.testzip() is None;count=len(z.namelist())
    return {'path':str(zpath.relative_to(R)),'sha256':sha(zpath),'bytes':zpath.stat().st_size,'entries':count,'crcPassed':True}

def package():
    for name in ['content-final.json','browser-final.json','visual-final.json']:
        result=read(N/'verification'/name);assert str(result['status']).lower()=='pass',name
        for rel,expected in result.get('hashes',{}).items():
            p=R/rel
            if p.is_file():assert sha(p)==expected,('changed after verification',rel)
    prepare()
    D.mkdir(parents=True,exist_ok=True);V.mkdir(parents=True,exist_ok=True)
    shutil.copytree(W,D,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.zip'))
    (D/'결과보기.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=results/final/index.html"><title>부산 신고 분석 최종 결과</title><a href="results/final/index.html">최종 결과 열기</a></html>',encoding='utf-8')
    instructions='''부산 119 최종 결과

1. ZIP을 풀고 결과보기.html을 열면 핵심 결론·시각화·통합 보고서를 볼 수 있습니다.
2. 지역별 상세도 파일 직접 실행됩니다.
3. 부산 지도 배경까지 이용하려면 배포 폴더에서 실행합니다:
   python serve.py --no-browser
   http://127.0.0.1:8765/
   최종 결과: http://127.0.0.1:8765/results/final/
   기존 서버가 있으면 같은 주소를 사용하세요. 다른 프로그램이 포트를 점유하면 --port 8766으로 바꾸세요.
4. 지도 외부 배경과 기관 링크는 인터넷이 필요합니다. 실제 신고를 수신하는 실시간 서비스는 아닙니다.

포함물: 실행 가능한 웹, 핵심 13종 PNG/SVG, 통합 MD, 출처·검증, 이번 변경 재현코드.
원신고·정밀 신고 위치·시설 원명부·대용량 원 PDF/ZIP은 포함하지 않았습니다.
재현코드는 원 프로젝트의 검증된 입력·기존 집계가 필요합니다. requirements-final-delivery.txt는 사용한 환경 기록입니다.
원본 재분석은 각 분석manifest의 코드와 입력을 따릅니다. 이번 마감은 기존 집계를 바꾸지 않았습니다.
'''
    (D/'실행방법.txt').write_text(instructions,encoding='utf-8')
    for p in [report,R/'docs/40-분석결과/부산-119-최종전달물-안내-20260916.md',R/'docs/10-작업계획/부산 분석 작업 계획.md',R/'docs/10-작업계획/부산 분석 작업 계획-20260916-마감전.md',R/'requirements-final-delivery.txt']:
        shutil.copy2(p,D/p.name)
    packaged_plan=D/'부산 분석 작업 계획.md'
    packaged_plan.write_text(packaged_plan.read_text(encoding='utf-8').replace('../40-분석결과/',''),encoding='utf-8')
    # Preserve relative links from the MD download.
    for p in (F/'references').glob('*.md'):shutil.copy2(p,D/p.name)
    codes=['scripts/build_final_delivery_20260916.py','scripts/plot_final_story_20260916.py','scripts/build_followup_explorer_20260916.py','scripts/connect_final_navigation_20260916.py','scripts/verify_final_figures_20260916.py','scripts/package_final_completion_20260916.py']
    for rel in codes:
        dest=D/'재현코드'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/rel,dest)
    for p in N.rglob('*'):
        if p.is_file() and p.suffix in ['.json','.md','.py','.png','.svg']:
            dest=D/'마감기록'/p.relative_to(N);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(N/'deliverable-guide.md',V/'시각화-읽는방법.md')
    shutil.copy2(F/'visual-catalogue.json',V/'시각화-출처명세.json')
    figures=read(F/'visual-catalogue.json');cards=[]
    for item in figures:
        for rel in [item['publicPath'],*item['alternativePaths']]:
            p=F/rel;dest=V/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        name=item['publicPath']
        cards.append(f'<figure><h2>{item["number"]:02d}. {item["title"]}</h2><a href="{name}"><img src="{name}" alt="{item["title"]}"></a><figcaption>{item["coreFinding"]}<br>{item["period"]} · {item["unit"]}<br>{item["source"]}</figcaption></figure>')
    (V/'그림모음.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>부산 119 최종 시각화</title><style>body{max-width:1150px;margin:35px auto;padding:0 25px;color:#173c48;font:17px/1.8 "Malgun Gothic",sans-serif}figure{margin:25px 0 55px}img{width:100%;height:auto}figcaption{font-size:15px}a{color:#0b7480}</style><h1>부산 119 · 최종 시각화 13종</h1><p>그림의 기간·단위·해석을 함께 사용하세요. PNG·SVG 원본과 출처 명세를 포함합니다.</p>'+''.join(cards)+'</html>',encoding='utf-8')
    records=[createzip(D),createzip(V)]
    (R/'output/부산119-최종완성본-배포기록.json').write_text(json.dumps({'packages':records,'includesPrivateIncidents':False,'includesLargeOriginalDocuments':False},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(records,ensure_ascii=False))

if __name__=='__main__':
    if '--package' in sys.argv:package()
    else:prepare();print('Current plan, environment and deliverable guide updated.')
