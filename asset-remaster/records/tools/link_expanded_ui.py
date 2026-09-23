"""Link extracted logical images to observed source dumps, without guessing padding."""
import sys,json,hashlib,collections,struct,io
from pathlib import Path
from PIL import Image
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];P=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture')
inv=json.loads((R/'qa/ui_inventory_expanded.json').read_text('utf8'));iso_sha=inv['iso_sha256']
groups=collections.defaultdict(list)
for t in inv['textures']:
 if 'padded_width' in t and 'rgba_sha256' in t:groups[(t['padded_width'],t['padded_height'])].append(t)
def sha(b):return hashlib.sha256(b).hexdigest()
files=collections.defaultdict(list);excluded=collections.Counter();roots=[]
for base in [R,P]:
 for mf in sorted((base/'workspace/sessions').glob('*/session.json')):
  m=json.loads(mf.read_text('utf-8-sig'))
  if m.get('iso_sha256')!=iso_sha:continue
  d=mf.parent/'memstick/PSP/TEXTURES/NPUH10126/new';roots.append(str(d))
  for f in d.glob('*.png'):
   if len(f.stem)!=24 or not f.stem.startswith('00000000'):excluded['non_base_address_independent_key']+=1;continue
   if f.stem[8:15]=='851096b':excluded['dynamic_font_cache_separate_scope']+=1;continue
   files[f.stem].append(f)
records=[];collisions=[];errors=[];by_asset=collections.defaultdict(list)
for key,paths in sorted(files.items()):
 variants={}
 for p in paths:
  try:
   data=p.read_bytes();digest=sha(data)
   if digest in variants:variants[digest]['paths'].append(str(p));continue
   im=Image.open(io.BytesIO(data)).convert('RGBA');variants[digest]={'paths':[str(p)],'png_sha256':digest,'rgba_sha256':sha(im.tobytes()),'size':im.size,'im':im}
  except (OSError,ValueError) as exc:errors.append({'path':str(p),'error':str(exc)})
 if len({v['rgba_sha256'] for v in variants.values()})>1:collisions.append({'key':key,'variants':[{k:v for k,v in x.items() if k!='im'} for x in variants.values()]})
 for variant in variants.values():
  im=variant.pop('im');crops={};matches=[]
  for t in groups.get(im.size,[]):
   logical=(t['width'],t['height'])
   if logical not in crops:crops[logical]=sha(im.crop((0,0,*logical)).tobytes())
   if crops[logical]!=t['rgba_sha256']:continue
   match={'key':key,**variant,'logical_rgba_sha256':t['rgba_sha256'],'logical_size':logical,'padding_status':'Only the observed full image is authoritative; no transparent padding assumed','consumer_status':'Texture observed, specific scene/state/UV not yet established'}
   by_asset[t['id']].append(match);matches.append(t['id'])
  records.append({'key':key,**variant,'matched_assets':matches})
# Stored GE frame records establish original-texture consumption, not GPU replacement bytes.
ge=json.loads((R/'workspace/ge/battle-results/ui_consumers.json').read_text('utf8'));ge_links=[]
for digest,tx in ge['textures'].items():
 im=Image.open(tx['file']).convert('RGBA')
 for t in groups.get(im.size,[]):
  if sha(im.crop((0,0,t['width'],t['height'])).tobytes())==t['rgba_sha256']:
   draws=[d for d in ge['draws'] if d['texture']==digest];ge_links.append({'asset':t['id'],'ge_texture':digest,'record_sha256':ge['source_sha256'],'draw_count':len(draws),'draws':draws,'scope':ge['scope']})
summary={'extracted_texture_count':len(inv['textures']),'unique_nonfont_keys_scanned':len(files),'matched_assets':len(by_asset),'matched_unique_keys':len({m['key'] for a in by_asset.values() for m in a}),'matched_assets_outside_prior27':sum(not t.get('prior_ui_ids') for t in inv['textures'] if t['id'] in by_asset),'ge_linked_assets':len({x['asset'] for x in ge_links}),'key_pixel_collisions':len(collisions),'read_errors':len(errors)}
report={'schema':'brs-expanded-ui-runtime-links/v1','iso_sha256':iso_sha,'rgba_hash_contract':'SHA256(raw row-major RGBA bytes), dimensions separate. Parent inventory uses SHA256(big-endian width,height + RGBA).','roots':roots,'summary':summary,'excluded':dict(excluded),'assets':dict(by_asset),'observed_records':records,'collisions':collisions,'errors':errors,'battle_results_ge_links':ge_links,'replacement_runtime_verified':False}
(R/'qa/ui_expanded_links.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(summary))
for group in ['if_rsdsys','title.vol','if/pict']:
 print(group,[(t['relative'],len(by_asset[t['id']])) for t in inv['textures'] if group in t['relative'] and t['id'] in by_asset])
