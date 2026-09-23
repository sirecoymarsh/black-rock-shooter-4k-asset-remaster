import json,hashlib,shutil
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts');Q=R/'qa/field_sr002_gpt_material.json';assert not Q.exists();r=json.loads((R/'qa/field_sr002_inference.json').read_text('utf8'));v=next(x for x in r['files'] if x['id']=='FM0160-wdn');src=Image.open(v['source']).convert('RGBA');O=R/'workspace/gpt-trials/FM0160-v1';O.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
gp=O/'generated-original.png';shutil.copyfile('P:/AI/Codex/generated_images/01a0c802-c7cf-7f71-a268-2f12b1fd7bd3/exec-a7cee535-b22e-4257-aab7-7e6b67d7dfc8.png',gp);pp=O/'prompt.txt';shutil.copyfile(C/'work/field160_prompt.txt',pp);raw=Image.open(gp).convert('RGBA');base=raw.resize((512,512),Image.Resampling.LANCZOS);a=np.asarray(src.convert('RGB'),float);b=np.asarray(base.convert('RGB'),float);sl=Image.fromarray(np.rint(gaussian_filter(a,(2,2,0))).astype('uint8')).resize((512,512),Image.Resampling.BICUBIC);delta=np.asarray(sl,float)-gaussian_filter(b,(16,16,0));files=[]
for strength in [0,.65]:
 out=Image.fromarray(np.rint(np.clip(b+strength*delta,0,255)).astype('uint8')).convert('RGBA');tag='raw' if strength==0 else 'tone065';op=O/f'FM0160-gpt-{tag}-8x.png';out.save(op);files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':'FM0160-gpt-'+tag,'generated':str(gp),'generated_sha256':sha(gp),'output':str(op),'output_sha256':sha(op),'output_size':list(out.size),'source_low_frequency_tone_strength':strength,'source_low_frequency_sigma_px':2,'new_local_neural_passes':0,'new_external_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
# Each seam edge is located by the strongest signed horizontal gradient in a
# source-derived search window, after equal source-coordinate smoothing.
def edges(im):
 sc=im.width/64;z=np.asarray(im.convert('RGB'),float).mean(2);z=gaussian_filter(z,(1*sc,.45*sc));g=np.gradient(z,axis=1);rs=[]
 for y in range(2,62):
  yy=min(len(g)-1,round((y+.5)*sc-.5));found=[]
  for lo,hi,sign in [(23,32,-1),(31,41,1)]:
   left=round(lo*sc);right=round(hi*sc);p=g[yy,left:right]*sign;k=int(np.argmax(p));found.append((left+k+.5)/sc)
  rs.append(found)
 return np.asarray(rs)
se=edges(src);audit=[]
for f in files:
 ge=edges(Image.open(f['output']));dif=ge-se;audit.append({'id':f['id'],'sampled_rows':list(range(2,62)),'source_edge_positions':se.tolist(),'output_edge_positions':ge.tolist(),'median_abs_offset_source_px':np.median(np.abs(dif),axis=0).tolist(),'p95_abs_offset_source_px':np.quantile(np.abs(dif),.95,axis=0).tolist(),'limit':'60 smoothed row samples and bounded gradient windows; not all-edge or native UV proof.'})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);canvas=Image.new('RGB',(1048,1104),'#25313c');d=ImageDraw.Draw(canvas)
for i,(path,label) in enumerate([(v['source'],'원본 · 단순 확대'),(v['output'],'로컬 WDN · 균열 강조'),(files[0]['output'],'GPT 재작화'),(files[1]['output'],'GPT 재작화 · 원본 명암 보정')]):
 x=i%2*524+4;y=i//2*552;d.text((x,y+6),label,font=font,fill='white');im=Image.open(path).convert('RGB').resize((512,512),Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);canvas.paste(im,(x,y+36))
p=R/'outputs/field-sr002/FM0160-gpt-compare.png';canvas.save(p);rep={'schema':'brs-field-gpt-material/v2','files':files,'external_tool':'built-in image_gen; model identifier not exposed','external_generative_calls':1,'image_upload':True,'local_neural_passes':0,'new_unique_originals':0,'raw_generated':str(gp),'raw_generated_sha256':sha(gp),'requested_size':[1024,1024],'actual_generated_size':list(raw.size),'final_canvas_size':[512,512],'final_resampling':'Lanczos downsample; not native AI8x','prompt':str(pp),'prompt_sha256':sha(pp),'comparison':str(p),'comparison_sha256':sha(p),'edge_diagnostics':audit,'source_fidelity_note':'Source already has faint diagonal/short marks. The defect under review is contrast/depth amplification, not proof that all cracks were invented.','runtime_verified':False};Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'generated_size':list(raw.size),'edge_offsets':[{'id':v['id'],'p95':v['p95_abs_offset_source_px']} for v in audit]}))
