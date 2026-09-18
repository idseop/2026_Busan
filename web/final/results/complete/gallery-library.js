(()=>{
 const cards=[...document.querySelectorAll('.visual')],search=document.getElementById('figure-search');
 let topic='전체';
 function draw(){
  const q=search.value.trim().toLocaleLowerCase();let count=0;
  cards.forEach(c=>{c.hidden=(topic!=='전체'&&c.dataset.topic!==topic)||(q&&!c.textContent.toLocaleLowerCase().includes(q));if(!c.hidden)count++;});
  document.querySelectorAll('button[data-topic]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.topic===topic)));
  document.getElementById('library-empty').hidden=count!==0;
 }
 document.querySelectorAll('button[data-topic]').forEach(b=>b.onclick=()=>{topic=b.dataset.topic;draw();});
 search.addEventListener('input',draw);
 function revealHash(){
  const card=cards.find(c=>'#'+c.id===location.hash);if(!card)return;
  topic='전체';search.value='';draw();
  requestAnimationFrame(()=>card.scrollIntoView({block:'start'}));
 }
 window.addEventListener('hashchange',revealHash);draw();revealHash();
})();
