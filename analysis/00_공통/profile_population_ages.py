"""부산 전 연령 주민등록인구 배경 비교. 신고 대상 연령을 추정하지 않는다."""
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed/연령배경비교'
DOC=ROOT/'docs/40-분석결과/부산-전체연령-배경비교.md'
AUDIT=ROOT/'data/interim/인구배경/audit.json'
SOURCE='https://jumin.mois.go.kr/ageStatMonth.do'


def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()


def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    previous=json.loads(AUDIT.read_text(encoding='utf-8'))
    sources=sorted([r for r in previous['files'] if '성연령별1인세대' not in r['file']],key=lambda r:r['period'])
    require([s['period'] for s in sources]==[f'{y}-12' for y in range(2018,2025)],'인구 원본 7개 연말 기간 불일치')
    groups=[(start,start+9,f'{start}~{start+9}세') for start in range(0,100,10)]+[(100,None,'100세 이상')]
    records=[];summary_records=[];source_checks=[];lookup={}
    for source in sources:
        file=ROOT/source['file'];year=int(source['period'][:4]);hash_value=sha(file)
        require(hash_value==source['sha256'],f'{year} 기존 감사 원본 해시 불일치')
        with file.open(encoding='cp949',newline='') as f:
            all_rows=list(csv.reader(f,strict=True))
        headers=all_rows[0];rows=all_rows[1:]
        require(len(rows)==source['rows'] and headers==source['headers'],f'{year} 원본 행·컬럼 불일치')
        # 성별 계만 선택한다. 남·여 열과 더해 같은 인구를 중복 계산하지 않는다.
        age_indexes={}
        for index,header in enumerate(headers):
            match=re.fullmatch(fr'{year}년12월_계_(\d+)세( 이상|이상)?',header)
            if match:age_indexes[int(match.group(1))]=index
        require(set(age_indexes)==set(range(101)),f'{year} 0~99세·100세 이상 열 누락')
        total_index=headers.index(f'{year}년12월_계_총인구수')
        selected=[]
        for row in rows:
            require(len(row)==len(headers),f'{year} 원본 행 길이 오류')
            code_match=re.search(r'\((\d{10})\)',row[0]);require(code_match is not None,f'{year} 지역코드 형식 오류')
            code=code_match.group(1)
            if not(code.startswith('26') and code.endswith('00000')):continue
            area=row[0][:code_match.start()].strip();level='시' if code=='2600000000' else '구군'
            values={age:int(row[i].replace(',','')) for age,i in age_indexes.items()}
            total=int(row[total_index].replace(',',''))
            require(sum(values.values())==total,f'{year} {code} 1세별 합계 불일치')
            counts=[]
            for lo,hi,label in groups:
                count=sum(values[age] for age in range(lo,(hi if hi is not None else 100)+1))
                records.append(dict(연도=year,기준월=12,공간수준=level,행정구역코드=code,행정구역명=area,연령구간=label,인구수=count,지역총인구=total,지역내비중_pct=round(count/total*100,6)))
                counts.append(count)
            require(sum(counts)==total,f'{year} {code} 연령구간 합계 불일치')
            age65plus=sum(values[age] for age in range(65,101))
            under65=sum(values[age] for age in range(65))
            require(under65+age65plus==total,f'{year} {code} 65세 기준 합계 불일치')
            for label,count in [('65세 미만',under65),('65세 이상',age65plus)]:
                summary_records.append(dict(연도=year,기준월=12,공간수준=level,행정구역코드=code,행정구역명=area,연령구간=label,인구수=count,지역총인구=total,지역내비중_pct=round(count/total*100,6)))
            selected.append(code);lookup[(year,code)]=dict(area=area,total=total,counts=counts,under65=under65,age65plus=age65plus)
        require(len(selected)==17 and len(set(selected))==17,f'{year} 부산시+16구군 범위 불일치')
        require(lookup[(year,'2600000000')]['total']==source['busan']['total'],f'{year} 부산 감사 총계 불일치')
        for i in range(11):
            require(sum(lookup[(year,c)]['counts'][i] for c in selected if c!='2600000000')==lookup[(year,'2600000000')]['counts'][i],f'{year} 16구군 연령구간 합계 불일치')
        for field in ['under65','age65plus']:
            require(sum(lookup[(year,c)][field] for c in selected if c!='2600000000')==lookup[(year,'2600000000')][field],f'{year} 16구군 65세 기준 합계 불일치')
        require(lookup[(year,'2600000000')]['age65plus']==source['busan']['age65plus'],f'{year} 기존 감사 65세 이상 합계 불일치')
        source_checks.append(dict(year=year,file=source['file'],sha256=hash_value,nationalRows=len(rows),selectedRegions=len(selected),hashMatchesPriorAudit=True,allAgesSumToTotal=True,districtAgeSumsMatchCity=True))
    require(len(records)==7*17*11,'최종 행 수 불일치')
    require(len(summary_records)==7*17*2,'65세 기준 요약 행 수 불일치')
    OUT.mkdir(parents=True,exist_ok=True);DOC.parent.mkdir(parents=True,exist_ok=True)
    csv_file=OUT/'부산_2018-2024_시구군_전체연령.csv'
    with csv_file.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    with csv_file.open(encoding='utf-8-sig',newline='') as f:readback=list(csv.DictReader(f))
    require(len(readback)==len(records),'출력 CSV 재읽기 행 수 불일치')
    for year,code in lookup:
        selected=[r for r in readback if int(r['연도'])==year and r['행정구역코드']==code]
        require(len(selected)==11 and sum(int(r['인구수']) for r in selected)==lookup[(year,code)]['total'],'출력 연령구간 합계 불일치')
    summary_file=OUT/'부산_2018-2024_시구군_65세기준요약.csv'
    with summary_file.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary_records[0]));writer.writeheader();writer.writerows(summary_records)
    with summary_file.open(encoding='utf-8-sig',newline='') as f:summary_readback=list(csv.DictReader(f))
    require(len(summary_readback)==238,'65세 기준 출력 재읽기 행 수 불일치')
    for year,code in lookup:
        selected=[r for r in summary_readback if int(r['연도'])==year and r['행정구역코드']==code]
        require(len(selected)==2 and sum(int(r['인구수']) for r in selected)==lookup[(year,code)]['total'],'65세 기준 출력 합계 불일치')
    start=lookup[(2018,'2600000000')];end=lookup[(2024,'2600000000')]
    diff=end['total']-start['total']
    change=[end['counts'][i]-start['counts'][i] for i in range(11)]
    most_up=max(range(11),key=lambda i:change[i]);most_down=min(range(11),key=lambda i:change[i])
    lines=['# 부산 전체 연령 배경 비교 — 2018~2024년','',
        '**신고 분석의 비교 배경으로 전체 연령을 유지했다.** 어린이·노약자 지원을 검토하더라도 중간 연령대를 제외하지 않는다. 아래 결과는 주민등록인구 구조 변화이며, 119 신고 대상자의 연령이나 예방활동 효과가 아니다.','',
        f"부산 연말 주민등록인구는 2018년 {start['total']:,}명에서 2024년 {end['total']:,}명으로 {abs(diff):,}명 {'감소' if diff<0 else '증가'}했다({diff/start['total']*100:+.2f}%). 구간별로는 {groups[most_up][2]}가 {change[most_up]:+,}명으로 가장 많이 늘었고, {groups[most_down][2]}가 {change[most_down]:+,}명으로 가장 많이 줄었다.",'',
        f'[출처: 행정안전부, 2018~2024년 각 12월 말, 연령별 주민등록인구]({SOURCE}). 원본·검증 해시는 `data/processed/연령배경비교/검증_manifest.json`에 기록했다.','',
        '| 연령구간 | 2018년 인구 | 2024년 인구 | 인구 증감 | 2018년 비중 | 2024년 비중 |',
        '|---|---:|---:|---:|---:|---:|']
    for i,(_,_,label) in enumerate(groups):lines.append(f"| {label} | {start['counts'][i]:,} | {end['counts'][i]:,} | {change[i]:+,} | {start['counts'][i]/start['total']*100:.2f}% | {end['counts'][i]/end['total']*100:.2f}% |")
    lines += ['', '## 주요 요약: 65세 기준','',
        '핵심 배경 설명에는 65세 미만·65세 이상 요약을 함께 쓴다. 원본의 65~69세부터 정확하게 합산했으며 60대를 통째로 65세 이상에 넣지 않았다. 기존 11구간 표와 데이터도 보존했다.','',
        '| 연도 | 65세 미만 | 65세 이상 | 65세 이상 비중 |',
        '|---|---:|---:|---:|',
        f"| 2018 | {start['under65']:,}명 | {start['age65plus']:,}명 | {start['age65plus']/start['total']*100:.2f}% |",
        f"| 2024 | {end['under65']:,}명 | {end['age65plus']:,}명 | {end['age65plus']/end['total']*100:.2f}% |",'',
        '65세 미만에는 어린이·청년·중년 등이 모두 포함되며 어느 연령도 제외하지 않았다. 이 요약은 어린이 범위를 확정하지 않고, 65세 이상이라는 사실만으로 노약자·장애·질병을 단정하지 않는다. 90~99세 등 세부 구간은 전체 분포를 보존하기 위한 것이며 별도 핵심 지원대상으로 확정한 것이 아니다.','',
        '## 범위와 해석','',
        '- 2018~2024년 7년 × 부산시·16구군 17지역 × 전체 연령 11구간 = 1,309행이다. 2019~2023년도 같은 CSV에 모두 포함했다.',
        '- 원본의 성별 `계`만 사용했다. 0~99세의 각 1세와 100세 이상 열을 빠짐없이 한 번씩 더했다. 남녀 열을 추가 합산하지 않았다.',
        '- 각 연도·지역의 11구간 합계가 원본 총인구와 일치하며, 구간별 16구군 합계도 부산시와 일치한다. 부산시 행과 구군 행을 함께 더하면 중복 집계된다.',
        '- 0~9세는 표시한 나이 구간이며 법적 어린이 전체와 같지 않다. 60~69세를 노약자로 단정하지 않는다. 연령만으로 질병·장애·돌봄 필요를 식별할 수 없다.',
        '- 100세 이상 인구의 큰 변화는 확인한 원자료 수치를 그대로 반영했다. 변화 원인을 확인하기 전에는 인구 현상이나 등록 정비 등의 원인 해석을 보류한다.',
        '- 지역내비중은 해당 지역·연도의 총인구를 분모로 직접 계산했다. 문서의 소수 둘째 자리 표시는 반올림이므로 비중 합계가 표시상 100%와 조금 다를 수 있다.',
        '- 연말 주민등록인구는 연중 유동인구·관광객·외국인을 포괄하는 위험 노출 인구가 아니다. 기본 전체 조회에는 거주불명자·재외국민이 포함되고 외국인은 제외된다.',
        '- 연령 인구구조와 신고 유형 분포는 별도로 비교할 배경이다. 인구비율로 신고에 나이를 붙이거나 연령별 신고 수·고독사 위험을 만들지 않았다.',
        '- 지역별 연령 구조는 중점 검토 대상을 논의하는 근거 중 하나이며, 특정 구나 인력·활동 배치를 확정한 결과가 아니다.','',
        '## 파일과 재현','',
        '- 집계: `data/processed/연령배경비교/부산_2018-2024_시구군_전체연령.csv`',
        '- 65세 기준 요약: `data/processed/연령배경비교/부산_2018-2024_시구군_65세기준요약.csv` (7년 × 17지역 × 2구간 = 238행)',
        '- 검증: `data/processed/연령배경비교/검증_manifest.json`',
        '- 실행: `.venv-check/Scripts/python.exe analysis/00_공통/profile_population_ages.py`','']
    DOC.write_text('\n'.join(lines),encoding='utf-8')
    manifest=dict(generatedAt=datetime.now(timezone.utc).isoformat(),script='analysis/00_공통/profile_population_ages.py',scriptSha256=sha(Path(__file__)),sourceUrl=SOURCE,sourceAudit=str(AUDIT.relative_to(ROOT)),sourceAuditSha256=sha(AUDIT),sources=source_checks,years=list(range(2018,2025)),regionsPerYear=17,ageBands=[g[2] for g in groups],csvRows=len(records),age65SummaryRows=len(summary_records),age65SummaryChecksPass=True,outputs=[dict(file=str(csv_file.relative_to(ROOT)),sha256=sha(csv_file)),dict(file=str(summary_file.relative_to(ROOT)),sha256=sha(summary_file)),dict(file=str(DOC.relative_to(ROOT)),sha256=sha(DOC))],allChecksPass=True,notes=['전체 연령 포함. 성별 계만 사용. 원본 1세별 값의 정확한 합계.','65세 기준 요약은 0~64세와 65~99세 및 100세 이상으로 전체 인구를 중복 없이 나눈 것이다.','부산시와 구군은 상하위 공간 수준이므로 같이 더하지 않는다.','연령별 신고 추정이나 신고 자료 결합은 수행하지 않았다.','연령구간은 분석 표시 단위이며 법적 어린이·노약자·장애·질병 정의가 아니다.'])
    (OUT/'검증_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(rows=len(records),city2018=start,city2024=end,allChecksPass=True),ensure_ascii=False))


if __name__=='__main__':main()
