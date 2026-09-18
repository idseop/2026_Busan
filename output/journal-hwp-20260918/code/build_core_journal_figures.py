"""Two integrated figures; re-expression of validated aggregates, no raw119 processing."""
from pathlib import Path
import csv, json, hashlib, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors, ticker
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from matplotlib.lines import Line2D
from shapely.geometry import shape
from shapely.ops import transform

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/journal-hwp-20260918'
FIG=OUT/'figures'; META=OUT/'metadata'
FIG.mkdir(parents=True,exist_ok=True);META.mkdir(exist_ok=True)
BASE=ROOT/'data/processed/5개년통합-지역유형-제안연결-20260917'
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':['Arial','Malgun Gothic'],'font.size':11,
 'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11,'legend.fontsize':11,
 'axes.linewidth':.65,'axes.edgecolor':'#333333','axes.labelcolor':'#222222',
 'text.color':'#222222','xtick.color':'#333333','ytick.color':'#333333',
 'axes.unicode_minus':False,'svg.fonttype':'path','figure.facecolor':'white',
 'savefig.facecolor':'white'})
TEAL='#197C80'; ORANGE='#CA6A38'; PURPLE='#7D6B91'; GRAY='#91999D'
sources={};checks=[]; records=[]
def read(p):
 sources[p.relative_to(ROOT).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def ck(s,v):
 checks.append({'check':s,'pass':bool(v)})
 assert v,s
def style(a,grid='x'):
 a.spines[['top','right']].set_visible(False)
 a.tick_params(width=.65,length=3,pad=4)
 if grid:a.grid(axis=grid,color='#E5E8E8',lw=.45);a.set_axisbelow(True)
def panel(f,s,x,y):f.text(x,y,s,fontsize=13,fontweight='bold',ha='left',va='top')
def save(f,name,data,definition):
 ck(name+' no titles',all(not a.get_title() for a in f.axes))
 ck(name+' figure labels only',all(t.get_text() in ['a','b','c'] for t in f.texts))
 f.canvas.draw()
 f.savefig(FIG/(name+'.png'),dpi=500)
 f.savefig(FIG/(name+'.svg'))
 display=META/(name+'-display-data.json')
 display.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 records.append({'id':name,'display_data':display.relative_to(OUT).as_posix(),
   'transformation':definition,'files':{ext:{'path':(FIG/(name+'.'+ext)).relative_to(OUT).as_posix(),
   'sha256':hashlib.sha256((FIG/(name+'.'+ext)).read_bytes()).hexdigest()} for ext in ['png','svg']}})
 plt.close(f)

district=read(next(BASE.glob('01-*.csv')))
district=sorted(district,key=lambda r:-int(r['countP']))
types=read(next(BASE.glob('02-*.csv')))
dt=read(next(BASE.glob('03-*.csv')))
dong=read(next(BASE.glob('07-*.csv')))
ck('16 district total P',sum(int(x['countP']) for x in district)==555786)
ck('70 type total P',sum(int(x['countP']) for x in types)==555786)
district_names=[x['district'] for x in district]
bydistrict={x['district']:x for x in district}
lookup={(x['district'],x['type'],x['subtype']):x for x in dt}
selected=sorted(types,key=lambda x:-int(x['countP']))[:6]
matrix=[];display=[]
for d in district:
 row=[]
 for t in selected:
  cell=lookup[(d['district'],t['type'],t['subtype'])]
  n=int(cell['countP']);den=int(d['countP']);city_n=int(t['countP'])
  ck('denom '+d['district']+t['subtype'],int(cell['districtDenominator'])==den)
  lq=(n/den)/(city_n/555786);log=math.log2(lq)
  row.append(log);display.append({'district':d['district'],'type':t['type'],'subtype':t['subtype'],
   'count':n,'district_total':den,'city_type_count':city_n,'city_total':555786,
   'district_share_pct':100*n/den,'city_share_pct':100*city_n/555786,'location_quotient':lq,'log2_location_quotient':log})
 matrix.append(row)
matrix=np.asarray(matrix)
geo_path=ROOT/'web/data/busan-districts.geojson'
sources[geo_path.relative_to(ROOT).as_posix()]=hashlib.sha256(geo_path.read_bytes()).hexdigest()
geo=json.loads(geo_path.read_text('utf-8'))
ck('map CRS explicit',geo['metadata']['outputCrs']=='EPSG:4326')
ck('map district exact match',{x['properties']['name'] for x in geo['features']}==set(district_names))
def project(lon,lat,z=None):
 # EPSG:3857 spherical Web Mercator; display only, never distance/area analysis.
 lon=np.asarray(lon);lat=np.asarray(lat)
 return 6378137*np.deg2rad(lon),6378137*np.log(np.tan(np.pi/4+np.deg2rad(lat)/2))
geometries={x['properties']['name']:transform(project,shape(x['geometry'])) for x in geo['features']}
ck('map geometries valid',all(g.is_valid for g in geometries.values()))

# 01: spatial counts, ordered counts, and composition specialization.
f=plt.figure(figsize=(180/25.4,221/25.4))
am=f.add_axes([.035,.61,.43,.35]); ad=f.add_axes([.665,.61,.295,.35])
ah=f.add_axes([.17,.16,.78,.36]); cb=f.add_axes([.31,.065,.51,.014])
panel(f,'a',.015,.984);panel(f,'b',.515,.984);panel(f,'c',.015,.545)
seq=colors.LinearSegmentedColormap.from_list('counts',['#E6EFEF',TEAL])
norm=colors.Normalize(0,65000)
for name,g in geometries.items():
 for poly in (list(g.geoms) if g.geom_type=='MultiPolygon' else [g]):
  vertices=[];codes=[]
  for ring in [poly.exterior,*poly.interiors]:
   coords=list(ring.coords);vertices.extend(coords)
   codes.extend([MplPath.MOVETO]+[MplPath.LINETO]*(len(coords)-2)+[MplPath.CLOSEPOLY])
  am.add_patch(PathPatch(MplPath(vertices,codes),facecolor='#F3F5F4',edgecolor='#CBD2D2',lw=.45))
for name,g in geometries.items():
 p=g.representative_point();am.scatter(p.x,p.y,s=int(bydistrict[name]['countP'])/300,facecolor=TEAL,alpha=.70,edgecolor='white',linewidth=.6,zorder=3)
for name,off in {'부산진구':(11500,-5500),'해운대구':(9000,6500),'사하구':(-5000,-7000),'사상구':(-14000,3000),'북구':(-8000,6500)}.items():
 p=geometries[name].representative_point();am.annotate(name,(p.x,p.y),xytext=(p.x+off[0],p.y+off[1]),fontsize=11,ha='center',va='center',
  color='#202627',bbox={'facecolor':'white','edgecolor':'none','pad':.7,'alpha':.86},
  arrowprops={'arrowstyle':'-','lw':.5,'color':'#666666'})
am.autoscale_view();am.set_aspect('equal');am.margins(.035);am.axis('off')
handles=[Line2D([],[],marker='o',lw=0,markersize=np.sqrt(n/300),markerfacecolor=TEAL,markeredgecolor='white',alpha=.70,label=f'{n//10000}만 건') for n in [20000,40000,60000]]
am.legend(handles=handles,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.02),frameon=False,handletextpad=.35,columnspacing=.9,borderpad=.2)
ys=np.arange(16);vals=np.array([int(x['countP']) for x in district])
ad.hlines(ys,0,vals,color='#D8DFDF',lw=.7);ad.scatter(vals,ys,s=22,c=TEAL,zorder=3)
for y,v in zip(ys,vals):ad.annotate(f'{v:,}',(v,y),xytext=(5,0),textcoords='offset points',fontsize=11,va='center')
ad.set(yticks=ys,yticklabels=district_names,xlim=(0,85000),ylim=(15.5,-.5),xlabel='접수 건수 (만 건)')
ad.set_xticks([0,30000,60000]);ad.set_xticklabels(['0','3','6']);style(ad)
limit=math.ceil(np.abs(matrix).max()*10)/10
div=colors.LinearSegmentedColormap.from_list('specialization',[PURPLE,'#FBFBFA',ORANGE])
im=ah.imshow(matrix,cmap=div,norm=colors.TwoSlopeNorm(vmin=-limit,vcenter=0,vmax=limit),aspect='auto',interpolation='none')
ah.set_yticks(ys,district_names);ah.set_xticks(np.arange(6),[x['subtype'].replace('화재확인출동','화재확인\n출동')+'\n'+x['type'] for x in selected]);ah.tick_params(length=0,pad=5)
for i in range(16):
 for j in range(6):
  val=matrix[i,j];label='0.00' if abs(val)<.005 else f'{val:+.2f}';ah.text(j,i,label,ha='center',va='center',fontsize=11,color='white' if abs(val)>limit*.70 else '#303030')
