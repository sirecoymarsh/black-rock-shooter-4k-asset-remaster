"""Decode every table-bound texture in the current ISO's battle-map STCM containers."""
import sys,json,struct,hashlib,re,math,collections
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
A=Path(r'P:\AI\Codex\work_archive\2026-07-25\new-chat-2\work')
sys.path.insert(0,str(A/'patch_pipeline'))
from brs_patch import Iso9660,Rtdp
from ptmd_expanded import decode

def sha(b):return hashlib.sha256(b).hexdigest()

identity=json.loads((R/'qa/source_identity.json').read_text('utf8'))
iso_path=Path(identity['iso']['path'])
with iso_path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==identity['iso']['sha256']
dest=R/'workspace/source/battle_maps';dest.mkdir(parents=True,exist_ok=True)
textures=[];containers=[];failures=[];excluded=[]
with Iso9660(iso_path,writable=False) as iso:
    entries=[e for k,e in iso.by_path.items() if '/gamedata/btl/map/' in k and not e.is_dir]
    for e in entries:
        raw=iso._read_at(e.extent*2048,e.size)
        if raw[:4]!=b'RTDP':failures.append({'iso_path':e.path,'reason':'Non-RTDP battle-map root'});continue
        vol=Rtdp(raw)
        for item in vol.items:
            enc=vol.payload(item);b=bytes(x^85 for x in enc)
            asset=e.path.split('/')[-1].lower()+f'/{item.index:03d}_'+item.name
            if b[:4]!=b'STCM':
                excluded.append({'id':asset,'magic':b[:4].hex(),'size':len(b),
                                 'reason':'Non-STCM member; not claimed as a decoded texture container'})
                continue
            folder=dest/asset;folder.mkdir(parents=True,exist_ok=True)
            source=folder/'source.stcm';source.write_bytes(b)
            rec={'id':asset,'iso_path':e.path,'iso_root_sha256':sha(raw),'rtdp_member':item.name,
                 'rtdp_member_index':item.index,'encoded_sha256':sha(enc),'xor55':True,
                 'source':str(source),'sha256':sha(b),'size':len(b),'runtime_verified':False}
            try:
                assert b[4]==1, 'Unsupported STCM version'
                rec['uninterpreted_header_bytes_6_7']=b[6:8].hex()
                count=b[5]
                assert struct.unpack_from('<I',b,16)[0]==0x30+4*count
                offsets=list(struct.unpack_from('<'+str(count)+'I',b,0x30))
                assert len(set(offsets))==count and offsets==sorted(offsets)
                if offsets:assert offsets[0]==struct.unpack_from('<I',b,28)[0]
                assert offsets==[m.start() for m in re.finditer(b'PTMD',b)],'PTMD outside declared table or false magic match'
                rec['texture_count']=count;rec['texture_table_offsets']=offsets;rec['table_verified']=True
                for n,off in enumerate(offsets):
                    end=offsets[n+1] if n+1<count else len(b)
                    data=b[off:end];assert data[:4]==b'PTMD'
                    tex={'id':asset+f'::tex{n:03d}','container':asset,'index':n,'offset':off,
                         'size':len(data),'source_sha256':sha(data),'consumer_status':'STCM texture table bound; material and runtime UV unverified',
                         'tile_repeat':'unverified','runtime_matches':[]}
                    p=folder/f'{n:03d}.ptm';p.write_bytes(data);tex['source']=str(p)
                    try:
                        im,details=decode(data);png=p.with_suffix('.png');im.save(png)
                        alpha=np.asarray(im.getchannel('A'))
                        tex.update(details,png=str(png),width=im.width,height=im.height,
                                   rgba_sha256=sha(im.tobytes()),alpha_min=int(alpha.min()),alpha_max=int(alpha.max()),
                                   opaque_fraction=float((alpha==255).mean()),status='decoded source; not upscaled')
                    except (AssertionError,ValueError) as exc:
                        tex.update(status='decode failed',error=str(exc));failures.append({'id':tex['id'],'reason':str(exc)})
                    textures.append(tex)
            except (AssertionError,ValueError,struct.error) as exc:
                rec.update(table_verified=False,error=str(exc));failures.append({'id':asset,'reason':str(exc)})
            containers.append(rec)
summary={'battle_map_root_files':len(entries),'stcm_containers':len(containers),
         'table_bound_textures':len(textures),'decoded':sum('png' in t for t in textures),'failures':len(failures)}
report={'schema':'brs-battle-map-textures/v1','iso_sha256':identity['iso']['sha256'],
        'scope':'All BTL/MAP files in fixed ISO only; field maps, characters, effects and cutscenes remain separate',
        'summary':summary,'containers':containers,'textures':textures,'failures':failures,'non_stcm_members':excluded,
        'all_game_complete':False,'upscaled_count':0}
(R/'qa/battle_map_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
font=ImageFont.truetype(r'C:\Windows\Fonts\consola.ttf',14)
first=[t for t in textures if t['container'].startswith('map_b_stg01_01.vol/') and 'png' in t]
for start in range(0,len(first),24):
    batch=first[start:start+24];sheet=Image.new('RGB',(1600,math.ceil(len(batch)/4)*300),'#35414f');d=ImageDraw.Draw(sheet)
    for n,t in enumerate(batch):
        x=n%4*400;y=n//4*300;d.text((x+5,y+5),t['id'].split('/',1)[1],font=font,fill='white')
        d.text((x+5,y+25),f"{t['width']}x{t['height']} alpha={t['alpha_min']}..{t['alpha_max']}",font=font,fill='white')
        pic=Image.open(t['png']).convert('RGBA');pic.thumbnail((385,245),Image.Resampling.NEAREST);sheet.paste(pic,(x+5,y+50),pic)
    sheet.save(R/f'qa/battle_map_stage01_sources_{start//24+1}.png')
print(json.dumps(summary),flush=True)
for f in failures[:20]:print(f,flush=True)
