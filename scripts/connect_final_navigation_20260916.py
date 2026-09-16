"""Connect the verified nine focus cases to map navigation; leave data totals intact."""
from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).resolve().parents[1];W=R/'web/final'
source=R/'data/processed/효과근거확장-20260916/temporal/focus-summary.json'
profiles=json.loads(source.read_text(encoding='utf-8'))
cases=[{'id':f'focus-{i+1}','district':x['district'],'rawDong':x['rawDong'],'type':x['type'],'subtype':x['subtype']} for i,x in enumerate(profiles)]
assert len(cases)==9 and all('벌집' not in x['subtype'] for x in cases)
registry={'period':[2020,2024],'scope':'C','sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cases':cases}
(W/'data/final-cases.js').write_text('window.BUSAN_FINAL_CASES='+json.dumps(registry,ensure_ascii=False)+';',encoding='utf-8')
p=W/'index.html';text=p.read_text(encoding='utf-8')
text=re.sub(r'<(?:button|a)[^>]*id="analysis-open"[^>]*>.*?</(?:button|a)>','<a id="analysis-open" class="text-button" href="results/complete/index.html">최종 결과</a>',text)
text=re.sub(r'<a class="text-button" href="results/(?:index.html|effects/index.html|(?:final|complete)/gallery.html)">.*?</a>','',text)
text=text.replace('<button id="about-open"','<a class="text-button" href="results/complete/gallery.html">그림 모음</a><button id="about-open"')
text=text.replace('경계·집계 기준 ⓘ','지도 정보 ⓘ')
if 'data/final-cases.js' not in text:text=text.replace('<script defer src="assets/detail-extension.js">','<script defer src="data/final-cases.js"></script><script defer src="assets/detail-extension.js">')
p.write_text(text,encoding='utf-8')
css=W/'assets/detail-extension.css';style=css.read_text(encoding='utf-8');instant='#year-buttons button{transition:none}'
if instant not in style:css.write_text(style+'\n'+instant+'\n',encoding='utf-8')
shutil.copy2(R/'output/부산119-전지역후속검증-20260916/explorer.html',W/'results/followup/explorer.html')
detail=W/'assets/detail-extension.js'
javascript=detail.read_text(encoding='utf-8')
function=''' function finalCaseLinks(c){
  const matches=finalCases().filter(x=>x.district===c.selection.district&&(c.selection.kind==='district'||x.rawDong===c.selection.rawDong)&&(c.type==='all'||c.type===x.type));
  const query=new URLSearchParams({district:c.selection.district,scope:'C'});
  if(c.selection.kind!=='district'&&c.selection.rawDong)query.set('dong',c.selection.rawDong);
  const section=document.createElement('section');section.className='final-case-links';section.dataset.extension='final-cases';
  section.innerHTML='<h3>지역 분석</h3><p>2020–2024 전체 · 정상 처리·운영성 제외 · 예방 관련 5개 유형의 별도 분석</p><a data-all-region-analysis href="results/followup/explorer.html?'+esc(query.toString())+'">지역 분석 전체 보기 →</a><div>'+matches.map(x=>`<a data-final-case="${esc(x.id)}" href="${esc(caseUrl(x))}"><strong>${esc(x.rawDong)} · ${esc(x.subtype)}</strong><span>신고 패턴부터 기존 대응·보완 결과까지 →</span></a>`).join('')+'</div>';
  c.content.prepend(section);
 }
'''
javascript=re.sub(r' function finalCaseLinks\(c\)\{.*?\n \}\n',lambda _:function,javascript,count=1,flags=re.S)
detail.write_text(javascript,encoding='utf-8')
backup=R/'data/processed/통합완성-20260916/previous-final-pages';backup.mkdir(parents=True,exist_ok=True)
for name in ['index.html','gallery.html','report.html']:
 old=W/'results/final'/name
 if not (backup/name).exists():shutil.copy2(old,backup/name)
 target='../complete/'+name
 old.write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}"><title>최신 부산 분석 결과로 이동</title><p><a href="{target}">최신 결과 보기</a></p></html>',encoding='utf-8')
(backup/'manifest.json').write_text(json.dumps([{'path':name,'sha256':hashlib.sha256((backup/name).read_bytes()).hexdigest()} for name in ['index.html','gallery.html','report.html']],ensure_ascii=False,indent=2),encoding='utf-8')
print('Connected',len(cases),'verified focus cases; map totals unchanged')
