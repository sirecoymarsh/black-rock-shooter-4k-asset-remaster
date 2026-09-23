from pathlib import Path
import sys,shutil,json,hashlib
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');G=Path(r'P:\AI\Codex\generated_images\01a0c802-c7cf-7f71-a268-2f12b1fd7bd3');P=R/'outputs/field-foliage006';Q=R/'qa/field_foliage006_gpt_raw.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text('utf8'))
local=read(R/'qa/field_foliage006_local.json');old={x['group_id']:x for x in local['files'] if x['id'].endswith('-photo')};names={'FM0290':'exec-ff144a04-4994-4098-895d-ec6a4f854247.png','FM0314':'exec-7150d026-802f-4136-9bed-10c64d1098cb.png'}
rep={'schema':'brs-field-foliage006-GPT-raw/v1','tool':'built-in image_gen','actual_external_calls':2,'model_id':'not exposed','files':[],'pages':[],'runtime_verified':False,'release_eligible':False};font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
for gid,name in names.items():
 o=R/'workspace/gpt-trials'/(gid+'-foliage-v1');p=read(o/'provenance.json');dest=o/'generated-raw.png';assert not dest.exists();shutil.copy2(G/name,dest);a=Image.open(dest).convert('RGBA');s=Image.open(p['source']).convert('RGBA');sa=np.asarray(s)[:,:,3];aa=np.asarray(a)[:,:,3];small=np.asarray(a.getchannel('A').resize(s.size,Image.Resampling.BOX));mask=small>=128;src=sa>=128;alpha={'extrema':[int(aa.min()),int(aa.max())],'unique_values':len(np.unique(aa)),'source_scale_IoU_at128':float((src&mask).sum()/(src|mask).sum()),'mass_ratio':float(aa.mean()/sa.mean()),'source_center_mask_disagreements':int((mask!=src).sum()),'source_nonzero_pixels':int(src.sum())};opaque=np.asarray(a)[aa>=128,:3];green=(opaque[:,1].astype(int)-opaque[:,0]>50)&(opaque[:,1].astype(int)-opaque[:,2]>30);cyan=(opaque[:,1].astype(int)-opaque[:,0]>70)&(opaque[:,2].astype(int)-opaque[:,0]>70)
 p.update(status='raw_generated_pending_review',generated_store_path=str(G/name),raw_generated_image=str(dest),raw_sha256=sha(dest),raw_size=list(a.size),raw_generated_image_preserved=True,raw_alpha_diagnostics=alpha,high_chroma_edge_diagnostics={'opaque_green_pixels':int(green.sum()),'opaque_cyan_pixels':int(cyan.sum())});(o/'provenance.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),'utf8');rep['files'].append(p)
 boxes=[('whole',None),('native',(20,0,60,40) if gid=='FM0290' else (28,20,68,60))]
 if gid=='FM0314':boxes.append(('trunks',(28,80,68,120)))
 for tag,box in boxes:
  can=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(can)
  for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
   for col,(path,title) in enumerate([(p['source'],'원본 · 단순 확대'),(old[gid]['output'],'로컬 Photo'),(str(dest),'GPT 재작화 · 원시 결과')]):
    im=Image.open(path).convert('RGBA')
    if box:
     xs=im.width/s.width;ys=im.height/s.height;im=im.crop(tuple(round(t*(xs if i%2==0 else ys)) for i,t in enumerate(box)))
    scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);d.text((col*350+8,row*405+8),gid+' '+title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/(gid+'-GPT-raw-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2),'utf8');print(json.dumps([{'id':p['group_id'],'size':p['raw_size'],'alpha':p['raw_alpha_diagnostics'],'chroma':p['high_chroma_edge_diagnostics']} for p in rep['files']]))
