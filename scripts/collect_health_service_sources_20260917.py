"""Preserve only question-relevant, public source pages; no login or submission."""
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, json, hashlib
from lxml import html

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/processed/신고보건심화-20260917/sources'
SOURCES=[
 ('saha-chronic-service','https://www.saha.go.kr/health/contents.do?mId=0404040000','사하구의 기존 질환관리 교육 대상·주기·연계 경로'),
 ('saha-village-centres','https://www.saha.go.kr/health/contents.do?mId=0404050000','마을건강센터 목록에서 다대가 안 보이는 것이 실제 서비스 부재인지 확인'),
 ('saha-living-centres','https://www.saha.go.kr/health/contents.do?mId=0404060000','다대 건강생활지원센터 존재·내용·시간 확인'),
 ('buk-health-centres','https://www.bsbukgu.go.kr/health/index.bsbukgu?menuCd=DOM_000000503001006000','금곡 마을건강센터의 주민 자격·내용·시간 확인'),
 ('buk-chronic-service','https://www.bsbukgu.go.kr/health/index.bsbukgu?menuCd=DOM_000000503001004000','기존 교육·등록관리·문자안내와 보완 제안의 중복 방지'),
 ('busan-hypertension-study','https://rcphn.org/journal/view.php?number=1437&viewtype=pubreader','부산 관리교육 경험에 관한 직접 연구; 효과 수치 전용 금지'),
 ('119-goods390','https://www.bigdata-119.kr/goods/goodsInfo?goods_mng_sn=390','질병 증상·환자 특성·신고와 출동 연결을 검증할 원자료 접근 확인'),
 ('119-goods393','https://www.bigdata-119.kr/goods/goodsInfo?goods_mng_sn=393','질병 출동의 실제 정의·임상 특성 자료 후보'),
 ('119-goods396','https://www.bigdata-119.kr/goods/goodsInfo?goods_mng_sn=396','부전 부상의 기전·발생장소를 확인할 원자료 후보'),
]
records=[]
for name,url,question in SOURCES:
    path=OUT/f'{name}.html'
    rec=dict(id=name,url=url,question=question,reviewed_at=datetime.now(timezone.utc).isoformat())
    try:
        if not path.exists():
            path.write_bytes(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35).read())
        raw=path.read_bytes();text=raw.decode('utf-8');tree=html.fromstring(text)
        for node in tree.xpath('//script|//style'):node.drop_tree()
        (OUT/f'{name}.txt').write_text('\n'.join(x.strip() for x in tree.text_content().splitlines() if x.strip()),encoding='utf-8')
        rec.update(file=str(path.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),status='public_page_saved')
        if name.startswith('119'):
            rec.update(dataDownloaded=False,access='구매 기능 로그인 필요; 공개 샘플 링크의 file_id 공란',
                loginGuardPresent='로그인이 필요한 기능' in text,
                sampleLinks=[a.get('onclick') for a in tree.xpath('//a[@onclick]') if 'sampleDown' in a.get('onclick','')],
                interpretation='공개 컬럼명은 후보 명세만 확인. AI 컬럼 설명 및 빈 한글 정의로 의미 확정하지 않음')
    except Exception as exc:rec.update(status='failed',error=str(exc))
    records.append(rec)
(OUT/'service-source-manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('source pages',len(records),'saved',sum(r['status']=='public_page_saved' for r in records))
