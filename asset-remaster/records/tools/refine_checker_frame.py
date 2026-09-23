"""Reduce speculative frame material while keeping checker pixels exact."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];q=json.loads((R/'qa/checker_fidelity_v1.json').read_text('utf8'))
row=next(r for r in q['files'] if r['id']=='BM221-wdn-protected')
src=Image.open(row['source']).convert('RGBA');parent=Image.open(row['output']).convert('RGBA');clean=Image.open(row['cleanplate']).convert('RGBA');mask=np.asarray(Image.open(row['mask']).convert('L'))>0;m8=np.repeat(np.repeat(mask,8,0),8,1);nn=np.asarray(src.resize(parent.size,Image.Resampling.NEAREST))
v=np.asarray(parent,dtype=np.float32);a=v[:,:,3:4]/255.;low=gaussian_filter(v[:,:,:3]*a,(6.,6.,0),mode='nearest')/np.maximum(gaussian_filter(a,(6.,6.,0),mode='nearest'),1e-6)
# Cleanplate target avoids restoring soft checker-color bleed into the surrounding material.
c=np.asarray(clean,dtype=np.float32);wa=c[:,:,3:4]/255.;p=gaussian_filter(c[:,:,:3]*wa,(.25,.25,0),mode='nearest')/np.maximum(gaussian_filter(wa,(.25,.25,0),mode='nearest'),1e-6)
target=np.asarray(Image.fromarray(np.rint(np.clip(p,0,255)).astype('uint8')).resize(parent.size,Image.Resampling.BILINEAR),dtype=np.float32)
records=[]
for weight in [.35,.6]:
    b=v.copy();b[:,:,:3]=np.clip(target+weight*(v[:,:,:3]-low),0,255);b=np.rint(b).astype('uint8');b[m8]=nn[m8];out=Image.fromarray(b);path=Path(row['output']).with_name(f'BM221-wdn-guided-{weight:.2f}-protected8x.png');out.save(path)
    assert np.array_equal(b[m8],nn[m8]) and out.getchannel('A').tobytes()==parent.getchannel('A').tobytes()
    records.append({'id':f'BM221-wdn-guided-{weight:.2f}','group_id':'BM221','source':row['source'],'source_rgba_sha256':row['source_rgba_sha256'],'parent':row['output'],'parent_sha256':row['output_sha256'],'cleanplate':row['cleanplate'],'cleanplate_sha256':row['cleanplate_sha256'],'mask':row['mask'],'mask_sha256':row['mask_sha256'],'output':str(path),'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_size':list(out.size),'detail_weight':weight,'method':'Source-cleanplate color guide with weighted parent high-frequency residual on frame, followed by exact protected checker restoration','new_neural_passes':0,'protected_rgba_exact_to_source_nearest8x':True,'alpha_exact_to_parent':True,'runtime_verified':False,'release_eligible':False,'visual_review':'pending'})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);ims=[(src,'원본 단순 확대'),(parent,'체크 보존 · 초기 프레임')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in records]
s=Image.new('RGB',(1480,1150),'#293440');d=ImageDraw.Draw(s);box=(0,32,32,96)
for i,bgcolor in enumerate(['#111111','#eeeeee']):
    for j,(im,label) in enumerate(ims):
        x=j*370+10;y=i*575+8;d.text((x,y),label,font=font,fill='white');im=im.crop(box if j==0 else tuple(v*8 for v in box)).resize((256,512),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',im.size,bgcolor);bg.paste(im,(0,0),im);s.paste(bg,(x,y+32))
path=R/'outputs/checker_fidelity_BM221_frame_rework.png';s.save(path)
report={'schema':'brs-checker-frame-rework/v1','files':records,'comparison_sheets':[str(path)],'new_neural_passes':0,'runtime_verified':False}
(R/'qa/checker_frame_rework_v1.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('2 postprocessing outputs; 0 new neural passes')
