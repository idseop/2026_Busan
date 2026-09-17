/* Keep the compact map and detail headings stable even when cached feature scripts redraw them. */
(()=>{
 let scheduled=false;
 const period=()=>{
  const value=document.getElementById('year')?.value;
  if(!value)return '';
  return value==='all'?'2020–2024년':`${value}년`;
 };
 const clean=()=>{
  scheduled=false;
  const label=period();
  const mapPeriod=document.getElementById('map-context-text');
  const detailUnit=document.getElementById('detail-unit');
  const detailPeriod=document.getElementById('detail-period');
  if(label&&mapPeriod?.textContent!==label)mapPeriod.textContent=label;
  if(detailUnit){if(detailUnit.textContent)detailUnit.textContent='';if(!detailUnit.hidden)detailUnit.hidden=true;}
  if(label&&detailPeriod&&detailPeriod.textContent!==label)detailPeriod.textContent=label;
  document.querySelectorAll('.open-regional-evidence').forEach(button=>button.remove());
 };
 const schedule=()=>{if(!scheduled){scheduled=true;requestAnimationFrame(clean);}};
 window.addEventListener('DOMContentLoaded',()=>{
  clean();
  new MutationObserver(schedule).observe(document.body,{subtree:true,childList:true,characterData:true});
  document.addEventListener('click',schedule,true);
  document.addEventListener('change',schedule,true);
 });
})();
