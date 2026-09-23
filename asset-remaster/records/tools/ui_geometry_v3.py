"""SDO-bounded UI corrections. Source coordinates are x1/y1 exclusive.

Evidence: qa/ui_consumers_static.json and qa/ui11_column_read.png.
Source meanings corrected here are authored by Codex internal.
"""
import json
import numpy as np
from PIL import Image,ImageFilter
CORRECTED_IDS={0,1,2,3,4,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26}
REVIEWED_LEGACY_IDS={5,8}
WORDING_CORRECTIONS=[{'assets':['UI-11','UI-14'],'source':'USE','korean':'사용'},
 {'assets':['UI-11','UI-14'],'source':'KEY ITEMS','korean':'중요 아이템'},
 {'assets':['UI-11','UI-14'],'source':'EQUIP','korean':'장비'},
 {'assets':['UI-19'],'source':'OK / __ / R / HP / %','korean':'OK / __ / R / HP / %','reason':'Separate status and unit sprites, not DMG_RANK. Preserve standard HUD abbreviations.'},
 {'assets':['UI-24'],'source':'CHALLENGES / CLEARED','korean':'도전 과제 / 완료','reason':'Separate consumers; restore omitted challenge meaning.'},
 {'assets':['UI-24'],'source':'CLEAR / RECORD','korean':'완료 / 기록','reason':'Restore two independent packed labels.'},
 {'assets':['UI-01','UI-03'],'source':'STAGE 1: SAN FRANCISCO','korean':'1 샌프란시스코'},
 {'assets':['UI-01','UI-03'],'source':'STAGE 4: FUJI JUKAI','korean':'4 후지 수해'},
 {'assets':['UI-01','UI-03'],'source':'STAGE 3: MOSCOW','korean':'3 모스크바','reason':'Restore correct row order; stage 3 and 4 source rows are not sequential.'},
 {'assets':['UI-12'],'source':'/','korean':'/','reason':'Preserve page separator; it is not ALL.'},
 {'assets':['UI-16'],'source':'SFX VOLUME','korean':'효과음 음량'}]

