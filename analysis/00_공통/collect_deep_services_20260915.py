"""Collect question-driven official service evidence, separately from receipt inputs."""
from pathlib import Path
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/processed/심층분석-20260915'
RAW = ROOT / 'data/interim/심층보완근거-20260915'
SOURCES = [
    dict(id='gijang_visit', title='기장군 방문건강관리사업',
         url='https://www.gijang.go.kr/health/index.gijang?menuCd=DOM_000000402002002000', referenceDate='2025-09-03',
         trigger='기장읍·정관읍 질병 신고 반복의 후속 질문: 방문형 건강관리의 기존 대상과 지역담당 범위는 무엇인가?',
         facts=['보건소 방문이 어려운 건강위험 취약가구를 대상으로 가정 방문·건강상담·보건의료 연계를 안내한다.', '대상 등록 동의와 방문약속 절차가 있으며 지역담당 간호사 표에 정관읍과 기장읍의 리별 담당이 기재돼 있다.'],
         target='기초생활수급·차상위 건강위험가구 등 우선순위에 따른 대상', hours='방문약속 방식; 구체적인 방문 가능 시간과 대기기간은 안내에서 미확인',
         conditions='대상 확인·등록 동의·방문약속 후 서비스', coverage='기장군 지역담당제; 기장읍 리별 담당과 정관읍 담당 명시',
         unknowns=['2020~2024 당시 운영조건', '읍별 적격 대상 규모·등록률·대기기간·미이용 사유', '질병 신고 기록과 서비스 대상의 실제 중첩']),
    dict(id='gijang_center', title='기장읍 하하마을건강센터',
         url='https://www.gijang.go.kr/index.gijang?menuCd=DOM_000000402002005000', referenceDate='2025-05-09',
         trigger='기장읍에서 주민 누구나 접근할 수 있는 건강상담 경로와 방문형 서비스의 이용조건은 어떻게 다른가?',
         facts=['기초건강검사·상담과 주민 건강활동을 제공하는 무료 서비스가 안내돼 있다.', '진료·처방·예방접종 등은 제공하지 않는다고 명시한다.'],
         target='주민 누구나', hours='평일 09:00~17:00, 점심 12:00~13:00',
         conditions='무료; 동아리 등 일부 프로그램은 인원 제한 가능', coverage='기장읍 차성로242번길 56, 복합커뮤니티센터 2층',
         unknowns=['2020~2024 운영 이력', '실제 이용 주민의 읍·연령 분포와 이용 장벽', '시간대별 미충족 상담 수요']),
    dict(id='busan_ems', title='부산소방 구급 서비스 안내',
         url='https://119.busan.go.kr/firefighting04', referenceDate='2024-01-24',
         trigger='질병 분류 신고에 대해 이미 제공되는 긴급 대응과 비응급 건강관리의 역할을 구분할 수 있는가?',
         facts=['응급환자에 대한 현장 응급처치와 치료 가능한 병원으로의 무료 이송을 안내한다.'],
         target='응급환자', hours='응급신고 대응; 이 페이지에는 시간표·응답시간 기준 미기재',
         conditions='119 신고를 통한 응급상황 접수', coverage='부산소방 구급 서비스',
         unknowns=['분석의 질병 분류별 실제 환자 중증도·이송 결과', '지역별 서비스 미충족 여부']),
    dict(id='busan_rescue', title='부산소방 구조 서비스 안내',
         url='https://119.busan.go.kr/firefighting03', referenceDate='2024-01-24',
         trigger='금곡동 구조 시건개방을 단순 생활불편으로 해석할 수 있는가?',
         facts=['재난과 사고에서 인명구조를 수행하는 기존 대응을 안내한다.', '이 안내만으로 시건개방 접수의 긴급성이나 개별 출동 판단 기준은 확인되지 않는다.'],
         target='재난·사고 현장의 구조 필요 대상', hours='안내 페이지에 개별 운영시간 미기재',
         conditions='구조 필요 상황의 신고·현장 판단; 시건개방 세부 판단 규칙은 미확인', coverage='부산소방 구조 서비스',
         unknowns=['시건개방 분류의 접수 코드 정의', '인명위험·실내갇힘·안전확인 등 목적별 구성', '현장 결과와 실제 반복 장소 여부']),
]

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'): self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style'): self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip(): self.parts.append(data.strip())

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def collect(source):
    s=dict(source); s['checkedAt']=datetime.now(timezone.utc).isoformat()
    s['evidenceKind']='official_page_reviewed_with_web_tool; analyst paraphrase'
    try:
        with urlopen(Request(s['url'],headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as response:
            content=response.read(); encoding=response.headers.get_content_charset() or 'utf-8'
        p=RAW/(s['id']+'.html'); p.write_bytes(content)
        parser=TextParser();parser.feed(content.decode(encoding,errors='replace'))
        txt=RAW/(s['id']+'.txt');txt.write_text('\n'.join(parser.parts),encoding='utf-8')
        s['download']={'status':'downloaded','path':str(p.relative_to(ROOT)),'sha256':digest(p),'textPath':str(txt.relative_to(ROOT)),'textSha256':digest(txt)}
    except Exception as exc:
        s['download']={'status':'failed','error':str(exc),'fallback':'Official page content inspected through web tool; source URL, date and paraphrased facts retained. Not an original HTML archive.'}
    return s

def main():
    OUT.mkdir(parents=True,exist_ok=True);RAW.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool: sources=list(pool.map(collect,SOURCES))
    cases=[
      dict(district='기장군',rawDong='기장읍',type='구급',subtype='질병',sourceIds=['gijang_center','gijang_visit','busan_ems'],
           observationQuestion='같은 질병 분류가 반복되는 가운데 어떤 시간 패턴과 주민 배경이 함께 관측되는가?',
           hypothesis='주민 누구나 이용하는 상담과 대상 조건이 있는 방문형 관리의 안내 경로를 구분해 제공할 필요가 있는지 확인한다.',
           nextEvidence=['읍별·연령별 서비스 인지도와 미이용 사유의 익명 집계', '방문건강관리 적격 대상·등록·대기기간 집계', '질병 세부 증상·중증도·이송 여부'],
           decision='현재 서비스의 대상·시간·신청 경로를 비교하는 정보카드를 제공한다. 지역 대응 공백 판단과 서비스 확대는 후속 확인 뒤 검토한다.', status='기존 서비스 안내 구현 · 확대안 검토'),
      dict(district='기장군',rawDong='정관읍',type='구급',subtype='질병',sourceIds=['gijang_visit','busan_ems'],
           observationQuestion='기장읍과 같은 군·같은 분류인데 결측 제외 후 규모 비교가 얼마나 달라지는가?',
           hypothesis='기록 잔존율 차이를 먼저 해소하거나 비교 범위를 정해야 두 읍의 지원 우선순위를 논의할 수 있다.',
           nextEvidence=['접수경로×읍×현장구군 기재 규칙', '같은 기록 조건에서의 질병 신고 구성', '정관읍 방문건강관리 이용조건·미이용 사유'],
           decision='같은 군의 비교 사례로 제시한다. 낮은 잔존 건수를 낮은 수요로 해석하지 않고 자원 배분 순위는 보류한다.',status='비교 관측 · 우선순위 판단 보류'),
      dict(district='연제구',rawDong='연산동',type='구급',subtype='질병',sourceIds=['busan_ems'],
           observationQuestion='큰 원문명칭 단위의 반복 관측을 실제 어느 행정동까지 좁힐 수 있는가?',
           hypothesis='복수 행정동으로 나누기 전에 확인된 시간 패턴과 기록명 단위 구성을 분석한다.',
           nextEvidence=['당시 주소 또는 신뢰 가능한 좌표 정의', '연도별 행정동 경계와 공간 연결 결과', '연결 후 행정동별 구성·주민 배경'],
           decision='원문 연산동의 반복·시간 특징을 제공한다. 여러 행정동 인구 합산과 특정 행정동 보완안은 보류한다.',status='원문 지역 심층 관측'),
      dict(district='북구',rawDong='금곡동',type='구조',subtype='시건개방',sourceIds=['busan_rescue'],
           observationQuestion='반복되는 시건개방은 어떤 구조 목적과 현장 결과로 구성되는가?',
           hypothesis='안전확인·인명위험·단순 잠금 등 실제 목적을 구분한 뒤 적합한 예방·지원 경로를 검토한다.',
           nextEvidence=['2020~2024 시건개방 코드 정의와 인명위험 판단 기준', '개인정보를 제거한 목적·시간대·처리결과 교차표', '관할 현장 대응과 기존 안내 절차'],
           decision='시건개방을 고독사·독거노인·비긴급 신고로 치환하지 않는다. 목적 확인 전 특정 인력·문개방 서비스 제안은 보류한다.',status='구조 목적 확인 후 보완 검토'),
    ]
    result={'period':'2020–2024','sources':sources,'cases':cases,
            'sourceSelection':'선정한 네 원문 지역·유형의 서비스 대상과 역할 질문에 한정. 상권·공사·생활인구는 현 단계 질문을 직접 검증하지 않아 결합하지 않음.',
            'timeInterpretation':'2025 갱신 안내는 현재 서비스 비교용이며 2020–2024 당시 운영 실적으로 간주하지 않음.'}
    p=OUT/'case_service_evidence.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    web=ROOT/'web/final/data/case-services.js';web.write_text('window.BUSAN_CASE_SERVICES='+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    (RAW/'manifest.json').write_text(json.dumps({'sources':sources,'outputs':[{'file':str(p.relative_to(ROOT)),'sha256':digest(p)},{'file':str(web.relative_to(ROOT)),'sha256':digest(web)}]},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({s['id']:s['download']['status'] for s in sources}))

if __name__=='__main__':main()
