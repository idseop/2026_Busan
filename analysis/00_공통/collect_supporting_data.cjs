// 공식 부산 보완자료 원본 수집. 사건 행과 임의 결합하지 않는다.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const raw = path.join(root, 'data/raw/보완자료');
const interim = path.join(root, 'data/interim/보완자료');
fs.mkdirSync(raw, {recursive:true});
fs.mkdirSync(interim, {recursive:true});
async function save(url, name, source) {
  const response = await fetch(url, {signal:AbortSignal.timeout(60000)});
  if (!response.ok) throw Error(`${response.status}: ${url}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  const destination = path.join(raw, name);
  if (fs.existsSync(destination)) throw Error(`원본 덮어쓰기 금지: ${name}`);
  fs.writeFileSync(destination, bytes, {flag:'wx'});
  const entry = {name, source, url, bytes:bytes.length, contentType:response.headers.get('content-type'), sha256:crypto.createHash('sha256').update(bytes).digest('hex'), receivedAt:new Date().toISOString()};
  console.log(JSON.stringify(entry));
  return entry;
}
(async()=>{
  const manifest=[];
  const welfare='https://www.data.go.kr/data/15042666/fileData.do';
  const html=await (await fetch(welfare)).text();
  fs.writeFileSync(path.join(interim,'노인복지관_공식목록.html'),html);
  const link=html.match(/"contentUrl":\s*"([^"]+)"/);
  if(!link) throw Error('공식 원본 다운로드 링크 없음');
  manifest.push(await save(link[1], '부산_노인복지관_15042666.csv',welfare));
  fs.writeFileSync(path.join(interim,'support-downloads.json'),JSON.stringify(manifest,null,2));
  const jobs='https://www.busan.go.kr/depart/welgrand02010103';
  const jobHtml=await (await fetch(jobs)).text();
  fs.writeFileSync(path.join(interim,'노인일자리_공식페이지.html'),jobHtml);
  const anchor=jobHtml.match(/href="([^"]+)"[^>]*>2026년 노인일자리 수행기관 및 사업 현황 다운로드/);
  if(!anchor) throw Error('2026년 공식 사업현황 링크 없음');
  const url=new URL(anchor[1].replaceAll('&amp;','&'),jobs).href;
  manifest.push(await save(url,'부산_노인일자리_2026.xlsx',jobs));
  fs.writeFileSync(path.join(interim,'support-downloads.json'),JSON.stringify(manifest,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
