from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from foliage006_weed_shape import build
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent;O=R/'workspace/local-sr/field-foliage006-authored';Q=R/'qa/field_foliage006_weed_shape.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
v1=read(R/'workspace/gpt-trials/FM0290-foliage-v1/provenance.json');v2=read(R/'qa/field_foliage006_weed_v2.json');s=Image.open(v1['source']).convert('RGBA');a=np.asarray(s);first=np.asarray(Image.open(v1['raw_generated_image']).convert('RGBA'));second=np.asarray(Image.open(v2['raw']).convert('RGBA'));out,diagnostics=build(a,first,second);op=O/'FM0290-GPT-source-density-shape-v3-8x.png';Image.fromarray(out).save(op);program=O/'foliage006_weed_shape_frozen.py';shutil.copy2(C/'foliage006_weed_shape.py',program)
small=np.asarray(Image.fromarray(out[:,:,3]).resize(s.size,Image.Resampling.BOX));sm=a[:,:,3]>=128;mask=small>=128;diagnostics['source_scale_IoU_at128']=float((sm&mask).sum()/(sm|mask).sum());diagnostics['source_scale_disagreements_at128']=int((sm!=mask).sum())
tips=[]
for name,box in [('left',(2,5,10,22)),('highest',(17,0,25,15)),('middle-right',(32,3,43,20)),('far-right',(57,14,64,34))]:
 x0,y0,x1,y1=box;rec={'name':name,'source_box':box}
 for lab,m in [('source',sm),('output',mask)]:
  ys,xs=np.where(m[y0:y1,x0:x1]);top=int(ys.min());sel=ys<=top+1;rec[lab]={'top_y':int(y0+top),'top_two_rows_x_mean':float(x0+xs[sel].mean())}
 rec['top_y_shift_source_px']=rec['output']['top_y']-rec['source']['top_y'];rec['top_x_shift_source_px']=rec['output']['top_two_rows_x_mean']-rec['source']['top_two_rows_x_mean'];tips.append(rec)
rep={'schema':'brs-field-foliage006-weed-shape/v1','id':'FM0290-GPT-source-density-shape-v3','group_id':'FM0290','source':v1['source'],'source_rgba_sha256':v1['source_rgba_sha256'],'parents':[{'path':v1['raw_generated_image'],'sha256':sha(v1['raw_generated_image'])},{'path':v2['raw'],'sha256':sha(v2['raw'])}],'program':str(program),'program_sha256':sha(program),'output':str(op),'output_sha256':sha(op),'output_size':list(Image.open(op).size),'diagnostics':diagnostics,'tip_landmarks':tips,'method':'Two actual GPT re-paintings with locally authored signed-distance contour interpolation to restore source total coverage; RGB colors interpolated from those paintings. No new neural pass. Fine leaf contours are repainted, not source pixel-exact.','new_local_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False,'pages':[]}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for tag,box in [('whole',None),('tips',(20,0,60,40)),('lower',(12,32,52,64))]:
 can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
 for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
  for col,(path,title) in enumerate([(v1['source'],'원본 · 단순 확대'),(v1['raw_generated_image'],'GPT 1차'),(str(op),'윤곽·밀도 조정')]):
   pic=Image.open(path).convert('RGBA')
   if box:
    xs=pic.width/s.width;ys=pic.height/s.height;pic=pic.crop(tuple(round(t*(xs if i%2==0 else ys)) for i,t in enumerate(box)))
   scale=min(320/pic.width,340/pic.height);pic=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',pic.size,matte);bg.alpha_composite(pic);d.text((col*350+8,row*405+8),title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
 pp=R/'outputs/field-foliage006'/('FM0290-GPT-shape-v3-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps({'diagnostics':diagnostics,'tip_landmarks':tips}))
