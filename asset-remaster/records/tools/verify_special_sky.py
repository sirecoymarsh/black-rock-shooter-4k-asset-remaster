"""Adopt only the byte-bound linear sky payload with complete observed RGBA proof."""
import sys,json,hashlib,struct,copy,shutil,importlib.util
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];C=Path('C:/Users/CadriacLord/Documents/Codex/2026-09-22/brs-hd-ui-fonts')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads((R/p).read_text('utf8'))
def write(p,o):(R/p).write_text(json.dumps(o,ensure_ascii=False,indent=2),'utf8')
if (R/'qa/ptmd_special_sky_verification.json').exists():raise SystemExit('Already adopted; use a new version for further layout investigation.')
sys.path.insert(0,str(R/'tools'));spec=importlib.util.spec_from_file_location('sky_decoder_candidate',C/'work/ptmd_expanded.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
inv=read('qa/battle_map_inventory.json');cat=read('qa/battle_sr_catalog.json');links=read('qa/battle_map_runtime_links.json');ui=read('qa/ui_inventory_expanded.json');observed=read('qa/ui_expanded_links.json')
assert len(cat['groups'])==283 and inv['summary']['decoded']==410 and len(inv['failures'])==6
assert observed['iso_sha256']==inv['iso_sha256']==cat['iso_sha256']==links['iso_sha256']
prior_groups=copy.deepcopy(cat['groups']);regression=[]
for label,rows in [('battle',inv['textures']),('ui',ui['textures'])]:
 for t in rows:
  if not t.get('png') or Path(t['source']).suffix.lower()!='.ptm':continue
  data=Path(t['source']).read_bytes();assert sha(data)==t.get('decoded_sha256',t['source_sha256']);im,details=decoder.decode(data)
  assert details['roundtrip_exact'] and im.size==(t['width'],t['height']) and sha(im.tobytes())==t['rgba_sha256'],t['id']
  regression.append({'scope':label,'id':t['id'],'source_sha256':sha(data),'rgba_sha256':t['rgba_sha256']})
assert len(regression)==849
rec=next(v for v in observed['observed_records'] if v['key']=='000000009c3edae9ca6a6a87' and v['size']==[256,4]);p=next(Path(p) for p in rec['paths'] if Path(p).is_file());ref=Image.open(p).convert('RGBA');assert sha(ref.tobytes())==rec['rgba_sha256'] and sha(p.read_bytes())==rec['png_sha256']
special=[t for t in inv['textures'] if t.get('status')=='decode failed'];adopted=[];hypotheses=[];unsupported=[]
for t in special:
 b=Path(t['source']).read_bytes();assert sha(b)==t['source_sha256'];w=1<<(b[7]>>4);h=b[6]|((b[7]&15)<<8);mode=b[8];off=struct.unpack_from('<I',b,12)[0];rowbytes=w//2 if mode==4 else w;pal=np.frombuffer(b[off:],np.uint8).reshape(-1,4)
 for layout in ['linear','block16_by_height']:
  packed=bytearray(off-16)
  for y in range(h):
   for x in range(rowbytes):packed[y*rowbytes+x]=b[16+(y*rowbytes+x if layout=='linear' else (x//16)*(16*h)+y*16+x%16)]
  inds=bytes(v for k in packed for v in [k&15,k>>4]) if mode==4 else bytes(packed);rgba=pal[np.frombuffer(inds,np.uint8)].reshape(h,w,4);digest=sha(rgba.tobytes());match=ref.size==(w,h) and digest==rec['rgba_sha256']
  hypotheses.append({'id':t['id'],'source_sha256':t['source_sha256'],'layout':layout,'size':[w,h],'rgba_sha256':digest,'full_observed_rgba_match':match})
 try:im,details=decoder.decode(b)
 except AssertionError as exc:unsupported.append({'id':t['id'],'reason':str(exc)});continue
 assert im.size==ref.size and im.tobytes()==ref.tobytes() and details['roundtrip_exact'];adopted.append((t,im,details))
assert len(adopted)==3 and len(unsupported)==3
assert {t['source_sha256'] for t,im,d in adopted}=={'f266ad36e0bf4af9b3f03ea6c96385aa8f384fa0db9c80e2b771a5a1bc5f0649'}
mutated=bytearray(Path(adopted[0][0]['source']).read_bytes());mutated[-1]^=1
try:decoder.decode(bytes(mutated))
except AssertionError:negative=True
else:raise AssertionError('Unknown payload was accepted')
backup=R/'qa/backups/special-sky-before';assert not backup.exists();backup.mkdir(parents=True)
for name in ['battle_map_inventory.json','battle_sr_catalog.json','battle_map_runtime_links.json']:shutil.copyfile(R/'qa'/name,backup/name)
shutil.copyfile(R/'tools/ptmd_expanded.py',backup/'ptmd_expanded.py')
new_bindings=[]
for t,im,details in adopted:
 png=Path(t['source']).with_suffix('.png');assert not png.exists();im.save(png)
 t.update(details,png=str(png),width=im.width,height=im.height,rgba_sha256=sha(im.tobytes()),alpha_min=255,alpha_max=255,opaque_fraction=1.,status='decoded source; not upscaled');t.pop('error',None)
 new_bindings.append({'asset_id':t['id'],'logical_full_image_match':True,'source_rgba_sha256':t['rgba_sha256'],'size':[256,4],'matches':[{'key':rec['key'],'paths':[str(p)],'png_sha256':rec['png_sha256'],'rgba_sha256':rec['rgba_sha256'],'size':[256,4]}],'consumer_scene_uv':'unverified: same pixels do not establish each duplicate container consumer','replacement_runtime_verified':False,'source_layout_evidence':'qa/ptmd_special_sky_verification.json'})
inv['failures']=unsupported;inv['summary'].update(decoded=413,failures=3)
group={'group_id':'BM284','width':256,'height':4,'rgba_sha256':rec['rgba_sha256'],'representative':copy.deepcopy(adopted[0][0]),'members':[t['id'] for t,im,d in adopted],'classification':'Observed sky color strip; gradient/lookup consumer needs analysis before remastering','classification_review':'Verified full observed RGBA and exact source payload; special_sky_layout.png','runtime_verified':False,'release_eligible':False,'local_sr_attempted':False,'candidate':None}
assert not any((g['width'],g['height'],g['rgba_sha256'])==(256,4,group['rgba_sha256']) for g in cat['groups'])
cat['groups'].append(group);assert cat['groups'][:-1]==prior_groups;cat['unique_rgba_groups']=284;cat['decoded_asset_count']=413;cat['source_decode_failures']=unsupported
cat['processing_summary'].update(battle_groups_total=284,battle_groups_not_yet_processed=137,source_decoded_entries=413,source_format_unresolved=3)
links['decoded_count']=413;links['matched_asset_count']+=3;links['format_counts']['(4, 48)']+=3;links['matched_format_counts']['(4, 48)']+=3;links['bindings'].extend(new_bindings)
verification={'schema':'brs-special-sky-layout/v1','iso_sha256':inv['iso_sha256'],'adopted_asset_ids':[t['id'] for t,im,d in adopted],'new_group_id':'BM284','hypotheses':hypotheses,'observed_key':rec['key'],'observed_png':str(p),'observed_png_sha256':rec['png_sha256'],'observed_rgba_sha256':rec['rgba_sha256'],'source_payload_sha256':adopted[0][0]['source_sha256'],'baseline_regression_count':len(regression),'baseline_regression':regression,'remaining_unsupported':unsupported,'unknown_payload_rejected':negative,'flag5_general_semantics':'unresolved; exact known-payload support only','duplicate_container_consumption':'not established','replacement_runtime_verified':False,'release_eligible':False,'backup':str(backup)}
for name,obj in [('qa/battle_map_inventory.json',inv),('qa/battle_sr_catalog.json',cat),('qa/battle_map_runtime_links.json',links),('qa/ptmd_special_sky_verification.json',verification)]:write(name,obj)
shutil.copyfile(C/'work/ptmd_expanded.py',R/'tools/ptmd_expanded.py');assert sha((R/'tools/ptmd_expanded.py').read_bytes())==sha((C/'work/ptmd_expanded.py').read_bytes())
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19);sheet=Image.new('RGB',(1060,270),'#293440');d=ImageDraw.Draw(sheet)
for i,(label,pic) in enumerate([('게임 추출 원본',ref),('특수 PTMD 해독 · 전체 RGBA 일치',adopted[0][1])]):
 d.text((12,i*115+8),label,font=font,fill='white');sheet.paste(pic.convert('RGB').resize((1024,64),Image.Resampling.NEAREST),(12,i*115+42))
sheet.save(R/'outputs/special_sky_layout.png')
with (R/'PROGRESS.md').open('a',encoding='utf8') as f:f.write('''

## 2026-09-23 — PTMD-SKY-001: 특수하늘3건의 정확한 원본 배열 확인

- 기존미해독6건을같은ISO의6832관측기록과크기별대조. 256×4의하늘T4 3항목은동일payload이며 linear/low-nibble-first 해석이관측키000000009c3edae9ca6a6a87의전체RGBA와정확히일치. block16×height해석은불일치. 가설이갈리는픽셀증거를확보했다.
- ptmd_expanded.decode에이payloadSHA f266ad36e0bf4af9b3f03ea6c96385aa8f384fa0db9c80e2b771a5a1bc5f0649만허용하는분기추가. flag5전체가linear라는규칙은미확정. 16×1의남은3건및변조된knownpayload는거부검사통과. 410battle+439UI 기존전체849항목의source/RGBA/roundtrip 회귀검사통과.
- 테이블416항목중410→413디코드,특수미해독6→3. 기존283그룹/후보내용정확보존하고고유색상띠BM284추가(미추론). battle_rgba/key연결30→33source항목;3개동일컨테이너각각의장면소비증거는아님. 284개는여전히전투맵고유분모이며게임전체분모아님.
- 원본PTM/ISO변경없고새decodedPNG3개만추가. qa/ptmd_special_sky_verification.json에관측원본경로/해시/대안가설/849검사내역. 이전decoder/3개인벤토리는qa/backups/special-sky-before. outputs/special_sky_layout.png.
- 하늘은짧은gradient/lookup일가능성이있어관측소비구조확인전새질감생성/자동교체하지않음. 새교체런타임/최종배포검증없음. 남은16×1색띠3항목의flag/배열소비는미해결.
''')
print(json.dumps({'decoded':413,'remaining_special':3,'new_group':'BM284','old_baseline_verified':849,'observed_full_rgba_match':True}),flush=True)
