(()=>{
 const cards=[...document.querySelectorAll('.visual')],search=document.getElementById('figure-search');
 let mode='core',topic='전체';
 function draw(){
  const q=search.value.trim().toLocaleLowerCase();let count=0;
  cards.forEach(c=>{c.hidden=(mode==='core'&&c.dataset.core!=='true')||(topic!=='전체'&&c.dataset.topic!==topic)||(q&&!c.textContent.toLocaleLowerCase().includes(q));if(!c.hidden)count++;});
  document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
  document.querySelectorAll('button[data-topic]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.topic===topic)));
  document.getElementById('library-count').textContent=`${mode==='core'?'핵심':'전체'} · ${topic} · ${count}개 그림`;
  document.getElementById('library-empty').hidden=count!==0;
 }
 document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;draw();});
 document.querySelectorAll('button[data-topic]').forEach(b=>b.onclick=()=>{topic=b.dataset.topic;draw();});
 search.addEventListener('input',draw);
 function revealHash(){
  const card=cards.find(c=>'#'+c.id===location.hash);if(!card)return;
  mode=card.dataset.core==='true'?'core':'all';topic='전체';search.value='';draw();
  requestAnimationFrame(()=>card.scrollIntoView({block:'start'}));
 }
 window.addEventListener('hashchange',revealHash);draw();revealHash();
})();
