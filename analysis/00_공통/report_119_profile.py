"""검증된 원본 교차집계에서 조건별 비교표를 생성한다."""
import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / 'data/processed/119기초분석/부산명시_연도구군종별분류처리결과.csv'
with source.open(encoding='utf-8-sig', newline='') as stream:
    rows = [r for r in csv.DictReader(stream) if r['연도'] == '2024']

def counts(column, predicate=lambda r: True):
    result = Counter()
    for row in rows:
        if predicate(row):
            result[row[column]] += int(row['접수행수'])
    return result

all_districts = counts('재난시군구')
normal_districts = counts('재난시군구', lambda r: r['처리결과'] == '정상')
results = counts('처리결과')
normal_subtypes = counts('긴급구조분류', lambda r: r['처리결과'] == '정상')
assert sum(all_districts.values()) == 272271
assert sum(normal_districts.values()) == results['정상']
table = '\n'.join(f'| {k or "미기재"} | {v:,} | {normal_districts[k]:,} |' for k,v in sorted(all_districts.items()))
processing = '\n'.join(f'| {k or "미기재"} | {v:,} |' for k,v in results.most_common())
text = f'''# 처리결과에 따른 지역 비교 — 2024년 확인표

**정상 처리된 접수만 선택해도 운영활동 기록이 남는다.** 따라서 정상 여부만으로 최종 사고 분석대상을 확정하지 않는다. 아래 표는7년 집계 중 최신2024년의 조건별 차이를 확인한 것이다. 분석기간 자체를1년으로 줄인 것이 아니다.

모집단: 재난시도명에 부산광역시가 명시된 접수272,271행. 기준 변수: 원본 재난시군구·처리결과. 동별 임의 배분이나 사고 중복 제거는 하지 않았다.

## 처리결과 구성

| 원본 처리결과 | 접수 행 |
|---|---:|
{processing}

정상 처리된 {results['정상']:,}행에도 업무운행 {normal_subtypes['업무운행']:,}행이 있다. ‘정상’은 데이터의 처리결과 값이며 실제 사고·환자 확인이나 예방활동의 필요성을 뜻하지 않는다. ‘동일신고’를 제외해도 남은 기록이 모두 서로 다른 사고라고 보장할 수 없다.

## 부산16구군과 지역 미기재

가나다순 표시이며 우선순위 순서가 아니다. 건수는 인구·유동인구·시설 규모·반복 접수의 영향을 받을 수 있어 이 표만으로 위험도나 지원 공백을 순위화하지 않는다.

| 재난시군구 | 모든 처리결과 | 처리결과 정상 |
|---|---:|---:|
{table}

지역 미기재는 모든 처리결과 {all_districts['']:,}행, 정상 처리 {normal_districts['']:,}행이다. 이를 특정 구군에 배분하지 않았다.

## 다음 분석에 적용할 기준

1. 종별과 세부분류를 함께 유지하고, 업무·훈련·확인출동 등을 원문 그대로 분리해 비교한다.
2. 포함·제외 조건을 바꿀 때 지역 구성과 건수가 얼마나 달라지는지 확인한다. 최종 대상과 효과는 이 검토 후 결정한다.
3. 구군별 인구 비교는 같은 연도·지역 정의를 확인한 뒤 별도 지표로 제공한다. 접수율을 개인의 사고확률로 해석하지 않는다.
4. 노인·아동 대상 분석은 대상별 원본·공식 집계의 연령 기준과 공간범위를 확인해야 한다. 현재 표에 대상 연령을 만들어 붙이지 않는다.

출처: data/processed/119기초분석/부산명시_연도구군종별분류처리결과.csv. 원본 출처·SHA256·포함조건·전체 집계검사는 같은 폴더의 검증_manifest.json에 기록한다. 이 CSV는2018~2024년 전체 같은 행에서 직접 교차집계한 것이다. 재현: .venv-check/Scripts/python.exe analysis/00_공통/report_119_profile.py.
'''
target = ROOT / 'docs/40-분석결과/119신고-처리조건-지역비교.md'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding='utf-8')
print('조건별 합계 검증 통과:', target.name)
