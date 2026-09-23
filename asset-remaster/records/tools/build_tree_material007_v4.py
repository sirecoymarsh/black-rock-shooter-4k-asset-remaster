from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from tree_material007 import build,TRACKS,CANOPY_BOTTOM
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');C=Path(__file__).resolve().parent;O=R/'workspace/local-sr/field-foliage007';P=R/'outputs/field-foliage007';Q=R/'qa/field_foliage007_trees_v4.json';assert not Q.exists()
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
local=read(R/'qa/field_foliage006_local.json');audit=read(R/'qa/field_foliage007_source_audit.json');d=read(R/'workspace/gpt-trials/FM0314-foliage-v1/provenance.json');donor=Image.open(d['raw_generated_image']).convert('RGBA');prog=O/'tree_material007_v4_frozen.py';shutil.copy2(C/'tree_material007.py',prog);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
rep={'schema':'brs-field-foliage007-trees/v4','source_audit_sha256':sha(R/'qa/field_foliage007_source_audit.json'),'catalog_before_sha256':audit['catalog_before_sha256'],'geometry_contract_before_sha256':audit['geometry_contract_before_sha256'],'program':str(prog),'program_sha256':sha(prog),'GPT_donor':d['raw_generated_image'],'GPT_donor_sha256':d['raw_sha256'],'files':[],'pages':[],'source_wood_classes':[],'new_unique_originals':0,'new_local_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False};classes={};sources={}
for gid in ['FM0314','FM0316','FM0317','FM0325']:
 p=next(z for z in local['files'] if z['id']==gid+'-photo');source=Image.open(p['source']).convert('RGBA');parent=Image.open(p['output']).convert('RGBA');a=np.asarray(source);sources[gid]=a;out,mask,layers,diag=build(a,np.asarray(parent),np.asarray(donor));op=O/(gid+'-source-material-v4-8x.png');Image.fromarray(out).save(op);mp=O/(gid+'-source-material-v4-mask.png');Image.fromarray(np.rint(mask*255).astype('uint8')).save(mp)
 classes[gid]=a[:,:,:3].mean(2)>=diag['source_wood_luma_threshold'];rec={'id':gid+'-source-material-v4','group_id':gid,'source':p['source'],'source_ptm':p['source_ptm'],'source_ptm_sha256':p['source_ptm_sha256'],'source_rgba_sha256':p['source_rgba_sha256'],'parent':p['output'],'parent_sha256':p['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'diagnostics':diag,'review_status':'pending','runtime_verified':False,'release_eligible':False};rep['files'].append(rec)
 for tag,box in [('whole',None),('canopy',(28,20,68,60)),('main-trunk',(38,80,70,128)),('fork-right',(72,86,112,126)),('left-edge',(0,28,40,76))]:
  can=Image.new('RGB',(1050,810),'#25313c');dr=ImageDraw.Draw(can)
  for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
   for col,(path,title) in enumerate([(p['source'],'원본 · 단순 확대'),(p['output'],'로컬 Photo'),(str(op),'원본 구조 + 잎·나무껍질')]):
    im=Image.open(path).convert('RGBA')
    if box:im=im.crop(box if col==0 else tuple(t*8 for t in box))
    scale=min(320/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,matte);bg.alpha_composite(im);dr.text((col*350+8,row*405+8),gid+' '+title,font=font,fill='white');dr.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da');can.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2))
  pp=P/(gid+'-source-material-v4-'+tag+'.png');can.save(pp);rep['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
 Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8');print('BUILT',gid,flush=True)
for gid in ['FM0316','FM0317','FM0325']:
 common=(sources['FM0314'][:,:,3]>0)&(sources[gid][:,:,3]>0);yy,xx=np.mgrid[:128,:128];core=common&(yy>=82)&(yy<125)&(xx>=45);rep['source_wood_classes'].append({'base':'FM0314','other':gid,'comparison_region':'source rows82..124, columns45..127, jointly opaque','compared_pixels':int(core.sum()),'classification_disagreements':int(((classes['FM0314']!=classes[gid])&core).sum()),'limit':'Same decoded material classification in these source regions supports reusing directional controls; not evidence of shared consumer or identical alpha.'})
Q.write_text(json.dumps(rep,ensure_ascii=False,indent=2,allow_nan=False),'utf8');print(json.dumps({'files':len(rep['files']),'pages':len(rep['pages']),'source_wood_classes':rep['source_wood_classes']}),flush=True)
