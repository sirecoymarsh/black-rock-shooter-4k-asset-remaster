import json,hashlib,shutil
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/gpt-trials/BM201-v1';Q=R/'qa/local_sr015_gpt_floor.json'
if Q.exists():raise SystemExit('Existing attempt')
O.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));g=next(g for g in cat['groups'] if g['group_id']=='BM201');src=Image.open(g['representative']['png']).convert('RGBA');assert sha(src.tobytes())==g['rgba_sha256']
raw=Path('P:/AI/Codex/generated_images/01a0c802-c7cf-7f71-a268-2f12b1fd7bd3/exec-fafb63bc-12cc-4328-bf75-8635e2795415.png');gp=O/'generated-original.png';shutil.copyfile(raw,gp);gen=Image.open(gp).convert('RGBA');assert np.asarray(gen)[:,:,3].min()==255
base=gen.resize((2048,2048),Image.Resampling.LANCZOS);v=np.asarray(base)[:,:,:3].astype(float);a=np.asarray(src)[:,:,:3].astype(float)
source_low=gaussian_filter(a,(12,12,0),mode='reflect');sl=np.asarray(Image.fromarray(np.rint(source_low).astype('uint8')).resize(base.size,Image.Resampling.BICUBIC),float);gl=gaussian_filter(v,(96,96,0),mode='reflect')
files=[]
for name,strength in [('raw',0.),('tone',.7)]:
 out=Image.fromarray(np.rint(np.clip(v+strength*(sl-gl),0,255)).astype('uint8')).convert('RGBA');p=O/f'BM201-gpt-{name}-8x.png';out.save(p)
 files.append({'id':'BM201-gpt-'+name,'group_id':'BM201','source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'generated':str(gp),'generated_sha256':sha(gp.read_bytes()),'generated_size':list(gen.size),'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(out.size),'method':'External full-atlas repaint resized to source8x, with optional low-frequency source tone correction','tone_strength':strength,'tone_sigma_source_px':12,'new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
local=Image.open(g['superseded_candidates'][-1]['candidate']['output']).convert('RGBA');font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for k,box in enumerate([(0,0,256,256),(50,20,149,80),(148,20,237,155),(15,105,75,194),(10,195,125,256),(194,197,249,253)]):
 w=512;h=round(w*(box[3]-box[1])/(box[2]-box[0]));rh=h+55;s=Image.new('RGB',(1064,rh*2),'#293440');d=ImageDraw.Draw(s)
 ims=[(src,'원본 단순 확대'),(local,'기존 로컬 후보')]+[(Image.open(f['output']).convert('RGBA'),f['id']) for f in files]
 for i,(im,label) in enumerate(ims):
  x=i%2*532+8;y=i//2*rh+8;d.text((x,y),label,font=font,fill='white');im=im.crop(box if i==0 else tuple(z*8 for z in box)).resize((w,h),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);s.paste(im.convert('RGB'),(x,y+32))
 p=R/f'outputs/sr015-BM201-initial-{k}.png';s.save(p);pages.append(str(p))
prompt=O/'prompt.txt';assert prompt.exists()
Q.write_text(json.dumps({'schema':'brs-sr015-gpt-floor/v1','files':files,'raw_generated':{'path':str(gp),'sha256':sha(gp.read_bytes()),'size':list(gen.size),'requested_size':[2048,2048],'direct_use_accepted':False},'prompt_file':str(prompt),'prompt_sha256':sha(prompt.read_bytes()),'reference_image':g['representative']['png'],'tool':'built-in image_gen; model identifier not exposed','new_neural_passes':0,'new_generative_calls':1,'image_upload':True,'comparison_sheets':pages,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'generated_size':gen.size,'outputs':2,'comparison_pages':len(pages)}))
