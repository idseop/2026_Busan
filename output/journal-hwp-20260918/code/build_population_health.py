"""Population and health multipanel figures from verified aggregates only."""
from pathlib import Path
import csv, json, hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'figures'; META = BASE / 'metadata'
OUT.mkdir(parents=True, exist_ok=True); META.mkdir(parents=True, exist_ok=True)
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
TEAL, ORANGE, PURPLE = '#197C80', '#CA6A38', '#7D6B91'
INK, GRID = '#272B30', '#E8EBEC'
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':11.5,
                     'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,
                     'axes.unicode_minus':False,'svg.fonttype':'path',
                     'figure.facecolor':'white','savefig.facecolor':'white'})
POP = next((ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917').glob('08-*.csv'))
HEALTH = ROOT/'data/processed/신고보건심화-20260917/health-district-summary-2024.csv'

def read(path):
    return list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))

def provenance(paths):
    return [{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]

def csv_save(name,rows):
    with (META/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def clean(ax,grid=False):
    for side,sp in ax.spines.items():
        sp.set_visible(side in ('bottom','left'));sp.set_linewidth(.65);sp.set_color(INK)
    ax.tick_params(axis='both',labelsize=11,length=3,width=.65,pad=5)
    if grid:ax.grid(axis='x',color=GRID,lw=.65)
    ax.set_axisbelow(True)

def letter(fig,s,x,y):
    fig.text(x,y,s,fontsize=15,fontweight='bold',ha='left',va='top')

def save(fig,name,metadata):
    fig.canvas.draw();renderer=fig.canvas.get_renderer();b=fig.bbox
    bad=[]
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text():
            bb=t.get_window_extent(renderer)
            if bb.width and bb.height and (bb.x0<-.5 or bb.y0<-.5 or bb.x1>b.width+.5 or bb.y1>b.height+.5):bad.append(t.get_text())
    assert not bad,(name,bad)
    png=OUT/(name+'.png');svg=OUT/(name+'.svg')
    fig.savefig(png,dpi=500);fig.savefig(svg)
    im=Image.open(png)
    metadata.update({'created':'2026-09-18','figure_inches':[7.1,8.7],
                     'nominal_width_mm':180.34,'png_dpi':im.info.get('dpi'),'size_px':im.size,
                     'font':'Malgun Gothic','palette':[TEAL,ORANGE,PURPLE],
                     'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
                     'svg_sha256':hashlib.sha256(svg.read_bytes()).hexdigest(),
                     'text_outside_canvas':bad,'visual_review':'pending'})
    (META/(name+'.json')).write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    plt.close(fig)

# 04: exactly sum all 101 resident-age columns; 100 means age 100 and older.
pop=read(POP)
names=['다대제1동','다대제2동','금곡동','부전제1동','부전제2동']
residents=[];bins=[]
for name in names:
    r=next(r for r in pop if r['year']=='2024' and r['candidateName']==name)
    n=int(float(r['residentTotal']));ages=np.array([int(float(r[f'age_{a}'])) for a in range(101)])
    assert sum(ages)==n
    counts=np.array([sum(ages[i:i+5]) for i in range(0,100,5)]+[ages[100]])
    assert sum(counts)==n
    row={'candidate':name,'short_name':name.replace('제',''),'resident_total':n,
         'pct65plus':float(sum(ages[65:])/n*100),'pct75plus':float(sum(ages[75:])/n*100),
         'age_bins':counts/n*100}
    assert abs(row['pct65plus']-float(r['pct_65plus']))<1e-8
    residents.append(row)
    for i,value in enumerate(counts):
        bins.append({'candidate':name,'reference_date':'2024-12-31','age_band':f'{i*5}–{i*5+4}' if i<20 else '100+',
                     'count':int(value),'resident_total':n,'percent':float(value/n*100)})
residents.sort(key=lambda r:r['pct65plus'],reverse=True)
f=plt.figure(figsize=(7.1,8.7));letter(f,'a',.022,.979)
for i,r in enumerate(residents):
    ax=f.add_axes([.265,.858-i*.092,.69,.071])
    xx=np.arange(21);yy=r['age_bins']
    ax.fill_between(xx,0,yy,step='mid',color=TEAL,alpha=.18)
    ax.step(xx,yy,where='mid',color=TEAL,lw=1.45)
    ax.plot(xx,yy,'o',ms=2.2,color=TEAL)
    ax.set_xlim(-.5,20.5);ax.set_ylim(0,18)
    ax.set_yticks([0,15],['0%','15%'])
    ax.set_xticks([0,4,8,12,16,20])
    if i==4:
        ax.set_xticklabels(['0–4','20–24','40–44','60–64','80–84','100+'],fontsize=11)
        ax.set_xlabel('연령 (세)',fontsize=12,labelpad=8)
    else:ax.set_xticklabels([]);ax.tick_params(axis='x',length=0)
    clean(ax)
    ax.spines['left'].set_visible(False)
    ax.text(-.14,.52,f'{r["short_name"]}\nN={r["resident_total"]:,}',transform=ax.transAxes,
            ha='right',va='center',fontsize=11.5,linespacing=1.5)

letter(f,'b',.022,.401)
ax=f.add_axes([.265,.075,.69,.27]);ys=np.arange(5)[::-1]
for y,r in zip(ys,residents):
    lo=r['pct75plus'];hi=r['pct65plus']
    ax.plot([lo,hi],[y,y],color='#C6CDD1',lw=1.5,zorder=1)
    ax.scatter([hi],[y],marker='o',s=46,color=ORANGE,zorder=3)
    ax.scatter([lo],[y],marker='D',s=36,color=PURPLE,zorder=3)
    ax.annotate(f'{hi:.1f}',(hi,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=11.5,color=ORANGE)
    ax.annotate(f'{lo:.1f}',(lo,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=11.5,color=PURPLE)
ax.set_yticks(ys,[r['short_name'] for r in residents],fontsize=12)
ax.set_ylim(-.45,4.65);ax.set_xlim(0,35);ax.set_xticks([0,10,20,30])
ax.set_xlabel('주민 비중 (%)',fontsize=12,labelpad=8);clean(ax,True)
legend=[Line2D([],[],marker='o',linestyle='none',color=ORANGE,markersize=6,label='65세 이상'),
        Line2D([],[],marker='D',linestyle='none',color=PURPLE,markersize=6,label='75세 이상')]
ax.legend(handles=legend,loc='upper center',bbox_to_anchor=(.50,1.20),ncol=2,frameon=False,
          fontsize=11.5,columnspacing=1.4,handletextpad=.25)
csv_save('04-resident-age-bins.csv',bins)
summary=[{k:v for k,v in r.items() if k!='age_bins'} for r in residents]
csv_save('04-resident-age-summary.csv',summary)
save(f,'04-resident-age-profile',{
 'caption':'2024년 말 주민 행정동 후보 5개의 전체 연령 분포와 65세·75세 이상 비중. a: 5세 구간별 주민 비중, 마지막은 100세 이상. b: 65세 이상 비중 내림차순의 두 연령기준 비교. 두 패널의 동 순서를 일치시켰다.',
 'sources':provenance([POP]),'reference_date':'2024-12-31',
 'denominator':'각 행정동 후보의 주민등록인구 합계. N은 주민 총수이며 환자 또는 신고 당사자 수가 아님.',
 'bin_method':'원본 age_0~age_99를 5세씩 정확 합산. age_100은 100세 이상으로 별도 표시. 평활화·보간·가상분포 없음.',
 'warnings':['신고 원문 다대동·부전동을 개별 행정동에 강제 배분하지 않음.','두 연령기준의 비중은 중첩됨: 75세 이상은 65세 이상의 부분집합.','접수자·환자의 연령 또는 연평균·생활인구로 해석하지 않음.'],
 'checks':{'five_candidates':len(residents)==5,'each_101_ages_and_21_bins_sum_total':True,'65plus_matches_verified_csv':True},
 'summary':summary,'panels':{'a':'21구간 계단형 분포, 공통 y축 0–18%','b':'동일 순서의 65+ 및 75+ 점 연결; 신뢰구간이 아님'}})

# 05: align disease/region rows in two metric panels, preserve distinct x scales.
health=read(HEALTH)
groups=[('사하구','고혈압'),('북구','고혈압'),('사하구','당뇨병'),('북구','당뇨병')]
pairs=[]
for district,disease in groups:
    pairs.append([next(r for r in health if r['district']==district and r['indicator']==indicator)
                  for indicator in [f'{disease} 진단 경험자의 치료율_30',f'{disease} 관리교육 이수율_30']])
f=plt.figure(figsize=(7.1,8.7));letter(f,'a',.022,.974);letter(f,'b',.60,.974)
panel_specs=[(.27,.29,(85,101),[85,90,95,100],'치료율 (%)',TEAL,'o'),
             (.665,.29,(0,16),[0,5,10,15],'관리교육 이수율 (%)',ORANGE,'s')]
for j,(left,width,xlim,xticks,xlabel,color,marker) in enumerate(panel_specs):
    ax=f.add_axes([left,.495,width,.415])
    for i,pair in enumerate(pairs):
        r=pair[j];y=3-i;x,lo,hi=[float(r[k]) for k in ('estimate','lower_approx95','upper_approx95')]
        interval=ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt=marker,markersize=6.7,color=color,
                            capsize=3.5,elinewidth=1.2,lw=1.2)
        if j==0 and i==0:interval_handle=interval
        ax.annotate(f'{x:.1f}',(x,y),xytext=(0,11),textcoords='offset points',
                    ha='center',va='bottom',fontsize=12,color=color)
    ax.axhline(1.5,color=GRID,lw=.8)
    if j==0:
        ax.set_yticks([3,2,1,0],[f'{g[0]} · {g[1]}\n(n={pairs[i][0]["n"]})' for i,g in enumerate(groups)],fontsize=11.5)
    else:ax.set_yticks([3,2,1,0],[])
    ax.set_xlim(*xlim);ax.set_xticks(xticks);ax.set_ylim(-.55,3.65)
    ax.set_xlabel(xlabel,fontsize=12,labelpad=10);clean(ax)
    if j==1:ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)

f.legend([interval_handle],['근사 95% 구간'],loc='upper right',bbox_to_anchor=(.95,.978),
         frameon=False,fontsize=11.5,handlelength=2.8,handletextpad=.7)
letter(f,'c',.022,.377)
ax=f.add_axes([.27,.083,.685,.235]);unmet=[]
for i,district in enumerate(['북구','부산진구','사하구']):
    r=next(r for r in health if r['district']==district and r['indicator']=='연간 미충족의료율(병의원)')
    unmet.append(r);y=2-i;x,lo,hi=[float(r[k]) for k in ('estimate','lower_approx95','upper_approx95')]
    ax.errorbar(x,y,xerr=[[x-lo],[hi-x]],fmt='D',markersize=6.5,color=PURPLE,
                capsize=3.5,elinewidth=1.2)
    ax.annotate(f'{x:.1f}',(x,y),xytext=(0,10),textcoords='offset points',ha='center',va='bottom',fontsize=12,color=PURPLE)
ax.set_yticks([2,1,0],[f'{r["district"]}\n(n={r["n"]})' for r in unmet],fontsize=11.5)
ax.set_ylim(-.45,2.65);ax.set_xlim(0,20);ax.set_xticks([0,5,10,15,20])
ax.set_xlabel('연간 미충족의료율 · 병의원 (%)',fontsize=12,labelpad=10);clean(ax,True)
csv_save('05-health-paired-source.csv',[r for pair in pairs for r in pair]);csv_save('05-health-unmet-source.csv',unmet)
save(f,'05-health-profile',{
 'caption':'2024년 구 단위 건강조사 비교. a와 b는 같은 구·질환 행을 나란히 배치한 치료율 및 관리교육 이수율의 비교이며 c는 별도 분모의 연간 미충족의료율 비교다. 각 점은 가중 공표값, 가로선은 근사 95% 구간이다.',
 'sources':provenance([HEALTH]),'year':2024,
 'denominators':{'a_b':'30세 이상 해당 질환 진단 경험자; n은 비가중 표본 수. 치료·교육 공표값은 조사 가중비율.',
                 'c':'병의원 진료가 필요했던 응답자; n은 비가중 표본 수. 전체 주민·동·119 신고 당사자 분모가 아님.'},
 'ci_definition':'기존 검증 CSV의 estimate ± 1.96×SE로 계산된 근사 95% 구간. 0–100 범위 제한. 새 검정·공식 공표 신뢰구간으로 주장하지 않음.',
 'warnings':['a 치료율 축 85–101%, b 교육 이수율 축 0–16%, c 미충족의료율 축 0–20%로 범위가 다름.','a와 b의 차이를 미충족 수요나 같은 개인의 교육 미이수로 해석하지 않음.','교육 4개 추정치는 RSE 25% 이상으로 정밀도 주의.','구 조사값을 다대·금곡 주민 또는 신고 당사자의 건강 상태로 적용하지 않음.','2023/2024 공표표의 분모 문구 차이가 있어 2024 단면만 표시. 정책 효과나 구 간 차이의 유의성 검정은 수행하지 않음.'],
 'official_source':'https://chs.kdca.go.kr/chs/recsRoom/healthStatsMain.do',
 'data_rows':{'a_b':[r for pair in pairs for r in pair],'c':unmet},
 'checks':{'paired_rows_n_identical':all(p[0]['n']==p[1]['n'] for p in pairs),
           'all_rows_verified_csv':all(r in health for r in [z for p in pairs for z in p]+unmet)}})
print('Created 04-resident-age-profile and 05-health-profile PNG500dpi + SVG.')
