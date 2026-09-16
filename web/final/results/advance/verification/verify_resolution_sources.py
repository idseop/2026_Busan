"""Independent source-level checks; do not edit authored evidence."""
from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as ET
import pandas as pd
from html.parser import HTMLParser
O=Path(__file__).resolve().parent;B=O.parent;R=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
checks=[];sources=[]
def check(name,value):
 checks.append({'check':name,'pass':bool(value)})
class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):self.parts.append(data.strip())
def text(name):
 parser=TextParser();parser.feed((B/'traffic'/f'{name}.html').read_text(encoding='utf-8'));return ' '.join(parser.parts)
r=read(B/'response/resolution-evidence.json');prior=R/Path(r['prior_input'])
check('previous inspection input hash',sha(prior)==r['prior_sha256'])
f=pd.read_csv(prior).fillna('');bad=f[f.fire_facility_result.str.contains('불량')|f.escape_firewall_result.str.contains('불량')]
check('19 defect rows',len(bad)==r['prior_defect_rows']==19)
check('6 onsite corrections noted',int(bad.onsite_correction_recorded.sum())==r['prior_onsite_correction_rows']==6)
check('13 not currently unresolved by inference',len(bad)-int(bad.onsite_correction_recorded.sum())==r['prior_no_correction_note_rows']==13 and r['confirmed_current_unresolved_defects'] is None)
check('zero new matches framed as search yield',r['new_completion_matches']==0 and '확보하지 못한' in r['interpretation'] and '첨부문서 전체' in r['source_limit'])
for rec in read(B/'response/manifest.json'):
 if rec.get('snapshot') and rec.get('sha256'):
  p=B/'response'/rec['snapshot'];check('response snapshot '+p.name,sha(p)==rec['sha256']);sources.append({'file':str(p.relative_to(R)),'sha256':sha(p)})
gm=read(B/'response/guideline-manifest.json');p=B/'response'/gm['file'];check('HWPX official original hash',sha(p)==gm['sha256'])
with zipfile.ZipFile(p) as z:
 paragraphs=[]
 for n in z.namelist():
  if n.startswith('Contents/section') and n.endswith('.xml'):
   root=ET.fromstring(z.read(n));paragraphs.extend(''.join(e.itertext()) for e in root.iter() if e.tag.endswith('}p'))
original='\n'.join(paragraphs)
for phrase in ['제8판','2026. 3.','장비 접근 및 사용이 가능한 시간','배터리(패치) 유효기간 초과','위치 정보(좌표)가 없을 경우','외부표출','보건소에서 정보를 수정','일요일 사용 가능 주','점검이력']:
 check('independent HWPX XML phrase '+phrase,phrase in original)
check('existing process acknowledged','기존월점검' in r['recommendation']['existing_process'])
for rec in read(B/'traffic/source-manifest.json'):
 if rec.get('file') and rec.get('sha256'):
  p=R/rec['file'];check('traffic snapshot '+rec['id'],sha(p)==rec['sha256']);sources.append({'file':str(p.relative_to(R)),'sha256':sha(p)})
t=read(B/'traffic/traffic-resolution.json');facts={v['id']:v for v in t['facts']}
check('Bujeon effect unavailable rather than not evaluated','미평가' not in facts['bujeon-2026']['status'] and '미확보' in facts['bujeon-2026']['status'])
for phrase in ['2026-02-05','부전역','제막식']:check('Bujeon ceremony '+phrase,phrase in text('bujeon-ceremony'))
for phrase in ['1,257','220','부전역']:check('Bujeon finance '+phrase,phrase in text('bujeon-finance'))
for phrase in ['49,625,750','48,520,000','1,105,750','2025-09-22','2025-09-23','20251107','2025-11-12','준공금','보험료']:check('Gwangan contract '+phrase,phrase in text('gwangan-contract-detail'))
check('Gwangan settlement arithmetic',49625750-1105750==48520000)
check('planned end not actual end','준공예정일10/20을 실제 준공일로 쓰지 않는다' in facts['gwangan-2025-payment']['limit'])
for phrase in ['2025.02.04','100,000,000','실시설계']:check('Sinpyeong design '+phrase,phrase in text('sinpyeong-design-full'))
for phrase in ['2025-03-10','09:00~21:00','11:30~14:00','남포사거리']:check('Nampo table '+phrase,phrase in text('nampo-cctv'))
for v in facts.values():check('no unverified spatial identity '+v['id'],v['same2023InspectionItemConfirmed'] is False and v['sameBdiSurveySegmentConfirmed'] is False)
out={'pass':all(v['pass'] for v in checks),'checks':checks,'checkedSourceHashes':sources,'scope':'Original saved official HTML and independent HWPX XML extraction. Search failure is not proof of no action; no on-site effectiveness validation.','correctionResolved':'Bujeon quantifiable effect not assessed -> evidence not acquired','authorFiles':{str(p.relative_to(R)):sha(p) for p in [B/'response/resolution-evidence.json',B/'traffic/traffic-resolution.json',B/'response/aed-guideline-v8.hwpx']}}
(O/'resolution-source-verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pass':out['pass'],'checks':len(checks),'failed':[v for v in checks if not v['pass']]},ensure_ascii=False))
assert out['pass']
