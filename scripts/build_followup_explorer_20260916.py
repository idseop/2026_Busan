"""A local-file compatible explorer for the full verified region catalogue."""
from pathlib import Path
import json,hashlib,shutil,csv
ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'data/processed/후속입증-20260916'
OUT=ROOT/'output/부산119-전지역후속검증-20260916';OUT.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
d=read(B/'analysis/all-region-followup.json')
dashpath=ROOT/'data/processed/최종결과-20260915/dashboard.json';dash=read(dashpath)
oldmanifest=read(dashpath.parent/'manifest.json')
assert hashlib.sha256(dashpath.read_bytes()).hexdigest()==next(x['sha256'] for x in oldmanifest['outputs'] if x['path'].endswith('/dashboard.json'))
d['population']=dash['population']
d['populationLinks']=[{k:r[k] for k in ['year','district','rawDong','candidateCodes']} for r in dash['rawRegions'] if r['scope']=='C']
d['trafficFollowup']=read(B/'traffic/traffic-followup.json')['sites']
d['fieldStudy']=read(B/'traffic/bdi-field-study.json')['areas']
d['outdoor']=read(B/'outdoor/outdoor-evidence.json')
d['services']=read(B/'services/followup-services-evidence.json')['facts']
d['facilityAddressCandidates']=list(csv.DictReader((B/'traffic/facility-address-candidates.csv').open(encoding='utf-8-sig')))
d['commerce']=read(B/'commerce/commerce-context.json')['profiles'] if (B/'commerce/commerce-context.json').exists() else []
d['living']=read(B/'living/living-context.json')['allDongProfiles'] if (B/'living/living-context.json').exists() else []
csvrows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
d['commerceCategories']=[x for x in csvrows(B/'commerce/four-law-dong-categories.csv') if x['snapshot']=='20240930']
housingNames={'기장읍','온천1동','온천2동','온천3동'}
d['housingRows']=[x for x in csvrows(B/'housing/busan_housing_context_2024.csv') if x['name'] in housingNames and x['level']=='dong']
d['housingAudit']=[x for x in csvrows(B/'housing/housing_sum_audit.csv') if x['name'] in housingNames and x['level']=='dong']
serviceBase=ROOT/'data/processed/동별보완-추가근거-20260916/services'
d['aedPublicHours']=read(serviceBase/'aed-summary.json')
d['apartmentSprinklers']=read(serviceBase/'apartment-summary.json')
complete=ROOT/'data/processed/통합완성-20260916'
d['currentCaseResults']=read(complete/'evidence/case-assessments.json')
d['currentCaseSources']=[{k:x[k] for k in ['id','url'] if k in x} for x in read(complete/'evidence/source-log.json')]
context=complete/'context'
rawNames={(x['district'],x['rawDong']) for x in d['catalogue']}
totals=[x for x in csvrows(context/'commerce-all-geographies-total.csv') if x['level']=='lawDong' and (x['district'],x['lawDong']) in rawNames]
codes={}
for x in totals:codes.setdefault((x['district'],x['lawDong']),set()).add(x['lawDongCode'])
matched={k for k,v in codes.items() if len(v)==1}
numfields=['shops','denominatorShops','sharePct','busanSharePct','districtSharePct','differenceFromBusanPP','differenceFromDistrictPP']
d['commerceLong']={}
for x in csvrows(context/'commerce-law-dong-comparisons.csv'):
 key=(x['district'],x['lawDong'])
 if key not in matched:continue
 row=[x['category']]+[float(x[k]) if x[k] else None for k in numfields]
 d['commerceLong'].setdefault('|'.join(key),{}).setdefault(x['snapshot'],[]).append(row)
d['commerceTotals']={}
for x in totals:
 if (x['district'],x['lawDong']) in matched:d['commerceTotals'].setdefault(x['district']+'|'+x['lawDong'],[]).append([x['snapshot'],int(x['shops'])])
d['livingYears']={}
for kind,filename,label in [('hours','living-hour-annual-equal-month-means.csv','시간대'),('ages','living-age-annual-equal-month-means.csv','나이대')]:
 for x in csvrows(context/filename):
  row=d['livingYears'].setdefault(x['year'],{}).setdefault(x['행정동코드'],{'name':x['행정동명'].strip() or x['행정동코드'],'nameMissing':x['nameMissing']=='True','observedMonths':int(x['observedMonths']),'hours':[],'ages':[]})
  assert row['observedMonths']==int(x['observedMonths']), 'Different observation month denominator within code/year'
  row[kind].append([x[label]]+[float(x['평균'+name+'인구수']) for name in ['주거','직장','방문']])
