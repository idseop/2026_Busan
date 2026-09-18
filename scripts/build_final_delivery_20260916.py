"""Consolidate verified results into a final entry page and figure gallery.

No new incident statistics are computed. Source figures remain byte-identical.
Run after the existing analysis/report builders and the final narrative authoring.
"""
from pathlib import Path
from urllib.parse import urlencode
import json,html,hashlib,shutil,re,csv

R=Path(__file__).resolve().parents[1]
N=R/'data/processed/최종마감-20260916';N.mkdir(parents=True,exist_ok=True)
W=R/'web/final';F=W/'results/final';F.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)
E=R/'data/processed/효과근거확장-20260916'
focus=read(E/'temporal/focus-summary.json')
stable=read(E/'temporal/selection_stable_temporal.json')['strata'][0]
assert stable['combinations']==325 and stable['seasonSameAllFiveLeaveOut']==121
cases=[]
judgements={
 '연산동':('교육·실습','심층 사례','기본 교육·수료증·실습기자재를 목적과 이용 조건에 맞춰 연결','연제구 주민의 교육·실습 경험은 구 단위 조사로 따로 제공하며, 특정 계절에 한정하지 않습니다.'),
 '부전동':('보행·교통','심층 사례','과거 보행 조사에 맞이길 정비의 내용과 시점을 함께 표시','새 시설 제안에 앞서 기존 정비를 반영했습니다. 조사선과 최종 시공선의 정확한 일치는 아직 확정하지 않았습니다.'),
 '광안동':('보행·교통','비교 사례','수영로 포장사업과 내부도로의 보차분리 문제를 구분','처리조건에 따라 증감 방향이 달라지는 사례입니다. 신고 증가·감소만으로 사업 우선순위를 정하지 않습니다.'),
 '초읍동':('산악·수난','확인 범위 제공','기존 매트·울타리 정비와 신고 시기를 함께 제공','최고계절은 한 해씩 제외한 5회 중 2회만 같았습니다. 계절별 인력 배치를 확정할 근거는 없습니다.'),
 '금성동':('산악·수난','확인 범위 제공','로프·안내 정비와 통제 기간을 구분해 제공','기존 정비와 종료된 통제를 현재 공백이나 상시 폐쇄로 표시하지 않습니다.'),
 '다대동':('산악·수난','시기 비교 사례','여름 신고 양상과 기존 해변 운영기간을 함께 제공','여름 최고는 한 해 제외 5회 모두 유지됐습니다. 정확한 발생장소가 없어 해수욕장 인력 부족으로 해석하지 않습니다.'),
 '우동':('산악·수난','확인 범위 제공','월·계절 결과와 기존 대응을 각각의 기준으로 제공','가장 높은 월은 5월, 계절은 가을입니다. 수난 발생 지점이 확정되지 않아 특정 시설 보완안은 없습니다.'),
 '기장읍':('주택 예방','확인 범위 제공','주택 배경과 기존 예방교육을 연중 안내에 연결','최고월이 한 해 제외 비교에서 자주 바뀌므로 한 달에만 예방을 집중하지 않습니다.'),
 '온천동':('주택 예방','확인 범위 제공','주민·주택 배경과 확인된 기존 예방교육을 연결','특정 건축물의 피해나 신규 시설 수량을 추정하지 않았습니다.')}
for r in focus:
    cat,status,action,meaning=judgements[r['rawDong']]
    cases.append({k:r[k] for k in ['district','rawDong','type','subtype','count','yearCounts','topSeasons','leaveOneSeasonExact']}|dict(displaySubtype='구급 교통사고' if r['subtype']=='교통사고' else r['subtype'],category=cat,status=status,action=action,meaning=meaning,url='../followup/explorer.html?'+urlencode(dict(district=r['district'],dong=r['rawDong'],type=r['subtype'],scope='C'))))

