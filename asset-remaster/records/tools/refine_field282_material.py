"""Remove stretched horizontal grain introduced by the first fixed-line recipe."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr004_plane282_v2.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
v=next(v for v in json.loads((R/'qa/field_sr004_planes.json').read_text('utf8'))['files'] if v['group_id']=='FM0282')
s=np.asarray(Image.open(v['source']).convert('RGBA'));p=np.asarray(Image.open(v['parent']).convert('RGBA'));old=np.asarray(Image.open(v['output']).convert('RGBA'));o=p.copy();mask=np.zeros(p.shape[:2],bool)
transfers=[[40,80,88,128],[472,512,424,464]]
for a,b,c,d in transfers:
 patch=p[:,c:d,:3].astype('float32');weight=np.minimum((np.arange(b-a)+.5)/4,1)
 if b<512:weight=np.minimum(weight,(b-a-np.arange(b-a)-.5)/4)
 o[:,a:b,:3]=np.rint(patch*weight[None,:,None]+p[:,a:b,:3]*(1-weight[None,:,None])).astype('uint8');mask[:,a:b]=True
profiles={}
for a,b in [(7,8),(61,64)]:
 profile=gaussian_filter1d(s[:,a:b,:3].mean(1).astype('float32'),1.2,axis=0,mode='nearest');profiles[str(a)]=profile.tolist();mat=cv2.resize(profile[:,None,:],(1,512),interpolation=cv2.INTER_LINEAR);o[:,a*8:b*8,:3]=np.rint(mat).astype('uint8')
expected=np.zeros((512,512),bool);expected[:,56:64]=True;expected[:,488:512]=True
assert np.array_equal(o[:,:,:3].mean(2)>80,expected) and np.array_equal(o[~mask],p[~mask])
O=R/'workspace/local-sr/field-sr004';ident='FM0282-source-fixed-planes-v2';op=O/(ident+'-8x.png');mp=O/(ident+'-mask.png');Image.fromarray(o).save(op);Image.fromarray(mask.astype('uint8')*255).save(mp)
row={**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','vector','vector_sha256','source_bright_boxes','editable_source_boxes']},'id':ident,'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'material_transfers_output_x':transfers,'transfer_edge_blend_output_pixels':4,'source_column_smoothing_sigma':1.2,'averaged_source_profiles':profiles,'method':'Original two vertical supports, source mean strip color smoothed along height. Nearby frozen WDN material patches fill correction bands with4-pixel edge blends, avoiding stretched per-row grain. No new neural inference.','diagnostic':v['diagnostic'],'outside_mask_parent_exact':True,'new_neural_passes':0,'runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for label,box in [('whole',(0,0,64,64)),('native',(0,16,32,48))]:
 w,h=(box[2]-box[0])*8,(box[3]-box[1])*8;cw=max(w+16,300);can=Image.new('RGB',(cw*3,h+44),'#26333f');draw=ImageDraw.Draw(can)
 for j,(a,title) in enumerate([(s,'원본 · 단순 확대'),(old,'좌표 고정 · 첫 수정'),(o,'좌표 유지 · 재질 연결 수정')]):
  im=Image.fromarray(a).crop(box).resize((w,h),Image.Resampling.NEAREST) if j==0 else Image.fromarray(a).crop(tuple(t*8 for t in box));draw.text((j*cw+6,5),title,font=font,fill='white');can.paste(im.convert('RGB'),(j*cw+6,36))
 path=R/'outputs/field-sr004'/('FM0282-v2-'+label+'.png');can.save(path);pages.append({'path':str(path),'sha256':sha(path),'source_box':list(box),'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-field-fixed-line-material/v2','basis':'The first correction copied one RGB value across each background row, creating horizontal ladder-like grain in the narrow correction bands. Preserve source-fixed support but transfer spatial local material instead.','previous_report_sha256':sha(R/'qa/field_sr004_planes.json'),'files':[row],'pages':pages,'new_neural_passes':0,'external_calls':0},ensure_ascii=False,indent=2),'utf8')
print('Created one improved material derivative and2 comparison pages.')
