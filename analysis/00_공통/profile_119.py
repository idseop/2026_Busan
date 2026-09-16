"""119 접수 전행의 원문 분류별 기초 집계. 사건/연령 추정이나 원본 변경 없음."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/119기초분석'
AUDIT = ROOT / 'data/interim/119접수감사/audit.json'
DISTRICTS = {'중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군'}


def digest(file):
    """전체 바이트 해시. CSV 해석과 별도로 수신 원본 일치 여부를 확인한다."""
    h = hashlib.sha256()
    with file.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def check_equal(actual, expected, label):
    if actual != expected: raise ValueError(f'{label}: 실제 {actual}, 기대 {expected}')


def main():
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    files = sorted(audit['files'], key=lambda f: f['year'])
    check_equal([f['year'] for f in files], list(range(2018,2025)), '분석 연도')
    # 빈 분류는 빈 문자열로 보존하고, 확인되지 않은 조합의 0행은 생성하지 않는다.
    dimensions = ['연도','긴급구조종별','긴급구조분류','처리결과']
    tables = {
        '전체_연도종별분류처리결과': (dimensions, Counter()),
        '부산명시_연도구군종별분류처리결과': (['연도','재난시군구','긴급구조종별','긴급구조분류','처리결과'], Counter()),
        '전체_연도월종별분류처리결과': (['연도','월']+dimensions[1:], Counter()),
        '전체_연도시간종별분류처리결과': (['연도','시간']+dimensions[1:], Counter()),
        '부산명시_연도월종별분류처리결과': (['연도','월']+dimensions[1:], Counter()),
        '부산명시_연도시간종별분류처리결과': (['연도','시간']+dimensions[1:], Counter()),
        '전체_연도재난시도구군기재상태': (['연도','재난시도','구군기재상태'], Counter()),
    }
    sources=[]
    for meta in files:
        file = ROOT / meta['file']
        hash_value = digest(file)
        check_equal(hash_value,meta['sha256'],f"{meta['year']} 감사 원본 해시")
        year=meta['year']; total=0; busan=0; missing_district=0; missing_province=0
        districts=Counter(); result_counts=Counter(); type_counts=Counter(); month_counts=Counter(); hour_counts=Counter()
        busan_district_counts=Counter()
        with file.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.reader(f,strict=True)
            header=[h.strip().upper() for h in next(reader)]
            check_equal(sorted(header),sorted(meta['schema']),f'{year} 컬럼')
            idx={name:i for i,name in enumerate(header)}
            for row in reader:
                if not row or row==['']:continue
                check_equal(len(row),len(header),f'{year} CSV 열 수')
                get=lambda name:row[idx[name]]
                check_equal(get('DCLR_YR').strip(),str(year),f'{year} 원본 연도')
                month=get('DCLR_MM');hour=get('DCLR_HR')
                if not (month.isdigit() and 1<=int(month)<=12 and hour.isdigit() and 0<=int(hour)<=23):raise ValueError(f'{year} 월/시간 범위 오류')
                kind=get('EMRG_RSCU_ASSRT_NM');subtype=get('EMRG_RSCU_CLSF_NM');result=get('PRCS_RSLT_SE_NM')
                province=get('CLMTY_CTPV_NM');district=get('CLMTY_SGG_NM')
                base=(kind,subtype,result)
                total+=1
                result_counts[result.strip() or '(빈값)']+=1;type_counts[kind.strip() or '(빈값)']+=1
                month_counts[get('DCLR_YMD').strip()[:6]]+=1;hour_counts[hour.strip() or '(빈값)']+=1
                tables['전체_연도종별분류처리결과'][1][(year,)+base]+=1
                tables['전체_연도월종별분류처리결과'][1][(year,month)+base]+=1
                tables['전체_연도시간종별분류처리결과'][1][(year,hour)+base]+=1
                tables['전체_연도재난시도구군기재상태'][1][(year,province,'미기재' if not district.strip() else '기재')]+=1
                if not province.strip():missing_province+=1
                if province.strip()=='부산광역시':
                    busan+=1
                    if not district.strip():missing_district+=1
                    districts[district]+=1;busan_district_counts[district.strip() or '(빈값)']+=1
                    tables['부산명시_연도구군종별분류처리결과'][1][(year,district)+base]+=1
                    tables['부산명시_연도월종별분류처리결과'][1][(year,month)+base]+=1
                    tables['부산명시_연도시간종별분류처리결과'][1][(year,hour)+base]+=1
        check_equal(total,meta['rows'],f'{year} 전체 행 합계')
        check_equal(busan,meta['busan']['rows'],f'{year} 부산 행 합계')
        check_equal(dict(busan_district_counts),meta['busan']['byDistrict'],f'{year} 부산 구군 주변합계')
        check_equal(dict(result_counts),meta['categories']['PRCS_RSLT_SE_NM'],f'{year} 처리결과 주변합계')
        check_equal(dict(type_counts),meta['categories']['EMRG_RSCU_ASSRT_NM'],f'{year} 종별 주변합계')
        check_equal(dict(month_counts),meta['date']['byMonth'],f'{year} 월별 주변합계')
        check_equal(dict(hour_counts),meta['categories']['DCLR_HR'],f'{year} 시간별 주변합계')
        for name,(_,counter) in tables.items():
            check_equal(sum(n for k,n in counter.items() if k[0]==year),busan if name.startswith('부산명시_') else total,f'{year} {name} 합계')
        sources.append(dict(year=year,file=meta['file'],sha256=hash_value,rows=total,busanRows=busan,busanDistrictMissing=missing_district,provinceMissing=missing_province,districtsAbsent=sorted(DISTRICTS-set(districts)),districtLabelsUnexpected=sorted(k for k in districts if k.strip() and k not in DISTRICTS),sourceAuditMatches=True,aggregateChecksPass=True))
        print(json.dumps(sources[-1],ensure_ascii=False),flush=True)
    # 모든 원본의 검사가 통과한 뒤에만 분석용 파일을 생성한다.
    OUT.mkdir(parents=True,exist_ok=True)
    outputs=[]
    for name,(headers,counter) in tables.items():
        file=OUT/(name+'.csv')
        with file.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.writer(f);writer.writerow(headers+['접수행수'])
            for key,count in sorted(counter.items()):writer.writerow(list(key)+[count])
        outputs.append(dict(file=str(file.relative_to(ROOT)),rows=len(counter),columns=headers+['접수행수'],countSum=sum(counter.values()),sha256=digest(file)))
    summary=dict(years=list(range(2018,2025)),totalRows=sum(s['rows'] for s in sources),busanRows=sum(s['busanRows'] for s in sources),yearsDetail=sources)
    summary_file=OUT/'연도별요약.json';summary_file.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    outputs.append(dict(file=str(summary_file.relative_to(ROOT)),sha256=digest(summary_file)))
    manifest=dict(generatedAt=datetime.now(timezone.utc).isoformat(),script='analysis/00_공통/profile_119.py',scriptSha256=digest(Path(__file__)),sourceAudit=str(AUDIT.relative_to(ROOT)),sourceAuditSha256=digest(AUDIT),source='사용자 제공 부산소방재난본부 119 신고접수 2018~2024 전체 CSV',sources=sources,outputs=outputs,allChecksPass=True,rules=['종별=EMRG_RSCU_ASSRT_NM, 분류=EMRG_RSCU_CLSF_NM, 처리결과=PRCS_RSLT_SE_NM. 원문 분류 문자열을 보존한다.','부산명시는 CLMTY_CTPV_NM의 trim 값이 부산광역시인 행. GRNDS 지역으로 미기재 재난지역을 채우지 않는다.','빈 문자열은 원본 결측이며 0건이 아니다. 미등장 조합의 0행을 생성하지 않았다.','각 CSV는 동일한 접수를 다른 차원에서 집계한 것이므로 파일 사이의 접수행수를 더하지 않는다.','월과 시간은 원본 값. 시간은 0~23시 시각 범주이며 개인별 시각은 출력하지 않는다.','모든 처리결과를 포함한다. 정상만 필터링해도 독립 사고·환자 수를 의미하지 않는다.','개별 접수번호·사건 주소·좌표·일자는 출력하지 않는다. 사건 식별 및 중복사고 제거는 수행하지 않았다.','집계 행 수의 내부 일관성 검사이며 실제 지역별 사건 누락 부재·분류 정확성·정책 효과의 증명은 아니다.'])
    (OUT/'검증_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(outputs=len(outputs),totalRows=summary['totalRows'],busanRows=summary['busanRows'],allChecksPass=True),ensure_ascii=False))


if __name__=='__main__':main()
