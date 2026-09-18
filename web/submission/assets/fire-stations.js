(() => {
  const start = async () => {
    const view = window.BUSAN_MAP_VIEW;
    if (!view) return setTimeout(start, 200);
    const control = document.createElement('section');
    control.className='fire-station-control';
    control.innerHTML='<button type="button" class="fire-station-toggle" aria-pressed="true" disabled><span class="fire-station-icon" aria-hidden="true">119</span><span class="fire-station-caption"><strong>소방관서 위치</strong><span class="fire-station-count">불러오는 중…</span></span><span class="fire-station-state">표시 중</span></button><small>같은 위치의 관서는 함께 표시합니다.</small>';
    document.querySelector('.filter-grid').after(control);
    const toggle=control.querySelector('button'), count=control.querySelector('.fire-station-count');
    const markers=[];
    const popups=[];
    const closePopups=except=>{popups.forEach(p=>{if(p===except)return;if(typeof p.remove==='function')p.remove();if(typeof p.close==='function')p.close();});if(view.map.closePopup)view.map.closePopup();};
    try {
      const response=await fetch('data/fire-stations.json');
      if(!response.ok)throw Error('HTTP '+response.status);
      const data=await response.json(), groups=new Map();
      data.rows.forEach(row=>{const key=row.lon+','+row.lat;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row);});
      const fmt=v=>Number(v||0).toLocaleString('ko-KR');
      const content = rows => {
        const div=document.createElement('div');div.className='fire-station-popup';
        rows.forEach(row=>{
          const item=document.createElement('section'),name=document.createElement('strong'),type=document.createElement('small'),address=document.createElement('p'),stats=document.createElement('dl');
          name.textContent=row.name;type.textContent=row.type;address.textContent=row.address;
          const add=(label,value)=>{const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;stats.append(dt,dd);};
          add('자료상 인원', fmt(row.personnel)+'명');
          add('자료상 차량', fmt(row.vehicles)+'대');
          if(row.vehicleTypes)add('차량 유형', row.vehicleTypes);
          item.append(name,type,address,stats);div.append(item);
        });
        return div;
      };
      groups.forEach(rows=>{
        const row=rows[0];
        if(view.map.getCanvas && window.maplibregl){
          const el=document.createElement('button');el.type='button';el.className='fire-station-marker';el.textContent='119';
          el.title=rows.map(r=>r.name).join(' · ');el.setAttribute('aria-label',el.title+' 위치 정보');
          if(rows.length>1){const badge=document.createElement('span');badge.textContent=rows.length;el.append(badge);}
          const popup=new maplibregl.Popup({offset:18,maxWidth:'340px',closeOnClick:false,className:'fire-station-popup-shell'}).setDOMContent(content(rows));
          const marker=new maplibregl.Marker({element:el}).setLngLat([row.lon,row.lat]).addTo(view.map);
          popups.push(popup);
          el.addEventListener('click',e=>{e.stopPropagation();if(popup.isOpen()){popup.remove();return;}closePopups(popup);popup.setLngLat([row.lon,row.lat]).addTo(view.map);});
          markers.push({setVisible:show=>{el.hidden=!show;if(!show)popup.remove();}});
        }else if(window.L){
          const marker=L.marker([row.lat,row.lon],{icon:L.divIcon({className:'fire-station-leaflet',html:'<span>119</span>',iconSize:[28,28]})}).bindPopup(content(rows),{autoClose:true,closeOnClick:false}).addTo(view.map);
          marker.on('click',()=>{closePopups();marker.openPopup();});
          popups.push(marker.getPopup());
          markers.push({setVisible:show=>{if(show)marker.addTo(view.map);else{view.map.removeLayer(marker);marker.closePopup();}}});
        }
      });
      count.textContent=`${data.rows.length}개 · ${groups.size}곳`;
      if(view.map.getZoom){
        const size=()=>document.querySelectorAll('.fire-station-marker').forEach(el=>el.classList.toggle('compact',view.map.getZoom()<11.5));
        view.map.on('zoom',size);size();
      }
      toggle.disabled=false;
      toggle.onclick=()=>{const show=toggle.getAttribute('aria-pressed')!=='true';toggle.setAttribute('aria-pressed',String(show));control.querySelector('.fire-station-state').textContent=show?'표시 중':'숨김';if(!show)closePopups();markers.forEach(m=>m.setVisible(show));};
      window.BUSAN_FIRE_STATIONS={records:data.rows.length,locations:groups.size};
    }catch(error){count.textContent='불러오기 실패';toggle.setAttribute('aria-pressed','false');control.querySelector('.fire-station-state').textContent='사용 불가';toggle.disabled=true;console.error('소방관서 위치',error);}
  };
  start();
})();
