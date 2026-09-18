"""Correct authored interpretation of the public remarks column; preserve inputs."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'data/processed/최종논리검증-20260916/corrections';O.mkdir(parents=True,exist_ok=True)
targets=['scripts/build_followup_report_20260916.py','scripts/build_resolution_report_20260916.py','scripts/plot_followup_services_20260916.py','scripts/collect_followup_services_20260916.py','scripts/collect_resolution_evidence_20260916.py','docs/40-분석결과/부산-119-문제제기와보완논리-20260916.md','docs/40-분석결과/부산-119-보조자료선택판단-20260916.md']
changes=[]
for name in targets:
 p=R/name;before=p.read_bytes();s=before.decode('utf-8')
 for a,b in [
 ('나머지 13행은 조치 기재가 없으며 미조치 확정값이 아닙니다.','나머지 13행의 일반 비고란은 공란입니다. 이 표에는 조치완료 전용 열이 없어 공란을 후속조치 누락으로 판단할 수 없습니다.'),
 ('조치 기재가 없는 13행을 미조치 시설로 판정하지 않았습니다. 현지시정도 이후 효과 검증을 뜻하지 않습니다.','13행은 일반 비고란의 공란입니다. 조치완료 전용 열이 아니므로 관리공백이나 현재 미조치의 증거가 아닙니다.'),
 ('금정3·부산진10행은 후속조치가 공개표에 기재되지 않았다.','금정3·부산진10행은 일반 비고란이 공란이다. 조치완료 전용 항목이 없으므로 후속조치 누락으로 판단하지 않는다.'),
 ('조치 미기재','비고 공란'),('조치미기재','비고 공란'),('조치 기재 없음','비고 공란'),
 ('기재 공백 감소를 시설 안전개선 효과와 구분한다.','일반 비고란의 공란을 기록 누락률이나 관리공백 지표로 사용하지 않는다. 후속 이행은 별도 문서로 확인해야 한다.'),
 ('조치 기록 부재를 미조치 시설 수나 위험 순위로 계산하는 오류를 막았습니다.','일반 비고란을 조치완료 전용 항목처럼 읽던 표현을 수정했습니다. 공란을 미조치 수·기록 누락률·관리공백으로 계산하지 않습니다.'),
 ('현재 점검에서 확인한 불량과 조치 기록은 다릅니다','공개 조사표의 불량 판정과 비고를 구분했습니다')]:s=s.replace(a,b)
 if s.encode('utf-8')!=before:
  p.write_text(s,encoding='utf-8');changes.append({'path':name,'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':hashlib.sha256(p.read_bytes()).hexdigest()})
record=O/'copy-corrections.json'
if changes:record.write_text(json.dumps({'reason':'원문 열은 일반 비고이며 조치완료 전용 필드가 아님. 13행을 관리공백 근거로 사용하지 않음. 원본·기존 검증 집계 불변.','files':changes},ensure_ascii=False,indent=2),encoding='utf-8')
print('Corrected authored files:',len(changes))
