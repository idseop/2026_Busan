"""Build one complete result library, single narrative MD, and linked map entry."""
from pathlib import Path
from urllib.parse import urlencode
import csv,hashlib,html,json,re,shutil
import mistune
R=Path(__file__).resolve().parents[1];N=R/'data/processed/통합완성-20260916';W=R/'web/final';P=W/'results/complete'
P.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
esc=lambda s:html.escape(str(s),quote=True)
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def lines(p):return p.read_text(encoding='utf-8-sig')
def page(title,body,active=''):
 links=[('index.html','통합 결과'),('../../index.html','부산 지도'),('../followup/explorer.html','지역별 상세'),('gallery.html','전체 시각화'),('data.html','집계표'),('report.html','전체 보고서')]
 return '<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><link rel="stylesheet" href="complete.css"></head><body><a class="skip" href="#content">본문으로</a><header class="site-header"><a class="brand" href="index.html">부산 신고 분석</a><nav aria-label="결과 탐색">'+''.join(f'<a class="{"active" if href==active else ""}" href="{href}">{label}</a>' for href,label in links)+'</nav></header><main id="content">'+body+'</main><script src="complete.js"></script></body></html>'

def load_figures():
 inv=read(N/'figure-inventory.json');figs=inv['figures']
 extra=N/'context/visuals.json'
 if extra.exists():
  more=read(extra);more=more if isinstance(more,list) else more.get('figures',[])
  for x in more:
   p=R/x['path'];x.update(sha256=sha(p),id=f'figure-{len(figs)+1:02d}');figs.append(x)
 advanced=R/'data/processed/지도입증확장-20260916/profiles'
 for stem,title,unit,finding in [
  ('coverage-194','194개 지역에서 연결되는 근거의 범위','연결 가능한 신고 지역명 수','주민·생활 후보192, 상권187, 주택 배경125. 서로 다른 기준의 자료이며 신고의 실제 발생 동 배정은 아니다.'),
  ('holdout-season-baselines','과거 지역별 계절 구성과 두 단순 기준을 2024년에 대조','계절 구성비 평균절대오차(%p)','407개 비교에서 유형별 평균은 지역별 과거 구성이 단순 기준보다 더 작지 않았다. 계절 인력 배치의 효과로 해석하지 않는다.'),
  ('holdout-top-season','과거 최고 계절이 2024년에도 겹친 비율','비교 가능한 지역·유형 조합 중 %','최고 일평균 계절의 일치는 유형별27.6~35.3%. 동률을 유지하고 2024년0건은 별도 보존했다.')]:
  p=advanced/(stem+'.png')
  if p.exists():figs.append({'id':f'figure-{len(figs)+1:02d}','path':p.relative_to(R).as_posix(),'sha256':sha(p),'svg':p.with_suffix('.svg').relative_to(R).as_posix(),'title':title,'kind':'지역 확장·시간 검증','period':'2020~2023 학습 / 2024 대조 또는 각 배경 기준일','unit':unit,'finding':finding,'source':'지도입증확장/profiles: 사후 시간 분리 검증 및 기존 집계. 공식 효과 실험이 아님.'})
 for x in figs:
  src=R/x['path'];assert sha(src)==x['sha256']
  x['publicPath']='figures/'+x['id']+'.png';dest=P/x['publicPath'];dest.parent.mkdir(exist_ok=True);shutil.copy2(src,dest)
  if x.get('svg'):
   x['svgPublic']='figures/'+x['id']+'.svg';shutil.copy2(R/x['svg'],P/x['svgPublic'])
 dump(P/'figure-catalogue.json',figs)
 return figs

