"""Source-derived alpha alternatives for faint smoke particles lost in initial trials."""
import hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr012_smoke_alpha.json'
if Q.exists():raise SystemExit('Existing alpha revision.')
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));r=next(r for r in q['files'] if r['group_id']=='BM111' and r['model_id']=='wdn');src=Image.open(r['source']).convert('RGBA');prior=Image.open(r['output']).convert('RGBA');O=R/'workspace/local-sr/sr012-smoke-alpha';O.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(Path(r['output']).read_bytes())==r['output_sha256'];original=np.asarray(src.getchannel('A'));lin=np.asarray(src.getchannel('A').resize(prior.size,Image.Resampling.BILINEAR));files=[]
for name,kernel in [('bicubic',Image.Resampling.BICUBIC),('lanczos',Image.Resampling.LANCZOS)]:
    alpha=np.asarray(src.getchannel('A').resize(prior.size,kernel)).copy();alpha[lin==0]=0;alpha[lin==255]=255;im=prior.copy();im.putalpha(Image.fromarray(alpha));p=O/f'BM111-wdn-source-{name}-alpha.png';im.save(p);down=np.asarray(im.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=original>=128;pred=down>=128;metric={'source_ge16_reduced_below8':int(((original>=16)&(down<8)).sum()),'source_threshold128_iou':float((gt&pred).sum()/(gt|pred).sum()),'mass_ratio':float(alpha.mean()/original.mean()),'outside_source_bilinear_support':int((alpha[lin==0]>0).sum())}
    files.append({'id':f'BM111-wdn-source-{name}-alpha','group_id':'BM111','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(im.size),'new_neural_passes':0,'alpha_kernel':name,'method':'Local WDN RGB retained byte-exact; source alpha resized with named kernel and constrained to source-bilinear zero/255 support','alpha_metrics':metric,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);s=Image.new('RGB',(1560,1150),'#293440');d=ImageDraw.Draw(s);ims=[(src,'원본'),(prior,'초기 WDN')]+[(Image.open(r['output']).convert('RGBA'),r['alpha_kernel']) for r in files]
for i,bgc in enumerate(['#111111','#eeeeee']):
    for j,(im,label) in enumerate(ims):
        x=j*390+8;y=i*575+8;d.text((x,y),label,font=font,fill='white');im=im.resize((256,512),Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',im.size,bgc);bg.paste(im,(0,0),im);s.paste(bg,(x,y+32))
p=R/'outputs/sr012_smoke_alpha.png';s.save(p);Q.write_text(json.dumps({'schema':'brs-sr012-smoke-alpha/v1','files':files,'comparison_sheets':[str(p)],'new_neural_passes':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({r['id']:r['alpha_metrics'] for r in files}))
