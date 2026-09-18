"""Audit only the five specified MOIS inputs; preserve every age and district key."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/동별예방분석-20260914/population'
DOC = ROOT / 'docs/40-분석결과/동별인구-실행결과-20260914.md'
GROUPS = [(f'{a}~{a+9}', range(a, a+10)) for a in range(0,100,10)] + [('100+', [100])]
SUPPORT = [('0~14', range(15)), ('15~64', range(15,65)), ('65+', range(65,101))]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def write_csv(name, rows):
    path = OUT / name
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with path.open(encoding='utf-8-sig', newline='') as f:
        saved = list(csv.DictReader(f))
    require(len(saved) == len(rows), f'{name}: readback count')
    return {'file': str(path.relative_to(ROOT)).replace('\\','/'), 'rows': len(saved),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    registry, single, grouped, supplementary, summary, sources = [], [], [], [], [], []
    maps = {}
    for year in range(2020,2025):
        path = ROOT / f'data/raw/인구배경/MOIS_{year}12_연령별인구_부산전체읍면동.csv'
        with path.open(encoding='cp949', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            raw = list(reader)
        expected = ['행정구역'] + [f'{year}년12월_{sex}_{label}' for sex in ['계','남','여']
                    for label in ['총인구수','연령구간인구수']+[f'{a}세' for a in range(100)]+['100세 이상']]
        require(headers == expected, f'{year}: full header mismatch')
        areas = {}
        for source_row, row in enumerate(raw,2):
            m = re.fullmatch(r'\s*(.*?)\s*\((\d{10})\)\s*',row['행정구역'])
            require(m is not None, f'{year}/{source_row}: region parse')
            name, code = m.groups()
            name = ' '.join(name.split())
            require(code.startswith('26') and code not in areas, f'{year}/{code}: code range/duplicate')
            level = 'city' if code == '2600000000' else ('district' if code.endswith('00000') else 'dong')
            require(None not in row and all(re.fullmatch(r'[\d,]+', row[h] or '') for h in headers[1:]), f'{year}/{code}: missing/noninteger')
            vals = [int(row[h].replace(',','')) for h in headers[1:]]
            for block in range(3):
                v = vals[block*103:(block+1)*103]
                require(v[0] == v[1] == sum(v[2:]), f'{year}/{code}: age total by sex')
            require(all(vals[i] == vals[103+i]+vals[206+i] for i in range(103)), f'{year}/{code}: male+female')
            areas[code] = dict(name=name, level=level, vals=vals, source_row=source_row)
        require(Counter(a['level'] for a in areas.values()) == {'city':1,'district':16,'dong':205}, f'{year}: hierarchy count')
        for code, area in areas.items():
            if area['level'] == 'dong':
                parent = code[:5]+'00000'
                require(parent in areas and area['name'].startswith(areas[parent]['name']+' '), f'{year}/{code}: parent')
            elif area['level'] == 'district':
                children = [a for c,a in areas.items() if a['level']=='dong' and c[:5]==code[:5]]
                require(all(sum(a['vals'][i] for a in children)==area['vals'][i] for i in range(309)), f'{year}/{code}: dong sum')
        require(all(sum(a['vals'][i] for a in areas.values() if a['level']=='district')==areas['2600000000']['vals'][i] for i in range(309)), f'{year}: district sum')
        for code, area in areas.items():
            parent = code[:5]+'00000' if area['level']!='city' else ''
            base = dict(year=year, population_reference_date=f'{year}-12-31', level=area['level'],
                        admin_code=code, admin_name=area['name'], district_code=parent,
                        district_name=areas[parent]['name'].removeprefix('부산광역시 ') if parent else '',
                        dong_name=area['name'].removeprefix(areas[parent]['name']+' ') if area['level']=='dong' else '',
                        population=area['vals'][0], source_file=str(path.relative_to(ROOT)).replace('\\','/'),source_row=area['source_row'])
            registry.append(base)
            ages=area['vals'][2:103]
            for label, indexes in SUPPORT:
                count=sum(ages[a] for a in indexes)
                supplementary.append(dict(base,age_group=label,age_population=count,share_pct=100*count/base['population']))
            for label, indexes in GROUPS:
                count=sum(ages[a] for a in indexes)
                grouped.append(dict(base,age_group=label,age_population=count,share_pct=100*count/base['population']))
            if area['level']=='dong':
                for age,count in enumerate(ages):
                    single.append(dict(base,age=age,age_label=f'{age}세' if age<100 else '100세 이상',age_population=count,share_pct=100*count/base['population']))
            summary.append(dict(base, **{f'age_{key}':sum(ages[a] for a in idx) for key,idx in SUPPORT},
                                **{f'share_{key}_pct':100*sum(ages[a] for a in idx)/base['population'] for key,idx in SUPPORT}))
        maps[year] = {c:a['name'] for c,a in areas.items() if a['level']=='dong'}
        sources.append(dict(year=year,file=str(path.relative_to(ROOT)).replace('\\','/'),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            bytes=path.stat().st_size,rows=len(raw),columns=len(headers),headers=headers,city_rows=1,district_rows=16,dong_rows=205,
                            all_numeric_cells_present=True,all_ages_equal_total_by_sex=True,male_plus_female_equal_total_every_age=True,
                            all_309_numeric_columns_hierarchy_reconciled=True))
    transitions=[]
    for year in range(2021,2025):
        old,new=maps[year-1],maps[year]
        transitions.append(dict(from_year=year-1,to_year=year,added=sorted(set(new)-set(old)),removed=sorted(set(old)-set(new)),
                                renamed=[dict(code=c,before=old[c],after=new[c]) for c in sorted(set(old)&set(new)) if old[c]!=new[c]]))
    outputs=[write_csv('region_registry.csv',registry),write_csv('dong_single_age.csv',single),
             write_csv('age_decade_all_levels.csv',grouped),write_csv('age_support_all_levels.csv',supplementary),write_csv('population_summary.csv',summary)]
    # Independent output partition reconciliation for every region/year and grouping.
    for filename, n in [('dong_single_age.csv',101),('age_decade_all_levels.csv',11),('age_support_all_levels.csv',3)]:
        totals, counts=Counter(),Counter()
        with (OUT/filename).open(encoding='utf-8-sig',newline='') as f:
            for r in csv.DictReader(f):
                k=(int(r['year']),r['admin_code']); totals[k]+=int(r['age_population']);counts[k]+=1
        selected=[r for r in registry if filename!='dong_single_age.csv' or r['level']=='dong']
        require(len(totals)==len(selected),f'{filename}: key coverage')
        require(all(totals[(r['year'],r['admin_code'])]==r['population'] and counts[(r['year'],r['admin_code'])]==n for r in selected),f'{filename}: saved partition')
    manifest=dict(inputs=sources,outputs=outputs,code_name_transitions=transitions,
                  validation='passed',excluded_rows=0,comparison_rows=1025,summary_only_rows=85,
                  caveat='Code/name stability is not proof of historical boundary stability; population is year-end resident background, never patient ages or annual exposure.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 동별 인구 배경 실행 결과 — 2020~2024년 12월 말','',
           '지정된 MOIS 부산 추출 원본 5개만 직접 읽었다. 기존 산출물은 입력으로 사용하지 않았다. 신고 연결 전 단계의 주민 배경이며, 인구만으로 신고 검토 후보를 선정하지 않았다.','',
           '## 입력·검증','',
           '- 파일마다 222행·310열: 시 1행, 구군 16행, 읍면동 205행이다. 비교용은 1,025 동·연도이며, 시·구군 85행은 요약·검산 전용이다.',
           '- 전 행에서 계·남·여 각각 총인구=연령구간인구=0~99세 및 100세 이상 101열 합계가 일치했다. 모든 연령 및 총계에서 계=남+여가 일치했다.',
           '- 309개 수치열 모두 동 합계=소속 구군, 구군 합계=부산시가 일치했다. 숫자 결측·지역코드 중복·부산 외 코드·제외 행은 0이다.',
           '- 출력 재읽기로 동 101연령·전체 지역 11구간·3구간의 키 수, 구간 수 및 인원 합계를 검증했다.',
           '- 구군 코드·이름과 동 코드·이름, 원본 파일·행 번호를 보존했다. CSV 코드는 문자열로 읽어야 한다.',
           '- 2020→2024 인접 연도에서 코드 추가 1개·삭제 1개가 확인됐다. 2021년 일광면(2671031000)이 2022년 파일에 없고, 일광읍(2671025900)이 새로 나타난다. 나머지 코드·명칭은 동일하다. 자동 치환하지 않았으며 공식 변경일·경계·동일 공간 여부 검증은 별도다.','',
           '## 부산시 연말 주민 구성','',
           '| 연도 | 전체 인구 | 0~14세 인원(비중) | 15~64세 인원(비중) | 65세 이상 인원(비중) |','|---|---:|---:|---:|---:|']
    for r in summary:
        if r['level']=='city':
            lines.append(f"| {r['year']} | {r['population']:,} | "+' | '.join(f"{r['age_'+k]:,} ({r['share_'+k+'_pct']:.2f}%)" for k,_ in SUPPORT)+' |')
    lines+=['','## 전체 연령 구간의 5개년 부산시 배경','',
            '각 칸은 인원(해당 연도 부산시 인구 내 비중)이다. 100세 이상은 개방 구간이다.','',
            '| 연령 구간 | 2020 | 2021 | 2022 | 2023 | 2024 |','|---|---:|---:|---:|---:|---:|']
    for label,_ in GROUPS:
        cells=[r for r in grouped if r['level']=='city' and r['age_group']==label]
        lines.append('| '+label+' | '+' | '.join(f"{r['age_population']:,} ({r['share_pct']:.2f}%)" for r in cells)+' |')
    lines+=['','## 동별 배경 분포의 5개년 범위','',
            '각 연도의 205개 읍면동을 동등한 관측 단위로 본 최솟값~최댓값이다. 합계가 아닌 분포 요약이며 연도별 극값의 동은 달라질 수 있다.','',
            '| 연도 | 동 인구 범위(명) | 0~14세 비중 범위 | 15~64세 비중 범위 | 65세 이상 비중 범위 |','|---|---:|---:|---:|---:|']
    for year in range(2020,2025):
        ys=[r for r in summary if r['year']==year and r['level']=='dong']
        cells=[f"{min(r['population'] for r in ys):,}~{max(r['population'] for r in ys):,}"]
        cells += [f"{min(r['share_'+k+'_pct'] for r in ys):.2f}~{max(r['share_'+k+'_pct'] for r in ys):.2f}%" for k,_ in SUPPORT]
        lines.append(f'| {year} | '+' | '.join(cells)+' |')
    lines+=['','## 2024년 동별 분포 사례','',
            '아래는 205개 동의 주민 배경 분포와 양 끝 사례다. 신고 위험·우선순위·돌봄 필요성의 순위가 아니다. 0~14/15~64/65+는 보조 표시이며, 모든 단일 연령과 11개 연령 구간을 별도로 보존했다.','',
            '| 항목 | 최솟값 동 | 값 | 최댓값 동 | 값 |','|---|---|---:|---|---:|']
    dongs=[r for r in summary if r['year']==2024 and r['level']=='dong']
    for key,label in [('population','전체 인구'),('age_0~14','0~14세 인원'),('share_0~14_pct','0~14세 비중'),('age_65+','65세 이상 인원'),('share_65+_pct','65세 이상 비중')]:
        lo=min(dongs,key=lambda r:r[key]); hi=max(dongs,key=lambda r:r[key]);fmt=lambda v:f'{v:,.2f}%' if 'share' in key else f'{v:,}명'
        lines.append(f"| {label} | {lo['district_name']} {lo['dong_name']} | {fmt(lo[key])} | {hi['district_name']} {hi['dong_name']} | {fmt(hi[key])} |")
    lines+=['','## 신고 분석 연결 조건과 한계','',
            '신고는 해당 연도의 연간 관측, 인구는 그해 12월 31일 기준 주민 구성이다. 관측 시점이 완전히 같지 않다. 연평균·생활인구·신고 대상자 인구로 해석하지 않으며 신고율은 계산하지 않았다. 지역 연령 구성으로 환자나 피해자의 나이, 연령별 신고 건수를 추정할 수 없다.',
            '신고와의 결합은 연도+검증된 행정동 코드로 수행해야 한다. 단순 동명 일치 또는 현재 경계의 과거 소급 적용만으로 결합 완료를 선언하지 않는다. 같은 코드의 시간 변화도 공식 경계 확인 전에는 같은 면적의 인구 변화라고 표현하지 않는다.',
            '동별 신고 연결이 검증되면 전체 연령별 인원·비중을 신고 특성과 나란히 표시한다. 현재는 신고와 인구 사이의 동반 양상이나 특정 동의 예방안을 결론 내리지 않았다.','',
            '## 재현·출력','',
            '` .venv-check/Scripts/python.exe analysis/00_공통/analyze_population_2020_2024.py `','',
            '| 출력 | 행 수 | 용도 |','|---|---:|---|']
    purposes=['계층별 코드·출처 연결','동별 0~99 및 100+ 전체 연령','시·구군·동 11연령 구간(계층 분리 필요)','시·구군·동 3연령 보조 구간(계층 분리 필요)','동·연도 결합 및 인원·비중 보조 요약']
    for output,purpose in zip(outputs,purposes):
        lines.append(f"| `{Path(output['file']).name}` | {output['rows']:,} | {purpose} |")
    lines+=['','모든 출력은 `data/processed/동별예방분석-20260914/population/`에 있다. `manifest.json`에 입력 5개 SHA-256·전체 헤더·검증 결과·출력 해시·코드 변경 점검을 기록했다. 원본의 공식 전국 자료 추출 경위는 사용자 제공 설명이며, 본 실행은 현재 부산 추출본 내부 정합성을 검증했다. 원본을 수정하지 않았다.']
    DOC.parent.mkdir(parents=True,exist_ok=True)
    DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(validation='passed',outputs=outputs,transitions=transitions,city_summary=[r for r in summary if r['level']=='city']),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
