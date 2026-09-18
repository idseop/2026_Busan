"""Build a standalone results report from verified aggregates; never reads individual calls."""
from pathlib import Path
import json, html, shutil, hashlib, zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/예방지원-근거분석-20260916'
OUT = ROOT / 'output/부산119-예방지원-분석결과-20260916'
OUT.mkdir(parents=True, exist_ok=True)
def read(p): return json.loads(p.read_text(encoding='utf-8'))
a = read(BASE/'analysis/action-patterns.json')
r = read(BASE/'response/official-response.json')
esc = lambda s: html.escape(str(s))
sources = {s['id']:s for s in r['sources']}
directions = {s['subtype']:s for s in r['implementationDirections']}
rows, cases, mdrows = [], [], []
for p in a['profiles']:
    c=p['scopeProfiles']['C']; d=directions[p['subtype']]
    weekend=c['weekendPerObservedDay']/c['weekdayPerObservedDay'] if c['weekdayPerObservedDay'] else None
    retention=p['stability']['C']['retention']
    pop=p['populationLinks'][-1]
    poptext='주민 코드 단일 후보' if pop['uniqueCode'] else f"주민 코드 {len(pop['candidateCodes'])}개 후보 · 합산 안 함"
    name=f"{p['district']} {p['rawDong']}"
    values=[name,p['subtype'],f"{c['count']:,}",'/'.join(map(str,c['yearCounts'])),f"{weekend:.2f}배",f"{retention:.1%}"]
    rows.append('<tr>'+''.join(f'<td>{esc(x)}</td>' for x in values)+'</tr>')
    mdrows.append('| '+' | '.join(values)+' |')
    applicable_sources=[s for s in d['sourceIds'] if s!='sasang_fire_onestop' or p['district']=='사상구']
    refs=''.join(f'<li><a href="{esc(sources[s]["url"])}">{esc(sources[s]["title"])}</a><p>{esc(sources[s]["target"])} · {esc(sources[s]["hours"])}</p><p>{esc(sources[s]["conditions"])} · 기준: {esc(sources[s]["referenceDate"] or "기준일 미기재 · 2026-09-16 열람")}</p></li>' for s in applicable_sources)
    hour=max(range(24),key=lambda x:c['hourCounts24'][x])
    cases.append(f'''<article id="{esc(p['id'])}"><p class="kicker">{esc(p['subtype'])}</p><h3>{esc(name)}</h3>
    <p class="number">{c['count']:,}<small>건 · 2020–2024 정상 처리, 운영성 분류 제외</small></p>
    <p>5년 모두 접수됐습니다. 해당 지역 신고 중 구성비는 {c['regionSubtypeShare']:.1%}, 같은 유형의 나머지 부산과 비교한 주말 비중 차이는 {c['weekendShareDifferencePP']:+.1f}%p입니다.</p>
    <p>5년 합계에서 가장 많은 접수 시각은 {hour:02d}시대({c['hourCounts24'][hour]:,}건)입니다. 주말 일평균은 평일의 {weekend:.2f}배입니다. 이 시각이 매년 동일한 최댓값이었다는 뜻은 아닙니다.</p>
    <p class="meta">제외 전 비교 집합 대비 잔존율 {retention:.1%} · {esc(poptext)} · 주민 기준 2024년 말</p>
    <h4>기존 대응 비교 결과</h4><p>{esc(d['result'])}</p><ul>{refs}</ul>
    <h4>서비스에 반영할 내용</h4><p>{esc(d['webAction'])}</p>
    <p class="status">{esc(d['serviceGapStatus'])}. 현재 자료로 시설·인력 증설안은 확정하지 않았습니다.</p></article>''')

