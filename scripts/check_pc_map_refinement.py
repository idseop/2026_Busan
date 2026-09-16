"""Independent desktop-map refinement QA. Existing public data must stay immutable."""
from pathlib import Path
import json,hashlib,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];WEB=ROOT/'web/final';OUT=ROOT/'data/processed/지도탐색웹-20260915/pc-refinement'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
SIZES=[(1920,1080),(1600,900),(1366,768)]
def geometry(p):
 return p.evaluate('''()=>{const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height}};const paths=[...document.querySelectorAll('.map-region')];const labels=[...document.querySelectorAll('.map-place-label')];const m=paths[0]?.getScreenCTM();return {viewport:box(document.querySelector('#map-viewport')),paths:paths.map(e=>({district:e.dataset.district,...box(e)})),labels:labels.map(e=>({district:e.dataset.district,...box(e)})),screenAreaScale:m?Math.abs(m.a*m.d-m.b*m.c):null}}''')
def large_geometry(p):
 return p.evaluate(r'''()=>{
 const transform=(x,y,m)=>new DOMPoint(x,y).matrixTransform(m), bounds=pts=>({x:Math.min(...pts.map(p=>p.x)),y:Math.min(...pts.map(p=>p.y)),width:Math.max(...pts.map(p=>p.x))-Math.min(...pts.map(p=>p.x)),height:Math.max(...pts.map(p=>p.y))-Math.min(...pts.map(p=>p.y))});
 const paths=[...document.querySelectorAll('.map-region')],major=[];
 paths.forEach(el=>{const m=el.getScreenCTM();const rings=[...el.getAttribute('d').matchAll(/M([^Z]+)Z/g)].map(x=>{const v=x[1].match(/-?\d+(?:\.\d+)?(?:e[+-]?\d+)?/gi).map(Number);const pts=[];for(let i=0;i<v.length;i+=2)pts.push({x:v[i],y:v[i+1]});const area=Math.abs(pts.reduce((a,p,i)=>{const q=pts[(i+1)%pts.length];return a+p.x*q.y-q.x*p.y},0)/2);return {pts,area}}).sort((a,b)=>b.area-a.area);rings.slice(0,el.dataset.district==='강서구'?2:1).forEach(r=>major.push({district:el.dataset.district,...bounds(r.pts.map(p=>transform(p.x,p.y,m)))}))});
 const features=window.BUSAN_MAP.features,rr=f=>f.geometry.type==='Polygon'?f.geometry.coordinates:f.geometry.coordinates.flat(),pts=features.flatMap(f=>rr(f).flat()),xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),xmin=Math.min(...xs),xmax=Math.max(...xs),ymax=Math.max(...ys),ymin=Math.min(...ys),cos=Math.cos(35.2*Math.PI/180),scale=Math.min(600/((xmax-xmin)*cos),480/(ymax-ymin)),bx=(800-(xmax-xmin)*cos*scale)/2,m=paths[0].getScreenCTM();
 const anchors=Object.entries(window.BUSAN_MAP_LABELS).map(([district,p])=>({district,...bounds([transform(bx+(p[0]-xmin)*cos*scale,48+(ymax-p[1])*scale,m)])}));
 const textFonts=[...document.querySelectorAll('.map-place-label text')].map(e=>({district:e.parentElement.dataset.district,screenPx:parseFloat(getComputedStyle(e).fontSize)*Math.hypot(e.getScreenCTM().a,e.getScreenCTM().b),stroke:getComputedStyle(e).stroke,strokeWidth:getComputedStyle(e).strokeWidth,paintOrder:getComputedStyle(e).paintOrder}));
 const sideFonts=[...document.querySelectorAll('#left-panel label,#left-panel select')].filter(e=>e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0).map(e=>({text:e.textContent.slice(0,30),px:parseFloat(getComputedStyle(e).fontSize)}));
 return {major,anchors,textFonts,sideFonts};}''')
