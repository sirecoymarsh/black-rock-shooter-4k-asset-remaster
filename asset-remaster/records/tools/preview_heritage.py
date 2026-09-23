"""Side-by-side design evidence from fixed source and both candidate builds."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];S=8
audit=json.loads((R/'qa/ui_source_audit.json').read_text('utf8'));sdo=json.loads((R/'qa/ui_consumers_static.json').read_text('utf8'))
def inputs(i):
 return [Image.open(Path(audit['assets'][i]['source']).with_suffix('.png')).convert('RGBA')]+[Image.open(R/f'workspace/ui_candidates_v{v}/UI-{i:02d}_8x.png').convert('RGBA') for v in [3,4]]
def crop(i,box):
 out=[]
 for k,im in enumerate(inputs(i)):
  scale=1 if k==0 else S;im=im.crop(tuple(v*scale for v in box))
  if k==0:im=im.resize((im.width*S,im.height*S),Image.Resampling.NEAREST)
  out.append(im)
 return out
def compose(i,archive,member,ids,size):
 ar=next(a for a in sdo['records'] if a['archive']==archive);m=next(m for m in ar['members'] if m['index']==member)
 pieces=[]
 for rid in ids:
  r=m['sdo']['records'][rid];box=tuple(round(v*size[n%2]) for n,v in enumerate(r['uv_normalized']));xy=[round(r['layout_xywh'][n]+min(v[n+2] for v in r['vertices'])) for n in range(2)];pieces.append((box,*xy))
 left=min(x for b,x,y in pieces);top=min(y for b,x,y in pieces);w=max(x+b[2]-b[0] for b,x,y in pieces)-left;h=max(y+b[3]-b[1] for b,x,y in pieces)-top;out=[]
 for k,im in enumerate(inputs(i)):
  dest=Image.new('RGBA',(w*S,h*S));scale=1 if k==0 else S
  for b,x,y in pieces:
   tile=im.crop(tuple(v*scale for v in b))
   if k==0:tile=tile.resize((tile.width*S,tile.height*S),Image.Resampling.NEAREST)
   dest.alpha_composite(tile,((x-left)*S,(y-top)*S))
  out.append(dest)
 return out
samples=[('조준 고정 · 원본 프레임 안에 배치',crop(22,(44,293,98,306))),('임무 목록 · 작은 표시',crop(6,(10,0,85,12))),('커스터마이즈 · 분할 제목 조립',compose(9,'MENU/MENU_CUSTOM',2,[61,62,63,64,65,66,81,82,83],(128,64))),('갤러리 · 반복 글자 슬롯 보호',compose(13,'MENU/MENU_GALLERY',4,list(range(54,61)),(64,128)))]
width=1890;rows=[];f=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',24)
for title,ims in samples:
 factor=min(1,600/max(i.width for i in ims));height=max(round(i.height*factor) for i in ims);row=Image.new('RGB',(width,height+65),'#243449');d=ImageDraw.Draw(row);d.text((15,8),title,font=f,fill='white')
 for col,im in enumerate(ims):
  im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);row.paste(im,(15+630*col,48),im)
 rows.append(row)
head=110;out=Image.new('RGB',(width,sum(r.height for r in rows)+head+60),'#243449');d=ImageDraw.Draw(out)
d.text((15,12),'원본의 직선적인 획을 살린 한글 후보',font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',32),fill='white')
for col,title in enumerate(['원본 영문','이전 한글 · Noto','수정 후보 · Orbit']):d.text((15+630*col,65),title,font=f,fill='white')
y=head
for r in rows:out.paste(r,(0,y));y+=r.height
d.text((15,y+12),'정적 텍스처·표시 좌표 비교입니다. 실제 게임 적용 화면은 아직 검증 전입니다.',font=f,fill='#c9d6e7')
out.save(R/'outputs/font_heritage_design.png')
print(out.size)

