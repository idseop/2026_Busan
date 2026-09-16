"""Expose verified region profiles inside the map without allocating incidents to buildings."""
from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parents[1];N=R/'data/processed/지도입증확장-20260916';W=R/'web/final'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    p=N/'profiles/regional-profiles.json';profiles=read(p)
    s=(W/'results/followup/explorer-data.js').read_text(encoding='utf8');d=json.loads(s[s.index('=')+1:].strip().rstrip(';'))
    cases=read(R/'data/processed/통합완성-20260916/evidence/case-assessments.json')['cases']
    sources={}
    for c in cases:
        links=[]
        for x in d['currentCaseSources']:
            if x['id'] in c['sourceRefs']:links.append({'url':x['url'],'title':'공식 후속 안내'})
        if c['subtype']=='심정지':
            links.extend({'url':x['url'],'title':x['name']} for x in d['serviceConditions'])
        if c['subtype']=='교통사고':
            ids=[i for a in d['updatedTraffic'] if a['district']==c['district'] and a['rawDongBackground']==c['rawDong'] for i in a['sourceIds']]
            links.extend({'url':x['url'],'title':x.get('sourceClass','공식 사업 기록')} for x in d['updatedTrafficSources'] if x['id'] in ids and x['status']=='saved')
            links.append({'title':'부산연구원 보행환경 조사','url':'https://data.bdi.re.kr/PDF/View.do?dir=report&path=RPT_00000000001&savename=20250715172207_54971'})
        if c['subtype'] in ['산악사고','수난사고']:
            links.extend({'url':x['sourceUrl'],'title':x['place']} for x in d['outdoor'] if c['rawDong'] in x['case'])
        if c['subtype']=='일반화재(주택)':
            links.extend([{'title':'부산 아파트 화재안전','url':'https://119.busan.go.kr/safeapt/index'},{'title':'화재안전취약자 지원','url':'https://119.busan.go.kr/supportcenter01'}])
            links.extend({'title':'기존 지역 협력·지원 기록','url':x['url']} for x in d['services'] if c['rawDong'] in x.get('region','') and x.get('url'))
            if c['rawDong']=='온천동':
                links.extend({'title':'동래 소방·복지 방문 안전 협력','url':x['url']} for x in d['services'] if 'silla.ac.kr/' in x.get('url',''))
        seen=set();sources[c['district']+'|'+c['rawDong']+'|'+c['subtype']]=[x for x in links if not (x['url'] in seen or seen.add(x['url']))]
    # Repeated strings and unused model diagnostics stay in downloadable audit JSON.
    for r in profiles['profiles']:
        for pop in r['populationCandidates']:pop.pop('shares',None)
        for t in r['typeProfiles']:
            h=t.get('holdout',{});t['holdout']={k:h[k] for k in ['status','comparisonEligible','trainCounts','testCount','predictedShare','actualShare','trainPeakSeasons','testPeakSeasons','peakOverlap','localTVD','uniformTVD','restBusanTVD'] if k in h}
    result={'profiles':profiles['profiles'],'meta':profiles['meta'],'cases':cases,'sources':sources,'housingRows':d['housingRows'],'serviceConditions':d['serviceConditions'],'aed':d['aedPublicHours'],'asOf':'2026-09-16'}
    target=W/'data/regional-evidence.js';target.write_text('window.BUSAN_REGIONAL_EVIDENCE='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';',encoding='utf8')
    (N/'ui').mkdir(exist_ok=True)
    (N/'ui/data-manifest.json').write_text(json.dumps({'input':str(p.relative_to(R)),'inputSha256':hashlib.sha256(p.read_bytes()).hexdigest(),'output':str(target.relative_to(R)),'outputSha256':hashlib.sha256(target.read_bytes()).hexdigest(),'regions':len(result['profiles']),'cases':len(cases),'bytes':target.stat().st_size},ensure_ascii=False,indent=2),encoding='utf8')
    print('Regional evidence:',len(result['profiles']),target.stat().st_size)
if __name__=='__main__':main()
