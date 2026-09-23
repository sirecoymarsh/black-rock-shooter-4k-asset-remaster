"""Source-defined flat border faces, retaining the local surface interior."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,cv2
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_sr005_geometry502.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((R/'qa/field_sr005_inference.json').read_text('utf8'));v=next(z for z in b['files'] if z['id']=='FM0502-photo');s=np.asarray(Image.open(v['source']).convert('RGBA'));parent=np.asarray(Image.open(v['output']).convert('RGBA'));out=parent.copy();O=R/'workspace/local-sr/field-sr005'
# The source's strip boundaries are fixed. Profiles only vary along each strip.
top=gaussian_filter1d(s[:5,:,:3].astype('float32'),.6,axis=1,mode='nearest')
bottom=gaussian_filter1d(s[30:,:,:3].astype('float32'),.6,axis=1,mode='nearest')
left=gaussian_filter1d(s[:,0:2,:3].astype('float32'),.6,axis=0,mode='nearest')
right=gaussian_filter1d(s[:,126:128,:3].astype('float32'),.6,axis=0,mode='nearest')
for profile,y0 in [(top,0),(bottom,30)]:
 for j,row in enumerate(profile):
  along=cv2.resize(row[None,:,:],(1024,1),interpolation=cv2.INTER_LINEAR)[0];out[(y0+j)*8:(y0+j+1)*8,:,:3]=np.rint(along).astype('uint8')[None,:,:]
for profile,x0 in [(left,0),(right,126)]:
 for j in range(2):
  along=cv2.resize(profile[:,j:j+1,:],(1,256),interpolation=cv2.INTER_LINEAR)[:,0,:];out[40:240,(x0+j)*8:(x0+j+1)*8,:3]=np.rint(along[40:240]).astype('uint8')[:,None,:]
rects=[[0,0,128,5],[0,30,128,2],[0,5,2,25],[126,5,2,25]]
vp=O/'FM0502-fixed-border.svg';vp.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="256" viewBox="0 0 128 32">'+''.join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>' for x,y,w,h in rects)+'</svg>','utf8')
mp=O/'FM0502-fixed-border-mask.png';subprocess.run([r'C:\Users\CadriacLord\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe',str(R/'workspace/local-sr/field-geometry006/render.cjs'),str(vp),str(mp)],check=True)
mask=np.asarray(Image.open(mp).convert('RGBA'))[:,:,3]>0;assert np.array_equal(out[~mask],parent[~mask]);assert np.array_equal(out[:,:,3],parent[:,:,3]);op=O/'FM0502-source-fixed-border-8x.png';Image.fromarray(out,'RGBA').save(op)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for tag,box in [('whole',(0,0,128,32)),('native',(44,0,76,32)),('corner',(0,0,32,32))]:
 can=Image.new('RGB',(1050,390),'#25313c');d=ImageDraw.Draw(can)
 for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(parent,'로컬 Photo'),(out,'원본 띠·외곽선 고정')]):
  im=Image.fromarray(a).crop(box if col==0 else tuple(t*8 for t in box));scale=min(320/im.width,320/im.height) if tag=='whole' else 8 if col==0 else 1;pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),'FM0502 '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,45+(320-pic.height)//2))
 pp=R/f'outputs/field-sr005/FM0502-fixed-{tag}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending_final_review'})
data={'schema':'brs-source-border-reconstruction/v1','id':'FM0502-source-fixed-border','group_id':'FM0502',**{k:v[k] for k in ['source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'parent':v['output'],'parent_sha256':v['output_sha256'],'parent_report_sha256':sha(R/'qa/field_sr005_inference.json'),'output':str(op),'output_sha256':sha(op),'vector':str(vp),'vector_sha256':sha(vp),'mask':str(mp),'mask_sha256':sha(mp),'rectangles_xywh_source':rects,'source_profile_sigma':.6,'method':'Source row/column color profiles on fixed axis-aligned strip rectangles; local Photo surface retained outside the strip mask. This is deterministic geometry correction, not another neural inference.','local_inference_passes':0,'external_calls':0,'output_size':[1024,256],'pages':pages,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8');print('Border reconstruction and3 comparison pages saved.')