def main():
 global OUT
 if '--large-before' in sys.argv:OUT=OUT/'large-before'
 OUT.mkdir(exist_ok=True,parents=True);checks=[];layouts=[];errors=[]
 def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
 baseline='--baseline' in sys.argv or '--large-before' in sys.argv
 data=json.loads((WEB/'data/dashboard.json').read_text(encoding='utf-8'))
 frozen=json.loads((ROOT/'data/processed/지도탐색웹-20260915/input_freeze.json').read_text(encoding='utf-8'))
 def counts(year):
  out={r['district']:0 for r in data['rawRegions']}
  for r in data['rawRegions']:
   if r['scope']=='A' and (year=='all' or r['year']==int(year)):out[r['district']]+=r['total']
  return out
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe',headless=True);p=b.new_page();p.context.set_offline(True);p.on('pageerror',lambda e:errors.append(str(e)))
  for width,height in SIZES:
   p.set_viewport_size({'width':width,'height':height});p.goto((WEB/'index.html').as_uri());p.wait_for_selector('#app:not([hidden])');p.add_style_tag(content='*{transition:none!important}')
   for state in ['initial','detail']:
    if state=='detail':
     el=p.locator('.map-place-label[data-district="기장군"]');el.focus();el.press('Enter')
    g=geometry(p);layouts.append({'width':width,'height':height,'state':state,**g})
    if '--large-before' in sys.argv:p.screenshot(path=str(OUT/f'{width}-{state}.png'))
    if not baseline:
     p.screenshot(path=str(OUT/f'{width}-{state}.png'))
     v=g['viewport'];inside=lambda x:x['x']>=v['x']-1 and x['y']>=v['y']-1 and x['x']+x['width']<=v['x']+v['width']+1 and x['y']+x['height']<=v['y']+v['height']+1
     large=large_geometry(p);g['largeAudit']=large
     check(f'{width}_{state}_major_land_inside',len(large['major'])==17 and all(inside(x) for x in large['major']))
     check(f'{width}_{state}_16_anchors_inside',len(large['anchors'])==16 and all(inside(x) for x in large['anchors']))
     check(f'{width}_{state}_sidebar_fonts_14',all(x['px']>=14 for x in large['sideFonts']),large['sideFonts'])
     check(f'{width}_{state}_label_screen_fonts_15',all(x['screenPx']>=14.99 for x in large['textFonts']),large['textFonts'])
     check(f'{width}_{state}_label_halo_visible',all(x['stroke']!='none' and float(x['strokeWidth'].removesuffix('px'))>0 and 'stroke' in x['paintOrder'] for x in large['textFonts']))
     check(f'{width}_{state}_labels_inside',len(g['labels'])==16 and all(inside(x) for x in g['labels']))
     overlaps=[]
     for i,a in enumerate(g['labels']):
      for z in g['labels'][i+1:]:
       if min(a['x']+a['width'],z['x']+z['width'])>max(a['x'],z['x'])+1 and min(a['y']+a['height'],z['y']+z['height'])>max(a['y'],z['y'])+1:overlaps.append([a['district'],z['district']])
     check(f'{width}_{state}_labels_no_overlap',not overlaps,overlaps)
     occlusion=p.evaluate('''()=>{const paths=[...document.querySelectorAll('.map-region')];return ['.map-tools','.map-total','.map-context','.map-legend'].flatMap(selector=>{const e=document.querySelector(selector);if(!e||!e.getClientRects().length)return [];const b=e.getBoundingClientRect();const hits=new Set();for(let i=0;i<7;i++)for(let j=0;j<7;j++){const screen=new DOMPoint(b.left+(i+.5)*b.width/7,b.top+(j+.5)*b.height/7);paths.forEach(path=>{if(path.isPointInFill(screen.matrixTransform(path.getScreenCTM().inverse())))hits.add(path.dataset.district)})}return hits.size?[{selector,districts:[...hits]}]:[]})}''')
     check(f'{width}_{state}_controls_do_not_cover_land',not occlusion,occlusion)
     check(f'{width}_{state}_no_page_overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1 && document.documentElement.scrollHeight<=innerHeight+1'))
     jargon=p.evaluate(r'''()=>{const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let node;const bad=[];while(node=walker.nextNode()){if(node.parentElement.closest('dialog,details,script,style'))continue;const range=document.createRange();range.selectNodeContents(node);if(![...range.getClientRects()].some(r=>r.width>0&&r.height>0))continue;const t=node.textContent.trim();if(/완전행|원문\s*동|참고\s*경계|\b[ABC]\b/.test(t))bad.push(t)}return bad}''')
     check(f'{width}_{state}_plain_visible_language',not jargon,jargon)
     if state=='detail':
      overlaps=p.locator('#detail-trend').evaluate('''e=>{const box=x=>x.getBoundingClientRect();const values=[...e.querySelectorAll('.value-label')], axes=[...e.querySelectorAll('.axis-label')].filter(x=>x.getAttribute('text-anchor')==='end');return values.flatMap(v=>axes.filter(a=>{const x=box(v),y=box(a);return Math.min(x.right,y.right)>Math.max(x.left,y.left)&&Math.min(x.bottom,y.bottom)>Math.max(x.top,y.top)}).map(a=>[v.textContent,a.textContent]))}''')
      check(f'{width}_trend_values_clear_of_y_axis',not overlaps,overlaps)
   if not baseline:
    p.locator('#map-reset').click();full=geometry(p);v=full['viewport'];check(f'{width}_full_fit_all_boundaries_inside',all(x['x']>=v['x']-1 and x['y']>=v['y']-1 and x['x']+x['width']<=v['x']+v['width']+1 and x['y']+x['height']<=v['y']+v['height']+1 for x in full['paths']));p.locator('#map-main').click()
    check(f'{width}_no_circle_quantity_encoding',p.locator('.map-symbol').count()==0)
    check(f'{width}_about_no_stale_circle_description','원의 면적' not in p.locator('#about-content').inner_text())
    for district in sorted(counts('all')):
     label=p.locator(f'.map-place-label[data-district="{district}"]');label.locator('text').click()
     check(f'{width}_{district}_actual_text_click',p.locator('#detail-content').get_attribute('data-district')==district and p.locator('#detail-content').get_attribute('data-kind')=='district')
     label.locator('text').hover();check(f'{width}_{district}_actual_text_hover',district in p.locator('#map-tooltip').inner_text() and f'{counts("all")[district]:,}' in p.locator('#map-tooltip').inner_text())
     label.focus();check(f'{width}_{district}_focus_count',f'{counts("all")[district]:,}' in (label.get_attribute('aria-label') or ''))
    el=p.locator('.map-place-label[data-district="기장군"]');el.focus();el.press('Enter')
    for year in ['all','2020','2021','2022','2023','2024']:
     button=p.locator(f'button[data-year="{year}"]');button.click();expected=counts(year)
     actual=p.locator('.map-region').evaluate_all('(es)=>Object.fromEntries(es.map(e=>[e.dataset.district,Number(e.dataset.count)]))')
     check(f'{width}_{year}_map_counts',actual==expected)
     check(f'{width}_{year}_year_control_sync',p.locator('#year').input_value()==year and button.get_attribute('aria-pressed')=='true' and p.locator('button[data-year][aria-pressed="true"]').count()==1)
     check(f'{width}_{year}_detail_sync',int(p.locator('#detail-content').get_attribute('data-total'))==expected['기장군'] and p.locator('#detail-content').get_attribute('data-year')==year)
     items=p.locator('#region-list [data-key]').evaluate_all('(es)=>es.map(e=>({district:e.dataset.district,count:Number(e.dataset.count)}))')
     check(f'{width}_{year}_list_sync',bool(items) and all(x['count']==expected[x['district']] for x in items))
    p.locator('#filters-reset').click();check(f'{width}_reset_year',p.locator('#year').input_value()=='all' and p.locator('button[data-year="all"]').get_attribute('aria-pressed')=='true' and p.locator('#right-panel').is_hidden())
    label=p.locator('.map-place-label[data-district="기장군"]');rect=label.bounding_box();p.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']/2);check(f'{width}_hover_count','기장군' in p.locator('#map-tooltip').inner_text() and f'{counts("all")["기장군"]:,}' in p.locator('#map-tooltip').inner_text());label.focus();check(f'{width}_focus_accessible_count',f'{counts("all")["기장군"]:,}' in (label.get_attribute('aria-label') or ''))
  if not baseline:
   deep=json.loads((WEB/'data/deep-data.json').read_text(encoding='utf-8'))
   for case in deep['cases']:
    p.locator('#filters-reset').click();p.locator('#list-raw').click();p.locator('#region-search').fill(case['rawDong']);p.locator(f'#region-list [data-key="{case["district"]}|{case["rawDong"]}"]').click();p.select_option('#type',case['type'])
    check(case['id']+'_story_three_routes',p.locator('.story-route [data-story-tab]').count()==3)
    p.locator('[data-tab="services"]').click()
    for scope in ['A','B','C']:
     p.select_option('#scope',scope)
     for year in ['all',*map(str,data['meta']['years'])]:
      p.locator(f'button[data-year="{year}"]').click();expected=sum(case['countsByScope'][scope]['yearCounts']) if year=='all' else case['countsByScope'][scope]['yearCounts'][data['meta']['years'].index(int(year))]
      node=p.locator('.case-observation');check(f'{case["id"]}_{scope}_{year}_helper_case_count',int(node.get_attribute('data-case-count'))==expected and node.get_attribute('data-year')==year and node.get_attribute('data-scope')==scope and node.get_attribute('data-case-id')==case['id'])
      model=p.evaluate('''arg=>{const c={data:BUSAN_DATA,deep:BUSAN_DEEP,services:BUSAN_CASE_SERVICES,selection:{kind:'raw',district:arg.district,rawDong:arg.rawDong},year:arg.year,scope:arg.scope,type:arg.type};const m=BUSAN_DETAIL_MODEL(c);return {total:m.total,hours:m.timing.hours.reduce((a,b)=>a+b,0),months:m.timing.months.reduce((a,b)=>a+b,0),cases:m.cases.map(x=>x.id)}}''',dict(district=case['district'],rawDong=case['rawDong'],year=year,scope=scope,type=case['type']))
      expectedregion=sum(r['typeCounts'].get(case['type'],0) for r in data['rawRegions'] if r['district']==case['district'] and r['rawDong']==case['rawDong'] and r['scope']==scope and (year=='all' or r['year']==int(year)))
      check(f'{case["id"]}_{scope}_{year}_helper_model',model['total']==model['hours']==model['months']==expectedregion and model['cases']==[case['id']])
    service_links=p.evaluate('''c=>{const r=BUSAN_CASE_SERVICES.cases.find(r=>r.district===c.district&&r.rawDong===c.rawDong&&r.subtype===c.subtype);return {expected:r.sourceIds.map(id=>BUSAN_CASE_SERVICES.sources.find(s=>s.id===id).url).sort(),actual:[...document.querySelectorAll('.response-service>a')].map(a=>a.getAttribute('href')).sort()}}''',case)
    check(case['id']+'_exact_service_sources',service_links['actual']==service_links['expected'])
    p.select_option('#type','화재');check(case['id']+'_unrelated_type_no_case',p.locator('.case-observation').count()==0)
   p.locator('#filters-reset').click();p.locator('.map-place-label[data-district="기장군"]').focus();p.locator('.map-place-label[data-district="기장군"]').press('Enter');p.locator('[data-tab="services"]').click();check('district_two_case_tabs',p.locator('[data-story-case]').count()==2)
   for button in p.locator('[data-story-case]').all():
    caseid=button.get_attribute('data-story-case');button.click();check('district_case_tab_'+caseid,p.locator('.case-observation').get_attribute('data-case-id')==caseid)
   p.set_viewport_size({'width':1600,'height':1000});p.locator('#filters-reset').click();p.locator('#list-raw').click();p.locator('#region-search').fill('기장읍');p.locator('#region-list [data-key="기장군|기장읍"]').click();p.locator('[data-tab="population"]').click();p.screenshot(path=str(OUT/'service-population.png'))
   p.locator('[data-tab="services"]').click();p.locator('#detail-content').evaluate('(e)=>e.scrollTop=0');p.screenshot(path=str(OUT/'service-response.png'));p.locator('#detail-content').evaluate('(e)=>e.scrollTop=e.scrollHeight');p.screenshot(path=str(OUT/'service-next.png'))
  b.close()
 if baseline:
  path=OUT/'baseline_layout.json'
  if path.exists():raise RuntimeError('Do not overwrite baseline')
  path.write_text(json.dumps({'layouts':layouts,'uiHashes':{str(x.relative_to(ROOT)):sha(x) for x in [WEB/'assets/app.js',WEB/'assets/style.css']}},ensure_ascii=False,indent=2),encoding='utf-8');print('baseline captured');return
 old=json.loads((OUT/'large-before/baseline_layout.json').read_text(encoding='utf-8'))
 for g,prior in zip(layouts,old['layouts']):
  check(f'{g["width"]}_{g["state"]}_screen_area_increased',g['screenAreaScale']>prior['screenAreaScale'],{'before':prior['screenAreaScale'],'after':g['screenAreaScale']})
 for item in frozen['files']:check('immutable_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
 check('no_browser_errors',not errors,errors)
 result={'passed':all(c['passed'] for c in checks),'checks':checks,'layouts':layouts,'uiHashes':{str(x.relative_to(ROOT)):sha(x) for x in [WEB/'index.html',WEB/'assets/app.js',WEB/'assets/style.css']},'scope':'PC refinement only. Scale comparison assumes same source geometry projection; source reviewed separately. No public input changes.'}
 result['status']='passed' if result['passed'] else 'failed'
 result['site_sha256']={str(x.relative_to(ROOT)):sha(x) for x in sorted(WEB.rglob('*')) if x.is_file()}
 for name in ['independent_review.json','result.json']:(OUT/name).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'passed':result['passed'],'checks':len(checks),'failures':[c for c in checks if not c['passed']]},ensure_ascii=False))
if __name__=='__main__':main()
