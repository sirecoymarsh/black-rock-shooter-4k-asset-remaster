"""Rerender only ISO-identified Korean cells in observed xxh64 glyph caches."""
import sys,json,collections,hashlib,shutil,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1]; P=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
from brs_font_pipeline import parse_font_layout,cell_bytes,decoded_cell_image,render_cell
S=8
src=R/'workspace/source/font';out=R/'workspace/build-v2/PSP/TEXTURES/NPUH10126';(out/'font').mkdir(parents=True,exist_ok=True)
source_caches=src/'caches';source_caches.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def savej(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
l,p=parse_font_layout((src/'font.lpk').read_bytes());mapping=json.loads((src/'glyph_alias_map.json').read_text(encoding='utf-8'));byindex={v['font_index']:v for v in mapping['aliases']}
font_path=Path(mapping['font']['path']);f14=ImageFont.truetype(str(font_path),14);f112=ImageFont.truetype(str(font_path),112)
f112.set_variation_by_axes([325])
lookup=collections.defaultdict(list);glyphs={};glyph_records=[]
for i in range(l.glyph_count):
 im=decoded_cell_image(cell_bytes(p,l,i),l.palette_rgba)
 if im.getchannel('A').getbbox():lookup[im.tobytes()].append(i)
 if i not in byindex:continue
 row=byindex[i];char=row['character']
 assert sha(cell_bytes(p,l,i))==row['patched_cell_sha256']
 assert render_cell(char,f14,[v[3] for v in l.palette_rgba])==cell_bytes(p,l,i),char
 a=Image.new('L',(15*S,15*S));ImageDraw.Draw(a).text((S,-S),char,font=f112,fill=255)
 # Render separately with a guard band to detect any clipping.
 guard=Image.new('L',(19*S,19*S));ImageDraw.Draw(guard).text((3*S,S),char,font=f112,fill=255)
 assert a.tobytes()==guard.crop((2*S,2*S,17*S,17*S)).tobytes()
 outside=np.array(guard);outside[2*S:17*S,2*S:17*S]=0;assert not outside.any(),char
 assert a.getbbox(),char
 hi=Image.new('RGBA',a.size,'white');hi.putalpha(a);glyphs[i]=hi
 glyph_records.append({'font_index':i,'character':char,'source_cell_sha256':row['patched_cell_sha256'],'hd_rgba_sha256':sha(hi.tobytes()),'bbox':a.getbbox()})
# The complete authored repertoire is a source atlas; the game consumes exact cache reconstructions below.
atlas=Image.new('RGBA',(32*16*S,math.ceil(len(glyphs)/32)*16*S),(255,255,255,0))
for n,(i,im) in enumerate(glyphs.items()):atlas.paste(im,(n%32*16*S,n//32*16*S))
atlas.save(R/'outputs/korean_919_glyphs_8x.png')
files={};provenance={}
for sess in sorted((P/'workspace/sessions').iterdir()):
 if not (sess/'session.json').is_file():continue
 meta=json.loads((sess/'session.json').read_text(encoding='utf-8-sig'))
 if meta.get('iso_sha256')!='525b5d2b7d8f4723be25b026e72b69d07d30c2cf84d8a48235577ca3728fc92a':continue
 for f in (sess/'memstick/PSP/TEXTURES/NPUH10126/new').glob('*851096b*.png'):
  if len(f.stem)!=24 or not f.stem.startswith('00000000'):continue
  if f.name in files:assert files[f.name].read_bytes()==f.read_bytes(),f.name
  files[f.name]=f;provenance.setdefault(f.name,[]).append(sess.name)
# Include newly collected independent sessions when present.
for f in (R/'workspace/sessions').glob('*/memstick/PSP/TEXTURES/NPUH10126/new/*851096b*.png'):
 if len(f.stem)==24 and f.stem.startswith('00000000'):files[f.name]=f;provenance.setdefault(f.name,[]).append(f.parents[5].name)
records=[];rejected=[];all_used=set()
for name,f in sorted(files.items()):
 im=Image.open(f).convert('RGBA')
 if im.size not in [(128,128),(256,128)]:rejected.append({'file':name,'reason':'unexpected size'});continue
 native=np.array(im);high=im.resize((im.width*S,im.height*S),Image.Resampling.NEAREST);protect=np.ones((im.height,im.width),bool);cells=[];unmatched=[]
 for y in range(0,im.height,16):
  for x in range(0,im.width,16):
   cell=im.crop((x,y,x+15,y+15));hits=lookup.get(cell.tobytes(),[])
   if not hits:
    if cell.getchannel('A').getbbox():unmatched.append([x,y])
    continue
   ids=[i for i in hits if i in glyphs]
   if not ids:continue
   assert len(ids)==1,(name,x,y,ids)
   i=ids[0];high.paste(glyphs[i],(x*S,y*S));protect[y:y+15,x:x+15]=False;all_used.add(i)
   cells.append({'x':x,'y':y,'font_index':i,'character':byindex[i]['character']})
 if unmatched:rejected.append({'file':name,'reason':'nonblank cell not identical to ISO font','cells':unmatched});continue
 if not cells:continue
 got=np.array(high);expect=np.repeat(np.repeat(native,S,axis=0),S,axis=1);mask=np.repeat(np.repeat(protect,S,axis=0),S,axis=1)
 assert np.array_equal(got[mask],expect[mask]),name
 # Each cell has a protected one-pixel right/bottom gutter, and no new ink can leak into it.
 dest=out/'font'/name;high.save(dest,optimize=True);shutil.copyfile(f,source_caches/name)
 records.append({'id':'FONT-CACHE-'+f.stem[8:],'key':f.stem,'source':str(source_caches/name),'observed_sources':provenance[name],'source_size':im.size,'output_size':high.size,'scale':S,'source_rgba_sha256':sha(im.tobytes()),'output_sha256':sha(dest.read_bytes()),'output_rgba_sha256':sha(high.tobytes()),'replacement':'font/'+name,'korean_cells':cells,'protected_pixels_pass':True,'gutter_pass':True,'runtime_verified':False})
lines=['# Korean glyph caches: ISO-verified, exact observed xxh64 content hashes.','[options]','version = 1','hash = xxh64','ignoreAddress = true','reduceHash = false','','[hashes]']+[r['key']+' = '+r['replacement'] for r in records]
(out/'textures.ini').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# Comparison uses a real decoded cache, not a newly composed sentence.
r=max(records,key=lambda r:len(r['korean_cells']));old=Image.open(r['source']).convert('RGBA');new=Image.open(out/r['replacement']).convert('RGBA');crop=(0,0,min(128,old.width),48)
old=old.crop(crop).resize((1024,384),Image.Resampling.NEAREST);new=new.crop((0,0,1024,384));sheet=Image.new('RGB',(2080,450),'#162032');d=ImageDraw.Draw(sheet);label=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',24)
d.text((16,12),'원본 글리프 8배 표시',font=label,fill='white');d.text((1056,12),'같은 글리프 · 벡터에서 8배 재렌더링',font=label,fill='white');sheet.paste(old,(16,58),old);sheet.paste(new,(1056,58),new);sheet.save(R/'outputs/font_before_after.png')
manifest={'schema':'brs-hd-fonts/v2','translator_model':'Codex internal','translation_change':'none; exact existing glyph identity reused','font_path':str(font_path),'font_sha256':sha(font_path.read_bytes()),'font_name':f112.getname(),'optical_weight':325,'native_source_weight':100,'native_integrated_alpha_ratio':1.0002701393686144,'method':'Noto Sans KR original font rerasterization at 112px into 120px cells; original glyph origins multiplied by 8','source_14px_rerender_exact_count':len(glyphs),'repertoire':glyph_records,'observed_cache_count':len(files),'built_cache_count':len(records),'observed_korean_repertoire_count':len(all_used),'rejected':rejected,'runtime_status':'unverified','coverage_limit':'Only enumerated exact dynamic cache contents. Unseen cache arrangements fall back to native font; 919 glyph source repertoire is not full runtime coverage.','records':records}
savej(R/'qa/font_build.json',manifest)
print(json.dumps({k:manifest[k] for k in ['source_14px_rerender_exact_count','observed_cache_count','built_cache_count','observed_korean_repertoire_count']},ensure_ascii=False));print('rejected',len(rejected),rejected[:2])