ah.set_xticks(np.arange(-.5,6,1),minor=True);ah.set_yticks(np.arange(-.5,16,1),minor=True);ah.grid(which='minor',color='white',linewidth=.8);ah.tick_params(which='minor',length=0)
for sp in ah.spines.values():sp.set_visible(False)
hcb=f.colorbar(im,cax=cb,orientation='horizontal');hcb.set_ticks([-limit,0,limit]);hcb.set_label('log₂(구·군 유형 비중 / 부산 유형 비중)',labelpad=2,fontsize=11);hcb.outline.set_linewidth(.5)
save(f,'01-city-spatial-specialization',{'district_counts':district,'matrix_cells':display,'selected_types':selected,'geometry_metadata':geo['metadata']},
 {'scope':'2020–2024 P: selected17 complete, normal processing, exclude business records and bee removal; 555786 receipts',
  'a':'2025-06-30 neutral reference district boundaries, EPSG4326 converted by spherical Web Mercator formula to EPSG3857 for display only. Symbol AREA proportional to count at representative point; not receipt location. Historical district boundaries differ (2020 Geumjeong/Haeundae change), so no choropleth or historical boundary reaggregation. No distance/area analysis.',
  'b':'district receipt counts, descending; not risk ranking',
  'c':'six types selected by Busan total counts; log2((district subtype count / district all receipts)/(Busan subtype count/555786)); 0=equal composition, +1=2x, -1=0.5x; descriptive composition, not relative individual risk',
  'uncertainty':'No inferential interval or significance test. Counts are records, not unique patients.'})