newbase=ROOT/'data/processed/고도화검증-20260916'
d['selectionDiagnostics']=list(csv.DictReader((newbase/'selection/same_mobile_comparison.csv').open(encoding='utf-8-sig'))) if (newbase/'selection/same_mobile_comparison.csv').exists() else []
d['selectionDiagnostics']=[{k:x[k] for k in ['CLMTY_SGG_NM','CLMTY_EMD_NM','EMRG_RSCU_CLSF_NM','scope','period','beforeAll','beforeMobile','afterMobile','beforeWeekendRatio','afterWeekendRatio']} for x in d['selectionDiagnostics'] if x['period']=='2020–2024']
d['serviceConditions']=read(newbase/'education/service-conditions.json')['records'] if (newbase/'education/service-conditions.json').exists() else []
d['updatedTraffic']=read(newbase/'traffic/traffic-resolution.json')['facts'] if (newbase/'traffic/traffic-resolution.json').exists() else []
d['updatedTrafficSources']=read(newbase/'traffic/source-manifest.json') if (newbase/'traffic/source-manifest.json').exists() else []
transferPath=ROOT/'data/processed/효과근거확장-20260916/temporal/temporal-transfer.json'
d['temporalProfiles']=[{k:v for k,v in x.items() if k!='windows'}|{'allWindow':x['windows'][0],'leaveOneWindows':[{'excludedYear':int(w['window'].split('_')[1]),'topMonths':w['topMonths'],'topSeasons':w['topSeasons']} for w in x['windows'][6:]]} for x in read(transferPath)['profiles']] if transferPath.exists() else []
populationContext=ROOT/'data/processed/최종논리검증-20260916/population/prevention-population.json'
d['populationChanges']=read(populationContext)['changes'] if populationContext.exists() else []
educationPath=ROOT/'data/processed/효과근거확장-20260916/context/chs-education-summary.json'
d['residentEducation']=read(educationPath) if educationPath.exists() else None
cprPath=ROOT/'data/processed/효과근거확장-20260916/services/cpr-trend.json'
d['cityCprContext']=read(cprPath) if cprPath.exists() else None
if educationPath.exists():
 shutil.copy2(educationPath.parent/'chs2024-cpr-education.csv',OUT/'chs2024-cpr-education.csv')
