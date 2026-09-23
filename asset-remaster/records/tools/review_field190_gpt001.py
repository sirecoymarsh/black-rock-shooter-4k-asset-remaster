import hashlib,json,shutil
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/gpt-trials/FM0190-v1';Q=R/'qa/field_geometry002_gpt190.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
generated=Path(r'P:\AI\Codex\generated_images\01a0c802-c7cf-7f71-a268-2f12b1fd7bd3\exec-c2d7b84f-6611-41e2-a9b7-fd76eda891cf.png')
raw=O/'generated-raw.png';shutil.copy2(generated,raw);im=Image.open(raw).convert('RGBA');raw_size=im.size
out=O/'FM0190-gpt-material-trial-8x.png';im=im.resize((512,1024),Image.Resampling.LANCZOS);im.save(out)
v=next(v for v in json.loads((R/'qa/field_geometry002_bevels_v4.json').read_text('utf8'))['files'] if v['group_id']=='FM0190')
src=Image.open(v['source']).convert('RGBA');p=Image.open(v['parent']).convert('RGBA');fixed=Image.open(v['output']).convert('RGBA');font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for kind,box in [('whole',(0,0,64,128)),('upper',(0,0,64,57)),('lower',(0,88,64,128))]:
 w=(box[2]-box[0])*8;h=(box[3]-box[1])*8;canvas=Image.new('RGB',((w+16)*4,h+42),'#26333f');d=ImageDraw.Draw(canvas)
 ims=[src.crop(box).resize((w,h),Image.Resampling.NEAREST)]+[z.crop(tuple(t*8 for t in box)) for z in [p,fixed,im]]
 for j,(z,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬','구조 보정 v4 · 보류','GPT 재작화 · 검수'])):d.text((j*(w+16)+6,5),title,font=font,fill='white');canvas.paste(z.convert('RGB'),(j*(w+16)+6,36))
 path=R/f'outputs/field-geometry002/FM0190-{kind}-gpt.png';canvas.save(path);pages.append({'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
diagnostics=[];g=np.asarray(im)[:,:,:3].mean(2);smoothed=gaussian_filter(g,(1.5,1.5));gradient=np.gradient(smoothed,axis=0)
for a,c in [(8,24),(40,56)]:
 for sy,sign in [(12,-1),(46,1),(57,-1),(91,1)]:
  nominal=sy*8-.5;ys=np.arange(int(round(nominal))-10,int(round(nominal))+11);xs=np.arange(a*8,c*8);traces=ys[(gradient[ys[:,None],xs[None,:]]*sign).argmax(0)];err=(traces-nominal)/8
  diagnostics.append({'source_x_span':[a,c],'source_y_boundary':sy,'search_radius_output':10,'signed_offset_source_px_percentiles':np.percentile(err,[0,50,95,100]).tolist(),'p95_absolute_offset_source_px':float(np.percentile(abs(err),95))})
report={'schema':'brs-facade-gpt-trial/v1','group_id':'FM0190','external_generative_calls':1,'tool':'built-in image_gen','model_identifier':'not exposed by tool','requested_size':[512,1024],'actual_generated_size':raw_size,'raw':str(raw),'raw_sha256':sha(raw),'generated_store_original':str(generated),'resized_output':str(out),'resized_output_sha256':sha(out),'resized_size':[512,1024],'resampling':'Lanczos from actual generated dimensions; not native8x model output','prompt':str(O/'prompt.txt'),'prompt_sha256':sha(O/'prompt.txt'),'references':[{'path':v['source'],'sha256':sha(v['source'])},{'path':v['output'],'sha256':v['output_sha256']}],'pages':pages,'sample_boundary_diagnostics':diagnostics,'decision':'held','reason':'Whole output has visually excessive pebbled/embossed material in glass and masonry, and source-fixed planes are not guaranteed by generation. Keep only as a possible masonry material reference for a separately constrained follow-up.','source_correction':'Dark pixels at source right window corners and side-face bevels do exist; do not classify all dark corner marks as generated inventions or erase them by default. Their geometry/shading interpretation still needs to yield a coherent joint.','new_local_passes':0,'runtime_verified':False,'release_eligible':False}
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'actual_generated_size':raw_size,'external_calls':1,'pages':3,'p95_boundary_offsets':[z['p95_absolute_offset_source_px'] for z in diagnostics]}))
