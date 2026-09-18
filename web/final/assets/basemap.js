/* Local administrative place map. No road, building, POI or tile layers. */
window.BUSAN_CREATE_MAP=({element,features,onSelect})=>{
 const map=L.map(element,{zoomControl:false,attributionControl:true,zoomSnap:.25,minZoom:8,maxZoom:18,maxBoundsViscosity:1,preferCanvas:false});
 const status=document.getElementById('tile-status'),message=document.getElementById('tile-status-text');
 let selected='',counts={},contextLayer=null,contextReady=false,contextError='',theme='base';
 const deepDistricts=new Set((window.BUSAN_DEEP?.cases||[]).map(c=>c.district));
 function style(name){
  return {color:name===selected?'#087c91':theme==='cases'&&deepDistricts.has(name)?'#ba7e21':'#407587',weight:name===selected?2.5:theme==='cases'&&deepDistricts.has(name)?2.2:1.1,opacity:name===selected?.95:.55,fillColor:theme==='cases'&&deepDistricts.has(name)?'#efc77c':name===selected?'#a4d5c0':'#cee3bf',fillOpacity:theme==='cases'&&deepDistricts.has(name)?.3:contextReady?(name===selected?.17:.015):1};
 }
 const layers=new Map(),geo=L.geoJSON(features,{style:f=>style(f.properties.name),onEachFeature:(f,layer)=>{const name=f.properties.name;layers.set(name,layer);layer.on('click',()=>onSelect({kind:'district',district:name}));layer.on('mouseover',()=>layer.setStyle({weight:2,color:'#07697f'}));layer.on('mouseout',()=>layer.setStyle(style(name)));}}).addTo(map);
 function updatePaths(){layers.forEach((layer,name)=>{const path=layer.getElement();if(!path)return;path.classList.add('map-region');path.dataset.district=name;path.dataset.count=counts[name]||0;path.setAttribute('tabindex','0');path.setAttribute('role','button');path.setAttribute('aria-label',`${name} ${(counts[name]||0).toLocaleString('ko-KR')}건`);path.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();onSelect({kind:'district',district:name});}};let title=path.querySelector('title');if(!title){title=document.createElementNS('http://www.w3.org/2000/svg','title');path.append(title);}title.textContent=path.getAttribute('aria-label');});}
 const mainPoints=[];features.features.forEach(f=>{const polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates,area=p=>Math.abs(p[0].slice(1).reduce((s,v,i)=>s+p[0][i][0]*v[1]-v[0]*p[0][i][1],0));[...polygons].sort((a,b)=>area(b)-area(a)).slice(0,f.properties.name==='강서구'?2:1).forEach(p=>p[0].forEach(([x,y])=>mainPoints.push([y,x])));});
 const mainBounds=L.latLngBounds(mainPoints);
 // Hide all geography outside the verified Busan polygons, including tile labels.
 map.createPane('busanMask');map.getPane('busanMask').style.zIndex=250;map.getPane('busanMask').style.pointerEvents='none';
 const maskRings=[[[-85,-180],[-85,180],[85,180],[85,-180]]];
 features.features.forEach(f=>{const polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;polygons.forEach(p=>p.forEach(r=>maskRings.push(r.map(([x,y])=>[y,x]))));});
 const mask=L.polygon(maskRings,{pane:'busanMask',interactive:false,stroke:false,fill:true,fillColor:'#eaf2f5',fillOpacity:1,fillRule:'evenodd',smoothFactor:0}).addTo(map);
 const allowedBounds=geo.getBounds().pad(.025);map.setMaxBounds(allowedBounds);
 function refreshMinZoom(){map.options.minZoom=8;map.setMinZoom(map.getBoundsZoom(geo.getBounds(),false,L.point(50,50)));}
 function fit(mode='all'){map.invalidateSize();refreshMinZoom();if(mode==='selected'&&layers.has(selected))map.fitBounds(layers.get(selected).getBounds(),{padding:[36,40],maxZoom:13,animate:false});else map.fitBounds(mode==='all'?geo.getBounds():mainBounds,{padding:[25,25],maxZoom:12,animate:false});updatePaths();}
 function connect(){
  if(contextLayer){map.removeLayer(contextLayer);contextLayer=null;}
  contextReady=false;contextError='';status.hidden=true;
  if(location.protocol==='file:'){contextError='file';message.textContent='상세 지형은 실행.cmd로 열면 표시됩니다.';status.hidden=false;return;}
  if(!window.maplibregl||!L.maplibreGL){contextError='library';message.textContent='상세 지형을 불러오지 못했습니다. 지역 결과는 이용할 수 있습니다.';status.hidden=false;return;}
  try{
   contextLayer=L.maplibreGL({style:window.BUSAN_CONTEXT_STYLE,pane:'tilePane',interactive:false,attribution:'<a href="https://openfreemap.org/">OpenFreeMap</a> · © <a href="https://openmaptiles.org/">OpenMapTiles</a> · © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);
   const gl=contextLayer.getMaplibreMap();
   gl.on('error',e=>{contextError=String(e.error?.message||'network');message.textContent='상세 지형 연결이 원활하지 않습니다. 지역 결과는 이용할 수 있습니다.';status.hidden=false;});
   gl.on('idle',()=>{if(!gl.isSourceLoaded('openmaptiles'))return;contextReady=true;contextError='';status.hidden=true;layers.forEach((layer,d)=>layer.setStyle(style(d)));});
  }catch(e){contextError=String(e.message);message.textContent='상세 지형을 표시할 수 없습니다. 지역 결과는 이용할 수 있습니다.';status.hidden=false;}
 }
 map.fitBounds(mainBounds,{padding:[25,25],maxZoom:12,animate:false});
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
   const el=item.marker.getElement(),p=map.latLngToContainerPoint(item.marker.getLatLng()),w=item.name.length*(item.kind==='district-name'?18:14)+10,h=item.kind==='district-name'?(theme==='share'?45:26):22;
   const span=el.querySelector('span');span.textContent=item.name;
   if(theme==='share'&&item.kind==='district-name'){const total=Object.values(counts).reduce((a,b)=>a+b,0),small=document.createElement('small');small.textContent=total?`${((counts[item.name]||0)/total*100).toFixed(1)}%`:'자료 없음';span.append(small);}
   const r={l:p.x-w/2,r:p.x+w/2,t:p.y-h/2,b:p.y+h/2};
   const show=(item.kind==='district-name'||zoom>=12)&&r.l>5&&r.r<size.x-5&&r.t>55&&r.b<size.y-50&&!used.some(v=>r.l<v.r+5&&r.r>v.l-5&&r.t<v.b+4&&r.b>v.t-4);
   el.style.display=show?'':'none';el.classList.toggle('selected-place',item.kind==='district-name'&&item.district===selected);
   if(show)used.push(r);
  }
 }
 map.on('zoomend moveend resize',layoutLabels);
 map.attributionControl.addAttribution('<a href="https://www.data.go.kr/data/15129688/fileData.do">SGIS</a>');
 const themes=document.createElement('div');themes.className='map-theme-control';themes.innerHTML='<span>지도 주제</span><div><button data-map-theme="base" aria-pressed="true">지형·지역</button><button data-map-theme="share" aria-pressed="false">신고 분포</button><button data-map-theme="cases" aria-pressed="false">심층 분석 지역</button></div><p class="theme-key" hidden></p>';
 document.getElementById('map-viewport').append(themes);
 function applyTheme(){
  layers.forEach((layer,d)=>layer.setStyle(style(d)));
  themes.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mapTheme===theme)));
  const key=themes.querySelector('.theme-key');key.hidden=theme==='base';
  key.textContent=theme==='share'?'구·군 이름별 접수 비중 (%) · 선택 조건의 부산 신고 합계 기준':theme==='cases'?'기장군·연제구·북구의 4개 지역·유형 사례 · 고정 검토 대상':'';
  layoutLabels();
 }
 themes.querySelectorAll('button').forEach(b=>b.onclick=()=>{theme=b.dataset.mapTheme;applyTheme();});
 fit('main');map.setMinZoom(map.getBoundsZoom(geo.getBounds(),false,L.point(50,50)));mask.getElement().classList.add('busan-outside-mask');connect();layoutLabels();
 new ResizeObserver(()=>{map.invalidateSize({pan:false});refreshMinZoom();}).observe(element);
 const api={update(next,selection){counts={...next};const name=selection?.district||'',changed=name!==selected;selected=name;applyTheme();updatePaths();layoutLabels();if(changed&&name)requestAnimationFrame(()=>fit('selected'));},fit,zoomIn:()=>map.zoomIn(),zoomOut:()=>map.zoomOut(),retry:connect,getCounts:()=>({...counts}),getState:()=>({zoom:map.getZoom(),minZoom:map.getMinZoom(),center:map.getCenter(),selected,theme,busanOnly:true,bounds:allowedBounds.toBBoxString(),loadedTiles:0,failedTiles:0,localOnly:false,contextReady,contextError,placeLabels:placeLabels.length,online:location.protocol!=='file:',size:map.getSize()}),select:name=>{if(layers.has(name))onSelect({kind:'district',district:name});},map,getContextMap:()=>contextLayer?.getMaplibreMap()};
 document.getElementById('filters-reset').addEventListener('click',()=>{theme='base';applyTheme();});
 document.getElementById('tile-retry').onclick=connect;window.BUSAN_MAP_VIEW=api;return api;
};