def figures_page(figs):
 kinds=list(dict.fromkeys(x['kind'] for x in figs));filters='<div class="filter-row" data-filter-group="visuals"><button data-value="전체" aria-pressed="true">전체</button>'+''.join(f'<button data-value="{esc(k)}" aria-pressed="false">{esc(k)}</button>' for k in kinds)+f'<small data-filter-count role="status">{len(figs)}개 시각화</small></div>'
 cards=[]
 for i,x in enumerate(figs,1):
  cards.append(f'<article class="visual" id="{x["id"]}" data-item-group="visuals" data-category="{esc(x["kind"])}"><span class="kicker">{i:02d} · {esc(x["kind"])}</span><h2>{esc(x["title"])}</h2><button class="thumb" data-image="{x["publicPath"]}" data-title="{esc(x["title"])}" aria-label="{esc(x["title"])} 확대"><img loading="lazy" src="{x["publicPath"]}" alt="{esc(x["title"])}"></button><p>{esc(x["finding"])}</p><p class="meta">{esc(x["period"])} · {esc(x["unit"])}</p><p class="meta">{esc(x.get("source","원 집계와 입력 명세를 전체 보고서에 보존"))}</p><div class="figure-actions"><a download href="{x["publicPath"]}">PNG 저장</a>'+ (f'<a download href="{x["svgPublic"]}">SVG 저장</a>' if x.get('svgPublic') else '')+'</div></article>')
 modal='<dialog id="image-dialog" aria-labelledby="dialog-title"><div class="dialog-head"><h2 id="dialog-title"></h2><button id="close-image">닫기 · Esc</button></div><div class="image-scroll"><img id="dialog-image" alt=""></div></dialog>'
 return page('부산 신고 분석 · 전체 시각화',f'<p class="eyebrow">전체 분석을 한곳에서</p><h1>신고부터 지역 배경과 대응까지</h1><p>기존 13종에서 빠졌던 상권·생활인구·주택·시설·현장 결과와 새 분석을 함께 제공합니다. 같은 그림의 중복 복사본과 화면 검증 캡처는 분리했습니다.</p>{filters}<div class="gallery-grid">'+''.join(cards)+'</div>'+modal,'gallery.html')

