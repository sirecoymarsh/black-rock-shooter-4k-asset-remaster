"""Compare fixed ISO source byte hashes against observed PPSSPP xxh64 keys.

Read-only hypothesis probe. Generated keys are not installed as replacements.
PPSSPP 1.20.4 TextureReplacer.cpp ComputeHash truncates XXH64 seed BACD7814
to u32. At height 512, maxSeenV may restrict the native byte range.
"""
import sys,json,gzip,hashlib
from pathlib import Path
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[1]
A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(A/'patch_pipeline'))
sys.path.insert(0,r'P:\AI\Codex\projects\black-rock-shooter-hd-retexture\workspace\tooldeps\imageqa')
from brs_patch import Iso9660,Rtdp,Lpk
import xxhash
from PIL import Image
import numpy as np
from ptmd_codec import decode_ptmd,unswizzle_psp,_decode_indexes
audit=json.loads((R/'qa/ui_source_audit.json').read_text(encoding='utf-8'))
rows=[];cache={}
with Iso9660(A/'release_build/runtime_fix_iso_20260823_test_v2/BRS_Korean_v1.0.iso',writable=False) as iso:
 def get(k):
  e=iso.by_path[k.lower()];return iso._read_at(e.extent*2048,e.size)
 vol=Rtdp(get('PSP_GAME/USRDIR/GAMEDATA/SYSTEM.VOL'))
 for a in audit['assets']:
  domain,name,file=a['relative'].split('/');key=domain+'/'+name
  if key not in cache:
   if domain=='MENU':raw=gzip.decompress(get('PSP_GAME/USRDIR/GAMEDATA/IF/MENU/'+name+'.GZ'))
   else:
    it=next(it for it in vol.items if it.name.lower()==name.lower()+'.lpk')
    raw=bytes(v^0x55 for v in vol.payload(it))
   cache[key]=(raw,Lpk(raw))
  raw,lpk=cache[key];it=lpk.items[int(file[:3])];ptmd=lpk.payload(it)
  assert hashlib.sha256(ptmd).hexdigest()==a['iso_ptmd_sha256']
  stride=a['width']*(4 if a['mode']==4 else 8)//8
  data=raw[it.offset+16:];heights=[a['padded_height']]
  if a['padded_height']==512:heights=list(range(1,513))
  hashes={h:f'{xxhash.xxh64(data[:h*stride],seed=0xBACD7814).intdigest()&0xffffffff:08x}' for h in heights if h*stride<=len(data)}
  observed=[m['key'][-8:] for m in a['matches']]
  tex=decode_ptmd(ptmd);dimension=(a['padded_width'].bit_length()-1)|((a['padded_height'].bit_length()-1)<<8)
  clutfmt=0xc500ff00|(2 if tex.palette_code==0x20 else 3)
  low=f'{xxhash.xxh32(ptmd[tex.palette_offset:],seed=0xc0108888).intdigest()^clutfmt^dimension:08x}'
  assert low==a['cache_low'],(a['id'],'unexpected palette cache key')
  padded=None;padding_checks=[]
  if a['padded_height']*stride<=len(data):
   linear=unswizzle_psp(data[:a['padded_height']*stride],stride,a['padded_height'])
   indices=_decode_indexes(linear,tex.mode,tex.width*a['padded_height'])
   rgba=np.array(tex.palette_rgba,dtype=np.uint8)[np.frombuffer(indices,dtype=np.uint8)].reshape(a['padded_height'],tex.width,4)
   padded=Image.fromarray(rgba)
   assert padded.crop((0,0,tex.width,tex.height)).tobytes()==tex.rgba_bytes
   for m in a['matches']:
    observed_im=Image.open(m['path']).convert('RGBA')
    equal=observed_im.tobytes()==padded.tobytes()
    assert equal,(a['id'],m['key'],'source padding differs from observed')
    padding_checks.append({'key':m['key'],'full_rgba_equal':equal})
  if a['id']=='UI-22':
   assert padded is not None
   dest=R/'workspace/ui22-static-review';dest.mkdir(parents=True,exist_ok=True)
   padded.save(dest/'original-full.png')
   replacement=padded.resize((tex.width*8,a['padded_height']*8),Image.Resampling.NEAREST)
   candidate=Image.open(R/'workspace/ui_candidates_v3/UI-22_8x.png').convert('RGBA')
   replacement.paste(candidate.crop((0,0,tex.width*8,tex.height*8)),(0,0))
   replacement.save(dest/'ui22.png')
   binding='00000000'+low+hashes[a['padded_height']]
   (dest/'textures.ini').write_text('# QA hypothesis: full-height static-source key; runtime acceptance pending.\n[options]\nversion = 1\nhash = xxh64\nignoreAddress = true\nreduceHash = false\n\n[hashes]\n'+binding+' = ui22.png\n',encoding='utf-8')
   (dest/'README.txt').write_text('Internal QA candidate only. Not installed. Exact full-height key derived from the fixed ISO; UI-22 runtime consumption remains unobserved. Padding is decoded from contiguous LPK bytes, not invented transparent pixels. No claim about reduced maxSeenV hash variants.\n',encoding='utf-8')
  rows.append({'id':a['id'],'archive':key,'cache_low':low,'observed':observed,'source_contiguous_matches':{k:[h for h,v in hashes.items() if v==k] for k in observed},'full_height_hash':hashes.get(a['padded_height']),'full_height_in_archive':a['padded_height']*stride<=len(data),'full_rgba_checks':padding_checks,'source_logical_sha256':hashlib.sha256(data[:a['height']*stride]).hexdigest(),'possible_height_hashes':hashes if a['id']=='UI-22' else None})
matched=[r for r in rows if r['observed'] and all(r['source_contiguous_matches'].values())]
report={'algorithm_sources':['https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/GPU/Common/TextureReplacer.cpp','https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/GPU/Common/TextureCacheCommon.h','https://raw.githubusercontent.com/hrydgard/ppsspp/v1.20.4/GPU/Vulkan/TextureCacheVulkan.cpp'],'status':'Source derivation validated against observations; UI22 remains an uninstalled QA hypothesis','iso_sha256':audit['iso_sha256'],'matched_asset_count':len(matched),'matched_unique_key_count':len({r['cache_low']+v for r in matched for v in r['observed']}),'rows':rows}
(R/'qa/ui_raw_hash_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'matched_assets':report['matched_asset_count'],'matched_unique_keys':report['matched_unique_key_count'],'full_rgba_checks':sum(len(r['full_rgba_checks']) for r in rows),'ui22_static_key':'00000000'+rows[22]['cache_low']+rows[22]['full_height_hash'],'ui22_runtime_verified':False}))
