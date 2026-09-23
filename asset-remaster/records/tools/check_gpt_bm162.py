import json,hashlib,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');O=R/'workspace/gpt-trials/BM162-v1';O.mkdir(parents=True,exist_ok=True)
generated=Path('P:/AI/Codex/generated_images/01a0c802-c7cf-7f71-a268-2f12b1fd7bd3/exec-26050dba-7f1a-4ce4-8249-6366ec147188.png');dest=O/'generated-original.png';shutil.copyfile(generated,dest);shutil.copyfile(C/'work/GPT_BM162_prompt.txt',O/'prompt.txt')
def sha(b):return hashlib.sha256(b).hexdigest()
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));g=next(g for g in cat['groups'] if g['group_id']=='BM162');src=Image.open(g['representative']['png']).convert('RGBA');im=Image.open(dest).convert('RGBA');a=np.asarray(src);v=np.asarray(im);ref=src.getchannel('A').resize(im.size,Image.Resampling.BILINEAR);mask=np.asarray(ref)>=128;act=v[:,:,3]>=128;union=(mask|act).sum()
ratio=v[:,:,3].mean()/a[:,:,3].mean();iou=(mask&act).sum()/union;forbidden=int(((np.asarray(ref)==0)&(v[:,:,3]>0)).sum());opaque=int(((np.asarray(ref)==255)&(v[:,:,3]<255)).sum());down=np.asarray(im.resize(src.size,Image.Resampling.LANCZOS));vis=a[:,:,3]>0
record={'schema':'brs-gpt-texture-trial/v1','group_id':'BM162','source':g['representative']['png'],'source_rgba_sha256':sha(src.tobytes()),'edit_target':str(R/'workspace/local-sr/observed-v1/BM162-wdn-rgba8x.png'),'generated_original':str(generated),'project_copy':str(dest),'output_sha256':sha(dest.read_bytes()),'size':list(im.size),'requested_size':[1024,1024],'image_model':'Built-in image_gen; actual model identifier not exposed','local_model_inference':False,'image_upload':True,'prompt':(O/'prompt.txt').read_text('utf8'),'alpha_mass_ratio':float(ratio),'threshold128_iou':float(iou),'nonzero_alpha_outside_source_bilinear_support':forbidden,'not_opaque_in_source_solid_support':opaque,'source_scale_rgb_mae_visible':float(np.abs(down[:,:,:3].astype(float)-a[:,:,:3])[vis].mean()),'visual_review':'pending','adopted':False,'runtime_verified':False}
(R/'qa/gpt_bm162_trial_v1.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);s=Image.new('RGB',(1536,615),'#293440');d=ImageDraw.Draw(s)
old=Image.open(record['edit_target']).convert('RGBA')
for i,(pic,t) in enumerate([(src,'원본 단순 확대'),(old,'로컬 후보 · 미채택'),(im,'GPT 대안 · 검증 중')]):
    pic=pic.resize((480,480),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',(480,480),'#72808b');bg.paste(pic,(0,0),pic);x=i*512+10;d.text((x,10),t,font=font,fill='white');s.paste(bg,(x,50))
d.text((12,552),f'원본 알파 면적 대비 {ratio:.3f} / 실루엣 IoU {iou:.3f} / 원본 투명 영역 침범 {forbidden}픽셀',font=font,fill='white');s.save(R/'outputs/gpt_bm162_compare_v1.png')
print(json.dumps({k:v for k,v in record.items() if k not in ['prompt']},ensure_ascii=False))