TABLE_NAMES={'all_194_regions_5_domains_3_scopes.csv':'194개 지역×5유형×3처리조건','all_region_prevention_catalogue.csv':'전체 지역 예방 검토 목록','all_subtype_annual_scopes.csv':'모든 세부유형 연도·처리조건','all205-hour-2024-monthly.csv':'205동 월별 24시간 생활인구','all205-age-2024-monthly.csv':'205동 월별 연령 생활인구','busan_housing_context_2024.csv':'부산 전체 주택유형·건축년도','four-law-dong-categories.csv':'4개 법정동 업종 구성','four-law-dong-middle-categories.csv':'4개 법정동 세부 업종','all16-district-categories.csv':'16구군 업종 구성','traffic-followup-all14.csv':'14곳 교통 점검 후속 상태','chs2024-cpr-education.csv':'3개 구 주민 교육·실습 경험','stability_profiles.csv':'지역별 최고 시기 민감도','service-conditions.csv':'교육·대여 이용 조건','inspection-form-summary.csv':'소방 조사 판정·비고 구분','selected_housing_type_context.csv':'기장·온천 주택유형','building_type_comparison.csv':'고층건물·일반주택 신고 구분','all205-noon-midnight-comparison.csv':'205동 낮·밤 생활인구 비교','coverage_mois_all14_inspection_sites.csv':'공식 현장점검 14지점','coverage_all16_districts_2020_2025.csv':'16구군 연도별 보행사고 지정기록'}
def export_tables():
 rows=read(N/'aggregate-inventory.json');seen={x['sha256'] for x in rows}
 for p in sorted((N/'context').rglob('*.csv')) if (N/'context').exists() else []:
  if sha(p) not in seen:rows.append({'path':p.relative_to(R).as_posix(),'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size});seen.add(sha(p))
 for p in sorted((R/'data/processed/지도입증확장-20260916/profiles').glob('*.csv')):
  if sha(p) not in seen:rows.append({'path':p.relative_to(R).as_posix(),'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size});seen.add(sha(p))
 for i,x in enumerate(rows,1):
  p=R/x['path'];x['publicPath']=f'tables/{i:02d}-{p.name}';dest=P/x['publicPath'];dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
  with p.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f);cols=reader.fieldnames or [];count=0;sample=[]
   for rr in reader:
    count+=1
    if len(sample)<50:sample.append(rr)
   # Aggregate exports must never carry incident-level identifiers or coordinates.
   assert not set(cols)&{'DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT'},p
  x.update(title=TABLE_NAMES.get(p.name,p.stem.replace('_',' ').replace('-',' ')),rows=count,columns=cols)
  x['previewPath']=f'tables/table-{i:02d}.html'
  table='<div class="table-wrap"><table><thead><tr>'+''.join(f'<th>{esc(c)}</th>' for c in cols)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{esc(rr.get(c,""))}</td>' for c in cols)+'</tr>' for rr in sample)+'</tbody></table></div>'
  (P/x['previewPath']).write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>'+esc(x['title'])+'</title><link rel="stylesheet" href="../complete.css"><main><a href="../data.html">전체 집계표</a><h1>'+esc(x['title'])+f'</h1><p>전체 {count:,}행 중 처음 {len(sample)}행 · 수치와 기간은 컬럼별 정의를 따릅니다.</p><a download href="{esc(dest.name)}">전체 CSV 저장</a>'+table+'</main></html>',encoding='utf-8')
 dump(P/'table-catalogue.json',rows)
 return rows

def results_home(figs, tables):
 cases=read(W/'results/final/cases.json')
 # The source cases retain their own 5-year C-scope, never inherit map filters.
 cards=[]
 for c in cases:
  q=urlencode(dict(district=c['district'],dong=c['rawDong'],type=c['subtype'],scope='C'))
  label='구급 교통사고' if c['subtype']=='교통사고' else c['subtype']
  cards.append(f'<article class="case"><div class="case-meta">{esc(c["district"])}<span class="count">{c["count"]:,}<small>건</small></span></div><h3><a href="../followup/explorer.html?{q}">{esc(c["rawDong"])} · {esc(label)}</a></h3><p>{esc(c.get("action",c.get("result","신고·주민·지역 환경과 기존 대응을 함께 확인")))}</p><a class="more" href="../followup/explorer.html?{q}">지역 전체 결과 →</a></article>')
 picks=['commerce_four_area_context','living_hour_context','housing_type_context','aed-operating-hours']
 visualpicks=[x for key in picks for x in figs if key in x['path']]
 evidence=''
 ep=N/'evidence/results.md'
 if ep.exists():
  evidence='<section id="current-evidence"><span class="kicker">추가 확보한 공식 근거</span><h2>현재 대응까지 반영한 보완 결과</h2><div class="feature-grid">'
  for title,finding in [('금정산 탐방 안내','2026년 국립공원공단의 폭염 취약 구간·쉼터와 통제 안내를 연결했습니다. 과거의 겨울 접수와 현재의 폭염 안내는 구분합니다.'),('폐장 이후 수상안전','다대포 등 9월13일까지의 특별관리 발표와 해운대 9월15일까지의 당초 운영 계획을 반영했습니다. 확인일에는 기간이 지났으므로 현재 운영 중으로 표시하지 않습니다.'),('기장 아파트 점검','비의무관리 5층 이상 아파트의 무상점검을 기존 대응에 추가했습니다. 6월8일 접수 마감과 6~12월 점검 예정 기간을 구분합니다.')]:
   evidence+=f'<article><h3>{title}</h3><p>{finding}</p></article>'
  evidence+='</div><a href="report.html#part-9">9개 사례의 근거·보완 결과 전체 →</a></section>'
 context=''
 cp=N/'context/results.md'
 if cp.exists():context='<section id="extended-context"><span class="kicker">새 시계열 분석</span><h2>상권 20분기, 생활인구 두 해를 비교했습니다</h2><div class="two-col"><article><h3>한 시점의 상권에서 5년 비교로</h3><p>부산·16구군·모든 등장 법정동의 업종 구성을 계산했습니다. 같은 분기의 연도 비교와 같은 해의 분기 차이를 확인합니다. 2024년9~12월 목록 규모 차이를 실제 개폐업으로 해석하지 않았습니다.</p></article><article><h3>같은 부전동에서도 활동 시각은 다름</h3><p>부전1동 방문 정점14시와 부전2동19시는 2023·2024년 모두 유지됐습니다. 후보 행정동의 주거·직장·방문 배경을 각각 보여줍니다. 2025년은 별도 자료이며 신규 코드의 관측월 수도 구분했습니다.</p></article></div><a href="report.html#part-6">새 분석의 수치·방법 전체 →</a></section>'
 body=f'''<div class="hero"><div><p class="eyebrow">부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h1>반복 신고의 배경을 읽고,<br>지역의 예방·지원으로 연결</h1><p class="lead">5년 신고와 주민 구성, 상권·생활인구·주택·현장 조건을 함께 살폈습니다. 이미 시행한 대응을 반영해 지역별 보완 범위를 정리했습니다.</p><div class="actions"><a class="button" href="../../index.html">부산 지도</a><a class="button secondary" href="gallery.html">전체 시각화 {len(figs)}종</a><a class="text-link" href="report.html">단일 통합 보고서 →</a></div><p class="scope">신고 2020–2024 · 지역 배경·운영자료는 각 기준일 표시 · 실시간 발생 현황 아님</p></div><figure><img src="{next(x['publicPath'] for x in figs if 'commerce_four_area_context' in x['path'])}" alt="동별 상권 구성이 다름"><figcaption>신고 건수 다음의 판단: 지역의 환경과 기존 대응을 함께 확인</figcaption></figure></div>
<div class="chain"><div><b>01 부산 전체</b><span>5년 신고·선택 영향</span></div><div><b>02 지역 환경</b><span>주민·상권·생활·주택</span></div><div><b>03 기존 대응</b><span>현장 조사·시설·운영·정비</span></div><div><b>04 보완 결과</b><span>확인된 근거와 적용 범위</span></div></div>
<section><span class="kicker">문제제기와 차별점</span><h2>통계와 현장 활용 사이를 지역별 근거로 연결</h2><p>소방청의 2025년 자체평가는 데이터 분석·시각화와 현장업무 연계의 보완 필요성을 제시했습니다. 부산의 반복 신고를 출발점으로 서로 다른 자료의 시점과 대상을 맞추고, 기존 서비스의 이용조건과 완료된 정비까지 연결합니다.</p><p>정부가 지역 특성을 보지 않았다거나 대응이 없었다고 주장하지 않습니다. 이미 확인한 업무를 재사용하면서, 주민이 보는 지역 결과에 근거·배경·이용 경로를 함께 제공하는 방식입니다.</p><a href="https://www.evaluation.go.kr/upload2/atch/eval/20260608093042921.pdf">소방청 공식 자체평가</a></section>
<section><span class="kicker">누락 없이 연결한 지역 배경</span><h2>상권·생활인구·주택·시설도 결과의 일부입니다</h2><div class="figure-links four">'''+''.join(f'<a href="gallery.html#{x["id"]}"><img src="{x["publicPath"]}" alt="{esc(x["title"])}"><b>{esc(x["title"])}</b></a>' for x in visualpicks)+f'''</div><p>분석한 모든 현재 시각화는 전체 모음에서, {len(tables)}개 집계표는 내려받기와 미리보기로 제공합니다.</p></section>
<section id="cases"><span class="kicker">지역별 적용</span><h2>신고에서 배경과 대응까지</h2><p>2020–2024 정상 처리·운영성 제외 신고. 아래는 설명 사례이며 위험 순위가 아닙니다. 194개 지역×5유형 전체는 지역 상세에서 탐색합니다.</p><div class="case-list">'''+''.join(cards)+'''</div><a class="button secondary" href="../followup/explorer.html">전체 지역·유형 탐색</a></section>'''+context+evidence+'''<section><h2>확정한 보완과 측정할 효과</h2><p>지역별 결과에 배경자료·유효한 이용조건·사업 상태를 연결했습니다. 신규 시설·인력 수량과 사고 감소 효과는 관측하지 않은 값으로 채우지 않았습니다. 이용 경로 선택 정확도·소요시간, 실제 참여·술기, 현장 상태는 각각 별도의 측정 대상으로 구분했습니다.</p><a href="report.html">전체 분석·보완안·검증 범위 읽기</a></section>'''
 if (R/'data/processed/지도입증확장-20260916/profiles/summary.json').exists():
  update='<section id="evidence-extension"><span class="kicker">지역 확장과 실제 구현</span><h2>194개 지역을 비교하고, 부산을 2D·3D로 탐색합니다</h2><div class="feature-grid"><article><h3>다른 환경의 지역까지</h3><p>5개 신고 유형과 주민·생활·상권·주택 자료를 지역별로 연결했습니다. 9개 심층 사례의 기존 대응과 보완 내용은 지도 안에서 바로 읽을 수 있습니다.</p></article><article><h3>시간 특성을 다시 검증</h3><p>2020~2023년의 계절 구성을 2024년과 대조했습니다. 407개 비교의 유형별 평균에서 지역별 과거 구성이 단순 기준보다 더 정확하지 않았습니다. 과거 최고 계절만으로 배치를 제안하지 않았습니다.</p></article><article><h3>효과를 구분하는 결과</h3><p>출처·대상·마감·사업 상태를 연결하는 기능을 실제 검사합니다. 시민의 이해도·서비스 참여·피해 감소는 별도 효과이며, 자동 화면 검사를 그 효과로 바꾸지 않습니다.</p></article></div><a href="../../index.html">부산 2D·3D 지도 열기 →</a> · <a href="report.html#part-20">확장 분석과 효과 입증 논리 →</a></section>'
  body=body.replace('<section><span class="kicker">문제제기와 차별점</span>',update+'<section><span class="kicker">문제제기와 차별점</span>')
 return page('부산 신고 분석 · 전체 통합 결과',body,'index.html')

def main():
 figs=load_figures();tables=export_tables()
 shutil.copy2(W/'results/final/final.css',P/'complete.css')
 with (P/'complete.css').open('a',encoding='utf-8') as f:f.write('\n.four{grid-template-columns:repeat(4,1fr)}.dataset-search{font:inherit;width:100%;padding:12px;margin:18px 0;border:1px solid #99b8b7}.dataset-table td{overflow-wrap:anywhere}.report img{max-width:100%}.report h2{scroll-margin-top:95px}@media(max-width:1200px){.four{grid-template-columns:1fr 1fr}}')
 js='''document.querySelectorAll('[data-filter-group]').forEach(g=>{g.addEventListener('click',e=>{let b=e.target.closest('button[data-value]');if(!b)return;g.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));let n=0;document.querySelectorAll('[data-item-group="'+g.dataset.filterGroup+'"]').forEach(x=>{x.hidden=b.dataset.value!=='전체'&&x.dataset.category!==b.dataset.value;if(!x.hidden)n++;});g.querySelector('[data-filter-count]').textContent=n+'개 시각화';});});
let last;const modal=document.getElementById('image-dialog');document.querySelectorAll('[data-image]').forEach(b=>b.addEventListener('click',()=>{last=b;document.getElementById('dialog-title').textContent=b.dataset.title;let im=document.getElementById('dialog-image');im.src=b.dataset.image;im.alt=b.dataset.title;modal.showModal();}));if(modal){document.getElementById('close-image').onclick=()=>modal.close();modal.addEventListener('close',()=>last?.focus());}
document.getElementById('table-search')?.addEventListener('input',e=>{let n=0;document.querySelectorAll('[data-table-row]').forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(e.target.value.toLowerCase());if(!r.hidden)n++;});document.getElementById('table-count').textContent=n+'개 집계표';});
document.getElementById('print-report')?.addEventListener('click',()=>window.print());'''
 (P/'complete.js').write_text(js,encoding='utf-8')
 (P/'gallery.html').write_text(figures_page(figs),encoding='utf-8')
 body=f'<h1>전체 집계 결과</h1><p>동일 파일은 한 번만 수록했습니다. CSV는 원래의 기간·공간 단위·분모를 유지합니다.</p><label for="table-search">이름·컬럼 검색</label><input id="table-search" class="dataset-search" placeholder="상권, 생활인구, year, housing 등"><p id="table-count" role="status">{len(tables)}개 집계표</p><div class="table-wrap"><table class="dataset-table"><thead><tr><th>집계표</th><th>행 수</th><th>주요 컬럼</th><th>열기</th></tr></thead><tbody>'
 for t in tables:body+=f'<tr data-table-row><td>{esc(t["title"])}<br><small>{esc(t["name"])}</small></td><td>{t["rows"]:,}</td><td>{esc(" · ".join(t["columns"][:7]))}</td><td><a href="{t["previewPath"]}">미리보기</a> · <a download href="{t["publicPath"]}">CSV</a></td></tr>'
 (P/'data.html').write_text(page('부산 신고 분석 · 전체 집계표',body+'</tbody></table></div>','data.html'),encoding='utf-8')
 (P/'index.html').write_text(results_home(figs,tables),encoding='utf-8')
 report=R/'docs/40-분석결과/부산-119-전체결과-단일보고서-20260916.md'
 newest=R/'docs/40-분석결과/부산-119-지도와입증-통합보고서-20260917.md'
 if newest.exists():report=newest
 if report.exists():
  md=lines(report);(P/'전체결과보고서.md').write_text(md,encoding='utf-8')
  rendered=mistune.create_markdown(plugins=['table'])(md);ids=[]
  def head(m):
   i=f'part-{len(ids)+1}';ids.append((i,re.sub('<[^>]+>','',m[1])));return f'<h2 id="{i}">{m[1]}</h2>'
  rendered=re.sub(r'<h2>(.*?)</h2>',head,rendered)
  toc='<nav class="report-toc">'+''.join(f'<a href="#{i}">{t}</a>' for i,t in ids)+'</nav>'
  (P/'report.html').write_text(page('부산 신고 분석 · 단일 통합 보고서','<div class="report"><div class="report-tools"><a download href="전체결과보고서.md">전체 MD 저장</a><button id="print-report">인쇄 · PDF 저장</button></div>'+toc+rendered+'</div>','report.html'),encoding='utf-8')
 dump(N/'build-manifest.json',{'figures':len(figs),'tables':len(tables),'unchangedIncidentCounts':[704689,579412,574662],'reportExists':report.exists(),'files':{p.relative_to(R).as_posix():sha(p) for p in P.iterdir() if p.is_file()}})
 print(json.dumps({'figures':len(figs),'tables':len(tables),'report':report.exists()},ensure_ascii=False))
if __name__=='__main__':main()
