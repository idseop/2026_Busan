"""Save selected official outdoor-response evidence; never infer incident positions."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin
import json,hashlib,re,html,subprocess
import sys
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/후속입증-20260916/outdoor'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=[
('saha-jobbook-2026','https://lll.saha.go.kr/uploadFile/upload_files/BBS_20260512.pdf','2026년 일자리 가이드북'),
('choeup-chanmul-reply-2025','https://www.bisco.or.kr/custom/custom10/custom10_02/01/custom_01_view.asp?branch=00026&page=2&vocno=25000021','2025-01-14'),
('saha-night-plan-2026','https://council.saha.go.kr/job/contents.do?mId=0101020000','2026년 계획; 웹 갱신일 미확인'),
('geumjeong-guide-2025','https://www.busan.go.kr/nbtnewsBU/1677693','2025-04-22'),
('busan-beach-close-2025','https://www.busan.go.kr/nbtnewsBU/1696238','2025-09-09'),
('haeundae-extension-2025','https://www.haeundae.go.kr/board/view.do?boardId=BBS_0000067&dataSid=3143435&menuCd=DOM_000000401001000000','2025-06-02'),
('haeundae-visitors-2025','https://www.haeundae.go.kr/board/view.do?boardId=BBS_0000144&dataSid=3154777&menuCd=DOM_000000302003000000','2025-11-11'),
('dadaepo-saha-2026','https://www.saha.go.kr/news/view.do?curHo=346&mId=0100000000&nIdx=1988','2026-06-25'),
('geumjeong-patrol-recruit-2026','https://www.korea.kr/archive/recruitInfoView.do?dataId=388518','2026-07-08'),
]
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ['script','style']:self.skip+=1
 def handle_endtag(self,t):
  if t in ['script','style']:self.skip=max(0,self.skip-1)
 def handle_data(self,d):
  if not self.skip and d.strip():self.parts.append(d.strip())
def fetch(url,path):
 if not path.exists():
  try:
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:data=r.read()
   path.write_bytes(data)
  except Exception:
   subprocess.run(['curl.exe','-L','--fail','--max-time','45','-A','Mozilla/5.0','-o',str(path),url],check=True,capture_output=True)
 return path.read_bytes()
def main():
 manifest=[]
 selected=[r for r in SOURCES if not sys.argv[1:] or r[0] in sys.argv[1:]]
 for key,url,date in selected:
  p=OUT/(key+('.pdf' if url.endswith('.pdf') else '.html'))
  try:
   raw=fetch(url,p)
   if raw.startswith(b'%PDF'):
    import fitz
    doc=fitz.open(p);(OUT/(key+'.txt')).write_text('\n'.join(page.get_text() for page in doc),encoding='utf-8')
    manifest.append({'id':key,'url':url,'published':date,'acquired':'2026-09-16','file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'pages':len(doc)})
    continue
   s=raw.decode('utf-8',errors='replace');parser=Text();parser.feed(s)
   (OUT/(key+'.txt')).write_text('\n'.join(parser.parts),encoding='utf-8')
   entry={'id':key,'url':url,'published':date,'acquired':'2026-09-16','file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
   # Busan attachment URL is linked in the original page. Only first PDF.
   links=[html.unescape(x) for x in re.findall(r'href=[\"\']([^\"\']+)[\"\']',s)]
   pdfs=[x for x in links if '/comm/getFile?' in x and 'fileNo=1' in x]
   if pdfs and 'busan.go.kr/nbtnewsBU' in url:
    u=urljoin(url,pdfs[0]);q=OUT/(key+'.pdf');data=fetch(u,q)
    if data.startswith(b'%PDF'):
     import fitz
     doc=fitz.open(q);(OUT/(key+'-pdf.txt')).write_text('\n'.join(page.get_text() for page in doc),encoding='utf-8')
     entry['pdf']={'url':u,'file':q.name,'sha256':hashlib.sha256(data).hexdigest(),'pages':len(doc)}
   manifest.append(entry)
  except Exception as e:manifest.append({'id':key,'url':url,'error':str(e),'acquired':'2026-09-16'})
 dest=OUT/'source-manifest.json'
 if dest.exists():
  old=json.loads(dest.read_text(encoding='utf-8'));manifest=[r for r in old if r['id'] not in {x['id'] for x in manifest}]+manifest
 dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{k:r[k] for k in ['id','bytes','error'] if k in r} for r in manifest],ensure_ascii=False))
 if all((OUT/(key+'.txt')).exists() for key in ['choeup-chanmul-reply-2025','geumjeong-guide-2025','dadaepo-saha-2026','busan-beach-close-2025','saha-night-plan-2026']):
  import csv
  facts=[
   {'case':'초읍동 산악','place':'어린이대공원 찬물샘 등산로','source':'choeup-chanmul-reply-2025','period':'2025-01-14 답변','status':'공식 답변으로 기존 설치 확인','finding':'돌출 뿌리·암석 보행 우려에 보행매트·목재 편책 설치. 흙길 이용 의견을 반영하여 불필요 구역 설치 지양 답변.','limit':'민원 1건과 기관 답변이며 사고원장·개선효과·신고 위치를 입증하지 않음. 초읍 신고를 이 등산로에 배정하지 않음.','candidate':'구간별 보행 상태·정비 이력·이용자 요구를 함께 연결. 일괄 매트 증설 보류.'},
   {'case':'금성동 산악','place':'금정산 북문 등산문화탐방지원센터 및 제3권역 개방등산로','source':'geumjeong-guide-2025','period':'2025-04-22 발표; 제3권역 휴식년제 2021-04-01~2026-03-31','status':'정비 완료 발표와 당시 안내 운영','finding':'북문로124 센터 매일09~18시. 지도사 해설은 예약 불필요하나 산림문화교육장 시설사용은 사전예약. 제9~21등산로 로프·표찰 정비 완료 발표.','limit':'2026현재 센터 지속운영·새 통제범위 확인 아님. 금성동 신고의 실제 등산로 배정 불가.','candidate':'과거 일반 안내 대신 출발 시점의 공식 탐방로·통제·지원센터 정보를 연결. 새 안전시설 설치안 보류.'},
   {'case':'우동 수난','place':'해운대해수욕장 및 부산8개 해수욕장','source':'busan-beach-close-2025','period':'2025-09-09 발표; 해운대9/14폐장','status':'개장중 시행 발표·폐장후 지속계획','finding':'취약시간 순찰·안전시설 점검·야간 입수통제·외국어 안내 등 시행. 폐장 후에도 안전요원·순찰·점검 계획.','limit':'해수욕장 전체가 우동만은 아님. 개별 운영 일지·우동 수난 신고의 해변 배정 미확보.','candidate':'개장·폐장을 무대응 여부로 변환하지 않고 해당 해변 관리조건과 확인시점을 함께 연결.'},
   {'case':'다대동 수난','place':'다대포 동측·서측 해수욕장','source':'dadaepo-saha-2026','period':'2026-06-25 발표; 7/1~8/31 운영','status':'개장 전 운영·안전시설 계획','finding':'감시탑2개소·고정식망루7개 설치 계획, 동측 우수관로 이설 완료 발표.','limit':'감시시설 계획은 준공·근무 이행 확인이 아님. 다대동 신고를 해수욕장에 배정하지 않음.','candidate':'동측 재개장 이후 구역별 안전관리 범위와 기존 감시시설을 먼저 대조. 증설 필요 미확정.'},
   {'case':'다대동 수난','place':'사하구 시설관리사업소 관리범위','source':'saha-night-plan-2026','period':'2026년 채용계획, 페이지 갱신일 미확인','status':'계획표상 사업 존재','finding':'야간 취약시간대 안전관리 연중 사업과 별도 해수욕장운영 사업 기재.','limit':'웹표16명과2026일자리PDF20명 등 버전차이 있어 실제배치수 해석 보류. 동측0표기는 안전인력0 증거 아님.','candidate':'야간 대응 신규 신설보다 구역·교대·실근무 일지 확인 후 기존 운영 연결.'},
  ]
  for row in facts:
   row['sourceUrl']=next(r[1] for r in SOURCES if r[0]==row['source']);row['acquired']='2026-09-16'
  (OUT/'outdoor-evidence.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding='utf-8')
  with (OUT/'outdoor-evidence.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(facts[0]));w.writeheader();w.writerows(facts)
  for key,pageno in [('geumjeong-guide-2025',1),('busan-beach-close-2025',2)]:
   import fitz
   doc=fitz.open(OUT/(key+'.pdf'));doc[pageno].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(OUT/(key+'-review-page.png'))
  checks=[]
  for item in manifest:
   if 'file' in item:
    checks.append({'test':item['id']+' source hash','passed':hashlib.sha256((OUT/item['file']).read_bytes()).hexdigest()==item['sha256']})
   if 'pdf' in item:
    checks.append({'test':item['id']+' PDF hash','passed':hashlib.sha256((OUT/item['pdf']['file']).read_bytes()).hexdigest()==item['pdf']['sha256']})
  for key,token in [('choeup-chanmul-reply-2025','불필요한'),('saha-night-plan-2026','야간 취약시간대 안전관리'),('dadaepo-saha-2026','감시탑 2개소'),('geumjeong-guide-2025-pdf','예약'),('busan-beach-close-2025-pdf','폐장 후에도')]:
   checks.append({'test':key+' adopted text','passed':token in (OUT/(key+'.txt')).read_text(encoding='utf-8')})
  (OUT/'author-checks.json').write_text(json.dumps({'checks':checks,'passed':sum(r['passed'] for r in checks),'failed':[r for r in checks if not r['passed']],'scope':'원문 해시와 채택 문구 확인. 독립 검증 아님.'},ensure_ascii=False,indent=2),encoding='utf-8')
  assert all(r['passed'] for r in checks)
if __name__=='__main__':main()
