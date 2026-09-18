"""검증된 지역 집계를 정적 웹 JSON으로 변환한다. 원시 신고나 좌표는 배포하지 않는다."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'web/data/dashboard.json'
VERIFY=ROOT/'data/interim/웹데이터검증'
YEARS=list(range(2018,2025))
NAMES=['중구','서구','동구','영도구','부산진구','동래구','남구','북구','해운대구','사하구','금정구','강서구','연제구','수영구','사상구','기장군']
LABELS=[f'{x}~{x+9}세' for x in range(0,100,10)]+['100세 이상']
FIELDS={'A':'A_모든처리','B':'B_정상','C':'C_정상_3분류제외'}
REPORT_TYPES=['구급','구조','화재','기타','미기재']


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition,message):
    if not condition:raise ValueError(message)


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))


def read_json(path):return json.loads(path.read_text(encoding='utf-8'))


def check_manifest_output(manifest,path):
    relative=path.relative_to(ROOT).as_posix()
    record=next(r for r in manifest['outputs'] if r['file'].replace('\\','/')==relative)
    require(sha(path)==record['sha256'],f'기존 검증 해시 불일치: {relative}')


def main():
    conditions_file=ROOT/'data/processed/신고조건비교/연도구군_조건별접수건수_순위변화.csv'
    conditions_manifest_file=conditions_file.parent/'manifest.json'
    ages_file=ROOT/'data/processed/연령배경비교/부산_2018-2024_시구군_전체연령.csv'
    summary_file=ages_file.parent/'부산_2018-2024_시구군_65세기준요약.csv'
    ages_manifest_file=ages_file.parent/'검증_manifest.json'
    year_totals_file=ROOT/'data/processed/119기초분석/연도별요약.json'
    base_manifest_file=year_totals_file.parent/'검증_manifest.json'
    conditions_manifest=read_json(conditions_manifest_file)
    ages_manifest=read_json(ages_manifest_file)
    base_manifest=read_json(base_manifest_file)
    base_file=ROOT/conditions_manifest['source']
    require(sha(conditions_file)==conditions_manifest['output_sha256'],'신고 조건표 해시 불일치')
    require(sha(base_file)==conditions_manifest['source_sha256'],'조건표 기초 집계 해시 불일치')
    for file in [ages_file,summary_file]:check_manifest_output(ages_manifest,file)
    for file in [base_file,year_totals_file]:check_manifest_output(base_manifest,file)
    condition_rows=read_csv(conditions_file);age_rows=read_csv(ages_file);summary_rows=read_csv(summary_file)
    require(len(condition_rows)==136 and len(age_rows)==1309 and len(summary_rows)==238,'입력 집계 행 수 불일치')
    condition_lookup={(r['기간'],r['재난시군구']):r for r in condition_rows}
    require(len(condition_lookup)==136,'조건표 키 중복')
    # 부산명시 기초 교차표에서 조건을 다시 적용해 조건표 136행을 직접 검산한다.
    direct=defaultdict(lambda:{'A':0,'B':0,'C':0})
    direct_types=defaultdict(lambda:{kind:{'A':0,'B':0,'C':0} for kind in REPORT_TYPES})
    raw_types=set()
    excluded=set(conditions_manifest['excluded_exact_values'])
    require(excluded=={'업무운행','훈련출동','구급차소독'},'조건 C 제외 원문 변경')
    for row in read_csv(base_file):
        n=int(row['접수행수'])
        raw_kind=row['긴급구조종별'];raw_types.add(raw_kind)
        require(raw_kind in {'구급','구조','화재','기타',''},'확인하지 않은 원본 종별 값')
        kind=raw_kind if raw_kind else '미기재'
        for period in [row['연도'],'7년합계']:
            target=direct[(period,row['재난시군구'])];target['A']+=n
            typed=direct_types[(period,row['재난시군구'])][kind];typed['A']+=n
            if row['처리결과']=='정상':
                target['B']+=n
                typed['B']+=n
                if row['긴급구조분류'] not in excluded:target['C']+=n;typed['C']+=n
    require(raw_types=={'구급','구조','화재','기타',''},'원본 종별 5값 범위 변화')
    for key,row in condition_lookup.items():
        for code,column in FIELDS.items():require(direct[key][code]==int(row[column]),f'{key} 조건{code} 원집계 불일치')
        for condition in FIELDS:require(sum(group[condition] for group in direct_types[key].values())==direct[key][condition],f'{key} 종별 합과 기존 조건 합 불일치')
    all_years=read_json(year_totals_file)
    original_years={r['year']:r for r in all_years['yearsDetail']}
    population={}
    for row in age_rows:
        year=int(row['연도']);raw_name=row['행정구역명']
        name=raw_name if raw_name=='부산광역시' else raw_name.removeprefix('부산광역시 ')
        require(name in NAMES+['부산광역시'],'인구 구군명 불일치')
        value=population.setdefault((year,name),dict(name=name,moisCode=row['행정구역코드'],populationTotal=int(row['지역총인구']),ageBands={}))
        require(value['moisCode']==row['행정구역코드'] and value['populationTotal']==int(row['지역총인구']),'인구 지역 총계·코드 불일치')
        require(row['연령구간'] not in value['ageBands'],'연령 구간 중복')
        value['ageBands'][row['연령구간']]=int(row['인구수'])
    for row in summary_rows:
        name=row['행정구역명'] if row['행정구역명']=='부산광역시' else row['행정구역명'].removeprefix('부산광역시 ')
        value=population[(int(row['연도']),name)]
        require(value['moisCode']==row['행정구역코드'] and value['populationTotal']==int(row['지역총인구']),'65세 요약 지역 대응 불일치')
        field={'65세 미만':'ageUnder65','65세 이상':'age65plus'}[row['연령구간']]
        require(field not in value,'65세 기준 구간 중복')
        value[field]=int(row['인구수'])
    require(len(population)==119,'7년 17지역 인구 범위 불일치')
    for value in population.values():
        require(set(value['ageBands'])==set(LABELS),'전체 연령 구간 누락')
        require(sum(value['ageBands'].values())==value['populationTotal'],'11구간 총계 불일치')
        require(value['ageUnder65']+value['age65plus']==value['populationTotal'],'65세 요약 총계 불일치')
        value['ageBands']=[dict(label=label,count=value['ageBands'][label]) for label in LABELS]
    by_year={}
    for year in YEARS:
        require({district for period,district in condition_lookup if period==str(year)}==set(NAMES+['']),f'{year} 신고 구군 범위 불일치')
        missing={k:int(condition_lookup[(str(year),'')][col]) for k,col in FIELDS.items()}
        missing_types=direct_types[(str(year),'')]
        districts={}
        for name in NAMES:
            value=population[(year,name)].copy();row=condition_lookup[(str(year),name)]
            value['reports']={k:int(row[col]) for k,col in FIELDS.items()}
            value['reportsByType']=direct_types[(str(year),name)]
            value['ranks']={k:int(row[k+'_건수순위']) for k in FIELDS}
            require(value['reports']['A']>=value['reports']['B']>=value['reports']['C'],'신고 조건 포함관계 오류')
            districts[name]=value
        for condition in FIELDS:
            for value in districts.values():
                expected=1+sum(other['reports'][condition]>value['reports'][condition] for other in districts.values())
                require(value['ranks'][condition]==expected,'동률 min 접수건수 순위 불일치')
        city=population[(year,'부산광역시')].copy()
        city['reports']={key:sum(r['reports'][key] for r in districts.values())+missing[key] for key in FIELDS}
        city['reportsByType']={kind:{condition:sum(r['reportsByType'][kind][condition] for r in districts.values())+missing_types[kind][condition] for condition in FIELDS} for kind in REPORT_TYPES}
        for condition in FIELDS:
            require(sum(v[condition] for v in city['reportsByType'].values())==city['reports'][condition],f'{year} 부산시 종별 합 불일치')
            require(sum(v[condition] for v in missing_types.values())==missing[condition],f'{year} 구군 미기재 종별 합 불일치')
        for value in [city]+list(districts.values()):
            for kind,counts in value['reportsByType'].items():require(counts['A']>=counts['B']>=counts['C'],f'{year} {kind} 종별 조건 포함관계 오류')
        original=original_years[year]
        require(city['reports']['A']==original['busanRows'],'부산 명시 총계 불일치')
        require(missing['A']==original['busanDistrictMissing'],'부산 구군 미기재 불일치')
        city['totalReceived']=original['rows'];city['provinceMissing']=original['provinceMissing']
        for field in ['populationTotal','age65plus','ageUnder65']:
            require(sum(r[field] for r in districts.values())==city[field],f'{year} 구군 합과 부산시 {field} 불일치')
        for i in range(11):require(sum(r['ageBands'][i]['count'] for r in districts.values())==city['ageBands'][i]['count'],'구군 연령별 합 불일치')
        by_year[str(year)]=dict(city=city,missingDistrict=missing,missingDistrictByType=missing_types,districts=districts)
    source_files=[conditions_file,ages_file,summary_file,base_file,year_totals_file,conditions_manifest_file,ages_manifest_file,base_manifest_file]
    sources=[dict(path=f.relative_to(ROOT).as_posix(),sha256=sha(f),url='https://jumin.mois.go.kr/ageStatMonth.do' if '연령배경비교' in f.as_posix() else None) for f in source_files]
    data=dict(schemaVersion=1,years=YEARS,districtNames=NAMES,ageBandLabels=LABELS,reportTypes=REPORT_TYPES,conditions={
        'A':dict(label='전체 처리결과',description='재난시도 부산 명시 접수의 모든 처리결과'),
        'B':dict(label='정상 처리',description='A 중 처리결과 원문이 정확히 정상인 접수'),
        'C':dict(label='정상·3분류 제외',description='B 중 업무운행·훈련출동·구급차소독 원문 3분류만 제외')},byYear=by_year,provenance=dict(sources=sources,notes=[
        '신고와 인구를 같은 연도·16구군 단위로 별도 표시한다. 개인이나 개별 신고에 인구 연령을 부여하지 않는다.',
        'reports는 재난시도 부산 명시 접수 건수다. city.reports는 16구군과 missingDistrict를 합친 값이다.',
        'city.totalReceived는 사용자 부산 119 파일의 전체 접수 행 수이며 재난시도 미기재도 포함한다. provinceMissing은 그 미기재 행 수다.',
        'A/B/C는 처리조건 비교이며 위험도·지원 우선순위·실제 독립 사고 수가 아니다. ranks는 접수건수 내림차순 동률 min이다.',
        'reportsByType는 원문 긴급구조종별별 동일 조건 집계다. 미기재는 원본 빈 문자열의 표시명이며 다른 유형으로 재분류하지 않았다. ranks는 전체 종별 합 기준으로 유형별 순위에 사용하지 않는다.',
        '인구는 각 연도 12월 말 주민등록 성별 계. 전체 11구간과 65세 미만/이상을 모두 보존한다.',
        '전체 연령 표와 65세 요약은 같은 인구를 다른 구간으로 표시한 것이므로 더하지 않는다.',
        '65세 이상을 노약자·질병·장애로 단정하지 않는다. 어린이 범위를 확정하거나 중간 연령을 제외하지 않는다.',
        '이 JSON에는 경계가 없다. 지도 경계의 기준시점·코드체계·공식 출처는 별도 레이어에서 확인해야 한다.'
    ]))
    OUT.parent.mkdir(parents=True,exist_ok=True);VERIFY.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    readback=read_json(OUT);require(readback==data,'웹 JSON 재읽기 불일치')
    manifest=dict(generatedAt=datetime.now(timezone.utc).isoformat(),script=Path(__file__).relative_to(ROOT).as_posix(),scriptSha256=sha(Path(__file__)),output=OUT.relative_to(ROOT).as_posix(),outputSha256=sha(OUT),sources=sources,checks=dict(sourceHashesMatch=True,condition136RowsRecomputed=True,population119RegionTotalsMatch=True,all11AgeBandsPresent=True,age65SummaryTotalsMatch=True,districtAndMissingSumToCity=True,ranksMatchMinTies=True,noIndividualIncidentRows=True,jsonReadbackMatches=True),years=YEARS,districtsPerYear=16)
    manifest['reportTypes']=REPORT_TYPES
    manifest['checks'].update(rawFiveReportTypesVerified=True,reportTypeSumsMatchOverall=True,reportTypeDistrictAndMissingSumToCity=True,noPopulationAllocatedToReportTypes=True)
    (VERIFY/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(file=OUT.relative_to(ROOT).as_posix(),bytes=OUT.stat().st_size,years=len(YEARS),districtRecords=112,checksPass=True),ensure_ascii=False))


if __name__=='__main__':main()
