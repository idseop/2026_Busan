"""Assemble only the adopted Busan 2020-2024 analysis into one current report."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/40-분석결과'
REPORT = DOCS / '부산-119-최신작업-통합정리-20260918.md'
AUDIT = ROOT / 'data/processed/최신작업-문서통합-20260918'
POOL = ROOT / 'data/processed/5개년통합-지역유형-제안연결-20260917'
HEALTH = ROOT / 'data/processed/신고보건심화-20260917'
PROFILE = ROOT / 'data/processed/신고주민연결심화-20260917'
SOURCE_NAMES = {
    'pool': '부산-119-5개년통합-우선지역과제안연결-20260918.md',
    'health': '부산-119-신고인구에서-보건이용과-보완으로-20260917.md',
    'direction': '부산-119-방향재검토와-유형별연결-20260917.md',
    'depth': '부산-119-신고주민-논리연결-심화결과-20260917.md',
    'columns': '컬럼-사용목적과-전체결측조건-20260915.md',
    'quality': '완전행-분석적합성-평가결과-20260915.md',
    'crosswalk': '원문동-행정동-대응검증-20260915.md',
    'connection': '부산-119-구군전체에서-동별심화로-연결정리-20260917.md',
}
INPUTS = {}


def read(path):
    path = Path(path)
    data = path.read_bytes()
    INPUTS[path.relative_to(ROOT).as_posix()] = {
        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)
    }
    return data.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')


def rows(path):
    return list(csv.DictReader(read(path).splitlines()))


def link(path, label=None):
    path = Path(path)
    relative = Path(os.path.relpath(path, REPORT.parent)).as_posix()
    return f'[{label or path.name}](<{relative}>)'


def table(headers, values):
    def clean(x):
        return str(x).replace('|', '/').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(clean(x) for x in row) + ' |' for row in values])


def section(text, heading, replacement=None):
    """Copy a selected current section, excluding unrelated sibling sections."""
    start = text.index(heading)
    level = len(heading.split(' ')[0])
    match = re.search(r'\n#{1,' + str(level) + r'} ', text[start + len(heading):])
    stop = start + len(heading) + match.start() if match else len(text)
    result = text[start:stop].strip()
    return result.replace(heading, replacement, 1) if replacement else result


def chapter(number, title, text):
    return f'<a id="s{number}"></a>\n\n## {number}. {title}\n\n{text.strip()}\n'


def body(text, heading):
    return section(text, heading).split('\n', 1)[1].strip()


def main():
    AUDIT.mkdir(parents=True, exist_ok=True)
    source = {key: read(DOCS / name) for key, name in SOURCE_NAMES.items()}
    current_verification = json.loads(read(POOL / 'verification.json'))
    assert current_verification['status'] == 'PASS'
    gu = rows(POOL / '01-16구군-5년합계와-한해제외순위.csv')
    subtypes = rows(POOL / '02-전체70유형-5년합계와-한해제외순위.csv')
    focus = rows(POOL / '07-상위5구군-유형별동비교.csv')
    assert len(gu) == 16 and len(subtypes) == 70 and len(focus) == 45
    assert sum(int(x['countP']) for x in gu) == sum(int(x['countP']) for x in subtypes) == 555786

    chapters = []
    chapters.append(chapter(1, '현재 프로젝트의 목적과 확정 범위', '''
**주제: 부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안.**

이 문서는 2026년9월18일 현재 실제 채택한 결과만 묶은 통합본이다. 최종 설명의 중심은 **2020~2024년 통합 신고 → 구·군의 큰 유형 → 같은 유형이 두드러지는 동 → 주민·필요한 지역 배경 → 기존 대응 → 보완 후보와 평가**다. 2025년 신고는 제외한다. 과거의 교통 중심 사례, 사용하지 않는 제안, 구버전 페이지·시각화 목록을 본문이나 부록에 모아 넣지 않았다.

분석을 시작한 이유는 접수 건수만으로는 어느 지역에서 무엇을 예방하고 어떤 서비스를 연결할지 정할 수 없기 때문이다. 같은 구 안에서도 유형 구성·접수 시간·주민 구성·활동 배경이 다르고, 이미 운영 중인 대응도 있다. 따라서 **규모를 먼저 비교하고, 동일 유형의 동으로 좁힌 뒤, 실제 이용·운영 자료로 제안의 근거를 확인**한다.

이번 결과의 차별점은 정부가 몰랐던 문제를 발견했다는 주장이 아니라, 신고·주민·별도 조사·기존 서비스의 서로 다른 단위를 구분하면서 지역 선정과 제안의 이유를 추적할 수 있게 만든 데 있다. 건강조사나 기존 사업 자체는 정부가 이미 운영하는 자료·서비스다.

| 항목 | 현재 확정 내용 |
|---|---|
| 분석기간 | 2020-01-01~2024-12-31, 5년 통합. 연도는 반복성과 민감도 검증에 보존 |
| 기본 입력 | 선택17개 컬럼에 결측이 없는704,689접수 |
| 지역 특성의 주 분모 | 정상 처리·운영성3분류·벌집제거 제외555,786접수 |
| 비교 범위 | 16구군·194접수 동명·70개 종별×세부유형 |
| 화면/표의 기본 순서 | 같은 조건의5년 접수 건수 내림차순. 코드순·피해 위험도순과 구분 |
| 주요5구 | 부산진구·해운대구·사하구·사상구·북구 |
| 심화 범위 | 주요5구의 주요3유형×유형별 구내 상위3동명, 총45조합 |
| 현재 보완 후보 | 다대·금곡의 기존 상담→교육 예약·참여·완료 연결 시범, 시행 전 실제 누락 확인 조건 |
| 효과 상태 | 기대 경로와 평가 기준은 구체화했으나 시범 시행·건강/신고 감소 효과는 측정 전 |

날짜가 오래된 검증본이라도 현재 전처리·동 대응·상권 계산에 실제 재사용하는 근거는 유지한다. 반대로 파일명에 ‘최종’이 있어도 현재 결론에 사용하지 않는 산출물은 이 문서의 전달 목록에 넣지 않는다. 파일 자체를 일괄 삭제한 것은 아니다.
'''))

    raw = sorted((ROOT / 'data/raw/119접수').rglob('*.csv'), key=lambda p: re.search(r'20\d{2}', p.name).group())
    pop_raw = sorted((ROOT / 'data/raw/인구배경').glob('MOIS_*_연령별인구_부산전체읍면동.csv'))
    assert len(raw) == 5 and len(pop_raw) == 5
    raw_table = table(['자료', '실제 파일', '현재 용도'],
        [['119접수', link(p, p.relative_to(ROOT).as_posix()), '2020~2024 원본; 기존 전처리 근거'] for p in raw] +
        [['연말 주민', link(p, p.name), '각 연말205읍면동; 시·구 합계는 검산'] for p in pop_raw])
    chapters.append(chapter(2, '사용 데이터·기간·공간 단위', raw_table + '''

신고 CSV는 연도별 하위 폴더 안에 있다. `data/raw/119접수/` 최상위에 CSV가 없다는 이유로 원본이 없다고 판단하지 않는다. 인구 각 파일은 부산시 합계1행·구군 합계16행·읍면동205행이다. 실제 동 비교에는 읍면동 행만 사용하고 시·구 합계를 중복 합산하지 않는다.

| 보조자료 | 현재 채택 범위와 사용 목적 | 합치지 않는 범위 |
|---|---|---|
| 공식 행정동·법정동 관계 | 해당 연도 코드·명칭·유효시점으로 주민 후보 연결 | 후보코드 일치를 실제 신고 위치 확정으로 전환하지 않음 |
| 상권 | 2020~2024의20분기. 주요 구급 유형12접수 동명의 음식·소매 등 업종 구성과 분기 범위 | 업소 수를 방문객 수·위험률 분모·실제 개폐업으로 쓰지 않음 |
| 생활인구 | 2023~2024의 후보 행정동별24개월, 방문·거주·직장 시간 배경 | 2025를 현재 분석에 넣지 않음. 시간×연령의 미제공 교차표를 추정하지 않음 |
| 주택·산업 | SGIS2024 통계·2025-06-30 제공 경계. 대저·명지·송정 및 건물 관련 유형의 보조 비교 | 과거 신고를 현재 경계로 배정하거나 주택을 승강기 수로 바꾸지 않음 |
| 지역사회건강조사 | 2024 5구×32지표, 공표 그룹6,980행·전체160행. 같은5지표는3구의2023~24 30행 | 구 단위 성인 응답을 특정 동·신고자에게 전가하지 않음 |
| 공식 시설·서비스 | 다대·금곡·모라·주례·우/좌 관련 기존 센터, 질환관리·교육·방문 활동의 대상·시간·조건 | 현행 안내를2020~2024 전체기간에 동일하게 소급하지 않음 |

신고와 주민의 같은 연도 연결도 관측시점이 완전히 같은 것은 아니다. 연말 주민은 연평균·생활인구·개별 환자 분모가 아니다. 2025~2026 서비스 안내는 기존 대응의 현재 내용을 비교하는 자료로만 쓰며2025년 신고를 편입한 것이 아니다.
'''))

    column_table = body(source['columns'], '## 현재 사용하는 17개')
    chapters.append(chapter(3, '17개 컬럼과 전처리의 확정 기준', column_table + '''

소방본부 설명서 `column_info!B3:F40`의38개 정의를 대조해17개를 채택했다. 나머지21개는 시간 중복표현10개·접수종료3개·도시농촌/규모2개·여부6개다. 시간은 검증한 신고일시에서 파생하며 접수종료를 현장 도착시간으로 쓰지 않는다. 일부 여부 항목과 전부 비어 있는 중앙구조대 요청 항목을 포함하면 연도별 분석이 불가능해져 현재 질문에 필요한17개로 확정했다.

- 17개 중 하나라도 비어 있으면 **그 행을 제외**한다. 컬럼을 지우거나 결측을 채우지 않는다.
- 공란·빈 문자열은 결측으로 처리한다. `N`·정상적인0값은 의미가 확인된 값이며 자동 결측이 아니다.
- 접수번호는 접수행 점검에 쓴다. 동일 위치·시각이라는 이유만으로 중복 제거하지 않는다.
- 부산 명시 여부와 지역 미기재는 분리한다. 미기재를 부산 밖으로 확정하지 않는다.
- 두 좌표쌍은 의미가 다르므로 빈칸이 적은 쪽으로 임의 대체하지 않는다. 좌표계·위치 정확성 검증 없이 행정동에 배정하지 않는다.
- 파생 월·요일·시간은 접수시점 기준이다. 시간 문자열의 양끝 공백을 제거하고 형식을 검증했다.
- 원본·전처리·제외/미연결 기록은 분리 보존한다. 공개 결과에는 개별 접수번호·정밀 신고 위치를 넣지 않는다.

| 집합 | 포함조건 | 5년 건수 |
|---|---|---:|
| 비교집합 | 부산 명시·기존8개 값 기재, 선택 영향 진단에만 사용 | 1,334,514 |
| A | 현재17개 값 모두 기재 | 704,689 |
| B | A 중 정상 처리 | 579,412 |
| C | B 중 업무운행·훈련출동·구급차소독 제외 | 574,662 |
| P | C 중 벌집제거18,876건 제외, 현재 지역 특성의 주 분모 | 555,786 |

비교집합과 P를 합치지 않는다. P의 구성비는 항상 P 안의 해당 지역·유형 분모를 명시한다. 벌집제거는 전처리 검산에만 남기며 심층 검토와 제안에는 사용하지 않는다.
'''))

    chapters.append(chapter(4, '결측 제외 영향과 분석 가능한 범위', '''
17개 완전 기재 자료는 기존8개 비교집합의52.81%다. 추가 제외629,825행은 무작위로 빠진 것으로 검증되지 않았다. 남은 규모가 크다는 이유만으로 부산 전체를 대표한다고 보지 않는다.

| 접수경로·전체처리5년 | 비교집합 | 현재17개 집합 | 의미 |
|---|---:|---:|---|
| 일반전화 | 141,540 | 0 | 좌표 결측과 현장구군 결측이 겹쳐 제외 |
| IP전화 | 16,676 | 0 | 사고발생 좌표 결측 |
| 공중전화 | 568 | 0 | 사고발생 좌표 결측 |
| 이동전화 | 973,466 | 704,396 | 같은 이동전화 안에서도 잔존율 차이 존재 |

이동전화 잔존율은 정관읍41.53%, 기장읍94.40%, 금곡동91.37%로 달랐다. 동 이름이 사라지지 않았다는 사실은 유형 구성·건수 비교가 그대로 보존됐다는 뜻이 아니다. 일반전화가 빠진 이유를 직접 방문 신고 여부나 전화기 자체의 위치확인 불가능으로 단정하지 않는다.

현재 사용하는 검증은 **결측 전후 비교집합2개×처리조건3개×5년=30조건**이다. 각 지역을 뺀 나머지 부산 및 같은 구의 나머지 지역과 유형 구성비를 비교했다. 30/30은 비교조건 모두에서 같은 방향이라는 의미이며 독립 표본30개·유의확률·정책 효과가 아니다.

보고하는 결론은 네 범위로 구분한다: ①선택 신고 집합에서 직접 확인한 수치 ②제외 전후에도 유지되는 탐색적 구성 특징 ③조건·연도에 민감한 결과 ④전체 부산·개별 환자·확정 행정동으로 확대할 수 없는 결과. 5년 합계는 표본 선택의 문제를 해결하지 않는다. 동×유형×시간의 결측 제외 전 안정성까지 확인했다고 주장하지 않는다.
'''))

    chapters.append(chapter(5, '동 대응과 주민 연결의 상태', '''
분석 단위는16개 구·군과194개 접수 동명이다. 주민 원자료는각 연말205개 행정동이며 두 수가 다른 이유는 원문 명칭과 행정동의 체계가 다르기 때문이다. 194개를205개 행정동에 그대로 배정하지 않는다.

공식 KIKcd_H(행정기관), KIKcd_B(법정동), KIKmix(관계)와 시점별 원본을 대조했다. 두 이름 가설의 후보를 함께 검토해 단일 후보·다중 후보·시점 불일치·미등록·위치 미확인을 구분한다. 주민 후보를 인구 비례로 나눠 신고를 배분하지 않는다.

- 2020~2024 연말 행정동 코드205개는 각 연도 MOIS 인구 코드와 일치했다.
- 연지동→부암제1동 관계는2020 원본과 후행 이력 복원에 차이가 있어 해당 시점 불확실성을 유지한다.
- 194동명×5년970조합 중 후보 없는9조합을 별도로 남겼다. 3조합은그해 P접수0건, 나머지6조합에는46접수가 있다.
- 2022 일광면은 후보가 있어도 그 후보코드의 연말 주민값이 없어 빈 상태를 유지한다.
- 부전·다대·우·좌·모라·주례 등의 복수 주민 후보는 개별로 표시한다. 미연결을 인구0명·신고0건으로 바꾸지 않는다.
- 지도용 현재 경계·대표점이 있어도 과거 신고의 위치 정확도가 높아지는 것은 아니다. 당시 경계·좌표의 검증이 필요한 행정동별 확정 배정은 완료로 표시하지 않는다.

전체101연령 인원·비중을 유지하고, 본문은 읽기 편하게0~14·15~39·40~64·65세 이상으로 묶는다. 인구 비교는 안내의 적합성과 서비스 이용조건을 검토하는 배경이며 신고자·환자의 나이 분포가 아니다.
'''))

    pool_overview = body(source['pool'], '## 3. 부산 전체에서 좁힌 상위 구·군')
    pool_all = body(source['pool'], '## 9. 전체16구와 나머지 유형의 위치')
    yearly_a = [114236, 139189, 158478, 149390, 143396]
    yearly_b = [100073, 113965, 127241, 121311, 116822]
    yearly_c = [99661, 113037, 126252, 120187, 115525]
    annual_rows = [[year, f'{yearly_a[i]:,}', f'{yearly_b[i]:,}', f'{yearly_c[i]:,}',
                    f"{sum(int(r[str(year)]) for r in gu):,}"] for i, year in enumerate(range(2020, 2025))]
    annual_table = table(['연도', 'A 전체처리', 'B 정상', 'C 운영성 제외', 'P 벌집제거까지 제외'], annual_rows)
    chapters.append(chapter(6, '5년 통합 결과와 전체16구·군의 순서', '''
건수는5년의 같은 지역·유형을 합산하고 구성비는5년 분자합계/분모합계로 계산했다. 연도별 비중이나 순위를 평균하지 않는다. 한 해를 제외한4년 합계5개를 추가 비교해 특정 연도에 대한 의존성을 확인했다. 이는 미래 예측이나 신뢰구간 추정이 아니다.

''' + pool_overview + '\n\n' + pool_all + '\n\n### 통합 합계의 연도별 검산\n\n'
        + annual_table + '\n\n주된 설명은5년 통합 결과이며 위 연도표는 누적 합계·반복성·기간 민감도를 확인하기 위해 유지한다.'))
    chapters.append(chapter(7, '같은 신고 유형을 따라 동으로 좁힌 핵심 결과', body(source['pool'], '## 4. 같은 신고 유형을 따라 동으로 좁힌 결과')))
    chapters.append(chapter(8, '월·요일·시간과 반복성', body(source['pool'], '## 5. 부족했던 시간 분석도 45조합 전체로 확대') + '''

추가로 연도별 반복을 보면 부전 부상의20~24시 정점은2/5년, 질병외는3/5년이다. 따라서 통합 정점을 매년 불변의 야간 정점으로 쓰지 않는다. 다대·금곡 질병의08~12시 정점은 기존 연도별 검토에서5/5년이었다. 월 최다값과 달력 일수당 최다값, 4시간·6시간 정점은 각각의 지표로 보존한다.
'''))
    chapters.append(chapter(9, '주민 전체 연령 구성과 해석', body(source['pool'], '## 6. 주민과 지역 배경을 함께 읽는 결과')))

    chapters.append(chapter(10, '상권·생활인구를 실제로 사용한 부분', '''
상권은 예시로만 언급한 것이 아니라 실제20분기 전체를 분석했다. 현재 큰 구급3유형의 상위10 합집합12접수 동명에 검증된 법정동 업종 구성을 연결했고, 생활인구는 후보 행정동별2023~2024 자료로 연결했다. 아래는 현재 부전 질병외·부상 설명에 쓰는 결과다.

| 지표 | 실제 결과 | 설명에 기여하는 내용 |
|---|---|---|
| 부전 법정동2024년12월 상권 | 7,064업소; 음식2,317(32.80%)·소매2,162(30.61%) | 주민 외 방문·활동 배경을 별도로 살필 이유 |
| 부전20분기 업종 비중 | 음식32.66~34.52%, 소매30.61~32.68% | 한 분기의 우연한 수치로만 설명하지 않음 |
| 부전1동 후보 방문 정점 | 2023·2024 모두14시 | 후보별 활동 시각이 다름 |
| 부전2동 후보 방문 정점 | 2023·2024 모두19시 | 부전 전체를 하나의 생활곡선으로 합치지 않음 |
| 부전 부상 통합 시간 | 20:00~다음08:00 직전55.09%; 최다4시간대20~24시 | 밤 접수 특성과 활동 배경을 나란히 제시하되 원인으로 단정하지 않음 |

상권20분기는 관측된 코드·명칭 사전을 대조하고 동일분기 연도 비교와 분기별 비중 범위를 계산한 자료다. 업소ID의 출현·소멸은 실제 개업·폐업이 아니다. 법정동 전체 업소를 특정 시장이나 사고 구간의 업소로 표시하지 않는다.

생활인구는 제공된 월별 추정값이며2023~2024 공통205동·24개월이다. 연간 곡선은12개월 동일가중 평균이며 관측월 수를 보존한다. 서로 다른 인구유형·24시간을 합쳐 고유인원으로 만들지 않고, 별도 시간·연령 파일을 교차해 없는 정보를 생성하지 않는다. 공식 산정 기준과 신고시점이 완전히 같다고 보지 않는다.

**현재 연결의 결론:** 부전에는 주민 배경만으로 설명되지 않는 활동 차이가 있다. 그러나 음식점·소매점이 많다는 사실은 음주·낙상·상점 사고의 직접 증거가 아니다. 특정 원인 예방안을 정하려면 실제 사고 기전·발생장소 자료가 추가되어야 한다. 질병 신고를 설명하는 모든 지역에 상권을 같은 설명변수로 붙이지 않는다.
'''))

    health_methods = body(source['health'], '## 4. 새 자료와 계산 기준')
    health_results = body(source['health'], '## 5. 추가 분석 결과')
    chapters.append(chapter(11, '보건 이용·교육 경험으로 더한 독립 근거', health_methods + '\n\n' + health_results))
    chapters.append(chapter(12, '지역별 기존 서비스와 실제 확인 내용', body(source['pool'], '## 7. 기존 대응을 대조하면서 수정한 제안 방향') + '\n\n' + body(source['health'], '## 6. 기존 서비스 대조에서 실제로 바로잡은 내용')))
    chapters.append(chapter(13, '현재 채택한 보완 후보와 평가 설계', body(source['health'], '## 7. 보완 후보를 실제 실행·평가 수준으로 구체화') + '\n\n' + body(source['health'], '## 8. 기대효과와 실제 평가 기준')))

    chapters.append(chapter(14, '다른 신고 특성에 사용하는 보조 비교', '''
상위5구의 큰 구급 유형이 주 설명 순서다. 전체70유형을 버리지 않으므로 같은 분류를 따라 추가 설명할 수 있는 아래 비교도 유지한다. 이는 기존의 교통 중심 프로젝트로 돌아가는 것이 아니며, 작은 현장 분기를 주 결과보다 앞에 두지 않는다.

''' + body(source['direction'], '## 7. 주택·사업체는 언제 쓰는가: 다른 신고 특성의 별도 분기') + '\n\n' + body(source['depth'], '## 5. 강서: 주민 구성만으로 설명할 수 없는 주택·사업장 차이') + '''

금곡↔화명은 같은 북구·구급의 비교로 유지한다. 금곡 구급8,425/9,293=90.66%, 화명7,536/8,548=88.16%다. 부산 나머지 대비는 둘 다30/30이나 구내 비교에서는 금곡30/30·화명13/30이다. 질병/지역 전체는38.90%·35.90%, 질병/구급만은42.91%·40.72%다. 같은 구급이라도 분모와 지역 내 특성을 구분할 이유다.

금곡의 질병은 통합08~12시, 화명은20~24시 정점으로 시간·주민 배경이 다르다. 기존 건강센터·조건에 맞는 방문관리·안심콜 등록/갱신은 서로 다른 서비스다. 이 비교만으로 야간 센터 연장이나 고령층 전용 돌봄이 필요하다고 결론 내리지 않는다.
'''))

    chapters.append(chapter(15, '확인한 필요·남은 공백·효과의 범위', body(source['health'], '## 9. 실제 공백·자료 공백·확정하지 않은 결론') + '''

| 현재 남은 판단 | 필요한 최소 자료 | 판단이 달라지는 조건 |
|---|---|---|
| 다대·금곡 교육 연결 누락 | 적격·희망자·예약·참여·완료·미참여 사유, 거주동·질환·관측기간 | 이미 충분히 연결되면 중복 시범을 도입하지 않음 |
| 부전 질병외·부상의 예방 내용 | 실제 사고 기전·장소·시각·환자/출동 단위, 공식 정의 | 음주·낙상·도로·상점 중 무엇인지 검증된 뒤 해당 대응만 대조 |
| 우·좌·모라·주례의 지역별 미이용 | 해당 지역 서비스 참여·완료·이용장벽 자료 | 구 전체 서비스 존재를 개별 주민 충족으로 바꾸지 않음 |
| 특정 센터의 출동 여력 | 해당 기간 전체 기관·관할·가용대원/차량·동시출동·도착시간 | 지도 표시센터 수를 분모로 시설 부족을 정하지 않음 |
| 확정 행정동의 과거 신고 | 당시 경계·주소/좌표 정의·위치 검증 | 후보 관계와 실제 공간 배정이 확인되는 범위만 확장 |
| 제안의 건강·사고 감소 효과 | 실제 시행·비교군/기간·추적·노출·변경 이력 | 참여 개선과 별도로 충분한 설계가 있을 때만 평가 |

현재 직접 기대하는 변화는 기존 상담에서 필요한 교육 참여로 이어지는 비율과 이행 확인 가능성이다. 기대 경로가 타당하다는 설명, 실제 서비스 부족의 입증, 시행 후 효과 추정은 서로 다른 단계다. ‘현재 확정한 지역별 대응 공백’이나 ‘정부가 미조치했다’는 문장으로 자료 공백을 바꾸지 않는다.
'''))

    read(ROOT / 'web/final/README.md')
    read(ROOT / 'web/final/serve.py')
    chapters.append(chapter(16, '현재 웹의 위치와 최신 분석 반영 상태', '''
웹은 분석의 근거를 대신하는 것이 아니라 검증된 결과를 탐색하는 전달물이다. 현재 `web/final/`에는 부산 한정 지도와 `analysis/`의 최신 결과 페이지를 연결했다.

**최신 웹 반영 완료:** 5년 통합·상위5구45조합·주민 전체 연령·보건 연결·기존 대응·조건부 시범안을 지도와 결과 페이지에 반영했다. 원격 `develop`의222159a까지5개 커밋을 검토했다.247ad91까지의3개 기능과,4bcb9e3의두 구 분석·PDF 공유,222159a의연도 필터·상세 헤더 간소화·캐시 방지까지 연결했다. cfbdbe7의비교 집계·12그림은4bcb9e3의공유본과 바이트가 같은 것을 git diff로 확인했다. 작업 중인 로컬 분석은 덮어쓰지 않고 원격 스냅샷의 필요한 기능·자료만 연결했다. 주 분석9종과 원격 부산진구·중구 비교12종은 탭으로 구분한다.

| 구성 | 현재 상태 | 최신 결과에 맞춘 연결 기준 |
|---|---|---|
| 지도 기반 | PC, 부산 한정 탐색·구군 강조·상세 패널 갱신 | 16구군 P555,786건·5년 합계 건수순; 연도·종별·70종별×세부유형 필터 |
| 동 선택 | 위치 미확정 명칭은 소속 구군 강조 | 임의의 동 경계·신고 지점 생성 금지 |
| 주민 | 후보별 전체 연령과 기준연도 | 신고 필터가 주민 수를 바꾸지 않게 처리 |
| 기관 표시 | 원격 제공 자료91행·68좌표 위치, 팝업·전환 | 기준일 미기재 인원·차량은 현재 가용량이 아님; 소재지로 관할·접근성 확정 금지 |
| 분석 이야기 | 전체→구군→동→기존서비스→다대·금곡 조건부 보완으로 연결 | 현재 신고 패턴과 실제 서비스 부족의 입증은 구분 |
| 지도 조작 | 최신 develop에 맞춰 일반지도·접수 비중, 연도 필터는 왼쪽 | 실시간 상황·개별 신고 건물·새 위치 정확성을 뜻하지 않음 |

PC1920×1080·1600×900·1366×768 브라우저로 수치·필터·검색·동 선택·인구 후보·뒤로가기·시설 팝업·일반지도/접수 비중·네트워크 실패를 실행 검증했다. 원격 C집계574,662건은16구 모두 기존 동일 조건과 일치하며, 주 분석과의18,876건 차이는 벌집제거다. 구급/구조 양쪽의 ‘교통사고’는 서로 다른 유형이므로 필터에서 구분한다. 코드와 검증은 `scripts/build_current_web_20260918.py`, `scripts/verify_current_web_20260918.py`, `data/processed/최신웹연결-20260918/`에 있다.

프로젝트 루트에서 PC 로컬 서버를 여는 방법:

```powershell
.venv-check/Scripts/python.exe web/final/serve.py --port 8765
```

지도: `http://127.0.0.1:8765/`, 분석 결과·시각화: `http://127.0.0.1:8765/analysis/`. 로컬 서버에서 검증한 주소이며 인터넷 공개 배포나 원격 푸시 완료를 뜻하지 않는다. 온라인 배경지도는 네트워크에 의존하고 지도 제공자·라이선스·출처 표시는 README와 화면에 유지한다.
'''))

    figure_specs = [
        ('주 흐름1', '전체16구의5년 규모·유형', ROOT/'figures/5개년통합-지역유형-제안연결-20260917/01-5년통합-지역규모와유형.png'),
        ('주 흐름2', '같은 유형의 동별 요일×시간', ROOT/'figures/5개년통합-지역유형-제안연결-20260917/02-지역유형별-5년통합시간.png'),
        ('주 흐름3', '구 단위 실제 의료 이용 경험', ROOT/'figures/신고보건심화-20260917/01-의료이용-추가근거.png'),
        ('주 흐름4', '기존 치료와 관리교육의 다른 지표', ROOT/'figures/신고보건심화-20260917/02-기존치료와-관리교육.png'),
        ('주 흐름5', '같은 보건 지표의 두 해 비교', ROOT/'figures/신고보건심화-20260917/03-두해-보건지표-검토.png'),
        ('비교 근거', '같은 구 내부 비교에 따른 판단', ROOT/'figures/신고주민연결심화-20260917/01-비교범위에따른-지역선정.png'),
        ('비교 근거', '금곡↔화명 시간과 전체 연령', ROOT/'figures/신고주민연결심화-20260917/02-금곡화명-신고시간과주민구성.png'),
        ('대상물 분기', '강서 주택·산업의 차이', ROOT/'figures/신고주민연결심화-20260917/03-강서-주택과산업배경.png'),
        ('선정 근거', '큰3유형 안에서 지역을 좁히는 근거', ROOT/'figures/신고주민연결심화-20260917/방향재검토/01-큰신고유형에서-지역선정.png'),
    ]
    frows = []
    for role, desc, path in figure_specs:
        assert path.exists() and path.with_suffix('.svg').exists()
        for p in [path, path.with_suffix('.svg')]:
            data = p.read_bytes()
            INPUTS[p.relative_to(ROOT).as_posix()] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
        frows.append([role, desc, link(path, 'PNG')+' · '+link(path.with_suffix('.svg'), 'SVG')])
    chapters.append(chapter(17, '지금 사용하는 시각화와 설명 순서', '''
현재 설명에 사용하는 그림은 **9종(PNG·SVG 각9개)**이다. 이전 그림 전체를 다시 나열하지 않고 주 흐름5종과 비교·선정 근거4종으로 구분했다. 그림 수는 분석의 깊이나 정책 효과를 뜻하지 않는다.

''' + table(['역할', '보여주는 결과', '파일'], frows) + '''

발표·서류에서는 먼저 구군 규모, 같은 유형의 동과 시간, 주민 배경, 독립 보건 근거, 기존 대응, 조건부 보완과 평가 순서로 설명한다. 필요할 때만 구내 비교·대상물 분기를 추가한다. 건수·구성비·달력 일수당 값·조사 가중 비율을 같은 축의 위험 지표로 합치지 않는다.
'''))

    proof_files = [
        POOL/'verification.json', POOL/'delivery-verification.json',
        ROOT/'data/processed/구군에서동심화연결-20260917/verification.json',
        PROFILE/'direction-verification/validation.json', PROFILE/'direction-verification/delivery-validation.json',
        PROFILE/'verification/validation.json', PROFILE/'verification/additional-validation.json',
        HEALTH/'verification/verification.json', HEALTH/'verification/final-review.json',
        ROOT/'data/processed/신고인구특성재정립-20260917/independent-verification/validation.json',
    ]
    proofs = []
    for path in proof_files:
        result = json.loads(read(path))
        if result.get('status') is not None:
            status = str(result['status'])
        elif result.get('passed') is True:
            status = 'PASS（passed=true）'
        else:
            status = '개별 검사 결과 기록'
        proofs.append([link(path, path.relative_to(ROOT/'data/processed').as_posix()), status])
    chapters.append(chapter(18, '검증 결과와 이번 정리의 검증 범위', '''
최신5년 통합 분석은 입력13개의 현재 SHA-256과 기존 명세를 대조했다. 별도 검산 코드는 작성 코드를 가져다 쓰지 않고 `csv/collections`로 구군·유형·동 합계와 동률 순위를 재계산했다. 시간 집계는 전처리5파일에서 별도 계산해18,990셀·540요약을 대조했다. 상위5구45조합, 주민195후보연말 행의 전체101연령 합계와 중복 키를 확인했다.

신고주민 비교의 기존 검산은 비교셀146,448개·시간셀142,213개·SGIS9,456셀을 대조하고, 비공표/비수치376셀을 유지했다. 추가 직접비교·시간조건·공식서비스 점검과 보건조사의 공표표·분모·SE 점검도 해당 검증기록으로 이어진다. 검사 개수를 표본 수나 통계적 신뢰도 점수로 사용하지 않는다.

''' + table(['현재 사용하는 검증 기록', '저장된 상태'], proofs) + '''

이번 통합 문서 작성은 검증된 CSV를 재사용하고 해시·링크·70유형/45조합·구군 순서를 검산한다. 이후 최신 웹 연결 작업에서 별도 검증 코드로 공개 집계를 대조하고 실제 PC 브라우저 검사를 새로 실행했다. 결과는 `data/processed/최신웹연결-20260918/verification.json`이며, 과거 웹 검사 PASS를 재표기한 것이 아니다.
'''))

    code_groups = {
        '전처리·코드북·동 대응': [
            'analysis/00_공통/complete_all_selected_20260915.py',
            'analysis/00_공통/audit_codebook_selection_20260915.py',
            'analysis/00_공통/validate_dong_crosswalk_20260915.py',
            'analysis/00_공통/assess_complete17_missingness_20260915.py',
            'analysis/00_공통/assess_complete17_stability_20260915.py'],
        '전체 신고·주민·유형 연결': [
            'analysis/00_공통/analyze_full_call_profiles_20260917.py',
            'analysis/00_공통/analyze_population_profiles_20260917.py',
            'analysis/00_공통/analyze_profile_depth_20260917.py',
            'analysis/00_공통/analyze_profile_context_20260917.py',
            'analysis/00_공통/reassess_profile_direction_20260917.py',
            'analysis/00_공통/connect_reassessed_profiles_20260917.py',
            'analysis/00_공통/verify_reassessed_profiles_20260917.py',
            'scripts/write_district_dong_connection_20260917.py',
            'scripts/verify_district_dong_connection_20260917.py'],
        '보건자료 수집·분석·검산': [
            'scripts/collect_chs_followup_20260917.py',
            'scripts/collect_health_service_sources_20260917.py',
            'analysis/00_공통/analyze_health_followup_20260917.py',
            'analysis/00_공통/verify_health_followup_20260917.py',
            'scripts/write_health_followup_report_20260917.py'],
        '5년 통합·그림·보고서': [
            'analysis/00_공통/analyze_pooled_five_years_20260917.py',
            'analysis/00_공통/verify_pooled_five_years_20260917.py',
            'scripts/write_pooled_five_year_report_20260918.py',
            'scripts/plot_profile_depth_20260917.py',
            'scripts/write_current_project_report_20260918.py',
            'scripts/verify_current_project_report_20260918.py'],
    }
    code_rows = []
    for role, files in code_groups.items():
        for filename in files:
            p = ROOT / filename
            read(p)
            code_rows.append([role, link(p, filename)])
    chapters.append(chapter(19, '재현 코드와 실행 순서', '''
기존 검증 전처리·집계가 보존된 상태에서 최신 통합 결과를 재생성하는 순서다. 수집 코드를 매번 다시 실행하면 공식 페이지가 달라질 수 있으므로, 보존된 입력으로 재현하는 작업과 최신 자료를 다시 받는 작업을 구분한다.

```powershell
$env:PYTHONUTF8='1'
.venv-check/Scripts/python.exe analysis/00_공통/analyze_pooled_five_years_20260917.py
.venv-check/Scripts/python.exe analysis/00_공통/verify_pooled_five_years_20260917.py
.venv-check/Scripts/python.exe scripts/write_pooled_five_year_report_20260918.py
.venv-check/Scripts/python.exe scripts/write_current_project_report_20260918.py
.venv-check/Scripts/python.exe scripts/verify_current_project_report_20260918.py
```

분석은 pandas·numpy·matplotlib, 검산은 Python 표준 라이브러리를 사용한다. 보건 원표는 openpyxl, SGIS의 기존 처리에는 pyshp/lxml 등이 쓰인다. 한글 그림은 Windows 맑은 고딕 기준이다. 현재 환경·입력 해시는 각 분석 명세를 따른다.

''' + table(['역할', '코드'], code_rows)))

    csv_roots = [POOL, HEALTH, PROFILE/'direction-reassessment', PROFILE/'direction-connections',
                 PROFILE/'analysis', PROFILE/'context', PROFILE/'services',
                 ROOT/'data/processed/구군에서동심화연결-20260917',
                 ROOT/'data/processed/신고인구특성재정립-20260917/calls',
                 ROOT/'data/processed/신고인구특성재정립-20260917/population',
                 ROOT/'data/processed/신고인구특성재정립-20260917/tables']
    data_rows = []
    for folder in csv_roots:
        for path in sorted(folder.glob('*.csv')):
            records = rows(path)
            data_rows.append([link(path, path.relative_to(ROOT/'data/processed').as_posix()), f'{len(records):,}', len(records[0]) if records else 0])
    chapters.append(chapter(20, '현재 사용하는 전체 집계표와 자료 연결', '''
본문의 작은 표만 결과의 전부는 아니다. 현재 단계에서 사용하는 집계표를 아래에 연결했다.13,580동명×유형 행·407,400비교셀·전체 연령 자료를 MD에 가로로 펼치지 않고 CSV에서 그대로 확인하게 한다. 조사 응답·업소·주민·접수의 서로 다른 분모는 합산하지 않는다. 시간표가 일부 사례만 있는 선행 표와45조합을 모두 채운 최신 시간표의 범위를 구분한다.

''' + table(['집계표', '행', '열'], data_rows) + '''

상권·생활인구의 기초 집계는 날짜가2026-09-16인 폴더에서도 현재 실제 재사용하는 파일이 있다. 해당 파일은 구버전 결론이 아니라 검증된 입력이다. 현재 `direction-connections/manifest.json`에 재사용 경로·해시가 명시되어 있다. 주민·보건·공식서비스 원본과 URL·확보일·원문 표 위치도 각 아래 명세로 추적한다.
'''))

    subtype_rows = [[r['pooledCountRank'] or '—',r['type'],r['subtype'],f"{int(r['countP']):,}",f"{float(r['citySharePct']):.3f}%"] for r in subtypes]
    chapters.append(chapter(21, '전체70개 신고 유형의 통합 결과', '''
분모는 P555,786접수다. 같은 세부명이라도 종별이 다르면 별도 유형이며0건도 보존한다. 이 표를 모든 유형에 같은 예방안이 필요하다는 뜻으로 사용하지 않는다.

''' + table(['건수순', '종별', '세부유형', '5년 건수', 'P전체 비중'], subtype_rows)))

    focus_rows = []
    for r in focus:
        band='/'.join(f'{int(x)*4:02d}~{int(x)*4+4:02d}' for x in r['hour4Peak'].split('|'))
        focus_rows.append([r['district'],r['rawDong'],r['subtype'],f"{int(r['countP']):,}",
            f"{float(r['shareRegionPct']):.2f}%",r['withinDistrict_pooledCountRank'],
            f"{r['aboveRestBusan30']}/30 · {r['aboveRestDistrict30']}/30",band,
            f"{float(r['night20to07Pct']):.2f}%"])
    chapters.append(chapter(22, '상위5구45개 지역·유형 조합의 상세 결과', '''
구의 총건수 순서를 고정하고 그 안의 주요유형·같은유형 동별 건수순으로 제시한다. 구성비는 해당 접수 동명의 P전체가 분모다. 우세 조건은 부산 나머지·같은 구 나머지 순이다. 야간은20:00~다음08:00 직전12시간이며 해당 동명·유형의 P접수가 분모다. 통합 최다시각이 매년 같다는 의미는 아니다.

''' + table(['구군','접수 동명','유형','5년 접수','동명 내 비중','구내 동일유형 건수순','구성비 우세 조건','최다4시간대','야간 비중'],focus_rows)))

    manifests = [POOL/'manifest.json', POOL/'report-delivery.json',
                 HEALTH/'analysis-specification.json', HEALTH/'delivery-manifest.json',
                 HEALTH/'sources/chs-download-manifest.json', HEALTH/'sources/chs2023-download-manifest.json',
                 HEALTH/'sources/service-source-manifest.json',
                 PROFILE/'direction-reassessment/manifest.json', PROFILE/'direction-connections/manifest.json',
                 PROFILE/'context/manifest.json', PROFILE/'services/manifest.json']
    manifests += sorted((POOL/'sources').glob('*.json'))
    manifest_rows=[]
    for p in manifests:
        read(p)
        manifest_rows.append([link(p,p.relative_to(ROOT/'data/processed').as_posix()),INPUTS[p.relative_to(ROOT).as_posix()]['sha256']])
    doc_rows = [[link(DOCS/name,name),INPUTS[(DOCS/name).relative_to(ROOT).as_posix()]['sha256']] for name in SOURCE_NAMES.values()]
    chapters.append(chapter(23, '출처·입력 명세와 현재 문서의 검증', '''
다음은 이번 통합에 실제 사용한 근거 문서와 입력 명세다. 전체 옛 문서 목록이나 이전 페이지를 붙인 기록보관용 부록이 아니다. 본문의 주요 결과·자료 해석·조건부 제안은 이 통합 MD에서 읽을 수 있고, 링크는 원표·공식 출처·재현 경로를 추적하는 용도다. 공식 외부 자료를 이번 문서 작업에서 다시 수집한 것으로 표시하지 않는다.

''' + table(['현재 근거 문서','통합 시점 SHA-256'],doc_rows) + '\n\n' + table(['입력·공식원본·출력 명세','통합 시점 SHA-256'],manifest_rows) + '''

이번 문서의 생성 명세와 별도 검증은 `data/processed/최신작업-문서통합-20260918/`에 기록한다. 검증된 분석 원본·CSV·시각화는 보존하고 최신 내용을 웹과 문서에 연결했다. 프로젝트 계획도 현재 방향과 웹 완료 상태에 맞춰 갱신했다.

**현재 완료한 것:** 5년 통합 통계, 구군→동의 동일유형 연결, 전체 연령 주민·활동 배경, 독립 보건 근거, 기존 대응 대조, 두 조건부 보완안과 평가 설계, 분석 검산, 최신 결과의 단일 문서화, develop·최신 비교 브랜치 검토 및 두 웹페이지 연결·PC 실행 검증.

**아직 완료하지 않은 것:** 동별 실제 교육 연결 누락의 입증, 부전 사고 기전·장소 연결, 개별 환자·확정 과거 행정동 배정, 보완안 시행·인과 효과, 인터넷 공개 배포.
'''))

    toc = '\n'.join(f'- [{re.search(r"## (.+)", c).group(1)}](#s{i})' for i,c in enumerate(chapters,1))
    result = '# 부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안 — 최신 작업 통합 정리\n\n'
    result += '**기준일: 2026-09-18 · 신고기간: 2020~2024 통합 · 현재 채택한 내용만 수록**\n\n'
    result += '설명·제안의 근거를 중심으로 현재 결과, 데이터, 방법, 시각화, 코드, 검증, 미완료 범위를 한 문서에 연결한다.\n\n'
    result += toc+'\n\n---\n\n'+'\n\n'.join(chapters)
    result = re.sub(r'(?m)^(#{3,6})\s+\d+(?:\.\d+)*\.?\s+', r'\1 ', result)
    REPORT.write_text(result,encoding='utf-8',newline='\n')
    plan = ROOT / 'docs/10-작업계획/부산 분석 작업 계획.md'
    plan.write_text('''# 부산 분석 작업 계획 — 현재 채택한 방향과 완료 상태

기준일: **2026-09-18**. 신고기간: **2020~2024년 통합**.

현재 결과·근거·방법·출처·코드·검증·남은 작업의 전체 설명은 [최신 작업 통합 정리](../40-분석결과/부산-119-최신작업-통합정리-20260918.md)를 기준으로 한다. 이 계획에는 현재 실행 방향만 남겼다. 이전 교통 중심 계획·사용하지 않는 사례·구버전 산출물 목록은 현재 계획에서 제외했다.

## 1. 목적과 분석 흐름

주제는 **부산 동별 119 신고 특성에 따른 맞춤형 예방안 제안**이다. 설명과 제안을 할 수 있도록 다음 순서로 좁힌다.

> 부산 전체의 큰 신고 유형 → 구·군의 같은 조건 접수 규모 → 같은 유형의 동별 규모·구성·반복 → 주민 전체 연령 → 해당 유형에 필요한 활동·건물·보건 등 추가 근거 → 기존 대응 → 근거가 연결된 보완 후보와 평가

처음부터 특정 동·인력·시설·돌봄을 해결책으로 정하지 않는다. 구의 신고 유형을 동에서 다른 유형으로 바꾸지 않는다. 접수 건수는 사건·출동·환자·피해 심각성과 구분한다.

## 2. 입력과 고정 조건

- 2025년 신고는 사용자 결정으로 제외한다. 추가 확보를 분석의 조건으로 두지 않는다.
- 신고는 `data/raw/119접수/` 하위 폴더의2020~2024 CSV5개다. 루트 중복본·2018~2019·미채택 이전 분석을 현재 입력으로 섞지 않는다.
- 인구는 `data/raw/인구배경/`의같은5개 연말 MOIS다. 매년205읍면동과101연령을 유지하고 시·구 합계는 검산에만 쓴다.
- 소방본부38컬럼 설명서를 확인해 선택한17개는 모두 유지한다. 하나라도 결측이면 해당 행을 제외하며 값 대체·컬럼 삭제로 바꾸지 않는다.
- A704,689건 → 정상 B579,412건 → 운영성3분류 제외 C574,662건 → 벌집제거 제외 P555,786건. P가 현재 지역 특성의 주 분모다.
- 같은 지역·유형의5년 건수를 합산하고 구성비는 합산 분자/분모로 계산한다. 주민5개 연말을 합치거나 인구 대비 신고율을 자동 계산하지 않는다.
- 벌집제거는 검산 외의 심화·조사·제안에서 제외한다.

## 3. 현재 완료한 분석과 판단

| 단계 | 완료 결과 | 해석 기준 |
|---|---|---|
| 전체 유형 | 16구군·194접수 동명·70유형. 질병·질병외·부상422,067건, P의75.94% | 큰 유형을 중심으로, 다른 유형은 별도 분기 유지 |
| 구군 순서 | 부산진64,059·해운대56,927·사하48,076·사상41,747·북41,205건 | 건수 내림차순. 한 해씩 제외한5개 비교에서도 상위5 순서 유지 |
| 같은 유형의 동 | 16구 주요유형141조합, 상위5구45조합; 부전 질병외/부상, 우/좌·다대·모라/주례·금곡 질병 | 구군 총량순·동일유형 건수순·구성비를 구분. 질병/질병외 선두는 기간 민감 |
| 선택·처리 민감도 | 결측 전후×처리3조건×5년30조건, 부산 나머지/같은 구 나머지 비교 | 30/30은 독립 검정·위험 점수 아님 |
| 시간 | 45조합의540요약·18,990통합 교차셀 | 부전20~24시, 다대·금곡 등 질병08~12시. 연도별 반복은 별도 확인 |
| 주민 | 상위5구의15접수 동명 후보195연말 행·101연령 | 복수 후보 개별, 신고자 나이로 해석하지 않음 |
| 활동·대상물 | 부전 등 상권20분기·생활인구2023~24, 강서 등의주택·사업체 배경 | 질병·부상·대상물 관련 유형에 필요한 자료만 사용 |
| 보건 | 2024 5구32지표·공표6,980행·전체160행;3구 동일5지표2023~24 30행 | 구 성인 조사와 동 신고 분모 분리, 공표SE 유지 |
| 기존 대응 | 다대·금곡·모라/주례·해운대 등의센터·등록관리·교육·방문 활동 | 자료 없음과 서비스 없음 구분, 실제 운영 시점 명시 |
| 보완 | 다대·금곡 상담→교육 예약·참여·완료 연결 시범, 시행 조건·평가·중단 기준 | 아직 시행하지 않았으며119 감소 효과는 미측정 |

## 4. 설명과 제안의 범위

완전 기재 자료는 일반·IP·공중전화가 제외되고 이동전화 내부도 지역별 잔존율이 달라 전체 부산의 대표성이 검증되지 않았다. 이름이 남았다는 이유로 동별 정보가 온전히 보존됐다고 보지 않는다.

공식 코드 후보와 실제 신고 위치는 다르다. 당시 경계·위치가 검증되지 않은 동은 임의 배정하지 않고 주민 후보를 인구 비례로 합치지 않는다. 지도는 검증된 구군만 강조하며 정밀 배경을 신고 정확성의 증거로 쓰지 않는다.

다대·금곡의 현재 제안은 새 시설이나 문자 신설이 아니다. 기존 상담에서 필요한 교육 참여로 연결하는 절차를 점검하는 조건부 시범이다. 실제 적격·희망자·예약·참여·완료·미참여 사유를 먼저 확인하고, 기존 절차가 충분하면 중복 도입하지 않는다.30일 첫 교육 완료·90일 후속 이행·대기 및 담당자 부담으로 평가하며 효과를 사전 확정하지 않는다.

부전 질병외·부상은 기전·장소 자료를 확보하기 전 음주·낙상·교통 중 하나로 대체하지 않는다. 해당 자료 제공처는 확인했으나 로그인 필요한 원자료는 미확보다. 센터 수 대비 신고 건수로 인력 부족을 확정하지 않는다.

## 5. 현재 산출물과 검증

- 통합 MD: [부산-119-최신작업-통합정리-20260918.md](../40-분석결과/부산-119-최신작업-통합정리-20260918.md).
- 최신 집계: `data/processed/5개년통합-지역유형-제안연결-20260917/`의11개 CSV·입력/출력 명세·검산·공식서비스 원문.
- 보건 심화: `data/processed/신고보건심화-20260917/`의공표표·조건부 제안·출처·검산.
- 현재 사용 그림9종: 통합2·보건3·주민/현장 비교3·유형 선정1. 구버전 그림 전체를 현재 전달물에 합치지 않는다.
- 코드: `analyze_pooled_five_years_20260917.py`와 별도 `verify_pooled_five_years_20260917.py`; 보고서 생성은 `scripts/write_current_project_report_20260918.py`.
- 입력13개 해시, 구군/유형/동 합계와 동률순위, 시간 전처리5파일 별도 집계, 주민101연령 합계 검산을 통과했다. 기존 검증을 재사용한 범위와 새로 검증한 범위를 분리한다.

## 6. 남은 작업의 순서와 완료 기준

1. **제안의 도입 판단:** 다대·금곡의 실제 교육 연결 누락 여부를 이용·완료 자료로 확인한다. 누락이 없으면 제안을 철회하거나 범위를 줄인다.
2. **사고 원인 연결:** 부전 등은 출동/환자 자료의단위·정의·기간·주소를 확인해 실제 기전·장소로 좁힌다. 접수집합과 단순 합산하지 않는다.
3. **추가 지역 검토:** 우·좌·모라·주례의실제 이용장벽과 참여를 확인한다. 기존센터 존재를 서비스 충족이나 결함으로 단정하지 않는다.
4. **최신 웹 유지:** `web/final/`과 `web/final/analysis/`에 최신45조합·보건 연결·구군 건수순·전체 연령을 반영하고 PC검증을 완료했다. develop의지도 개선과 최신 두 구 비교의조건 차이도 반영했다. 새로운 집계가 생기면 같은 필터·분모·공개 집계 검증을 거친다.
5. **실제 효과 평가:** 시행 전 대상·분모·기간·비교·추적누락을 고정하고 참여·완료·부담을 측정한다. 현장 실험 없이 건강·사고·119 감소 효과를 완료로 표시하지 않는다.

현재 완료 범위는 분석과 조건부 설계, 검증된 시각화·통합 문서·최신 두 웹페이지와 PC 로컬 실행이다. 인터넷 공개 배포·기관 실적 확보·현장 결함 확인·실제 정책 효과는 각각 완료 증거가 생겼을 때 갱신한다.
''', encoding='utf-8', newline='\n')
    output = {'scope':'current adopted analysis only; no historical document archive',
              'report':REPORT.relative_to(ROOT).as_posix(),
              'reportSha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),
              'plan':plan.relative_to(ROOT).as_posix(),
              'planSha256':hashlib.sha256(plan.read_bytes()).hexdigest(),
              'sections':len(chapters),'sourceDocuments':list(SOURCE_NAMES.values()),
              'figures':[p.relative_to(ROOT).as_posix() for _,_,p in figure_specs],
              'csvTables':len(data_rows),'inputs':INPUTS,
              'populationRule':'annual snapshots, never summed across years',
              'newAnalysisExecuted':False,'webUpdated':True,'sourceFilesDeleted':False}
    (AUDIT/'manifest.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'report':output['report'],'sections':len(chapters),'sourceDocuments':len(SOURCE_NAMES),
                      'csvTables':len(data_rows),'figures':len(figure_specs),'bytes':REPORT.stat().st_size},ensure_ascii=False))


if __name__=='__main__':
    main()
