"""Independent final package and documented verification-chain check."""
from pathlib import Path
import json,hashlib,zipfile,re
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[2];O=R/'data/processed/심층분석-20260915';B=O/'browser_verification';W=R/'web/final'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
def check(n,c):checks.append({'name':n,'passed':bool(c)});assert c,n
d=read(B/'delivery.json');a=read(B/'result.json');b=read(B/'details_result.json')
check('all_browser_delivery_statuses',all(x['status']=='passed' for x in [d,a,b]))
check('browser_evidence_hash_chain',sha(B/'result.json')==d['base_browser_result_sha256'] and sha(B/'details_result.json')==d['detail_browser_result_sha256'])
check('current_site_matches_delivery',all(sha(R/p)==h for p,h in d['site_sha256'].items()))
check('current_site_matches_detail_evidence',all(sha(R/p)==h for p,h in b['site_sha256'].items()))
zpath=R/d['archive'];check('archive_hash',sha(zpath)==d['archive_sha256'])
with zipfile.ZipFile(zpath) as z:
 check('archive_crc',z.testzip() is None)
 check('all_11_site_members',set(z.namelist())==set(d['archive_members'])=={p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file()} and len(z.namelist())==11)
 check('each_archive_member_content_hash',all(hashlib.sha256(z.read(p)).hexdigest()==sha(W/p) for p in z.namelist()))
check('browser_count_claims',len(a['map_filter_combinations'])==90 and len(a['local_heatmap_checks'])==111 and len(b['monthly_filter_checks'])==90 and len(b['case_subtype_hour_checks'])==12)
for n,k in [('independent_deep_verification.json',126),('independent_deep_ui_report_review.json',183),('independent_deep_ui_delta_review.json',148)]:
 r=read(O/n);check('review_count_'+n,(r.get('status')=='passed' or r.get('passed') is True) and len(r['checks'])==k and all(x['passed'] for x in r['checks']))
report=R/'docs/40-분석결과/부산-119-지도와-심층사례-20260915.md';text=report.read_text(encoding='utf-8')
check('report_validation_claims',all(s in text for s in ['126개','183개','148개','1,440개','111개','90개 조건','12개 사례']))
links=re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text)
local=[x.split('#')[0] for x in links if not x.startswith(('https:','http:'))]
check('report_markdown_link_targets_exist',all((report.parent/x).exists() for x in local))
check('report_detail_result_relative_path_correct','`browser_verification/details_result.json`' in text)
check('all_screenshots_current',all(sha(B/p)==h for p,h in d['screenshots'].items()))
result={'status':'passed','reviewed_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'scope':'Read-only independent ZIP CRC/member hash and final browser evidence chain, documented counts and report links. No raw receipt reprocessing or full browser rerun.','report_sha256':sha(report),'delivery_sha256':sha(B/'delivery.json'),'archive_sha256':sha(zpath),'script_sha256':sha(Path(__file__)),'source_site_hashes':d['site_sha256'],'resolved_comment':'Relative details_result.json reference explicitly points to browser_verification/details_result.json.'}
(O/'independent_deep_delivery_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('passed',len(checks))
