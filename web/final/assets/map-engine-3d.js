/* One camera for ground, verified boundaries and explicitly tagged OSM heights. */
window.BUSAN_CREATE_MAP_LEGACY=window.BUSAN_CREATE_MAP;
window.BUSAN_CREATE_MAP=({element,features,onSelect})=>{
 if(!window.maplibregl?.Map)return window.BUSAN_CREATE_MAP_LEGACY({element,features,onSelect});
 const status=document.getElementById('tile-status'),message=document.getElementById('tile-status-text');
 let selected='',counts={},theme='base',mode='2d',ready=false,contextReady=false,contextError='';
 const polygonRings=f=>(f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates);
 const bounds=f=>{const b=new maplibregl.LngLatBounds();(f.features||[f]).forEach(x=>polygonRings(x).forEach(p=>p[0].forEach(c=>b.extend(c))));return b;};
 const fullBounds=bounds(features),districts=new Map(features.features.map(f=>[f.properties.name,f]));
 const main={type:'FeatureCollection',features:features.features.map(f=>{const areas=polygonRings(f).map(p=>({p,a:Math.abs(p[0].slice(1).reduce((s,v,i)=>s+p[0][i][0]*v[1]-v[0]*p[0][i][1],0))})).sort((a,b)=>b.a-a.a);return {...f,geometry:{type:'MultiPolygon',coordinates:areas.slice(0,f.properties.name==='강서구'?2:1).map(x=>x.p)}};})};
 const style=JSON.parse(JSON.stringify(window.BUSAN_CONTEXT_STYLE));
 style.sources.busan={type:'geojson',data:features};
 style.sources.heightBuildings={type:'geojson',data:window.BUSAN_HEIGHT_BUILDINGS||{type:'FeatureCollection',features:[]}};
 style.sources.outside={type:'geojson',data:window.BUSAN_OUTSIDE_MASK};
 const boundaryLayers=[
  {id:'district-fill',type:'fill',source:'busan',paint:{'fill-color':'#80b7a0','fill-opacity':.035}},
  {id:'district-line',type:'line',source:'busan',paint:{'line-color':'#668b87','line-width':1.1,'line-opacity':.8}},
  {id:'district-selected',type:'fill',source:'busan',filter:['==',['get','name'],''],paint:{'fill-color':'#168b86','fill-opacity':.12}},
  {id:'district-selected-line',type:'line',source:'busan',filter:['==',['get','name'],''],paint:{'line-color':'#087c91','line-width':2.5}},
  {id:'explicit-height-buildings',type:'fill-extrusion',source:'heightBuildings',minzoom:13,layout:{visibility:'none'},paint:{'fill-extrusion-color':'#83a7ad','fill-extrusion-height':['get','height'],'fill-extrusion-base':0,'fill-extrusion-opacity':.94,'fill-extrusion-vertical-gradient':true}},
  {id:'outside-busan',type:'fill',source:'outside',paint:{'fill-color':'#eaf2f5','fill-opacity':1}}
 ];
 style.layers.push(...boundaryLayers);
 // A tight viewport bound would crop this tall city on wide PC screens.
 // Permit surrounding water-space while the polygon mask hides all other geography.
 const allowedBounds=[[fullBounds.getWest()-.4,fullBounds.getSouth()-.25],[fullBounds.getEast()+.4,fullBounds.getNorth()+.25]];
 let map;try{map=new maplibregl.Map({container:element,style,center:[129.06,35.18],zoom:10,minZoom:9,maxZoom:18,maxPitch:60,maxBounds:allowedBounds,attributionControl:false,renderWorldCopies:false,pitch:0,bearing:0,antialias:true});}catch(error){element.replaceChildren();return window.BUSAN_CREATE_MAP_LEGACY({element,features,onSelect});}
 map.addControl(new maplibregl.AttributionControl({compact:false,customAttribution:'<a href="https://www.data.go.kr/data/15129688/fileData.do">SGIS</a>'}),'bottom-right');
 map.invalidateSize=()=>map.resize();
 const controls=document.createElement('div');controls.className='map-scene-control';controls.innerHTML='<div class="scene-row" role="group" aria-label="지도 표시"><button data-theme="base" aria-pressed="true">일반지도</button><button data-theme="share" aria-pressed="false">접수 비중</button></div>';
 document.getElementById('map-viewport').append(controls);
 const tip=document.getElementById('map-tooltip');
 const markers=[];
 let focusPin=null,focusMarker=null,selectionKey='';
 const canonicalName=name=>String(name||'').trim().replace(/제(?=\d+동$)/,'');
 function clearFocus(){focusMarker?.remove();focusMarker=null;focusPin=null;}
 function showFocus(value){
  clearFocus();focusPin={...value};const e=document.createElement('div');e.className='scene-focus-pin';
  const dot=document.createElement('span');dot.className='scene-focus-dot';dot.setAttribute('aria-hidden','true');
  const text=document.createElement('span');text.textContent=value.name+' · '+(value.kind==='background'?'배경 지역':'선택 구·군');
  e.append(dot,text);e.setAttribute('role','status');
  focusMarker=new maplibregl.Marker({element:e,anchor:'left',offset:[-6,0],pitchAlignment:'viewport',rotationAlignment:'viewport'}).setLngLat([value.lng,value.lat]).addTo(map);labels();
 }
 function districtFocus(){const p=window.BUSAN_MAP_LABELS?.[selected];if(p)showFocus({kind:'district',district:selected,name:selected,lng:p[0],lat:p[1],baseDate:null});else clearFocus();}
 function focusPlace({district,name}={}){
  const rows=(window.BUSAN_PLACE_LABELS?.places||[]).filter(x=>x.district===district&&canonicalName(x.name)===canonicalName(name));
  if(district!==selected||rows.length!==1||!ready)return false;
  const x=rows[0];if(!Number.isFinite(x.lng)||!Number.isFinite(x.lat))return false;
  showFocus({kind:'background',district,name:x.name,lng:x.lng,lat:x.lat,baseDate:window.BUSAN_PLACE_LABELS.metadata.baseDate});
  map.flyTo({center:[x.lng,x.lat],zoom:14,pitch:mode==='3d'?52:0,duration:650});return true;
 }
 function label(name,position,kind,district){
  const e=document.createElement('button');e.type='button';e.className='scene-label '+kind;e.textContent=name;e.setAttribute('aria-label',name);e.onclick=()=>onSelect({kind:'district',district});
  const marker=new maplibregl.Marker({element:e,anchor:'center',pitchAlignment:'viewport',rotationAlignment:'viewport'}).setLngLat(position).addTo(map);
  markers.push({marker,e,name,kind,district,position});
 }
 Object.entries(window.BUSAN_MAP_LABELS||{}).forEach(([name,p])=>label(name,p,'gu-label',name));
 (window.BUSAN_PLACE_LABELS?.places||[]).forEach(x=>label(x.name,[x.lng,x.lat],'dong-label',x.district));
 function labels(){
  const used=[],w=element.clientWidth,h=element.clientHeight,z=map.getZoom(),total=Object.values(counts).reduce((a,b)=>a+b,0);
  if(focusPin){const p=map.project([focusPin.lng,focusPin.lat]);used.push({l:p.x-9,r:p.x+190,t:p.y-13,b:p.y+13});}
  for(const x of markers){const p=map.project(x.position),gu=x.kind==='gu-label';
   x.e.textContent=x.name+(gu&&theme==='share'?' '+(total?((counts[x.name]||0)/total*100).toFixed(1)+'%':'자료 없음'):'');
   x.e.classList.toggle('selected',x.district===selected);const width=x.e.textContent.length*(gu?17:13),height=gu?25:20,box={l:p.x-width/2,r:p.x+width/2,t:p.y-height/2,b:p.y+height/2};
   const show=(gu||z>=12.2)&&box.l>10&&box.r<w-10&&box.t>40&&box.b<h-45&&!used.some(b=>box.l<b.r+6&&box.r>b.l-6&&box.t<b.b+5&&box.b>b.t-5);
   x.e.hidden=!show;if(show)used.push(box);
  }
 }
 function themeUpdate(){
  if(ready){
   const deep=[...new Set((window.BUSAN_FINAL_CASES?.cases||[]).map(x=>x.district))];
   map.setPaintProperty('district-fill','fill-color',theme==='cases'?['case',['in',['get','name'],['literal',deep]],'#e1b873','#80b7a0']:'#80b7a0');
   map.setPaintProperty('district-fill','fill-opacity',theme==='cases'?.2:.035);
   map.setFilter('district-selected',['==',['get','name'],selected]);map.setFilter('district-selected-line',['==',['get','name'],selected]);
  }
  controls.querySelectorAll('[data-theme]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.theme===theme)));labels();note();
 }
 function note(){}
 function setMode(value){mode=value;controls.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));if(ready)map.setLayoutProperty('explicit-height-buildings','visibility',mode==='3d'?'visible':'none');map.easeTo({pitch:mode==='3d'?52:0,bearing:mode==='2d'?0:map.getBearing(),duration:500});note();}
 controls.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
 controls.querySelectorAll('[data-theme]').forEach(b=>b.onclick=()=>{theme=b.dataset.theme;themeUpdate();});
 function fit(which='all'){map.resize();const f=which==='selected'&&districts.has(selected)?districts.get(selected):which==='main'?main:features;map.fitBounds(bounds(f),{padding:{top:65,right:35,bottom:55,left:35},maxZoom:which==='selected'?14:12,duration:450,pitch:mode==='3d'?52:0,bearing:0});}
 map.on('style.load',()=>{ready=true;themeUpdate();setMode(mode);fit(selected?'selected':'main');});
 map.on('idle',()=>{if(map.getSource('openmaptiles')&&map.isSourceLoaded('openmaptiles')){contextReady=true;contextError='';status.hidden=true;}labels();});
 map.on('error',e=>{contextError=String(e.error?.message||'network');message.textContent='배경 연결이 원활하지 않습니다. 지역 집계와 경계는 계속 확인할 수 있습니다.';status.hidden=false;});
 map.on('move',labels);map.on('resize',labels);
 map.on('click','district-fill',e=>{if(e.features?.length)onSelect({kind:'district',district:e.features[0].properties.name});});
 map.on('mousemove','district-fill',e=>{if(!e.features?.length)return;const name=e.features[0].properties.name;tip.textContent=name+' · '+(counts[name]||0).toLocaleString('ko-KR')+'건';tip.hidden=false;tip.style.left=Math.min(e.point.x+15,element.clientWidth-180)+'px';tip.style.top=(e.point.y+15)+'px';map.getCanvas().style.cursor='pointer';});
 map.on('mouseleave','district-fill',()=>{tip.hidden=true;map.getCanvas().style.cursor='';});
 new ResizeObserver(()=>{map.resize();labels();}).observe(element);
 const api={update(next,selection){counts={...next};const name=selection?.district||'',changed=name!==selected;const key=JSON.stringify([name,selection?.kind,selection?.rawDong||selection?.dong||'']);selected=name;if(key!==selectionKey){selectionKey=key;districtFocus();}themeUpdate();if(changed&&name&&ready)requestAnimationFrame(()=>fit('selected'));},fit,zoomIn:()=>map.zoomIn(),zoomOut:()=>map.zoomOut(),retry:()=>{status.hidden=true;contextReady=false;contextError='';map.setStyle(JSON.parse(JSON.stringify(style)),{diff:false});},getCounts:()=>({...counts}),focusPlace,clearFocus,getState:()=>({focusPin:focusPin?{...focusPin}:null,zoom:map.getZoom(),minZoom:map.getMinZoom(),center:map.getCenter(),selected,theme,busanOnly:true,bounds:fullBounds.toArray(),contextReady,contextError,placeLabels:markers.length,online:location.protocol!=='file:',size:{x:element.clientWidth,y:element.clientHeight},mode,pitch:map.getPitch(),bearing:map.getBearing(),heightFootprints:window.BUSAN_HEIGHT_BUILDINGS?.features.length||0}),select:name=>{if(districts.has(name))onSelect({kind:'district',district:name});},map,getContextMap:()=>map,setMode};
 document.getElementById('tile-retry').onclick=api.retry;document.getElementById('filters-reset').addEventListener('click',()=>{clearFocus();selectionKey='';theme='base';setMode('2d');themeUpdate();fit('main');});
 window.BUSAN_MAP_VIEW=api;return api;
};
