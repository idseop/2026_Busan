"""Write the current plan/verification and package public results after review."""
from pathlib import Path
import json,hashlib,shutil,zipfile
R=Path(__file__).resolve().parents[1];N=R/'data/processed/효과근거확장-20260916'
O=R/'output/부산119-효과근거확장-20260916';W=R/'web/final'
D=R/'output/부산119-고도화결과-20260916'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def document():
    ver='''# 효과 근거 확장: 검증 기록

## 기존 자료 재사용

신고 원본을 수정하지 않고 입력해시가 일치하는 17컬럼 전처리본을 읽었다. 기존 값은 전체704,689/정상처리579,412/정상처리·운영성제외574,662건이다. 인구·공간 후보·선택 영향은 이전 검증과 현재 입력 일치를 바탕으로 재사용했다.

## 새 분석의 독립 검증

- 시간 집계: 작성코드와 다른 csv/gzip 스트리밍·datetime 달력 계산·정확한 분수 비교로970조합×11기간10,670개 결과 재계산. 입력704,689/C574,662/5유형41,720 대조 통과. 연도·월기존집계일치. 작성과검증 별도.
- 선택 조건에 안정적인325조합: 기존 A/B/C목록에서 독립 재선정, 연도최소1/5/10/20건 층별 최고월·계절 유지 집계 일치.
- CPR: 공식원PDF75–76쪽 표42,6–8쪽 정의를 독립 추출·시각검토. 부산/전국5개년10행 원값·16.5%p차·분모null 일치.
- 교육 경험: 공식 XLSX의 ZIP/XML을 직접 읽어99개 행·1,089개 수치/표기 검사 통과. 3구 PDF의표·가중조율·분모·19세이상 정의 확인. RSE30%이상7행은 주의값으로 보존, 대표 연령그림6개는 모두30%미만.
- 도로: 원XLS103행과 HWP바이너리에서수량·공고를대조한243개검사통과. 제작/설치/기초중복합산없음. 원지도 거리합1102.5m와 실제조사표1034.4m차이68.1m직접확인. 표번호3-17오기→실제3-9로수정후재검증.

## 수정한 오류

그림 제작 중 원본 연령범주에 '세'가 없어 추출이 비는 문제를 발견해 6개정확범주로수정하고 assertion을추가했다. 교육그림의범례와제목겹침도실제PNG검토후수정했다. 최종표의 '시행인원'은 구조자수로읽힐수있어 'CPR을 받은 환자'로명확히했다. 기존 일반비고13공란을미조치13시설로해석하지않는교정도유지한다.

## 검증의 범위

검증은 출처·집계·웹동작과 결과전달의검사이며, 사용자 이해도개선·예약성공·실제술기·피해감소를측정한것은아니다. 공간미확정신고에정밀위치나가짜행정동배정을추가하지않았다.
'''
    for key,label in [('report-independent.json','최종 내용·그림 검토'),('report/browser-independent.json','독립 PC 브라우저 검사')]:
        p=N/'verification'/key
        if p.exists():
            x=read(p);ver+=f'\n## {label}\n\n세부 결과는 `verification/{key}`에 기록했다. 상태: {x.get("status","기록 확인")}.\n'
        else:ver+=f'\n## {label}\n\n검증 진행 중. 최종 배포 전에 별도 검증 결과를 반영한다.\n'
    for dest in [O,W/'results/effects']:
        dest.mkdir(parents=True,exist_ok=True);(dest/'검증기록.md').write_text(ver,encoding='utf-8')
        for p in (N/'verification').rglob('*'):
            if p.is_file() and p.suffix in ['.json','.md']:
                t=dest/'verification'/p.relative_to(N/'verification');t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
    plan=R/'docs/10-작업계획/부산 분석 작업 계획.md';s=plan.read_text(encoding='utf-8')
    marker='## 2026-09-16 효과 근거·계절·교육경험 확장'
    if marker in s:s=s.split(marker)[0].rstrip()
    s+='\n\n'+marker+'''

최신 단계는 과거 신고를 현재의 예방·지원 선택과 연결할 근거를 보강한다. 모든유형반복을 위험순위로바꾸거나 실제서비스공백·효과를 가정하지않는다.

1. 기존 신고선택집합704,689건과A/B/C기준을유지한다. 970지역×유형에서연도별월집계를추가하고11기간달력일수당최고시기를검증했다. 기존조건안정325개중계절유지121개이며, 특정계절집중안의제약으로반영한다. 사전명세와원전처리해시를보존한다.
2. 공식급성심장정지2024원통계집에서2020–2024부산·전국10행,2024CHS연제·부산진·수영공식XLSX/PDF에서99개교육·실습집계를확보했다. 환자·주민표본·신고·행정동후보인구를별개로제공한다. CHS조율/SE/RSE를보존하고환자연령·미충족수요·참여전환으로추정하지않는다.
3. 부전맞이길원설계와공고,광안조사선지도와실측표를비교했다. 설계수량을완료수량으로취급하지않고표번호오기를수정했다. 못골평가수행·거제위원회예산검토의확인범위를보존한다.
4. 심정지상세에구단위교육경험과부산환자통계를별도로연결했다. 모든유형에의료설명을복사하지않는다. 시간비교는C전용/고정5년임을해당위치에표시한다.
5. 기대효과는공식조건선택정확도·시간→실제참여/술기→현장/환자성과로나눈다. 효과율은미측정이며실험명세를별도작성했다. 기관원정보수정이나현장공사를본웹성과로표현하지않는다.

최신보고서: `../40-분석결과/부산-119-효과근거확장-20260916.md`.
최신웹: `web/final/results/effects/`,지역탐색: `web/final/results/followup/explorer.html`.
신규코드·입력·출처·검증: `data/processed/효과근거확장-20260916/`와각manifest.
미확보원자료는공식경로시도내역과함께남긴다. BDI개별구간/준공도면,평가최종수치,등록ID별실제접근·점검,비식별교육참여와술기자료가확보되면해당단계판정을갱신한다.
'''
    plan.write_text(s,encoding='utf-8')
    # Output explorer lives beside the standalone report; served explorer uses web hierarchy.
    p=R/'output/부산119-전지역후속검증-20260916/explorer.html'
    s=p.read_text(encoding='utf-8').replace('../effects/','../부산119-효과근거확장-20260916/')
    p.write_text(s,encoding='utf-8')