intro='''# 부산 119 신고 분석: 반복 양상에서 현재 서비스 연결까지

2026-09-16 작성. 분석은 2020–2024년, 운영 자료는 각 출처의 2025·2026년 기준이다.

## 왜 분석했는가
같은 부산 안에서도 신고 유형에 따라 반복되는 지역명과 시간 양상이 다르다. 지역별 접수 사실에 주민 구성과 기존 서비스 조건을 연결하면, 어떤 내용을 누구에게 어떤 경로로 안내할지 검토할 수 있다. 이 프로젝트는 먼저 그 근거를 분석하고, 결과를 이용할 수 있는 웹 시제품으로 전달한다.

## 직접 확인한 결과
- 17개 선택 컬럼에 결측이 없는 신고 704,689건. 정상 처리 579,412건, 정상 처리에서 운영성 분류를 제외한 주 분석은 574,662건이다.
- 주 분석의 194개 접수 지역명 × 예방 관련 5분류를 970개 조합으로 정리했다. 205개 행정동 위험 순위가 아니다.
- 산악 신고의 주말 일평균은 평일의 2.26배, 수난은 1.56배다. 심정지·주택화재는 약 0.99배다. 모든 유형에 같은 시간 전략을 적용할 근거는 없다.
- 10개 설명 사례는 5년 모두 반복되며, 세 처리조건에서 결측 제외 전후 반복 여부와 2020→2024 증감 방향이 유지된다. 이는 선택 영향이 없다는 뜻이 아니다.
- 수난 765건 중 2026 자원봉사 공고의 7/4–8/30과 같은 달력 구간에 184건, 나머지에 581건이었다. 그러나 일수 보정 후 각각 0.634건/일과 0.378건/일로 공고 구간이 더 높다. 이 기간은 전체 수상구조 운영기간이 아니다.

## 과거 자료를 현재에 연결한 결과
2026년 발행 연보에 수록된 2025년 부산 구급 출동은 188,760건, 이송 인원은 97,470명이다. 2024년 대비 각각 1,272건, 3,901명 감소했다. 대응이 지속되는 현안임은 보여주지만 수요 증가나 과거 동별 양상의 지속을 증명하지 않는다. 이송·출동과 본 분석의 신고접수는 서로 다른 모집단이다.

2026 수상구조 자원봉사 모집계획 250명과 모집결과 191명의 차이는 59명(23.6%)이며, 모집결과는 계획의 76.4%다. 확인한 것은 모집 지표의 차이다. 추가 모집·계획 변경·실제 배치 인원을 확인하지 못했으므로 현장 인력 부족이나 대응 실패로 해석할 수 없다.

## 기존 정부 운영과 차별점
부산은 이미 지역 특성별 구조 훈련, 화재 이력이 있는 노후아파트 우선 교육, CPR 교육·예약과 지원 자격 심사를 운영한다. 정부가 지역 분석을 하지 않았다고 주장하지 않는다.

이번 결과의 차별점은 접수 지역별 반복 근거·시간 분포·선택 민감도와 현재 서비스의 대상·시간·이용 경로를 한 사례 안에 연결하고, 근거가 연결되지 않은 시설·인력 증설은 구분해 보류한 것이다. 기존 서비스보다 효과가 좋다는 성과 검증은 아직 하지 않았다.

## 확인한 공백과 보류한 주장
현재 자료로 입증된 주민의 서비스 미충족 또는 특정 도로·해안·등산로의 대응 공백은 없다. 모집계획과 발표 결과의 차이는 운영 확인 대상으로 남는다. 접수 특성과 공식 이용 정보를 함께 전달하는 시제품은 제안할 수 있지만, 정보 분산 때문에 실제 이용이 실패했다는 주장은 이용 조사 없이는 할 수 없다.

## 유형별 결과의 활용 범위
- 심정지: 반복 근거와 CPR·AED 교육 대상·소요 시간·예약 경로를 함께 제공한다. 환자 연령 또는 야간 교육 수요는 추정하지 않는다.
- 주택화재: 반복 접수와 소방시설 지원 자격·예산 심사·신청 경로를 연결한다. 미설치 가구 수를 추정하지 않는다.
- 산악: 주말 접수의 일수 보정 결과를 기존 지역 특성별 훈련과 대조한다. 개별 등산로·순찰 증설은 보류한다.
- 수난: 연중 과거 접수와 해당 연도 전체 운영·자원봉사 일정을 구분해서 보여준다. 비활동 기간을 미대응 기간으로 표시하지 않는다.
- 교통: 반복 지역명과 기존 사고 지점 개선사업을 대조한다. 좌표·사건 연결 검증 전 도로 시설 입지는 보류한다.

## 사례별 수치
건수는 주 분석 조건의 신고접수이며, 주말 배수는 주말 하루 평균÷평일 하루 평균이다. 잔존율의 분모는 기존 8컬럼 비교 집합으로 원본 전체와 다르다.

| 지역명 | 유형 | 건수 | 2020/21/22/23/24 | 주말 일평균/평일 | 잔존율 |
|---|---|---:|---|---:|---:|
'''
tail='''
## 주민 배경·추가 자료의 채택 기준
주민은 같은 연도 12월 말의 전체 연령별 인원·비중을 사용한다. 동명 코드 후보가 여러 개면 각각 표시하며 합산·인구 비례 배분하지 않는다. 단일 코드 후보도 사건의 실제 공간 배정을 확정한 것은 아니다. 주민 연령은 안내 형식과 이용 조건을 검토하는 배경이며 신고자 연령이 아니다.

시설·서비스는 다섯 유형의 기존 대응을 확인하는 데 필요한 공식 자료만 채택했다. 상권·공사·생활인구는 현재 검증 수준에서 원인이나 대응 공백을 판단할 연결 근거가 없어 결합하지 않았다. 자료를 많이 확보하는 것과 타당한 근거를 만드는 것은 다르다.

## 검증과 재현
추가 분석은 analysis/00_공통/analyze_action_patterns_20260916.py, 연보 대조는 analyze_current_ems_bridge_20260916.py, 독립 검증은 verify_action_patterns_20260916.py로 실행한다. 모두 프로젝트 루트에서 .venv-check/Scripts/python.exe로 실행한다. 입력 해시·전체 합계·지역/분류/시간/처리조건·일수 분모·제외 전후 비교를 별도 검증 기록에 남겼다. 보고서 제작은 scripts/build_action_report_20260916.py다.

인구 대비 신고율·인과효과·피해 감소·실시간 위험도는 계산하지 않았다. 벌집제거는 심층 검토에서 제외했다. 향후 공백 판단에는 유형별 실제 사건 위치, 기존 사업의 당시 범위·배치·수혜·탈락 사유, 주민 이용 장벽 자료가 필요하다. 시제품의 효과는 과제 수행 정확도·공식 이용 경로 도달 여부 등으로 별도 평가해야 한다.
'''
background='''
## 문제제기를 뒷받침하는 공식 평가
소방청 「2025년도 자체평가 결과보고서」(2026년 1월, PDF 10쪽)는 분석·시각화와 현장업무의 연계 부족을 지적한다. 같은 보고서의 맞춤형 예방 성과도 함께 확인했다. 이는 전국 단위의 활용·환류 개선 근거이며 특정 부산 동의 서비스 미충족 증거는 아니다. 이번에는 그림을 만드는 데서 끝내지 않고 지역별 결과에 실제 서비스의 대상·운영 조건·이용 경로를 연결하는 활용 시나리오를 구체화했다.
출처: https://www.evaluation.go.kr/upload2/atch/eval/20260608093042921.pdf
문헌별 적용·보류 기준은 별도 「부산-119-연구차별성-20260916.md」에 정리했다.
'''
md=intro+'\n'.join(mdrows)+'\n'+tail+background
md+='\n## 공식 출처\n'+'\n'.join(f"- [{s['title']}]({s['url']}) · {s['referenceDate'] or '기준일 미기재 · 2026-09-16 열람'}" for s in r['sources'])
(OUT/'분석결과.md').write_text(md,encoding='utf-8')
(ROOT/'docs/40-분석결과/부산-119-예방지원-종합결과-20260916.md').write_text(md,encoding='utf-8')
figs=[]
for folder in ['analysis','yearbooks','population']:
    for f in sorted((BASE/folder).glob('*.svg')):
        shutil.copy2(f,OUT/f.name)
        png=f.with_suffix('.png')
        if png.exists(): shutil.copy2(png,OUT/png.name)
        figs.append(f'<figure><img src="{esc(f.name)}" alt="{esc(f.stem)}"><figcaption><a href="{esc(f.name)}">SVG 원본</a></figcaption></figure>')
