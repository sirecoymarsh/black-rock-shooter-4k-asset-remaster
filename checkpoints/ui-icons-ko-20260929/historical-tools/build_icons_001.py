"""Faithful icon remaster: source-traced geometry and local neural relief detail.

Produces a staged, cumulative UI-only overlay. Never touches the live game.
"""
from pathlib import Path
import sys,json,hashlib,configparser,math,ast,shutil,time
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf8')
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt
from skimage.measure import find_contours,approximate_polygon
import cv2,xxhash
from ptmd_codec import decode_ptmd,unswizzle_psp,_decode_indexes
from icon_specs_001 import SPECS
import local_sr as sr
R=Path(__file__).resolve().parents[1];S=8
O=R/'workspace/ui-icons-001';V=R/'outputs/ui-icons-001'
BASE=R/'workspace/ui-remaining-ko-001/pack/PSP/TEXTURES/NPUH10126'
PACK=O/'ui-overlay/PSP/TEXTURES/NPUH10126'
def read(p):return json.loads(p.read_text('utf8'))
def dh(b):return hashlib.sha256(b).hexdigest()
def h(p):return dh(p.read_bytes())
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2),'utf8')
def sb(b):return tuple(round(v*S) for v in b)

def load_binding():
 # Reuse the already observed-verified exact byte hashing implementation.
 # Its ph512 guard belongs to its translation batch, not to icon source types.
 tree=ast.parse((R/'tools/build_remaining_ko_001.py').read_text('utf8'))
 fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='binding_source')
 fn.body=[n for n in fn.body if not (isinstance(n,ast.Assert) and 'ph != 512' in ast.unparse(n))]
 for n in fn.body:
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='heights' for t in n.targets):
   n.value=ast.parse("range(350,ph+1) if 'UI-22' in t.get('prior_ui_ids',[]) else [ph]",mode='eval').body
 exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'binding_source_icons','exec'),globals())

def trace_alpha(src,scale=S):
 """Recover subpixel contour at 50% coverage, simplify staircase runs.

 Original fringe/soft shadow remains at its original low opacity. Main face
 is rerasterized from editable SVG polygons, not nearest-neighbor expansion.
 """
 a=np.asarray(src.getchannel('A'));mx=int(a.max())
 if mx==0:return Image.new('L',(src.width*scale,src.height*scale)),[]
 paths=[]
 for c in find_contours(np.pad(a.astype(float),1),mx*.5):
  # Source sample center is x+.5, so the padded contour offset is -.5.
  c=approximate_polygon(c,tolerance=.40)
  if len(c)<4:continue
  paths.append([[round(float(x)-.5,4),round(float(y)-.5,4)] for y,x in c])
 high=np.zeros((src.height*scale*3,src.width*scale*3),np.uint8)
 contours=[np.rint(np.array(p)*scale*3).astype(np.int32) for p in paths]
 if contours:cv2.fillPoly(high,contours,mx,lineType=cv2.LINE_8)
 core=Image.fromarray(high).resize((src.width*scale,src.height*scale),Image.Resampling.LANCZOS)
 return core,paths

