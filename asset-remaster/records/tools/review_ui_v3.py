import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];a=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'));sdo=json.loads((R/'qa/ui_consumers_static.json').read_text(encoding='utf-8'));S=8
protected={2:[(0,0,94,48),(94,43,99,48)],4:[(0,0,94,48),(94,43,99,48)],6:[(0,10,228,35),(0,0,15,10)],7:[(0,80,104,185),(104,0,128,180)],10:[(157,0,214,29),(157,29,164,42),(0,0,157,96)],11:[(56,12,88,28),(0,28,89,56),(95,48,105,58),(100,12,105,20),(106,6,111,14),(112,12,117,20)],14:[(56,12,88,28),(0,28,89,56),(95,48,105,58),(100,12,105,20),(106,6,111,14),(112,12,117,20)],17:[(0,0,128,6)],22:[(46,294,96,296),(46,303,96,305),(46,296,48,303),(87,296,96,303),(62,322,77,338),(46,306,62,337),(48,339,53,352),(108,339,126,352)]}
proof=[];ims={}
build=json.loads((R/'qa/ui_build_v3.json').read_text(encoding='utf-8'))
# Source ink extents measured independently from original pixels, including
# the baseline rows missed by the first correction. A clear region must cover
# the entire old label before any new glyph is composed over it.
source_ink={6:[(16,4,78,9)],9:[(36,4,37,11),(90,4,91,16),(90,25,91,26)],11:[(100,20,105,47),(106,14,111,61),(112,20,117,37)],14:[(100,20,105,47),(106,14,111,61),(112,20,117,37)],22:[(49,297,87,302),(53,340,107,350)]}
ink_checks=[]
for i in [2,4,6,7,9,10,11,14,17,18,22]:
 row=a['assets'][i];old=Image.open(Path(row['source']).with_suffix('.png')).convert('RGBA');new=Image.open(R/f'workspace/ui_candidates_v3/UI-{i:02d}_8x.png').convert('RGBA');ims[i]=(old,new)
 clear_mask=np.zeros((old.height,old.width),bool)
 for clear in build['records'][i]['proof']['clear_regions']:
  x,y,x1,y1=clear['box'];clear_mask[y:y1,x:x1]=True
 for box in source_ink.get(i,[]):
  x,y,x1,y1=box;assert clear_mask[y:y1,x:x1].all(),(i,box,'source text not completely erased');ink_checks.append({'id':f'UI-{i:02d}','source_ink_box':box,'fully_cleared':True})
 for box in protected.get(i,[]):
  xy=tuple(v*S for v in box);before=old.crop(box).resize((xy[2]-xy[0],xy[3]-xy[1]),Image.Resampling.NEAREST);after=new.crop(xy);assert before.tobytes()==after.tobytes(),(i,box,'protected pixels altered');proof.append({'id':f'UI-{i:02d}','box':box,'rgba_equal':True})

# Compare flat original background positions to catch a clean plate that
# accidentally changes color even when protected regions still pass.
old,new=ims[6];bg=(10,7,5,255)
assert old.getpixel((15,3))==bg and new.getpixel((15*S,3*S))==bg
exit_pixels=np.array(new.crop((218*S,56*S,255*S,70*S)))
assert tuple(exit_pixels.reshape(-1,4)[exit_pixels[:,:,3].argmax()])==(78,78,78,252)
for box in source_ink[9]:
 assert not np.array(ims[9][1].crop(tuple(v*S for v in box)))[:,:,3].any(),('UI-09 shadow residue',box)
def compose(i,archive,ids,slot,texsize):
 ar=next(x for x in sdo['records'] if x['archive']==archive);m=next(m for m in ar['members'] if 'sdo' in m);parts=[]
 for sid in ids:
  r=m['sdo']['records'][sid];assert r['texture_slot']==slot
  uv=tuple(round(v*texsize[j%2]) for j,v in enumerate(r['uv_normalized']));x,y=[round(r['layout_xywh'][j]+min(v[j+2] for v in r['vertices'])) for j in range(2)];parts.append((uv,x,y))
 left=min(p[1] for p in parts);top=min(p[2] for p in parts);w=max(x+b[2]-b[0] for b,x,y in parts)-left;h=max(y+b[3]-b[1] for b,x,y in parts)-top;outs=[]
 for n,im in enumerate(ims[i]):
  canvas=Image.new('RGBA',(w*S,h*S))
  for box,x,y in parts:
   b=tuple(v*(S if n else 1) for v in box);tile=im.crop(b)
   if not n:tile=tile.resize((tile.width*S,tile.height*S),Image.Resampling.NEAREST)
   canvas.alpha_composite(tile,((x-left)*S,(y-top)*S))
  outs.append(canvas)
 return outs
rows=[];f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
def add(label,old,new):
 w=1100;scale=min(1,(w-30)/max(old.width,new.width));old=old.resize((round(old.width*scale),round(old.height*scale)),Image.Resampling.NEAREST);new=new.resize((round(new.width*scale),round(new.height*scale)),Image.Resampling.LANCZOS)
 row=Image.new('RGB',(2200,max(old.height,new.height)+40),'#243449');d=ImageDraw.Draw(row);d.text((6,3),label+' / 원본 → 후보',font=f,fill='white');row.paste(old,(6,34),old);row.paste(new,(1106,34),new);rows.append(row)
for i,ar,ids,slot,sz,label in [(9,'MENU/MENU_CUSTOM',[61,62,63,64,65,66,81,82,83],1,(128,64),'UI-09 실제 제목 조립'),(18,'MENU/MENU_OPTION',list(range(18,25)),3,(128,64),'UI-18 실제 제목 조립'),(7,'MENU/IF_STAGE_SELECT',[145,201],13,(128,256),'UI-07 임무 정보 조립')]:
 old,new=compose(i,ar,ids,slot,sz);add(label,old,new)
for i,box in [(2,(85,0,110,48)),(6,(0,0,110,16)),(7,(50,170,128,192)),(10,(155,0,245,43)),(11,(0,0,128,64)),(17,(0,0,128,24)),(22,(44,290,128,353))]:
 old,new=ims[i];add(f'UI-{i:02d}',old.crop(box).resize(((box[2]-box[0])*S,(box[3]-box[1])*S),Image.Resampling.NEAREST),new.crop(tuple(v*S for v in box)))
out=Image.new('RGB',(2200,sum(r.height for r in rows)),'#243449');y=0
for row in rows:out.paste(row,(0,y));y+=row.height
out.save(R/'outputs/ui_v3_geometry_proof.png')
old,new=ims[22];box=(44,290,98,306);before=old.crop(box).resize((864,256),Image.Resampling.NEAREST);after=new.crop(tuple(v*S for v in box)).resize((864,256),Image.Resampling.NEAREST)
focus=Image.new('RGB',(884,600),'#243449');d=ImageDraw.Draw(focus);d.text((10,5),'원본',font=f,fill='white');focus.paste(before,(10,35),before);d.text((10,305),'수정: 조준 고정',font=f,fill='white');focus.paste(after,(10,335),after);focus.save(R/'outputs/lock_on_before_after.png')
(R/'qa/ui_v3_protected_regions.json').write_text(json.dumps({'protected_regions':proof,'count':len(proof),'source_ink_coverage':ink_checks,'status':'Exact RGBA equals native nearest expansion in specified ornament/icon regions; all measured old source ink extents cleared. Runtime acceptance remains pending.'},indent=2),encoding='utf-8')
print(json.dumps({'protected_regions_passed':len(proof),'sheet_size':out.size}))
