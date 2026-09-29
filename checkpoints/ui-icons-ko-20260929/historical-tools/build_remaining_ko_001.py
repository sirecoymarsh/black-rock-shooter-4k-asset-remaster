"""Complete remaining atlas English; exact source-bound 8x UI replacements.

Observed bindings are preferred. Additional keys are derived from contiguous
source LPK bytes by the algorithm already cross-checked against observed UI.
Derived bindings remain explicitly distinguished from runtime observations.
"""
from pathlib import Path
import sys,json,hashlib,configparser,shutil,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import font_heritage as style
from ptmd_codec import decode_ptmd,unswizzle_psp,_decode_indexes
R=Path(__file__).resolve().parents[1]
import xxhash
sys.stdout.reconfigure(encoding='utf8');sys.dont_write_bytecode=True
S=8;OUT=R/'workspace/ui-remaining-ko-001';REVIEW=R/'outputs/ui-remaining-ko-001'
BASE=R/'workspace/ui-title-ko-002/pack/PSP/TEXTURES/NPUH10126'
PACK=OUT/'pack/PSP/TEXTURES/NPUH10126'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dh(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
def sb(b):return tuple(round(x*S) for x in b)
def entry(src,ko,box,**kw):return dict(source=src,korean=ko,box=box,**kw)
P='system.vol::005_if_rsdsys.lpk::';B='system.vol::007_if_btlsys.lpk::'
SPECS=[
dict(id='MUI-01',asset='if::menu::if_rec_info.gz::005',prior='UI-01',labels=[
 entry('TO UNLOCK','해금 조건',[58,46,96,58]),entry('TO CLEAR','완료 조건',[85,84,123,96]),
 entry('REWARD','보상',[88,76,127,84],slot=[89,77,126,83]),entry('CLEAR','완료',[103,46,120,51]),entry('NO.','번호',[91,30,104,35])]),
dict(id='MUI-05',asset='if::menu::if_stage_select.gz::014',prior='UI-05',labels=[
 entry('STAGE SELECT','스테이지 선택',[0,0,128,11],slot=[1,0,128,10]),entry('LOAD','불러오기',[0,22,46,32]),
 entry('SAVE','저장',[0,11,46,21]),entry('HUNT','헌트',[57,11,104,21]),entry('MENU','메뉴',[0,32,46,42]),entry('STORY','스토리',[46,32,128,42]),
 entry('EXTRA','추가 임무',[57,22,114,32]),entry('MISSION','임무',[0,43,39,48],slot=[1,43,38,48]),
 entry('REC. LEVEL','권장 레벨',[39,43,93,48],slot=[39,43,91,48]),entry('TYPE','유형',[93,43,116,48])]),
dict(id='MUI-16',asset='if::menu::menu_option.gz::005',prior='UI-16',labels=[entry('BGM VOLUME','배경음 음량',[1,18,104,28],align='left')]),
dict(id='MUI-19',asset=B+'003',prior='UI-19',labels=[entry('OK','준비',[155,37,166,42]),entry('HP','체력',[185,37,197,42])]),
dict(id='RUI-007',asset=P+'016',labels=[entry('HP','체력',[20,1,32,6])]),
dict(id='RUI-008',asset=P+'018::015',labels=[entry('LV','레벨',[24,10,37,17],clean=[40,40,40,255],ink=[233,234,220,255])]),
dict(id='RUI-009',asset=P+'018::016',clear_family=[[0,38,85,56],[0,37,27,38]],labels=[
 entry('OVER / HEAT','과열',[1,37,24,50]),entry('STUN','기절',[1,51,27,56]),entry('JUST','정확',[28,51,54,56]),entry('GOOD','성공',[55,51,79,56]),
 entry('STATUS / DOWN','능력\n저하',[28,38,54,50]),entry('BAD / EFFECT','상태\n이상',[55,39,73,50],extra=[[73,44,77,50]]),entry('UP','상승',[73,39,83,44])]),
dict(id='RUI-010',asset=P+'019::007',labels=[
 entry('CHALLE / NGES','도전 과제',[1,1,11,66],rotate=True,extra=[[22,1,32,44]]),
 entry('MAX','최대',[12,1,22,33],rotate=True),
 entry('HP','체력',[12,34,22,55],rotate=True),
]),
dict(id='RUI-011',asset=P+'020',labels=[
 entry('ATK','공격',[16,182,32,188],color_mask=True,ink=[198,86,94,255]),
 entry('DEF','방어',[32,182,48,188],color_mask=True,ink=[119,149,100,255]),
 entry('SPD','속도',[48,182,64,188],color_mask=True,ink=[82,174,211,255]),
 entry('ATK','공격',[0,198,16,204],color_mask=True,ink=[198,86,94,255]),
 entry('DEF','방어',[16,198,32,204],color_mask=True,ink=[119,149,100,255]),
 entry('SPD','속도',[32,198,48,204],color_mask=True,ink=[82,174,211,255])]),
dict(id='RUI-012',asset=P+'021::004',labels=[
 entry('CHALLENGE','도전 과제',[9,1,14,54],rotate=True),entry('UNLOCKED','해금',[15,1,20,48],rotate=True),
 entry('CLEARED','완료',[27,1,32,42],rotate=True),entry('CLEAR','완료',[21,1,26,18],rotate=True)]),
dict(id='BUI-001',asset=B+'006::003',labels=[entry('ITEMS FOUND','획득 아이템',[54,6,63,69],rotate=True,blue_plate=True,ink=[195,220,240,220])]),
dict(id='BUI-002',asset=B+'006::004',labels=[
 entry('RESULT(S)','결과',[0,5,67,17],slot=[1,6,23,16],reason='Shared S crop [23,6,33,16] kept blank; Korean has no plural suffix.'),
 entry('BATTLE','전투',[0,28,67,40],slot=[1,28,66,38],align='right'),entry('LV','레벨',[67,5,87,17],slot=[67,6,87,16]),
 entry('LEVEL','레벨',[0,17,56,28],slot=[1,17,55,27],align='right'),entry('UP','상승',[56,17,83,28],slot=[56,17,82,27]),
 entry('RANK','등급',[99,17,123,22]),entry('NEXT','다음',[99,22,123,28],slot=[99,22,122,27]),
 entry('EXP','경험치',[99,28,117,34],slot=[99,28,116,33]),entry('EARNED','획득',[92,34,128,40],slot=[93,34,128,39])]),
dict(id='BUI-003',asset=B+'011::003',labels=[entry('CLOSE','닫기',[1,11,30,16],ink=[0,0,0,255],align='right'),entry('ITEM','아이템',[9,17,29,22],ink=[0,0,0,255]),entry('S (ITEMS plural tail)','',[25,5,30,10],reason='Consumer 23 appends English plural S; Korean label needs no suffix.')]),
dict(id='MUI-27',asset='if::menu::if_rec_info.gz::009',labels=[entry('CHALLENGES','도전 과제',[0,0,64,40],composite=[[[41,1,60,20],0],[[1,1,20,20],17],[[1,21,20,40],34]],reason='Shared L and E sprites must stay empty. Complete Korean occupies C/H/A union, 53x19 native; SDO geometry unchanged.')]),
dict(id='MUI-28',asset='if::menu::if_rec_info.gz::010',labels=[entry('G / S (CHALLENGES tail)','',[44,0,64,48],reason='Word rendered as a complete semantic unit in MUI-27; remove all glyph shadow pixels and preserve trophy.')]),
]

def binding_source(t,links):
 src=Path(t['source']);b=src.read_bytes();assert dh(b)==t['decoded_sha256']
 tex=decode_ptmd(b);parent=src.parent/'container.lpk';raw=parent.read_bytes()
 assert dh(raw)==t['origin'].get('parent_sha256',dh(raw))
 off=t['origin']['offset'];assert raw[off:off+len(b)]==b
 stride=tex.width//2 if tex.mode==4 else tex.width;ph=t['padded_height']
 data=raw[off+16:off+16+ph*stride]
 # A last member's PSP padding may extend beyond its nested LPK. Preserve
 # actual enclosing bytes only when the complete child is embedded exactly.
 nesting=[]
 while len(data)<ph*stride:
  outer=parent.parent.parent/'container.lpk';outer_raw=outer.read_bytes();at=outer_raw.find(raw)
  assert at>=0 and outer_raw.find(raw,at+1)<0,(t['id'],'ambiguous enclosing LPK')
  nesting.append(dict(child=str(parent),parent=str(outer),child_offset=at))
  off+=at;parent=outer;raw=outer_raw;data=raw[off+16:off+16+ph*stride]
 linear=unswizzle_psp(data,stride,ph);idx=_decode_indexes(linear,tex.mode,tex.width*ph)
 rgba=np.array(tex.palette_rgba,np.uint8)[np.frombuffer(idx,np.uint8)].reshape(ph,tex.width,4)
 im=Image.fromarray(rgba);assert im.crop((0,0,tex.width,tex.height)).tobytes()==tex.rgba_bytes
 dimension=(tex.width.bit_length()-1)|((ph.bit_length()-1)<<8)
 clutfmt=0xc500ff00|(2 if tex.palette_code==0x20 else 3)
 low=xxhash.xxh32(b[tex.palette_offset:],seed=0xc0108888).intdigest()^clutfmt^dimension
 # Include the complete last translated row in every shortened hash. Short
 # blank prefixes can collide with unrelated atlases using the same palette.
 assert ph!=512 or 'UI-22' in t.get('prior_ui_ids',[]),t['id']
 heights=range(350,ph+1) if ph==512 else [ph]
 keys={'00000000'+f'{low:08x}'+f'{xxhash.xxh64(data[:height*stride],seed=0xBACD7814).intdigest()&0xffffffff:08x}':height for height in heights}
 observed={m['key']:m for m in links.get(t['id'],[])}
 for k,m in observed.items():
  assert k in keys,(t['id'],k,'raw source key mismatch')
  captured=Image.open(m['paths'][0]).convert('RGBA');assert captured.tobytes()==im.tobytes(),t['id']
 return im,dict(keys=keys,observed=sorted(observed),parent=str(parent),parent_sha256=dh(raw),offset=off,source_sha256=dh(b),enclosing_lpk=nesting,padding='Decoded from actual contiguous LPK bytes; no transparent padding invented. Unobserved enclosing-LPK cases require runtime confirmation.')

def typeset(text,w,h,ink,align='center'):
 style.require_chars(text);lines=text.split('\n');out=Image.new('RGBA',(w,h),(255,255,255,0))
 for n,line in enumerate(lines):
  mask=style.text_ink(line,128);pad=Image.new('L',(mask.width+16,mask.height+16));pad.paste(mask,(8,8))
  pad=Image.blend(pad,pad.filter(ImageFilter.MaxFilter(3)),.45);mask=pad.crop(pad.getbbox())
  height=h//len(lines)-2;width=min(w-2,round(mask.width*height/mask.height*1.35))
  mask=mask.resize((width,height),Image.Resampling.LANCZOS)
  tile=Image.new('RGBA',mask.size,tuple(ink[:3])+ (0,));tile.putalpha(mask.point(lambda a:round(a*ink[3]/255)))
  xx=w-width-1 if align=='right' else 1 if align=='left' else (w-width)//2
  out.alpha_composite(tile,(xx,n*(h//len(lines))+1))
 return out

def patch(im,spec):
 before=np.array(im);clean=before.copy();owned=np.zeros(before.shape[:2],bool);layer=Image.new('RGBA',im.size,(255,255,255,0));details=[]
 for box in spec.get('clear_family',[]):
  x,y,x1,y1=sb(box);clean[y:y1,x:x1]=[255,255,255,0];owned[y:y1,x:x1]=True
 for l in spec['labels']:
  x,y,x1,y1=sb(l['box']);region=clean[y:y1,x:x1];native=np.array(im.resize((im.width//S,im.height//S),Image.Resampling.NEAREST))
  if l.get('blue_plate'):
   # White letters have R>=177; plate R is 34. Each row's plate is recovered
   # from text-free horizontal neighbors at the same y, retaining its gradient.
   bx,by,bx1,by1=l['box'];native_region=native[by:by1,bx:bx1];mask=native_region[:,:,0]>100
   repaired=native_region.copy()
   for yy in range(by,by1):
    row=native[yy,53:64];bg=row[row[:,0]==34];assert len(bg)>0
    color=np.median(bg,axis=0).round().astype(np.uint8);repaired[yy-by,mask[yy-by]]=color
   expanded=np.repeat(np.repeat(mask,S,0),S,1);region[expanded]=np.repeat(np.repeat(repaired,S,0),S,1)[expanded];owned[y:y1,x:x1]|=expanded
  elif l.get('color_mask'):
   rgb=region[:,:,:3].astype(int);mask=(rgb.max(2)-rgb.min(2)>30)&(region[:,:,3]>0)
   colors,counts=np.unique(region[mask],axis=0,return_counts=True);assert len(colors)>0
   l=dict(l,ink=colors[counts.argmax()].tolist());region[mask]=[0,0,0,255];owned[y:y1,x:x1]|=mask
  else:
   region[:]=l.get('clean',[255,255,255,0]);owned[y:y1,x:x1]=True
  for extra in l.get('extra',[]):
   xx,yy,xx1,yy1=sb(extra);clean[yy:yy1,xx:xx1]=[255,255,255,0];owned[yy:yy1,xx:xx1]=True
  slot=l.get('slot',l['box']);xx,yy,xx1,yy1=sb(slot);rot=l.get('rotate',False)
  w,h=(yy1-yy,xx1-xx) if rot else (xx1-xx,yy1-yy)
  if not l['korean']:
   details.append(dict(l,uid=spec['id']+'/'+str(len(details)+1),translator_model='Codex internal'));continue
  if l.get('composite'):
   full=typeset(l['korean'],53*S,19*S,[255,255,255,255]);taken=np.zeros((19*S,53*S),bool)
   for box,at in l['composite']:
    a=np.array(full.crop((at*S,0,(at+19)*S,19*S)));used=taken[:,at*S:(at+19)*S];a[used,3]=0;used[:]=True
    layer.alpha_composite(Image.fromarray(a),(box[0]*S,box[1]*S))
   details.append(dict(l,uid=spec['id']+'/'+str(len(details)+1),translator_model='Codex internal'));continue
  tile=typeset(l['korean'],w,h,l.get('ink',[255,255,255,255]),l.get('align','center'))
  if rot:tile=tile.transpose(Image.Transpose.ROTATE_270)
  layer.alpha_composite(tile,(xx,yy));details.append(dict(l,uid=spec['id']+'/'+str(len(details)+1),translator_model='Codex internal'))
 clean_im=Image.fromarray(clean);result=clean_im.copy();result.alpha_composite(layer);owned|=np.array(layer)[:,:,3]>0
 assert np.array_equal(np.array(result)[~owned],before[~owned])
 return result,clean_im,layer,Image.fromarray(owned.astype('uint8')*255),details

def build():
 for p in [OUT,REVIEW,PACK]:p.mkdir(parents=True,exist_ok=True)
 inv=read(R/'qa/ui_inventory_expanded.json');textures={t['id']:t for t in inv['textures']};links=read(R/'qa/ui_expanded_links.json')['assets']
 c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(BASE/'textures.ini',encoding='utf8')
 for rel in set(c['hashes'].values()):
  d=PACK/rel;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(BASE/rel,d)
 old=read(R/'qa/ui_build_v4.json');prior={r['id']:r for r in old['records']}
 records=[];all_specs=list(SPECS)
 # Activate the eight already-localized but previously unobserved families,
 # keeping calculated keys distinct from captured keys.
 for r in old['records']:
  if not r['bindings']:
   t=next(t for t in inv['textures'] if r['id'] in t.get('prior_ui_ids',[]))
   all_specs.append(dict(id=r['id'],asset=t['id'],prior=r['id'],labels=[]))
 for spec in all_specs:
  t=textures[spec['asset']];full,proof=binding_source(t,links);source=full.resize((full.width*S,full.height*S),Image.Resampling.NEAREST)
  initial=source.copy()
  if spec.get('prior'):
   p=prior[spec['prior']];candidate=Image.open(p['candidate']).convert('RGBA');w,hh=p['logical_size'];initial.paste(candidate.crop((0,0,w*S,hh*S)),(0,0))
  final,clean,layer,mask,labels=patch(initial,spec);adir=OUT/'assets'/spec['id'];adir.mkdir(parents=True,exist_ok=True)
  files={}
  for role,img in [('source',source),('before',initial),('clean',clean),('layer',layer),('mask',mask),('candidate',final)]:
   p=adir/(role+'.png');img.save(p,optimize=True);files[role]={'path':str(p),'sha256':h(p)}
  relative='remaining-ko-001/'+spec['id']+'.png';dest=PACK/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(adir/'candidate.png',dest)
  for k in proof['keys']:c['hashes'][k]=relative
  rec=dict(id=spec['id'],asset=spec['asset'],source_sha256=t['decoded_sha256'],logical_size=[t['width'],t['height']],binding=proof,labels=labels,files=files,replacement=relative,output_sha256=h(dest),runtime_verified=False)
  records.append(rec)
  # Each proof includes the whole logical atlas and only changed label crops.
  crops=[]
  for l in labels:
   box=l['box'];a=initial.crop(sb(box));b=final.crop(sb(box));cl=clean.crop(sb(box))
   if l.get('rotate'):a=a.transpose(Image.Transpose.ROTATE_90);b=b.transpose(Image.Transpose.ROTATE_90);cl=cl.transpose(Image.Transpose.ROTATE_90)
   crops.append((l,a,cl,b))
  for start in range(0,len(crops),5):
   chunk=crops[start:start+5];height=sum(max(90,a.height+30) for _,a,_,_ in chunk)
   sheet=Image.new('RGB',(1500,height+36),'#263344');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
   d.text((8,2),spec['id']+'   이전 / 지운 바탕 / 한국어',font=font,fill='white');yy=35
   for l,a,cl,b in chunk:
    d.text((8,yy),l['source']+' → '+l['korean'].replace('\n',' '),font=font,fill='white')
    for n,img in enumerate([a,cl,b]):
     if img.width>480:img=img.resize((480,round(img.height*480/img.width)))
     sheet.paste(img,(8+n*500,yy+25),img)
    yy+=max(90,a.height+30)
   sheet.save(REVIEW/(spec['id']+f'-words-{start//5+1}.png'))
  w,hh=t['width'],t['height'];scale=min(6,900/w,1400/hh)
  comparison_before=source if not spec['labels'] else initial
  ims=[im.crop((0,0,w*S,hh*S)).resize((round(w*scale),round(hh*scale)),Image.Resampling.LANCZOS) for im in [comparison_before,final]]
  sheet=Image.new('RGB',(ims[0].width*2+40,ims[0].height+40),'#33465a');d=ImageDraw.Draw(sheet)
  d.text((8,8),spec['id']+'   before / Korean',font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18),fill='white')
  for n,im in enumerate(ims):sheet.paste(im,(n*(im.width+20)+8,35),im)
  sheet.save(REVIEW/(spec['id']+'-atlas.png'))
 with (PACK/'textures.ini').open('w',encoding='utf8') as f:c.write(f)
 m=dict(schema='brs-remaining-ko-001/v1',translator_model='Codex internal',baseline=str(BASE),baseline_ini_sha256=h(BASE/'textures.ini'),font=style.PROFILE,build_script_sha256=h(Path(__file__)),records=records,asset_count=len(records),semantic_entry_count=sum(bool(l['korean']) for r in records for l in r['labels']),total_keys=len(c['hashes']),calculated_binding_note='Keys without captured observations are exact contiguous-source hypotheses; runtime verification pending. UI-22 shortened hashes cover at least all 350 translated rows; no short blank-prefix or wildcard keys.',required_companion_iso=str(R/'workspace/ui-title-ko-002/BRS_UI_title_v2.iso'),runtime_verified=False,live_installation_performed=False)
 write(OUT/'manifest.json',m);write(R/'qa/ui_remaining_ko_001.json',m)
 print(json.dumps({k:m[k] for k in ['asset_count','semantic_entry_count','total_keys']}))
if __name__=='__main__':build()
