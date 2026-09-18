"""Independent check of the two final explanatory plots against existing inputs."""
from pathlib import Path
import hashlib,json,zipfile
R=Path(__file__).resolve().parents[1];N=R/'data/processed/최종마감-20260916'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=read(R/'data/processed/최종논리검증-20260916/population/prevention-population.json')
data=read(N/'derivedplotdata.json');checks=[]
def check(name,result):
    checks.append({'name':name,'pass':bool(result)})
    assert result,name
check('10 distinct candidate/year records',len(data['populationAnnual'])==10 and len({(r['candidateCode'],r['year']) for r in data['populationAnnual']})==10)
for row in data['populationAnnual']:
    original=next(r for r in source['annual'] if r['candidateCode']==row['candidateCode'] and r['year']==row['year'])
    for k,v in row.items():
        if k in original:check(f"{row['candidateCode']}/{row['year']}/{k}",v==original[k])
    check(f"yearend {row['candidateCode']}/{row['year']}",original['referenceDate']==f"{row['year']}-12-31")
    check(f"share {row['candidateCode']}/{row['year']}",abs(original['age65Plus']/original['total']-original['age65PlusShare'])<1e-12)
stable=read(R/'data/processed/효과근거확장-20260916/temporal/selection_stable_temporal.json')['strata'][0]
check('selection stable input equality',data['selection']['stable']==stable)
check('194 x 5 = 970',data['selection']['rawNames']==194 and data['selection']['types']==5 and data['selection']['universe']==970)
check('Gwangan separate comparison',data['selection']['parallelComparison']=='광안동 교통사고')
for item in read(N/'additional-visuals.json'):
    for fmt in ['png','svg']:check(item['id']+'/'+fmt+' hash',sha(N/item[fmt])==item['sha256'][fmt])
catalog=read(R/'web/final/results/final/visual-catalogue.json')
check('13 curated visuals',len(catalog)==13)
for row in catalog:
    check(row['publicPath']+' byte-exact',sha(R/row['path'])==sha(R/'web/final/results/final'/row['publicPath']))
with zipfile.ZipFile(R/'output/부산119-고도화결과-20260916.zip') as z:
    for name in ['data/dashboard-data.js','data/deep-data.js','data/map-data.js','data/case-services.js','results/followup/explorer-data.js']:
        check(name+' aggregate unchanged from verified previous release',hashlib.sha256(z.read(name)).hexdigest()==sha(R/'web/final'/name))
out={'status':'pass','checks':checks,'total':len(checks),'method':'Existing candidate/year source records and exact fractions; current public aggregates byte-compared with independently verified preceding ZIP','visualReview':'Parent opened both new PNG files and reviewed labels, axes, branches, cautions, empty states. No clipped values or overlaps observed.','hashes':{str(p.relative_to(R)):sha(p) for p in [N/'derivedplotdata.json',N/'additional-visuals.json',R/'web/final/results/final/visual-catalogue.json']}}
(N/'verification').mkdir(exist_ok=True);(N/'verification/visual-final.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS',len(checks))
