// 부산 119 접수 원본 전행 감사. 원본은 읽기만 하며 개별 신고는 출력하지 않는다.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const input = path.join(root, 'data/raw/119접수');
const output = path.join(root, 'data/interim/119접수감사');

// 청크 경계의 이중따옴표, CRLF, 인용 필드 안 줄바꿈을 보존한다.
function parser(onRow) {
  let row = [], field = '', state = 0, skipLF = false;
  const fieldEnd = () => { row.push(field); field = ''; state = 0; };
  const rowEnd = () => { fieldEnd(); onRow(row); row = []; };
  return {
    feed(s) {
      for (let i = 0; i < s.length; i++) {
        const c = s[i];
        if (skipLF) { skipLF = false; if (c === '\n') continue; }
        if (state === 1) { if (c === '"') state = 2; else field += c; continue; }
        if (state === 2 && c === '"') { field += '"'; state = 1; continue; }
        if (state === 2 && c !== ',' && c !== '\r' && c !== '\n') throw Error('닫힌 인용 필드 뒤 비구분자');
        if (c === ',') fieldEnd();
        else if (c === '\r' || c === '\n') { rowEnd(); skipLF = c === '\r'; }
        else if (c === '"') { if (field) throw Error('비인용 필드 안 따옴표'); state = 1; }
        else field += c;
      }
    },
    end() { if (state === 1) throw Error('닫히지 않은 인용 필드'); if (field || row.length || state === 2) rowEnd(); }
  };
}
function selfCheck() {
  const s = 'A,B\r\n"가,나","줄\n바꿈"\r\n"인용""문자",끝';
  const expected = [['A','B'],['가,나','줄\n바꿈'],['인용"문자','끝']];
  for (let size = 1; size < 16; size++) { const rows = []; const p = parser(r => rows.push(r)); for (let i = 0; i < s.length; i += size) p.feed(s.slice(i,i+size)); p.end(); assert.deepEqual(rows,expected); }
}
const add = (o,k) => { o[k] = (o[k] || 0) + 1; };
const walk = p => fs.readdirSync(p,{withFileTypes:true}).flatMap(e => e.isDirectory() ? walk(path.join(p,e.name)) : e.name.endsWith('.csv') ? [path.join(p,e.name)] : []);
const coordinateNames = ['ACDNT_OCRN_LOT','ACDNT_OCRN_LAT','DAMG_RGN_LOT','DAMG_RGN_LAT'];
const excluded = new Set(['DCLR_RCPT_NO','DCLR_DT','DCLR_YMD','DCLR_TM','RCPT_END_DT','RCPT_END_YMD','RCPT_END_TM',...coordinateNames]);
function coordStats() { return {bothBlank:0,partialBlank:0,nonNumeric:0,invalidWorldRange:0,validWorldRange:0,withinBroadBusanBox:0,outsideBroadBusanBox:0,minLon:null,maxLon:null,minLat:null,maxLat:null}; }
function coord(s,a,b) {
  if (!a && !b) { s.bothBlank++; return false; }
  if (!a || !b) { s.partialBlank++; return false; }
  const x=Number(a),y=Number(b);
  if (!Number.isFinite(x)||!Number.isFinite(y)) { s.nonNumeric++; return false; }
  if (Math.abs(x)>180||Math.abs(y)>90) { s.invalidWorldRange++; return false; }
  s.validWorldRange++;
  for (const [k,v,fn] of [['minLon',x,Math.min],['maxLon',x,Math.max],['minLat',y,Math.min],['maxLat',y,Math.max]]) s[k]=s[k]===null?v:fn(s[k],v);
  const inside=x>=128.7&&x<=129.4&&y>=34.85&&y<=35.45;
  s[inside?'withinBroadBusanBox':'outsideBroadBusanBox']++;
  return inside;
}
async function audit(file) {
  let headers, index, ids = new Set();
  const year=Number(path.basename(file).match(/20\d{2}/)[0]);
  const r={file:path.relative(root,file).replaceAll('\\','/'),year,bytes:fs.statSync(file).size,rows:0,blankRecords:0,malformedRows:0,missing:{},categories:{},id:{blank:0,unique:0,duplicates:0},date:{invalid:0,yearMismatch:0,componentMismatch:0,min:null,max:null,byDay:{},byMonth:{},missingDates:[]},coordinates:{incident:coordStats(),damage:coordStats()},busan:{rows:0,byDistrict:{},byType:{},bySubtype:{},coordinates:{incident:coordStats(),damage:coordStats()},byTypeCompleteness:{}},provinceMissing:{rows:0,byProcessingResult:{},byType:{},coordinates:{incident:coordStats(),damage:coordStats()}},schema:[]};
  const p=parser(values=>{
    if (!headers) {
      r.originalHeaders=values; headers=values.map(s=>s.replace(/^\uFEFF/,'').trim().toUpperCase()); r.schema=headers;
      if (new Set(headers).size!==headers.length) throw Error('중복 컬럼');
      index=Object.fromEntries(headers.map((h,i)=>[h,i]));
      for (const h of headers) { r.missing[h]=0; if (!excluded.has(h)) r.categories[h]={}; }
      return;
    }
    if (values.length===1&&!values[0]) {r.blankRecords++;return;}
    r.rows++;
    if (values.length!==headers.length) { r.malformedRows++; return; }
    values=values.map(s=>s.trim());
    const get=h=>values[index[h]]||'';
    for(let i=0;i<headers.length;i++){const h=headers[i],v=values[i];if(!v)r.missing[h]++;if(r.categories[h])add(r.categories[h],v||'(빈값)');}
    const id=get('DCLR_RCPT_NO');if(!id)r.id.blank++;else if(ids.has(id))r.id.duplicates++;else ids.add(id);
    const d=get('DCLR_YMD'),iso=d.slice(0,4)+'-'+d.slice(4,6)+'-'+d.slice(6,8);
    const dt=new Date(iso+'T00:00:00Z');
    if(!/^\d{8}$/.test(d)||!Number.isFinite(dt.getTime())||dt.toISOString().slice(0,10)!==iso)r.date.invalid++;
    else {add(r.date.byDay,d);add(r.date.byMonth,d.slice(0,6));if(Number(d.slice(0,4))!==year)r.date.yearMismatch++;if(get('DCLR_YR')!==d.slice(0,4)||get('DCLR_MM').padStart(2,'0')!==d.slice(4,6)||get('DCLR_DAY').padStart(2,'0')!==d.slice(6,8))r.date.componentMismatch++;if(r.date.min===null||d<r.date.min)r.date.min=d;if(r.date.max===null||d>r.date.max)r.date.max=d;}
    const a=get('ACDNT_OCRN_LOT'),b=get('ACDNT_OCRN_LAT'),c=get('DAMG_RGN_LOT'),dlat=get('DAMG_RGN_LAT');
    coord(r.coordinates.incident,a,b);coord(r.coordinates.damage,c,dlat);
    if(!get('CLMTY_CTPV_NM')) {
      r.provinceMissing.rows++;add(r.provinceMissing.byProcessingResult,get('PRCS_RSLT_SE_NM')||'(빈값)');add(r.provinceMissing.byType,get('EMRG_RSCU_ASSRT_NM')||'(빈값)');
      coord(r.provinceMissing.coordinates.incident,a,b);coord(r.provinceMissing.coordinates.damage,c,dlat);
    }
    if(get('CLMTY_CTPV_NM')==='부산광역시') {
      r.busan.rows++;const type=get('EMRG_RSCU_ASSRT_NM')||'(빈값)';add(r.busan.byDistrict,get('CLMTY_SGG_NM')||'(빈값)');add(r.busan.byType,type);
      add(r.busan.bySubtype,get('EMRG_RSCU_CLSF_NM')||'(빈값)');
      const ic=coord(r.busan.coordinates.incident,a,b),dc=coord(r.busan.coordinates.damage,c,dlat);
      const t=r.busan.byTypeCompleteness[type]??={rows:0,districtFilled:0,dongFilled:0,incidentBroadBox:0,damageBroadBox:0,eitherBroadBox:0,bothBroadBox:0};
      t.rows++;if(get('CLMTY_SGG_NM'))t.districtFilled++;if(get('CLMTY_EMD_NM'))t.dongFilled++;if(ic)t.incidentBroadBox++;if(dc)t.damageBroadBox++;if(ic||dc)t.eitherBroadBox++;if(ic&&dc)t.bothBroadBox++;
    }
  });
  const hash=crypto.createHash('sha256'),decoder=new TextDecoder('utf-8',{fatal:true});
  for await(const chunk of fs.createReadStream(file)){hash.update(chunk);p.feed(decoder.decode(chunk,{stream:true}));}
  p.feed(decoder.decode());p.end();r.sha256=hash.digest('hex');r.id.unique=ids.size;ids=null;
  // 집계 불일치는 성공 보고 대신 실행 실패로 처리한다.
  const sum=o=>Object.values(o).reduce((s,n)=>s+n,0);
  assert.equal(r.id.blank+r.id.unique+r.id.duplicates,r.rows-r.malformedRows);
  assert.equal(sum(r.date.byDay)+r.date.invalid,r.rows-r.malformedRows);
  assert.equal(sum(r.busan.byDistrict),r.busan.rows);
  for(const o of Object.values(r.categories))assert.equal(sum(o),r.rows-r.malformedRows);
  for(const [stats,n] of [[r.coordinates,r.rows-r.malformedRows],[r.busan.coordinates,r.busan.rows],[r.provinceMissing.coordinates,r.provinceMissing.rows]])for(const s of Object.values(stats))assert.equal(s.bothBlank+s.partialBlank+s.nonNumeric+s.invalidWorldRange+s.validWorldRange,n);
  for(let d=new Date(Date.UTC(year,0,1));d.getUTCFullYear()===year;d.setUTCDate(d.getUTCDate()+1)){const k=d.toISOString().slice(0,10).replaceAll('-','');if(!r.date.byDay[k])r.date.missingDates.push(k);}
  fs.writeFileSync(path.join(output,`${year}.json`),JSON.stringify(r,null,2)+'\n');
  console.log(JSON.stringify({year,rows:r.rows,busan:r.busan.rows,malformed:r.malformedRows,duplicates:r.id.duplicates,missingDates:r.date.missingDates.length}));
  return r;
}
async function main(){
  selfCheck();fs.mkdirSync(output,{recursive:true});const results=[];
  const files = walk(input).filter(f => /202[0-4]/.test(path.basename(f))).sort();
  assert.equal(files.length,5,'2020~2024년 원본 CSV 5개 필요');
  for(const f of files)results.push(await audit(f));
  assert.deepEqual(results.map(r=>r.year).sort(),[2020,2021,2022,2023,2024]);
  results.sort((a,b)=>a.year-b.year);
  const report={auditedAt:new Date().toISOString(),method:'UTF-8 엄격 디코딩, 인용 줄바꿈 지원 CSV 전행 스트리밍. 빈값은 trim 후 빈 문자열. ID 중복은 연도별만 검사.',broadBox:{west:128.7,east:129.4,south:34.85,north:35.45,note:'품질 점검용 넓은 직사각형이며 부산 경계 판정이나 좌표계 검증이 아님.'},rows:results.reduce((s,r)=>s+r.rows,0),busanRows:results.reduce((s,r)=>s+r.busan.rows,0),files:results};
  fs.writeFileSync(path.join(output,'audit.json'),JSON.stringify(report,null,2)+'\n');
  const lines=['# 부산 119 신고접수 원본 전행 감사','',`전체 ${report.rows.toLocaleString('ko-KR')}행, 재난 시도명이 부산광역시인 ${report.busanRows.toLocaleString('ko-KR')}행을 확인했다. 원본을 수정하거나 가짜 좌표·연령을 생성하지 않았다.`,'','| 연도 | 전체 행 | 부산 재난 행 | ID 중복 | 열 수 오류 | 날짜가 없는 일수 |','|---|---:|---:|---:|---:|---:|',...results.map(r=>`| ${r.year} | ${r.rows} | ${r.busan.rows} | ${r.id.duplicates} | ${r.malformedRows} | ${r.date.missingDates.length} |`),'','- 개별 행·접수번호는 산출물에 저장하지 않았다. 연도별 JSON에 모든 컬럼의 결측 수, 범주 빈도, 일별·월별 건수, 지역·유형별 공간정보 채움 수를 기록했다.','- 날짜가 모두 있다고 모든 신고가 누락 없이 제공됐다는 의미는 아니다. 기관 대조 통계와 추출 기준은 별도 확인이 필요하다.','- 2024년 컬럼 소문자·배열 차이는 감사 과정에서만 대문자 이름으로 대응했다.','- 부산 필터는 관할 기관이 아닌 CLMTY_CTPV_NM의 부산광역시 값이다. 위치 누락 행을 부산 외 지역으로 간주하지 않는다.','- 좌표 통계는 WGS84 범위와 넓은 부산 직사각형을 점검했으며 공식 경계 포함 여부·좌표계는 확정하지 않았다.','- 현재 컬럼에는 연령·생년월일·노인·아동 대상 식별 변수가 없다. 질병·사고 유형을 연령으로 대체할 수 없다.','- 원본 행은 신고접수 단위다. 접수번호 중복이 없더라도 같은 사고에 대한 여러 신고를 제거했다고 볼 수 없다.','','출처: 사용자가 제공한 부산소방재난본부 119신고접수 원본 CSV, 2018~2024. 정확한 원본 경로와 SHA-256은 audit.json 참조.',''];
  fs.writeFileSync(path.join(output,'README.md'),lines.join('\n'));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