def patch(index,im,g):
 if index not in CORRECTED_IDS:return False
 def label(text,box,maximum=11,fill=None,align='left',ink=None):
  g.clear_exclusive(im,box,g.n.WHITE_TRANSPARENT if fill is None else fill)
  g.draw_box(im,text,box,maximum=maximum,minimum=3,align=align,fill=g.n.WHITE if ink is None else ink)
 def vertical(text,box,clockwise=True,maximum=8,align='left',ink=None):
  g.clear_exclusive(im,box);x,y,x1,y1=box
  tile,size=g.make_text(text,(y1-y)*g.S,(x1-x)*g.S,maximum=maximum,minimum=3,align=align,fill=g.n.WHITE if ink is None else ink)
  im.alpha_composite(tile.rotate(-90 if clockwise else 90,expand=True),(x*g.S,y*g.S))
  g.active['labels'].append({'text':text,'box':box,'size_px':size,'orientation':'clockwise' if clockwise else 'counterclockwise'})
 def evidence(archive,member_index,record_id,texslot,size):
  global _sdo_catalog
  if '_sdo_catalog' not in globals():_sdo_catalog=json.loads((g.R/'qa/ui_consumers_static.json').read_text(encoding='utf-8'))
  ar=next(a for a in _sdo_catalog['records'] if a['archive']==archive)
  member=next(m for m in ar['members'] if 'sdo' in m and (member_index is None or m['index']==member_index));rec=member['sdo']['records'][record_id]
  assert rec['id']==record_id and rec['texture_slot']==texslot
  uv=[rec['uv_normalized'][i]*size[i%2] for i in range(4)];assert all(x==round(x) for x in uv);box=tuple(map(round,uv))
  xy=[rec['layout_xywh'][i]+min(v[i+2] for v in rec['vertices']) for i in range(2)]
  assert all(x==round(x) for x in xy)
  g.active.setdefault('sdo_evidence',[]).append({'archive':archive,'member':member['index'],'member_sha256':member['sha256'],'record':record_id,'texture_slot':texslot,'uv_box':box,'screen_xy':xy,'vertex_bytes_sha256':rec['vertex_bytes_sha256']})
  return rec,box,xy
 def piece(archive,record_id,texslot,size,member_index=None):
  rec,box,xy=evidence(archive,member_index,record_id,texslot,size)
  assert [max(v[i+2] for v in rec['vertices'])-min(v[i+2] for v in rec['vertices']) for i in range(2)]==[box[2]-box[0],box[3]-box[1]]
  return box,*map(round,xy)
 def glow_label(text,box,maximum,ink,glow):
  g.clear_exclusive(im,box);x,y,x1,y1=box
  tile,size=g.make_text(text,(x1-x)*g.S,(y1-y)*g.S,maximum=maximum,minimum=3,fill=ink,edge_margin=2)
  halo=Image.new('RGBA',tile.size,(*glow,0));halo.putalpha(tile.getchannel('A').filter(ImageFilter.GaussianBlur(g.S)).point(lambda a:round(a*0.65)))
  im.alpha_composite(halo,(x*g.S,y*g.S));im.alpha_composite(tile,(x*g.S,y*g.S))
  g.active['labels'].append({'text':text,'box':box,'size_px':size,'orientation':'horizontal','glow_rgb':glow,'ink_rgba':ink})
 def composite(text,pieces,clear_boxes=None,maximum=18,ink=None):
  # Paint the complete phrase once in its consumed layout, then put each part
  # back into its source UV cell. Screen overlaps belong to the first piece.
  # This prevents double alpha compositing in overlapping letter sprites.
  left=min(x for box,x,y in pieces);top=min(y for box,x,y in pieces)
  right=max(x+box[2]-box[0] for box,x,y in pieces);bottom=max(y+box[3]-box[1] for box,x,y in pieces)
  tile,size=g.make_text(text,(right-left)*g.S,(bottom-top)*g.S,maximum=maximum,minimum=3,align='center',fill=g.n.WHITE if ink is None else ink)
  owned=np.zeros((tile.height,tile.width),bool)
  for box in clear_boxes or [p[0] for p in pieces]:g.clear_exclusive(im,box)
  for box,x,y in pieces:
   x0,y0,x1,y1=box;sx=(x-left)*g.S;sy=(y-top)*g.S;w=(x1-x0)*g.S;h=(y1-y0)*g.S
   part=np.array(tile.crop((sx,sy,sx+w,sy+h)));mask=owned[sy:sy+h,sx:sx+w];part[mask,3]=0;mask[:]=True
   im.alpha_composite(Image.fromarray(part),(x0*g.S,y0*g.S))
  g.active['labels'].append({'text':text,'size_px':size,'orientation':'SDO-composite','pieces':[{'box':b,'screen_xy':[x,y]} for b,x,y in pieces],'virtual_size':[right-left,bottom-top],'overlap_alpha_owner':'first'})
  # The text's whole ink must be assigned to an actual consumer.
  assert not (np.array(tile)[:,:,3][~owned]>0).any(),(index,text,'uncovered ink')
 if index==0:
  for rid in [13,14,15,16,17,18]:evidence('MENU/IF_MISSION_FAILED',3,rid,1,(128,128))
  label('임무',(1,1,98,16),18,align='right')
  label('실패',(0,17,91,32),18)
  label('임무 재도전',(1,33,125,43),13)
  label('스테이지 선택',(1,44,126,54),13)
  label('불러오기',(84,55,127,65),13)
 elif index in (1,3):
  # Preserve each >> prefix, both CLEAR helpers, REWARD, and all big icons.
  archive='MENU/IF_REC_INFO' if index==1 else 'MENU/MENU_LIBRARY'
  for rid in [87,88,89,90,91,92]:evidence(archive,None,rid,1,(128,128))
  for text,box in [('1 샌프란시스코',(8,59,121,64)),('2 뉴욕',(8,65,121,70)),('4 후지 수해',(8,71,102,76)),('3 모스크바',(8,77,87,82)),('5 도쿄',(8,83,81,88)),('6 달',(8,89,75,94))]:label(text,box,7)
 elif index in (2,4):
  # IF_REC_INFO SDO 72: [94,1,99,42]; 68..71 use the corner at y43..48.
  vertical('미확인',(94,1,99,42))
 elif index==6:
  # Exact original dark-brown clean plate; retain >>, sloped edge and frame.
  label('임무 목록',(15,3,80,10),7,fill=(10,7,5,255),ink=(229,229,229,255))
  label('나가기',(218,56,255,70),11,align='right',ink=(78,78,78,252))
 elif index==7:
  # IF_STAGE_SELECT SDO 145 + 201 compose INFORM + ATION on one line.
  # A one-pixel gap between the two consumers must fall in the Korean space.
  label('임무',(65,66,97,71),7,align='right')
  label('정보',(65,60,101,65),7)
  label('스테이지',(65,72,101,77),7)
  label('조건',(55,186,102,191),7)
  label('이전',(105,180,128,185),7)
  label('다음',(105,186,128,191),7)
 elif index==9:
  # MENU_CUSTOM SDO 61..66,81..83: individual CUSTOMIZE letter cells.
  pieces=[piece('MENU/MENU_CUSTOM',i,1,(128,64)) for i in [61,62,63,64,65,66,81,82,83]]
  # Low-alpha original shadows extend one pixel beyond the consumed cells.
  # Clear only the measured shadow pixels, preserving unrelated atlas art.
  for box in [(36,4,37,11),(90,4,91,16),(90,25,91,26)]:g.clear_exclusive(im,box)
  composite('커스터마이즈',pieces,maximum=17)
 elif index==10:
  # MENU_CUSTOM SDO 37,38,40,52. Keep both 28px icons and >> markers.
  label('켬',(215,9,232,14),7)
  label('끔',(215,15,232,20),7)
  label('무기 스킬',(164,30,237,35),7)
  label('패시브 스킬',(164,36,241,41),7)
 elif index in (11,14):
  # MENU_ITEM SDO 57,59; button icons start at x56, y12.
  label('공격',(1,1,77,11),12)
  label('블레이드',(1,12,55,22),12)
  # SDO 33..35 are three independently selected, rotated categories.
  # The previous MISC/ITEMS reading of the packed atlas was incorrect.
  vertical('사용',(112,20,117,61))
  vertical('중요 아이템',(106,14,111,61))
  vertical('장비',(100,20,105,47))
 elif index==12:
  for rid in [9,10,20,22,33,35,36,37,41,43,44,45,46]:evidence('MENU/MENU_GALLERY',4,rid,2,(128,128))
  for text,box in [('아트 감상',(8,30,63,35)),('음악 감상',(8,36,77,41)),('영상 감상',(8,42,73,47))]:label(text,box,7)
  label('비어 있음',(1,48,59,58),13)
  label('비어 있음',(33,59,62,65),8)
  label('음악',(90,38,117,43),7,align='center')
 elif index==13:
  all_pieces=[piece('MENU/MENU_GALLERY',i,3,(64,128),4) for i in range(54,61)]
  # Both L sprites consume the same UV. Keep that shared cell empty and
  # place the full Korean title in contiguous E/R/Y sprites, at the right
  # edge of the original title envelope. No source geometry is modified.
  composite('갤러리',all_pieces[4:],clear_boxes=list(dict.fromkeys(p[0] for p in all_pieces)),maximum=17)
  g.active['layout_note']='Gallery title right-aligned within original title envelope; shared repeated L cell blank. Runtime transition review pending.'
 elif index==15:
  pieces=[piece('MENU/MENU_ITEM',i,1,(128,256),2) for i in [60,61,62,63,65]]
  for box,x,y in pieces:g.clear_exclusive(im,box)
  g.clear_exclusive(im,(43,112,44,113))  # Original E shadow in the gutter.
  # The one-pixel gaps between T/E/M sprites become Korean character spacing.
  for text,p in zip('아이템',pieces[1:4]):label(text,p[0],18,align='center',ink=(17,17,17,255))
 elif index==16:
  for rid in range(4,17):
   evidence('MENU/MENU_OPTION',2,rid,0,(256,64))
  for text,box in [('데이터 설치',(1,6,118,16)),('음성 음량',(119,6,238,16)),('BGM 음량',(1,18,104,28)),('효과음 음량',(1,30,104,40)),('자동 넘김',(1,42,115,52)),('끔',(155,24,193,34)),('켬',(155,36,193,46))]:label(text,box,13)
  g.clear_exclusive(im,(105,24,154,35))
  label('음소거',(105,24,154,34),13)
 elif index==17:
  # MENU_OPTION SDO 2/3. The original MAX is x53..92, not x77..128.
  label('최소',(1,6,52,21),12)
  label('최대',(53,6,92,21),12)
 elif index==18:
  # MENU_OPTION repeats one O cell at two screen positions. Keep it blank;
  # put 설정 in the contiguous T/I consumers without altering their geometry.
  all_pieces=[piece('MENU/MENU_OPTION',i,3,(128,64)) for i in [18,19,20,21,23,24]]
  composite('설정',[all_pieces[2],all_pieces[3]],clear_boxes=[p[0] for p in all_pieces],maximum=17)
 elif index==19:
  # These packed cells are status/units, not a DMG_RANK phrase. R and the
  # two underscores remain native until their dynamic consumer is resolved.
  evidence('SYSTEM/if_btlsys',0,20,0,(256,64))
  evidence('SYSTEM/if_btlsys',0,19,0,(256,64))
  evidence('SYSTEM/if_btlsys',0,27,0,(256,64))
  label('OK',(155,37,166,42),7)
  label('HP',(185,37,197,42),7)
  label('%',(198,37,203,42),7)
 elif index==20:
  # The INFORMATION strip is counterclockwise in the atlas; its prefix
  # chevrons are a separate protected part at y107..112.
  evidence('SYSTEM/if_btlsys',0,4,1,(64,128))
  evidence('SYSTEM/if_btlsys',0,38,1,(64,128))
  vertical('정보',(49,43,55,106),clockwise=False,ink=(227,227,227,255))
  label('적',(1,113,41,119),7,ink=(227,227,227,255))
 elif index==21:
  evidence('SYSTEM/if_btlsys',0,28,2,(256,64))
  glow_label('과열',(0,0,110,23),18,(255,238,119,255),(238,0,0))
  # This second alert has a separate dynamic consumer; keep its native band.
  glow_label('블레이드 모드 준비',(0,23,195,47),18,(204,255,255,255),(0,51,255))
 elif index==22:
  # Keep the LOCK ON frame/triangle and the separate square-button icon.
  # Source LOCK ON ink is x49..86, y297..301 inclusive. The y301
  # baseline must be erased; the actual frame's bottom edge is at y304.
  label('조준 고정',(48,296,87,303),7)
  label('사격',(53,339,108,350),12)
 elif index==23:
  # Two independent rotated words. The circular frame ends at x103.
  evidence('SYSTEM/if_fldsys',12,52,3,(128,128))
  evidence('SYSTEM/if_fldsys',12,53,3,(128,128))
  vertical('임무',(116,1,126,65),maximum=13,align='right')
  vertical('결과',(105,1,115,77),maximum=13)
 elif index==24:
  for member,rid in [(26,28),(12,17),(12,19),(12,20),(12,56),(12,57)]:
   evidence('SYSTEM/if_fldsys',member,rid,8,(128,32))
  label('일시정지',(1,1,88,16),18)
  # Preserve >> and the adjacent X; CLEAR and RECORD are distinct cells.
  label('완료',(96,1,113,6),7)
  label('기록',(89,7,125,12),7)
  label('도전 과제',(1,17,60,22),7)
  label('완료',(60,17,105,22),7)
 elif index==25:
  evidence('SYSTEM/if_fldsys',23,2,0,(128,32))
  evidence('SYSTEM/if_fldsys',23,3,0,(128,32))
  evidence('SYSTEM/if_fldsys',23,5,0,(128,32))
  # The source is packed MISSION/BEGIN, but SDO 3+2 displays BEGIN MISSION.
  # Translate the whole consumed phrase, then scatter back into both cells.
  composite('임무 시작',[piece('SYSTEM/if_fldsys',3,0,(128,32),23),piece('SYSTEM/if_fldsys',2,0,(128,32),23)],maximum=18)
  label('시간',(85,17,108,22),7)
 elif index==26:
  for rid in [32,33,34,54,55]:evidence('SYSTEM/if_fldsys',12,rid,16,(256,32))
  label('임무',(0,10,117,25),18,align='right')
  label('완료',(118,10,245,25),18)
 g.active['geometry_review']='SDO coordinates and fixed-ISO pixel boundaries; runtime acceptance pending'
 return True
