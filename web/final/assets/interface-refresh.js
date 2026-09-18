/* 원래 필터와 목록 이벤트를 유지하며 탐색 순서와 사례 접기만 개선한다. */
(()=>{
 const enhance=()=>{
  const panel=document.getElementById('left-panel');
  const shortcuts=panel?.querySelector('.deep-shortcuts');
  if(shortcuts&&!shortcuts.closest('.case-disclosure')){
   const disclosure=document.createElement('details');
   disclosure.className='case-disclosure';
   const summary=document.createElement('summary');
   summary.textContent='분석 사례 둘러보기';
   shortcuts.before(disclosure);disclosure.append(summary,shortcuts);
  }
  const disclosure=panel?.querySelector('.case-disclosure');
  const regionList=panel?.querySelector('.region-list');
  if(disclosure&&regionList&&regionList.nextElementSibling!==disclosure)regionList.after(disclosure);
  const fireControl=panel?.querySelector('.fire-station-control');
  const footer=panel?.querySelector('.left-footer');
  if(fireControl&&footer&&footer.previousElementSibling!==fireControl)footer.before(fireControl);
 };
 window.addEventListener('DOMContentLoaded',()=>{
  enhance();
  const panel=document.getElementById('left-panel');
  if(panel)new MutationObserver(enhance).observe(panel,{childList:true,subtree:true});
 });
})();
