"""Extract official aggregate spreadsheet values, preserving crude rate and SE."""
from pathlib import Path
import json,re,hashlib,csv
import pandas as pd
import pymupdf as fitz
R=Path(__file__).resolve().parents[1];O=R/'data/processed/효과근거확장-20260916/context'
rows=[];sources=[];notes=[]
for gu,page in [('연제구',206),('부산진구',207),('수영구',208)]:
 path=O/f'chs-{gu}-tables.xlsx';x=pd.ExcelFile(path);sheet=next(s for s in x.sheet_names if '교육경험률' in s);f=pd.read_excel(x,sheet,header=None)
 source=next(s for s in json.loads((O/'chs-browser-attempts.json').read_text(encoding='utf-8')) if s.get('district')==gu)
 sources.append({'district':gu,'publicLanding':'https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do','downloadURL':source['url'],'zipSHA256':source['sha256'],'spreadsheet':path.name,'spreadsheetSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'sheet':sheet,'pdf':f'chs-browser-{gu}-1.pdf','pdfSHA256':hashlib.sha256((O/f'chs-browser-{gu}-1.pdf').read_bytes()).hexdigest(),'pdfTablePage':page})
 footnotes=[str(f.iloc[i,1]).strip() for i in range(len(f)) if '조사대상 응답자 수' in str(f.iloc[i,1])];assert len(footnotes)==3
 notes.append({'district':gu,'exactDenominatorNotes':footnotes})
 for i in [5,7,8,10,11,12,13,14,15,17,18]:
  for col,indicator in [(3,'심폐소생술 교육 경험률'),(5,'마네킹 실습 경험률'),(7,'AED 실습 경험률')]:
   match=re.fullmatch(r'(\d+\.\d+)\((\d+\.\d+)\)',str(f.iloc[i,col]));assert match
   rows.append({'district':gu,'year':2024,'subgroup':str(f.iloc[i,1]).strip(),'sampleN':int(f.iloc[i,2]),'indicator':indicator,'crudeWeightedPercent':float(match[1]),'standardErrorPP':float(match[2]),'relativeStandardErrorPercent':float(f.iloc[i,col+1]),'ageStandardizedPercent':None,'confidenceInterval':None,'period':'최근 2년 동안','denominator':'해당 하위집단 조사대상 응답자(19세 이상 표본)','rateType':'가중치 적용 조율','sourceSheet':sheet,'excelRow':i+1,'excelColumn':col+1,'pdfPage':page})
 doc=fitz.open(O/f'chs-browser-{gu}-1.pdf')
 intro='\n'.join(p.get_text() for p in list(doc)[:8]);assert '가중치를 적용한 결과(조율)' in intro
 (O/f'chs-{gu}-rate-definition.txt').write_text(intro,encoding='utf-8')
 agehits=[]
 for i,p in enumerate(doc):
  t=p.get_text()
  if ('19세' in t or '19 세' in t) and i<50:agehits.append({'pdfPage':i+1,'text':t})
 (O/f'chs-{gu}-sampling-definition.json').write_text(json.dumps(agehits,ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame(rows).to_csv(O/'chs2024-cpr-education.csv',index=False,encoding='utf-8-sig')
out={'asOf':'2026-09-16','surveyYear':2024,'unit':'구 단위 주민 표본조사 추정치, 접수 환자·동별 통계 아님','sources':sources,'definitions':notes,'records':rows,'limits':['모든 교육·실습 지표의 분모는 조사대상 응답자이며 교육경험자로 제한하지 않는다.','가중치 적용 조율만 확보. 표준화율은 빈값이며 구간·연령 구성 차이를 보정한 구 순위가 아니다.','괄호는 표준오차이며 신뢰구간이 아니다. 임의의 정규근사 신뢰구간을 만들지 않았다.','19세 이상 조사이며 12세 이상 교육조건과 대상이 다르다. 미성년 주민 교육경험을 외삽하지 않는다.','경험 없음이 수강 희망·접근 장벽·기관 부족·현재 숙련도 부족을 입증하지 않는다.','소그룹 RSE30%이상은 공식 주의 기준. 시각화 또는 정책 판단시 별도 표시 필요.','원ZIP과XLSX·PDF는 내부출처 보존, 웹배포는 이 추출표와출처만 권장.']}
(O/'chs-education-summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 2024 지역사회건강조사: 교육 경험과 실습 경험','', '공식 CHS 공개 페이지의 정상 브라우저 POST·첨부 클릭으로 3개 구 ZIP을 확보했다. 로그인이나 비공개 접근을 사용하지 않았다. 2024 조사자료이며 현재 접수·신청 상태와 다르다.','', '|지역|표본 n|교육 경험 % (SE)|마네킹 실습 % (SE)|AED 실습 % (SE)|','|---|---:|---:|---:|---:|']
for gu in ['연제구','부산진구','수영구']:
 rr=[r for r in rows if r['district']==gu and r['subgroup']=='전체'];lines.append('|'+gu+'|'+str(rr[0]['sampleN'])+'|'+'|'.join(f"{r['crudeWeightedPercent']:.1f} ({r['standardErrorPP']:.1f})" for r in rr)+'|')
lines+=['','세 지표 모두 최근2년 경험자 / 조사대상 응답자 ×100이며 실습률의 분모를 교육경험자로 바꾸지 않는다. 표본 n에 조율을 곱해 경험자 수를 계산하지 않는다. 조율은 가중치가 적용된 추정치이며 SE는 표준오차(퍼센트포인트), 괄호가 신뢰구간은 아니다. 표준화율과 신뢰구간은 이번 추출표에서 빈값으로 남겼다.','', '연제구의 19–29세 교육경험률48.8%(SE5.8),70세 이상7.6%(SE2.1)는 주민 조사에서 확인한 연령 차이다. 이것을 심정지 환자의 연령별 신고나 교육 미충족 수요로 연결하지 않는다. 응답자19세 이상과 기본 교육의12세 이상 자격은 별개이며, 미취학 과정의 필요량을 추정하지 않는다.','', '이 자료는 시설 부족의 증거가 아니라 지역 주민의 교육 경험을 설명하는 추가 배경이다. 교육·실습 경험의 확인은 정보안내를 넘어 실제 참여와 현재 수행능력을 별도로 평가해야 한다는 기준을 제공한다.','', '연제 원문PDF206쪽(인쇄190),부산진207쪽(인쇄191),수영208쪽(인쇄192)의 표와 공식 엑셀 셀을 대조했다. 국회도서관 목차의 인쇄쪽수와 실제 CHS배포본 쪽수가 달라 실제 다운로드 원본을 기준으로 기록했다.']
(O/'교육경험-확보결과.md').write_text('\n'.join(lines),encoding='utf-8')
(O/'chs-extraction-manifest.json').write_text(json.dumps({'sources':sources,'code':{'path':str(Path(__file__).relative_to(R)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'outputFiles':[{'file':n,'sha256':hashlib.sha256((O/n).read_bytes()).hexdigest()} for n in ['chs2024-cpr-education.csv','chs-education-summary.json','교육경험-확보결과.md']],'directImageReview':['연제구 PDF206/94','부산진구 PDF207','수영구 PDF208'],'missingValues':['표준화율','신뢰구간'],'noPrivateMicrodata':True},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(rows),'aggregate cells extracted')
