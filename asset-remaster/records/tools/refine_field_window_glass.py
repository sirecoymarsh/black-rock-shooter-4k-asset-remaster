"""Remove old rounded-frame highlight residue from the new rectangular glass edges."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import label
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_windows003.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_windows002.json').read_text('utf8'));O=R/'workspace/local-sr/field-geometry001';files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in old['files']:
 gid=v['group_id'];s=Image.open(v['source']).convert('RGBA');original=np.asarray(Image.open(v['parent']).convert('RGBA'));parent=np.asarray(Image.open(v['output']).convert('RGBA'));out=parent.copy();classes=np.asarray(Image.open(v['classes']));pad=8
 for index,(a,b,c,d) in enumerate(v['plan']['panes'],1):
  crop=original[b*8:d*8,a*8:c*8,:3];inner=crop[pad:-pad,pad:-pad];assert inner.size;replacement=cv2.copyMakeBorder(inner,pad,pad,pad,pad,cv2.BORDER_REPLICATE);replacement=np.minimum(replacement,v['plan']['glass_max_rgb']);out[b*8:d*8,a*8:c*8,:3]=replacement
 assert np.array_equal(out[classes==0],parent[classes==0]);assert np.all(out[:,:,3]==255);x0,y0,x1,y1=v['plan']['outer'];test=out[y0*8:y1*8,x0*8:x1*8,:3].mean(2)<108;assert np.array_equal(test,classes[y0*8:y1*8,x0*8:x1*8]>0);assert label(test,np.ones((3,3)))[1]==len(v['plan']['panes'])
 op=O/f'{gid}-straight-windows-v3-clean-glass-8x.png';Image.fromarray(out,'RGBA').save(op);row={**v,'id':gid+'-straight-windows-v3-clean-glass','geometry_parent':v['output'],'geometry_parent_sha256':v['output_sha256'],'glass_inner_padding_output_px':pad,'glass_edge_method':'Extend the original local glass interior by8 output pixels (1source px) using nearest interior samples; retain core pixels and remove inherited curved bright frame fragments. Clip to previous glass ceiling.','output':str(op),'output_sha256':sha(op),'method':'Exact source-defined straight frame fromv2 +local glass interior with source1px edge extension; all geometry masks unchanged.','visual_review':'pending'};files.append(row)
 for kind,box in [('whole',(0,0,s.width,s.height)),('windows',(max(0,x0-2),max(0,y0-2),min(s.width,x1+2),min(s.height,y1+2)))]:
  ims=[s.crop(box).resize(((box[2]-box[0])*8,(box[3]-box[1])*8),Image.Resampling.NEAREST),Image.fromarray(original,'RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out,'RGBA').crop(tuple(t*8 for t in box))];ww,hh=ims[0].size;cw=max(ww+18,270);canvas=Image.new('RGB',(cw*3,hh+48),'#26333f');d=ImageDraw.Draw(canvas)
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','직선·직각 보정 v3'])):d.text((j*cw+6,8),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*cw+6,38))
  path=R/f'outputs/field-geometry001/windows-v3-{gid}-{kind}.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':list(box),'review_status':'pending'})
rep={'schema':'brs-straight-field-windows/v3','basis':'v2 class mask was rectangular, but old brighter rounded-frame fragments remained inside glass corners; class-mask success alone was insufficient visual evidence.','files':files,'pages':pages,'new_neural_passes':0,'image_upload':False,'limits':['The1-source-pixel glass edge band is material extrapolation, not recovered detail; core local glass pixels are retained subject to the recorded ceiling.','Geometric rectangles, frame material and outside-edit pixels are inherited exactly fromv2.','Native consumer/UV/runtime verification remains open.'],'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':2,'pages':4,'new_neural_passes':0}))
