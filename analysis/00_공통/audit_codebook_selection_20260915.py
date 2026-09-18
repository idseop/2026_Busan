"""Link all 38 actual workbook definitions to the approved 17-field selection."""
from pathlib import Path
import csv, hashlib, json
import openpyxl
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/동대응-전체결측제외-20260915/completeness'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    workbook=ROOT/'data/부산소방재난본부_119신고접수_현황_컬럼_정보_데이터.xlsx'
    input_path=ROOT/'data/interim/분석입력-2020-2024/manifest.json'
    inputs=json.loads(input_path.read_text(encoding='utf-8-sig'))
    policy=json.loads((OUT/'comparison_policy.json').read_text(encoding='utf-8'))
    selected=set(policy['current_selected_fields']); assert len(selected)==17
    prior_dir=ROOT/'data/processed/컬럼선별-결측제외-20260915'
    prior_manifest=json.loads((prior_dir/'manifest.json').read_text(encoding='utf-8'))
    prior_decisions=prior_dir/'column_decisions.csv'
    expected=next(x['sha256'] for x in prior_manifest['outputs'] if x['file']==prior_decisions.name)
    assert sha(prior_decisions)==expected
    prior_reasons=pd.read_csv(prior_decisions,keep_default_na=False).set_index('column').reason.to_dict()
    time_columns={'DCLR_YMD','DCLR_TM','DCLR_YR','DCLR_MM','DCLR_DAY','DCLR_HR','DCLR_MN','DCLR_DOW','SEASN_NM','QTR_NO'}
    flags={'OTR_CTPV_DCLR_YN','OTR_CTPV_DSPT_YN','CLLBC_YN','JNT_CRSP_YN','CENTR_RSUN_DSPT_DMND_YN','CHEM_ACDNT_YN'}
    uses={
        'RCPT_PATH_NM':'접수경로별 분포를 실제 집계하여 완전행 선택이 이동전화에 편중되는지 확인.',
        'ACDNT_OCRN_LOT':'사고발생 경도의 숫자 파싱·0·경도 가정 범위와 손상지역 좌표쌍의 수치상 일치 점검에 실제 사용.',
        'ACDNT_OCRN_LAT':'사고발생 위도의 숫자 파싱·0·위도 가정 범위와 두 좌표쌍의 수치상 동시 일치 점검에 실제 사용.',
        'DAMG_RGN_LOT':'손상지역 경도의 숫자 파싱·0·범위 및 사고발생 좌표와 비교에 실제 사용. 좌표계·정확위치 검증을 의미하지 않음.',
        'DAMG_RGN_LAT':'손상지역 위도의 숫자 파싱·0·범위 및 사고발생 좌표와 비교에 실제 사용. 다른 좌표의 결측 대체에 사용하지 않음.',
        'GRNDS_CTPV_NM':'재난시도명과 현장시도명의 일치 여부를 실제 비교. 임의 지역 대체 없음.',
        'GRNDS_SGG_NM':'재난구군명과 현장구군명의 일치·불일치를 실제 집계. 불일치를 위치 오류로 확정하지 않음.',
        'CMPTNC_FRSTN_NM':'연도·종별·재난구군별 기록상 관할소방서 분포를 실제 집계. 현재 운영시간·가용인력의 근거는 아님.',
        'PLCSCN_CNTR_NM':'관할소방서와 함께 기록상 관할센터의 분포를 실제 집계. 현재 서비스 범위·현장 도착시간의 근거는 아님.',
    }
    wb=openpyxl.load_workbook(workbook,read_only=True,data_only=True)
    sheet=wb['column_info']; rows=[]
    for row_number,row in enumerate(sheet.iter_rows(values_only=True),1):
        if len(row)<6 or not isinstance(row[1],str): continue
        english=row[1].strip().upper()
        if english not in prior_reasons: continue
        chosen=english in selected
        if chosen:
            group='현재 분석 선택17'; reason=uses.get(english,prior_reasons[english])
        elif english in time_columns:
            group='중복 시간 표현10'; reason='신고일시 DCLR_DT와 일관성이 검증된 중복 시간 표현. 현재 필요한 연·월·요일·시간·계절은 단일 신고일시에서 파생하여 사용.'
        elif english.startswith('RCPT_END_'):
            group='접수종료3'; reason='접수 업무 종료 시점이며 현장 도착시간·대응 소요시간이 아님. 현재 신고 특성 비교에 필요하지 않아 제외; 원본 유지.'
        elif english=='CTY_FRMVL_SE_NM':
            group='도시농촌1'; reason='현재 원문지역·유형별 비교에서 추가 설명 필요성이 확인되지 않아 제외. 상세 지역 환경은 질문에 맞는 자료로 별도 확인; 원본 유지.'
        elif english=='EMRG_RSCU_SCL_NM':
            group='긴급구조규모1'; reason='설명서에는 긴급구조 규모에 따른 출동 횟수라고 적혀 있으나 접수행·사건·환자 수의 대체 지표로 사용하지 않음. 현재 규모명 분석 질문이 없어 제외; 원본 유지.'
        elif english in flags:
            group='플래그6'; reason='현재 지역·유형·시간·관할·좌표 진단의 분석 변수로 사용하지 않아 선택17에서 제외. 실제 Y·N·공란과 연도별 기록 차이는 별도 도메인 표로 검증했고 공란을 N으로 대체하지 않음; 원본 유지.'
            if english=='CENTR_RSUN_DSPT_DMND_YN': reason+=' 현재5년 전부 공란으로 값에 따른 비교가 불가능함.'
        else: raise AssertionError(english)
        rows.append({'excel_sheet':sheet.title,'excel_row':row_number,
            'english_cell':f'B{row_number}','korean_cell':f'E{row_number}','detail_cell':f'F{row_number}',
            'english_name_original':row[1],'english_name_normalized':english,'korean_name':row[4],
            'detail_description':row[5],'selected17':chosen,'decision_group':group,
            'current_use_or_exclusion_reason':reason,'original_preservation':'원본 수정·삭제 없음'})
    wb.close()
    assert len(rows)==38 and len({x['english_name_normalized'] for x in rows})==38
    codebook_names={x['english_name_normalized'] for x in rows}
    assert selected<=codebook_names
    header_checks=[]
    for item in inputs['reports']:
        source=ROOT/item['file']
        with source.open(encoding=item['encoding'],newline='') as f: headers=next(csv.reader(f))
        normalized=[h.upper() for h in headers]
        assert set(normalized)==codebook_names and len(normalized)==38
        assert source.stat().st_size==item['bytes']
        header_checks.append({'year':item['year'],'file':item['file'],'actual_headers':headers,
            'normalized_header_count':len(normalized),'header_set_matches_codebook':True,
            'missing_from_codebook':[],'extra_codebook_columns':[],
            'bytes_checked_now':source.stat().st_size,'previously_verified_source_sha256':item['sha256'],
            'hash_evidence_note':'This focused audit rereads headers and file size only; unchanged source SHA was verified in the preceding completeness run and is reused, not recomputed here.'})
    output=OUT/'codebook_all38_selection.csv'
    pd.DataFrame(rows).to_csv(output,index=False,encoding='utf-8-sig')
    groups=pd.Series([x['decision_group'] for x in rows]).value_counts().to_dict()
    assert sum(x['selected17'] for x in rows)==17
    audit={'workbook':str(workbook.relative_to(ROOT)),'workbook_sha256':sha(workbook),
        'worksheet':'column_info','definition_range':'B3:F40','rows_read':38,
        'selected_count':17,'excluded_from_current_analysis_count':21,'decision_groups':groups,
        'all_five_header_sets_match':True,'source_header_checks':header_checks,
        'input_manifest':str(input_path.relative_to(ROOT)),'input_manifest_sha256':sha(input_path),
        'reused_reason_source':str(prior_decisions.relative_to(ROOT)),'reused_reason_source_sha256':sha(prior_decisions),
        'current_policy':str((OUT/'comparison_policy.json').relative_to(ROOT)),
        'current_policy_sha256':sha(OUT/'comparison_policy.json'),
        'policy_note':'17 selected fields have equal missing-value exclusion status. Earlier core/auxiliary labels are not carried into this selection table.',
        'coordinate_note':'Workbook Korean label is 사고발생경도/위도 but details say 환자발생 위치; neither field definition supplies verified CRS, positional accuracy or applicability to every incident type.',
        'output':output.name,'output_sha256':sha(output),
        'script':str(Path(__file__).relative_to(ROOT)),'script_sha256':sha(__file__)}
    (OUT/'codebook_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'definitions':38,'selected':17,'excluded':21,'groups':groups,'all_five_headers_match':True},ensure_ascii=False))

if __name__=='__main__': main()
