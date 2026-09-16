"""Migrate the existing app's map adapter while retaining verified data rendering."""
from pathlib import Path
root=Path(__file__).resolve().parents[1];web=root/'web/final'
p=web/'assets/app.js';s=p.read_text(encoding='utf-8')
start=s.index('  const geometry=[];');end=s.index('  function setTab(',start)
s=s[:start]+'''  let mapView=null;
  function drawMap(){
    syncYears();const t=totals();
    $('map-context-text').textContent=`${period()} · ${scopeText[S.scope]} · ${typeName()}`;
    $('map-total').innerHTML=`<span>부산 전체 신고</span><strong>${n(sum([...t.values()]))}<small>건</small></strong>`;
    if(!$('map-total').closest('.left-footer'))$('left-panel').querySelector('.left-footer').prepend($('map-total'));
    if(!mapView)mapView=window.BUSAN_CREATE_MAP({element:$('district-map'),features:M,onSelect:selectRegion});
    mapView.update(Object.fromEntries(t),S.selection);$('map-empty').hidden=sum([...t.values()])>0;
  }
  function fit(mode='all'){mapView?.fit(mode==='main'?'selected':'all');}
  function zoom(factor){if(factor>1)mapView?.zoomIn();else mapView?.zoomOut();}
  function updateCamera(){mapView?.map.invalidateSize({pan:false});}
  function openLeft(){$('left-panel').classList.add('open');$('left-toggle').setAttribute('aria-expanded','true');}
  function closeLeft(){$('left-panel').classList.remove('open');$('left-toggle').setAttribute('aria-expanded','false');}
''' +s[end:]
p.write_text(s,encoding='utf-8')
p=web/'index.html';s=p.read_text(encoding='utf-8');s=s.replace('<script defer src="assets/detail-extension.js">','<script defer src="assets/detail-model.js"></script><script defer src="assets/basemap.js"></script><script defer src="assets/detail-extension.js">');s=s.replace('주요 지역 크게 보기','선택 지역 보기').replace('>크게</button>','>선택</button>');p.write_text(s,encoding='utf-8')
