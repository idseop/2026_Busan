from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'web/final/index.html'
s=p.read_text(encoding='utf-8').replace('<script defer src="data/map-data.js"></script>','<script defer src="data/map-data.js"></script><script defer src="data/map-labels.js"></script><script defer src="data/place-labels.js"></script>')
p.write_text(s,encoding='utf-8')
p=root/'web/final/assets/basemap.js'
s=p.read_text(encoding='utf-8')
s=s.replace('/* Normal browser tile loading only. No prefetch, download or tile archives. */','/* Local administrative place map. No road, building, POI or tile layers. */')
s=s.replace("let selected='',counts={},loaded=0,failed=0,tiles=null;","let selected='',counts={};")
s=s.replace("fillColor:'#1492a3',fillOpacity:name===selected?.12:.015","fillColor:name===selected?'#a4d5c0':'#cee3bf',fillOpacity:1")
start=s.index(' function notice(');end=s.index(" fit('main');",start)
s=s[:start]+''' function connect(){status.hidden=true;}
 const placeLabels=[];
 function addLabel(name,lat,lng,kind,district=''){
  const node=document.createElement('span');node.textContent=name;
  const marker=L.marker([lat,lng],{interactive:false,keyboard:false,icon:L.divIcon({className:'place-name '+kind,html:node,iconSize:[1,1],iconAnchor:[0,0]})}).addTo(map);
  placeLabels.push({marker,name,kind,district});
 }
 Object.entries(window.BUSAN_MAP_LABELS||{}).forEach(([name,[lng,lat]])=>addLabel(name,lat,lng,'district-name',name));
 (window.BUSAN_PLACE_LABELS?.places||[]).forEach(p=>addLabel(p.name,p.lat,p.lng,'dong-name',p.district));
 function layoutLabels(){
  const used=[],size=map.getSize(),zoom=map.getZoom();
  const sorted=[...placeLabels].sort((a,b)=>(a.kind==='district-name'?0:1)-(b.kind==='district-name'?0:1));
  for(const item of sorted){
   const el=item.marker.getElement(),p=map.latLngToContainerPoint(item.marker.getLatLng()),w=item.name.length*(item.kind==='district-name'?18:14)+10,h=item.kind==='district-name'?26:22;
   const r={l:p.x-w/2,r:p.x+w/2,t:p.y-h/2,b:p.y+h/2};
   const show=(item.kind==='district-name'||zoom>=12.5)&&r.l>5&&r.r<size.x-5&&r.t>55&&r.b<size.y-50&&!used.some(v=>r.l<v.r+5&&r.r>v.l-5&&r.t<v.b+4&&r.b>v.t-4);
   el.style.display=show?'':'none';el.classList.toggle('selected-place',item.kind==='district-name'&&item.district===selected);
   if(show)used.push(r);
  }
 }
 map.on('zoomend moveend resize',layoutLabels);
 map.attributionControl.addAttribution('<a href="https://www.data.go.kr/data/15129688/fileData.do">SGIS</a>');
''' +s[end:]
s=s.replace("mask.getElement().classList.add('busan-outside-mask');connect();","mask.getElement().classList.add('busan-outside-mask');connect();layoutLabels();")
s=s.replace('updatePaths();if(changed&&name)','updatePaths();layoutLabels();if(changed&&name)')
s=s.replace("loadedTiles:loaded,failedTiles:failed,online:location.protocol!=='file:'","loadedTiles:0,failedTiles:0,localOnly:true,placeLabels:placeLabels.length,online:false")
p.write_text(s,encoding='utf-8')
