"""Rebuild frozen Korean UI wording at 8x, preserving current-ISO art and observed padding."""
import sys,json,hashlib,math,shutil
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageFont,ImageDraw
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1];import frozen_ui_wording as n
import ui_geometry_v3 as geometry
S=8;FONT=Path(r'C:\Windows\Fonts\NotoSansKR-VF.ttf');out=R/'workspace/build-v3/PSP/TEXTURES/NPUH10126';(out/'ui').mkdir(parents=True,exist_ok=True);candidate=R/'workspace/ui_candidates_v3';candidate.mkdir(exist_ok=True)
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'));active={};records=[];bindings={};bound_pixels={};rows=[]
def h(b):return hashlib.sha256(b).hexdigest()
@lru_cache(None)
def font(size):
 f=ImageFont.truetype(str(FONT),size);f.set_variation_by_name('Bold');return f
def mark(box):
 x0,y0,x1,y1=box
 if not(0<=x0<x1<=active['width'] and 0<=y0<y1<=active['height']):raise ValueError(('outside logical canvas',active['id'],box))
 active['editable'][y0:y1,x0:x1]=True

def clear(image,box,color=n.WHITE_TRANSPARENT,exclusive=False):
 x0,y0,x1,y1=box
 if not exclusive:x1+=1;y1+=1
 # Native Pillow clears clip to the logical image, never into runtime padding.
 x1=min(x1,active['width']);y1=min(y1,active['height'])
 mark((x0,y0,x1,y1));active['clears'].append({'box':[x0,y0,x1,y1],'rgba':color})
 ImageDraw.Draw(image).rectangle((x0*S,y0*S,x1*S-1,y1*S-1),fill=color)
