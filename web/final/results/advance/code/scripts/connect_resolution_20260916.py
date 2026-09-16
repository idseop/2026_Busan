"""Connect new findings without replacing prior aggregates or source registers."""
from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1];N=R/'output/부산119-쟁점해결-20260916';O=R/'output/부산119-전지역후속검증-20260916';W=R/'web/final'
for target in [O,W/'results/followup']:
 target.mkdir(parents=True,exist_ok=True)
 (target/'쟁점해결.html').write_text((N/'index.html').read_text(encoding='utf-8').replace('source-register.json','쟁점출처.json'),encoding='utf-8')
 shutil.copy2(N/'source-register.json',target/'쟁점출처.json')
 for p in N.iterdir():
  if p.suffix in ['.png','.svg','.csv']:shutil.copy2(p,target/p.name)
for name in ['explorer.html','explorer-data.js']:
 shutil.copy2(O/name,W/'results/followup'/name)
for target in [O/'index.html',W/'results/followup/index.html']:
 s=target.read_text(encoding='utf-8')
 if 'href="쟁점해결.html"' not in s:s=s.replace('</nav>','<a href="쟁점해결.html">최신 쟁점·보완 결과</a></nav>')
 target.write_text(s,encoding='utf-8')
p=W/'index.html';s=p.read_text(encoding='utf-8').replace('href="results/followup/index.html">후속검증 결과','href="results/advance/index.html">최신 분석 결과');p.write_text(s,encoding='utf-8')
print('Latest report and region explorer connected.')
