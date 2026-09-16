"""검증된 웹 집계와 실제 경계로 Track1 시각화 PDF 검토본을 만든다."""
import json
import math
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/'web/data/dashboard.json').read_text(encoding='utf-8'))
GEO=json.loads((ROOT/'web/data/busan-districts.geojson').read_text(encoding='utf-8'))
OUT=ROOT/'output/pdf/트랙1-시각화-검토본.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Korean','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KoreanBold','C:/Windows/Fonts/malgunbd.ttf'))
W,H=landscape(A4)
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('부산 신고 기반 지역 비교 - 시각화 검토본')
c.setAuthor('부산 공모전 분석 프로젝트')
TEAL='#006d77';INK='#163743';MUTED='#607681'
COLORS=['#d9edeb','#acd5d1','#76b6b4','#398f94','#006775']

def text(x,y,value,size=10,color=INK,bold=False):
    c.setFont('KoreanBold' if bold else 'Korean',size)
    c.setFillColor(HexColor(color));c.drawString(x,y,str(value))

def page(title,subtitle,number):
    c.setFillColor(HexColor('#f7fafb'));c.rect(0,0,W,H,fill=1,stroke=0)
    text(35,H-30,'BUSAN SAFETY INSIGHTS  /  Track 1 시각화 검토본',9,TEAL,True)
    text(35,H-63,title,22,INK,True);text(35,H-86,subtitle,10,MUTED)
    text(35,22,'2026-09-10 검토본 · 최종 제출본 아님 · 접수 건수는 독립 사고·환자 수가 아님',8,MUTED)
    text(W-52,22,f'{number}/3',8,MUTED)

def polygons(f):
    g=f['geometry'];return [g['coordinates']] if g['type']=='Polygon' else g['coordinates']

def map_draw(x,y,width,height,condition,lo,hi):
    project=lambda p:(p[0]*math.cos(math.radians(35.2)),p[1])
    pts=[project(p) for f in GEO['features'] for poly in polygons(f) for ring in poly for p in ring]
    minx,miny=min(p[0] for p in pts),min(p[1] for p in pts)
    maxx,maxy=max(p[0] for p in pts),max(p[1] for p in pts)
    scale=min(width/(maxx-minx),height/(maxy-miny))
    ox=x+(width-(maxx-minx)*scale)/2;oy=y+(height-(maxy-miny)*scale)/2
    for f in GEO['features']:
        value=DATA['byYear']['2024']['districts'][f['properties']['name']]['reports'][condition]
        idx=min(4,int((value-lo)/(hi-lo)*5)) if hi>lo else 0
        c.setFillColor(HexColor(COLORS[idx]));c.setStrokeColor(HexColor('#ffffff'));c.setLineWidth(.35)
        path=c.beginPath()
        for poly in polygons(f):
            for ring in poly:
                for i,p in enumerate(ring):
                    px,py=project(p);px=ox+(px-minx)*scale;py=oy+(py-miny)*scale
                    if i==0:path.moveTo(px,py)
                    else:path.lineTo(px,py)
                path.close()
        c.drawPath(path,fill=1,stroke=1,fillMode=0)

page('조건을 바꾸면, 지역 비교도 달라집니다','2024년 부산 명시 접수 · 동일한 색상 구간으로 비교 · 구군명별 집계의 참고 지도',1)
year=DATA['byYear']['2024'];city=year['city']
values=[r['reports'][key] for r in year['districts'].values() for key in ['A','C']]
lo,hi=min(values),max(values)
for x,key,title in [(35,'A','A · 전체 처리결과'),(W/2+12,'C','C · 정상 중 운영기록 3종 제외')]:
    text(x,H-121,title,12,TEAL,True)
    text(x,H-146,f"부산 전체 {city['reports'][key]:,}건 / 구군 미기재 {year['missingDistrict'][key]:,}건",10)
    map_draw(x,145,W/2-60,270,key,lo,hi)
step=(hi-lo)/5
for i,color in enumerate(COLORS):
    x=35+i*150;c.setFillColor(HexColor(color));c.rect(x,120,18,8,fill=1,stroke=0)
    text(x+23,120,f'{lo+step*i:,.0f}–{lo+step*(i+1):,.0f}건',8,MUTED)
