from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz

root=Path(__file__).resolve().parents[2]
out=root/'output/pdf/부산진구·중구_신고기반_정책제안_분석설계.pdf'
out.parent.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('KR','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KRB','C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('KR',normal='KR',bold='KRB')
ink=colors.HexColor('#17394b');teal=colors.HexColor('#147d87')
styles={
 'title':ParagraphStyle('title',fontName='KRB',fontSize=23,leading=32,textColor=ink,spaceAfter=16,wordWrap='CJK'),
 'h':ParagraphStyle('h',fontName='KRB',fontSize=15,leading=22,textColor=ink,spaceBefore=10,spaceAfter=8,wordWrap='CJK'),
 'body':ParagraphStyle('body',fontName='KR',fontSize=10,leading=16,textColor=ink,spaceAfter=7,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=9,leading=15,textColor=ink,wordWrap='CJK'),
 'head':ParagraphStyle('head',fontName='KRB',fontSize=9,leading=14,textColor=colors.white,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='KR',fontSize=8,leading=13,textColor=colors.HexColor('#617887'),spaceAfter=7,wordWrap='CJK')}
def p(s,style='body'): return Paragraph(s,styles[style])
def table(headers,rows,widths):
 t=Table([[p(v,'head') for v in headers]]+[[p(v,'cell') for v in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),teal),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f6f8'),colors.white]),('LINEBELOW',(0,1),(-1,-1),.5,colors.HexColor('#dce7ec'))]))
 return t
story=[]
story += [p('BUSAN · 분석 설계안 / 2026.09.17','small'),p('부산진구·중구\n신고 기반 정책제안'.replace('\n','<br/>'),'title'),p('신고 수요와 대응 여건을 비교하고, 지역별로 필요한 예방·지원 기능을 찾는 분석 설계다. 이 문서는 분석 결과나 자원 부족을 확정한 보고서가 아니다.'),p('핵심 연구 질문','h'),p('“어떤 신고 수요가 어디에 반복되고, 기존 대응 여건을 고려할 때 어느 지역에 어떤 기능을 보완해야 하는가?”'),p('01  신고 수요와 소방 대응','h')]
story.append(table(['분석 축','구체적으로 확인할 내용','판단과 정책 연결'],[
 ['1. 규모·구성','구급·구조·화재 및 세부 유형별 건수와 구성비. 연도별 증감, A/B/C 처리조건 변경에 따른 차이.','건수가 많은 유형과 다른 지역보다 비중이 높은 유형을 구분해 우선 분석 대상을 선정한다.'],
 ['2. 시간 집중','평일·주말, 시간대, 계절별 건수와 일평균. 특정 해의 증가인지 여러 해 반복되는지 확인.','반복되는 시간대에 예방·지원 운영시간을 검토한다. 접수 시각만으로 동시 출동 부담을 확정하지 않는다.'],
 ['3. 공간 편중','동별 유형·시간 분포와 상위 동의 신고 집중 비중. 원문 동명과 행정동 연결, 좌표의 의미를 검토.','구 전체에 일괄 적용하지 않고 대상 동·생활권을 좁힌다. 위치 연결이 불확실한 기록은 별도 처리한다.'],
 ['4. 대응 자원','출동 거점과 본부·학교 등을 구분. 중복 등록, 차량 용도, 인력 기준일과 근무조 확인.','구급·구조·화재별 대응 가능 자원을 비교한다. 시설 개수나 전체 차량 수를 대응 능력으로 대체하지 않는다.']
 ],[78,218,215]))
story += [Spacer(1,10),p('비교 원칙: 부산진구·중구를 상세 분석 대상으로 하되, 부산 전체 분포를 비교 기준으로 활용한다. 총건수는 업무 수요의 규모, 구성비는 신고 특성으로 구분하며 위험도로 표현하지 않는다.','small'),PageBreak()]
story += [p('02  접근성·주민 여건·기존 지원','title'),p('긴급 대응과 예방·돌봄은 별도 축으로 판단한다. 돌봄사업이 소방 인력이나 응급 대응을 대신한다고 해석하지 않는다.')]
story.append(table(['분석 축','구체적으로 확인할 내용','판단과 정책 연결'],[
 ['5. 거점 접근성','구 밖 센터를 포함한 적합 거점까지의 도로 이동거리·시간. 평균뿐 아니라 먼 지역과 그곳의 신고 비중.','상대적으로 접근성이 낮은 지역을 찾는다. 출동·도착 기록이 없으면 모형상 접근성으로 한정한다.'],
 ['6. 고령 주민 여건','고령인구 수와 비율, 75세·85세 이상 구성, 독거노인가구. 관련 세부 신고 분포와 지역 단위 비교.','비율이 높은 지역과 지원 대상 인원이 많은 지역을 구분한다. 지역 연령으로 신고 당사자 나이를 추정하지 않는다.'],
 ['7. 실제 지원 범위','보건소·건강센터·복지관 위치, 방문사업 대상·지원 인원·운영시간·대기 수요·신청 방식.','누가 어떤 서비스를 이용할 수 있는지 판단한다. 자료 부재를 미지원으로 확정하지 않는다.'],
 ['8. 정책 적합성','해당 신고 유형에 개입 가능한 활동, 담당 기관, 필요 인력·시간·비용, 기존 사업과 중복 여부.','시설 신설·시간 조정·방문지원·예방교육·기관 연계 중 근거에 맞는 대안을 비교한다.']
 ],[78,218,215]))
story += [p('보완할 문제에 따라 정책도 달라진다','h')]
story.append(table(['문제 구분','확인해야 할 근거','제안 방향'],[
 ['긴급 대응 여건','적합 거점까지의 거리, 실제 도착 지연, 가용자원 부족 여부','출동체계·근무시간대·차량 및 인력 배치 검토'],
 ['예방·생활 지원','관련 신고 반복과 주민의 지원 필요 여건, 기존 사업 미충족 범위','방문건강관리·돌봄·예방활동 확대'],
 ['서비스 연결','사업은 있으나 대상 조건·시간·신청 절차 때문에 이용이 어려움','안내·대상 발굴·의뢰·기관 간 연계 개선']
 ],[87,222,202]))
story.append(PageBreak())
story += [p('03  근거에서 정책 제안까지','title'),p('분석의 연결 순서','h'),p('<b>신고 특성 → 지역 여건 → 기존 대응 → 보완 제안</b>'),p('“신고가 많고 센터 수가 적다”는 출발점이다. 구 밖 센터의 접근성, 차량 종류, 실제 근무 인원을 확인해야 어떤 대응 기능을 보완할지 판단할 수 있다.'),p('고령 주민 관련 제안도 같은 원칙을 적용한다. 고령 주민 규모 → 관련 신고 특성 → 방문건강·돌봄사업 지원 범위 → 미충족 기능에 맞는 대안 비교 순서로 근거를 쌓는다.'),p('정책 수단별 역할','h')]
story.append(table(['수단','검토할 역할과 조건'],[
 ['방문건강관리','건강 점검·상담·의료 연계가 필요한 경우 검토한다. 보건소 신설과 기존 방문사업 확대를 같은 대안으로 취급하지 않는다.'],
 ['돌봄·안부 확인','독거·돌봄 공백의 근거와 기존 지원 범위를 확인한 뒤 대상 지역을 검토한다.'],
 ['노인일자리 연계','교육받은 참여자의 안부 확인·생활 안내·서비스 신청 지원 같은 비의료 활동을 검토한다. 전문 돌봄·의료·응급 대응을 대체하지 않는다.']
 ],[100,411]))
story += [p('최종 산출물: 지역별 정책 판단표','h'),p('두 구의 순위를 매기는 데 그치지 않고 아래 여섯 항목을 지역별로 작성한다. 대상 동·생활권은 분석 후 선정한다.')]
story.append(table(['항목','작성 기준'],[
 ['대상 동·생활권 / 신고 특성','선정 근거와 유형·시간·여러 해 반복 여부를 기재'],
 ['주민·대응 여건 / 기존 지원','고령 주민 규모·거점 접근성, 사업 대상·운영시간·지원 규모를 기재'],
 ['보완 제안 / 추가 근거','담당 기관과 활동을 명시하고, 실제 출동시간·대기인원 등 미확인 근거를 병기']
 ],[154,357]))
story += [p('우선 실행 순서','h'),p('① 보유 자료로 신고 수요·공간 분포·소방자원 구성·연령 구성을 점검한다.<br/>② 도로망과 근무조·출동 기록, 보건·돌봄사업 자료를 추가 확보한다.<br/>③ 지역별로 필요한 기능과 대안을 비교하고, 기대효과와 검증 결과를 분리해 제시한다.'),p('자료 상태: 앞선 대화에서 정리한 분석 설계를 문서화했다. 보유 파일의 기준시점·정의·누락 여부는 실제 분석 전에 재확인한다. 새로운 분석 수치나 정책 효과를 산출한 문서는 아니다.','small')]
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#dce7ec'));c.line(42,39,553,39)
 c.setFont('KR',8);c.setFillColor(colors.HexColor('#617887'));c.drawString(42,25,'부산진구·중구 | 신고 기반 정책제안 분석 설계');c.drawRightString(553,25,str(doc.page))
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=39,bottomMargin=50,title='부산진구·중구 신고 기반 정책제안 분석 설계',author='부산 프로젝트').build(story,onFirstPage=footer,onLaterPages=footer)
doc=fitz.open(out)
print('pages',len(doc))
for i,page in enumerate(doc):
 page.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(root/f'tmp/pdfs/policy-{i+1}.png')
 assert page.get_text().strip()
print(str(out))
