"""Package reviewed analysis and web separately, preserving the former releases."""
from pathlib import Path
import hashlib, json, re, zipfile, shutil

R=Path(__file__).resolve().parents[1]
N=R/'data/processed/통합완성-20260916'
W=R/'web/final'
P=W/'results/complete'
O=R/'output'
REPORT=R/'docs/40-분석결과/부산-119-전체결과-단일보고서-20260916.md'
PLAN=R/'docs/10-작업계획/부산 분석 작업 계획.md'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def verify_inputs():
    checks=[]
    for name in ['context-independent','evidence-independent','report-independent','browser-independent']:
        p=N/'verification'/f'{name}.json'
        obj=read(p)
        assert obj['status'].lower() in {'pass','pass_after_correction'},(name,obj['status'])
        for rel,digest in obj.get('hashes',obj.get('reviewedHashes',{})).items():
            f=R/rel
            assert f.is_file() and sha(f.read_bytes())==digest,('reviewed file changed',name,rel)
        for rel,digest in obj.get('outputHashes',{}).items():
            found=list((N/'context').rglob(rel))
            assert len(found)==1 and sha(found[0].read_bytes())==digest,('reviewed context changed',rel)
        checks.append({'file':p.relative_to(R).as_posix(),'sha256':sha(p.read_bytes())})
    assert len(read(P/'figure-catalogue.json'))==45
    assert len(read(P/'table-catalogue.json'))==68
    return checks

def common():
    files={'전체결과보고서.md':REPORT.read_bytes(),'상세작업계획.md':PLAN.read_bytes(),
           'requirements-final-delivery.txt':(R/'requirements-final-delivery.txt').read_bytes()}
    for folder in [R/'analysis/00_공통',R/'scripts']:
        for p in folder.iterdir():
            if p.is_file() and p.suffix in {'.py','.js','.cjs','.ps1','.txt'}:
                files['재현코드/'+p.relative_to(R).as_posix()]=p.read_bytes()
    # Exact current evidence manifests and reviewer records. Raw personal records stay local.
    for p in N.rglob('*'):
        if p.is_file() and p.suffix in {'.json','.md','.py'} and not any(x in p.parts for x in ['previous-final-pages','package-check']):
            files['근거검증/'+p.relative_to(N).as_posix()]=p.read_bytes()
    for name in ['complete-index-1600.png','complete-map-selected-1366.png','complete-explorer-living-1600.png','complete-explorer-commerce-1600.png','complete-explorer-기장읍-1600.png']:
        p=N/'verification'/name
        files['대표화면/'+name]=p.read_bytes()
    return files

def standalone_html(raw):
    text=raw.decode('utf-8')
    # The analysis ZIP is independent of the separately delivered map ZIP.
    text=re.sub(r'href="(?:\.\./)+index\.html"', 'href="report.html#part-12"',text)
    text=re.sub(r'href="\.\./followup/explorer\.html[^\"]*"','href="report.html#part-9"',text)
    text=text.replace('>부산 지도<','>웹 이용 안내<').replace('>지역별 상세<','>지역별 결과<')
    return text.encode('utf-8')

def make_zip(name,files):
    manifest=[{'path':k,'bytes':len(v),'sha256':sha(v)} for k,v in sorted(files.items())]
    files['배포명세.json']=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8')
    path=O/name
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for rel,blob in sorted(files.items()):z.writestr(rel,blob)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(set(z.namelist()))==len(files)
    return {'path':path.relative_to(R).as_posix(),'bytes':path.stat().st_size,'entries':len(files),'sha256':sha(path.read_bytes()),'crcPassed':True}

def main():
    checks=verify_inputs();O.mkdir(exist_ok=True)
    base=common()
    analysis=dict(base)
    for p in P.rglob('*'):
        if p.is_file():
            rel=p.relative_to(P).as_posix()
            analysis[rel]=standalone_html(p.read_bytes()) if p.suffix=='.html' and '/' not in rel else p.read_bytes()
    analysis['읽는방법.txt']='''부산 119 전체 분석·시각화 (2026-09-16)

압축을 완전히 푼 뒤 index.html을 여세요. Python이나 인터넷 없이 분석 결과를 읽을 수 있습니다.
gallery.html: 45종 PNG/SVG, 확대·분류·저장
data.html: 68개 집계표 미리보기와 전체 CSV
report.html / 전체결과보고서.md: 목적·배경·자료·지역별 결과·보완 내용·효과 측정·한계
상세작업계획.md: 현재 상세 계획
재현코드/: 분석과 구현 코드. 전체 재분석에는 원 프로젝트 입력·디렉터리 구조가 필요합니다.
근거검증/: 입력·출처·해시·독립 검증 기록

이 ZIP은 분석 결과용입니다. 조작 가능한 부산 지도와 지역 필터는 별도 통합지도웹 ZIP을 이용하세요.
신고 분석 기간은 2020~2024년. 생활·상권·현장·운영 자료는 각 결과 옆 기준일을 따릅니다.
개별 신고 접수번호·정밀 신고 위치·원 신고자료는 배포하지 않습니다.
서비스 증설의 효과나 현재 현장별 위험을 입증했다고 표현하지 않습니다.
'''.encode('utf-8')
    web=dict(base)
    for p in W.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.zip','.pyc'}:
            web[p.relative_to(W).as_posix()]=p.read_bytes()
    web['결과보기.html']=b'<!doctype html><html lang="ko"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=results/complete/index.html"><a href="results/complete/index.html">Open results</a></html>'
    web['실행방법.txt']='''부산 119 통합 지도 웹 (2026-09-16)

1. ZIP 압축을 완전히 풉니다.
2. Python 3이 있는 PC에서 실행.cmd를 실행합니다. 또는 해당 폴더에서 python serve.py
3. 지도: http://127.0.0.1:8765/
   전체 결과: http://127.0.0.1:8765/results/complete/
   지역별 상세: http://127.0.0.1:8765/results/followup/explorer.html
4. 다른 서버가 포트를 사용하면 python serve.py --port 8766

지도 외 통합 결과·그림·표·지역 상세는 결과보기.html에서 파일 직접 실행도 가능합니다.
상세 지형 배경과 외부 공식 링크는 인터넷이 필요합니다. 로딩 실패 시 경계·분석 결과를 유지합니다.
API 키는 필요하지 않습니다. 지도 이용 조건·출처는 README.md와 assets/vendor 라이선스에 보존합니다.
지도와 인구가 실시간 신고나 개인 이동을 표시하는 것은 아닙니다. 3D 기능은 이번 배포에 없습니다.

통합 결과 45그림·68집계표·194신고지역명 탐색·187직접 대응 상권·생활/주택/AED·9심층사례를 포함합니다.
원 신고·시설 원명부·대용량 원본은 포함하지 않습니다. 전체 재분석은 원 프로젝트 입력이 필요합니다.
재현코드/ 및 전체결과보고서.md의 실행 순서를 따르세요.
'''.encode('utf-8')
    records=[make_zip('부산119-전체분석-시각화-20260916.zip',analysis),make_zip('부산119-통합지도웹-20260916.zip',web)]
    delivered_report=O/'부산119-전체결과보고서-20260916.md';shutil.copy2(REPORT,delivered_report)
    result={'packages':records,'report':{'path':delivered_report.relative_to(R).as_posix(),'sha256':sha(delivered_report.read_bytes())},'reviewInputs':checks,'figures':45,'tables':68,'privateIncidentDataIncluded':False,'implemented3D':False}
    (O/'부산119-통합완성-배포기록.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