def package():
    for name in ['temporal-independent.json','content-independent.json','chs-independent.json','traffic-independent.json','report-independent.json','report/browser-independent.json']:
        x=read(N/'verification'/name);assert x['status'].lower()=='pass',(name,x.get('status'))
        if name in ['report-independent.json','report/browser-independent.json']:
            for rel,expected in x['hashes'].items():
                assert sha(R/rel)==expected,('changed after independent review',rel)
    document()
    D.mkdir(parents=True,exist_ok=True)
    shutil.copytree(W,D,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.zip'))
    (D/'결과보기.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=results/effects/index.html"><a href="results/effects/index.html">최신 분석 결과 열기</a>',encoding='utf-8')
    shutil.copy2(O/'보고서.md',D/'이번작업-보고서.md')
    shutil.copy2(R/'docs/10-작업계획/부산 분석 작업 계획.md',D/'분석계획.md')
    (D/'실행방법.txt').write_text('''압축을 푼 뒤 결과보기.html을 여세요. 최신 시각화·표·지역탐색은 파일 직접 실행됩니다.
지도 포함 전체 서비스: python serve.py --no-browser
웹: http://127.0.0.1:8765/ / 최신보고서: http://127.0.0.1:8765/results/effects/
기존 서버가 켜져 있으면 재실행하지 않고 위 주소를 여세요. 포트가 다른 프로그램에 사용 중이면 --port 8766 등으로 변경할 수 있습니다.
지도 외부 배경과 기관링크는 인터넷이 필요합니다. 실시간 신고조회는 아닙니다.
원 신고·시설 원명부·대용량 CHS PDF/ZIP는 포함하지 않았습니다. 재현코드는 원 프로젝트 입력과 Python 환경이 있어야 합니다. 이번작업-보고서.md의 순서와 각스크립트 사용법을 참조하세요.
''',encoding='utf-8')
    codepaths=['analysis/00_공통/analyze_temporal_transfer_20260916.py','scripts/verify_temporal_transfer_20260916.py','scripts/collect_prevention_effects_20260916.py','scripts/probe_chs_public_20260916.py','scripts/extract_chs_education_20260916.py','scripts/summarize_chs_education_20260916.py','scripts/collect_traffic_effects_20260916.py','scripts/build_followup_explorer_20260916.py','scripts/connect_temporal_results_20260916.py','scripts/build_effect_evidence_20260916.py','scripts/finalize_effect_evidence_20260916.py']
    for rel in codepaths:
        target=D/'재현코드'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/rel,target)
    selected={
        'temporal':['specification.json','manifest.json','stability_profiles.csv','selection_stable_temporal.json','all_region_month_windows.csv','분석결과.md'],
        'services':['cpr-trend.json','cpr-trend.csv','prevention-effects.json','search-audit.json','source-manifest.json','summary.md'],
        'context':['chs-education-summary.json','chs2024-cpr-education.csv','chs-browser-attempts.json','chs-extraction-manifest.json','교육경험-확보결과.md','chs-연제구-sampling-definition.json','chs-부산진구-sampling-definition.json','chs-수영구-sampling-definition.json'],
        'traffic':['traffic-effects-extension.json','case-evidence-status.csv','bujeon-designed-quantities.csv','reused-inputs.json','search-attempts.json','download-manifest.jsonl','도로보행-후속확장.md']}
    for folder,names in selected.items():
        for name in names:
            source=N/folder/name
            if not source.exists():raise FileNotFoundError(source)
            target=D/'추가집계와출처'/folder/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    for p in (N/'verification').rglob('*'):
        if p.is_file() and p.suffix in ['.json','.md','.py','.png']:
            target=D/'검증'/p.relative_to(N/'verification');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    manifest=[{'path':p.relative_to(D).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='배포명세.json']
    (D/'배포명세.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    zpath=D.with_suffix('.zip')
    with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED) as z:
        for p in D.rglob('*'):
            if p.is_file():z.write(p,p.relative_to(D))
    with zipfile.ZipFile(zpath) as z:assert z.testzip() is None;entry_count=len(z.namelist())
    record={'path':str(zpath.relative_to(R)),'bytes':zpath.stat().st_size,'sha256':sha(zpath),'entries':entry_count,'crcPassed':True,'rawIncidentExport':False,'originalChsPdfZipExport':False}
    (R/'output/부산119-고도화결과-배포기록.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False))

if __name__=='__main__':
    import sys
    if '--package' in sys.argv:package()
    else:document();print('Plan and verification records updated; package gated on independent passes.')
