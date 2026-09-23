"""Original-design font candidate; consume only the frozen exact-cache manifest."""
import sys,json,hashlib,math,shutil
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import font_heritage as style
from brs_font_pipeline import parse_font_layout,cell_bytes,decoded_cell_image
R=Path(__file__).resolve().parents[1];S=8
src=R/'workspace/source/font';prior=json.loads((R/'qa/font_build.json').read_text('utf8'))
mapping=json.loads((src/'glyph_alias_map.json').read_text('utf8'));aliases={a['font_index']:a for a in mapping['aliases']}
layout,payload=parse_font_layout((src/'font.lpk').read_bytes());out=R/'workspace/build-v4/PSP/TEXTURES/NPUH10126';(out/'font').mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
glyphs={};native={};records=[];totals=[0,0]
for i,a in aliases.items():
 cell=cell_bytes(payload,layout,i);assert sha(cell)==a['patched_cell_sha256']
 old=decoded_cell_image(cell,layout.palette_rgba);new=style.body_glyph(a['character']);glyphs[i]=new;native[i]=old
 totals[0]+=int(np.array(old.getchannel('A')).sum())*S*S;totals[1]+=int(np.array(new.getchannel('A')).sum())
 records.append({'font_index':i,'character':a['character'],'source_cell_sha256':sha(cell),'hd_rgba_sha256':sha(new.tobytes()),'bbox':new.getchannel('A').getbbox(),'clipping_pass':True})
atlas=Image.new('RGBA',(32*128,math.ceil(len(glyphs)/32)*128),(255,255,255,0))
for n,new in enumerate(glyphs.values()):atlas.paste(new,(n%32*128,n//32*128))
atlas.save(R/'outputs/korean_919_heritage.png')
cache_records=[];used=set()
for rec in prior['records']:
 im=Image.open(rec['source']).convert('RGBA');assert sha(im.tobytes())==rec['source_rgba_sha256']
 new=im.resize((im.width*S,im.height*S),Image.Resampling.NEAREST);protect=np.ones((im.height,im.width),bool)
 for c in rec['korean_cells']:
  x,y,i=c['x'],c['y'],c['font_index'];assert im.crop((x,y,x+15,y+15)).tobytes()==native[i].tobytes()
  new.paste(glyphs[i],(x*S,y*S));protect[y:y+15,x:x+15]=False;used.add(i)
 expected=np.repeat(np.repeat(np.array(im),S,0),S,1);mask=np.repeat(np.repeat(protect,S,0),S,1)
 assert np.array_equal(np.array(new)[mask],expected[mask])
 dest=out/'font'/f"{rec['key']}.png";new.save(dest,compress_level=6)
 cache_records.append({**rec,'output_sha256':sha(dest.read_bytes()),'output_rgba_sha256':sha(new.tobytes()),'runtime_verified':False})
# Body samples are an offline assembly at the game's fixed 16px cell advance.
chars={a['character']:i for i,a in aliases.items()}
sentences=['임무를 시작합니다.','무기 스킬을 사용합니다.','중요 아이템을 확인합니다.','조준 고정']
# Only known translated glyphs, native punctuation and a measured native space.
sample_chars=set(''.join(sentences))
assert {c for c in sample_chars if '\uac00'<=c<='\ud7a3'}<=chars.keys()
sheet=Image.new('RGB',(2100,850),'#202e42');d=ImageDraw.Draw(sheet);caption=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',26)
d.text((20,15),'대사용 폰트 · 고정 글자 간격 비교 (실제 게임 화면 아님)',font=caption,fill='white')
for row,sentence in enumerate(sentences):
 y=75+row*180;d.text((20,y),'기존',font=caption,fill='white');d.text((1060,y),'원본 디자인 계승 후보',font=caption,fill='white')
 for col in range(2):
  for pos,c in enumerate(sentence):
   if c==' ':continue
   if c not in chars:continue
   cell=native[chars[c]].resize((60,60),Image.Resampling.NEAREST) if col==0 else glyphs[chars[c]].resize((60,60),Image.Resampling.LANCZOS)
   sheet.paste(cell,(20+col*1040+pos*64,y+48),cell)
sheet.save(R/'outputs/font_heritage_body.png')
manifest={'schema':'brs-hd-fonts/v4','translator_model':'Codex internal','translation_change':'none; exact existing glyph identity reused','font_profile':style.PROFILE,'source_manifest_sha256':sha((R/'qa/font_build.json').read_bytes()),'authored_glyph_count':len(records),'built_cache_count':len(cache_records),'observed_korean_repertoire_count':len(used),'native_integrated_alpha_ratio':totals[1]/totals[0],'repertoire':records,'records':cache_records,'runtime_status':'unverified; previous Noto runtime proof does not transfer to Orbit','coverage_limit':'Only the 522 frozen observed cache arrangements; unseen arrangements fall back to native.','source_font_license':str(src/'orbit/OFL.txt'),'sample_limit':'Offline fixed-grid Hangul assembly. Punctuation is excluded from this proof; actual cache builds preserve native punctuation unchanged.'}
(R/'qa/font_build_v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf8')
bindings=json.loads((R/'qa/ui_bindings_v4.json').read_text('utf8'))
for rec in cache_records:
 assert rec['key'] not in bindings;bindings[rec['key']]=rec['replacement']
lines=['# Original-design Korean font/UI candidate. Runtime acceptance pending.','[options]','version = 1','hash = xxh64','ignoreAddress = true','reduceHash = false','','[hashes]']+[k+' = '+v for k,v in sorted(bindings.items())]
(out/'textures.ini').write_text('\n'.join(lines)+'\n','utf8')
(out/'licenses').mkdir(exist_ok=True);shutil.copyfile(src/'orbit/OFL.txt',out/'licenses/Orbit-OFL.txt')
print(json.dumps({k:manifest[k] for k in ['authored_glyph_count','built_cache_count','observed_korean_repertoire_count','native_integrated_alpha_ratio']}))
