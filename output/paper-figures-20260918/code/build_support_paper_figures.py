"""Clean 08–10 in two styles and add 2024-only verified health comparison 16."""
from pathlib import Path
import csv
import json
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parents[1]
META = BASE / 'support-metadata'
META.mkdir(parents=True, exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':13,
                     'axes.unicode_minus':False,'svg.fonttype':'path',
                     'figure.facecolor':'white','savefig.facecolor':'white'})
HEALTH = ROOT / 'data/processed/신고보건심화-20260917/health-district-summary-2024.csv'
YEARS = ROOT / 'data/processed/신고보건심화-20260917/health-same-indicators-2023-2024.csv'
PROPOSAL = ROOT / 'data/processed/신고보건심화-20260917/regional-improvement-and-evaluation.csv'
STYLES = {
 'A':{'folder':'01-clean-original','blue':'#168B8A','dark':'#17324D','orange':'#E89335'},
 'B':{'folder':'02-paper-style','blue':'#376C8A','dark':'#333333','orange':'#B97937'},
}
MANIFEST=[]

def read_csv(path):
    return list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))

def csv_out(name,rows):
    with (META/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def fig(height):
    return plt.figure(figsize=(180/25.4,height/25.4))

def save(figure,style,stem):
    folder=BASE/STYLES[style]['folder'];folder.mkdir(parents=True,exist_ok=True)
    figure.canvas.draw()
    renderer=figure.canvas.get_renderer()
    bounds=figure.bbox
    outside=[]
    for text in figure.findobj(matplotlib.text.Text):
        if not text.get_visible() or not text.get_text():continue
        bb=text.get_window_extent(renderer)
        if bb.width and bb.height and (bb.x0 < -.5 or bb.y0 < -.5 or bb.x1>bounds.width+.5 or bb.y1>bounds.height+.5):
            outside.append(text.get_text())
    if outside:raise ValueError(f'{stem}: text outside figure: {outside}')
    png=folder/(stem+'.png');svg=folder/(stem+'.svg')
    figure.savefig(png,dpi=450);figure.savefig(svg)
    im=Image.open(png)
    MANIFEST.append({'style':style,'stem':stem,'png':str(png.relative_to(BASE)),
                     'svg':str(svg.relative_to(BASE)),'size_px':im.size,
                     'dpi':im.info.get('dpi'),'width_mm':180,'outside_text':outside,
                     'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
    plt.close(figure)

def style_axis(ax,style):
    for name,spine in ax.spines.items():
        spine.set_visible(style=='B' and name in ('bottom','left'))
        spine.set_linewidth(.8);spine.set_color('#111111')
    ax.tick_params(labelsize=13,color='#111111',labelcolor=STYLES[style]['dark'],
                   length=4 if style=='B' else 0,pad=8,width=.8)
    ax.set_axisbelow(True)
    if style=='A':ax.grid(axis='x',linewidth=.65,color='#E4E9EC')

health=read_csv(HEALTH)
health_rows=[]
groups=[('사하구','고혈압'),('사하구','당뇨병'),('북구','고혈압'),('북구','당뇨병')]
for district,disease in groups:
    for ind in [f'{disease} 진단 경험자의 치료율_30',f'{disease} 관리교육 이수율_30']:
        health_rows.append(next(r for r in health if r['district']==district and r['indicator']==ind))
csv_out('08-health-source.csv',health_rows)

for style,palette in STYLES.items():
    f=fig(133);ax=f.add_axes([.29,.19,.67,.68]);ticks=[]
    for i,(district,disease) in enumerate(groups):
        yy=3-i
        for j,row in enumerate(health_rows[2*i:2*i+2]):
            x,lo,hi=[float(row[k]) for k in ('estimate','lower_approx95','upper_approx95')]
            y=yy+(.16 if j==0 else -.16)
            color=[palette['blue'],palette['orange']][j]
            ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt=['o','s'][j],markersize=7.5,
                        color=color,elinewidth=1.4,capsize=3,
                        label=['치료율','관리교육 이수율'][j] if i==0 else None)
            ax.annotate(f'{x:.1f}',(x if j==0 else hi,y),
                        xytext=(-6,12) if j==0 else (7,0),textcoords='offset points',
                        ha='right' if j==0 else 'left',va='center',fontsize=12.5,
                        color=color,weight='bold' if style=='A' else 'normal')
        ticks.append(f'{district} · {disease}\n(n={row["n"]})')
    ax.set_yticks([3,2,1,0],ticks);ax.set_xlim(0,105);ax.set_ylim(-.55,3.65)
    ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('가중 비율 (%)',fontsize=14,labelpad=12)
    style_axis(ax,style)
    ax.legend(loc='upper center',bbox_to_anchor=(.41,1.18),frameon=False,ncol=2,
              fontsize=12.5,columnspacing=1.2,handletextpad=.3)
    save(f,style,'08-health-treatment-education')

def diagram_canvas(height):
    f=fig(height);ax=f.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    return f,ax

def node(ax,style,x,y,w,h,text,color):
    fill='#F3F6F8' if style=='A' else 'white'
    radius=.018 if style=='A' else .002
    patch=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0,rounding_size={radius}',
                        facecolor=fill,edgecolor=color,linewidth=1.2 if style=='A' else .8)
    ax.add_patch(patch)
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=13,
            color=color,weight='bold' if style=='A' else 'normal',linespacing=1.65)