text(35,96,'C 제외값: 업무운행·훈련출동·구급차소독. 실제 사고만 남았다는 뜻이 아닙니다.',9)
text(35,77,'경계: SGIS 2025.06.30 · 과거 사건의 공간 재집계 아님. 지역 미기재는 지도에 배분하지 않았습니다.',8,MUTED)
text(35,58,'출처: 사용자 제공 부산소방 119 원본 및 검증된 조건별 집계 / SGIS data.go.kr/data/15129688/fileData.do',8,MUTED)
c.showPage()

page('16개 구·군을 같은 조건으로 비교','2024년 · 가나다순 · 접수량을 위험도나 지원 공백의 확정 순위로 해석하지 않습니다.',2)
xs=[35,225,365,505,660]
for x,label in zip(xs,['구군','A 전체 접수','B 정상','C 운영 3종 제외','65세 이상 인구 비중']):text(x,H-122,label,10,TEAL,True)
names=sorted(DATA['districtNames'])
for i,name in enumerate(names):
    y=H-146-i*19;r=year['districts'][name]
    if i%2==0:c.setFillColor(HexColor('#eaf1f3'));c.rect(30,y-5,W-60,19,fill=1,stroke=0)
    vals=[name,*[f"{r['reports'][k]:,}" for k in ['A','B','C']],f"{100*r['age65plus']/r['populationTotal']:.2f}%"]
    for x,value in zip(xs,vals):text(x,y,value,9)
text(35,126,'사례: 연제구의 접수량 순위는 A 9위 → B 7위 → C 9위. 포함 조건을 먼저 설명해야 합니다.',9,TEAL,True)
text(35,105,'65세 이상 비중은 별도 인구 배경이며 고령자 신고 비중이 아닙니다. 노약자 여부를 연령만으로 판단하지 않습니다.',8.5)
text(35,84,'부산 명시 중 구군 미기재: A 510건 / B 92건 / C 91건. 표의 16구군과 미기재를 합하면 부산 전체와 일치합니다.',8.5)
text(35,63,'출처: data/processed/신고조건비교/ · 행정안전부 연령별 주민등록인구, 2024.12 (jumin.mois.go.kr)',8,MUTED)
c.showPage()

page('중간 연령을 포함한 전체 인구 배경','2018·2024년 연말 비교 · 7년 전체 데이터 보존 · 연령별 신고 건수나 위험률을 산출한 결과가 아닙니다.',3)
old=DATA['byYear']['2018']['city'];new=DATA['byYear']['2024']['city']
text(35,H-120,'2018년',10,'#709da7',True);text(123,H-120,'2024년',10,TEAL,True)
maxn=max(b['count'] for r in [old,new] for b in r['ageBands'])
for i,(a,b) in enumerate(zip(old['ageBands'],new['ageBands'])):
    assert a['label']==b['label']
    y=H-150-i*29;text(35,y,a['label'],9)
    for value,dy,col in [(a['count'],4,'#b3d3d9'),(b['count'],-6,TEAL)]:
        c.setFillColor(HexColor(col));c.rect(118,y+dy,410*value/maxn,7,fill=1,stroke=0)
    text(554,y,f"{a['count']:,} → {b['count']:,}명",9)
text(35,107,f"65세 이상 인구: {old['age65plus']:,}명({100*old['age65plus']/old['populationTotal']:.2f}%) → {new['age65plus']:,}명({100*new['age65plus']/new['populationTotal']:.2f}%)",10,TEAL,True)
text(35,86,'65세 기준은 원본 1세별 값을 정확히 합산했습니다. 100세 이상 큰 변화의 원인은 확인 전 해석을 보류합니다.',8.5)
text(35,65,'출처: 행정안전부 연령별 주민등록인구, 각 연도 12월 말 · 외국인 제외 (jumin.mois.go.kr/ageStatMonth.do)',8,MUTED)
text(35,46,'검증: 7년 전체 원본과 별도 집계 대조. 상세 근거는 보고서 작업초안 및 검증 manifest를 따릅니다.',8,MUTED)
c.save()
print(OUT)