nav='''<a class="skip" href="#main">본문으로 이동</a><header class="site-header"><a class="brand" href="index.html">부산 신고 분석<span>예방·지원 연결</span></a><nav aria-label="결과 탐색"><a href="index.html" data-nav="home">최종 결과</a><a href="../../index.html">부산 지도</a><a href="../followup/explorer.html">지역별 상세</a><a href="gallery.html" data-nav="gallery">시각화 모음</a><a href="report.html" data-nav="report">통합 보고서</a></nav></header>'''
css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:92px}body{margin:0;background:#f5f8f7;color:#173c48;font:16px/1.7 "Malgun Gothic",sans-serif}a{color:#076f79;text-underline-offset:4px}a:hover{color:#b36732}a:focus-visible,button:focus-visible,select:focus-visible{outline:3px solid #bb753e;outline-offset:4px}button{font:inherit;cursor:pointer}.skip{position:fixed;left:18px;top:-70px;background:#fff;padding:10px;z-index:30}.skip:focus{top:5px}.site-header{height:78px;display:flex;align-items:center;justify-content:space-between;padding:0 3.6vw;background:#fff;border-bottom:1px solid #d6e3e3;position:sticky;top:0;z-index:10}.brand{font-size:21px;font-weight:800;letter-spacing:-.7px;text-decoration:none;color:#174857}.brand span{margin-left:13px;padding-left:13px;border-left:1px solid #bad1d1;color:#54717a;font-size:14px;font-weight:400}.site-header nav{display:flex;gap:24px;align-items:center}.site-header nav a{font-size:15px;text-decoration:none;color:#34535d;padding:24px 0}.site-header nav a.active{font-weight:bold;color:#057b7b;border-bottom:3px solid #0c8583}main{max-width:1430px;margin:auto;padding:36px 46px 70px}.eyebrow{color:#157d81;font-size:14px;font-weight:bold;margin:0 0 14px}h1{font-size:40px;line-height:1.3;letter-spacing:-1.5px;margin:0 0 20px}h2{font-size:27px;line-height:1.4;letter-spacing:-.6px;margin:0 0 16px}h3{font-size:20px;line-height:1.5;margin:8px 0}p{margin:10px 0}.hero{display:grid;grid-template-columns:1.05fr 1fr;gap:44px;align-items:center;padding:18px 0 36px}.hero .lead{font-size:18px;line-height:1.9}.hero figure{margin:0;background:white;padding:12px}.hero img{width:100%;display:block}.hero figcaption{font-size:13px;color:#56707a;padding:10px}.actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:25px}.button{display:inline-block;padding:11px 19px;border:1px solid #176e78;border-radius:5px;text-decoration:none;font-size:15px;font-weight:bold;background:#176e78;color:white}.button.secondary{background:transparent;color:#176e78}.text-link{display:inline-flex;align-items:center;padding:10px 0;font-size:15px}.scope{font-size:13px;color:#60747b;margin-top:17px}.chain{display:grid;grid-template-columns:repeat(4,1fr);gap:25px;border-top:1px solid #c9dbda;border-bottom:1px solid #c9dbda;padding:22px 0}.chain div+div{border-left:1px solid #c9dbda;padding-left:24px}.chain b{font-size:17px}.chain span{display:block;font-size:14px;color:#536e74;margin-top:7px}section{padding:38px 0;scroll-margin-top:92px}section+section{border-top:1px solid #d2dfdf}.section-intro{display:flex;justify-content:space-between;gap:35px;align-items:flex-start}.section-intro p{max-width:750px;color:#49666d}.kicker{font-size:13px;color:#99713d;font-weight:bold;display:block;margin-bottom:6px}.filter-row{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:22px 0}.filter-row button{border:1px solid #bdd3d2;background:#fff;color:#2e525d;padding:8px 17px;border-radius:30px;font-size:15px}.filter-row button[aria-pressed=true]{background:#166c76;color:#fff;border-color:#166c76}.filter-row small{margin-left:auto;color:#587078}.case-list{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:0 32px}.case{padding:23px 0;border-top:2px solid #a7cac8;min-width:0}.case[hidden],.visual[hidden]{display:none}.case-meta{display:flex;justify-content:space-between;gap:10px;font-size:13px;color:#587179}.case .count{font-size:27px;font-weight:bold;color:#176e78;white-space:nowrap}.case h3 a{color:#193e4b;text-decoration:none}.case h3 small{font-size:15px;font-weight:400}.case p{font-size:15px}.case .meaning{color:#5e757a;font-size:14px}.case a.more{font-size:14px;font-weight:bold}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:15px;margin:20px 0;background:#fff}th,td{text-align:left;vertical-align:top;padding:15px 17px;border-bottom:1px solid #dbe6e5}th{background:#e6f0ee;color:#20525d}td:first-child{font-weight:bold;min-width:125px}.gap-type{font-size:13px;color:#8c6032;font-weight:bold}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:36px}.result-box{border-left:4px solid #20817f;background:#e5f1ed;padding:18px 25px;margin-top:20px}.result-box p{font-size:16px}.quiet{font-size:14px;color:#5a7479}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:30px}.feature-grid article{padding:20px 0;border-top:2px solid #98bfbd}.feature-grid span{font-size:13px;color:#89603e;font-weight:bold}.feature-grid p{font-size:15px}.figure-links{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:25px}.figure-links a{text-decoration:none;display:block;background:#fff;padding:12px;color:#234653}.figure-links img{width:100%;height:185px;object-fit:contain;display:block}.figure-links b{font-size:15px;display:block;margin:10px 4px}.gallery-intro{max-width:950px}.gallery-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:32px}.visual{background:#fff;padding:22px;min-width:0;scroll-margin-top:95px}.visual .thumb{display:block;width:100%;border:0;background:#f9fbfa;padding:0;cursor:zoom-in}.visual img{display:block;width:100%;height:280px;object-fit:contain}.visual h2{font-size:21px}.visual p{font-size:15px}.visual .meta{font-size:13px;color:#597078}.figure-actions{display:flex;gap:18px;flex-wrap:wrap;font-size:14px;margin-top:12px}dialog{padding:0;border:1px solid #c0d5d4;border-radius:8px;width:94vw;max-width:1450px;max-height:92vh;background:#fff}dialog::backdrop{background:#0e2f3a99}.dialog-head{display:flex;align-items:center;justify-content:space-between;gap:30px;padding:14px 24px;border-bottom:1px solid #cadbd9}dialog h2{font-size:21px;margin:0}dialog button{border:1px solid #a7c4c5;background:#fff;padding:8px 15px;border-radius:5px}dialog .image-scroll{overflow:auto;max-height:75vh;padding:16px}dialog img{width:100%;height:auto;display:block}.report{max-width:1060px;margin:auto}.report h1{font-size:34px}.report h2{margin-top:35px}.report h3{margin-top:25px}.report li{margin:7px 0}.report pre{overflow:auto;background:#e7efed;padding:16px}.report blockquote{border-left:4px solid #4a9393;margin:20px 0;padding:5px 20px;background:#eaf3f0}.report img{max-width:100%}.report-toc{padding:18px 24px;background:#e6f0ee;columns:2;column-gap:32px;margin-bottom:30px}.report-toc a{display:block;font-size:14px;margin:5px 0;break-inside:avoid}.report-tools{display:flex;gap:16px;align-items:center;margin-bottom:25px}.report-tools button{background:#fff;border:1px solid #b9cfce;padding:9px 15px;border-radius:5px;color:#275561}footer{border-top:1px solid #c9dada;padding:23px 0;font-size:13px;color:#536b73;display:flex;justify-content:space-between;gap:25px}.foot-links{display:flex;gap:22px}@media(max-width:1150px){main{padding:28px}.site-header{padding:0 24px}.brand span{display:none}.case-list{gap:0 22px}h1{font-size:34px}.hero{gap:25px}.chain{gap:14px}.site-header nav{gap:18px}}@media(max-width:800px){.site-header{height:auto;position:static;align-items:flex-start;flex-direction:column;padding:15px 20px}.site-header nav{gap:16px;flex-wrap:wrap}.site-header nav a{padding:7px 0}.hero,.case-list,.two-col,.feature-grid,.gallery-grid{grid-template-columns:1fr}.chain{grid-template-columns:1fr 1fr}.chain div+div{border:0;padding:0}.figure-links{grid-template-columns:1fr}.section-intro{display:block}.report-toc{columns:1}h1{font-size:30px}main{padding:20px}.visual img{height:auto}}@media print{.site-header,.filter-row,.actions,.report-tools,.skip,footer{display:none}body{background:white}main{padding:0;max-width:none}.hero{display:block}.hero figure{max-width:700px}.visual,figure,table{break-inside:avoid}a{color:inherit}.case-list{display:block}.case{break-inside:avoid}}'''
js='''(()=>{'use strict';const all=(s)=>Array.from(document.querySelectorAll(s));all('[data-filter-group]').forEach(group=>{const target=group.dataset.filterGroup,items=all(`[data-item-group="${target}"]`);group.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{group.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));let n=0;items.forEach(i=>{i.hidden=button.dataset.value!=='전체'&&i.dataset.category!==button.dataset.value;if(!i.hidden)n++;});group.querySelector('[data-filter-count]').textContent=`${n}개 ${target==='cases'?'사례':'시각화'}`;}));});const dlg=document.getElementById('figure-dialog');if(dlg){let trigger;all('[data-open-figure]').forEach(b=>b.addEventListener('click',()=>{trigger=b;document.getElementById('figure-image').src=b.dataset.src;document.getElementById('figure-image').alt=b.dataset.title;document.getElementById('figure-title').textContent=b.dataset.title;dlg.showModal();}));document.getElementById('figure-close').addEventListener('click',()=>dlg.close());dlg.addEventListener('click',e=>{if(e.target===dlg)dlg.close();});dlg.addEventListener('close',()=>trigger?.focus());}document.querySelector('[data-print]')?.addEventListener('click',()=>window.print());})();'''

def page(title,body,active):
    menu=nav.replace(f'data-nav="{active}"',f'data-nav="{active}" class="active" aria-current="page"')
    return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><link rel="stylesheet" href="final.css"><script defer src="final.js"></script></head><body>'+menu+'<main id="main">'+body+'''<footer><span>신고 분석 2020–2024 · 후속 자료 확인 2026.9.16</span><div class="foot-links"><a href="report.html">통합 보고서·출처</a><a href="verification.html">검증·실행 방법</a></div></footer></main></body></html>'''
def filters(target,categories,count):
    return f'<div class="filter-row" data-filter-group="{target}" role="group" aria-label="'+('사례 분류' if target=='cases' else '시각화 분류')+'">'+''.join(f'<button type="button" data-value="{esc(c)}" aria-pressed="{str(i==0).lower()}">{esc(c)}</button>' for i,c in enumerate(['전체',*categories]))+f'<small data-filter-count role="status">{count}개 '+('사례' if target=='cases' else '시각화')+'</small></div>'
case_html=''.join(f'''<article class="case" data-item-group="cases" data-category="{esc(c['category'])}"><div class="case-meta"><span>{esc(c['district'])} · {esc(c['status'])}</span><span class="count">{c['count']:,}<small>건</small></span></div><h3><a href="{esc(c['url'])}">{esc(c['rawDong'])} <small>· {esc(c['subtype'])}</small></a></h3><p><b>{esc(c['action'])}</b></p><p class="meaning">{esc(c['meaning'])}</p><a class="more" href="{esc(c['url'])}">신고·주민·대응 결과 보기 →</a></article>''' for c in cases)
home='''<div class="hero"><div><p class="eyebrow">부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>지역의 반복 신고를<br>예방·지원 정보로 연결</h1><p class="lead">5년간의 신고를 주민 구성과 현장 배경으로 살펴보고,<br>기존 서비스와 정비를 대조해 지역별 보완 범위를 정했습니다.</p><div class="actions"><a class="button" href="../../index.html">부산 지도에서 탐색</a><a class="button secondary" href="#cases">지역별 핵심 결과</a><a class="text-link" href="report.html">통합 보고서 읽기 →</a></div><p class="scope">2020–2024 선택 조건의 신고 분석 · 실시간 발생 현황이 아닙니다.</p></div><figure><img src="../effects/figures/cpr-trend.png" alt="2020–2024 부산과 전국의 기록된 일반인 CPR 시행률 추이"><figcaption>문제 배경의 한 근거: 부산의 기록된 일반인 CPR 시행률 하락.<br>질병관리청 환자 조사이며 이 프로젝트의 신고접수와 별도입니다. <a href="../effects/index.html#cpr">근거 보기</a></figcaption></figure></div>
<div class="chain" aria-label="분석 흐름"><div><b>01 부산에서 출발</b><span>5년 신고 특성과 선택 영향을 확인</span></div><div><b>02 지역으로 좁히기</b><span>반복성·시기·주민·현장 배경 비교</span></div><div><b>03 기존 대응 확인</b><span>서비스 조건과 후속 정비를 대조</span></div><div><b>04 보완 결과 전달</b><span>근거가 있는 안내와 활용 범위를 연결</span></div></div>
<section id="message"><span class="kicker">문제제기와 프로젝트의 역할</span><div class="section-intro"><h2>신고 건수 다음의 판단을<br>지역별로 연결했습니다</h2><p>어느 지역에서 어떤 신고가 반복되는지 알아도 곧바로 필요한 시설이나 인력을 정할 수는 없습니다. 주민 배경, 현재 이용할 수 있는 서비스, 이미 끝난 정비까지 함께 읽어야 합니다. 이번 서비스는 그 판단에 필요한 근거를 한 흐름으로 제공합니다.</p></div><div class="feature-grid"><article><span>부산 초기대응</span><h3>주민 교육·실습까지 확인</h3><p>부산의 2024년 기록된 CPR 시행률은 13.8%. 연제구의 교육 경험 29.0%와 AED 실습 경험 18.5%는 별도 주민 조사로 확인했습니다.</p><a href="../effects/index.html#education">공식 조사와 해석</a></article><article><span>시간 전략</span><h3>반복과 계절 집중을 구분</h3><p>선택 조건에 안정적인 325개 지역·유형 조합 중, 한 해씩 제외해도 최고계절이 모두 유지된 조합은 121개였습니다.</p><a href="../effects/index.html#temporal">시기 비교 결과</a></article><article><span>현재 대응</span><h3>이미 시행한 사업도 반영</h3><p>부전 맞이길의 설계·사업 기록, 광안 포장사업, 못골시장 효과평가 수행을 확인해 과거 문제와 현재 대응을 구분했습니다.</p><a href="../effects/index.html#roads">기존 사업과 비교</a></article></div></section>
<section id="cases"><span class="kicker">숲에서 나무로 · 9개 설명 사례</span><div class="section-intro"><h2>지역마다 다른 보완 결과</h2><p>194개 신고 지역명×5유형의 970개 조합에서 출발했습니다. 아래는 기존 대응과 함께 설명할 수 있는 사례입니다. 위험 순위가 아니며, 광안동은 조건에 민감한 비교 사례로 구분했습니다.</p></div><p class="quiet">아래 수치: 2020–2024 합계 · 정상 처리·운영성 기록 제외 · 해당 지역명으로 접수된 신고</p>'''+filters('cases',['교육·실습','보행·교통','산악·수난','주택 예방'],len(cases))+'<div class="case-list">'+case_html+'''</div></section>
<section id="gaps"><span class="kicker">확인한 공백과 구현한 보완</span><h2>정보의 문제와 현장 부족을 구분했습니다</h2><div class="table-wrap"><table><thead><tr><th>확인한 내용</th><th>근거</th><th>이번에 반영한 보완</th></tr></thead><tbody><tr><td>이용 조건의 충돌</td><td>사하 교육 공고의 운영·신청 종료일과 정확히 10명일 때 개설 조건이 상충</td><td>현재 예약 가능으로 단정하지 않고 공식 사전협의 경로를 제공</td></tr><tr><td>목적이 다른 서비스</td><td>기본교육·수료증 과정·교육용 장비·환자용 장비는 대상과 조건이 다름</td><td>목적·시간·이용 조건을 구분해 잘못된 선택을 줄이도록 안내</td></tr><tr><td>과거 조사와 후속 사업의 시점 차이</td><td>2024년 현장 조사 뒤 2025–2026년 정비·평가 기록 확인</td><td>과거 문제를 현재 미대응으로 표시하지 않고 사업 단계와 함께 제공</td></tr><tr><td>분석에서 바로잡은 기록 해석</td><td>13행은 조치완료 전용란이 아닌 일반 비고란 공란</td><td>현재 미조치 13곳이나 관리공백 비율로 쓰지 않도록 교정</td></tr></tbody></table></div><p class="quiet">시설·인력의 실제 부족과 개별 주민의 미충족 수요는 확인되지 않았습니다. 정보가 없다는 사실만으로 현장 공백을 만들지 않았습니다.</p></section>
<section id="service"><span class="kicker">최종 서비스 구성</span><h2>지역 찾기부터 근거 확인까지</h2><div class="feature-grid"><article><span>지도</span><h3>부산에서 지역 찾기</h3><p>구·군과 동명 검색, 연도·종별·처리조건, 지역 선택을 연결합니다. 위치가 확정되지 않은 동은 소속 구·군으로 안내합니다.</p><a class="button secondary" href="../../index.html">부산 지도 열기</a></article><article><span>지역 상세</span><h3>신고·주민·기존 대응 읽기</h3><p>5년 변화와 시간 패턴, 후보별 전체 연령 구성, 서비스 조건과 시기 비교를 해당 지역의 결과로 제공합니다.</p><a class="button secondary" href="../followup/explorer.html">지역별 상세 열기</a></article><article><span>시각화·보고서</span><h3>결과를 설명하고 공유하기</h3><p>핵심 그림을 목적과 결론별로 모았습니다. 원본 이미지와 벡터 그림, 출처, 통합 MD를 내려받을 수 있습니다.</p><a class="button secondary" href="gallery.html">시각화 모음 열기</a></article></div></section>
<section id="visuals"><span class="kicker">시각화로 보는 핵심 근거</span><h2>문제 배경·지역 판단·보완을 한 흐름으로</h2><div class="figure-links"><a href="gallery.html"><img src="../effects/figures/education-practice.png" alt="연제 부산진 수영 교육과 실습 경험"><b>주민의 교육 경험과 실습 경험</b></a><a href="gallery.html"><img src="../effects/figures/leave_one_season.png" alt="지역 사례의 최고계절 유지 비교"><b>여러 해에서도 유지되는 시기</b></a><a href="gallery.html"><img src="../advance/service_conditions_comparison.svg" alt="기존 교육과 대여 서비스의 조건 비교"><b>목적에 따라 다른 이용 조건</b></a></div></section>
<section id="effects"><div class="two-col"><div><span class="kicker">차별점</span><h2>공공 정보를 지역의 판단 근거로 연결</h2><p>기존 공공 지도·예방교육·점검·정비를 대체하는 서비스는 아닙니다. 신고의 선택 영향, 주민 배경, 운영 조건, 후속 사업의 시점을 함께 보여주는 것이 이번 결과물의 역할입니다.</p></div><div><span class="kicker">기대효과와 확인 범위</span><h2>정확한 선택부터 측정</h2><p>직접 기대효과는 목적에 맞는 서비스 선택과 과거·현재 상태의 혼동 감소입니다. 같은 과제의 정답률·탐색시간·오선택률로 측정하도록 정리했습니다. 실제 참여와 사고·피해 감소 효과는 아직 측정하지 않았습니다.</p><a href="../effects/effect-measurement.json">효과 측정 명세</a></div></div><div class="result-box"><b>완성한 결과</b><p>검증된 분석과 시각화, 지역별 근거 연결, 실행 가능한 결과 웹을 완성했습니다. 기관의 원공고 수정이나 현장 공사·인력 배치를 수행한 것은 아닙니다.</p></div></section>'''
home=home.replace('<small>· 교통사고</small>','<small>· 구급 교통사고</small>').replace('아래 수치: 2020–2024 합계 · 정상 처리·운영성 기록 제외 · 해당 지역명으로 접수된 신고','아래 수치: 2020–2024 합계 · 정상 처리·운영성 기록 제외 · 해당 지역명으로 접수된 신고<br>최고 시기: 접수 건수를 해당 기간의 달력 일수로 나누어 비교')
(F/'index.html').write_text(page('부산 신고 분석 · 최종 결과',home,'home'),encoding='utf-8')
(F/'final.css').write_text(css,encoding='utf-8');(F/'final.js').write_text(js,encoding='utf-8')
(F/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')

# The inventory is separately audited before this build consumes it.
invpath=N/'visual-inventory.json'
if invpath.exists():
    raw=read(invpath)
    visuals=raw if isinstance(raw,list) else raw.get('figures',raw.get('items',raw.get('records',[])))
    extra=N/'additional-visuals.json'
    if extra.exists():
        more=read(extra);more=more if isinstance(more,list) else more.get('items',more.get('figures',[]))
        for v in more:
            population=v['id']=='population-count-and-share'
            visuals.append(v|dict(path=(N/v['png']).relative_to(R).as_posix(),sha256=v['sha256']['png'],kind='주민 배경' if population else '사례 선정',source='같은 연도 말 공식 주민 인구 · 검증된 후보별 집계' if population else '기존 전 지역 비교와 선택·시기 민감도 집계',reportLink='web/final/results/final/report.html#report-'+('5' if population else '4'),coreFinding='연산3동과 부전2동은 2020년보다 2024년의 65세 이상 주민 인원은 늘고 비중은 낮아졌습니다. 신고자의 연령은 아닙니다.' if population else '325개는 반복·증감 방향의 선택 안정성입니다. 계절 121개와 월 33개는 별도 비교이며, 광안동은 별도 비교 사례입니다.'))
    assert visuals,'No audited figures in inventory'
    cards=[];gallery_records=[];groups=[]
    for i,v in enumerate(visuals,1):
        p=R/v['path'];assert p.is_file(),p
        if v.get('sha256'):assert sha(p)==v['sha256'],('inventory figure changed',p)
        cat=v.get('category',v.get('kind','분석 결과'))
        if cat not in groups:groups.append(cat)
        dest=F/'figures'/f'{i:02d}-{p.name}';dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
        uri=dest.relative_to(F).as_posix();name=v['title'];finding=v.get('coreFinding',v.get('finding',''))
        downloads=f'<a download href="{esc(uri)}">{p.suffix[1:].upper()} 저장</a>'
        pair=p.with_suffix('.svg' if p.suffix=='.png' else '.png')
        alternatives=[]
        if pair.is_file():
            alt=dest.with_suffix(pair.suffix);shutil.copy2(pair,alt);alternatives.append(alt.relative_to(F).as_posix());downloads+=f'<a download href="{esc(alternatives[-1])}">{pair.suffix[1:].upper()} 저장</a>'
        link=v.get('reportLink','../effects/index.html')
        if link.startswith('web/final/'):link='../../'+link[len('web/final/'):]
        src=v.get('source','검증된 분석 집계')
        if not isinstance(src,str):src=json.dumps(src,ensure_ascii=False)
        cards.append(f'''<article id="figure-{i:02d}" class="visual" data-item-group="figures" data-category="{esc(cat)}"><span class="kicker">{i:02d} · {esc(cat)}</span><h2>{esc(name)}</h2><button class="thumb" type="button" data-open-figure data-src="{esc(uri)}" data-title="{esc(name)}" aria-label="{esc(name)} 크게 보기"><img src="{esc(uri)}" alt="{esc(finding)}" loading="lazy"></button><p><b>{esc(finding)}</b></p><p class="meta">{esc(v.get('period',''))} · {esc(v.get('unit',''))}<br>출처: {esc(src)}</p><div class="figure-actions">{downloads}<a href="{esc(link)}">관련 결과·해석</a></div></article>''')
        gallery_records.append(v|dict(number=i,publicPath=uri,alternativePaths=alternatives,sourceSHA256=sha(p)))
    gallery='''<div class="gallery-intro"><p class="eyebrow">설명과 공유를 위한 최종 시각화</p><h1>핵심 근거를 그림으로</h1><p class="lead">문제 배경에서 지역 판단과 기존 대응까지, 각 그림의 결론·기간·단위를 함께 정리했습니다. 그림을 누르면 크게 볼 수 있고, PNG·SVG 원본을 저장할 수 있습니다.</p></div>'''+filters('figures',groups,len(cards))+'<div class="gallery-grid">'+''.join(cards)+'</div><dialog id="figure-dialog" aria-labelledby="figure-title"><div class="dialog-head"><h2 id="figure-title"></h2><button id="figure-close" type="button" autofocus>닫기 ×</button></div><div class="image-scroll"><img id="figure-image" alt=""></div></dialog>'
    (F/'gallery.html').write_text(page('부산 신고 분석 · 시각화 모음',gallery,'gallery'),encoding='utf-8')
    (F/'visual-catalogue.json').write_text(json.dumps(gallery_records,ensure_ascii=False,indent=2),encoding='utf-8')

# Render the authored Markdown; source stays downloadable and authoritative.
mdpath=R/'docs/40-분석결과/부산-119-최종통합보고서-20260916.md'
if mdpath.exists():
    import mistune
    md=mdpath.read_text(encoding='utf-8')
    rendered=mistune.create_markdown(plugins=['table','strikethrough'])(md)
    # Code-like project paths remain prose; relocate genuine Markdown file links.
    from urllib.parse import unquote
    def relocate(m):
        href=html.unescape(m.group(1))
        if href.startswith(('http:','https:','#','mailto:')):return m.group(0)
        path,_,frag=href.partition('#');target=(mdpath.parent/unquote(path)).resolve()
        try:
            rel=target.relative_to(W.resolve()).as_posix();return 'href="../../'+esc(rel)+('#'+esc(frag) if frag else '')+'"'
        except ValueError:pass
        if target.is_file() and target.suffix in ['.md','.json','.csv']:
            dest=F/'references'/target.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(target,dest)
            if '/' not in path and '\\' not in path:shutil.copy2(target,F/target.name)
            return 'href="references/'+esc(target.name)+('#'+esc(frag) if frag else '')+'"'
        # Only delivered files are linked. Workspace paths remain readable text.
        return 'data-project-path="'+esc(href)+'"'
    rendered=re.sub(r'href="([^"]+)"',relocate,rendered)
    toc=[]
    def heading(m):
        idx=len(toc)+1;name=m.group(1);toc.append((idx,name));return f'<h2 id="report-{idx}">{name}</h2>'
    rendered=re.sub(r'<h2>(.*?)</h2>',heading,rendered,flags=re.S)
    links='<nav class="report-toc" aria-label="보고서 목차">'+''.join(f'<a href="#report-{i}">{name}</a>' for i,name in toc)+'</nav>'
    body='<div class="report"><div class="report-tools"><a class="button secondary" href="최종통합보고서.md" download>MD 원본 저장</a><button type="button" data-print>인쇄 / PDF 저장</button></div>'+links+rendered+'</div>'
    (F/'report.html').write_text(page('부산 신고 분석 · 최종 통합 보고서',body,'report'),encoding='utf-8')
    shutil.copy2(mdpath,F/'최종통합보고서.md')

# Current report pages lead back to the final entry point without replacing evidence.
effect=W/'results/effects/index.html'
s=effect.read_text(encoding='utf-8')
s=re.sub(r'<header>.*?</header>','<header><strong>부산 신고 분석 · 근거 상세</strong><nav><a href="../final/index.html">최종 결과</a><a href="../../index.html">부산 지도</a><a href="../followup/explorer.html">지역별 상세</a><a href="../final/gallery.html">시각화 모음</a><a href="../final/report.html">통합 보고서</a></nav></header>',s,count=1,flags=re.S)
effect.write_text(s,encoding='utf-8')
provenance={'scope':'Presentation consolidation; existing selected incident population and figures unchanged','inputs':[{'path':str(p.relative_to(R)),'sha256':sha(p)} for p in [E/'temporal/focus-summary.json',E/'temporal/selection_stable_temporal.json',invpath,mdpath] if p.exists()],'cases':len(cases),'figures':len(visuals) if invpath.exists() else 0,'entry':'web/final/results/final/index.html'}
(N/'build-manifest.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
review_items=[]
for name,label in [('content-final.json','핵심 수치·해석과 통합 보고서'),('browser-final.json','PC 화면·지도 연결·필터·그림 확대')]:
    path=N/'verification'/name
    if path.exists():
        check=read(path);status=check.get('status','검토 기록 있음');count=check.get('total',check.get('count',len(check.get('checks',[]))))
        review_items.append(f'<tr><td>{esc(label)}</td><td>{esc(status)} · {count}개 검사</td><td><a href="verification/{esc(name)}">실행 기록</a></td></tr>')
        dest=F/'verification'/name;dest.parent.mkdir(exist_ok=True);shutil.copy2(path,dest)
        mdfile=path.with_suffix('.md')
        if mdfile.exists():shutil.copy2(mdfile,dest.with_suffix('.md'))
    else:review_items.append(f'<tr><td>{esc(label)}</td><td>최종 검증 진행 중</td><td>배포 전 확인</td></tr>')
verify='''<div class="report"><p class="eyebrow">실행 방법과 확인한 범위</p><h1>검증·실행 안내</h1><h2>PC에서 여는 방법</h2><p>압축을 푼 뒤 <code>결과보기.html</code>을 열면 최종 결과·시각화·보고서·지역 탐색을 확인할 수 있습니다. 지도 배경까지 보려면 배포 폴더에서 다음 명령을 실행합니다.</p><pre>python serve.py --no-browser</pre><p><a href="http://127.0.0.1:8765/">http://127.0.0.1:8765/</a> · 이미 서버가 실행 중이면 같은 주소를 열면 됩니다. 공식기관 링크와 지도 배경은 인터넷 연결이 필요합니다.</p><h2>검증된 분석을 재사용</h2><p>기존 신고 집합과 집계를 바꾸지 않았습니다. 원자료 대조·시간 분석·주민 조사·사업 내역 검증은 파일 해시가 맞는 기록을 재사용하고, 이번에 바꾼 결과 연결과 화면을 별도로 확인했습니다.</p><p><a href="../effects/검증기록.md">분석별 독립 검증 기록</a> · <a href="../effects/data/input-manifest.json">분석 입력 명세</a> · <a href="visual-catalogue.json">그림별 출처·원본 해시</a></p><h2>이번 마감 검증</h2><table><thead><tr><th>구분</th><th>상태</th><th>기록</th></tr></thead><tbody>'''+''.join(review_items)+'''</tbody></table><p>새 주민 변화 그림은 기존 연령 집계와 대조합니다. PNG·SVG 원본과 갤러리 사본도 해시로 확인합니다. 전체 웹 ZIP과 시각화 ZIP은 별도의 배포 명세·무결성 검사 기록으로 관리합니다.</p><h2>검증의 의미</h2><p>이는 자료·표시·기능의 검사입니다. 사용자 실험, 실제 교육 참여 증가, 사고·피해 감소 효과를 검증한 것은 아닙니다. 효과 검증의 다음 단계는 <a href="../effects/effect-measurement.json">측정 명세</a>에 구분했습니다.</p></div>'''
(F/'verification.html').write_text(page('부산 신고 분석 · 검증과 실행',verify,'report'),encoding='utf-8')
print(json.dumps(provenance,ensure_ascii=False))
