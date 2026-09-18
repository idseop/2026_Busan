"""Reflow the existing verified heatmap to a 200 x 140 mm canvas."""
from pathlib import Path
import json, hashlib, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, colors
from matplotlib.patches import Rectangle
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
FIG=OUT/'figures';FIG.mkdir(parents=True,exist_ok=True)
source=ROOT/'output/paper-figures-20260918/core-01-07-metadata.json'
record=next(r for r in json.loads(source.read_text(encoding='utf-8'))['outputs']
            if r['set']=='01-clean-original' and r['file']=='06-dong-time-patterns')
rows=record['data'];a=np.array([r['hour4_share_pct'] for r in rows])
assert np.allclose(a.sum(axis=1),100)
assert [[f'{v:.1f}' for v in row] for row in a]==[
 ['11.0','12.3','22.4','19.1','17.6','17.5'],
 ['10.1','11.6','25.2','19.4','17.6','15.9'],
 ['16.2','10.9','13.5','19.9','18.9','20.7'],
 ['21.1','12.2','10.4','14.9','19.6','21.7']]
assert [f"{r['night_share_pct']:.1f}" for r in rows]==['40.9','37.7','47.8','55.1']
font_manager.fontManager.addfont('C:/Windows/Fonts/malgun.ttf')
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':14,'text.color':'#17324D',
 'axes.labelcolor':'#17324D','xtick.color':'#17324D','ytick.color':'#17324D',
 'axes.unicode_minus':False,'svg.fonttype':'path','figure.facecolor':'white','savefig.facecolor':'white'})
f=plt.figure(figsize=(200/25.4,140/25.4))
ax=f.add_axes([.145,.17,.69,.65])
cmap=colors.LinearSegmentedColormap.from_list('heat',['#F0F5F8','#168B8A'])
im=ax.imshow(a,aspect='auto',cmap=cmap,vmin=0,vmax=30)
ax.set_xticks(range(6),['00–04','04–08','08–12','12–16','16–20','20–24'])
ax.set_yticks(range(4),[r['dong']+'\n'+r['subtype'] for r in rows])
ax.set_xlabel('시간대 (시)',fontsize=14,labelpad=13)
ax.tick_params(axis='both',length=0,labelsize=14,pad=7)
for sp in ax.spines.values():sp.set_visible(False)
for i,row in enumerate(a):
 for j,v in enumerate(row):
  ax.text(j,i,f'{v:.1f}',ha='center',va='center',fontsize=14,color='white' if v>22 else '#17324D')
 ax.add_patch(Rectangle((np.argmax(row)-.475,i-.475),.95,.95,fill=False,ec='#E89335',lw=2))
cax=f.add_axes([.145,.947,.69,.018]);cb=f.colorbar(im,cax=cax,orientation='horizontal',ticks=[0,15,30])
cb.set_label('접수 비중 (%)',fontsize=14,labelpad=3);cb.ax.tick_params(labelsize=14,length=2,width=.8);cb.outline.set_visible(False)
side=f.add_axes([.865,.17,.115,.65]);side.set(xlim=(0,1),ylim=(3.5,-.5))
side.set_xticks([.5],['야간\n비중 (%)']);side.tick_params(axis='x',length=0,pad=7,labelsize=13.5);side.set_yticks([])
for sp in side.spines.values():sp.set_visible(False)
for i,r in enumerate(rows):side.text(.5,i,f"{r['night_share_pct']:.1f}",ha='center',va='center',fontsize=14.5,weight='bold')
f.canvas.draw();renderer=f.canvas.get_renderer();bad=[]
for t in f.findobj(matplotlib.text.Text):
 if not t.get_visible() or not t.get_text():continue
 b=t.get_window_extent(renderer)
 if b.width and b.height and (b.x0<0 or b.y0<0 or b.x1>f.bbox.width or b.y1>f.bbox.height):bad.append(t.get_text())
assert not bad,bad
name='01-time-heatmap-200x140mm'
f.savefig(FIG/(name+'.png'),dpi=500)
f.savefig(FIG/(name+'.svg'))
plt.close(f)
target=ROOT/'시간대별-접수비중-200mm.png'
shutil.copyfile(FIG/(name+'.png'),target)
with Image.open(target) as im:
 dpi=im.info['dpi'];size=im.size
 mm=[size[i]/dpi[i]*25.4 for i in range(2)]
 assert abs(mm[0]-200)<.06 and abs(mm[1]-140)<.06
meta={'status':'PASS','width_mm':200,'height_mm':140,'png_pixels':list(size),'dpi':list(dpi),
 'measured_png_mm':mm,'text_inside_canvas':True,'values_and_highlights_unchanged':True,
 'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'data':rows,'png_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(OUT/'resize-check.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in meta.items() if k not in ['data']},ensure_ascii=False,indent=2))
