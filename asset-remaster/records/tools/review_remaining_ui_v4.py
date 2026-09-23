"""Independent original-pixel protection and SDO display-geometry review.

These are static point-sampled reconstructions, not screenshots or runtime proof.
"""
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];S=8
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'))
build=json.loads((R/'qa/ui_build_v4.json').read_text(encoding='utf-8'))
sdo=json.loads((R/'qa/ui_consumers_static.json').read_text(encoding='utf-8'))
protected={0:[(0,55,70,59)],1:[(0,0,128,59),(0,59,8,96),(87,76,128,83),(81,83,128,89),(75,89,128,96)],3:[(0,0,128,59),(0,59,8,96),(87,76,128,83),(81,83,128,89),(75,89,128,96)],12:[(0,0,128,30),(0,30,8,47),(78,30,85,46),(60,48,85,59),(0,59,33,80),(62,59,128,80),(88,19,119,38),(88,43,119,60)],13:[(0,0,37,37)],15:[(0,0,128,103),(0,121,128,144),(68,87,110,129),(62,103,110,121)],16:[(0,0,256,6),(239,5,256,18),(104,17,256,24)],19:[(0,0,256,37),(0,37,155,48),(166,37,185,48),(203,37,256,48)],20:[(0,0,49,113),(55,0,64,113),(49,106,55,113),(41,113,64,120)],21:[(110,0,256,23),(195,23,256,48),(0,47,195,48)],23:[(0,0,105,104),(115,0,116,104),(126,0,128,104),(105,77,115,104),(116,65,126,104)],24:[(88,0,96,7),(113,0,128,7),(88,12,128,17),(105,17,128,24)],25:[(94,0,128,17),(84,22,128,32)],26:[(0,0,256,10),(245,10,256,32),(0,25,245,32)]}
# Areas known to contain only the old label and its own shadow; any visible
# source pixel here must have been cleared, including gutter pixels.
old_text={0:[(0,0,128,55),(84,55,128,72)],1:[(8,59,121,64),(8,65,121,70),(8,71,102,76),(8,77,87,82),(8,83,81,88),(8,89,75,94)],3:[(8,59,121,64),(8,65,121,70),(8,71,102,76),(8,77,87,82),(8,83,81,88),(8,89,75,94)],12:[(8,30,63,35),(8,36,77,41),(8,42,73,47),(1,48,59,58),(33,59,62,65),(89,37,119,44)],13:[(37,0,64,41),(0,40,64,80)],15:[(0,103,68,121),(110,103,128,121)],16:[(0,5,119,17),(119,5,239,17),(0,17,105,29),(0,29,105,41),(0,41,116,53),(105,24,154,35),(155,24,193,35),(155,36,193,47)],19:[(155,37,166,42),(185,37,197,42),(198,37,203,42)],20:[(49,43,55,106),(0,113,64,120)],21:[(0,0,110,23),(0,23,195,47)],23:[(104,0,116,104),(116,0,128,104)],24:[(0,0,88,17),(96,0,113,7),(88,7,128,16),(0,16,128,24)],25:[(0,0,94,17),(0,17,84,32),(85,17,108,22)],26:[(0,10,117,32),(118,10,245,32)]}
# UI-19 has no translated label: retain its original Latin abbreviation atlas.
protected[19]=[(0,0,256,48)]
old_text[19]=[]
ims={};checks=[];issues=[];ink=[]
for i in sorted(protected):
 a=audit['assets'][i];old=Image.open(Path(a['source']).with_suffix('.png')).convert('RGBA');new=Image.open(R/f'workspace/ui_candidates_v4/UI-{i:02d}_8x.png').convert('RGBA');ims[i]=(old,new)
 assert hashlib.sha256((R/f'workspace/ui_candidates_v4/UI-{i:02d}_8x.png').read_bytes()).hexdigest()==build['records'][i]['candidate_sha256']
 for b in protected[i]:
  x,y,x1,y1=b;expected=old.crop(b).resize(((x1-x)*S,(y1-y)*S),Image.Resampling.NEAREST)
  assert expected.tobytes()==new.crop(tuple(v*S for v in b)).tobytes(),(i,b,'protected pixels changed')
  checks.append({'id':f'UI-{i:02d}','box':b,'exact_rgba_equal':True})
 clear=np.zeros((old.height,old.width),bool)
 for row in build['records'][i]['proof']['clear_regions']:
  x,y,x1,y1=row['box'];clear[y:y1,x:x1]=True
 alpha=np.array(old)[:,:,3]>0
 for b in old_text[i]:
  x,y,x1,y1=b;missing=alpha[y:y1,x:x1]&~clear[y:y1,x:x1]
  if missing.any():
   yy,xx=np.where(missing);issues.append({'id':f'UI-{i:02d}','box':b,'uncleared_count':int(missing.sum()),'coordinates':[[int(px+x),int(py+y)] for px,py in zip(xx,yy)]})
  ink.append({'id':f'UI-{i:02d}','box':b,'source_ink_count':int(alpha[y:y1,x:x1].sum()),'fully_cleared':not missing.any()})