def clear_exclusive(image,box,color=n.WHITE_TRANSPARENT):return clear(image,box,color,True)
def make_text(text,w,h,maximum,minimum=5,fill=n.WHITE,align='left',valign='center',spacing=0,stroke_width=0,stroke_fill=n.BLACK,edge_margin=0,**kw):
 probe=ImageDraw.Draw(Image.new('L',(1,1)));margin=edge_margin*S;sw=stroke_width*S;sp=spacing*S;mw=w-2*margin;mh=h-2*margin
 selected=None
 for size in range(maximum*S,max(12,minimum*S)-1,-1):
  f=font(size);box=probe.multiline_textbbox((0,0),text,font=f,spacing=sp,stroke_width=sw)
  if box[2]-box[0]<=mw and box[3]-box[1]<=mh:selected=f;break
 if selected is None:raise ValueError(('text cannot fit',active['id'],text,w,h,minimum,maximum))
 bw,bh=box[2]-box[0],box[3]-box[1]
 x=margin+(mw-bw if align=='right' else (mw-bw)//2 if align=='center' else 0)-box[0]
 y=margin+(mh-bh if valign=='bottom' else (mh-bh)//2 if valign=='center' else 0)-box[1]
 tile=Image.new('RGBA',(w,h),(255,255,255,0));d=ImageDraw.Draw(tile);d.multiline_text((x,y),text,font=selected,fill=fill,spacing=sp,align=align,stroke_width=sw,stroke_fill=stroke_fill)
 # A larger guard image independently checks clipping beyond the declared rectangle.
 g=16;guard=Image.new('L',(w+2*g,h+2*g));ImageDraw.Draw(guard).multiline_text((x+g,y+g),text,font=selected,fill=255,spacing=sp,align=align,stroke_width=sw,stroke_fill=255);ga=np.array(guard);ga[g:g+h,g:g+w]=0
 if ga.any():raise ValueError(('ink outside text box',active['id'],text))
 return tile,selected.size

def draw_box(image,text,box,**kw):
 mark(box);x0,y0,x1,y1=box;tile,size=make_text(text,(x1-x0)*S,(y1-y0)*S,**kw);image.alpha_composite(tile,(x0*S,y0*S));active['labels'].append({'text':text,'box':box,'size_px':size,'orientation':'horizontal'})
def draw_vertical(image,text,box,clockwise=True,**kw):
 mark(box);x0,y0,x1,y1=box;kw['align']='center';tile,size=make_text(text,(y1-y0)*S,(x1-x0)*S,**kw);tile=tile.rotate(-90 if clockwise else 90,expand=True);image.alpha_composite(tile,(x0*S,y0*S));active['labels'].append({'text':text,'box':box,'size_px':size,'orientation':'clockwise' if clockwise else 'counterclockwise'})
n.clear=clear;n.clear_exclusive=clear_exclusive;n.draw_box=n.draw_pixel_box=draw_box;n.draw_vertical=n.draw_pixel_vertical=draw_vertical

def render(base,a,spec):
 global active
 active={'id':a['id'],'width':a['width'],'height':a['height'],'editable':np.zeros((base.height,base.width),bool),'clears':[],'labels':[]}
 before=base.resize((base.width*S,base.height*S),Image.Resampling.NEAREST);im=before.copy()
 if geometry.patch(a['index'],im,sys.modules[__name__]):pass
 elif a['index']==0:
  # Preserve wording and boxes from the old HD pack's special-case mission-failure renderer.
  clear_exclusive(im,(0,0,127,56));clear_exclusive(im,(65,56,127,71));draw_box(im,'임무 실패',(1,0,127,25),maximum=23);draw_box(im,'임무 재도전',(1,25,127,40),maximum=13);draw_box(im,'스테이지 선택',(1,40,127,55),maximum=12);draw_box(im,'불러오기',(65,56,127,71),maximum=12,align='right')
 else:
  spec.patcher(im)
  if a['index'] in geometry.REVIEWED_LEGACY_IDS:active['geometry_review']='Known SDO consumers and visible protected pixels reviewed; remaining dynamic consumers unverified'
 mask=np.repeat(np.repeat(active['editable'],S,0),S,1);aa=np.array(im);bb=np.array(before);assert np.array_equal(aa[~mask],bb[~mask]),a['id']
 return im,{'protected_rgba_pass':True,'clipping_pass':True,'labels':active['labels'],'clear_regions':active['clears'],'editable_native_pixel_count':int(active['editable'].sum()),'geometry_review':active.get('geometry_review','Legacy coordinate review pending'),'sdo_evidence':active.get('sdo_evidence',[]),'layout_note':active.get('layout_note')}

for a,spec in zip(audit['assets'],n.SPECS):
 assert a['relative']==spec.relative
 logical=Image.open(Path(a['source']).with_suffix('.png')).convert('RGBA');base=Image.new('RGBA',(a['padded_width'],a['padded_height']),(255,255,255,0));base.paste(logical,(0,0));im,proof=render(base,a,spec)
 fn=a['id']+'_8x.png';im.save(candidate/fn,optimize=True)
 rec={'id':a['id'],'source_relative':a['relative'],'source_ptmd_sha256':a['iso_ptmd_sha256'],'candidate':str(candidate/fn),'candidate_sha256':h((candidate/fn).read_bytes()),'source_size':base.size,'logical_size':logical.size,'output_size':im.size,'method':'Korean labels rerasterized from Noto Sans KR Bold with source-backed wording and consumer-bound corrections. Original ornament, portraits, numeric cells and alpha preserved outside declared text regions. This is not a claim that all nontext art is remastered.','proof':proof,'bindings':[],'runtime_verified':False}
 for match in a['matches']:
  source=Path(match['path']);base2=Image.open(source).convert('RGBA');assert h(base2.tobytes())==match['full_rgba_sha256'];rebuilt,pr=render(base2,a,spec);key=match['key'];digest=h(rebuilt.tobytes())
  if key in bindings:assert bound_pixels[key]==digest,(a['id'],key,'conflict')
  else:
   dest=out/'ui'/f'{key}.png';rebuilt.save(dest,optimize=True);bindings[key]='ui/'+dest.name;bound_pixels[key]=digest
   snap=R/'workspace/source/ui/dumps'/source.name;snap.parent.mkdir(exist_ok=True);shutil.copyfile(source,snap)
  rec['bindings'].append({'key':key,'replacement':bindings[key],'output_rgba_sha256':digest,'source_rgba_sha256':match['full_rgba_sha256'],'padding_preserved':True})
 records.append(rec)
 # Presentation compares source and new UI at the same displayed width.
 old=logical.resize((logical.width*4,logical.height*4),Image.Resampling.NEAREST);new=im.crop((0,0,logical.width*S,logical.height*S)).resize(old.size,Image.Resampling.LANCZOS)
 row=Image.new('RGB',(2100,max(old.height,new.height)+48),'#172237');dd=ImageDraw.Draw(row);dd.text((12,10),a['id']+'  '+a['relative'],font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',20),fill='white');row.paste(old,(12,42),old);row.paste(new,(1062,42),new);rows.append(row)
# Merge font bindings after the independent font build has completed, via a separate packaging step.
(R/'qa/ui_bindings_v3.json').write_text(json.dumps(bindings,indent=2),encoding='utf-8')
manifest={'schema':'brs-hd-ui/v3','translator_model':'Codex internal','translation_change':'Source-backed corrections to misread categories, stage rows, omitted HUD terms and abbreviations; unchanged wording inherited from the frozen source. See wording_corrections.','wording_corrections':geometry.WORDING_CORRECTIONS,'geometry_corrected_ids':[f'UI-{i:02d}' for i in sorted(geometry.CORRECTED_IDS)],'geometry_reviewed_unchanged_ids':[f'UI-{i:02d}' for i in sorted(geometry.REVIEWED_LEGACY_IDS)],'wording_source_sha256':h((R/'tools/frozen_ui_wording.py').read_bytes()),'geometry_source_sha256':h((R/'tools/ui_geometry_v3.py').read_bytes()),'scale':S,'font':str(FONT),'font_sha256':h(FONT.read_bytes()),'asset_count':len(records),'mapped_asset_count':sum(bool(r['bindings']) for r in records),'exact_binding_count':len(bindings),'broad_wildcards':0,'runtime_status':'unverified; not release eligible','records':records}
(R/'qa/ui_build_v3.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for start in range(0,len(rows),9):
 block=rows[start:start+9];sheet=Image.new('RGB',(2100,sum(x.height for x in block)),'#172237');y=0
 for row in block:sheet.paste(row,(0,y));y+=row.height
 sheet.save(R/f'outputs/ui_comparison_v3_{start//9+1}.png')
print(json.dumps({k:manifest[k] for k in ['asset_count','mapped_asset_count','exact_binding_count','broad_wildcards']}))
