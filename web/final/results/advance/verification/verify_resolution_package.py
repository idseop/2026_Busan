"""Read-only review of delivery instructions and existing ZIP artifacts."""
from pathlib import Path
import json,hashlib,zipfile,ast
O=Path(__file__).resolve().parent;R=O.parents[3];p=R/'scripts/package_resolution_20260916.py';s=p.read_text(encoding='utf-8');ast.parse(s)
ck={'syntax':True,'explicitTrackCommand':'collect_resolution_evidence_20260916.py track' in s,'explicitAnalyzeCommand':'collect_resolution_evidence_20260916.py analyze' in s,'baseCollectorAcknowledged':'collect_dong_services_20260916.py' in s,'savedHwpxPrerequisite':'aed-guideline-v8.hwpx' in s,'savedEducationPrerequisite':'web-extraction' in s,'standaloneRawReproductionNotClaimed':'이 ZIP만으로 원자료 전체 분석을 재생성할 수 있는 것은 아닙니다' in s,'zipCrcCheck':'z.testzip() is None' in s,'noRemovalCalls':not any(x in s for x in ['rmtree','unlink(','remove('])}
records=[]
for n in ['부산119-쟁점해결-20260916.zip','부산119-지도와쟁점분석-20260916.zip']:
 zpath=R/'output'/n
 if not zpath.exists():continue
 with zipfile.ZipFile(zpath) as z:
  names=z.namelist();ok=z.testzip() is None;forbidden=[a for a in names if Path(a).suffix.lower() in ['.gz','.xlsx','.hwpx','.env'] or a.startswith('data/raw/')]
  ck[n+'Crc']=ok;ck[n+'NoRawSensitiveFormats']=not forbidden;records.append({'name':n,'entries':len(names),'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest()})
result={'pass':all(ck.values()),'checks':ck,'scriptSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'packages':records,'scope':'Code, actual CLI dispatch, input preservation and archive boundary. ZIP checks only apply to archives listed above. Full raw analysis requires retained project inputs.'}
(O/'resolution-package-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert result['pass']
