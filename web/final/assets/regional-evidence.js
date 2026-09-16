(() => {
 'use strict';
 const D=window.BUSAN_REGIONAL_EVIDENCE;if(!D)return;
 const old=window.BUSAN_DETAIL_EXTENSION,esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const n=x=>Number(x).toLocaleString('ko-KR',{maximumFractionDigits:1}),sum=a=>a.reduce((s,x)=>s+Number(x),0),key=r=>r.district+'|'+r.rawDong;
 const types=['심정지','교통사고','일반화재(주택)','산악사고','수난사고'],labels={'일반화재(주택)':'주택 화재','교통사고':'구급 교통사고'};
 const chosen=new Map();let lastContext=null;
 const link=r=>'results/followup/explorer.html?'+new URLSearchParams({district:r.district,dong:r.rawDong,scope:'C'});
 function spark(values,labelsList,title){
  const width=360,height=145,pad=20,max=Math.max(1,...values),point=(v,i)=>`${pad+i*(width-2*pad)/Math.max(1,values.length-1)},${height-36-v/max*(height-63)}`;
  return `<svg class="evidence-spark" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><path fill="none" stroke="#187b83" stroke-width="2.5" d="${values.map((v,i)=>(i?'L':'M')+point(v,i)).join(' ')}"/>${values.map((v,i)=>{const [x,y]=point(v,i).split(',');return `<circle cx="${x}" cy="${y}" r="3" fill="#187b83"/><text x="${x}" y="${Number(y)-9}" text-anchor="${i===0?'start':i===values.length-1?'end':'middle'}">${n(v)}</text><text x="${x}" y="${height-10}" text-anchor="${i===0?'start':i===values.length-1?'end':'middle'}">${esc(labelsList[i])}</text>`;}).join('')}</svg>`;
 }
 function field(label,value,name){return `<div class="evidence-field" data-evidence-field="${name}"><h4>${esc(label)}</h4><p>${esc(value)}</p></div>`;}
 function knownCase(r,t){return D.cases.find(x=>key(x)===key(r)&&x.subtype===t.subtype);}
 function renderContext(r,target){
  const pops=r.populationCandidates;
  target.innerHTML=`<h4>주민과 지역 활동</h4>${pops.length?`<label class="evidence-label">주민·생활 배경 지역<select data-evidence-pop>${pops.map(x=>`<option value="${esc(x.code)}">${esc(x.name)}</option>`).join('')}</select></label><div data-evidence-pop-result></div><p class="evidence-note">2024년 말 주민 · ${pops.length>1?'후보 동을 각각 표시합니다. ':''}신고자 연령을 뜻하지 않습니다.</p>`:'<p>연결된 주민 자료가 없습니다.</p>'}`;
  if(pops.length){const draw=()=>{const p=pops.find(x=>x.code===target.querySelector('[data-evidence-pop]').value),life=r.livingCandidates.filter(x=>x.code===p.code&&x.populationType==='평균방문인구수');target.querySelector('[data-evidence-pop-result]').innerHTML=`<p><strong>${esc(p.name)} ${n(p.total)}명</strong><br>65세 이상 ${n(p.age65Plus)}명 · ${(p.age65Plus/p.total*100).toFixed(1)}%</p>${life.map(x=>`<p class="evidence-life">${x.year}년 방문 생활인구 정점 <b>${esc(x.peakHours)}</b></p>`).join('')}<p class="evidence-note">생활인구는 ${life.length?'각 연도 12개 기준월의 제공 일평균값을 동일가중 평균한 값':'연결 자료 없음'}입니다. 주민 수와 합산하지 않습니다.</p>`;};target.querySelector('[data-evidence-pop]').onchange=draw;draw();}
  if(r.commerceHistory.length){const a=r.commerceHistory[0],b=r.commerceHistory.at(-1);target.insertAdjacentHTML('beforeend',`<h4>같은 이름의 법정동 상권</h4><p>${a.snapshot.slice(0,4)}년 1분기 ${n(a.shops)}개 → ${b.snapshot.slice(0,4)}년 4분기 ${n(b.shops)}개</p><p class="evidence-note">20개 분기 등록 목록 · 실제 개업·폐업이나 사고 원인으로 해석하지 않습니다.</p>`);}
  if(r.housingCandidates.length){target.insertAdjacentHTML('beforeend',`<h4>주택 형태</h4><label class="evidence-label">주택 배경 지역<select data-evidence-house>${r.housingCandidates.map(x=>`<option value="${esc(x.sgisCode)}">${esc(x.name)}</option>`).join('')}</select></label><div data-evidence-house-result></div>`);const show=()=>{const h=r.housingCandidates.find(x=>x.sgisCode===target.querySelector('[data-evidence-house]').value),rows=D.housingRows.filter(x=>x.sgisCode===h.sgisCode&&x.kind==='type'&&x.itemLabel!=='주택이외 거처');target.querySelector('[data-evidence-house-result]').innerHTML=`<p>${esc(h.name)} 총 ${n(h.total)}호</p>${rows.map(x=>`<div class="evidence-pair"><span>${esc(x.itemLabel)}</span><b>${x.missing==='True'?'미제공':n(x.value)+'호 · '+(Number(x.value)/Number(h.total)*100).toFixed(1)+'%'}</b></div>`).join('')}<p class="evidence-note">2024 통계 · 2025 경계의 배경. 신고를 주택에 배정하지 않습니다.</p>`;};target.querySelector('[data-evidence-house]').onchange=show;show();}
 }
 function renderCase(c,r,t,node){
  const item=knownCase(r,t),h=t.holdout||{},uid=key(r)+'|'+t.subtype,steps=['신고 특징','지역 배경','기존 대응','보완 결과'];let current=0;
  const sources=()=>`<div class="evidence-source" data-evidence-field="source"><span>운영자료 확인 ${D.asOf}</span>${(D.sources[uid]||[]).map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)} ↗</a>`).join('')}</div>`;
  node.innerHTML=`<div class="evidence-result" data-evidence-key="${esc(uid)}"><p class="evidence-period">2020–2024 · 정상 처리·업무성 기록 제외</p><p class="evidence-note">지도 필터와 별도의 5년 심층 결과</p><nav class="evidence-steps" aria-label="지역 결과 4단계">${steps.map((name,i)=>`<button type="button" data-evidence-step="${i+1}" aria-current="${i===0?'step':'false'}"><span>${i+1}</span>${name}</button>`).join('')}</nav><div class="evidence-paging"><button type="button" data-evidence-prev>← 이전</button><span data-evidence-progress aria-live="polite"></span><button type="button" data-evidence-next>다음 →</button></div><div data-evidence-body></div><a class="evidence-full" target="_blank" rel="noopener" href="${esc(link(r)+'&type='+encodeURIComponent(t.subtype))}">지역 상세 자료 보기 ↗</a></div>`;
  const body=node.querySelector('[data-evidence-body]');
  function show(step,focus=false){
   current=step;node.querySelectorAll('[data-evidence-step]').forEach(b=>b.setAttribute('aria-current',Number(b.dataset.evidenceStep)===step+1?'step':'false'));
   node.querySelector('[data-evidence-prev]').disabled=step===0;node.querySelector('[data-evidence-next]').disabled=step===3;node.querySelector('[data-evidence-progress]').textContent=`${step+1} / 4`;
   body.innerHTML=`<h4 class="evidence-step-title" tabindex="-1">${step+1}. ${steps[step]}</h4>`;
   if(step===0){
    body.insertAdjacentHTML('beforeend',`<div class="evidence-intro" data-evidence-field="receipt"><h3>${esc(labels[t.subtype]||t.subtype)} <strong>${n(t.count)}건</strong></h3><p>지역 전체 신고 ${n(t.denominatorAllTypes)}건 중 ${Number(t.sharePct||0).toFixed(1)}%</p></div><div class="evidence-statline"><b>${t.yearCounts.filter(v=>v>0).length}개 연도에서 접수</b><span>${!t.count?'선택 조건에서 0건':t.core8Comparison.directionReversal?'제외 조건에 따라 증감 방향 달라짐':'결측 제외 전후 증감 방향 유지'}</span></div><h4>5년 신고 변화</h4>${spark(t.yearCounts,['2020','2021','2022','2023','2024'],'5년 신고 건수')}<p>${t.count&&t.peakHours.length?'건수 기준 최다 시간 '+t.peakHours.map(x=>x+'시').join('·'):'시간 특징을 표시할 신고가 없습니다.'}</p><button type="button" class="evidence-compare-toggle" aria-expanded="false">계절 비교 보기</button><div data-season-result hidden></div>`);
    const result=body.querySelector('[data-season-result]'),toggle=body.querySelector('.evidence-compare-toggle');
    result.innerHTML=`<h4>2020–2023년과 2024년 비교</h4><p class="evidence-note">과거 구성비와 이후 관측을 비교한 결과입니다. 정책 효과나 미래 위험 예측이 아닙니다.</p>`+(h.comparisonEligible?`<p>2024년 ${n(h.testCount)}건</p><table class="evidence-table"><thead><tr><th>계절</th><th>과거 기반</th><th>2024 관측</th></tr></thead><tbody>${['봄','여름','가을','겨울'].map((x,i)=>`<tr><th>${x}</th><td>${(h.predictedShare[i]*100).toFixed(1)}%</td><td>${(h.actualShare[i]*100).toFixed(1)}%</td></tr>`).join('')}</tbody></table><p class="evidence-note">유형별 전체 비교의 평균에서는 지역 과거 구성의 오차가 단순 기준보다 작지 않았습니다. 특정 계절만으로 시설·인력 배치를 정하지 않았습니다.</p>`:`<p>${esc(h.status||'비교 자료 없음')}</p>`);
    toggle.onclick=()=>{result.hidden=!result.hidden;toggle.setAttribute('aria-expanded',String(!result.hidden));toggle.textContent=result.hidden?'계절 비교 보기':'계절 비교 닫기';};
   }else if(step===1){
    if(item)body.insertAdjacentHTML('beforeend',field('지역 배경 요약',item.context,'context'));
    const context=document.createElement('div');body.append(context);renderContext(r,context);
    const pop=context.querySelector('[data-evidence-pop]');if(pop){
     const box=document.createElement('div');box.className='evidence-map-action';box.innerHTML='<button type="button" data-evidence-focus>이 배경 지역 지도에서 보기</button><p class="evidence-note">2025년 경계의 배경 지역 위치 · 신고 지점이 아닙니다.</p><p data-focus-status role="status"></p>';pop.closest('label').after(box);
     box.querySelector('button').onclick=()=>{const candidate=r.populationCandidates.find(x=>x.code===pop.value);const ok=window.BUSAN_MAP_VIEW?.focusPlace?.({district:r.district,name:candidate.name});box.querySelector('[data-focus-status]').textContent=ok?`${candidate.name} 배경 위치를 표시했습니다.`:'이 배경 지역의 지도 위치는 확인되지 않았습니다.';};pop.addEventListener('change',()=>{window.BUSAN_MAP_VIEW?.clearFocus?.();box.querySelector('[data-focus-status]').textContent='';});
    }
   }else if(step===2){
    body.insertAdjacentHTML('beforeend',item?field('확인한 기존 대응',item.existingResponse,'response')+`<p class="evidence-status" data-evidence-field="status">${esc(item.status)}</p>`+sources():'<p>이 지역·유형과 대조한 공식 운영 근거가 연결되어 있지 않습니다.</p><p class="evidence-note">서비스가 없다는 뜻은 아닙니다.</p>');
   }else{
    body.insertAdjacentHTML('beforeend',item?field('예방·지원 보완 내용',item.proposal,'proposal')+field('근거와 적용 범위',item.confirmedGap,'basis')+`<p class="evidence-status">${esc(item.status)}</p><p class="evidence-note">안내·검토 결과이며 피해 감소 효과를 측정한 결과는 아닙니다.</p>`+sources():'<p class="evidence-status">현재 자료로 확정한 보완안 없음</p><p>현재 확인한 신고 특징과 지역 배경을 제공합니다. 시설·인력 확대 필요성은 확정하지 않았습니다.</p>');
   }
   if(focus)body.querySelector('.evidence-step-title').focus({preventScroll:true});
  }
  node.querySelectorAll('[data-evidence-step]').forEach(b=>b.onclick=()=>show(Number(b.dataset.evidenceStep)-1,true));node.querySelector('[data-evidence-prev]').onclick=()=>show(Math.max(0,current-1),true);node.querySelector('[data-evidence-next]').onclick=()=>show(Math.min(3,current+1),true);show(0);
 }
 function render(c){
  lastContext=c;
  const matches=D.profiles.filter(r=>r.district===c.selection.district&&(c.selection.kind==='district'||r.rawDong===c.selection.rawDong));
  if(!matches.length)return;
  const root=document.createElement('section');root.className='regional-evidence';root.dataset.extension='regional-evidence';
  const previous=chosen.get(c.selection.district+'|'+(c.selection.rawDong||''));
  let r=matches.find(x=>x.rawDong===previous?.dong)||matches.find(x=>D.cases.some(y=>key(y)===key(x)))||matches[0];
  const valid=()=>r.typeProfiles.filter(x=>c.type==='all'||x.major===c.type);
  let subtype=valid().find(x=>x.subtype===previous?.subtype)?.subtype||D.cases.find(x=>key(x)===key(r)&&valid().some(t=>t.subtype===x.subtype))?.subtype||valid()[0]?.subtype;
  root.innerHTML=`<div class="evidence-heading"><h3>지역별 예방·지원 결과</h3><button data-evidence-expand aria-pressed="false">넓게</button></div>${c.selection.kind==='district'?`<label class="evidence-label">이 구·군의 지역<select data-evidence-region>${matches.map(x=>`<option value="${esc(x.rawDong)}" ${x===r?'selected':''}>${esc(x.rawDong)}</option>`).join('')}</select></label>`:''}<label class="evidence-label">심층 분석 유형<select data-evidence-domain></select></label><div data-evidence-result></div>`;
  if(c.tab==='services')c.content.replaceChildren(root);else{c.content.querySelector('.final-case-links')?.remove();const button=document.createElement('button');button.className='open-regional-evidence';button.textContent='지역 배경·기존 대응·보완 결과';button.onclick=()=>c.onTab('services');c.content.prepend(button);return;}
  const draw=()=>{const rows=valid(),select=root.querySelector('[data-evidence-domain]');if(!rows.some(x=>x.subtype===subtype))subtype=rows[0]?.subtype;select.innerHTML=types.filter(t=>rows.some(x=>x.subtype===t)).map(t=>`<option value="${esc(t)}" ${t===subtype?'selected':''}>${esc(labels[t]||t)}</option>`).join('');chosen.set(c.selection.district+'|'+(c.selection.rawDong||''),{dong:r.rawDong,subtype});const node=root.querySelector('[data-evidence-result]');if(!rows.length){node.innerHTML='<p>이 종별은 5개 심층 분석 유형에 포함되지 않습니다. 요약·시간·주민 탭의 해당 조건 결과를 이용할 수 있습니다.</p>';select.disabled=true;return;}select.disabled=false;renderCase(c,r,rows.find(x=>x.subtype===subtype),node);};
  root.querySelector('[data-evidence-domain]').onchange=e=>{window.BUSAN_MAP_VIEW?.clearFocus?.();subtype=e.target.value;draw();};
  const region=root.querySelector('[data-evidence-region]');if(region)region.onchange=e=>{window.BUSAN_MAP_VIEW?.clearFocus?.();r=matches.find(x=>x.rawDong===e.target.value);subtype=null;draw();};
  root.querySelector('[data-evidence-expand]').onclick=e=>{const app=document.querySelector('.map-app');app.classList.toggle('evidence-wide');e.target.setAttribute('aria-pressed',String(app.classList.contains('evidence-wide')));e.target.textContent=app.classList.contains('evidence-wide')?'좁게':'넓게';};draw();
 }
 window.BUSAN_DETAIL_EXTENSION=c=>{old?.(c);render(c);};
 document.addEventListener('DOMContentLoaded',()=>{
  const tab=document.querySelector('[data-tab="services"]');if(tab)tab.textContent='지역 결과';
  document.querySelectorAll('[data-deep-shortcut]').forEach(b=>b.addEventListener('click',()=>{const item=window.BUSAN_FINAL_CASES.cases.find(x=>x.id===b.dataset.deepShortcut);if(item){chosen.set(key(item),{dong:item.rawDong,subtype:item.subtype});lastContext?.onTab('services');}}));
  document.getElementById('detail-close').addEventListener('click',()=>document.querySelector('.map-app').classList.remove('evidence-wide'));
  document.getElementById('filters-reset').addEventListener('click',()=>{chosen.clear();document.querySelector('.map-app').classList.remove('evidence-wide');});
 });
})();