def arrow(ax,p,q,color,style):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle='-|>',mutation_scale=16,
                 linewidth=1.5 if style=='A' else 1.,color=color))

for style,p in STYLES.items():
    f,ax=diagram_canvas(55)
    xs=[.025,.275,.525,.775]
    texts=['기존 상담\n다대·금곡센터','연결 누락\n확인','교육 연계\n후보','시범 평가\n30일·90일']
    colors=[p['blue'],p['dark'],p['orange'],p['dark']]
    for x,text,color in zip(xs,texts,colors):node(ax,style,x,.22,.20,.56,text,color)
    for i in range(3):arrow(ax,(xs[i]+.205,.5),(xs[i+1]-.005,.5),p['dark'],style)
    save(f,style,'09-proposal-counselling-education-evaluation')
    f,ax=diagram_canvas(98)
    xy=[(.045,.60),(.57,.60),(.57,.115),(.045,.115)]
    texts=['조건·지역 선택','동별 상세 확인','분석 근거 확인','조건 변경·재비교']
    colors=[p['blue'],p['dark'],p['blue'],p['orange']]
    for (x,y),text,color in zip(xy,texts,colors):node(ax,style,x,y,.385,.275,text,color)
    for a,b in [((.44,.7375),(.56,.7375)),((.7625,.59),(.7625,.40)),
                ((.56,.2525),(.44,.2525)),((.2375,.40),(.2375,.59))]:
        arrow(ax,a,b,p['dark'],style)
    save(f,style,'10-web-exploration-cycle')

# The 2023/2024 published denominator wording differs. Do not draw a temporal trend.
year_rows=read_csv(YEARS)
unmet=[next(r for r in year_rows if r['year']=='2024' and r['district']==g
            and r['indicator']=='연간 미충족의료율(병의원)') for g in ['북구','부산진구','사하구']]
csv_out('16-unmet-healthcare-2024-source.csv',unmet)
f=fig(103);ax=f.add_axes([.225,.23,.71,.68]);p=STYLES['B']
for i,row in enumerate(unmet):
    y=2-i;x,lo,hi=[float(row[k]) for k in ('estimate','lower_approx95','upper_approx95')]
    ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt='o',markersize=8,color=p['blue'],
                elinewidth=1.4,capsize=4)
    ax.annotate(f'{x:.1f}',(x,y),xytext=(0,15),textcoords='offset points',
                ha='center',va='center',fontsize=12.5,color=p['dark'])
ax.set_yticks([2,1,0],[f'{r["district"]}\n(n={r["n"]})' for r in unmet])
ax.set_xlim(0,20);ax.set_ylim(-.48,2.60);ax.set_xticks([0,5,10,15,20])
ax.set_xlabel('연간 미충족의료율(병의원, %)',fontsize=14,labelpad=12)
style_axis(ax,'B');save(f,'B','16-unmet-healthcare-2024')

proposal_rows=[r for r in read_csv(PROPOSAL) if r['id'] in ('H1','H2')]
csv_out('09-proposal-source.csv',proposal_rows)
sources=[HEALTH,YEARS,PROPOSAL,ROOT/'web/final/index.html',ROOT/'web/final/assets/current-map.js',ROOT/'web/final/analysis/index.html']
manifest={'date':'2026-09-18','width_mm':180,'png_dpi':450,'font':'Malgun Gothic',
          'font_sizes_pt':{'tick':13,'axis':14,'legend':12.5,'value':12.5,'diagram_node':13},
          'palettes':STYLES,'sources':[{'path':str(x.relative_to(ROOT)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in sources],
          'figures':MANIFEST,'health_rows_exact':all(r in health for r in health_rows),
          'unmet_rows_exact':all(r in year_rows for r in unmet),'pdf_created':False}
(META/'support-figure-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':len(MANIFEST),'all_text_in_bounds':all(not x['outside_text'] for x in MANIFEST),
                  'pngs':[x['png'] for x in MANIFEST]},ensure_ascii=False,indent=2))
