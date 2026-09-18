"""Extend the existing verified explorer with C-scope seasonal sensitivity."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1]
P=R/'scripts/build_followup_explorer_20260916.py'
s=P.read_text(encoding='utf-8')
marker="populationContext=ROOT/'data/processed/최종논리검증-20260916/population/prevention-population.json'"
if "d['temporalProfiles']" not in s:
 s=s.replace(marker,"""transferPath=ROOT/'data/processed/효과근거확장-20260916/temporal/temporal-transfer.json'
d['temporalProfiles']=[{k:v for k,v in x.items() if k!='windows'}|{'allWindow':x['windows'][0],'leaveOneWindows':[{'excludedYear':int(w['window'].split('_')[1]),'topMonths':w['topMonths'],'topSeasons':w['topSeasons']} for w in x['windows'][6:]]} for x in read(transferPath)['profiles']] if transferPath.exists() else []
"""+marker)
 s=s.replace('renderUpdatedEvidence(r);','renderUpdatedEvidence(r);renderTemporalTransfer(r);')
 fn='''
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
'''
 s=s.replace('function renderUpdatedEvidence(r){',fn+'\nfunction renderUpdatedEvidence(r){')
 s=s.replace('<a href="쟁점해결.html">쟁점·보완 결과</a>','<a href="쟁점해결.html">기존 심층 결과</a> · <a href="../effects/index.html">추가 분석·기대효과</a>')
 P.write_text(s,encoding='utf-8')
print('Temporal extension installed in the existing builder.')
