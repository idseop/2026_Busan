"""Publish existing verified aggregates; do not reprocess incident records."""
from pathlib import Path
import csv, json, hashlib, shutil, subprocess
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web/submission'
AUDIT = ROOT / 'data/processed/최신웹연결-20260918'
REMOTE = ROOT / 'data/interim/원격최신-웹갱신-20260918/snapshot'
BASE = ROOT / 'data/processed/5개년통합-지역유형-제안연결-20260917'
inputs = {}

def track(p):
    p = Path(p)
    inputs[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p

def rows(p):
    return list(csv.DictReader(track(p).open(encoding='utf-8-sig', newline='')))

def jsdata(p):
    s = track(p).read_text(encoding='utf-8-sig')
    return json.loads(s[s.index('=') + 1:].strip().rstrip(';'))

def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8', newline='\n')

def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(track(WEB/'assets/current-shell.html'), WEB/'index.html')
    d = jsdata(WEB / 'data/dashboard-data.js')
    district = rows(BASE / '01-16구군-5년합계와-한해제외순위.csv')
    subtypes = rows(BASE / '02-전체70유형-5년합계와-한해제외순위.csv')
    focus = rows(BASE / '07-상위5구군-유형별동비교.csv')
    gu_types = rows(BASE / '04-구군별-주요3유형.csv')
    children = rows(BASE / '06-구군주요유형에서-동별상위3-연결.csv')
    proposals = rows(BASE / '09-5년신고에서-기존대응-보완평가로.csv')
    time = [r for r in rows(BASE / '11-상위5구군45조합-5년시간교차집계.csv') if r['scope'] == 'P']
    time_summary = [r for r in rows(BASE / '10-상위5구군45조합-시간요약.csv') if r['scope'] == 'P']
    annual = rows(ROOT / 'data/processed/신고인구특성재정립-20260917/calls/region-all-subtypes-by-year.csv')
    counts = [[r['CLMTY_SGG_NM'], r['CLMTY_EMD_NM'], int(r['year']), r['EMRG_RSCU_ASSRT_NM'], r['EMRG_RSCU_CLSF_NM'], int(r['count'])] for r in annual]
    assert sum(r[5] for r in counts) == 555786
    compare = rows(REMOTE / 'output/부산진구-중구-1차분석/01_부산전체_구군비교.csv')
    c_totals = {r['구군']: int(r['C신고건수']) for r in compare}
    for gu, n in c_totals.items():
        assert n == sum(r['total'] for r in d['rawRegions'] if r['scope'] == 'C' and r['district'] == gu)
    # Same 5-year source and scope; the only C/P subtraction is beehive removal.
    crosswalk = [dict(district=r['district'], C=c_totals[r['district']], P=int(r['countP']), excludedBee=c_totals[r['district']]-int(r['countP'])) for r in district]
    assert sum(r['excludedBee'] for r in crosswalk) == 18876
    remote_sub = rows(REMOTE / 'output/부산진구-중구-1차분석/01_세부유형_연도.csv')
    for gu in ['부산진구', '중구']:
        assert sum(int(r['신고건수']) for r in remote_sub if r['CLMTY_SGG_NM'] == gu and r['EMRG_RSCU_CLSF_NM'] == '벌집제거') == next(r['excludedBee'] for r in crosswalk if r['district'] == gu)
    candidates = rows(ROOT / 'data/processed/신고주민연결심화-20260917/direction-reassessment/all-name-population-candidates.csv')
    links = defaultdict(list)
    for r in candidates:
        if r['populationAvailable'] == 'True':
            links[f"{r['district']}|{r['rawDong']}|{r['year']}"].append(r['candidateCode'])
    # Public aggregates only. No call IDs or incident coordinates.
    data = dict(meta=dict(updated='2026-09-18', years=list(range(2020,2025)), primaryScope='P', primaryCount=555786,
        remoteCommit='222159a133e72f1c8ba97b21835eab690a7d5904', developCommit='222159a', comparisonSnapshot='cfbdbe749083c4900ba533ba8af648dc4ef48395',
        scopeLabels={'P':'주 분석 · 업무성·벌집제거 제외','C':'비교 · 업무성 기록 제외','B':'비교 · 정상 처리 전체','A':'비교 · 모든 처리결과'}),
        counts=counts, existing=d['rawRegions'], population=d['population'], links=dict(links), districts=district,
        subtypes=subtypes, guTypes=gu_types, children=children, focus=focus, proposals=proposals, time=time,
        timeSummary=time_summary, crosswalk=crosswalk)
    write(WEB/'data/current-data.js', 'window.BUSAN_CURRENT='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
    for relative in ['assets/fire-stations.js','assets/fire-stations.css','data/fire-stations.json']:
        src = track(REMOTE/'web/final'/relative)
        shutil.copy2(src, WEB/relative)
    p = WEB/'assets/fire-stations.js'
    s=p.read_text(encoding='utf-8')
    s=s.replace("add('출동가능 인원'", "add('자료상 인원'").replace("add('출동가능 차량'", "add('자료상 차량'")
    s=s.replace("const note=document.createElement('small');note.textContent='출동가능 인원·차량은 제공 CSV를 관서명·주소로 연결한 값입니다. 기준일 미기재. 신고 발생 위치가 아닙니다.';div.append(note);return div;", 'return div;')
    s=s.replace('      toggle.disabled=false;', '''      if(view.map.getZoom){
        const size=()=>document.querySelectorAll('.fire-station-marker').forEach(el=>el.classList.toggle('compact',view.map.getZoom()<11.5));
        view.map.on('zoom',size);size();
      }
      toggle.disabled=false;''')
    write(p,s)
    figs=[]
    for folder in ['5개년통합-지역유형-제안연결-20260917','신고보건심화-20260917','신고주민연결심화-20260917']:
        for p in sorted((ROOT/'figures'/folder).rglob('*.png')):
            track(p); name=f'figure-{len(figs)+1:02}.png'
            (WEB/'analysis/figures').mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,WEB/'analysis/figures'/name)
            figs.append(dict(file='figures/'+name,title=p.stem,source=p.relative_to(ROOT).as_posix()))
    remote_figs=[]
    for p in sorted((REMOTE/'figures/부산진구-중구-1차분석').glob('*.png')):
        track(p);name=f'remote-{len(remote_figs)+1:02}.png';shutil.copy2(p,WEB/'analysis/figures'/name)
        remote_figs.append(dict(file='figures/'+name,title=p.stem,source=p.relative_to(ROOT).as_posix()))
    data_assets=dict(figures=figs,remoteFigures=remote_figs,crosswalk=crosswalk)
    write(WEB/'analysis/figures.js','window.BUSAN_FIGURES='+json.dumps(data_assets,ensure_ascii=False)+';\n')
    for name in ['01-16구군-5년합계와-한해제외순위.csv','02-전체70유형-5년합계와-한해제외순위.csv','07-상위5구군-유형별동비교.csv','09-5년신고에서-기존대응-보완평가로.csv']:
        target=WEB/'analysis/downloads'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(track(BASE/name),target)
    report=ROOT/'docs/40-분석결과/부산-119-최신작업-통합정리-20260918.md'
    shutil.copy2(track(report),WEB/'analysis/downloads/전체결과보고서.md')
    latest=ROOT/'data/interim/원격최신-웹갱신-20260918/develop-snapshot'
    for p in (latest/'output/pdf').glob('*.pdf'):
        assert p.read_bytes().startswith(b'%PDF-')
        shutil.copy2(track(p),WEB/'analysis/downloads'/p.name)
    for rel in ['assets/map-engine-3d.js','assets/ui-cleanup.js','index.html','serve.py']:
        track(latest/'web/final'/rel)
    write(AUDIT/'remote-local-crosswalk.json',json.dumps(crosswalk,ensure_ascii=False,indent=2))
    write(AUDIT/'build-manifest.json',json.dumps(dict(inputs=inputs,primaryCount=555786,comparisonCount=sum(c_totals.values()),figures=figs,remoteFigures=remote_figs,
        copiedRemoteComponents=['fire-stations.js','fire-stations.css','fire-stations.json'],
        developChangesIntegrated=['station layer','detail back navigation','consistent subtype summary','two-district figures and source PDFs','left year controls and compact map/header','no-store local server'],
        remoteBranch='develop', remoteCommit=data['meta']['remoteCommit'],comparisonSnapshot=data['meta']['comparisonSnapshot'],
        preservedLocalBranch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()),ensure_ascii=False,indent=2))
    print(json.dumps({'P':555786,'C':sum(c_totals.values()),'regions':len(set((r[0],r[1]) for r in counts)),'figures':len(figs),'remoteDistrictChecks':16},ensure_ascii=False))

if __name__=='__main__': main()