def trace(src):
 a=np.asarray(src);alpha,paths=trace_alpha(src)
 valid=a[:,:,3]>max(1,int(a[:,:,3].max())//2)
 colors=a[:,:,:3][valid]
 # Geometry sources here are white/black artwork. Keep original colored
 # edge and shadow values rather than replacing them with invented colors.
 rgb=src.convert('RGB').resize(alpha.size,Image.Resampling.LANCZOS)
 if len(colors) and np.max(np.ptp(colors.astype(int),axis=0))<4:
  rgb=Image.new('RGB',alpha.size,tuple(np.median(colors,axis=0).astype(int)))
 rgb=rgb.convert('RGBA');rgb.putalpha(alpha)
 return rgb,paths

from icon_geometry import rebuild as palette_trace
from local_icon_sr import render as local_lineart

def common_atlas(src,folder):
 """Rebuild each actual icon independently; avoid cross-cell palette bleed."""
 out=Image.new('RGBA',(src.width*S,src.height*S));cells=[]
 for y in range(0,240,16):
  row=[[x,y,x+16,y+16]for x in range(0,64,16)]
  if y==128:row=[[0,y,16,y+16],[16,y,40,y+16],[40,y,64,y+16]]
  cells.extend(row)
 for j,box in enumerate(cells):
  if not src.crop(box).getchannel('A').getbbox():
   out.paste(src.crop(box).resize(((box[2]-box[0])*S,(box[3]-box[1])*S),Image.Resampling.NEAREST),(box[0]*S,box[1]*S));continue
  if j in {4,12,13,14,15,16,17,18,26,31,32,33,34,44,45,46,47,48,49,56}:
   p=folder/f'cell-{j}';p.mkdir(exist_ok=True);im=palette_trace(src.crop(box),p);out.paste(im,(box[0]*S,box[1]*S))
  elif j>=4:
   p=folder/f'cell-{j}';p.mkdir(exist_ok=True);im=local_lineart(src.crop(box),p);out.paste(im,(box[0]*S,box[1]*S))
 # Original PSP face-button geometry, drawn at 24 samples/native pixel.
 # Constant-width lines replace the source antialias stair steps.
 z=S*3
 for i in range(4):
  im=Image.new('RGBA',(16*z,16*z));d=ImageDraw.Draw(im)
  def box(v):return tuple(round(n*z)for n in v)
  d.ellipse(box([.6,.6,15.4,15.4]),fill=(77,77,78,180))
  d.ellipse(box([1.25,1.25,14.75,14.75]),fill=(0,0,0,255))
  if i==0:d.ellipse(box([3.5,3.5,12.5,12.5]),outline='white',width=round(1.05*z))
  if i==1:
   for xy in [[4.2,4.2,11.8,11.8],[4.2,11.8,11.8,4.2]]:d.line(box(xy),fill='white',width=round(.95*z))
  if i==2:d.line([tuple(box(p))for p in [(8,3.7),(12.4,11.6),(3.6,11.6),(8,3.7)]],fill='white',width=round(1.05*z),joint='curve')
  if i==3:d.rectangle(box([4.1,4.1,11.9,11.9]),outline='white',width=z)
  out.paste(im.resize((16*S,16*S),Image.Resampling.LANCZOS),(i*16*S,0))
 # Source-defined small colored symbols. Keep their flat source colors and
 # geometry: the SR draft introduced speckles inside the tiny colored faces.
 for j in [39,40,41,50,51,52,54]:
  xy=cells[j];sample=np.array(src.crop(xy));colors=sample[:,:,:3][(sample[:,:,3]>0)&(np.ptp(sample[:,:,:3].astype(int),axis=2)>20)]
  cs,counts=np.unique(colors,axis=0,return_counts=True);col=tuple(int(v)for v in cs[np.argmax(counts)])
  im=Image.new('RGBA',(16*z,16*z));d=ImageDraw.Draw(im)
  def pt(p):return tuple(round(v*z)for v in p)
  def poly(p,fill):d.polygon([pt(a)for a in p],fill=fill)
  if j<50:
   poly([(8,.7),(15.3,8),(8,15.3),(.7,8)],'black')
   if j==39:
    for b in [(8,3,9,4),(6,5,8,7),(9,6,12,9),(7,10,10,13)]:d.ellipse(pt(b),fill=col)
   elif j==40:poly([(8.5,7),(9.7,11),(12.8,10),(8.5,14.7),(4,10),(7.2,11)],col)
   else:
    for p in [[(5,6),(8,8.5),(5,11)],[(9,7),(11,8.5),(9,10)],[(12,8),(13.2,8.5),(12,9)]]:poly(p,col)
  else:
   d.ellipse(pt((.9,.9,15.1,15.1)),fill='black')
   if j in [50,51,54]:
    d.ellipse(pt((2,2,14,14)),fill='white')
   if j==50:
    d.rectangle(pt((1,4.2,15,11.8)),fill='black')
    for x in [4,8]:d.line([pt(p)for p in [(x,4.5),(x+3.5,8),(x,11.5)]],fill=col,width=round(1.5*z),joint='curve')
   elif j==51:
    for b in [(3.8,6,12.2,10),(6,3.2,10,12.8)]:d.rectangle(pt(b),fill='black')
    for b in [(4.8,7.4,11.2,8.6),(7.4,4.2,8.6,11.8)]:d.rectangle(pt(b),fill=col)
   elif j==52:
    d.arc(pt((2.2,2.2,13.8,13.8)),90,270,fill='white',width=round(1.25*z));poly([(8,4),(11.8,6),(11.8,10),(8,12)],col)
   elif j==54:
    poly([(8,1.8),(14.2,8),(8,14.2),(1.8,8)],'black')
    d.line([pt((3,8)),pt((13,8))],fill=col,width=z);d.line([pt((8,3)),pt((8,13))],fill=col,width=z)
   round_mask=Image.new('L',im.size);ImageDraw.Draw(round_mask).ellipse(pt((.9,.9,15.1,15.1)),fill=255);im.putalpha(round_mask)
  out.paste(im.resize((16*S,16*S),Image.Resampling.LANCZOS),(xy[0]*S,xy[1]*S))
 return out

def neural(src,model,cache):
 rgba=np.array(src);a=rgba[:,:,3];rgb=rgba[:,:,:3].copy()
 if (a>0).any():
  inds=distance_transform_edt(a==0,return_distances=False,return_indices=True)
  rgb[a==0]=rgb[inds[0][a==0],inds[1][a==0]]
 inp=Image.fromarray(rgb);inp.save(cache/'rgb-input.png')
 native=sr.infer_rgb(model,inp);native.save(cache/'native4x-rgb.png')
 size=(src.width*S,src.height*S)
 # Recover source low-frequency color; high-frequency model detail is bounded
 # by the original design. Never ask a model to invent the silhouette.
 nr=np.asarray(native,dtype=np.float32)
 error=rgb.astype(np.float32)-cv2.resize(nr,(src.width,src.height),interpolation=cv2.INTER_AREA)
 nr=np.clip(nr+.75*cv2.resize(error,native.size,interpolation=cv2.INTER_CUBIC),0,255)
 out=Image.fromarray(np.rint(nr).astype('uint8')).resize(size,Image.Resampling.LANCZOS).convert('RGBA')
 al=np.array(src.getchannel('A').resize(size,Image.Resampling.LANCZOS))
 support=np.array(src.getchannel('A').resize(size,Image.Resampling.BILINEAR))>0
 al[~support]=0
 # Clamp palette range, retain original maximum opacity.
 al=np.minimum(al,int(a.max())).astype(np.uint8);out.putalpha(Image.fromarray(al))
 return out

def protections(t,inventory):
 boxes=[]
 for q in read(R/'qa/ui_build_v4.json')['records']:
  if q['id'] not in t.get('prior_ui_ids',[]):continue
  proof=q.get('proof',{})
  for x in proof.get('clear_regions',[]):boxes.append(x['box'])
  for x in proof.get('labels',[]):
   if 'box'in x:boxes.append(x['box'])
   boxes.extend(p['box'] for p in x.get('pieces',[]))
 for file in ['ui-resident-ko-001','ui-title-ko-002','ui-remaining-ko-001']:
  for q in read(R/f'workspace/{file}/manifest.json')['records']:
   if q.get('asset',q.get('asset_id'))!=t['id']:continue
   for x in q.get('erase_regions',[]):boxes.append(x['box'])
   for x in q.get('erasures',[]):boxes.append(x['box'])
   for x in q.get('labels',[]):
    if 'box'in x:boxes.append(x['box'])
    boxes.extend(x.get('extra',[]));boxes.extend([p[0] for p in x.get('composite',[])])
 return boxes

def main():
 load_binding();O.mkdir(exist_ok=True);V.mkdir(exist_ok=True)
 inv=read(R/'qa/ui_inventory_expanded.json');ts={t['id']:t for t in inv['textures']}
 links=read(R/'qa/ui_expanded_links.json')['assets'];cfg=configparser.ConfigParser(interpolation=None);cfg.optionxform=str;cfg.read(BASE/'textures.ini',encoding='utf-8-sig');basebind=dict(cfg['hashes'])
 prior=R/'workspace/ui-remaining-ko-001/ui-overlay'
 shutil.copytree(prior,O/'ui-overlay',dirs_exist_ok=True)
 binds=read(prior/'manifest.json')['bindings'].copy();records=[];blocked=[];model=None
 for spec in SPECS:
  t=ts[spec['asset']];sid=spec['id'];ad=O/'assets'/sid;ad.mkdir(parents=True,exist_ok=True)
  variants=[]
  try:source,binding=binding_source(t,links)
  except Exception as e:
   observed=links.get(t['id'],[])
   if not observed:
    blocked.append(dict(id=sid,asset=t['id'],error=repr(e)));print('BLOCK',sid,repr(e),flush=True);continue
   # Captured full RGBA is authoritative when allocation-tail bytes differ
   # from contiguous archive bytes. Only exact observed keys are retained.
   logical=Image.open(t['png']).convert('RGBA')
   captures=[Image.open(m['paths'][0]).convert('RGBA')for m in observed]
   assert all(im.crop((0,0,logical.width,logical.height)).tobytes()==logical.tobytes()for im in captures)
   source=captures[0];primary=[m for m,im in zip(observed,captures)if im.tobytes()==source.tobytes() and im.size==source.size]
   variants=[dict(key=m['key'],path=m['paths'][0])for m,im in zip(observed,captures)if im.tobytes()!=source.tobytes() or im.size!=source.size]
   binding=dict(keys={m['key']:source.height for m in primary},observed=[m['key']for m in primary],source_sha256=h(Path(t['source'])),padding='Actual observed allocation RGBA; logical source equality checked. Distinct padding preserved in separate variants.',calculated_key_rejected=repr(e),captured=[dict(path=m['paths'][0],sha256=h(Path(m['paths'][0])))for m in primary])
  native=Image.open(t['png']).convert('RGBA');assert source.crop((0,0,native.width,native.height)).tobytes()==native.tobytes()
  expected=source.resize((source.width*S,source.height*S),Image.Resampling.NEAREST)
  existing=[BASE/basebind[k] for k in binding['keys'] if k in basebind]
  before=Image.open(existing[0]).convert('RGBA') if existing else expected.copy()
  assert before.size==expected.size
  if existing:assert len({h(p)for p in existing})==1
  source.save(ad/'source.png');before.save(ad/'before.png')
  boxes=spec['boxes'] or [[0,0,native.width,native.height]]
  mask=Image.new('L',before.size);dr=ImageDraw.Draw(mask)
  for b in boxes:
   x,y,x1,y1=sb(b);dr.rectangle((x,y,x1-1,y1-1),fill=255)
  # Existing localization remains byte-identical, including cleared source
  # spaces. Protect both declared slots and every changed baseline pixel.
  protected=protections(t,inv)
  for b in protected:
   x,y,x1,y1=sb(b);dr.rectangle((x,y,x1-1,y1-1),fill=0)
  ma=np.array(mask);ba=np.array(before);ea=np.array(expected);ma[np.any(ba!=ea,axis=2)]=0
  mask=Image.fromarray(ma);mask.save(ad/'mask.png')
  layer=Image.new('RGBA',before.size);svg=[]
  processing_boxes=[b.copy()for b in boxes]
  again=True
  while again:
   again=False
   for j,a in enumerate(processing_boxes):
    for k,b in enumerate(processing_boxes[j+1:],j+1):
     if max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3]):
      processing_boxes[j]=[min(a[0],b[0]),min(a[1],b[1]),max(a[2],b[2]),max(a[3],b[3])];del processing_boxes[k];again=True;break
    if again:break
  for i,box in enumerate(processing_boxes):
   part=source.crop(box);partdir=ad/f'part-{i}';partdir.mkdir(exist_ok=True)
   inp=dh(part.tobytes());meta=partdir/'cache.json'
   version=(18 if sid in {'ICO-048','ICO-055'} else 17 if sid in {'ICO-001','ICO-041','ICO-054','ICO-060'} else 16 if sid in {'ICO-037','ICO-046','ICO-056','ICO-059'} else 15) if spec['method']=='palette_trace' else 3
   if meta.exists() and read(meta)==dict(input=inp,method=spec['method'],version=version):
    result=Image.open(partdir/'result.png').convert('RGBA')
   elif spec['method']=='palette_trace':
    if spec.get('cells'):result=common_atlas(part,partdir)
    elif sid=='ICO-048':
     z=S*3;high=Image.new('RGBA',(part.width*z,part.height*z));d=ImageDraw.Draw(high)
     for offset,color in [(1,(36,26,23,232)),(0,(251,251,251,252))]:
      d.rectangle(tuple(round((v+offset)*z)for v in (.5,1.5,9.5,10.5)),outline=color,width=z)
      for xy in [(1.3,2.3,8.7,9.7),(1.3,9.7,8.7,2.3)]:d.line(tuple(round((v+offset)*z)for v in xy),fill=color,width=z)
     result=high.resize((part.width*S,part.height*S),Image.Resampling.LANCZOS)
    elif sid=='ICO-041':
     high=Image.new('RGBA',(part.width*S*3,part.height*S*3));d=ImageDraw.Draw(high);ar=np.array(part);color=tuple(int(v)for v in ar[np.unravel_index(ar[:,:,3].argmax(),ar[:,:,3].shape)])
     for start in [15,105,195,285]:d.arc(tuple(round(v*S*3)for v in (11.2,11.2,20.8,20.8)),start,start+60,fill=color,width=round(1.5*S*3))
     result=high.resize((part.width*S,part.height*S),Image.Resampling.LANCZOS)
    elif sid=='ICO-059':result=part.resize((part.width*S,part.height*S),Image.Resampling.LANCZOS)
    elif sid in {'ICO-036','ICO-037','ICO-043','ICO-055','ICO-058','ICO-061'} or (sid in {'ICO-028','ICO-056'} and i==0):result=palette_trace(part,partdir)
    else:
     result=local_lineart(part,partdir)
     if sid=='ICO-046':
      geometry=palette_trace(part,partdir);result.paste(geometry.crop((0,0,part.width*S,24*S)),(0,0))
     if sid=='ICO-060' and i==0:
      frame=part.crop((0,0,28,30));p=partdir/'frame-original';p.mkdir(exist_ok=True)
      result.paste(palette_trace(frame,p),(0,0))
     if sid=='ICO-060' and i==3:
      p=partdir/'frame-original';p.mkdir(exist_ok=True);result=palette_trace(part,p)
   elif spec['method']=='trace':
    result,paths=trace(part)
    svgtext='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s"><path fill="white" fill-rule="evenodd" d="%s"/></svg>'%(part.width,part.height,' '.join('M '+' L '.join(f'{x},{y}'for x,y in p)+' Z'for p in paths))
    (partdir/'source-contours.svg').write_text(svgtext,'utf8')
   else:
    if model is None:
     mi=next(x for x in read(R/'workspace/local-sr/models/models.json')['records']if x['name']=='RealESRGAN_x4plus.pth')
     model=sr.load_model(Path(mi['path']),mi['sha256'])
     write(O/'local-model.json',dict(model=mi['name'],model_path=mi['path'],model_sha256=mi['sha256'],inference='Local PyTorch CUDA RGB, float32',native_neural_scale=4,final_canvas_scale=8,post_scale='Lanczos 2x',alpha='Original alpha, Lanczos 8x; no neural silhouette',source_color_correction=.75,image_upload=False,external_image_generation=False))
    result=neural(part,model,partdir)
   result.save(partdir/'result.png');write(meta,dict(input=inp,method=spec['method'],version=version))
   layer.paste(result,(box[0]*S,box[1]*S))
  out=Image.composite(layer,before,mask);dest=PACK/'icons-001'/f'{sid}.png';dest.parent.mkdir(parents=True,exist_ok=True);out.save(dest);out.save(ad/'candidate.png')
  changes=int(np.any(np.array(out)!=ba,axis=2).sum())
  for k in binding['keys']:binds[k]=f'icons-001/{sid}.png'
  for variant in variants:
   vi=Image.open(variant['path']).convert('RGBA');vi=vi.resize((vi.width*S,vi.height*S),Image.Resampling.NEAREST)
   if variant['key']in basebind:vi=Image.open(BASE/basebind[variant['key']]).convert('RGBA')
   logical_box=(0,0,native.width*S,native.height*S)
   assert vi.crop(logical_box).tobytes()==before.crop(logical_box).tobytes(),'Variant has a distinct localized baseline; requires its own protection mask'
   variant_mask=Image.new('L',vi.size);variant_mask.paste(mask.crop((0,0,native.width*S,native.height*S)),(0,0))
   variant_layer=Image.new('RGBA',vi.size);variant_layer.paste(layer.crop((0,0,native.width*S,native.height*S)),(0,0))
   vi=Image.composite(variant_layer,vi,variant_mask)
   variant['replacement']=f"icons-001/{sid}-{variant['key']}.png";vi.save(PACK/variant['replacement']);variant['sha256']=h(PACK/variant['replacement']);binds[variant['key']]=variant['replacement']
  aliases=[x['id']for x in inv['textures']if x.get('rgba_sha256')==t.get('rgba_sha256')]
  rec=dict(**spec,source_sha256=h(Path(t['source'])),binding=binding,aliases=aliases,logical_size=list(native.size),padded_size=list(source.size),output_size=list(out.size),protected_boxes=protected,baseline=str(existing[0])if existing else 'original nearest x8 for comparison',files={n:dict(path=str(ad/f'{n}.png'),sha256=h(ad/f'{n}.png'))for n in ['source','before','mask','candidate']},replacement=f'icons-001/{sid}.png',sha256=h(dest),changed_pixels=changes,visual_review='pending',runtime_verified=False)
  rec['allocation_variants']=variants
  rec['processing_boxes']=processing_boxes
  rec['actual_method']='local binary-mask SR plus original-geometry corrections' if spec['method']=='palette_trace' else 'local photo SR with original alpha and color correction'
  if sid=='ICO-059':rec['actual_method']='Original soft-light gradient resampled with Lanczos; no neural inference or new geometry'
  if sid in {'ICO-036','ICO-037','ICO-041','ICO-043','ICO-048','ICO-055','ICO-058','ICO-061'}:rec['actual_method']='Source coordinate geometry/palette reconstruction; no neural inference in final pixels'
  rec['processing_boxes_disjoint']=all(max(a[0],b[0])>=min(a[2],b[2]) or max(a[1],b[1])>=min(a[3],b[3]) for j,a in enumerate(processing_boxes)for b in processing_boxes[j+1:])
  records.append(rec);write(O/'manifest.json',dict(records=records,blocked=blocked,runtime_verified=False));print('BUILT',sid,spec['name'],changes,flush=True)
 write(O/'manifest.json',dict(schema='brs-icons-001/v1',records=records,blocked=blocked,build_script_sha256=h(Path(__file__)),spec_sha256=h(R/'tools/icon_specs_001.py'),helper_sha256={n:h(R/'tools'/n)for n in ['icon_geometry.py','local_icon_sr.py','local_sr.py']},lineart_model=sr.provenance(),original_canvas_scale=S,translator_model='Codex internal',translation_note='No new semantic translation; previous Korean pixels preserved exactly',required_companion_iso=read(R/'workspace/ui-remaining-ko-001/manifest.json')['required_companion_iso'],runtime_verified=False,live_installation_performed=False))
 used=set(binds.values());files={p:dict(sha256=h(PACK/p),bytes=(PACK/p).stat().st_size)for p in sorted(used)}
 (PACK/'textures-fragment.ini').write_text('[hashes]\n'+'\n'.join(f'{k} = {v}'for k,v in sorted(binds.items()))+'\n','utf8')
 write(O/'ui-overlay/manifest.json',dict(bindings=binds,unique_pngs=len(used),files=files,required_title_iso=str(R/'workspace/ui-title-ko-002/BRS_UI_title_v2.iso'),installation_performed=False,instruction='Merge only exact hashes into the latest combined pack; never replace its full textures.ini.'))
 print('DONE',len(records),'blocked',len(blocked),'bindings',len(binds))
if __name__=='__main__':main()
