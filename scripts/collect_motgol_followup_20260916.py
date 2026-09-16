"""Official project follow-up snapshots. Council statements remain attributed, not incident registers."""
from pathlib import Path
import json,hashlib,concurrent.futures,re,html,subprocess
import fitz
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/동별보완-추가근거-20260916/followup';OUT.mkdir(parents=True,exist_ok=True)
sources=[
dict(id='namgu-investment-2025',url='https://www.bsnamgu.go.kr/open/2025/2en_1105/19.pdf',format='pdf',title='2025 남구 재정공시 투자심사사업 추진현황',reference='2025년 공시, 사업별 실적 기준 확인'),
dict(id='namgu-investment-2024',url='https://www.bsnamgu.go.kr/open/2024/2en/20.pdf',format='pdf',title='2024 남구 재정공시 투자심사사업 추진현황',reference='2024년 공시, 사업별 실적 기준 확인'),
dict(id='namgu-council-motgol-20241111',url='https://council.bsnamgu.go.kr/kr/activity/bbs?bbs_id=vod5&reform=view&uid=7D0F2EF5FEA059B6673DE6DBFBC4C083',format='html',title='못골시장 보행환경 개선사업에 대한 제언',reference='2024-11-11 5분 자유발언'),
]
def fetch(s):
    p=OUT/f"{s['id']}.{s['format']}"
    try:
        if not p.exists():
            completed=subprocess.run(['curl.exe','--fail','--location','--max-time','40',s['url']],capture_output=True,check=True)
            p.write_bytes(completed.stdout)
        raw=p.read_bytes()
        if s['format']=='pdf':
            assert raw.startswith(b'%PDF')
            doc=fitz.open(p);pages=[]
            for i,page in enumerate(doc):
                text=page.get_text()
                if '못골' in text:
                    pages.append({'pdfPage':i+1,'text':text})
                    page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(OUT/f"{s['id']}-page-{i+1}.png"))
            (OUT/f"{s['id']}-pages.json").write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
        else:
            text=html.unescape(re.sub('<[^>]+>','\n',raw.decode('utf-8')))
            text='\n'.join(x.strip() for x in text.splitlines() if x.strip())
            (OUT/f"{s['id']}.txt").write_text(text,encoding='utf-8')
            pages=[{'text':text}]
        return dict(**s,status='downloaded',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),localFile=str(p.relative_to(ROOT)),matchedPages=[x.get('pdfPage') for x in pages])
    except Exception as e:return dict(**s,status='unavailable',error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,sources))
query={'ctrtNm':'못골시장 일원 보행환경개선사업 효과평가','page':1,'rowNum':20,'ctrtYmdFr':'20200101','ctrtYmdTo':'20260916','ctrtGovCd':'','ctrtKindCd':'','custNm':'','ctrtAmtFr':'','ctrtAmtTo':''}
body=OUT/'evaluation-query.json';body.write_text(json.dumps(query,ensure_ascii=False),encoding='utf-8')
endpoint='http://contract.bsnamgu.go.kr/basis/ajaxSituationList.do'
try:
    raw=subprocess.run(['curl.exe','--fail','--location','--max-time','30','--data-binary','@'+str(body),endpoint],capture_output=True,check=True).stdout
    response=json.loads(raw);assert response.get('cmiosRtnCode')=='SUCC';assert response['totalCount']==len(response['dataList'])
    target=OUT/'evaluation-contract.json';target.write_bytes(raw)
    results.append(dict(id='namgu-evaluation-contract-2026',title='못골시장 일원 보행환경개선사업 효과평가용역 계약',url=endpoint,query=query,reference='계약일·계약기간은 원문 필드, 이행 완료와 구분',status='downloaded',sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),localFile=str(target.relative_to(ROOT))))
    for row in response['dataList']:
        url='http://contract.bsnamgu.go.kr/basis/situationView.do?ctrtAcctBookMngNo='+row['ctrtAcctBookMngNo']
        results.append(fetch(dict(id='evaluation-contract-detail',title='효과평가용역 계약 상세',url=url,format='html',reference='2026-09-16 열람')))
        detail_query={'ctrtAcctBookMngNo':row['ctrtAcctBookMngNo']}
        detail_path=OUT/'evaluation-detail-query.json';detail_path.write_text(json.dumps(detail_query),encoding='utf-8')
        detail_url='http://contract.bsnamgu.go.kr/basis/ajaxSituationData.do'
        raw_detail=subprocess.run(['curl.exe','--fail','--location','--max-time','30','--data-binary','@'+str(detail_path),detail_url],capture_output=True,check=True).stdout
        detail=json.loads(raw_detail);assert detail.get('cmiosRtnCode')=='SUCC'
        (OUT/'evaluation-detail.json').write_bytes(raw_detail)
        results.append(dict(id='evaluation-detail-api',title='효과평가용역 준공·대금 지급',url=detail_url,query=detail_query,reference='2026-09-16 열람',status='downloaded',localFile=str((OUT/'evaluation-detail.json').relative_to(ROOT)),sha256=hashlib.sha256(raw_detail).hexdigest(),bytes=len(raw_detail)))
except Exception as e: results.append(dict(id='namgu-evaluation-contract-2026',url=endpoint,status='unavailable',error=str(e)))
(OUT/'manifest.json').write_text(json.dumps({'retrievedAt':'2026-09-16','sources':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
