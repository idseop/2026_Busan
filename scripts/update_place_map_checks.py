from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'web/final/index.html';s=p.read_text(encoding='utf-8').replace('<div class="map-context"><p','<div class="map-context"><h2>부산광역시</h2><p');p.write_text(s,encoding='utf-8')
p=R/'scripts/check_result_map.py';s=p.read_text(encoding='utf-8').replace("'OpenStreetMap' in page.locator('.leaflet-control-attribution').inner_text()","'SGIS' in page.locator('.leaflet-control-attribution').inner_text()")
a=s.index("  mode['fail']=True;");b=s.index("  check('no_external_dependencies'",a)
s=s[:a]+'''  check('no_roads_or_tiles',page.locator('.leaflet-tile').count()==0 and not tile_requests)
  check('local_dong_names',page.evaluate('BUSAN_PLACE_LABELS.places.length===206 && BUSAN_MAP_VIEW.getState().localOnly'))
  page.evaluate('BUSAN_MAP_VIEW.map.setZoom(14)');page.wait_for_timeout(300)
  check('dong_labels_on_zoom',page.locator('.dong-name:visible').count()>0)
  check('plain_text_labels',page.locator('.place-name:visible').first.evaluate("e=>getComputedStyle(e).backgroundColor==='rgba(0, 0, 0, 0)' && getComputedStyle(e).boxShadow==='none'"))
  check('label_collisions',page.evaluate("""()=>{const a=[...document.querySelectorAll('.place-name')].filter(e=>e.style.display!=='none').map(e=>e.querySelector('span').getBoundingClientRect());return a.every((r,i)=>a.slice(i+1).every(v=>r.right<=v.left||v.right<=r.left||r.bottom<=v.top||v.bottom<=r.top));}"""))
  page.goto((WEB/'index.html').as_uri());page.wait_for_timeout(300);check('file_local_map',not tile_requests and page.locator('#tile-status').is_hidden() and page.locator('.map-region').count()==16)
''' +s[b:]
s=s.replace("'tile_policy':'All OSM URLs intercepted and fulfilled with synthetic local SVG or deliberately aborted. No real tiles downloaded. All other external requests blocked. Real basemap visual verification belongs to parent.'","'tile_policy':'Local administrative map: all external requests blocked; no road or raster tile layers permitted.'")
p.write_text(s,encoding='utf-8')
p=R/'scripts/view_result_map.py';s=p.read_text(encoding='utf-8').replace('window.BUSAN_MAP_VIEW?.getState().loadedTiles > 0','window.BUSAN_MAP_VIEW?.getState().localOnly').replace('Headed initial view and one requested regional result; no tile prefetch, area sweep or tile archives.','Headed local place-map initial and selected result inspection. No external tiles.');p.write_text(s,encoding='utf-8')
p=R/'scripts/package_result_map.py';s=p.read_text(encoding='utf-8').replace("live['state']['loadedTiles']>0 and not live['errors']","live['state']['localOnly'] and live['state']['loadedTiles']==0 and not live['errors'] and not live['requests']");p.write_text(s,encoding='utf-8')
