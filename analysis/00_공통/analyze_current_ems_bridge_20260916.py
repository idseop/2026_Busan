"""Separate city-level 2024/2025 official EMS series, never merge receipt denominators."""
from pathlib import Path
import json,re,hashlib
import fitz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import StrMethodFormatter
R=Path(__file__).resolve().parents[2];O=R/'data/processed/예방지원-근거분석-20260916/yearbooks';O.mkdir(parents=True,exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf');plt.rcParams['font.family']='Malgun Gothic';plt.rcParams['axes.unicode_minus']=False
manifest=json.loads((R/'data/raw/보완자료/구급연보_수집_manifest.json').read_text(encoding='utf8'))
rows=[];evidence=[]
for edition,pages in [(2025,{'totals':89,'severe':111}),(2026,{'totals':89,'severe':110})]:
 p=R/f'data/raw/보완자료/소방청_119구급서비스통계연보_{edition}.pdf';sha=hashlib.sha256(p.read_bytes()).hexdigest();record=next(x for x in manifest if f'_{edition}.pdf' in x['file']);assert record['sha256']==sha
 doc=fitz.open(p);values={}
 for kind,page_no in pages.items():
  page=doc[page_no-1];text=page.get_text();snippet=text.split('부산\n',1)[1].split('대구\n',1)[0];nums=[int(s.replace(',','')) for s in re.findall(r'[\d,]+',snippet)]
  assert len(nums)==(8 if kind=='totals' else 5),(edition,kind,nums)
  if kind=='totals':values.update(ambulances=nums[0],dispatches=nums[1],transports=nums[2],patients=nums[3])
  else:values.update(severePatients=nums[0],cardiacArrestPatients=nums[1]);assert sum(nums[1:])==nums[0]
  page.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(str(O/f'official-{edition}-page-{page_no}.png'))
  evidence.append({'edition':edition,'coverageYear':edition-1,'pdfPage':page_no,'printedPage':page_no-8,'kind':kind,'busanValues':nums,'sourceUrl':record['source_page'],'sourceSha256':sha})
 rows.append({'year':edition-1,**values})
result={'scope':'부산광역시 공식 구급 출동/이송통계. 17컬럼 신고 집합과 다른 모집단이며 동별 또는 현재 2026 실적 아님.','rows':rows,'evidence':evidence,'differences':{k:{'absolute':rows[1][k]-rows[0][k],'percent':(rows[1][k]/rows[0][k]-1)*100} for k in ['dispatches','patients','cardiacArrestPatients']}}
(O/'current-ems-bridge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
fig,axs=plt.subplots(1,3,figsize=(12.4,4.8));fig.suptitle('2025년에도 구급 대응은 지속됐다 · 증가 여부는 지표별로 확인',fontsize=17,x=.06,ha='left',y=.98)
for ax,(k,title,unit) in zip(axs,[('dispatches','구급 출동','건'),('patients','이송 인원','명'),('cardiacArrestPatients','심정지 이송 인원','명')]):
 vals=[r[k] for r in rows];ax.plot([2024,2025],vals,'o-',color='#12788b',linewidth=2,markersize=8);ax.set_xticks([2024,2025]);ax.set_xlim(2023.65,2025.35);ax.set_ylim(0,max(vals)*1.28);ax.set_title(title,fontsize=13,pad=20);ax.set_ylabel(unit);ax.grid(axis='y',alpha=.15);ax.spines[['top','right']].set_visible(False);ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'));ax.tick_params(labelsize=10)
 for x,v in zip([2024,2025],vals):ax.annotate(f'{v:,}{unit}',(x,v),xytext=(0,12),textcoords='offset points',ha='center',fontsize=11)
 ax.text(.5,.05,f"2024년 대비 {result['differences'][k]['percent']:+.1f}%",transform=ax.transAxes,ha='center',fontsize=10)
fig.text(.06,.04,'소방청 2025·2026 구급서비스 통계연보 부산 행. 출동·이송 통계이며 신고접수 표본과 합산하지 않음.\n과거 동별 신고 양상이 2025년 같은 동에서 지속됐다는 증거로 사용하지 않음.',fontsize=10,color='#56616a')
fig.tight_layout(rect=[.03,.15,1,.9]);fig.savefig(O/'current-ems-bridge.png',dpi=180);fig.savefig(O/'current-ems-bridge.svg');plt.close(fig)
print(json.dumps(result,ensure_ascii=False))
