"""Independent static integration review; browser run is recorded separately by root."""
from pathlib import Path
import json,re,hashlib
from urllib.parse import unquote
R=Path(__file__).resolve().parents[4];B=R/'data/processed/후속입증-20260916';O=R/'output/부산119-전지역후속검증-20260916';V=Path(__file__).parent
load=lambda p:json.loads(p.read_text(encoding='utf-8'));checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
html=(O/'index.html').read_text(encoding='utf-8');explorer=(O/'explorer.html').read_text(encoding='utf-8');md=(O/'보고서.md').read_text(encoding='utf-8');run=(O/'실행방법.txt').read_text(encoding='utf-8')
for name,text in [('index.html',html),('explorer.html',explorer)]:
 for u in re.findall(r'(?:href|src)="([^"]+)"',text):
  if u.startswith(('http:','https:','#','${')):continue
  ck('local link '+name+u,(O/unquote(u.split('#')[0])).is_file())
for command in ['scripts/collect_followup_services_20260916.py analyze','scripts/collect_followup_services_20260916.py report','analysis/00_공통/analyze_commerce_context_20260916.py']:
 ck('explicit reproduction '+command,command in run)
reg=load(O/'source-register.json');ck('all source classes',set(['traffic','services','outdoor','housing','commerce','living']).issubset(reg))
js=(O/'explorer-data.js').read_text(encoding='utf-8');data=json.loads(js[len('window.FOLLOWUP='):-1]);base=load(B/'analysis/all-region-followup.json')
ck('catalogue exact exported',data['catalogue']==base['catalogue'])
living=load(B/'living/living-context.json')
ck('all205 living profiles exported',data.get('living')==living['allDongProfiles'] and len(data.get('living',[]))==205)
ck('living fixed2024 independent controls','x.year===2024&&x.district===r.district&&x.rawDong===r.rawDong' in explorer and '신고 조건과 주민 연도 선택에 영향받지 않는 별도 배경' in explorer)
ck('living separate candidate display','후보 인구를 합산하지 않습니다.' in explorer)
ck('194 regions / 2910 records',len({(r['district'],r['rawDong']) for r in data['catalogue']})==194 and len(data['catalogue'])==2910)
for p in data['population']:ck('population101 sum '+str(p['code'])+str(p['year']),len(p['ages'])==101 and sum(p['ages'])==p['total'])
for token in ['DCLR_RCPT_NO','ACDNT_OCRN_LOT','DAMG_RGN_LAT','inspection-internal-rows.csv','address_internal','target_name']:
 ck('no private data '+token,token not in js and not (O/token).exists())
for marker in ['704,689','574,662','325','322','144','5,113.4','132','131','19','4,431','19,738','14,146','143,964','6,216','4,314','3,203','1,081']:
 ck('reported confirmed numeric '+marker,marker in html)
for text in ['현재 미해결 시설 목록으로 공개하거나','실제 고령자 표본이 아니라','체험복 실험','효과평가 계약 준공','방문객 수나 사고 노출량이 아닙니다','시제품을 사용해 실제 예방효과가 생겼다는 평가는 아직 수행하지 않았습니다']:
 ck('claim boundary '+text,text in html)
ck('all figures present',len(re.findall('<img ',html))>=10)
for p in O.glob('*.csv'):
 header=p.read_text(encoding='utf-8-sig').splitlines()[0];ck('public CSV schema '+p.name,not any(k in header for k in ['상가업소번호','상호명','DCLR_RCPT_NO','address_internal','target_name','ACDNT_OCRN']))
for name in ['index.html','explorer.html','explorer-data.js','보고서.md','실행방법.txt']:
 w=R/'web/final/results/followup'/name;ck('web copy '+name,w.exists() and w.read_bytes()==(O/name).read_bytes())
result={'passed':sum(c['passed'] for c in checks),'failed':[c for c in checks if not c['passed']],'checks':checks,'reviewedFiles':[{ 'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [O/'index.html',O/'explorer.html',O/'explorer-data.js',R/'docs/40-분석결과/부산-119-문제제기와보완논리-20260916.md']],'scope':'원 집계 대조와 공개 산출물·수치·주장·재현 명령 정적 검토. 브라우저 조작 검사는 별도 기록.'}
(V/'delivery-independent.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','reviewedFiles']},ensure_ascii=False));assert not result['failed']
