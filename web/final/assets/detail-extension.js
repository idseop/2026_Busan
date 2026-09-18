(() => {
 'use strict';
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const n=v=>Number(v).toLocaleString('ko-KR'),sum=a=>a.reduce((s,v)=>s+Number(v||0),0),pct=(a,b)=>b?`${(a/b*100).toFixed(1)}%`:'—';
 const scopeNames={A:'전체 처리결과',B:'정상 처리',C:'정상 처리 · 운영성 신고 제외'};
 const typeColors={구급:'#19868c',구조:'#709eaf',화재:'#ca9a58',기타:'#506b7e'};
 const finalCases=()=>window.BUSAN_FINAL_CASES?.cases||[];
 const caseUrl=item=>'results/followup/explorer.html?'+new URLSearchParams({district:item.district,dong:item.rawDong,type:item.subtype,scope:'C'}).toString();
 function finalCaseLinks(c){
  const matches=finalCases().filter(x=>x.district===c.selection.district&&(c.selection.kind==='district'||x.rawDong===c.selection.rawDong)&&(c.type==='all'||c.type===x.type));
  const query=new URLSearchParams({district:c.selection.district,scope:'C'});
  if(c.selection.kind!=='district'&&c.selection.rawDong)query.set('dong',c.selection.rawDong);
  const section=document.createElement('section');section.className='final-case-links';section.dataset.extension='final-cases';
  section.innerHTML='<h3>지역 분석</h3><p>2020–2024 전체 · 정상 처리·운영성 제외 · 예방 관련 5개 유형의 별도 분석</p><a data-all-region-analysis href="results/followup/explorer.html?'+esc(query.toString())+'">지역 분석 전체 보기 →</a><div>'+matches.map(x=>`<a data-final-case="${esc(x.id)}" href="${esc(caseUrl(x))}"><strong>${esc(x.rawDong)} · ${esc(x.subtype)}</strong><span>신고 패턴부터 기존 대응·보완 결과까지 →</span></a>`).join('')+'</div>';
  c.content.append(section);
 }
 const peaks=a=>{const max=Math.max(...a,0);return max?a.flatMap((v,i)=>v===max?[i]:[]):[];};
 const resultText={
  기장읍:{comparison:'주민 누구나 이용하는 건강상담과 대상 조건이 있는 방문건강관리는 이용 대상·방식이 다릅니다. 응급 구급은 응급처치와 병원 이송을 제공합니다.',output:'건강상담·방문건강관리·응급 구급의 이용 정보를 구분해 제공합니다.',status:'서비스 확대를 뒷받침할 대응 공백은 현재 자료에서 확인되지 않았습니다.'},
  정관읍:{comparison:'방문건강관리 안내에 정관읍 담당이 포함돼 있습니다. 기장읍과는 분석에 남은 기록의 비율이 달라 건수만으로 수요 순위를 정할 수 없습니다.',output:'방문건강관리의 대상과 이용 절차를 제공합니다.',status:'현재 자료로 확정한 보완안 없음'},
  연산동:{comparison:'연산동으로 접수된 질병 신고는 5년 모두 확인됩니다. 여러 동에 걸친 지역명이므로 특정 행정동의 서비스 부족으로 연결할 수 없습니다.',output:'질병 신고의 반복·시간 특성과 부산 구급 서비스 정보를 제공합니다.',status:'현재 자료로 확정한 보완안 없음'},
  금곡동:{comparison:'시건개방 신고는 5년 모두 확인됩니다. 분류명만으로 인명위험 여부나 문을 열어야 했던 목적을 구분할 수 없습니다.',output:'시건개방의 반복·시간 특성과 기존 구조 서비스 정보를 제공합니다.',status:'현재 자료로 확정한 보완안 없음'}
 };
 function population(c){const p=c.population;if(p?.people?.length)return `${c.populationYear}년 말 주민 ${n(p.total)}명 · 65세 이상 ${pct(sum(p.ages.slice(65)),p.total)}`;return p?.choices?.length?'주민 자료: 동별 선택 가능':'연결된 주민 자료 없음';}
 function comparisons(c,m){
  const matches=r=>r.district===c.selection.district&&(c.selection.kind==='district'||r.rawDong===c.selection.rawDong);
  const rest=c.data.rawRegions.filter(r=>r.scope===c.scope&&(c.year==='all'||r.year===+c.year)&&!matches(r));
  const localTotal=sum(m.mix.map(r=>r.count)),restTotal=sum(rest.map(r=>r.total));
  const values=m.mix.filter(r=>c.type==='all'||r.name===c.type).map(r=>{const other=sum(rest.map(x=>x.typeCounts[r.name]||0));return {...r,localTotal,restTotal,other,difference:localTotal&&restTotal?100*(r.count/localTotal-other/restTotal):null};}).sort((a,b)=>(b.difference??-Infinity)-(a.difference??-Infinity));
  const indices=new Set(c.deep.regions.filter(r=>!matches(r)).map(r=>r.index)),hours=Array(6).fill(0);
  c.deep.dayHour.forEach(([ri,y,si,ti,w,h,count])=>{if(indices.has(ri)&&(c.year==='all'||y===+c.year)&&si===c.deep.meta.scopes.indexOf(c.scope)&&(c.type==='all'||c.deep.meta.types[ti]===c.type))hours[h]+=count;});
  return {composition:values[0],hours};
 }
 function caseSummary(c,item){
  const counts=item.countsByScope[c.scope],idx=c.data.meta.years.indexOf(+c.year),value=c.year==='all'?sum(counts.yearCounts):counts.yearCounts[idx];
  const record=item.service,sources=(record?.sourceIds||[]).map(id=>c.services.sources.find(s=>s.id===id)).filter(Boolean);
  const stable=Object.values(item.countsByScope).every(v=>v.positiveInAllFiveYears&&!v.directionReversal);
  const service=sources[0],text=resultText[item.rawDong];
  const paired=c.deep.cases.find(x=>x.district===item.district&&x.id!==item.id&&x.subtype===item.subtype),pairedCounts=paired?.countsByScope[c.scope];
  const comparison=pairedCounts?`${item.rawDong}의 기록 잔존율 ${pct(counts.selected17Total,counts.core8Total)}, ${paired.rawDong} ${pct(pairedCounts.selected17Total,pairedCounts.core8Total)}. 두 지역의 건수 차이를 그대로 지원 수요 차이로 볼 수 없습니다.`:text.comparison;
  return `<article class="case-conclusion"><p class="case-eyebrow">심층 결과 · ${esc(item.rawDong)} / ${esc(item.subtype)}</p><h4>${esc(item.subtype)} 신고, 5년 연속 확인</h4><p>${esc(maybePeriod(c))} <strong>${n(value)}건</strong>. ${stable?'처리조건을 바꾸고 결측 제외 전후를 비교해도 5년 반복과 2020→2024 변화 방향이 유지됩니다.':'포함 조건에 따라 양상이 달라지는 사례입니다.'}</p><p class="case-evidence">5년 전체 비교 · ${esc(comparison)}</p>${!pairedCounts?`<p class="source-date">현재 처리조건에서 비교 기록의 ${pct(counts.selected17Total,counts.core8Total)}가 남았습니다. 전체 신고의 대표성은 검증되지 않았습니다.</p>`:''}${service?`<div class="service-brief"><strong>${esc(service.title)}</strong><p>${esc(service.target)} · ${esc(service.hours)}</p><a href="${esc(service.url)}" target="_blank" rel="noopener">공식 서비스 안내 ↗</a><span>${esc(service.referenceDate)} 기준</span></div>`:''}<p class="case-outcome"><b>제공 결과</b> ${esc(text.output)}</p><p class="case-decision">${esc(text.status)}</p></article>`;
 }
 const maybePeriod=c=>c.year==='all'?'2020–2024년':`${c.year}년`;
 function compositionSummary(c,m){
  const byName=new Map(m.mix.map(x=>[x.name,x.count])),items=c.data.meta.types.map(name=>({name,count:byName.get(name)||0,color:typeColors[name]||'#80919a'})),total=sum(items.map(x=>x.count));
  let cursor=0;const stops=items.filter(x=>x.count>0).map(x=>{const start=cursor,end=cursor+(x.count/total*100);cursor=end;return `${x.color} ${start.toFixed(3)}% ${end.toFixed(3)}%`;});
  const gradient=total?`conic-gradient(${stops.join(',')})`:'#e5ecef',top=[...items].sort((a,b)=>b.count-a.count)[0];
  const label=items.map(x=>`${x.name} ${n(x.count)}건 ${pct(x.count,total)}`).join(', ');
  const section=document.createElement('section');section.dataset.extension='result';section.className='region-summary';
  section.innerHTML=`<div class="region-summary-heading"><div><span class="summary-period">${esc(m.period)}</span><h3>신고 유형별 현황</h3></div><strong>${n(total)}<small>건</small></strong></div><div class="type-donut-layout"><div class="type-donut" role="img" aria-label="${esc(label||'신고 기록 없음')}" style="--donut:${gradient}"><span><b>${n(total)}</b><small>전체</small></span></div><div class="type-donut-legend">${items.map(x=>`<div><i style="background:${x.color}"></i><span>${esc(x.name)}</span><b>${pct(x.count,total)}</b><small>${n(x.count)}건</small></div>`).join('')}</div></div><p class="summary-takeaway">${total?`가장 큰 비중은 <b>${esc(top.name)} ${pct(top.count,total)}</b>입니다.`:'선택 조건에서 확인된 신고 기록이 없습니다.'}</p><p class="source-date">같은 기간·처리조건에서 신고 유형이 확인된 분석용 기록의 구성입니다. 실제 사건·출동·환자 수나 주민당 발생률이 아닙니다.</p>`;
  return section;
 }
 function overview(c,m){
  const top=m.mix[0],hours=m.timing?peaks(m.timing.hours).map(i=>c.deep.meta.hourBands[i]+'시').join(' · '):'',repeat=m.years.filter(y=>y.count>0).length;
  const comp=comparisons(c,m),mix=comp.composition,peak=m.timing?peaks(m.timing.hours)[0]:undefined;
  const comparable=m.total&&mix?.difference!==null&&mix?.restTotal;
  const lead=comparable?`${mix.name} 비중, 부산 나머지 지역보다 ${Math.abs(mix.difference).toFixed(1)}%p ${mix.difference>0?'높음':mix.difference<0?'낮음':'차이 없음'}`:m.total?`${top.name} 신고가 가장 많이 접수됨`:'선택 조건의 신고 없음';
  const s=document.createElement('section');s.dataset.extension='result';s.className='region-result';
  s.innerHTML=`<span class="summary-eyebrow">지역별 해석</span><h3>이 지역의 특징</h3><p class="result-lead result-insight">${esc(lead)}</p><p class="result-countline">${esc(m.period)} · ${esc(scopeNames[c.scope])} · 현재 신고 유형 ${n(m.total)}건</p>${comparable?`<div class="composition-contrast" data-local-share="${mix.count/mix.localTotal}" data-rest-share="${mix.other/mix.restTotal}"><div><span>선택 지역 ${esc(mix.name)}</span><b>${pct(mix.count,mix.localTotal)}</b><i style="width:${100*mix.count/mix.localTotal}%"></i></div><div><span>부산 나머지 지역 ${esc(mix.name)}</span><b>${pct(mix.other,mix.restTotal)}</b><i style="width:${100*mix.other/mix.restTotal}%"></i></div></div><p class="source-date">같은 기간·처리조건의 전체 종별 신고 중 구성비. 선택 지역을 비교 대상에서 제외했습니다. 위험도나 주민당 발생률이 아닙니다.</p>`:''}<ul class="result-facts">${m.total&&hours?`<li><b>${esc(hours)}</b> 접수 최다<span>${esc(m.period)} · 4시간 구간별 건수 비교${peak!==undefined?`<br>첫 표시 구간 비중: 선택 지역 ${pct(m.timing.hours[peak],m.total)} · 부산 나머지 지역 ${pct(comp.hours[peak],sum(comp.hours))}`:''}</span></li>`:''}<li><b>${repeat}개 연도</b>에서 신고 확인<span>2020–2024년 · 같은 신고 조건</span></li><li>${esc(population(c))}</li></ul>${m.cases.map(item=>caseSummary(c,item)).join('')}${!m.cases.length?'<p class="case-decision">이 지역의 서비스 확대나 신규 예방안은 현재 분석에서 확정하지 않았습니다.</p>':''}<div class="result-links"><button data-result-tab="time">시간 분포</button><button data-result-tab="population">주민 구성</button><button data-result-tab="services">서비스·보완 결과</button></div>`;
  const old=c.content.querySelector('.detail-block');if(old?.querySelector('.hero-count'))old.remove();
  c.content.querySelector('.type-row')?.closest('.detail-block')?.remove();
  c.content.prepend(s);c.content.prepend(compositionSummary(c,m));s.querySelectorAll('[data-result-tab]').forEach(b=>b.onclick=()=>c.onTab(b.dataset.resultTab));
 }
 function sourceCard(s){return `<article class="response-service"><h4>${esc(s.title)}</h4>${s.facts.map(x=>`<p>${esc(x)}</p>`).join('')}<dl><dt>대상</dt><dd>${esc(s.target)}</dd><dt>시간</dt><dd>${esc(s.hours)}</dd><dt>이용 조건</dt><dd>${esc(s.conditions)}</dd><dt>지역</dt><dd>${esc(s.coverage)}</dd></dl><a href="${esc(s.url)}" target="_blank" rel="noopener">공식 안내 ↗</a><span class="source-date">${esc(s.referenceDate)} 기준</span></article>`;}
 function services(c,m,id){
  const item=m.cases.find(x=>x.id===id)||m.cases[0];
  if(!item){c.content.innerHTML='<section class="region-result" data-extension="result"><h3>예방·지원 보완 결과</h3><p class="result-status">현재 자료로 확정한 보완안 없음</p></section>';return;}
  const record=item.service,counts=item.countsByScope[c.scope],value=c.year==='all'?sum(counts.yearCounts):counts.yearCounts[c.data.meta.years.indexOf(+c.year)],h=Array(6).fill(0);
  c.deep.caseTime.forEach(r=>{if(r[0]===item.index&&r[2]===c.deep.meta.scopes.indexOf(c.scope)&&(c.year==='all'||r[1]===+c.year))h[r[4]]+=r[5];});
  const hours=peaks(h).map(i=>c.deep.meta.hourBands[i]+'시').join(' · '),text=resultText[item.rawDong],sources=(record?.sourceIds||[]).map(id=>c.services.sources.find(s=>s.id===id)).filter(Boolean);
  c.content.innerHTML=`<section class="region-result" data-extension="result"><h3>기존 대응 비교 결과</h3>${m.cases.length>1?`<div class="result-case-tabs">${m.cases.map(x=>`<button data-result-case="${x.id}" aria-pressed="${x.id===item.id}">${esc(x.rawDong)} · ${esc(x.subtype)}</button>`).join('')}</div>`:''}<p class="result-lead">${esc(item.rawDong)} · ${esc(item.subtype)}</p><p class="case-observation" data-case-count="${value}" data-case-id="${item.id}" data-year="${c.year}" data-scope="${c.scope}">${esc(m.period)} · ${esc(scopeNames[c.scope])}<br><strong>${n(value)}건</strong>${hours?` · ${esc(hours)} 접수 최다`:''}</p><p>${esc(text.comparison)}</p></section><section class="detail-block" data-extension="result"><h3>예방·지원 보완 결과</h3><p class="result-status">${esc(text.output)}</p><p>${esc(text.status)}</p></section><section class="detail-block" data-extension="result"><h3>관련 서비스</h3><p class="source-date">서비스 안내 기준일은 신고 기간과 다를 수 있습니다.</p>${sources.map(sourceCard).join('')}</section>`;
  c.content.querySelectorAll('[data-result-case]').forEach(b=>b.onclick=()=>services(c,m,b.dataset.resultCase));
 }
 window.BUSAN_DETAIL_EXTENSION=c=>{
  c.content.querySelectorAll('[data-extension]').forEach(e=>e.remove());
  const m=window.BUSAN_DETAIL_MODEL(c);
  if(c.tab==='overview')overview(c,m);
  if(c.tab==='services')services(c,m);
  c.content.querySelectorAll('details').forEach(e=>{if(e.querySelector('.age-table-wrap')){const wrap=e.querySelector('.age-table-wrap'),button=document.createElement('button');button.className='age-table-toggle';button.textContent='전체 연령표';button.setAttribute('aria-expanded','false');wrap.hidden=true;button.onclick=()=>{wrap.hidden=!wrap.hidden;button.setAttribute('aria-expanded',String(!wrap.hidden));};e.replaceWith(button,wrap);}else e.remove();});
  finalCaseLinks(c);
 };
 function projectResults(){
  const D=window.BUSAN_DATA,Deep=window.BUSAN_DEEP,target=document.getElementById('analysis-content');if(!D||!target)return;
  const rows=D.rawRegions.filter(r=>r.scope==='A'),total=sum(rows.map(r=>r.total)),types=D.meta.types.map(t=>({name:t,count:sum(rows.map(r=>r.typeCounts[t]||0))})).sort((a,b)=>b.count-a.count);
  target.innerHTML=`<p class="project-kicker">2020–2024 · 부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안</p><h3>지역별 신고 특성에 맞춘 예방·지원 정보</h3><p>지역마다 반복되는 신고와 주민 구성을 함께 살펴보고, 기존 서비스와 연결할 수 있는 예방·지원 정보를 정리했습니다.</p><section><h4>부산에서 확인한 결과</h4><p>분석에 포함된 신고는 <strong>${n(total)}건</strong>입니다. ${esc(types[0].name)}가 ${n(types[0].count)}건(${pct(types[0].count,total)})으로 가장 많았습니다.</p><p>기장읍·정관읍·연산동의 질병 신고와 금곡동의 시건개방 신고는 2020~2024년 모두 확인됐습니다.</p></section><section><h4>집중 분석한 네 사례</h4><table class="data-table"><thead><tr><th>지역</th><th>유형</th><th>5년 건수</th></tr></thead><tbody>${Deep.cases.map(x=>`<tr><td>${esc(x.rawDong)}</td><td>${esc(x.subtype)}</td><td>${n(sum(x.countsByScope.C.yearCounts))}</td></tr>`).join('')}</tbody></table><p class="source-date">정상 처리 중 운영성 신고 제외 · 2020–2024년 합계</p><p>5년 반복성, 비교 조건의 영향, 주민 자료 연결 가능성과 서비스 근거를 대조한 사례입니다. 위험 순위는 아닙니다.</p></section><section><h4>기존 대응을 비교한 결과</h4><p>건강센터·방문건강관리·응급 구급은 대상과 이용 방식이 달랐습니다. 기장읍과 정관읍은 기록이 남은 비율도 달라, 신고 건수만으로 지원 우선순위를 정할 수 없었습니다.</p></section><section><h4>이번 프로젝트가 제공한 결과</h4><p>지역별 신고·시간·주민 정보를 지도에 연결하고, 확인한 서비스의 대상·시간·이용 조건을 한곳에 정리했습니다.</p><p><strong>실제 서비스 부족이나 시설·인력 확대의 필요성은 현재 자료에서 확정되지 않았습니다.</strong> 주소나 이용 실적의 부족은 서비스 공백과 구분했습니다.</p></section>`;
  const dialog=document.getElementById('analysis-dialog');if(document.getElementById('analysis-open')?.tagName==='BUTTON')document.getElementById('analysis-open').onclick=()=>dialog.showModal();document.getElementById('analysis-close').onclick=()=>dialog.close();
  const shortcuts=document.createElement('section');shortcuts.className='deep-shortcuts';shortcuts.setAttribute('aria-label','심층 분석 사례');
  shortcuts.innerHTML=`<h2>사례 지역 찾기</h2><div>${finalCases().map(item=>`<button data-deep-shortcut="${esc(item.id)}">${esc(item.rawDong)}<span>${esc(item.subtype==='일반화재(주택)'?'주택 화재':item.subtype)}</span></button>`).join('')}</div>`;
  const regionList=document.querySelector('.region-list');
  if(regionList)regionList.after(shortcuts);else document.querySelector('.list-tabs').before(shortcuts);
  shortcuts.querySelectorAll('button').forEach(button=>button.onclick=()=>{
   const item=finalCases().find(x=>x.id===button.dataset.deepShortcut);
   const district=document.getElementById('district'),type=document.getElementById('type'),search=document.getElementById('region-search');
   search.value='';search.dispatchEvent(new Event('input',{bubbles:true}));
   district.value=item.district;district.dispatchEvent(new Event('change',{bubbles:true}));
   type.value=item.type;type.dispatchEvent(new Event('change',{bubbles:true}));
   document.getElementById('list-raw').click();search.value=item.rawDong;search.dispatchEvent(new Event('input',{bubbles:true}));
   [...document.querySelectorAll('.region-row')].find(row=>row.dataset.district===item.district&&row.dataset.rawDong===item.rawDong)?.click();
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',projectResults);else projectResults();
})();