def rec(archive,member,rid):
 a=next(a for a in sdo['records'] if a['archive']==archive);m=next(m for m in a['members'] if m['index']==member);return m['sdo']['records'][rid]

def consumed(i,archive,member,ids,slot,dimensions):
 records=[rec(archive,member,rid) for rid in ids];bounds=[]
 for r in records:
  assert r['texture_slot']==slot
  v=np.array(r['vertices']);xy=v[:,2:4]+np.array(r['layout_xywh'][:2]);bounds.append((xy.min(0),xy.max(0)))
 left,top=np.min([b[0] for b in bounds],axis=0);right,bottom=np.max([b[1] for b in bounds],axis=0)
 outs=[]
 for n,im in enumerate(ims[i]):
  scale=1 if n==0 else S;arr=np.array(im);canvas=Image.new('RGBA',(round((right-left)*S),round((bottom-top)*S)))
  for r,(lo,hi) in zip(records,bounds):
   v=np.array(r['vertices']);xy=v[:,2:4]+np.array(r['layout_xywh'][:2]);uv=v[:,:2]*np.array(dimensions)
   # Fit the source UV as a function of display XY, including 90-degree turns.
   coeff=np.linalg.lstsq(np.c_[xy,np.ones(len(xy))],uv,rcond=None)[0]
   assert np.max(np.abs(np.c_[xy,np.ones(len(xy))]@coeff-uv))<1e-7
   w,h=np.rint((hi-lo)*S).astype(int);yy,xx=np.mgrid[:h,:w]
   pts=np.stack([lo[0]+(xx+.5)/S,lo[1]+(yy+.5)/S,np.ones_like(xx)],-1)@coeff
   pix=np.floor(pts*scale+1e-7).astype(int)
   tile=Image.fromarray(arr[pix[:,:,1],pix[:,:,0]])
   canvas.alpha_composite(tile,(round((lo[0]-left)*S),round((lo[1]-top)*S)))
  outs.append(canvas)
 return outs

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
def row(label,old,new):
 factor=min(1,1010/max(old.width,new.width));old=old.resize((round(old.width*factor),round(old.height*factor)),Image.Resampling.NEAREST);new=new.resize(old.size,Image.Resampling.LANCZOS)
 out=Image.new('RGB',(2100,old.height+42),'#596270');d=ImageDraw.Draw(out);d.text((10,5),label+' / 원본 → 수정 (정적 표시 좌표)',font=font,fill='white');out.paste(old,(10,36),old);out.paste(new,(1060,36),new);return out
def crop(i,box):
 old,new=ims[i];x,y,x1,y1=box;return old.crop(box).resize(((x1-x)*S,(y1-y)*S),Image.Resampling.NEAREST),new.crop(tuple(v*S for v in box))
def save(name,rows):
 out=Image.new('RGB',(2100,sum(r.height for r in rows)),'#596270');y=0
 for r in rows:out.paste(r,(0,y));y+=r.height
 out.save(R/'outputs'/name)
menu=[row('UI-00 제목',*consumed(0,'MENU/IF_MISSION_FAILED',3,[17,18],1,(128,128))),row('UI-00 선택 항목',*crop(0,(0,32,128,72))),row('UI-01/03 스테이지 행',*crop(1,(0,58,128,96))),row('UI-12 갤러리 메뉴',*crop(12,(0,28,128,80))),row('UI-13 갤러리 제목',*consumed(13,'MENU/MENU_GALLERY',4,list(range(54,61)),3,(64,128))),row('UI-15 아이템 제목',*consumed(15,'MENU/MENU_ITEM',2,[60,61,62,63,65],1,(128,256))),row('UI-16 옵션',*crop(16,(0,0,256,64)))]
hud=[row('UI-19 독립 상태·단위',*crop(19,(153,35,205,44))),row('UI-20 회전 정보',*consumed(20,'SYSTEM/if_btlsys',0,[4],1,(64,128))),row('UI-20 적 표시',*crop(20,(0,113,64,120))),row('UI-21 경고·준비',*crop(21,(0,0,195,48))),row('UI-23 임무 결과',*consumed(23,'SYSTEM/if_fldsys',12,[52,53],3,(128,128))),row('UI-24 일시정지·기록',*crop(24,(0,0,128,24))),row('UI-25 임무 시작',*consumed(25,'SYSTEM/if_fldsys',23,[3,2,5],0,(128,32))),row('UI-26 임무 완료',*consumed(26,'SYSTEM/if_fldsys',12,[32,55],16,(256,32)))]
save('ui_menu_heritage.png',menu);save('ui_hud_heritage.png',hud)
report={'schema':'brs-ui-independent-review/v1','protected_region_count':len(checks),'protected_regions':checks,'source_ink_regions':ink,'remaining_source_ink':issues,'geometry_scope':'Static SDO point-sampling only; no game code transforms, animation, tint or runtime acceptance proof','source_ink_status':'pass' if not issues else 'fail'}
(R/'qa/ui_remaining_review_v4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'protected_regions':len(checks),'source_ink_regions':len(ink),'uncleared':[{k:v for k,v in it.items() if k!='coordinates'} for it in issues]}))
assert not issues,'Uncleared original label pixels; see report'
