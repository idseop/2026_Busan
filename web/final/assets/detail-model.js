/* Region stories derived only from the frozen public aggregates. */
(() => {
  'use strict';
  const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const number=v=>Number(v).toLocaleString('ko-KR'),sum=a=>a.reduce((s,v)=>s+Number(v||0),0),share=(a,b)=>b?`${(100*a/b).toFixed(1)}%`:'—';
  const scopeNames={A:'전체 처리결과',B:'정상 처리',C:'정상 처리 · 운영성 신고 제외'};
  let indexedDeep=null,timeIndex;
  function times(context){
    const {deep,selection,year,scope,type}=context;
    if(!deep)return null;
    if(indexedDeep!==deep){
      indexedDeep=deep;timeIndex=new Map();
      const get=(ri,y,si,ti)=>{const key=[ri,y,si,ti].join('|');if(!timeIndex.has(key))timeIndex.set(key,{hours:Array(6).fill(0),weekdays:Array(7).fill(0),months:Array(12).fill(0)});return timeIndex.get(key);};
      deep.dayHour.forEach(([ri,y,si,ti,w,h,n])=>{const t=get(ri,y,si,ti);t.hours[h]+=n;t.weekdays[w]+=n;});
      deep.month.forEach(([ri,y,si,ti,m,n])=>get(ri,y,si,ti).months[m-1]+=n);
    }
    const out={hours:Array(6).fill(0),weekdays:Array(7).fill(0),months:Array(12).fill(0)},years=year==='all'?deep.meta.years:[+year],types=type==='all'?deep.meta.types:[type],si=deep.meta.scopes.indexOf(scope);
    deep.regions.filter(r=>r.district===selection.district&&(selection.kind==='district'||r.rawDong===selection.rawDong)).forEach(r=>years.forEach(y=>types.forEach(t=>{const record=timeIndex.get([r.index,y,si,deep.meta.types.indexOf(t)].join('|'));if(record)Object.keys(out).forEach(k=>record[k].forEach((v,i)=>out[k][i]+=v));})));
    return out;
  }
  function model(context){
    const {data,deep,services,selection,year,scope,type}=context;
    const matching=r=>r.district===selection.district&&(selection.kind==='district'||r.rawDong===selection.rawDong);
    const all=data.rawRegions.filter(r=>r.scope===scope&&matching(r)),rows=all.filter(r=>year==='all'||r.year===+year),value=r=>type==='all'?r.total:r.typeCounts[type]||0;
    const total=sum(rows.map(value)),mix=data.meta.types.map(t=>({name:t,count:sum(rows.map(r=>r.typeCounts[t]||0))})).sort((a,b)=>b.count-a.count),years=data.meta.years.map(y=>{const rs=all.filter(r=>r.year===y);return {year:y,count:rs.length?sum(rs.map(value)):null};});
    const timing=times(context),cases=(deep?.cases||[]).filter(c=>matching(c)&&(type==='all'||c.type===type)).map(c=>({...c,service:services?.cases?.find(s=>s.district===c.district&&s.rawDong===c.rawDong&&s.subtype===c.subtype)}));
    return {total,mix,years,timing,cases,hasRows:rows.length>0,period:year==='all'?'2020–2024년':`${year}년`,type:type==='all'?mix[0]?.name:type};
  }
  window.BUSAN_DETAIL_MODEL=model;
})();