# 02: selected raw-dong size/composition, paired district reference, pp difference.
dr=[x for x in dong if x['type']=='구급' and x['subtype']=='질병']
ck('15 selected disease dongs',len(dr)==15 and len({(x['district'],x['rawDong']) for x in dr})==15)
dr=sorted(dr,key=lambda x:(district_names.index(x['district']),-int(x['countP'])))
for r in dr:
 gu=lookup[(r['district'],'구급','질병')]
 r['districtDiseaseCount']=int(gu['countP']);r['districtTotal']=int(gu['districtDenominator']);r['districtDiseaseShare']=100*int(gu['countP'])/int(gu['districtDenominator'])
 r['dongDiseaseShare']=100*int(r['countP'])/int(r['regionTotalP']);r['differencePercentagePoints']=r['dongDiseaseShare']-r['districtDiseaseShare']
 ck('dong share '+r['district']+r['rawDong'],abs(r['dongDiseaseShare']-float(r['shareRegionPct']))<1e-9)
 r['districtRestShare']=100*(r['districtDiseaseCount']-int(r['countP']))/(r['districtTotal']-int(r['regionTotalP']))
 ck('rest district '+r['rawDong'],abs(r['districtRestShare']-float(r['restDistrictSharePct']))<1e-9)
def col(r):return TEAL if r['rawDong']=='다대동' else ORANGE if r['rawDong']=='금곡동' else GRAY
f=plt.figure(figsize=(180/25.4,221/25.4))
aa=f.add_axes([.13,.60,.83,.34]);ab=f.add_axes([.29,.115,.335,.345]);ac=f.add_axes([.75,.115,.22,.345])
panel(f,'a',.015,.97);panel(f,'b',.015,.51);panel(f,'c',.69,.51)
cityshare=190682/555786*100
aa.axhline(cityshare,color=PURPLE,lw=.9,ls=(0,(3,3)),zorder=1)
offsets={'부전동':(0,-17),'개금동':(-20,12),'전포동':(-32,-18),'우동':(4,-18),'좌동':(5,-17),'반여동':(3,12),'다대동':(6,8),'괴정동':(0,18),'하단동':(18,-7),'모라동':(-22,11),'괘법동':(8,10),'주례동':(-26,11),'금곡동':(0,12),'구포동':(7,-16),'화명동':(5,10)}
for r in dr:
 focus=r['rawDong'] in ['다대동','금곡동'];x=int(r['countP']);y=r['dongDiseaseShare']
 aa.scatter(x,y,s=76 if focus else 38,c=col(r),edgecolors='white',linewidth=.6,zorder=4)
 dx,dy=offsets[r['rawDong']]
 aa.annotate(r['rawDong'],(x,y),xytext=(dx,dy),textcoords='offset points',fontsize=11,
  ha='left' if dx>0 else 'right' if dx<0 else 'center',fontweight='bold' if focus else 'normal',color=col(r) if focus else '#454B4C',
  arrowprops={'arrowstyle':'-','lw':.45,'color':'#ABB2B3'} if abs(dx)+abs(dy)>25 else None)
