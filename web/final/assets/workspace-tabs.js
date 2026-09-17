/* 지도 상태를 보존한 채 결과·그림 화면을 같은 작업 공간에서 전환한다. */
(()=>{
 window.addEventListener('DOMContentLoaded',()=>{
  const header=document.querySelector('.topbar'),map=document.querySelector('.map-app');
  const results=document.getElementById('analysis-open');
  const gallery=header?.querySelector('a[href="results/complete/gallery.html"]');
  if(!header||!map||!results||!gallery)return;
  const nav=document.createElement('nav');nav.className='workspace-tabs';nav.setAttribute('role','tablist');nav.setAttribute('aria-label','부산 분석 화면');
  const mapTab=document.createElement('button');mapTab.type='button';mapTab.textContent='신고 지도';mapTab.id='workspace-map-tab';
  results.before(nav);nav.append(mapTab,results,gallery);
  const tabs=[mapTab,results,gallery],keys=['map','results','gallery'];
  const panel=document.createElement('section');panel.id='result-workspace';panel.className='result-workspace';panel.hidden=true;panel.setAttribute('role','tabpanel');
  const status=document.createElement('div');status.className='workspace-loading';status.setAttribute('role','status');status.textContent='분석 화면을 불러오고 있습니다…';
  const frame=document.createElement('iframe');frame.className='workspace-frame';frame.title='부산 신고 분석 결과';
  panel.append(status,frame);map.after(panel);
  map.id='map-workspace';map.setAttribute('role','tabpanel');map.setAttribute('aria-labelledby',mapTab.id);
  let current='map',loaded='',scrolls={};
  const root=new URL('./',location.href),pages={results:new URL('results/complete/index.html',root).href,gallery:new URL('results/complete/gallery.html',root).href};
  function setView(key,url){
   if(!keys.includes(key))return;
   if(current!=='map'&&frame.contentWindow)scrolls[loaded]=frame.contentWindow.scrollY;
   current=key;
   tabs.forEach((tab,i)=>{tab.setAttribute('aria-selected',String(keys[i]===key));tab.tabIndex=keys[i]===key?0:-1;});
   map.hidden=key!=='map';panel.hidden=key==='map';
   const menu=document.getElementById('left-toggle');if(menu)menu.hidden=key!=='map';
   if(key==='map'){requestAnimationFrame(()=>window.BUSAN_MAP_VIEW?.map?.resize());return;}
   panel.setAttribute('aria-labelledby',tabs[keys.indexOf(key)].id);
   const target=url||pages[key];
   if(target!==loaded){status.hidden=false;frame.style.visibility='hidden';frame.src=target;loaded=target;}
  }
  tabs.forEach((tab,i)=>{
   tab.id=tab.id||`workspace-${keys[i]}-tab`;tab.setAttribute('role','tab');tab.setAttribute('aria-controls',i===0?'map-workspace':panel.id);
   tab.addEventListener('click',e=>{e.preventDefault();setView(keys[i]);});
   tab.addEventListener('keydown',e=>{let n;if(e.key==='ArrowRight')n=(i+1)%3;else if(e.key==='ArrowLeft')n=(i+2)%3;else if(e.key==='Home')n=0;else if(e.key==='End')n=2;else return;e.preventDefault();tabs[n].focus();setView(keys[n]);});
  });
  frame.addEventListener('load',()=>{
   const doc=frame.contentDocument;if(!doc)return;
   if(frame.contentWindow.location.href==='about:blank')return;
   loaded=frame.contentWindow.location.href;
   doc.documentElement.classList.add('workspace-embedded');
   const css=doc.createElement('link');css.rel='stylesheet';css.href=new URL('assets/result-workspace.css?v=20260918-1',root).href;
   const ready=()=>{status.hidden=true;frame.style.visibility='visible';if(!new URL(frame.contentWindow.location.href).hash)frame.contentWindow.scrollTo(0,scrolls[loaded]||0);};
   css.onload=ready;css.onerror=ready;doc.head.append(css);
   doc.querySelectorAll('a[href]').forEach(a=>{const u=new URL(a.href);if(u.origin!==location.origin){a.target='_blank';a.rel='noopener noreferrer';}});
   doc.addEventListener('click',e=>{
    const a=e.target.closest('a[href]');if(!a||a.hasAttribute('download')||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
    const url=new URL(a.href);if(url.origin!==location.origin)return;
    if(url.pathname===root.pathname+'index.html'||url.pathname===root.pathname){e.preventDefault();setView('map');}
    else if(url.pathname===new URL(pages.gallery).pathname&&current!=='gallery'){e.preventDefault();setView('gallery',url.href);}
    else if(url.pathname===new URL(pages.results).pathname&&current!=='results'){e.preventDefault();setView('results',url.href);}
   });
  });
  setView('map');
 });
})();
