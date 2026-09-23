import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from scipy.signal import find_peaks
R=Path(__file__).resolve().parents[1];r=json.loads((R/'qa/field_sr002_inference.json').read_text('utf8'));rows={v['id']:v for v in r['files']};O=R/'outputs/field-sr002';Q=R/'qa/field_sr002_details.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);pages=[]
boxes={128:(0,0,64,64),129:(45,20,76,54),132:(0,0,54,64),142:(0,28,64,58),147:(4,0,59,128),153:(66,0,126,52),161:(38,0,55,128),167:(0,220,94,256),265:(192,64,256,128),160:(0,0,64,64),188:(0,0,128,32)}
for n,box in boxes.items():
 gid=f'FM{n:04d}';v=rows[gid+'-wdn'];w=(box[2]-box[0])*8;h=(box[3]-box[1])*8;cw=max(w,260);canvas=Image.new('RGB',(cw*3,h+42),'#25313c');d=ImageDraw.Draw(canvas)
 for i,(path,label) in enumerate([(v['source'],'원본 8배'),(v['output'],'로컬 WDN'),(rows[gid+'-photo']['output'],'로컬 Photo')]):
  im=Image.open(path).convert('RGB').crop(box if i==0 else tuple(b*8 for b in box));im=im.resize((w,h),Image.Resampling.NEAREST) if i==0 else im;d.text((i*cw+4,4),gid+' '+label,font=font,fill='white');canvas.paste(im,(i*cw+(cw-w)//2,34))
 p=O/f'detail-{gid}.png';canvas.save(p);pages.append({'group_id':gid,'box_source':box,'scale':8,'path':str(p),'sha256':sha(p),'review_status':'pending'})
profiles=[]
for gid,axis,lo,hi,start,end,prom,dist in [('FM0128','x',12,50,1,58,12,3),('FM0129','y',56,69,25,44,10,2),('FM0132','y',12,40,8,54,8,2),('FM0142','x',35,48,0,64,4,1.5),('FM0147','y',10,50,0,128,6,3),('FM0153','y',80,115,7,43,10,2),('FM0161','y',43,49,0,128,6,3),('FM0265','y',203,250,66,125,10,3)]:
 data={'group_id':gid,'axis':axis,'band':[lo,hi],'range':[start,end],'prominence':prom,'minimum_distance':dist,'values':{}}
 for tag in ['source','wdn','photo']:
  v=rows[gid+'-wdn'];path=v['source'] if tag=='source' else rows[gid+'-'+tag]['output'];a=np.asarray(Image.open(path).convert('RGB'),float).mean(2);sc=1 if tag=='source' else 8;pr=a[lo*sc:hi*sc,start*sc:end*sc].mean(0) if axis=='x' else a[start*sc:end*sc,lo*sc:hi*sc].mean(1);peaks,props=find_peaks(-pr,distance=max(1,dist*sc),prominence=prom);data['values'][tag]={'count':len(peaks),'troughs_source_units':[(float(x)+.5)/sc+start for x in peaks],'profile_0_255':[float(x) for x in pr]}
 profiles.append(data);print(gid,{k:v['count'] for k,v in data['values'].items()})
Q.write_text(json.dumps({'pages':pages,'line_diagnostics':profiles,'diagnostic_limit':'Sampled luminance troughs are not physical bar counts or proof of preserved full geometry.'},ensure_ascii=False,indent=2),'utf8')
