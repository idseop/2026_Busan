(() => {
 'use strict';
 const D=window.BUSAN_CURRENT,$=id=>document.getElementById(id),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const n=v=>Number(v||0).toLocaleString('ko-KR'),pct=(a,b)=>b?(100*a/b).toFixed(1)+'%':'—',sum=a=>a.reduce((a,b)=>a+Number(b),0),opt=(v,s)=>`<option value="${esc(v)}">${esc(s)}</option>`;
 const initial={year:'all',scope:'P',type:'all',subtype:'all',mode:'district',query:'',sort:'count',selection:null,tab:'overview',population:'',timeKey:''};
 let S={...initial},history=[],map;
 const gu=D.districts.map(x=>x.district),raw=[...new Map(D.counts.map(r=>[r[0]+'|'+r[1],{district:r[0],rawDong:r[1]}])).values()];
 const period=()=>S.year==='all'?'2020–2024 합계':S.year+'년',py=()=>S.year==='all'?2024:+S.year;
 const observed=(sel,year=S.year)=>!sel||sel.kind==='district'||year==='all'||D.existing.some(r=>r.scope==='A'&&r.year===+year&&r.district===sel.district&&r.rawDong===sel.rawDong);
 const matches=(r,sel=S.selection)=>!sel||(r[0]===sel.district&&(sel.kind==='district'||r[1]===sel.rawDong));
 function records(allYears=false){
   if(S.scope==='P')return D.counts.filter(r=>(allYears||S.year==='all'||r[2]===+S.year)&&(S.type==='all'||r[3]===S.type)&&(S.subtype==='all'||r[4]===S.subtype));
   return D.existing.filter(r=>r.scope===S.scope&&(allYears||S.year==='all'||r.year===+S.year)).flatMap(r=>Object.entries(r.typeCounts).filter(([t])=>S.type==='all'||t===S.type).map(([t,v])=>[r.district,r.rawDong,r.year,t,'',v]));
 }
 function groups(rows,index){const m=new Map();rows.forEach(r=>m.set(r[index],(m.get(r[index])||0)+r[5]));return [...m].sort((a,b)=>b[1]-a[1]);}
 function mix(items,total){return items.map(([name,v])=>`<div class="mix-row"><span>${esc(name)}</span><span class="mix-track"><i style="width:${total?100*v/total:0}%"></i></span><span>${n(v)} <small>${pct(v,total)}</small></span></div>`).join('');}
 function trend(values){const max=Math.max(...values,1),x=i=>27+i*72,y=v=>140-v/max*100;return `<svg class="trend" viewBox="0 0 345 174" role="img" aria-label="2020~2024년 ${values.map(v=>v===null?'자료 없음':v+'건').join(', ')}"><path d="M27 140H315" stroke="#dbe5e7"/><path d="${values.map((v,i)=>v===null?'':(i&&values[i-1]!==null?'L':'M')+x(i)+' '+y(v)).join(' ')}" fill="none" stroke="#087e8b" stroke-width="3"/>${values.map((v,i)=>`${v===null?'':`<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="#087e8b"/>`}<text x="${x(i)}" y="${y(v)-12}" font-size="12" text-anchor="middle" fill="#143c4d">${v===null?'—':n(v)}</text><text x="${x(i)}" y="163" font-size="12" text-anchor="middle" fill="#60767d">${2020+i}</text>`).join('')}</svg>`;}
 const block=(title,content)=>`<section class="detail-block"><h3>${title}</h3>${content}</section>`;
 function relevantFocus(){return D.focus.filter(r=>r.district===S.selection.district&&(S.selection.kind==='district'||r.rawDong===S.selection.rawDong)&&(S.type==='all'||r.type===S.type)&&(S.subtype==='all'||r.subtype===S.subtype));}
 function select(selection){if(S.selection&&JSON.stringify(S.selection)!==JSON.stringify(selection))history.push({...S,selection:{...S.selection}});S.selection=selection;S.tab='overview';S.population='';S.timeKey='';draw();$('detail-content').scrollTop=0;}
 function draw(){
   const rr=records(),totals=Object.fromEntries(gu.map(d=>[d,0]));rr.forEach(r=>totals[r[0]]+=r[5]);
   $('map-total').textContent=n(sum(Object.values(totals)))+'건';$('map-context-text').textContent=period();
   document.querySelectorAll('[data-year]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.year===S.year)));
   $('scope').value=S.scope;$('type').value=S.type;$('sort').value=S.sort;$('region-search').value=S.query;
   const st=D.subtypes.filter(r=>S.type==='all'||r.type===S.type);$('subtype').innerHTML=opt('all',S.scope==='P'?'전체 유형':'종별 비교만 제공')+st.map(r=>opt(r.type+'|'+r.subtype,S.type==='all'?r.type+' · '+r.subtype:r.subtype)).join('');$('subtype').disabled=S.scope!=='P';$('subtype').value=S.subtype==='all'?'all':S.type+'|'+S.subtype;
   $('filter-note').textContent=S.scope==='P'?'선택 조건의 신고 · 위험 순위 아님':'비교 조건 · 벌집제거 포함, 종별 집계';
   let items=S.mode==='district'?gu.map(d=>({district:d,name:d,count:totals[d]})):raw.map(r=>({...r,name:r.rawDong,count:0}));
   if(S.mode==='raw'){const keyed=new Map(items.map(r=>[r.district+'|'+r.rawDong,r]));rr.forEach(r=>{const item=keyed.get(r[0]+'|'+r[1]);if(item)item.count+=r[5];});}
   const q=S.query.replace(/\s/g,'');items=items.filter(r=>(r.district+r.name).includes(q));items.sort(S.sort==='count'?(a,b)=>b.count-a.count||a.name.localeCompare(b.name,'ko'):(a,b)=>a.name.localeCompare(b.name,'ko'));
   $('list-count').textContent=items.length+'개 지역';
   $('region-list').innerHTML=items.map(r=>`<button class="region-row ${S.selection?.district===r.district&&(S.mode==='district'?S.selection.kind==='district':S.selection.rawDong===r.rawDong)?'active':''}" data-district="${esc(r.district)}" data-raw="${esc(r.rawDong||'')}" data-count="${observed({...r,kind:S.mode})?r.count:''}"><span class="row-name">${esc(r.name)}${S.mode==='raw'?`<span class="row-sub">${r.district} · 신고 지역명</span>`:''}</span><span class="row-number">${observed({...r,kind:S.mode})?n(r.count)+'<small>건</small>':'<small>자료 없음</small>'}</span></button>`).join('')||'<p class="empty">검색 결과가 없습니다.</p>';
   $('region-list').querySelectorAll('button').forEach(b=>b.onclick=()=>select({kind:S.mode,district:b.dataset.district,...(S.mode==='raw'?{rawDong:b.dataset.raw}:{})}));
   document.querySelectorAll('[data-list]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.list===S.mode)));
   $('right-panel').hidden=!S.selection;document.querySelector('.map-app').classList.toggle('detail-open',!!S.selection);$('detail-back').hidden=!history.length;
   if(!map){window.BUSAN_FINAL_CASES={cases:D.districts.slice(0,5).map(r=>({district:r.district}))};map=window.BUSAN_CREATE_MAP({element:$('district-map'),features:window.BUSAN_MAP,onSelect:select});}
   map.update(totals,S.selection);if(S.selection)detail(rr);
   window.BUSAN_CURRENT_STATE={...S,total:sum(Object.values(totals)),districtCounts:totals};
 }
 function detail(rr){
   const sel=S.selection,rows=rr.filter(r=>matches(r)),total=sum(rows.map(r=>r[5]));
   $('detail-title').textContent=sel.kind==='raw'?sel.rawDong:sel.district;$('detail-unit').textContent=sel.kind==='raw'?sel.district+' · 신고 지역명':'';$('detail-period').textContent=period();
   document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===S.tab)));
   if(S.tab==='population')return population();if(S.tab==='services')return services();if(S.tab==='time')return timeDetail();
   if(!observed(sel)){$('detail-content').innerHTML=block('해당 연도 자료 없음','<p>이 지역명은 선택한 연도의 분석 자료에서 관측되지 않았습니다. 실제 신고 0건을 뜻하지 않습니다.</p>');return;}
   const displayRows=rows.map(r=>r[4]==='교통사고'?[...r.slice(0,4),r[3]+'·'+r[4],r[5]]:r);
   const parts=groups(displayRows,S.scope==='P'?4:3),annual=D.meta.years.map(y=>observed(sel,y)?sum(records(true).filter(r=>matches(r)&&r[2]===y).map(r=>r[5])):null),top=parts[0],f=relevantFocus(),steady=f.filter(r=>+r.aboveRestBusan30===30&&+r.aboveRestDistrict30===30);
   let html=block('선택 조건의 신고',`<p class="muted">${D.meta.scopeLabels[S.scope]} · ${esc(S.subtype!=='all'?S.subtype:S.type==='all'?'전체 유형':S.type)}</p><div id="detail-total" class="hero-count" data-count="${total}">${n(total)}<small>건</small></div>${total?`<ul class="findings"><li><strong>${esc(top[0])}</strong> ${n(top[1])}건 · 지역 내 ${pct(top[1],total)}</li><li>현재 유형·처리 조건으로 5개년 중 ${annual.filter(v=>v>0).length}년에서 접수 확인</li></ul>`:'<p>선택 조건의 집계값은 0건입니다.</p>'}`);
   html+=block(S.scope==='P'?'주요 세부 유형':'신고 종별 구성',`<p class="muted">${period()} · 분모 ${n(total)}건</p>${mix(parts.slice(0,6),total)}${parts.length>6?'<p class="muted">상위 6개 표시 · 모든 유형은 왼쪽 필터에서 선택</p>':''}`);
   html+=block('5년 변화',`<p class="muted">2020–2024 · 현재 유형·처리 조건 · 연도 선택과 별도 비교</p>${trend(annual)}`);
   if(S.scope==='P'&&f.length)html+=block('지역에서 반복된 특징',`<p class="muted">2020–2024 고정 비교 · 결측 제외·처리 조건을 바꾼 30개 비교 조합</p>${steady.length?`<p>${steady.slice(0,3).map(x=>esc(x.rawDong+' '+x.subtype)).join(' · ')}: 나머지 부산 및 같은 구의 나머지 지역보다 높은 구성비가 30개 비교에서 모두 유지됐습니다.</p>`:'<p>반복 접수는 확인됐습니다. 구성비의 두드러짐은 비교 조건에 따라 달라집니다.</p>'}<a href="analysis/#focus">중점 지역 선정 결과 ↗</a>`);
   if(sel.kind==='district'){
     const names=groups(rows,1);html+=block('같은 유형을 동에서 보기',names.slice(0,8).map(([name,v])=>`<button class="detail-link" data-child="${esc(name)}">${esc(name)}<small>${n(v)}건 →</small></button>`).join(''));
   }else html+='<p class="muted">지도는 소속 구·군을 강조합니다. 개별 신고의 동 위치는 표시하지 않습니다.</p>';
   $('detail-content').innerHTML=html;$('detail-content').querySelectorAll('[data-child]').forEach(b=>b.onclick=()=>{S.mode='raw';select({kind:'raw',district:sel.district,rawDong:b.dataset.child});});
 }
 function population(){
   const sel=S.selection,year=py(),codes=D.links[`${sel.district}|${sel.rawDong}|${year}`]||[],candidates=D.population.filter(p=>p.year===year&&p.district===sel.district&&(sel.kind==='district'||codes.includes(p.code)));
   const chosen=sel.kind==='district'?candidates:candidates.length===1?candidates:candidates.filter(p=>p.code===S.population);
   const control=sel.kind==='raw'&&candidates.length>1?`<label>주민 자료의 동 선택<select id="population-choice" class="pop-select">${opt('','동별로 선택')+candidates.map(p=>opt(p.code,p.name)).join('')}</select></label><p class="muted">여러 동의 후보 자료입니다. 합산하거나 신고를 배분하지 않습니다.</p>`:'';
   if(!chosen.length){$('detail-content').innerHTML=block('주민 연령 구성',`<p>${year}년 12월 말 주민</p>${control}<p class="status-note">${candidates.length?'주민 자료를 선택하면 전체 연령 분포가 표시됩니다.':'연결된 주민 자료가 없습니다.'}</p>`);}
   else{
     const ages=Array.from({length:101},(_,i)=>sum(chosen.map(p=>p.ages[i]))),total=sum(ages),bands=Array.from({length:11},(_,i)=>[i===10?'100세 이상':`${i*10}–${i*10+9}세`,sum(ages.slice(i*10,Math.min(i*10+10,101)))]);
     $('detail-content').innerHTML=block('주민 연령 구성',`<p>${esc(sel.kind==='district'?sel.district:chosen[0].name)} · ${year}년 12월 말</p>${control}<div class="hero-count" id="population-total" data-count="${total}">${n(total)}<small>명</small></div><p>65세 이상 ${n(sum(ages.slice(65)))}명 · ${pct(sum(ages.slice(65)),total)}</p>${mix(bands,total)}<p class="muted">전체 연령대의 인원·비중입니다. 신고자의 나이를 뜻하지 않습니다. 신고 유형·처리 조건은 주민 수를 바꾸지 않습니다.</p><button id="age-toggle">단일 연령별 수치</button><div id="age-full" hidden><table class="age-table"><thead><tr><th>연령</th><th>인원</th><th>비중</th></tr></thead><tbody>${ages.map((v,i)=>`<tr><td>${i===100?'100세 이상':i+'세'}</td><td>${n(v)}</td><td>${pct(v,total)}</td></tr>`).join('')}</tbody></table></div>`);
     $('age-toggle').onclick=()=>{$('age-full').hidden=!$('age-full').hidden;};
   }
   if($('population-choice')){$('population-choice').value=S.population;$('population-choice').onchange=e=>{S.population=e.target.value;population();};}
 }
 function timeDetail(){
   if(S.scope!=='P'){$('detail-content').innerHTML=block('시간 분석', '<p>이 페이지의 세부 유형별 시간 분석은 주 분석 조건으로 제공됩니다.</p><button id="time-primary">주 분석 조건으로 보기</button>');$('time-primary').onclick=()=>{S.scope='P';draw();};return;}
   const ff=relevantFocus();if(!ff.length){$('detail-content').innerHTML=block('시간 분석','<p>선택 지역·유형의 추가 시간 분석은 이번 심층 45개 조합에 포함되지 않았습니다.</p><a href="analysis/#focus">검증된 시간 분석 결과 보기 ↗</a>');return;}
   const key=r=>r.rawDong+'|'+r.subtype,f=ff.find(r=>key(r)===S.timeKey)||ff[0];S.timeKey=key(f);
   const summary=D.timeSummary.find(r=>r.district===f.district&&r.rawDong===f.rawDong&&r.subtype===f.subtype&&+r.year===(S.year==='all'?0:+S.year));
   const hours=['00–04','04–08','08–12','12–16','16–20','20–24'],week=['월','화','수','목','금','토','일'];
   let html=`<select id="time-choice" class="time-select" aria-label="심층 시간 분석 지역 유형">${ff.map(r=>opt(key(r),r.rawDong+' · '+r.subtype)).join('')}</select>`;
   html+=block(`${esc(f.rawDong)} · ${esc(f.subtype)}`,`<p class="muted">${period()} · 해당 유형 ${n(summary.count)}건</p><ul class="findings"><li>가장 많은 4시간 구간: <strong>${hours[+summary.hour4Peak]}시</strong></li><li>20시–다음 날 08시 ${pct(summary.night20to07Count,summary.count)}</li><li>월별 최다 ${summary.monthPeak}월 · 요일별 최다 ${week[+summary.weekdayPeak]}요일</li></ul>`);
   if(S.year==='all'){
     const cells=Array.from({length:7},()=>Array(6).fill(0)),months=Array(12).fill(0);
     D.time.filter(r=>r.district===f.district&&r.rawDong===f.rawDong&&r.subtype===f.subtype).forEach(r=>{if(r.dimension==='weekdayHour'){const day=Math.floor(+r.value/24),h=+r.value%24;cells[day][Math.floor(h/4)]+=+r.count;}if(r.dimension==='month')months[+r.value-1]+=+r.count;});
     const mx=Math.max(...cells.flat(),1);
     html+=block('요일 × 4시간대',`<p class="muted">2020–2024 합계 · ${esc(f.rawDong)} ${esc(f.subtype)}</p><div class="heatmap"><span></span>${hours.map(h=>`<span>${h}</span>`).join('')}${cells.map((a,i)=>`<span>${week[i]}</span>${a.map((v,j)=>`<span class="cell" title="${week[i]}요일 ${hours[j]}시 ${n(v)}건" style="background:hsl(176 33% ${96-v/mx*58}%);color:${v/mx>.6?'white':'#173e4b'}">${n(v)}</span>`).join('')}`).join('')}</div>`);
     html+=block('월별 접수',mix(months.map((v,i)=>[(i+1)+'월',v]),sum(months))+'<p class="muted">달력일수 보정 전 건수</p>');
   }
   $('detail-content').innerHTML=html;$('time-choice').value=S.timeKey;$('time-choice').onchange=e=>{S.timeKey=e.target.value;timeDetail();};
 }
 const serviceInfo={
   '해운대구':{name:'심뇌혈관질환 예방관리',text:'30세 이상 주민·고위험군 및 가족 대상. 4개 권역의 6주 교육 프로그램을 공식 안내에서 확인했습니다.',url:'https://www.haeundae.go.kr/index.do?menuCd=DOM_000000804005002000',date:'2025-05-15 안내'},
   '사상구':{name:'마을건강센터',text:'모라1·3동, 주례1·2·3동의 주민 건강상담·교육 운영을 확인했습니다. 평일 09–17시, 점심시간 제외. 모라3동의 2024년 9월 방문 활동 기록도 확보했습니다.',url:'https://www.sasang.go.kr/health/index.sasang?menuCd=DOM_000000404013000000',date:'2026-09 확인'},
   '북구':{name:'금곡 마을건강센터',text:'금곡동 복지센터 1층, 주민 누구나 무료 건강상담·교육. 평일 09–18시, 점심시간 제외. 북구는 만성질환 등록·투약 안내도 운영합니다.',url:'https://www.bsbukgu.go.kr/health/index.bsbukgu?menuCd=DOM_000000503001006000',date:'2026-09 확인'},
   '사하구':{name:'다대 건강생활지원센터',text:'다대1동 복지센터 3층. 건강측정·상담·만성질환 관리, 평일 09–17시, 점심시간 제외. 구의 질환교육과 생활터 강좌도 확인했습니다.',url:'https://www.saha.go.kr/health/contents.do?mId=0404060000',date:'2025-08-29 안내'}
 };
 function services(){
   const sel=S.selection,rows=D.proposals.filter(r=>r.district===sel.district&&(sel.kind==='district'||r.rawDong===sel.rawDong)&&(S.type==='all'||r.type===S.type)&&(S.subtype==='all'||r.subtype===S.subtype)),pro=[...new Map(rows.map(r=>[r.id,r])).values()],info=serviceInfo[sel.district];
   let html='<p class="muted">5개년 주 분석과 별도 공식 자료를 연결한 결과 · 신고 연도·처리 필터와 별도 기준</p>';
   if(info&&(S.type==='all'||S.type==='구급'))html+=block('확인한 기존 서비스',`<div class="service-info"><h4>${info.name}</h4><p>${info.text}</p><small>${info.date} · 과거 신고와 운영 시점 다름</small><br><a href="${info.url}" target="_blank" rel="noopener">공식 안내 ↗</a></div>`);
   if(!pro.length)html+=block('예방·지원 보완 결과','<p class="status-note">현재 자료로 확정한 지역별 보완안 없음</p><p>접수 규모와 주민 구성만으로 서비스 부족이나 시설 신설을 확정하지 않았습니다.</p>');
   for(const p of pro){
     html+=block(p.id==='I1'?'부전동 · 원인별 제안 보류':`${p.rawDong} · 교육 연결 시범 후보`,`<p>${esc(p.measuredNeed)}</p><p class="muted">보건 지표는 구 전체 조사이며 이 동 신고자의 상태가 아닙니다.</p><div class="status-note ${p.id==='I1'?'caution':''}">${esc(p.id==='I1'?'현재 자료로 확정한 부상 예방안 없음':p.proposal)}</div><h4>기존 대응과의 연결</h4><p>${esc(p.existing)}</p><h4>시행 조건</h4><p>${esc(p.precondition)}</p><h4>평가 기준</h4><p>${esc(p.primaryMetric)}</p><p>${esc(p.secondaryMetric)}</p><h4>수정·중단 기준</h4><p>${esc(p.stopRule)}</p><p class="muted">${esc(p.effect)}</p>`);
   }
   html+='<a href="analysis/#proposals">보완안과 효과 평가 전체 결과 ↗</a>';$('detail-content').innerHTML=html;
 }
 $('scope').innerHTML=Object.entries(D.meta.scopeLabels).map(([k,v])=>opt(k,v)).join('');$('type').innerHTML=opt('all','전체 종별')+['구급','구조','화재','기타'].map(t=>opt(t,t)).join('');
 $('year-buttons').innerHTML=['all',...D.meta.years.map(String)].map(y=>`<button data-year="${y}" aria-pressed="false">${y==='all'?'전체 기간':y}</button>`).join('');
 document.querySelectorAll('[data-year]').forEach(b=>b.onclick=()=>{S.year=b.dataset.year;S.population='';draw();});
 ['scope','type','subtype','sort'].forEach(id=>$(id).onchange=e=>{if(id==='subtype'&&e.target.value!=='all'){[S.type,S.subtype]=e.target.value.split('|');}else S[id]=e.target.value;if(id==='type'||id==='scope')S.subtype='all';S.timeKey='';draw();});
 $('region-search').oninput=e=>{S.query=e.target.value;if(S.query&&!gu.some(g=>g.includes(S.query))&&raw.some(r=>r.rawDong.includes(S.query)))S.mode='raw';draw();};
 document.querySelectorAll('[data-list]').forEach(b=>b.onclick=()=>{S.mode=b.dataset.list;draw();});
 document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{S.tab=b.dataset.tab;draw();$('detail-content').scrollTop=0;});
 $('detail-close').onclick=()=>{S.selection=null;history=[];draw();};$('detail-back').onclick=()=>{if(history.length){S=history.pop();draw();}};
 $('filters-reset').onclick=()=>{S={...initial};history=[];draw();map.fit('main');};$('map-reset').onclick=()=>map.fit('all');$('map-selected').onclick=()=>map.fit('selected');$('map-zoom-in').onclick=()=>map.zoomIn();$('map-zoom-out').onclick=()=>map.zoomOut();
 const q=new URLSearchParams(location.search);if(gu.includes(q.get('district'))){S.selection={kind:'district',district:q.get('district')};const name=q.get('dong');if(raw.some(r=>r.district===S.selection.district&&r.rawDong===name))S.selection={kind:'raw',district:S.selection.district,rawDong:name};const ss=D.subtypes.filter(r=>r.subtype===q.get('subtype'));if(ss.length===1){S.subtype=ss[0].subtype;S.type=ss[0].type;}}
 draw();window.BUSAN_CURRENT_ACTIONS={select,reset:()=>$('filters-reset').click()};
})();
