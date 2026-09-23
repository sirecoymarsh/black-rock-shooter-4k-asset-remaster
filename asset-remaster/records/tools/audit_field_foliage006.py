from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/field_foliage006_source_audit.json';assert not Q.exists();P=R/'outputs/field-foliage006';O=R/'workspace/local-sr/field-foliage006';P.mkdir(exist_ok=True);O.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={}
for p in sorted((R/'qa').glob('field_source_review0*.json')):
 for z in json.loads(p.read_text('utf8')).get('files',[]):sources[z['group_id']]=z
ids=json.loads((R/'qa/field_pending_routing010.json').read_text('utf8'))['next_bounded_batch'];assert len(ids)==9
files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for page in range(3):
 can=Image.new('RGB',(1020,1110),'#25313c');d=ImageDraw.Draw(can)
 for row,gid in enumerate(ids[page*3:page*3+3]):
  z=sources[gid];src=Image.open(z['source']).convert('RGBA');a=np.asarray(src);assert sha(z['source_ptm'])==z['source_ptm_sha256'] and hashlib.sha256(a.tobytes()).hexdigest()==z['source_rgba_sha256'];al=a[:,:,3];rgb=a[:,:,:3];info={'min':int(al.min()),'max':int(al.max()),'mass':int(al.sum()),'zero_pixels':int((al==0).sum()),'nonzero_pixels':int((al>0).sum()),'weak_1_to31_pixels':int(((al>0)&(al<32)).sum()),'opaque_pixels':int((al==255).sum()),'RGB_in_alpha0_mean':rgb[al==0].mean(0).tolist() if (al==0).any() else None,'unique_alpha_levels':int(np.unique(al).size)};files.append({**z,'source_alpha':info});print(gid,src.size,info,flush=True)
  for col,(matte,title) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경'),(None,'원본 투명도')]):
   if matte is None:im=src.getchannel('A').convert('RGB')
   else:bg=Image.new('RGBA',src.size,matte);bg.alpha_composite(src);im=bg.convert('RGB')
   scale=min(300/im.width,310/im.height);pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);d.text((col*340+10,row*370+10),gid+' '+title,font=font,fill='white');can.paste(pic,(col*340+(340-pic.width)//2,row*370+45+(310-pic.height)//2))
 pp=P/f'source-alpha-{page+1:02}.png';can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_ids':ids[page*3:page*3+3],'review_status':'pending'})
report={'schema':'brs-field-foliage006-source-audit/v1','previous_goal_turn_classification':'The most recent user percentage reply was status-only/no progress; authoritative geometry010 previously resolved496. No live job is being assumed or restarted. Safe next action is the queued9 unprocessed foliage originals.','files':files,'pages':pages,'catalog_before_sha256':sha(R/'qa/field_sr_catalog.json'),'geometry_contract_before_sha256':sha(R/'qa/architectural_geometry_contract.json'),'new_local_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
