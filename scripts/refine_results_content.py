"""Rebuild result tabs from checked-in aggregate reports; never read raw incidents."""
from pathlib import Path
from urllib.parse import urlencode
import csv,hashlib,html,json,re,shutil
import mistune

R=Path(__file__).resolve().parents[1];P=R/'web/final/results/complete'
esc=lambda x:html.escape(str(x),quote=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
text=lambda p:p.read_text(encoding='utf-8-sig')
report=R/'output/부산진구-중구-1차분석'
manifest=json.loads(text(report/'manifest.json'))
# Verify the packaged local analysis against its recorded output hashes.
for name,digest in manifest['outputs_sha256'].items():
 source=R/name.replace('\\','/')
 assert source.exists() and sha(source)==digest,name
evidence=json.loads(text(R/'web/final/data/regional-evidence.js').split('=',1)[1].strip().rstrip(';'))
inventory=P/'content-inventory.json'
if inventory.exists():figures=json.loads(text(inventory))['figures'][:48]
else:
 figures=[]
 for block in re.findall(r'<article class="visual".*?</article>',text(P/'gallery.html')):
  get=lambda pattern:html.unescape(re.search(pattern,block,re.S)[1])
  paragraphs=re.findall(r'<p(?: class="meta")?>(.*?)</p>',block,re.S)
  figures.append(dict(id=get(r'id="(.*?)"'),category=get(r'data-category="(.*?)"'),title=get(r'<h2>(.*?)</h2>'),finding=html.unescape(paragraphs[0]),period=html.unescape(paragraphs[1]),source=html.unescape(paragraphs[2])))
 assert len(figures)==48
def theme(f):
 c=f['category']
 if c in ['문제 배경','신고·시간']:return '신고 규모·시간'
 if c in ['선택 영향','지역 확장·시간 검증']:return '자료·검증'
 if c=='주민 배경':return '주민·건강'
 if c in ['상권','생활인구']:return '상권·생활인구'
 if c=='주택·시설':return '주택·소방자원'
 return '현장·기존 대응'
core={1,2,6,17,23,31,34,36,39,43,44,47}
for f in figures:
 f['theme']=theme(f);f['core']=int(f['id'].split('-')[1]) in core
 f['png']='figures/'+f['id']+'.png';f['svg']='figures/'+f['id']+'.svg'
descriptions=[
 ('두 구의 신고 총량은 어떻게 다른가?','부산진구 65,302건, 중구 14,650건. 같은 C 조건으로 부산 16개 구·군을 비교합니다.','2020–2024 · C 신고 건수'),
 ('어떤 유형의 신고가 큰 비중을 차지하는가?','구급 비중은 부산진구 83.7%, 중구 81.7%입니다. 유형별 대응 과제를 좁히는 출발점입니다.','2020–2024 · 각 구 C 신고 전체 대비 비중'),
 ('연도와 포함 조건을 바꿔도 같은 모습인가?','연도별 A·B·C를 함께 비교해 합계에 가려진 변화와 제외 조건의 영향을 확인합니다.','2020–2024 · A/B/C 조건별 신고 건수'),
 ('요일·시간의 집중은 두 구에서 어떻게 다른가?','같은 색 눈금을 사용하고 해당 요일의 달력일수로 나눠 비교합니다.','2020–2024 · C 신고 / 해당 요일 일수'),
 ('월별 변화가 여러 해에 반복되는가?','월 길이를 보정하고 연도를 분리했습니다. 한 해의 정점을 반복적 계절성으로 단정하지 않습니다.','2020–2024 · C 신고 / 해당 월 일수'),
 ('각 구 안에서는 어느 지역명에 모이는가?','원문 동명별 집중을 비교합니다. 여러 행정동에 걸친 명칭은 임의로 나누지 않았습니다.','2020–2024 · C 신고 · 원문 동명'),
 ('구 안에 있는 소방자원은 어느 정도인가?','소재지 기준 센터·인원·차량입니다. 관할과 교대 가용량이 없어 자원 부족을 판정하지 않았습니다.','소방관서 제공 원표 · 기준일 미기재'),
 ('신고에 기록된 센터는 구 경계와 일치하는가?','중구 기록에는 서구 소재 부민·충무센터도 나타납니다. 실제 상호지원 출동 여부는 추가 확인이 필요합니다.','2020–2024 · C 신고의 관할서센터명 구성'),
 ('총량과 주민 규모 대비 신고는 어떻게 다른가?','2024년 고령 주민 비율은 부산진구 23.1%, 중구 32.4%. 주민 규모 대비 신고는 방문객 노출을 반영하지 않습니다.','2024 · 연말 주민 및 C 신고'),
 ('고령 주민 안의 연령 구성은 어떠한가?','겹치지 않는 연령 구간으로 주민 구성을 비교합니다. 신고자의 나이 또는 독거 여부는 알 수 없습니다.','2020–2024 · 연말 주민 연령 구간'),
 ('돌봄·보건 서비스의 실제 범위는 확인됐는가?','대상·시간·정원·이용·대기 자료 확보 현황입니다. 실제 서비스 공백의 크기를 측정한 그림은 아닙니다.','1차 분석 · 지원범위 근거 확보 현황'),
 ('정책 판단 전에 무엇을 더 확인해야 하는가?','접근성·서비스 이용·정책 효과를 판단하기 위한 후속 검증 항목을 정리했습니다.','1차 분석 · 검증 계획')]
for i,src in enumerate(sorted((R/'figures/부산진구-중구-1차분석').glob('*.png')),1):
 title,finding,period=descriptions[i-1];fid=f'district-{i:02d}'
 for ext in ['png','svg']:shutil.copy2(src.with_suffix('.'+ext),P/f'figures/{fid}.{ext}')
 figures.append(dict(id=fid,title=title,finding=finding,period=period,source='부산진구·중구 1차 분석 · 2026-09-17 검증',category='부산진구·중구',theme='부산진구·중구',core=i in {1,2,4,7,8,9},png=f'figures/{fid}.png',svg=f'figures/{fid}.svg'))
assert len(figures)==60
def page(title,body,script=''):
 return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · 부산 안전나침반</title><link rel="stylesheet" href="complete.css"><link rel="stylesheet" href="../../assets/result-workspace.css"><link rel="stylesheet" href="content-refresh.css"></head><body><header class="site-header"><a class="brand" href="../../index.html">부산 안전나침반</a><nav><a href="index.html">최종 결과</a><a href="gallery.html">그림 모음</a></nav></header><main id="content">{body}</main><script src="complete.js"></script>{script}</body></html>'
def fig(fid,label=None):
 f=next(x for x in figures if x['id']==fid)
 return f'<a class="evidence-figure" href="gallery.html#{fid}"><img loading="lazy" src="{f["png"]}" alt="{esc(f["title"])}"><b>{esc(label or f["title"])}</b><span>그림과 해석 보기 →</span></a>'
def section(id,kicker,title,body):return f'<section id="{id}"><span class="kicker">{kicker}</span><h2>{title}</h2>{body}</section>'
body='''<div class="result-intro"><p class="eyebrow">분석 결과 · 신고 2020–2024</p><h1>어디에 신고가 모이고,<br>어떤 대응을 보완할 것인가</h1><p class="lead">부산 전체의 신고 패턴, 부산진구·중구의 차이, 9개 지역 사례를 연결해 예방·지원의 검토 방향을 정리했습니다.</p><div class="result-metrics"><div><b>574,662<span>건</span></b><small>C 조건 · 5년 신고</small></div><div><b>194<span>개</span></b><small>분석에 연결한 원문 지역명</small></div><div><b>9<span>개</span></b><small>기존 대응을 대조한 설명 사례</small></div></div><nav class="reading-nav"><a href="#city">부산 전체</a><a href="#districts">부산진구·중구</a><a href="#context">지역 배경</a><a href="#cases">대응 제안</a><a href="#next">다음 검증</a></nav></div>'''
body+=section('city','01 · 전체에서 출발','구급이 큰 비중을 차지하지만, 시간 패턴은 다시 확인해야 합니다','''<div class="finding-grid"><article><span>유형 구성</span><h3>C 신고 중 구급 82.55%</h3><p>구급 474,392건, 구조 62,014건, 기타 27,266건, 화재 10,990건입니다. 대분류의 규모를 확인한 뒤 세부유형과 지역을 나눠 봅니다.</p></article><article><span>연도별 변화</span><h3>2022년 126,252건 → 2024년 115,525건</h3><p>C 조건의 관측 건수입니다. 전체 5년 합계와 함께 연도별 변화를 확인해야 증가·감소를 구분할 수 있습니다.</p></article><article><span>시점 분리 검증</span><h3>과거의 최고 계절이 다음 해를 보장하지 않습니다</h3><p>2020–2023년으로 2024년을 대조한 407개 비교에서, 유형별 평균 오차는 단순 기준보다 작지 않았습니다. 특정 계절만으로 인력 배치를 정하지 않았습니다.</p></article></div><p class="basis">C = 선택 17개 완전기재 → 정상 처리 → 업무운행·훈련출동·구급차소독 제외. 지도 기본 A 조건과는 집계 범위가 다릅니다.</p>'''+f'<div class="figure-links">{fig("figure-17")}{fig("figure-34")}{fig("figure-47")}</div><a class="text-link" href="report.html#part-5">전체 수치·선정 기준 →</a>')
body+=section('districts','02 · 부산진구·중구 비교','두 구는 다른 이유로 살펴봐야 합니다','''<div class="district-comparison"><article><span>부산진구 · 신고 총량</span><h3>65,302<small>건 / 5년</small></h3><p>구급 비중 <b>83.7%</b><br>2024년 C 신고 <b>13,264건</b><br>2024년 65세 이상 주민 <b>23.1%</b></p><div class="decision">구급 세부유형과 시간·원문 동별 집중을 좁혀 기존 건강·돌봄 지원의 대상·시간과 대조합니다.</div></article><article><span>중구 · 주민 규모와 연령 배경</span><h3>14,650<small>건 / 5년</small></h3><p>구급 비중 <b>81.7%</b><br>2024년 C 신고 <b>2,510건</b><br>2024년 65세 이상 주민 <b>32.4%</b></p><div class="decision">고령 주민의 생활·지원 여건을 추가로 확인할 지역입니다. 고령자의 신고가 많다고 확정한 결과는 아닙니다.</div></article></div><p>2024년 연말 주민 1천 명 대비 C 신고는 부산진구 36.9건, 중구 66.9건입니다. 주민 외 방문객이 포함된 신고이므로 주민 개인의 발생 위험으로 해석하지 않습니다.</p><div class="decision-note"><b>센터 수만으로 부족을 판단하지 않습니다.</b><p>중구 신고 기록에는 서구 소재 부민·충무119안전센터도 나타납니다. 소재지 기준 자원 수와 실제 관할·상호지원·교대 가용량은 구분해야 합니다.</p></div>'''+f'<div class="figure-links">{fig("district-01")}{fig("district-09")}{fig("district-08")}</div><a class="button secondary" href="district-report.html">두 구의 12개 분석 축과 검증 기록 →</a>')
body+=section('context','03 · 신고 뒤의 지역 여건','같은 지역명 안에서도 생활과 주거 조건은 다릅니다','''<div class="finding-grid"><article><span>상권 · 20분기</span><h3>한 시점보다 같은 분기를 비교</h3><p>2020–2024년 등록목록으로 업종 구성을 비교했습니다. 목록 규모 변화는 실제 개업·폐업과 구분합니다.</p></article><article><span>생활인구 · 2023–2024</span><h3>부전1동 14시, 부전2동 19시</h3><p>방문 생활인구 정점이 두 해 모두 달랐습니다. 같은 ‘부전동’ 신고명에 하나의 활동 시간대를 적용하기 어렵습니다.</p></article><article><span>주택 · 시설</span><h3>주택 형태에 맞춰 지원조건 확인</h3><p>기장·온천의 주택유형과 공시 설비를 비교했습니다. 단독·다세대와 아파트의 지원조건을 구분하는 배경이며, 신고 발생건물을 특정한 자료는 아닙니다.</p></article></div>'''+f'<div class="figure-links">{fig("figure-43")}{fig("figure-44")}{fig("figure-36")}</div>')
cards=''
for c in evidence['cases']:
 url='../followup/explorer.html?'+urlencode(dict(district=c['district'],dong=c['rawDong'],type=c['subtype'],scope='C'))
 uid=c['district']+'|'+c['rawDong']+'|'+c['subtype']
 sources=''.join(f'<a target="_blank" rel="noopener" href="{esc(s["url"])}">{esc(s["title"])} ↗</a>' for s in evidence['sources'].get(uid,[]))
 cards+=f'''<article class="policy-card"><div class="case-meta">{esc(c['district'])}<span>{c['observation']['count']:,}건 · C 5년</span></div><h3>{esc(c['rawDong'])} · {esc(c['subtype'])}</h3><p class="policy-proposal">{esc(c['proposal'])}</p><p class="policy-status">{esc(c['status'])}</p><details><summary>기존 대응과 판단 근거</summary><h4>이미 시행한 대응</h4><p>{esc(c['existingResponse'])}</p><h4>확인한 범위</h4><p>{esc(c['confirmedGap'])}</p><h4>추가로 확보할 자료</h4><ul>{''.join('<li>'+esc(x)+'</li>' for x in c['remainingEvidence'])}</ul><div class="case-sources">{sources}</div></details><a href="{esc(url)}">지역 분석 자세히 →</a></article>'''
body+=section('cases','04 · 지역별 대응','새 시설을 제안하기 전에, 기존 대응과 남은 근거를 대조했습니다','<p>아래 9개는 설명 사례입니다. 운영정보는 2026-09-16까지 확인한 기록이며, 신청·운영 가능 여부는 각 공식 안내에서 확인합니다.</p><div class="policy-grid">'+cards+'</div>')
policies=json.loads(text(P/'policy-proposals.json'))
policy_cards=''
for i,c in enumerate(policies['proposals'],1):
 policy_cards+=f'''<article class="proposal-card" id="proposal-{i}"><div class="proposal-top"><span>제안 {i:02d} · {esc(c['area'])}</span><span class="proposal-tag">시범사업 후보</span></div><h3>{esc(c['title'])}</h3><p class="proposal-aim">{esc(c['aim'])}</p><div class="proposal-basis"><b>분석 근거</b><p>{esc(c['evidence'])}</p><a href="gallery.html#{c['figure']}">연결된 분석 그림 →</a></div><h4>대상</h4><p>{esc(c['target'])}</p><h4>실행 흐름</h4><ol class="proposal-steps">{''.join('<li>'+esc(x)+'</li>' for x in c['steps'])}</ol><h4>기존 사업과의 차이</h4><p>{esc(c['difference'])}</p><details><summary>협력 주체·시행 조건·성과 확인</summary><h4>협력 주체</h4><p>{esc(c['partners'])}</p><h4>시행 전 확인</h4><p>{esc(c['prerequisite'])}</p><h4>어떻게 평가하나요?</h4><p>{esc(c['measure'])}</p></details></article>'''
body=body.replace('<a href="#next">다음 검증</a>','<a href="#policy">정책 제안</a><a href="#next">추진 조건</a>')
body+=section('policy','05 · 분석에서 정책으로','기존 서비스를 연결하는 세 가지 정책 후보',f'<p class="proposal-state">{esc(policies["status"])}</p><p>신규 시설·인력 수량을 먼저 정하기보다, 대상과 운영 공백을 확인한 뒤 작은 범위에서 실행·평가할 제안입니다.</p><div class="proposal-list">{policy_cards}</div>')
body+=section('next','06 · 단계별 추진 조건','근거 확인 → 시범 운영 → 평가 후 확대','''<div class="finding-grid"><article><span>1단계 · 착수 판단</span><h3>기존 사업과 실제 수요 확인</h3><p>지원 대상·시간·정원·대기 및 관할·가용량 자료를 확보합니다. 담당기관·자료 범위·동의 절차를 합의하고, 기존 사업으로 해결할 수 있는 부분을 먼저 정리합니다.</p></article><article><span>2단계 · 제한된 시범</span><h3>대상과 업무 범위를 명시</h3><p>시범 생활권·참여 규모·기간·예산·담당 역할을 협의해 정합니다. 시작 전에 비교 기준과 중단 조건을 정하고, 참여자 부담과 안전 문제를 함께 기록합니다.</p></article><article><span>3단계 · 유지·수정·확대 판단</span><h3>연결 완료와 이용 결과 평가</h3><p>기존 방식 또는 유사 생활권과 같은 기간으로 비교합니다. 신고 감소를 곧바로 성공으로 보지 않고 이용 완료·소요시간·미연결 사유를 확인해 다음 단계를 결정합니다.</p></article></div>''')
body+=section('basis','자료와 해석 기준','상세 근거는 한곳에서 확인할 수 있습니다','''<details><summary>자료 범위·선택 영향</summary><p>원신고 4,552,768행 중 부산 명시·선택 17개 완전기재 A 704,689행, 정상 처리 B 579,412행, 업무성 기록 제외 C 574,662행입니다. 결측 제외에 따른 접수경로·지역 구성 변화가 있어 전체 신고의 대표성을 보장하지 않습니다.</p><p>신고 지역명, 주민 행정동, 상권 법정동과 현재 경계의 단위를 구분합니다. 신고 건수는 사건·환자·출동 건수가 아닙니다.</p></details><div class="actions"><a class="button" href="gallery.html">핵심 그림 보기</a><a class="button secondary" href="data.html">기존 집계표 73개</a><a class="text-link" href="report.html">전체 통합 보고서 →</a><a class="text-link" href="district-report.html">부산진구·중구 추가 분석 →</a></div>''')
(P/'index.html').write_text(page('최종 결과',body),encoding='utf-8')
themes=['전체','부산진구·중구','신고 규모·시간','주민·건강','상권·생활인구','주택·소방자원','현장·기존 대응','자료·검증']
gallery='''<div class="result-intro"><p class="eyebrow">분석 그림 모음</p><h1>질문에 맞는 근거를 찾아보세요</h1><p class="lead">핵심 그림 18개로 시작하고, 전체 60개에서 지역·주제별 결과를 더 살펴볼 수 있습니다.</p></div><div class="gallery-tools"><div class="library-mode" role="group" aria-label="그림 범위"><button data-mode="core" aria-pressed="true">핵심 18개</button><button data-mode="all" aria-pressed="false">전체 60개</button></div><label class="gallery-search">그림 검색<input id="figure-search" type="search" placeholder="부산진구, 중구, 시간, 고령, AED…"></label><div class="topic-filters" role="group" aria-label="분석 주제">'''+''.join(f'<button data-topic="{t}" aria-pressed="{str(t=="전체").lower()}">{t}</button>' for t in themes)+'''</div><p id="library-count" role="status" aria-live="polite"></p></div><p id="library-empty" hidden>일치하는 그림이 없습니다. 검색어를 줄이거나 전체 그림으로 전환해 주세요.</p><div class="visual-grid curated-grid">'''
for f in figures:
 gallery+=f'''<article class="visual" id="{f['id']}" data-topic="{f['theme']}" data-core="{str(f['core']).lower()}" {'' if f['core'] else 'hidden'}><span class="kicker">{f['theme']}</span><h2>{esc(f['title'])}</h2><button class="thumb" data-image="{f['png']}" data-title="{esc(f['title'])}" aria-label="{esc(f['title'])} 확대"><img loading="lazy" src="{f['png']}" alt="{esc(f['title'])}"></button><p class="figure-finding">{esc(f['finding'])}</p><p class="meta">{esc(f['period'])}</p><details><summary>출처와 파일</summary><p class="meta">{esc(f['source'])}</p><div class="figure-actions"><a download href="{f['png']}">PNG 저장</a><a download href="{f['svg']}">SVG 저장</a></div></details></article>'''
gallery+='''</div><dialog id="image-dialog" aria-labelledby="dialog-title"><div class="dialog-head"><h2 id="dialog-title"></h2><button id="close-image">닫기 · Esc</button></div><div class="image-scroll"><img id="dialog-image" alt=""></div></dialog>'''
(P/'gallery.html').write_text(page('그림 모음',gallery,'<script src="gallery-library.js"></script>'),encoding='utf-8')
# Package the existing supplementary report and its verified figures, without incident data.
md=text(report/'분석보고서.md')
md=re.sub(r'!\[(.*?)\]\(../../figures/부산진구-중구-1차분석/(\d+)_.*?\.png\)',lambda m:f'![{m[1]}](figures/district-{m[2]}.png)',md)
md='\n'.join(line for line in md.splitlines() if '원격 develop' not in line)
md=md.split('## 재현')[0]
table_dir=P/'tables/district';table_dir.mkdir(parents=True,exist_ok=True)
downloads=[]
for source in sorted(report.glob('*.csv')):
 with source.open(encoding='utf-8-sig',newline='') as stream:
  columns=next(csv.reader(stream))
 assert not set(columns)&{'DCLR_RCPT_NO','ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT'},source
 dest=table_dir/source.name;shutil.copy2(source,dest)
 downloads.append(f'<li><a download href="tables/district/{esc(source.name)}">{esc(source.stem)} CSV ↓</a></li>')
supplement='<section><h2>검산용 집계표</h2><p>원본 신고 대신 지역·연도·유형별 집계표를 제공합니다.</p><ul>'+''.join(downloads)+'</ul></section>'
(P/'district-report.html').write_text(page('부산진구·중구 추가 분석','<article class="report">'+mistune.create_markdown(plugins=['table'])(md)+supplement+'</article>'),encoding='utf-8')
inventory.write_text(json.dumps({'reviewed':'2026-09-18','sourceReport':'전체결과보고서.md','supplement':'output/부산진구-중구-1차분석/분석보고서.md','figures':figures},ensure_ascii=False,indent=2),encoding='utf-8')
audit={'inputs':{str(p.relative_to(R)):sha(p) for p in [report/'manifest.json',report/'분석보고서.md',P/'전체결과보고서.md',R/'web/final/data/regional-evidence.js',P/'policy-proposals.json']},'figure_count':len(figures),'core_count':sum(f['core'] for f in figures),'outputs':{f['png']:sha(P/f['png']) for f in figures}}
audit['outputs'].update({str(p.relative_to(P)):sha(p) for p in [P/'index.html',P/'gallery.html',P/'district-report.html',*table_dir.glob('*.csv')]})
(P/'content-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print('Built final results, 60 figures (18 core), district supplement; verified local output hashes.')