for f in (BASE/'analysis').glob('*.csv'): shutil.copy2(f,OUT/f.name)
for f in (BASE/'population').glob('*.csv'): shutil.copy2(f,OUT/f.name)
body=f'''<header><span>부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</span><a href="../index.html">지도 탐색</a></header>
<main><p class="kicker">2020–2024 분석 · 2025–2026 운영 자료 대조</p><h1>어떤 신고가 반복됐고,<br>현재 서비스와 어떻게 연결되는가</h1>
<p class="lead">지역별 접수와 시간 차이를 분석하고, 기존 예방·지원의 대상과 이용 경로를 연결했습니다. 시설·인력의 부족을 확인하지 못한 곳에는 증설안을 제시하지 않았습니다.</p>
<nav><a href="#findings">핵심 결과</a><a href="#figures">시각화</a><a href="#cases">지역별 결과</a><a href="#conclusion">보완 결과</a><a href="분석결과.md">보고서 원문</a></nav>
<section id="findings"><h2>신고 유형별로 주말 양상이 달랐습니다</h2><div class="metrics"><p><strong>2.26배</strong>산악 · 주말 일평균 / 평일</p><p><strong>1.56배</strong>수난 · 주말 일평균 / 평일</p><p><strong>약 0.99배</strong>심정지·주택화재 · 같은 비교</p></div><p>정상 처리에서 운영성 분류를 제외한 574,662건 중 각 유형을 비교했습니다. 선택한 신고 집합의 특징이며 부산 전체 사건 위험률은 아닙니다.</p>
<h3>분석을 실제 이용으로 연결하는 것이 출발점입니다</h3><p>소방청 자체평가는 분석·시각화와 현장업무의 연계 부족을 지적했습니다. 이번 결과는 지역별 반복 근거를 실제 서비스 대상·운영 조건·이용 경로와 연결하는 방식으로 이 과제를 구체화합니다. 전국 평가의 지적을 부산 특정 지역의 서비스 부족으로 해석하지 않았습니다. <a href="https://www.evaluation.go.kr/upload2/atch/eval/20260608093042921.pdf">공식 평가 · 2026년 1월, PDF 10쪽</a></p>
<h3>현재 대응은 이미 운영되고 있습니다</h3><p>2025년 부산의 구급 출동은 188,760건입니다. 2024년보다 1,272건 감소했지만 대응은 지속됐습니다. 부산은 지역 특성별 구조 훈련과 화재 이력 주택 우선 교육 등을 이미 시행합니다.</p>
<h3>모집 지표의 차이와 현장 공백은 구분했습니다</h3><p>2026 수상구조 자원봉사 모집계획 250명 → 발표 191명(76.4%). 차이 59명을 실제 배치 인원 부족으로 볼 수는 없습니다. 7/4–8/30은 자원봉사 활동기간이며 전체 수상구조 운영기간이 아닙니다.</p></section>
<section id="figures"><h2>계산 결과를 직접 비교하세요</h2>{''.join(figs)}</section>
<section id="cases"><h2>반복성과 선택 영향을 확인한 10개 사례</h2><p>분류별 2개 설명 사례입니다. 건수 순위나 정책 우선순위가 아닙니다. 접수 지역명 기준이며 실제 행정동 배정과 구분합니다.</p><div class="table-scroll"><table><thead><tr>{''.join('<th>'+x+'</th>' for x in ['지역명','유형','건수','2020/21/22/23/24','주말 일평균/평일','잔존율'])}</tr></thead><tbody>{''.join(rows)}</tbody></table></div><div class="cases">{''.join(cases)}</div></section>
<section id="conclusion"><h2>새 시설을 단정하기보다, 검증된 지역 근거와 이용 경로를 연결합니다</h2><p>심정지는 CPR·AED 교육, 주택화재는 지원 자격과 신청 경로를 접수 근거와 함께 보여주는 서비스 구성이 가능합니다. 산악·수난·교통은 기존 운영과 비교하되 실제 지점과 서비스 실적을 확인하기 전 시설·인력 증설을 보류합니다.</p><p>현재 자료로 확정한 주민의 서비스 미충족은 없습니다. 이 결과물의 차별점은 지역별 반복·시간 차이와 선택 영향을 현재 운영 조건과 함께 공개한 것입니다. 실제 이용 개선이나 피해 감소는 별도 검증 대상입니다.</p><a href="all_region_prevention_catalogue.csv">194개 지역명 × 5분류 전체 탐색표 내려받기</a></section>
<footer>입력: 결측 제외 신고 704,689건 · 분석: 2020–2024 · 주민: 해당 연도 말 · 운영: 출처별 기준일 · 개별 접수번호·정밀 위치 미포함<br>출처·재현 방법·보류 근거: <a href="분석결과.md">분석 보고서</a></footer></main>'''
css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:#173846;background:#f4f8f7;font:16px/1.7 "Malgun Gothic",sans-serif}header{padding:18px 4vw;background:#123c4a;color:white;display:flex;justify-content:space-between}header a{color:white}main{max-width:1420px;margin:auto;padding:48px 5vw}h1{font-size:clamp(32px,3.7vw,56px);line-height:1.25;letter-spacing:-2px}h2{font-size:28px;line-height:1.4}h3{font-size:23px;margin-bottom:8px}h4{margin-bottom:4px}.kicker{color:#0c736d;font-weight:bold}.lead{max-width:1000px;font-size:21px}nav{display:flex;flex-wrap:wrap;gap:24px;border-block:1px solid #b9cdcd;padding:16px 0}a{color:#086b74}section{padding:32px 0;border-bottom:1px solid #b9cdcd}.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}.metrics strong{display:block;font-size:42px;color:#0a786f}figure{margin:28px 0;background:white;padding:12px}figure img{width:100%;height:auto}figcaption{font-size:14px}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:15px}td,th{padding:12px 9px;text-align:left;border-bottom:1px solid #ccdadc;white-space:nowrap}.cases{display:grid;grid-template-columns:1fr 1fr;gap:36px}article{padding:28px 0;border-bottom:2px solid #bfd4d0}.number{font-size:36px;font-weight:bold}.number small{display:block;font-size:14px;font-weight:normal}.meta,.status{color:#4d626b;font-size:15px}li p{font-size:14px;margin:4px 0}footer{font-size:14px;padding-top:28px}@media(max-width:800px){.cases,.metrics{grid-template-columns:1fr}main{padding:24px}.metrics{gap:0}header span{max-width:70%}}'''
(OUT/'index.html').write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 예방·지원 분석 결과</title><style>'+css+'</style>'+body+'</html>',encoding='utf-8')
manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.iterdir() if f.is_file() and f.name!='manifest.json'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
web=ROOT/'web/final/results'; web.mkdir(exist_ok=True)
for f in OUT.iterdir():
    if f.is_file(): shutil.copy2(f,web/f.name)
# The archive is standalone; its parent does not contain the map application.
standalone=OUT/'index.html'
standalone.write_text(standalone.read_text(encoding='utf-8').replace('<a href="../index.html">지도 탐색</a>','<a href="분석결과.md">분석 보고서</a>'),encoding='utf-8')
manifest['index.html']=hashlib.sha256(standalone.read_bytes()).hexdigest()
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
    for f in OUT.iterdir():
        if f.is_file(): z.write(f,f.name)
print(json.dumps({'profiles':len(cases),'figures':len(figs),'output':str(OUT)},ensure_ascii=False))
