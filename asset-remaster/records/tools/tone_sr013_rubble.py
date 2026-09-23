"""Correct broad repaint colors without restoring coarse pixel noise over painted facets."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr013_rubble_tone.json'
if Q.exists():raise SystemExit('Existing tone revision.')
q=json.loads((R/'qa/local_sr013_gpt_rubble.json').read_text('utf8'));r=q['files'][0];src=Image.open(r['source']).convert('RGBA');parent=Image.open(r['output']).convert('RGBA');a=np.asarray(src,dtype=float);v=np.asarray(parent,dtype=float)
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(Path(r['output']).read_bytes())==r['output_sha256'];alpha=a[:,:,3:4]/255.;smooth=gaussian_filter(a[:,:,:3]*alpha,(1.5,1.5,0),mode='nearest')/np.maximum(gaussian_filter(alpha,(1.5,1.5,0),mode='nearest'),1e-6);vis=a[:,:,3]>0;near=distance_transform_edt(~vis,return_distances=False,return_indices=True);smooth[~vis]=smooth[near[0][~vis],near[1][~vis]];guide=np.asarray(Image.fromarray(np.rint(np.clip(smooth,0,255)).astype('uint8')).resize(parent.size,Image.Resampling.BICUBIC),dtype=float);w=v[:,:,3:4]/255.;low=gaussian_filter(v[:,:,:3]*w,(12.,12.,0),mode='nearest')/np.maximum(gaussian_filter(w,(12.,12.,0),mode='nearest'),1e-6)
O=Path(r['output']).parent;files=[]
for strength in [.55,.8]:
    rgb=np.rint(np.clip(v[:,:,:3]+strength*(guide-low),0,255)).astype('uint8');im=Image.fromarray(rgb).convert('RGBA');im.putalpha(parent.getchannel('A'));p=O/f'BM115-tone-{strength:.2f}.png';im.save(p);files.append({'id':f'BM115-tone-{strength:.2f}','group_id':'BM115','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'generated':r['generated'],'generated_sha256':r['generated_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(im.size),'method':'Low-frequency source color correction on the registered GPT repaint; original source alpha preserved','source_smoothing_sigma':1.5,'registered_smoothing_sigma':12.,'strength':strength,'new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for label,box in [('whole',(0,0,256,64)),('left',(0,0,64,64)),('middle',(64,0,128,64)),('right',(128,0,256,64))]:
    w=1024 if label=='whole' else 512;h=round(w*(box[3]-box[1])/(box[2]-box[0]));rh=h+60;s=Image.new('RGB',((w+20)*2,rh*2),'#293440');d=ImageDraw.Draw(s);ims=[(src,'원본 단순 확대'),(parent,'재그리기 · 위치 보정')]+[(Image.open(row['output']).convert('RGBA'),f'원본 전체 색조 반영 {row["strength"]}') for row in files]
    for i,(pic,title) in enumerate(ims):
        x=i%2*(w+20)+8;y=i//2*rh+8;d.text((x,y),title,font=font,fill='white');pic=pic.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',pic.size,'#72808b');bg.paste(pic,(0,0),pic);s.paste(bg,(x,y+34))
    p=R/f'outputs/sr013_rubble_tone_{label}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr013-rubble-tone/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'image_upload':False,'external_parent_repaint':True,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('Two broad-color corrections; 0 new model passes or generation calls.')
