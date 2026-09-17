from pathlib import Path
import re, json, html
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from PIL import Image
import fitz

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'output/부산진구-중구-1차분석'
DEST=ROOT/'output/pdf/부산진구·중구_신고기반_정책검토_통합분석.pdf'
DEST.parent.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'tmp/pdfs/integrated-review'; TMP.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('KR','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KR-Bold','C:/Windows/Fonts/malgunbd.ttf'))
W,H=landscape(A4); M=38
INK=HexColor('#17354A'); TEAL=HexColor('#137C88'); MUTED=HexColor('#526775')
c=canvas.Canvas(str(DEST),pagesize=(W,H))
c.setTitle('부산진구·중구 신고 기반 정책 검토 | 1차 통합분석')
c.setAuthor('부산 신고 데이터 분석 프로젝트')
style=ParagraphStyle('body',fontName='KR',fontSize=10.5,leading=16,textColor=INK,wordWrap='CJK')
small=ParagraphStyle('small',parent=style,fontSize=9,leading=14)
page=0
def text(s,x,y,width=W-2*M,st=style):
    p=Paragraph(s,st); _,h=p.wrap(width,H); p.drawOn(c,x,y-h); return y-h
def start(title,kicker='부산진구·중구 | 신고 기반 정책 검토'):
    global page
    page+=1
    c.setFillColor(TEAL); c.rect(0,H-8,W,8,fill=1,stroke=0)
    c.setFont('KR',9); c.drawString(M,H-31,kicker)
    c.setFillColor(INK); c.setFont('KR-Bold',21); c.drawString(M,H-64,title)
    c.setStrokeColor(HexColor('#DDE5EB')); c.line(M,34,W-M,34)
    c.setFillColor(MUTED); c.setFont('KR',8)
    c.drawString(M,21,'1차 분석 · 작성 2026-09-17 · 신고는 출동·사고·피해자 수와 다름')
    c.drawRightString(W-M,21,f'{page:02d} / 16')
