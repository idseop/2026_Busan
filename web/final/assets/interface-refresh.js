/* 원래 필터와 목록 이벤트를 유지하며 탐색 순서와 사례 접기만 개선한다. */
(()=>{
 const enhance=()=>{
  const panel=document.getElementById('left-panel');
  const search=panel?.querySelector('.search-wrap');
  const years=panel?.querySelector('.left-year-filter');
  if(search&&years&&search.nextElementSibling!==years)search.after(years);
  const shortcuts=panel?.querySelector('.deep-shortcuts');
  if(shortcuts&&!shortcuts.closest('.case-disclosure')){
   const disclosure=document.createElement('details');
   disclosure.className='case-disclosure';
   const summary=document.createElement('summary');
   summary.textContent='분석 사례 둘러보기';
   shortcuts.before(disclosure);disclosure.append(summary,shortcuts);
  }
 };
 window.addEventListener('DOMContentLoaded',()=>{
  enhance();
  const panel=document.getElementById('left-panel');
  if(panel)new MutationObserver(enhance).observe(panel,{childList:true,subtree:true});
 });
})();