aa.set(xlim=(2100,4380),ylim=(26.7,41.1),xlabel='동별 질병 접수 (건)',ylabel='동 내 질병 비중 (%)')
aa.set_xticks([2500,3000,3500,4000]);aa.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'));aa.set_yticks([28,32,36,40]);style(aa,'y')
aa.legend(handles=[Line2D([],[],marker='o',lw=0,color=TEAL,label='다대동'),Line2D([],[],marker='o',lw=0,color=ORANGE,label='금곡동'),Line2D([],[],marker='o',lw=0,color=GRAY,label='비교 동'),Line2D([],[],lw=1,ls='--',color=PURPLE,label='부산 전체')],
 loc='lower center',bbox_to_anchor=(.51,1.035),ncol=4,frameon=False,handletextpad=.4,columnspacing=1.0)
y=np.arange(15)
for k,r in enumerate(dr):
 a=r['districtDiseaseShare'];b=r['dongDiseaseShare'];delta=r['differencePercentagePoints'];c=col(r)
 ab.plot([a,b],[k,k],color=c,lw=1.2,zorder=2)
 ab.scatter(a,k,s=34,facecolor='white',edgecolor=PURPLE,lw=1.05,zorder=3)
 ab.scatter(b,k,s=42,color=c,edgecolor='white',lw=.45,zorder=4)
 ac.hlines(k,0,delta,color=c,lw=1.0);ac.scatter(delta,k,color=c,s=35,zorder=4)
 ac.annotate(f'{delta:+.2f}',(delta,k),xytext=(5 if delta>=0 else -5,0),textcoords='offset points',va='center',ha='left' if delta>=0 else 'right',fontsize=11,color=c if r['rawDong'] in ['다대동','금곡동'] else '#454B4C')
for ax in [ab,ac]:
 for sep in [2.5,5.5,8.5,11.5]:ax.axhline(sep,color='#DCE0E0',lw=.5)
 ax.set_ylim(14.7,-.7);style(ax)
ab.set(yticks=y,yticklabels=[r['district']+' '+r['rawDong'] for r in dr],xlim=(26,41.5),xlabel='질병 비중 (%)')
ab.set_xticks([28,34,40]);ab.tick_params(axis='y',length=0,pad=8)
ab.legend(handles=[Line2D([],[],marker='o',lw=0,markerfacecolor='white',markeredgecolor=PURPLE,label='구 전체'),Line2D([],[],marker='o',lw=0,color=GRAY,label='원문동')],
 loc='lower center',bbox_to_anchor=(.45,1.01),ncol=2,frameon=False,columnspacing=.7,handletextpad=.3)
ac.set(yticks=y,yticklabels=[],xlim=(-8.5,6.7),xlabel='동 − 구 차이 (%p)');ac.set_xticks([-5,0,5]);ac.tick_params(axis='y',length=0);ac.axvline(0,color='#555555',lw=.65)
save(f,'02-district-dong-disease-continuity',{'city_disease_share_pct':cityshare,'selected_dongs':dr},
 {'scope':'2020–2024 P; disease only. 15 raw-name dongs: the existing selected top3 disease-count dongs within each top5 total-count district, not all Busan dongs.',
  'a':'x=dong disease receipt count; y=dong disease count/dong all P receipt count*100; reference line=city disease count/city all P count*100',
  'b':'open point=district disease count/district all P count*100; filled point=dong share; district reference includes the displayed dong',
  'c':'dong percentage minus its whole-district percentage, percentage points; descriptive paired comparison, not a statistical effect or significance test',
  'spatial_unit':'rawDong is report raw place-name unit; no redistribution to administrative dong population candidates',
  'uncertainty':'No confidence intervals. Cases selected from existing analysis; cannot infer all-dong distribution, patients, causation or service gap.'})
payload={'date':'2026-09-18','creator':'core_evidence','size_mm':[180,221],'png_dpi':500,'fonts':{'tick':11,'label':12,'value':11,'panel':13},
 'palette':{'teal':TEAL,'orange':ORANGE,'purple':PURPLE,'dadae':TEAL,'geumgok':ORANGE},'sources':sources,'checks':checks,'figures':records,'status':'PASS'}
(META/'01-02-core-journal-metadata.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'figures':[x['id'] for x in records],'checks':len(checks),'status':'PASS'},ensure_ascii=False))
