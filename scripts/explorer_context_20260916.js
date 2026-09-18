// Aggregate-only context views. Separate denominators are kept next to each result.
function contextPlot(lines,labels,unit){
 const colors=['#147b75','#35678c','#b87931'],W=900,H=250,P=50,M=Math.max(1,...lines.flatMap(x=>x.values));
 let s=`<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(lines.map(x=>x.name).join('·'))} ${esc(unit)} 분포">`;
 [0,.5,1].forEach(f=>{const y=H-P-f*(H-2*P);s+=`<line x1="${P}" x2="${W-P}" y1="${y}" y2="${y}" stroke="#dce8e4"/><text x="${P-8}" y="${y+5}" text-anchor="end" font-size="13">${num(Math.round(M*f))}</text>`;});
 lines.forEach((l,j)=>{s+=`<polyline fill="none" stroke="${colors[j]}" stroke-width="3" points="${l.values.map((v,i)=>`${P+i*(W-2*P)/Math.max(1,labels.length-1)},${H-P-v/M*(H-2*P)}`).join(' ')}"/>`;});
 labels.forEach((x,i)=>{if(labels.length<10||i%4===0||i===labels.length-1)s+=`<text x="${P+i*(W-2*P)/Math.max(1,labels.length-1)}" y="${H-15}" text-anchor="middle" font-size="14">${esc(x)}</text>`;});
 return `<p>${lines.map((x,j)=>`<span style="color:${colors[j]};margin-right:20px">● ${esc(x.name)}</span>`).join('')} · ${esc(unit)}</p>`+s+'</svg>';
}
function renderLongCommerce(r){
 $('detail').querySelector('[data-commerce-full]')?.remove();
 if(r.subtype!=='교통사고')return;
 const key=r.district+'|'+r.rawDong,history=d.commerceLong[key],totals=d.commerceTotals[key];if(!history||!totals)return;
 const quarters=Object.keys(history).sort();
 $('detail').insertAdjacentHTML('beforeend',`<section data-commerce-full><h3>${esc(r.rawDong)} 법정동 상권의 분기별 구성</h3><p>신고의 구·군과 법정동 이름이 정확히 일치하고 후보 코드가 하나인 경우의 배경입니다. 신고 발생 행정동·상점 위치를 확정한 결합은 아닙니다.</p><label>상권 기준 분기<select id="commerce-quarter">${quarters.map(q=>`<option value="${q}" ${q==='20240930'?'selected':''}>${q.slice(0,4)}년 ${Math.ceil(Number(q.slice(4,6))/3)}분기</option>`).join('')}</select></label><div id="commerce-quarter-profile"></div><h4>2020~2024 등록 목록 규모</h4>${contextPlot([{name:'법정동 등록업소',values:totals.map(x=>x[1])}],totals.map(x=>x[0].slice(0,4)+'Q'+Math.ceil(Number(x[0].slice(4,6))/3)),'개 / 각 분기 목록')}${valueTable('commerce-quarter',['기준일','등록업소'],totals.map(x=>[x[0],num(x[1])]),'20분기 목록 수치표')}<p class="muted">목록 변화는 실제 개폐업·방문량·보행량과 다릅니다. 관측 분류코드·명칭은 같지만 과거 분류제도의 불변을 뜻하지 않습니다.</p><a href="https://www.data.go.kr/data/15083033/fileData.do">공식 상권자료</a></section>`);
 const draw=()=>{const q=$('commerce-quarter').value,rows=[...history[q]].sort((a,b)=>b[1]-a[1]);
  $('commerce-quarter-profile').innerHTML=`<p data-commerce-denominator>${q.slice(0,4)}년 ${Math.ceil(Number(q.slice(4,6))/3)}분기 · 등록업소 ${num(rows[0][2])}개 / ${rows.length}개 관측 업종</p><p class="muted">초록=동, 파랑=부산, 황토=소속 구·군. 각 지역 전체 등록업소를 분모로 한 구성비입니다.</p>`+rows.map(x=>`<div style="display:grid;grid-template-columns:120px 1fr 80px;gap:12px;align-items:center;margin:12px 0"><strong>${esc(x[0])}</strong><div>${[3,4,5].map((j,i)=>`<div style="height:7px;margin:3px 0;background:${['#147b75','#35678c','#b87931'][i]};width:${x[j]}%"></div>`).join('')}</div><span>${x[3].toFixed(1)}%</span></div>`).join('')+valueTable('commerce',['업종','업소 수','동 비중','부산 비중','구·군 비중','부산 차이(%p)','구·군 차이(%p)'],rows.map(x=>[x[0],num(x[1]),...x.slice(3).map(y=>y===null?'비교 자료 없음':y.toFixed(1))]),'전체 업종 비교표');
 };$('commerce-quarter').onchange=draw;draw();
}
function renderCurrentCase(r){
 const x=d.currentCaseResults.cases.find(x=>x.district===r.district&&x.rawDong===r.rawDong&&x.subtype===r.subtype);if(!x)return;
 const sources=d.currentCaseSources.filter(s=>x.sourceRefs.includes(s.id));
 let dated='';if(r.rawDong==='다대동')dated='폐장 후 특별관리 발표기간 2026-09-01~09-13은 확인일 9월 16일 기준 종료됐습니다. 이후 운영의 부재를 뜻하지 않습니다.';
 if(r.rawDong==='우동')dated='발표된 정상 운영 종료일 2026-09-15는 확인일 9월 16일 이전입니다. 이후 운영 상태·대응 부족은 이 발표만으로 판정하지 않습니다.';
 if(r.rawDong==='기장읍')dated='2026 무상점검 신청은 6월 8일 마감됐습니다. 점검 계획 6~12월을 현재 신규 접수 가능 기간으로 표시하지 않습니다.';
 const section=`<section id="current-case-result"><h3>기존 대응과 이번 보완 결과</h3><p class="muted">공식 후속 자료 확인 2026-09-16 · 아래 과거 신고 해석은 2020~2024 C 조건의 별도 비교이며 현재 선택 조건의 건수와 합산하지 않습니다.</p><p><strong>${esc(x.status)}</strong></p><p>${esc(x.context)}</p><h4>확인한 기존 대응</h4><p>${esc(x.existingResponse)}</p>${dated?`<p><strong>${esc(dated)}</strong></p>`:''}<h4>제공하는 보완 내용</h4><p>${esc(x.proposal)}</p><p class="muted">${esc(x.confirmedGap)}</p>${sources.map(s=>`<p><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc({'water-afterclose-2026':'폐장 후 수상 안전 운영 발표','geumjeong-current':'금정산 국립공원 탐방 안내','geumjeong-heat':'금정산 폭염 탐방 안내','gijang-small-housing':'기장군 무상점검 공고 · 접수 마감','education-current':'부산소방 교육 안내'}[s.id]||'공식 근거')}</a></p>`).join('')}</section>`;
 $('detail').firstElementChild.insertAdjacentHTML('afterend',section);
}
function renderLiving(r){
 if(!$('living-context'))$('population').closest('section').insertAdjacentHTML('afterend','<section id="living-context"></section>');
 const link=d.populationLinks.find(x=>x.year===2024&&x.district===r.district&&x.rawDong===r.rawDong),profiles=(d.living||[]).filter(x=>link?.candidateCodes.includes(x.code));
 const target=$('living-context');
 target.innerHTML='<h3>주민 수와 다른 시간대별 지역 활동</h3><p>주거·직장·방문 생활인구를 따로 비교합니다. 신고자의 신분이나 방문 목적을 뜻하지 않습니다.</p><p class="muted">선택 연도 12개 기준월의 제공 일평균 값을 동일가중 평균 · 주민 연도·신고 조건과 별도 기준</p>';
 if(!profiles.length){target.innerHTML+='<p>이 지역에 연결된 2024 생활인구 배경은 없습니다.</p>';return;}
 target.innerHTML+=`<label>생활인구 지역 후보<select id="living-code">${profiles.map(x=>`<option value="${esc(x.code)}">${esc(x.name)}</option>`).join('')}</select></label><div id="living-profile"></div><p class="muted">후보 동을 합산하지 않습니다. 24시간 값이나 주거·직장·방문 세 유형을 더해 연간 실인원으로 사용하지 않습니다. 통신 기반 추정이며 파일 기준월과 신고 관측월이 완전히 같다는 뜻이 아닙니다.</p><p><a href="https://www.data.go.kr/data/15142761/fileData.do">시간 자료</a> · <a href="https://www.data.go.kr/data/15142760/fileData.do">연령 자료</a></p>`;
 const show=()=>{
  const code=$('living-code').value,year=$('living-year').value,profile=profiles.find(z=>z.code===code),current=d.livingYears[year]?.[code],order=['20대미만','20대','30대','40대','50대','60대이상'];
  if(!current||current.name!==profile.name){$('living-profile').innerHTML='<p>이 연도에 같은 코드·명칭으로 비교할 수 있는 자료가 없습니다.</p>';return;}
  const convert=(rows,label)=>rows.map(z=>({[label]:z[0],'평균주거인구수':z[1],'평균직장인구수':z[2],'평균방문인구수':z[3]}));
  const hours=convert(current.hours,'시간대').sort((a,b)=>a['시간대'].localeCompare(b['시간대'])),ages=convert(current.ages,'나이대').sort((a,b)=>order.indexOf(a['나이대'])-order.indexOf(b['나이대']));
  const max=Math.max(...hours.map(z=>z['평균방문인구수'])),x={name:current.name,visitorPeakHour:hours.filter(z=>z['평균방문인구수']===max).map(z=>z['시간대']).join('·'),visitor00:hours[0]['평균방문인구수'],visitor12:hours[12]['평균방문인구수']};
  const names=['주거','직장','방문'],lines=names.map(name=>({name,values:hours.map(z=>Number(z['평균'+name+'인구수']))}));
  const ageLines=names.map(name=>({name,values:ages.map(z=>Number(z['평균'+name+'인구수']))}));
  $('living-profile').innerHTML=`<p data-living-summary><strong>${esc(x.name)}</strong> · 방문 생활인구 최대 ${esc(x.visitorPeakHour)}, 00시 ${num(Math.round(x.visitor00))}명 → 12시 ${num(Math.round(x.visitor12))}명.</p>${contextPlot(lines,hours.map(x=>x['시간대']),'명 / 제공 일평균의 12개월 평균')}${valueTable('living-hours',['시각',...names.map(x=>x+'(명)')],hours.map(z=>[z['시간대'],...names.map(name=>num(Number(z['평균'+name+'인구수']).toFixed(1)))]),'생활인구 24시간 수치표')}<h4>생활인구의 전체 6연령대</h4>${contextPlot(ageLines,ages.map(x=>x['나이대']),'명 / 제공 일평균의 12개월 평균')}${valueTable('living-ages',['연령대',...names.map(x=>x+' 명 (유형 내 비중)')],ages.map((z,i)=>[z['나이대'],...names.map((name,j)=>{const n=Number(z['평균'+name+'인구수']),den=ageLines[j].values.reduce((a,b)=>a+b,0);return num(n.toFixed(1))+' ('+(den?n/den*100:0).toFixed(1)+'%)';})]),'생활인구 6연령 수치표')}<p class="muted">연령 비중의 분모는 해당 생활인구 유형의 6연령대 합계입니다. 주민등록인구와 다른 추정값이며 어린이는 ‘20대 미만’에 포함됩니다.</p>`;
  const peak=y=>{const z=d.livingYears[y]?.[code];if(!z||z.name!==profile.name)return '비교 자료 없음';const m=Math.max(...z.hours.map(a=>a[3]));return z.hours.filter(a=>a[3]===m).map(a=>a[0]).join('·');};
  $('living-profile').insertAdjacentHTML('afterbegin',`<p><strong>${year}년 생활인구 · 관측 ${current.observedMonths}개월 동일가중 평균</strong>${current.nameMissing?' · 명칭 미제공: 코드로 표시':''}${year==='2025'?' · 신고 분석 종료 이후의 별도 배경. 2020~2024 신고 추세에 연결하지 않습니다.':''}<br>방문 정점 비교: 2023 ${peak('2023')} → 2024 ${peak('2024')}</p>`);
 };
 $('living-code').insertAdjacentHTML('beforebegin','<select id="living-year" aria-label="생활인구 기준 연도"><option>2023</option><option selected>2024</option><option value="2025">2025 · 별도 배경</option></select>');
 $('living-year').onchange=show;$('living-code').onchange=show;show();
}
function renderAdditionalContext(r){
 let html='';
 if(r.subtype==='교통사고'){
  const rows=d.commerceCategories.filter(x=>x.district===r.district&&x.lawDong===r.rawDong).sort((a,b)=>Number(b.shops)-Number(a.shops));
  if(rows.length){
   html+=`<section data-commerce-full><h3>${esc(r.rawDong)} 전체 상권의 10개 업종</h3><p>2024년 9월 말 등록업소 ${num(rows[0].denominatorShops)}개. 보행 현장조사 구간과 구분한 법정동 전체 배경입니다.</p><p class="muted">초록: 해당 동 / 파랑: 같은 자료·같은 시점의 부산 전체 업소 구성비. 업소 수는 방문량이나 사고 원인이 아닙니다.</p>`;
   html+=rows.map(x=>`<div style="display:grid;grid-template-columns:110px 1fr 90px;gap:12px;align-items:center;margin:10px 0"><strong>${esc(x.category)}</strong><div><div style="background:#147b75;height:10px;width:${Number(x.sharePct)}%"></div><div style="background:#35678c;height:6px;margin-top:4px;width:${Number(x.busanSameSnapshotSharePct)}%"></div></div><span>${Number(x.sharePct).toFixed(1)}%</span></div>`).join('');
   html+=valueTable('commerce',['업종','업소 수','동 구성비','부산 구성비','차이(%p)'],rows.map(x=>[x.category,num(x.shops),Number(x.sharePct).toFixed(1)+'%',Number(x.busanSameSnapshotSharePct).toFixed(1)+'%',Number(x.differenceFromBusanPercentagePoints).toFixed(1)]),'상권 10업종 비교표')+'<p><a href="https://www.data.go.kr/data/15083033/fileData.do">소상공인시장진흥공단 공식 자료</a></p></section>';
  }
 }
 if(r.subtype==='일반화재(주택)'){
  const names=r.rawDong==='기장읍'&&r.district==='기장군'?['기장읍']:r.rawDong==='온천동'&&r.district==='동래구'?['온천1동','온천2동','온천3동']:[];
  if(names.length){
   const building=d.buildingContext.find(x=>x.scope===r.scope&&x.rawDong===r.rawDong&&x.district===r.district);
   html+=`<section data-housing-context><h3>주택 배경과 별도 건물 분류</h3><p>선택한 주택 화재 ${num(r.count)}건${building?`, 별도 ‘${esc(building.subtype)}’ 접수 ${num(building.count)}건`:''}. 두 분류를 합쳐 아파트 화재로 해석하지 않습니다.</p>`;
   names.forEach(name=>{
    const audit=d.housingAudit.find(x=>x.name===name&&x.district===r.district);if(!audit)return;
    const rows=d.housingRows.filter(x=>x.name===name&&x.district===r.district),total=Number(audit.total),types=rows.filter(x=>x.kind==='type'&&x.itemLabel!=='주택이외 거처'),years=rows.filter(x=>x.kind==='constructionYear').sort((a,b)=>a.itemCode.localeCompare(b.itemCode));
    const display=xs=>xs.map(x=>[x.itemLabel,x.missing==='True'?'미제공':num(x.value)+'호',x.missing==='True'?'미제공':(Number(x.value)/total*100).toFixed(1)+'%']);
    const leading=types.filter(x=>x.missing!=='True').sort((a,b)=>Number(b.value)-Number(a.value))[0],yearTop=years.filter(x=>x.missing!=='True').sort((a,b)=>Number(b.value)-Number(a.value))[0];
    html+=`<h4>${esc(name)} · 총 주택 ${num(total)}호</h4><p>${esc(leading.itemLabel)} ${num(leading.value)}호(${(Number(leading.value)/total*100).toFixed(1)}%)가 가장 많습니다. 건축 시기 공개값 중 최다 구간은 ${esc(yearTop.itemLabel)} ${num(yearTop.value)}호입니다.</p><p class="muted">2024 통계 / 2025-06-30 경계 기준(부산 206개 동 코드). 과거 신고를 이 경계에 재배정하지 않았습니다.</p>${valueTable('housing-type-'+audit.sgisCode,['주택 유형','호수','총 주택 중 비중'],display(types),'주택 유형 전체표')}<p>주택 이외 거처 ${num(audit.otherLivingQuarters)}개는 위 총 주택 분모와 별도입니다.</p>${valueTable('housing-year-'+audit.sgisCode,['건축 시기','호수','총 주택 중 비중'],display(years),'건축 시기 전체표')}<p class="muted">건축 시기 공개값 합계 ${num(audit.constructionPublishedSum)}호 · 미제공 ${num(audit.missingConstructionCells)}개 항목. 미제공은 0호로 바꾸지 않습니다.</p>`;
   });
   html+='<p>주택 구조와 건축 시기는 기존 예방교육의 지역 배경입니다. 위 신고가 특정 주택 유형·건축 시기·단지에서 발생했다는 근거는 아닙니다.</p><a href="https://www.data.go.kr/data/15129688/fileData.do">SGIS 공식 통계</a></section>';
  }
  const a=d.apartmentSprinklers.find(x=>x.region===r.rawDong);
  if(a)html+=`<section data-sprinklers><h3>등록 단지의 스프링클러 표기</h3><p>2026-09-16 확보 · ${a.complexes_with_records}단지의 등록 동 항목 ${a.building_records}개.</p>${valueTable('sprinklers',['공식 표기','등록 항목 수','등록 항목 중 비중'],Object.entries(a.sprinkler_labels).map(([k,v])=>[k,num(v),pct(v/a.building_records)]),'스프링클러 표기 비교표')}<p>${esc(a.scope)} 신고를 해당 단지에 배정하거나 현재 안전 성능을 판정하지 않았습니다.</p><a href="../deepening/index.html">등록 자료 조사 결과·출처</a></section>`;
 }
 if(r.subtype==='심정지'){
  const a=d.aedPublicHours.find(x=>x.region===r.rawDong);
  if(a)html+=`<section data-aed-hours><h3>AED 공개 이용시간</h3><p>${esc(a.source_asof)}. 공개 검색 ${a.listed}개 등록 ID 중 차량 등록 ${a.mobile_excluded_from_comparison}개를 제외한 ${a.nonvehicle_listed}개를 비교했습니다.</p><p><strong>매일·공휴일 24시간 모두 명시 ${a.nonvehicle_all_days_24h}개</strong> / 모두 명시하지 않은 등록 ${a.nonvehicle_not_all_days_24h}개.</p><p>시간 미명시를 이용 불가능으로 판정하지 않았습니다. 대여용 장비도 포함될 수 있고, 공개 검색은 모든 등록 장비를 뜻하지 않습니다. 신고 지점별 접근거리나 작동 여부를 검증한 값이 아닙니다.</p><a href="../deepening/index.html">시간대 대조 결과·출처</a> · <a href="../advance/index.html">교육용·실제 장비의 이용 조건</a></section>`;
 }
 if(html)$('detail').insertAdjacentHTML('beforeend',html);
 renderLongCommerce(r);renderCurrentCase(r);
 const jumps=[['#living-context','생활인구'],['[data-commerce-full]','상권 10업종'],['[data-housing-context]','주택·건축 시기'],['[data-sprinklers]','스프링클러 표기'],['[data-aed-hours]','AED 이용시간']].flatMap(([sel,title],i)=>{const node=$('detail').querySelector(sel);if(!node)return [];if(!node.id)node.id='context-section-'+i;return `<a href="#${node.id}">${title}</a>`;});
 if(jumps.length)$('detail').firstElementChild.insertAdjacentHTML('beforeend',`<nav aria-label="지역 배경과 대응 바로가기" style="display:flex;gap:16px;flex-wrap:wrap;margin-top:18px">${jumps.join('')}</nav>`);
}
