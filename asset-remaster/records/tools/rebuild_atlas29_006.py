"""Explicit source-coordinate painted frame and panel reconstruction."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,cv2
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry006';V=R/'outputs/field-geometry006';Q=R/'qa/field_geometry006_atlas29_v1.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arr(p):return np.array(Image.open(p).convert('RGBA'))
v=next(v for v in json.loads((R/'qa/field_geometry005_material_v3.json').read_text('utf8'))['files'] if v['group_id']=='FM0029');s=arr(v['source']);p=arr(v['output']);parts=[];shapes=[];glass=[]
def poly(points,color,name):
 parts.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+'" fill="rgb('+','.join(str(int(x)) for x in color)+')"/>');shapes.append({'id':name,'points':points,'RGB':list(color)})
def rect(box,color,name):
 a,b,c,d=box;poly([[a,b],[c,b],[c,d],[a,d]],color,name)
def octagon(box,c=0):
 a,b,d,e=box
 return [[a+c,b],[d-c,b],[d,b+c],[d,e-c],[d-c,e],[a+c,e],[a,e-c],[a,b+c]] if c else [[a,b],[d,b],[d,e],[a,e]]
def ring(outer,inner,base,name):
 assert len(outer)==len(inner)
 for i in range(len(outer)):
  j=(i+1)%len(outer);a=np.array(outer[i]);b=np.array(outer[j]);edge=b-a;n=np.array([edge[1],-edge[0]],float);n/=max(np.linalg.norm(n),.01);light=np.dot(n,np.array([-.5,-.866]));gain=.89+.15*light;color=np.clip(np.array(base)*gain,0,255).astype(int).tolist();poly([outer[i],outer[j],inner[j],inner[i]],color,name+f'-face{i}')
def frame(name,outerbox,innerbox,chamfer=0,base=[114,55,41]):
 outer=octagon(outerbox,chamfer);inner=octagon(innerbox,max(0,chamfer-.6) if chamfer else 0);poly(outer,[52,36,32],name+'-shadow');ring(outer,inner,base,name);glass.append({'id':name,'inner_box':innerbox,'inner_polygon':inner})
rect([0,20,92,64],[114,55,41],'painted-body')
rect([0,20,92,21],[52,36,32],'window-header')
for box,col,name in [([10,21,29,44],[172,147,118],'left-trim'),([43,21,46,44],[172,147,118],'middle-trim'),([62,21,64,45],[172,147,118],'right-trim'),([74,21,92,45],[172,147,118],'small-window-base'),([75,23,91,44],[241,239,227],'small-window-cream'),([0,44,64,45],[172,147,118],'lower-sill-shadow'),([10,43,27,44],[241,239,227],'left-sill-light'),([43,23,45,44],[241,239,227],'center-strip-light'),([62,23,64,45],[241,239,227],'right-strip-light')]:rect(box,col,name)
frame('left-clipped',[-1,22,10,44],[0,23,8,42])
frame('small-left',[11,23,24,43],[13,25,22,41])
frame('large-left',[27,22,43,44],[29,24,41,42],2)
frame('large-right',[46,22,62,44],[48,24,60,42],2)
frame('small-right',[76,30,90,44],[78,32,88,42],2)
rect([64,22,73,64],[114,55,41],'narrow-frame');rect([73,22,75,64],[52,36,32],'narrow-right-shadow');glass.append({'id':'narrow','inner_box':[64,23,72,64],'inner_polygon':octagon([64,23,72,64])})
# Original separate lower panels, gold chamfers and the right trapezoid. No
# invented corner bolts; intentional slope is part of this atlas fragment.
for x in [10,25,27,42,46,61]:rect([x,45,x+1,64],[52,36,32],f'lower-joint-{x}')
for name,box in [('gold-left',[29,47,41,62]),('gold-right',[48,47,60,62])]:
 a,b,c,d=box;outer=octagon(box,2);inner=octagon([a+1,b+1,c-1,d-1],1.5);ring(outer,inner,[176,110,33],name);poly(inner,[114,55,41],name+'-center')
poly(octagon([13,49,23,60],1.5),[172,147,118],'plate-bevel');poly(octagon([14,50,22,59],1),[241,239,227],'plate-white')
right_outer=[[75,46],[91,46],[88,64],[75,64]];right_gold=[[76,47],[89.5,47],[87.1,62],[76,62]];right_inside=[[77,48],[88.4,48],[86.25,61],[77,61]];poly(right_outer,[52,36,32],'trapezoid-shadow');ring(right_outer,right_gold,[114,55,41],'trapezoid-outer');ring(right_gold,right_inside,[176,110,33],'trapezoid-gold');poly(right_inside,[114,55,41],'trapezoid-center')
vp=O/'FM0029-frame-panel-v1.svg';vp.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="512" viewBox="0 0 128 64">'+''.join(parts)+'</svg>','utf8');rp=O/'FM0029-frame-panel-v1-render.png';node='C:/Users/CadriacLord/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';subprocess.run([node,str(O/'render.cjs'),str(vp),str(rp)],check=True,capture_output=True);layer=arr(rp);out=p.copy();mask=layer[:,:,3]>0
# Reuse modest fine painted material from existing GPT draft, strictly inside
# fixed geometry. Edge contrast belongs to the geometric faces, not to grain.
gp=R/'workspace/gpt-trials/FM0029-v1/generated-raw.png';gen=np.array(Image.open(gp).convert('RGBA').resize((1024,512),Image.Resampling.LANCZOS));grain=gen[:,:,:3].astype('float32')-gaussian_filter(gen[:,:,:3].astype('float32'),(2,2,0),mode='nearest');layer[:,:,:3]=np.rint(np.clip(layer[:,:,:3].astype('float32')+2*np.tanh(grain*.2/2),0,255)).astype('uint8');out[mask]=layer[mask];out[:,:,3]=p[:,:,3]
# Restore the existing tone-matched glass only within authored inner polygons.
glass_masks=[]
for z in glass:
 m=np.zeros((512,1024),np.uint8);cv2.fillConvexPoly(m,np.rint(np.array(z['inner_polygon'])*8*16).astype('int32'),255,shift=4);a,b,c,d=[int(t*8) for t in z['inner_box']];clip=np.zeros_like(m);clip[b:d,a:c]=255;m=cv2.bitwise_and(m,clip)>0;out[m]=p[m];glass_masks.append({'id':z['id'],'output_pixels':int(m.sum())})
# Preserve the intentionally cropped round fitting and source-authored small
# hinge blocks, rather than generative bolts. This is an explicit source layer.
out[54*8:61*8,:5*8]=p[54*8:61*8,:5*8]
nn=np.repeat(np.repeat(s,8,0),8,1);detailmask=np.zeros((64,128),bool)
for a,b,c,d in [[9,45,13,64],[24,45,29,64]]:
 rgb=s[b:d,a:c,:3];valid=np.all(rgb==[52,36,32],axis=2)|np.all(rgb==[172,147,118],axis=2);detailmask[b:d,a:c]|=valid
dm=np.repeat(np.repeat(detailmask,8,0),8,1);out[dm]=nn[dm];assert np.array_equal(out[~mask],p[~mask]);assert np.array_equal(out[:,:,3],p[:,:,3]);op=O/'FM0029-frame-panel-v1-8x.png';mp=O/'FM0029-frame-panel-v1-mask.png';Image.fromarray(out).save(op);Image.fromarray(mask.astype('uint8')*255).save(mp)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for name,box in [('whole',[0,0,128,64]),('windows',[10,20,64,45]),('panels',[8,44,92,64]),('small-and-sloped',[74,20,92,64])]:
 a,b,c,d=box;ww,hh=(c-a)*8,(d-b)*8;scale=min(1,640/ww,512/hh);sw,sh=round(ww*scale),round(hh*scale);cw=max(320,sw+16);can=Image.new('RGB',(cw*3,sh+44),'#26333f');draw=ImageDraw.Draw(can)
 for j,(im,title) in enumerate([(Image.fromarray(s).crop(box).resize((ww,hh),Image.Resampling.NEAREST),'원본 · 단순 확대'),(Image.fromarray(p).crop(tuple(t*8 for t in box)),'유리 수정 뒤 기존 틀'),(Image.fromarray(out).crop(tuple(t*8 for t in box)),'원본 좌표로 틀·패널 수정')]):
  im=im.resize((sw,sh),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);draw.text((j*cw+6,4),title,font=font,fill='white');m=Image.new('RGB',(sw,sh),'#252d35');m.paste(im,(0,0),im);can.paste(m,(j*cw+6,35))
 pp=V/('FM0029-'+name+'-v1.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-source-painted-frame-atlas/v1','file':{**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':'FM0029-frame-panel-v1','parent':v['output'],'parent_sha256':sha(v['output']),'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'vector':str(vp),'vector_sha256':sha(vp),'render':str(rp),'render_sha256':sha(rp),'generated_material':str(gp),'generated_material_sha256':sha(gp),'shapes':shapes,'glass':glass,'glass_masks':glass_masks,'outside_mask_parent_RGBA_exact':True,'alpha_parent_exact':True,'method':'Source-position straight/chamfered frame rings and lower painted/gold panels, source sloped right panel, existing glass restored inside inner polygons, bounded previously generated fine material.','limitation':'Top-left mechanical fragment and small source fitting retained from prior local draft; whole-atlas acceptance requires inspection, not assumed from frame geometry.','visual_review':'pending','runtime_verified':False,'release_eligible':False},'pages':pages,'new_local_inference_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({'output':str(op),'shape_count':len(shapes),'pages':len(pages)}))