if (B/'living/living_hour_context.png').exists():shutil.copy2(B/'living/living_hour_context.png',OUT/'living_hour_context.png')
for p in d['population']:assert len(p['ages'])==101 and sum(p['ages'])==p['total']
(OUT/'explorer-data.js').write_text('window.FOLLOWUP='+json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False)+';',encoding='utf-8')
page='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>부산 119 · 전 지역 결과 탐색</title>
<style>*{box-sizing:border-box}body{margin:0;font:16px/1.65 system-ui,"Malgun Gothic",sans-serif;background:#f1f6f5;color:#153a43}header{padding:18px 30px;background:#143e49;color:white;display:flex;align-items:center;justify-content:space-between}header a{color:white}h1{font-size:24px;margin:0}.layout{display:grid;grid-template-columns:320px minmax(0,1fr);height:calc(100vh - 78px)}aside{background:white;border-right:1px solid #d5e3df;display:flex;flex-direction:column;padding:22px 18px;overflow:hidden}label{display:block;font-size:15px;font-weight:600;margin-bottom:14px}input,select{width:100%;font:inherit;border:1px solid #b2c9c3;border-radius:5px;padding:9px;margin-top:5px;background:white;color:#153a43}button{font:inherit;cursor:pointer}#list{overflow:auto;flex:1;margin-top:12px}#list button{display:block;text-align:left;width:100%;border:0;background:white;border-bottom:1px solid #e4eeeb;padding:14px 12px}#list button[aria-pressed=true]{background:#dcefe8;border-left:4px solid #13806d}#list small{display:block;color:#52716e}.content{overflow:auto;padding:25px 40px}h2{font-size:30px;margin:8px 0}h3{font-size:21px;margin-top:28px}.number{font-size:40px;font-weight:750;color:#086f66}.number span{font-size:16px;font-weight:400;color:#486863}.muted{color:#52706e;font-size:14px}.split{display:grid;grid-template-columns:1fr 1fr;gap:30px}.fact{border-left:4px solid #2a8a78;padding:10px 18px;margin:20px 0;background:white}.chart{width:100%;height:auto;background:#fff}table{border-collapse:collapse;width:100%;background:#fff}td,th{padding:8px;text-align:left;border-bottom:1px solid #e2eae8}section{padding-bottom:25px;border-bottom:1px solid #ccded8}a{color:#08746c}.popcontrols{display:flex;gap:20px;max-width:600px}.popcontrols label{flex:1}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #cf8827;outline-offset:2px}@media(max-width:1000px){.layout{grid-template-columns:270px 1fr}.content{padding:20px}.split{grid-template-columns:1fr}}</style>
<header><h1>부산 119 · 지역별 결과</h1><nav aria-label="결과 탐색"><a href="../final/index.html">최종 결과</a> · <a href="../../index.html">부산 지도</a> · <a href="../final/gallery.html">그림 모음</a></nav></header>
<div class="layout"><aside><label>지역 검색<input id="search" placeholder="구·군 또는 동명 검색"></label><label>구·군<select id="district"></select></label><label>신고 유형<select id="subtype"></select></label><label>처리 조건<select id="scope"><option value="C">정상 처리 · 운영성 제외</option><option value="B">정상 처리</option><option value="A">모든 처리 결과</option></select></label><p class="muted">2020–2024 전체 기간 · 이름순<br>194개 지역명, 예방 관련 5개 유형</p><div id="resultcount" aria-live="polite"></div><div id="list"></div></aside><main class="content" id="detail" aria-live="polite"></main></div>
<script src="explorer-data.js"></script><script>
const d=window.FOLLOWUP,$=id=>document.getElementById(id),esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),num=x=>Number(x).toLocaleString('ko-KR'),pct=x=>x==null?'비교 자료 없음':(x*100).toFixed(1)+'%';
let selected='부산진구|부전동',popYear=2024,popCode='';
const gu=[...new Set(d.catalogue.map(r=>r.district))],types=[...new Set(d.catalogue.map(r=>r.subtype))];
$('district').innerHTML='<option value="">부산 전체</option>'+gu.map(x=>`<option>${esc(x)}</option>`).join('');
$('subtype').innerHTML=types.map(x=>`<option ${x==='교통사고'?'selected':''}>${esc(x)}</option>`).join('');
const params=new URLSearchParams(location.search),requestedGu=params.get('district'),requestedType=params.get('type'),requestedDong=params.get('dong'),requestedScope=params.get('scope');
if(gu.includes(requestedGu))$('district').value=requestedGu;
if(types.includes(requestedType))$('subtype').value=requestedType;
if(['A','B','C'].includes(requestedScope))$('scope').value=requestedScope;
if(requestedDong&&d.catalogue.some(x=>x.rawDong===requestedDong&&(!requestedGu||x.district===$('district').value))){$('search').value=requestedDong;const match=d.catalogue.find(x=>x.rawDong===requestedDong&&(!$('district').value||x.district===$('district').value));selected=match.district+'|'+match.rawDong;}
function series(values,labels,kind='line'){
 const W=680,H=210,P=35,M=Math.max(1,...values),step=(W-P*2)/Math.max(1,values.length-1);
 let s=`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${kind==='line'?'5년 접수 변화':'시간별 접수 분포'}">`;
 s+=`<line x1="${P}" y1="${H-P}" x2="${W-P}" y2="${H-P}" stroke="#b9ceca"/>`;
 if(kind==='line'){s+=`<polyline fill="none" stroke="#168573" stroke-width="3" points="${values.map((v,i)=>`${P+i*step},${H-P-v/M*(H-P*2)}`).join(' ')}"/>`;}
 values.forEach((v,i)=>{let x=P+i*step,y=H-P-v/M*(H-P*2);if(kind==='line')s+=`<circle cx="${x}" cy="${y}" r="4" fill="#168573"/><text x="${x}" y="${Math.max(15,y-9)}" text-anchor="middle" font-size="14">${num(v)}</text>`;else s+=`<rect x="${x-step*.32}" y="${y}" width="${Math.max(2,step*.64)}" height="${H-P-y}" fill="#168573"><title>${labels[i]}: ${num(v)}건</title></rect>`;if(values.length<=12||i%4===0)s+=`<text x="${x}" y="${H-10}" text-anchor="middle" font-size="13">${labels[i]}</text>`;});return s+'</svg>';
}
function valueTable(kind,headers,rows,label){
 const id=kind+'-values';return `<button type="button" aria-expanded="false" aria-controls="${id}" data-value-toggle>${esc(label)}</button><div id="${id}" hidden tabindex="0" role="region" aria-label="${esc(label)}" style="max-height:320px;overflow:auto;margin-top:12px"><table data-${kind}-table><thead><tr>${headers.map(x=>`<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>'<tr>'+row.map(x=>`<td>${esc(x)}</td>`).join('')+'</tr>').join('')}</tbody></table></div>`;
}
$('detail').addEventListener('click',e=>{const b=e.target.closest('[data-value-toggle]');if(!b)return;const panel=$(b.getAttribute('aria-controls')),open=b.getAttribute('aria-expanded')==='true';b.setAttribute('aria-expanded',String(!open));panel.hidden=open;});
function render(){
 let q=$('search').value.trim();let rr=d.catalogue.filter(r=>r.scope===$('scope').value&&r.subtype===$('subtype').value&&(!$('district').value||r.district===$('district').value)&&(!q||(r.district+' '+r.rawDong).includes(q)));
 $('resultcount').textContent=`${rr.length}개 지역 · ${num(rr.reduce((a,r)=>a+r.count,0))}건`;
 if(!rr.some(r=>r.district+'|'+r.rawDong===selected)){selected=rr.length?rr[0].district+'|'+rr[0].rawDong:'';popCode='';}
 $('list').innerHTML=rr.map(r=>`<button data-key="${esc(r.district+'|'+r.rawDong)}" aria-pressed="${selected===r.district+'|'+r.rawDong}"><strong>${esc(r.rawDong)}</strong> · ${num(r.count)}건<small>${esc(r.district)}</small></button>`).join('');
 $('list').querySelectorAll('button').forEach(b=>b.onclick=()=>{selected=b.dataset.key;popCode='';render();});
 let r=rr.find(r=>r.district+'|'+r.rawDong===selected);if(!r){$('detail').innerHTML='<h2>검색 결과 없음</h2><p>검색어나 구·군 조건을 변경해 주세요.</p>';return;}
 const all=d.catalogue.filter(x=>x.district===r.district&&x.rawDong===r.rawDong&&x.type===r.type&&x.subtype===r.subtype);
 const stable=all.every(x=>x.repeatedBefore&&x.repeatedAfter&&!x.directionReversal);
 let p=r.weekendRatio2020_2022,z=r.weekendRatio2023_2024;
 let sites=r.subtype==='교통사고'?d.inspectionSites.filter(s=>s.district===r.district&&(s.rawRegionComparisons.some(x=>x.rawDong===r.rawDong)||d.facilityAddressCandidates.some(x=>x.inspectionPlace===s.place&&x.district===r.district&&x.rawDongCandidate===r.rawDong))):[];
 let field=r.subtype==='교통사고'?d.fieldStudy.filter(x=>x.district===r.district&&x.placeNameDongContext===r.rawDong):[];
 let outdoors=d.outdoor.filter(x=>x.case.startsWith(r.rawDong)&&((r.subtype==='산악사고'&&x.case.includes('산악'))||(r.subtype==='수난사고'&&x.case.includes('수난'))));
 let services=d.services.filter(x=>((r.subtype==='심정지'&&x.id.includes('aed'))||(r.subtype==='심정지'&&x.id.includes('register'))||(r.subtype==='심정지'&&x.id.includes('rental'))||(r.subtype==='일반화재(주택)'&&x.id.includes('fire')))&&(x.region.includes(r.district)||x.region.includes(r.rawDong)||x.region==='부산 전체'||(x.id==='dongnae-fire2026'&&r.district==='동래구')));
 let evidence=sites.map(s=>{let f=d.trafficFollowup.find(x=>x.place===s.place);return `<div class="fact"><strong>${esc(s.place)}</strong><p>2023 현장점검: 단기 개선 ${s.shortTermItems}항목 · 중장기 ${s.longTermItems}항목</p><p>${esc(f?.confirmedFollowup||'후속 자료 미확보')}</p><small>지역명 배경 비교이며 위 신고를 이 지점의 사고로 배정하지 않았습니다.</small></div>`;}).join('');
 evidence+=field.map(f=>`<div class="fact"><strong>${esc(f.area)} · 부산연구원 현장연구</strong><p>2024년 조사 ${f.surveySegments}구간, 보차 미분리 ${f.unseparatedSegments}구간. 체험복 착용 조건 평균시간 변화 ${f.publishedTimeChangePct}%.</p><small>30대 조사원 체험복 실험이며 실제 고령자 보행속도나 현재 상태를 뜻하지 않습니다.</small></div>`).join('');
 if(r.subtype==='교통사고')evidence+=d.commerce.filter(x=>x.district===r.district&&x.rawDong===r.rawDong).map(x=>`<div class="fact"><strong>동 전체의 상권 배경 · 2024년 9월 말</strong><p>등록업소 ${num(x.shops)}개 · 음식 ${num(x.foodShops)}개 · 소매 ${num(x.retailShops)}개. 음식·소매 합계 ${x.foodRetailSharePct.toFixed(1)}%.</p><small>시장·역 조사구간에 배정한 업소 수나 방문량이 아닙니다.</small><p><a href="https://www.data.go.kr/data/15083033/fileData.do">공식 상권자료</a></p></div>`).join('');
 evidence+=outdoors.map(x=>`<div class="fact"><strong>${esc(x.place)}</strong><p>${esc(x.finding)}</p><p>${esc(x.candidate)}</p><small>${esc(x.period)} · ${esc(x.status)}</small><p><a href="${esc(x.sourceUrl)}">공식 근거</a></p></div>`).join('');
 evidence+=services.map(x=>`<div class="fact"><strong>${esc(x.region)} · ${esc(x.status)}</strong><p>${esc(x.result)}</p><small>${esc(x.period)}</small><p><a href="${esc(x.url)}">공식 근거</a></p></div>`).join('');
 if(!evidence)evidence='<p>이 지역·유형은 신고 패턴까지 확인했습니다. 지역에 직접 연결한 운영·개선 결과는 현재 수집 범위에 없습니다.</p>';
 $('detail').innerHTML=`<section><p class="muted">${esc(r.district)} · 해당 지역명으로 접수된 신고 · 2020–2024</p><h2>${esc(r.rawDong)} · ${esc(r.subtype)}</h2><div class="number">${num(r.count)} <span>건 / 지역 전체 선택 신고 ${num(r.regionAllTypes)}건 중 ${pct(r.regionShare)}</span></div><p>${r.count?`${r.yearCounts.filter(x=>x>0).length}개 연도에 접수 기록이 있습니다.`:'이 조건에서 관측된 신고가 없습니다. 실제 사고가 없다는 뜻은 아닙니다.'} ${stable?'세 처리조건에서 제외 전후 5년 반복·증감 방향이 유지됐습니다.':'결측 제외·처리조건에 민감하거나 5년 반복 조건을 충족하지 않았습니다.'}</p><p class="muted">적용 조건: ${esc($('scope').selectedOptions[0].textContent)} · 제외 전 비교 집합 대비 잔존율 ${pct(r.retention)}</p></section><section><h3>5년 변화</h3>${series(r.yearCounts,['2020','2021','2022','2023','2024'])}<div class="split"><div><h3>월별 분포 · 5년 합계</h3>${series(r.monthCounts,Array.from({length:12},(_,i)=>(i+1)+'월'),'bar')}</div><div><h3>접수 시각 · 5년 합계</h3>${series(r.hourCounts,Array.from({length:24},(_,i)=>i+'시'),'bar')}</div></div><p>주말/평일 하루 평균 비율: 2020–22 ${p==null?'비교 불가':p.toFixed(2)+'배'} → 2023–24 ${z==null?'비교 불가':z.toFixed(2)+'배'}.</p><p class="muted">월·시각 그래프는 건수입니다. 주말 비교에만 각 기간의 달력 일수를 적용했습니다.</p></section><section><h3>주민 연령 구성</h3><div class="popcontrols"><label>주민 자료 연도<select id="pop-year">${[2020,2021,2022,2023,2024].map(y=>`<option ${y===popYear?'selected':''}>${y}</option>`).join('')}</select></label><label>주민 통계 지역<select id="pop-code"></select></label></div><div id="population"></div></section><section><h3>현장과 기존 대응 결과</h3>${evidence}<p class="muted">현재 시설·운영 자료를 과거 신고 당시 상태로 취급하지 않습니다. 확정한 시설·인력 증설안은 없습니다.</p></section>`;
 const hourChart=$('detail').querySelectorAll('.split > div')[1];hourChart.insertAdjacentHTML('beforeend',valueTable('hours',['접수 시각','건수','선택 신고 중 비중'],r.hourCounts.map((n,i)=>[i+'시',num(n)+'건',r.count?(n/r.count*100).toFixed(2)+'%':'분모 없음']),'24시간 수치표'));
 $('pop-year').onchange=()=>{popYear=Number($('pop-year').value);popCode='';renderPopulation(r);};renderPopulation(r);renderUpdatedEvidence(r);renderTemporalTransfer(r);renderResidentEducation(r);renderAdditionalContext(r);
}

function renderTemporalTransfer(r){
 const p=(d.temporalProfiles||[]).find(x=>x.district===r.district&&x.rawDong===r.rawDong&&x.subtype===r.subtype&&x.type===r.type);
 if(!p)return;
 const anchor=$('selection-update')||$('detail').firstElementChild;
 if(r.scope!=='C'){anchor.insertAdjacentHTML('afterend','<section id="temporal-transfer"><h3>월·계절의 연도별 비교</h3><p>정상 처리·운영성 제외 조건에서 제공하는 별도 비교입니다. 해당 조건을 선택하면 표시됩니다.</p></section>');return;}
 if(!p.count){anchor.insertAdjacentHTML('afterend','<section id="temporal-transfer"><h3>월·계절의 연도별 비교</h3><p>이 조건의 접수 기록이 없어 최고 시기를 계산하지 않았습니다.</p></section>');return;}
 const months=p.topMonths.map(m=>m+'월').join('·'),seasons=p.topSeasons.join('·'),w=p.allWindow;
 let body=`<section id="temporal-transfer"><h3>반복된 시기와 연도별 차이</h3><p>전체 기간의 달력일수당 접수가 가장 많은 시기: <strong>${esc(months)} / ${esc(seasons)}</strong></p><p>한 해씩 제외한 5번의 비교에서 같은 최고월 ${p.leaveOneMonthExact}/5회 · 같은 최고계절 ${p.leaveOneSeasonExact}/5회.</p><table data-season-table><caption>2020–2024 · 정상 처리·운영성 제외 · 해당 지역명 접수</caption><thead><tr><th>계절</th><th>접수</th><th>달력일수</th><th>일수당 접수</th></tr></thead><tbody>${['봄','여름','가을','겨울'].map((name,i)=>`<tr><th>${name}</th><td>${num(w.seasonCounts[i])}건</td><td>${num(w.seasonCalendarDays[i])}일</td><td>${w.seasonPerCalendarDay[i].toFixed(3)}건/일</td></tr>`).join('')}</tbody></table><p>${p.leaveOneSeasonExact===5?'최고계절은 다섯 비교에서 유지됐습니다. 기존 운영기간과 대조할 배경으로 활용합니다.':'최고계절이 제외한 연도에 따라 달라집니다. 한 계절에만 예방·지원을 집중하는 근거로 사용하지 않습니다.'}</p><p class="muted">겨울은 각 연도의 1·2·12월입니다. 최고월과 3개월 묶음 최고계절은 다를 수 있습니다. 달력일수당 접수는 주민 위험률이나 미래 예측이 아닙니다.</p><p><a href="../effects/index.html#temporal">시기 비교의 전체 결과</a></p></section>`;
 anchor.insertAdjacentHTML('afterend',body);
}

function renderResidentEducation(r){
 if(r.subtype!=='심정지')return;
 const rows=(d.residentEducation?.records||[]).filter(x=>x.district===r.district&&x.subgroup==='전체');
 let html='<section id="resident-education-context"><h3>주민 교육 경험과 실제 초기대응</h3>';
 if(rows.length){
  html+=`<h4>${esc(r.district)} 전체 주민 조사 · 2024년</h4><p>19세 이상 응답자 ${num(rows[0].sampleN)}명 표본에서 최근 2년 교육·실습 경험을 조사했습니다. 아래 값은 <strong>${esc(r.rawDong)}만의 결과가 아닌 ${esc(r.district)} 전체 추정치</strong>입니다.</p><table data-education-context><caption>가중치 적용 조율 · 분모: 각 지표의 조사대상 응답자</caption><thead><tr><th>경험</th><th>경험률</th><th>표준오차</th></tr></thead><tbody>${rows.map(x=>`<tr><th>${esc(x.indicator)}</th><td>${x.crudeWeightedPercent.toFixed(1)}%</td><td>${x.standardErrorPP.toFixed(1)}%p</td></tr>`).join('')}</tbody></table><p class="muted">실습률도 교육경험자가 아닌 조사대상 응답자를 분모로 합니다. 표준오차는 신뢰구간이 아닙니다. 연령을 표준화한 구 순위나 미충족 교육 수요로 해석하지 않습니다.</p><p>교육과 실제 장비 실습을 구분해 안내합니다. 교육 경험은 환자의 나이·현재 수행능력·교육 부족의 원인을 뜻하지 않습니다.</p><p><a href="chs2024-cpr-education.csv">교육·실습 집계표</a> · <a href="https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do">질병관리청 지역사회 건강통계</a></p>`;
 }
 const city=(d.cityCprContext?.rows||[]).find(x=>x.region==='부산'&&x.year===2024);
 if(city){html+=`<h4>부산 전체 환자 조사 · 2024년</h4><p>기록된 일반인 심폐소생술 시행률은 <strong>${city.cpr_rate_percent.toFixed(1)}%</strong>입니다. 119구급대 이송 급성심장정지 환자 중 의무기록조사가 완료된 자료로, 근무 중 구급대원·의료인이 발견·목격한 경우는 제외합니다.</p><p class="muted">발생장소 기준의 부산 전체 자료이며 ${esc(r.rawDong)} 비율이 아닙니다. 위 주민 교육 조사, 선택 신고 ${num(r.count)}건, 주민 인구와 분모가 다릅니다. 병원 기록상 시행률로 실제 시행보다 낮게 추정될 수 있으며, 이 웹의 효과가 아닙니다.</p><p><a href="${esc(d.cityCprContext.source)}">질병관리청 급성심장정지조사 통계</a></p>`;}
 html+='<p class="muted">교육·환자 조사는 2024년 고정 자료입니다. 신고 처리조건이나 주민 인구 연도 선택에 따라 이 비율이 바뀌지 않습니다.</p></section>';
 if(rows.length||city){const anchor=$('service-update');if(anchor)anchor.insertAdjacentHTML('beforebegin',html);else $('detail').insertAdjacentHTML('beforeend',html);}
}
function renderUpdatedEvidence(r){
 let story='';
 if(r.district==='연제구'&&r.rawDong==='연산동'&&r.subtype==='심정지'&&r.count)story=`선택 조건에서 심정지 관련 접수 ${num(r.count)}건을 확인했습니다. 기존 AED 조회와 동래소방서의 교육용 기자재 대여가 있어, 응급환자용 장비·연습 장비·수료증 과정을 구분한 공식 안내를 연결했습니다. 이용량이나 장비 부족을 판정한 결과는 아닙니다.`;
 const project=(d.updatedTraffic||[]).find(x=>x.district===r.district&&x.rawDongBackground===r.rawDong&&['bujeon-2026','gwangan-2025-payment'].includes(x.id));
 if(r.subtype==='교통사고'&&project&&r.count)story=`선택 조건에서 교통사고 관련 접수 ${num(r.count)}건을 확인했습니다. ${project.id==='bujeon-2026'?'부전역 맞이길은 2026년 제막식 기록':'광안역 수영로 포장사업은 2025년 검사·준공금 지급'}이 있어, 과거 조사와 이후 사업을 함께 표시했습니다. 조사구간 전체가 해결되었거나 현재 미개선이라는 단정 없이 확인된 사업 단계와 출처를 제공합니다.`;
 if(story)$('detail').firstElementChild.insertAdjacentHTML('beforeend',`<p data-result-story>${esc(story)}</p>`);
 const n=x=>x===''||x==null?null:Number(x),ratio=x=>n(x)==null?'비교 불가':n(x).toFixed(3)+'배';
 const s=d.selectionDiagnostics.find(x=>x.CLMTY_SGG_NM===r.district&&x.CLMTY_EMD_NM===r.rawDong&&x.EMRG_RSCU_CLSF_NM===r.subtype&&x.scope===r.scope&&x.period==='2020–2024');
 if(s){const note=`<section id="selection-update"><h3>같은 이동전화에서도 확인한 특징</h3><p>비교 집합 ${num(s.beforeAll)}건 → 그중 이동전화 ${num(s.beforeMobile)}건 → 결측 제외 후 이동전화 ${num(s.afterMobile)}건.</p><p>주말/평일 하루 평균 비율: ${ratio(s.beforeWeekendRatio)} → ${ratio(s.afterWeekendRatio)}.</p><p class="muted">2020–2024 · 현재 처리조건의 비교. 위 신고 집합을 바꾸지 않으며, 다른 전화경로를 제거한 영향과 이동전화 내부 제외를 구분합니다.</p></section>`;$('detail').firstElementChild.insertAdjacentHTML('afterend',note);}
 let update='';
 if(r.subtype==='교통사고')update+=(d.updatedTraffic||[]).filter(x=>x.district===r.district&&x.rawDongBackground===r.rawDong).map(x=>`<div class="fact"><strong>${esc(x.place)} · ${esc(x.status)}</strong><p>${esc(x.finding)}</p><p>${esc(x.comparison)}</p><small>${esc(x.limit)}</small><p>${d.updatedTrafficSources.filter(z=>x.sourceIds.includes(z.id)&&z.status==='saved').map(z=>`<a href="${esc(z.url)}">공식 근거</a>`).join(' · ')}</p></div>`).join('');
 if(r.subtype==='심정지')update+='<p>AED 공개목록에는 위치정보와 소모품 유효기간 등에 따른 표출 조건이 있습니다. 지도 미표시를 장비 부재로 판단하지 않습니다. 기존 보건소·설치기관의 정보 수정 절차를 활용합니다.</p><p><a href="https://www.e-gen.or.kr/egen/search_aed.do">공식 AED 찾기</a> · <a href="쟁점해결.html#s4">새로 확인한 표출기준과 이용조건</a></p>';
 const services=(d.serviceConditions||[]).filter(x=>x.type===r.subtype&&(x.area==='부산'||(x.id==='dongnae-training-rental'&&['연제구','동래구'].includes(r.district))||(x.area==='사하구'&&r.district==='사하구')));
 update+=services.map(x=>`<div class="fact"><strong>${esc(x.name)}</strong><p>${esc(x.target)} · ${esc(x.duration)}</p><p>${esc(x.equipment)} · ${esc(x.certificate)}</p><p>${esc(x.condition)}</p><small>${esc(x.status)}</small><p><a href="${esc(x.url)}">공식 안내 확인</a></p></div>`).join('');
 if(services.some(x=>x.id==='dongnae-training-rental'))update+='<p class="muted">동래소방서 대여는 소재지와 관련된 지역 사례로 연결했습니다. 연제구·동래구 주민만 이용할 수 있다는 자격 제한을 뜻하지 않습니다.</p>';
 if(update)$('detail').insertAdjacentHTML('beforeend','<section id="service-update"><h3>추가로 확인한 조치와 이용조건</h3>'+update+'<p class="muted">공식 기록의 안내이며 실시간 운영·예약 재고를 확인한 값은 아닙니다.</p></section>');
}
function renderLiving(r){
 if(!$('living-context'))$('population').closest('section').insertAdjacentHTML('afterend','<section id="living-context"></section>');
 const link=d.populationLinks.find(x=>x.year===2024&&x.district===r.district&&x.rawDong===r.rawDong);
 const rows=(d.living||[]).filter(x=>link?.candidateCodes.includes(x.code));
 $('living-context').innerHTML='<h3>시간에 따라 달라지는 생활인구</h3><p class="muted">2024 기준월 12개의 일평균 값을 동일가중 평균 · 신고 조건과 주민 연도 선택에 영향받지 않는 별도 배경</p>'+(rows.length?`<table><thead><tr><th>행정동</th><th>00시 방문</th><th>12시 방문</th><th>방문 최대시간</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${esc(x.name)}</td><td>${num(Math.round(x.visitor00))}명</td><td>${num(Math.round(x.visitor12))}명</td><td>${esc(x.visitorPeakHour)}</td></tr>`).join('')}</tbody></table><p class="muted">${rows.length>1?'대응 후보를 각각 표시했습니다. 후보 인구를 합산하지 않습니다. ':''}방문 값은 연간 방문자 수·등산객·신고 대상자 수가 아닙니다. 해당 신고의 실제 행정동을 확정한 값도 아닙니다.</p>`:'<p>기존 2024년 지역 연결 후보에서 확인할 수 있는 생활인구 자료가 없습니다.</p>')+'<p><a href="living_hour_context.png" target="_blank" rel="noopener">주거·직장·방문 시간 분포 사례</a> · <a href="https://www.data.go.kr/data/15142761/fileData.do" target="_blank" rel="noopener">공식 자료와 기준</a></p>';
}
function renderPopulation(r){renderLiving(r);let link=d.populationLinks.find(x=>x.year===popYear&&x.district===r.district&&x.rawDong===r.rawDong);let candidates=d.population.filter(x=>x.year===popYear&&link?.candidateCodes.includes(x.code));if(!candidates.some(x=>x.code===popCode))popCode=candidates.length===1?candidates[0].code:'';
 $('pop-code').innerHTML='<option value="">'+(candidates.length?'지역 선택':'연결 자료 없음')+'</option>'+candidates.map(p=>`<option value="${p.code}" ${p.code===popCode?'selected':''}>${esc(p.name)}</option>`).join('');$('pop-code').onchange=()=>{popCode=$('pop-code').value;renderPopulation(r);};
 let p=candidates.find(x=>x.code===popCode);if(!p){$('population').innerHTML=`<p>${candidates.length?'대응 후보 '+candidates.length+'곳을 각각 선택해 볼 수 있습니다. 후보 인구를 합산하지 않습니다.':'해당 연도에 연결 가능한 주민 자료가 없습니다.'}</p>`;return;}
 const W=900,H=230,P=30,M=Math.max(1,...p.ages);let svg=`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="0세부터 100세 이상까지 주민 인원">`;
 p.ages.forEach((n,i)=>{let x=P+i*(W-2*P)/101,h=n/M*170;svg+=`<rect x="${x}" y="${H-P-h}" width="6" height="${h}" fill="#278b79"><title>${i===100?'100세 이상':i+'세'}: ${num(n)}명 (${(n/p.total*100).toFixed(2)}%)</title></rect>`;if(i%10===0)svg+=`<text x="${x}" y="${H-8}" font-size="12" text-anchor="middle">${i===100?'100+':i}</text>`;});svg+='</svg>';
 const change=(d.populationChanges||[]).find(x=>x.candidateCode===p.code&&x.district===r.district&&x.rawDong===r.rawDong);
 const changeText=change?`<p data-population-change><strong>2020→2024 연말 비교 · 고정 기간</strong><br>전체 주민 ${num(change.total2020)}→${num(change.total2024)}명. 65세 이상 ${num(change.age65Plus2020)}→${num(change.age65Plus2024)}명, 비중 ${(change.age65Share2020*100).toFixed(2)}→${(change.age65Share2024*100).toFixed(2)}%.</p><p class="muted">선택 연도와 별도인 동일 코드·명칭 후보의 비교입니다. 신고자 연령이나 교육 수요를 뜻하지 않습니다.</p>`:'';
 $('population').innerHTML=`<p><strong>${esc(p.name)} ${num(p.total)}명</strong> · ${esc(p.referenceDate)} 기준</p>${svg}${valueTable('ages',['연령','주민 인원','전체 주민 중 비중'],p.ages.map((n,i)=>[i===100?'100세 이상':i+'세',num(n)+'명',(n/p.total*100).toFixed(2)+'%']),'전체 101연령 수치표')}${changeText}<p class="muted">수치표에서 모든 연령의 인원·비중을 확인할 수 있습니다. 주민 구성은 신고자 연령이 아니며, 이 신고의 발생 행정동을 확정한 통계가 아닙니다.</p>`;}
['search','district','subtype','scope'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));render();
</script></html>'''
extension=(ROOT/'scripts/explorer_context_20260916.js').read_text(encoding='utf-8')
extension=extension.replace('선택 연도 12개 기준월의 제공 일평균 값을 동일가중 평균','선택 연도의 관측 기준월별 제공 일평균 값을 동일가중 평균').replace('명 / 제공 일평균의 12개월 평균','명 / 제공 일평균의 관측개월 평균')
page=page.replace("['search','district','subtype','scope'].forEach",extension+"\n['search','district','subtype','scope'].forEach")
page=page.replace('../final/index.html','../complete/index.html').replace('../final/gallery.html','../complete/gallery.html')
(OUT/'explorer.html').write_text(page,encoding='utf-8')
print(OUT/'explorer.html')
