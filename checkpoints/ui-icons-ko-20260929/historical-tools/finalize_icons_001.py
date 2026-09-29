"""Validate persisted staging and export only referenced UI overlay files."""
from pathlib import Path
import json,hashlib,shutil,re,configparser
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'workspace/ui-icons-001';V=R/'outputs/ui-icons-001'
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2),'utf8')
m=read(O/'manifest.json');q=read(R/'qa/ui_icons_001_review.json');overlay=read(O/'ui-overlay/manifest.json')
src=O/'ui-overlay/PSP/TEXTURES/NPUH10126';dest=O/'ready-ui-overlay/PSP/TEXTURES/NPUH10126'
base=R/'workspace/ui-remaining-ko-001/pack/PSP/TEXTURES/NPUH10126'
c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(base/'textures.ini',encoding='utf-8-sig')
assert not m['blocked'];assert {x['id']for x in m['records']}=={x['id']for x in q['asset_checks']}
review={x['id']:x for x in q['asset_checks']}
for record in m['records']:
 check=review[record['id']]
 assert check['candidate_sha256']==record['sha256']==sha(Path(record['files']['candidate']['path'])),record['id']
 assert all(check[key] is True for key in ['geometry','protected_rgba','prior_localization_equal']),record['id']
extra=[]
inventory=read(R/'qa/ui_inventory_expanded.json');ts={t['id']:t for t in inventory['textures']}
for r in m['records']:
 assert sha(Path(ts[r['asset']]['source']))==r['source_sha256']
 for v in r.get('allocation_variants',[]):
  source=Image.open(v['path']).convert('RGBA');b=source.resize((source.width*8,source.height*8),Image.Resampling.NEAREST)
  if v['key']in c['hashes']:b=Image.open(base/c['hashes'][v['key']]).convert('RGBA')
  a=Image.open(src/v['replacement']).convert('RGBA');assert a.size==b.size
  mask=Image.open(r['files']['mask']['path']);aligned=Image.new('L',a.size);aligned.paste(mask.crop((0,0,r['logical_size'][0]*8,r['logical_size'][1]*8)),(0,0))
  assert not np.any(np.array(a)!=np.array(b),axis=2)[np.array(aligned)==0].any()
  assert sha(src/v['replacement'])==v['sha256'];extra.append(dict(key=v['key'],padding_and_protected_pixels=True,geometry=True))
 assert r['changed_pixels']>0,r['id']
for key,path in overlay['bindings'].items():
 assert re.fullmatch('[0-9a-f]{24}',key);assert path in overlay['files'];assert '..'not in Path(path).parts
for relative,meta in overlay['files'].items():
 p=src/relative;assert sha(p)==meta['sha256'];assert p.stat().st_size==meta['bytes']
 t=dest/relative;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
 assert sha(t)==meta['sha256']
shutil.copy2(src/'textures-fragment.ini',dest/'textures-fragment.ini');write(O/'ready-ui-overlay/manifest.json',overlay)
assert {str(p.relative_to(dest)).replace('\\','/')for p in dest.rglob('*.png')}==set(overlay['files'])
covered={a for r in m['records']for a in r['aliases']}
coverage=[]
for t in inventory['textures']:
 aid=t['id']
 if aid in covered:status='icon_family_covered'
 elif '::pict::'in aid:status='embedded_tutorial_or_illustration_separate_scope'
 elif '::011::'in aid and 'gallery'in aid:status='gallery_art_strip_not_standalone_ui_icon'
 elif aid.startswith('mc.vol'):status='native_save_system_art_fixed_resolution_not_HD_texture_overlay'
 else:status='other_UI_text_frame_map_background_or_art_not_selected_icon_family'
 coverage.append(dict(asset=aid,status=status))
write(O/'coverage.json',dict(inventory_sha256=sha(R/'qa/ui_inventory_expanded.json'),source_textures=len(inventory['textures']),icon_source_aliases=len(covered),entries=coverage,scope='Standalone icon families in IF/SYSTEM/TITLE UI; screenshots, character artwork and native PSP save-system images are separate surfaces.'))
report=dict(schema='brs-icons-001-acceptance/v1',asset_families=len(m['records']),source_aliases=len(covered),static_primary_checks=q['check_count'],allocation_variant_checks=extra,overlay_keys=len(overlay['bindings']),unique_overlay_pngs=len(overlay['files']),comparison_regions=q['comparison_regions'],comparison_pages=q['comparison_pages'],source_bytes_unchanged=True,overlay_file_allowlist_pass=True,existing_Korean_pixels_equal=True,geometry_8x_pass=True,visual_review='pending',deterministic_rebuild='pending',runtime_verified=False,live_installation_performed=False,manifest_sha256=sha(O/'manifest.json'),required_companion_iso=m['required_companion_iso'])
write(R/'qa/ui_icons_001_acceptance.json',report)
print(json.dumps({k:report[k]for k in ['asset_families','source_aliases','static_primary_checks','overlay_keys','unique_overlay_pngs','comparison_regions']}))
