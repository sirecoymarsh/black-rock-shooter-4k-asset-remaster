"""Use original broad shading on the authored metal fastener, keeping holes sharp."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr012_manual_shaded.json'
if Q.exists():raise SystemExit('Existing revision.')
q=json.loads((R/'qa/local_sr012_manual_hybrid.json').read_text('utf8'));r=q['files'][0];src=Image.open(r['source']).convert('RGBA');parent=Image.open(r['output']).convert('RGBA');paint=Image.open(r['manual_parent']).convert('RGBA')
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(Path(r['output']).read_bytes())==r['output_sha256']
v=np.asarray(parent).copy();p=np.asarray(paint);yy,xx=np.indices(v.shape[:2]);sx=(xx+.5)/8;sy=(yy+.5)/8;dist=np.hypot(sx-48,sy-15.7)
# Solid painted center metal only; all black holes and all pixels outside the center remain exact.
metal=(dist<4.1)&(p[:,:,:3].mean(2)>65);rgb=np.asarray(src)[:,:,:3].astype('float32');sm=gaussian_filter(rgb,(.55,.55,0),mode='nearest');field=np.asarray(Image.fromarray(np.rint(sm).astype('uint8')).resize(parent.size,Image.Resampling.BICUBIC),dtype=np.float32);luma=field.mean(2);gain=np.clip(.38+.62*luma/95.,.65,1.4)
v[metal,:3]=np.rint(np.clip(v[metal,:3].astype(float)*gain[metal,None],0,255)).astype('uint8');im=Image.fromarray(v);O=Path(r['output']).parent;path=O/'BM110-codex-grid-and-fastener-v3.png';im.save(path);mp=O/'BM110-center-metal-mask-v3.png';Image.fromarray(metal.astype('uint8')*255).save(mp)
assert np.array_equal(v[~metal],np.asarray(parent)[~metal])
record={'id':'BM110-codex-grid-and-fastener-v3','group_id':'BM110','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'alpha_parent':r['alpha_parent'],'alpha_parent_sha256':r['alpha_parent_sha256'],'manual_parent':r['manual_parent'],'manual_parent_sha256':r['manual_parent_sha256'],'vector':r['vector'],'vector_sha256':r['vector_sha256'],'mask':str(mp),'mask_sha256':sha(mp.read_bytes()),'output':str(path),'output_sha256':sha(path.read_bytes()),'output_size':list(im.size),'new_neural_passes':0,'method':'Source broad luminance applied only to manually drawn center metal; sharp authored holes, straight grid, external local frame and alpha unchanged','shading':{'source_gaussian_sigma':.55,'resample':'RGB bicubic8x','gain_formula':'clip(0.38+0.62*source_luma/95,0.65,1.4)','center_metal_pixels':int(metal.sum())},'visual_review':'pending','runtime_verified':False,'release_eligible':False}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);s=Image.new('RGB',(1596,660),'#293440');d=ImageDraw.Draw(s);initial=Image.open(r['alpha_parent']).convert('RGBA')
for i,bgc in enumerate(['#111111','#eeeeee']):
    for j,(img,label) in enumerate([(src,'원본 단순 확대'),(initial,'초기 로컬 AI'),(im,'격자·중심부 직접 재구성')]):
        x=j*532+8;y=i*330+8;d.text((x,y),label,font=font,fill='white');img=img.resize((512,256),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',img.size,bgc);bg.paste(img,(0,0),img);s.paste(bg,(x,y+34))
sheet=R/'outputs/sr012_manual_shaded_BM110.png';s.save(sheet)
Q.write_text(json.dumps({'schema':'brs-sr012-manual-shaded/v1','files':[record],'comparison_sheets':[str(sheet)],'new_neural_passes':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('Shaded authored center; no new model inference')