def end(): c.showPage()
def table(rows,widths,y):
    rows=[[Paragraph(html.escape(str(v)),small) for v in r] for r in rows]
    t=Table(rows,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#E8F1F4')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#DDE5EB'))]))
    _,h=t.wrap(W-2*M,H); t.drawOn(c,M,y-h); return y-h

pop=pd.read_csv(SRC/'06_구별인구와_신고.csv')
counts=pd.read_csv(SRC/'01_부산전체_구군비교.csv').set_index('구군')
types=pd.read_csv(SRC/'01_유형구성.csv').set_index('지역')
start('핵심 결과와 정책 검토 방향')
y=text('부산진구는 신고 총량, 중구는 고령 주민 비율과 주민 규모 대비 신고를 중심으로 후속 검토한다.',M,H-88)
rows=[['지표 · 기간','부산진구','중구']]
for label,vals in [
    ('C 조건 신고 · 2020-2024 합계',[f'{counts.loc[r,"C신고건수"]:,}건' for r in ['부산진구','중구']]),
    ('구급 비중 · 2020-2024 합계',[f'{types.loc[r,"구급"]/counts.loc[r,"C신고건수"]*100:.1f}%' for r in ['부산진구','중구']]),
    ('65세 이상 주민 비율 · 2024년 말',[f'{pop[(pop.지역==r)&(pop.연도==2024)].iloc[0]["65세이상비율"]:.1f}%' for r in ['부산진구','중구']]),
    ('주민 1천 명 대비 연간 C 신고 · 2024',[f'{pop[(pop.지역==r)&(pop.연도==2024)].iloc[0]["연말주민1천명대비신고"]:.1f}건' for r in ['부산진구','중구']])]: rows.append([label,*vals])
y=table(rows,[390,185,185],y-17)
y=text('해석과 한계',M,y-22,st=ParagraphStyle('h',parent=style,fontName='KR-Bold',fontSize=13))
y=text('두 구 모두 구급 신고가 주를 이루지만, 지역의 고령 주민이 그 신고를 했다는 뜻은 아니다. 주민 대비 신고 비율에는 방문객·유동인구의 노출이 반영되지 않았다.',M,y-10)
y=text('소방센터 부족, 고독사 위험, 보건소 신설 또는 노인 일자리 확대 필요성은 아직 확정하지 않았다. 접근성과 실제 지원 공백은 추가 원본이 필요한 미완료 분석이다.',M,y-10)
text('구성: 분석 기준 2쪽 → 연도별 수치 3쪽 → 시각화 12개 4-15쪽 → 추가자료·검증 16쪽',M,73,st=small)
end()

start('기간과 분모를 먼저 구분한다')
y=table([
    ['분석 항목','사용 기간','읽는 기준'],
    ['구별 규모·유형 / 원문 동명 / 센터 기록','2020-2024 합산','5년간 누적 신고의 구성과 집중'],
    ['요일·시간대','2020-2024 통합','해당 요일 일수로 나눈 시간 구간별 건수'],
    ['연간 변화·A/B/C 비교·월별 패턴','각 연도 별도','월별은 그달 일수로 보정, 반복 계절성 미입증'],
    ['인구·주민 대비 신고','연도별 / 연말 인구','연령 세부 구성 그림은 2024년 말'],
    ['소방관서·인원·차량','보유 원표, 기준일 미확인','소재지 기준, 당시 교대 가용량·관할과 다름']
],[270,175,315],H-91)
y=text('분석 모집단',M,y-20,st=ParagraphStyle('h2',parent=style,fontName='KR-Bold',fontSize=13))
y=text('원신고 4,552,768건 → A 704,689건 → B 579,412건 → C 574,662건',M,y-10)
y=text('A: 부산 명시 + 선택 17개 항목 모두 기재. B: A 중 정상처리. C: B 중 업무운행·훈련출동·구급차소독 제외. 본문 그림은 C가 기본이며 조건 비교 그림에서 A/B/C를 구분한다.',M,y-8)
text('C는 전체 신고의 대표 표본으로 보장되지 않는다. 동별 분석은 원문 동명 기준이며, 행정동 인구를 임의 연결하거나 신고 건수를 나눠 배분하지 않았다.',M,y-8)
end()

start('연도별 핵심 수치 | 합계와 별도로 확인')
rows=[['연도','부산진구 C 신고','중구 C 신고','부산진구 65세 이상','중구 65세 이상']]
for year in range(2020,2025):
    a=pop[(pop.연도==year)&(pop.지역=='부산진구')].iloc[0]; b=pop[(pop.연도==year)&(pop.지역=='중구')].iloc[0]
    rows.append([year,f'{int(a.신고건수):,}건',f'{int(b.신고건수):,}건',f'{a["65세이상비율"]:.1f}%',f'{b["65세이상비율"]:.1f}%'])
y=table(rows,[80,170,170,170,170],H-98)
y=text('두 구 모두 이 C 조건 집계에서는 2022년에 신고가 가장 많다. 2024년 신고 감소와 고령 주민 비율 상승은 동시에 나타나므로, 고령화만으로 신고 변화를 설명할 수 없다.',M,y-24)
y=text('각 연도의 자료 누락·선택17개 완전기재 조건·처리결과 구성 변화가 추세에 영향을 줄 수 있다. 그림 03의 조건 민감도를 함께 읽어야 한다.',M,y-12)
text('출처: 06_구별인구와_신고.csv / 신고는 C 조건, 인구는 각 연도 12월 주민등록 인구.',M,y-22,st=small)
end()

md=(SRC/'분석보고서.md').read_text(encoding='utf-8')
entries=re.findall(r'### ([^\n]+)\n([^\n]+)\n!\[[^\]]+\]\(([^)]+)\)',md)
assert len(entries)==12
titles=['부산 전체에서 두 구의 신고 규모 비교','구급 중심의 유형 구성','연도별 추세와 조건 민감도','요일·시간대별 집중','월별 패턴은 연도를 나눠 비교','원문 동명별 신고 집중','소방자원의 소재지별 비교','기록상 센터 구성 | 접근성의 사전 진단','고령 주민과 주민 대비 신고','고령층 내부의 연령 구성','실제 지원범위 | 필요한 근거','정책 대안으로 연결하는 판단 조건']
periods=['2020-2024 합산','2020-2024 합산','2020-2024 연도별','2020-2024 통합 · 요일 일수 보정','2020-2024 연도별 · 월 일수 보정','2020-2024 합산 · 원문 동명','기준일 미확인 · 원표 소재지','2020-2024 합산 · 관할서센터명','2020-2024 연도별 · 연말 인구','2024년 12월','지원 공백 분석 미완료','정책 효과 검증 미완료']
for i,((name,note,path),title,period) in enumerate(zip(entries,titles,periods),1):
    start(title,f'그림 {i:02d} / 12 · {period}')
    image_path=(SRC/path).resolve()
    iw,ih=Image.open(image_path).size
    scale=min((W-2*M)/iw,355/ih)
    dw,dh=iw*scale,ih*scale
    c.drawImage(str(image_path), (W-dw)/2,135+(355-dh)/2, dw,dh, mask='auto')
    c.setFillColor(HexColor('#EFF5F7')); c.roundRect(M,47,W-2*M,76,7,fill=1,stroke=0)
    text(note.replace('–','-'),M+12,111,W-2*M-24,small)
    end()

start('추가 확보 자료와 재현·검증 기록')
y=table([
    ['다음 판단','필요한 원본','현재 가능한 결론'],
    ['소방 대응의 시간·공간 공백','출동/도착 시각, 당시 가용인원·차량, 관할·상호지원, 도로 통행조건','기록상 센터 구성까지 확인. 실제 접근성·업무량 미판정'],
    ['고령층 건강·돌봄 지원 공백','사업별 자격·담당 구역·시간·정원·실제 이용·대기','주민 연령 맥락 확인. 미지원·시설 부족 확정 불가'],
    ['정책 대안의 효과','같은 인력·시간·예산 조건, 수행 업무와 감독·평가 기준','대안 검토 조건 정리. 개선율·신설 효과 미계산']
],[145,340,275],H-93)
y=text('검증 결과',M,y-18,st=ParagraphStyle('h3',parent=style,fontName='KR-Bold',fontSize=13))
y=text('C 접수번호 574,662개 중복 없음. 구·동·유형·월·요일시간·센터 집계 합계 일치. 인구 연령 합계 일치. 관서 인원·차량 연결 누락 0건. 입력 25개·출력 40개 해시 검증 통과. 웹 시각화 12개 로딩 확인.',M,y-9)
y=text('자료 및 재현 경로',M,y-16,st=ParagraphStyle('h4',parent=style,fontName='KR-Bold',fontSize=13))
y=text('부산소방재난본부 2020-2024 접수 원본의 로컬 A/B/C 전처리와 공식 컬럼 설명, 행정안전부 각 연도 12월 연령별 인구, 사용자 제공 소방관서 위치·인원·차량 CSV 3종을 사용했다. 소방자원의 기준일·공식 원문 URL은 미확인이다.',M,y-9,st=small)
y=text('집계·해시·검증: output/부산진구-중구-1차분석/<br/>제작·검증 코드: analysis/01_쏠림진단/analyze_two_districts.py, verify_two_districts.py<br/>이 PDF는 기존 1차 분석 결과를 통합한 문서이며, 신규 분석이나 정책 효과 입증을 추가한 문서가 아니다.',M,y-8,st=small)
end()
assert page==16
c.save()
doc=fitz.open(DEST)
assert len(doc)==16
for i,p in enumerate(doc):
    p.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(TMP/f'page-{i+1:02d}.png')
    assert p.get_text().strip()
# 전체 페이지 확인용 미리보기
thumbs=[]
for f in sorted(TMP.glob('page-*.png')):
    im=Image.open(f).convert('RGB'); im.thumbnail((505,365)); thumbs.append(im)
for batch in range(4):
    sheet=Image.new('RGB',(1030,760),'#dce4e9')
    for j,im in enumerate(thumbs[batch*4:(batch+1)*4]): sheet.paste(im,(10+(j%2)*515,10+(j//2)*380))
    sheet.save(TMP/f'review-{batch+1}.png')
print(json.dumps({'pdf':str(DEST),'pages':len(doc),'figures':len(entries)},ensure_ascii=False))
