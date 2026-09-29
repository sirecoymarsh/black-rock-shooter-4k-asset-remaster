"""Independent persisted-byte and affine SDO review of the title batch."""
from pathlib import Path
import configparser, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/ui-title-ko-002';S=8
m=json.loads((O/'manifest.json').read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def compose(image,rec,dimensions):
    # General affine sampling uses the actual vertex coordinates, independently
    # of the builder's rotation-only implementation.
    v=np.array(rec['vertices']);xy=v[:,2:4];uv=v[:,:2]*np.array(dimensions)
    coeff=np.linalg.lstsq(np.c_[xy,np.ones(len(xy))],uv,rcond=None)[0]
    assert np.max(np.abs(np.c_[xy,np.ones(len(xy))]@coeff-uv))<1e-7
    lo=xy.min(0);hi=xy.max(0);w,h=np.rint((hi-lo)*S).astype(int)
    yy,xx=np.mgrid[:h,:w]
    p=np.stack([lo[0]+(xx+.5)/S,lo[1]+(yy+.5)/S,np.ones_like(xx)],-1)@coeff
    pix=np.floor(p*S+1e-7).astype(int);arr=np.array(image)
    assert pix[:,:,0].min()>=0 and pix[:,:,0].max()<image.width
    assert pix[:,:,1].min()>=0 and pix[:,:,1].max()<image.height
    return Image.fromarray(arr[pix[:,:,1],pix[:,:,0]])

inv=json.loads((R/'qa/ui_inventory_expanded.json').read_text('utf8'))
sd=next(x for x in inv['containers'] if x['id']=='title.vol::001_if_title.zzz::009')['sdo']['records']
old_sd=sd;sd=m['sdo_records']
assert sha(Path(m['sdo_source']))==m['sdo_sha256']
assets={};checks=[]
for rec in m['records']:
    im={}
    for role,f in rec['files'].items():
        p=Path(f['path']);assert sha(p)==f['sha256'];im[role]=Image.open(p).copy()
    native=Image.open(rec['observed_path']).convert('RGBA')
    assert sha(Path(rec['observed_path']))==rec['observed_png_sha256']
    assert native.resize(im['candidate'].size,Image.Resampling.NEAREST).tobytes()==im['source-8x'].tobytes()
    old=np.array(im['source-8x']);new=np.array(im['candidate']);owned=np.array(im['owned-mask'])>0
    assert np.array_equal(old[~owned],new[~owned])
    mask=np.array(im['source-glyph-mask'])>0
    assert np.all(np.array(im['clean-plate'])[:,:,3][mask]==0)
    comp=im['clean-plate'].copy();comp.alpha_composite(im['korean-layer'])
    assert comp.tobytes()==im['candidate'].tobytes()
    assert sha(Path(m['pack'])/rec['replacement'])==rec['output_sha256']
    logical_h=rec['logical_size'][1]*S
    assert np.array_equal(old[logical_h:],new[logical_h:])
    im['dimensions']=rec['padded_size'];assets[rec['texture_slot']]=im

modified={31,32,34,36,38,42,43,44,45,53,55,65}
for rec in sd:
    if rec['texture_slot'] not in assets or 'vertices' not in rec or rec['id'] in modified:continue
    a=assets[rec['texture_slot']]
    old=compose(a['source-8x'],rec,a['dimensions']);new=compose(a['candidate'],rec,a['dimensions'])
    assert old.tobytes()==new.tobytes(),rec['id']
    checks.append(dict(consumer=rec['id'],texture_slot=rec['texture_slot'],rgba_exact=True))

for word in m['labels'][:5]:
    sharp=word['sharp_consumer'];glow=word['glow_consumer']
    a=assets[7];b=assets[5]
    tile=compose(a['candidate'],sharp,a['dimensions'])
    if 'shared_tail' in word:
        joined=Image.new('RGBA',(90*S,10*S));joined.alpha_composite(tile)
        joined.alpha_composite(compose(a['candidate'],sd[word['shared_tail']],a['dimensions']),(43*S,0));tile=joined
    assert tile.getchannel('A').getbbox()
    x,y,w,h=sharp['layout_xywh'];gx,gy,gw,gh=glow['layout_xywh']
    bbox=tile.getchannel('A').getbbox();assert x+bbox[2]/S<=464 and x+bbox[0]/S>=x
    assert bbox[3]-bbox[1]>=77,word['uid']
    expected=Image.new('RGBA',(gw*S,gh*S));expected.alpha_composite(tile,((x-gx)*S,(y-gy)*S))
    expected_alpha=expected.getchannel('A').filter(ImageFilter.GaussianBlur(2*S))
    actual=compose(b['korean-layer'],glow,b['dimensions']).getchannel('A')
    assert actual.tobytes()==expected_alpha.tobytes(),word['uid']
    old_dot=compose(b['source-8x'],glow,b['dimensions']).crop((0,0,20*S,gh*S))
    new_dot=compose(b['candidate'],glow,b['dimensions']).crop((0,0,20*S,gh*S))
    assert old_dot.tobytes()==new_dot.tobytes()
    clean=np.array(compose(b['clean-plate'],glow,b['dimensions']))[:,:,3]
    for yy in range(gh*S):
        active=np.flatnonzero(clean[yy,20*S:])+20*S
        if len(active):
            assert 13*S<=yy<16*S
            assert active[0]==20*S and np.all(np.diff(active)==1)
            assert active[-1]<(x-gx-6)*S and np.all(clean[yy,active]==17)
    checks.append(dict(consumer=glow['id'],selector_first_20_pixels_exact=True,sharp_glow_alignment_exact=True))
assert compose(assets[7]['candidate'],sd[65],assets[7]['dimensions']).getchannel('A').getbbox()
assert sd[65]['layout_xywh']==[417,208,47,10]
assert sd[65]['uv_normalized']==[55/64,1/128,63/64,48/128]
for n,(a,b) in enumerate(zip(old_sd,sd)):
    if n!=65: assert a==b

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
out=R/'outputs/ui-title-ko-002';out.mkdir(parents=True,exist_ok=True);pages=[]
def save(im,name):
    p=out/name;im.save(p);pages.append(dict(path=str(p),sha256=sha(p)))
def plate(im):
    bg=Image.new('RGBA',im.size,'#283746');bg.alpha_composite(im);return bg.convert('RGB')

# Same static SDO coordinates in each state. Runtime animation/tint is unknown.
menu_rows=[]
for selected in range(5):
    row=Image.new('RGB',(1260,430),'#202d38');d=ImageDraw.Draw(row)
    d.text((10,6),'선택 상태: '+m['labels'][selected]['korean']+'  |  SDO 정적 조립 · 실제 게임 캡처 아님',font=font,fill='white')
    for col,role in enumerate(['source-8x','candidate']):
        canvas=Image.new('RGBA',(150*S,94*S),'#283746')
        glow=m['labels'][selected]['glow_consumer'];im=compose(assets[5][role],glow,assets[5]['dimensions'])
        canvas.alpha_composite(im,((glow['layout_xywh'][0]-330)*S,(glow['layout_xywh'][1]-180)*S))
        for word in m['labels'][:5]:
            rec=word['sharp_consumer'];im=compose(assets[7][role],rec,assets[7]['dimensions'])
            canvas.alpha_composite(im,((rec['layout_xywh'][0]-330)*S,(rec['layout_xywh'][1]-180)*S))
            if 'shared_tail' in word:
                rec=(old_sd if role=='source-8x' else sd)[word['shared_tail']];im=compose(assets[7][role],rec,assets[7]['dimensions'])
                canvas.alpha_composite(im,((rec['layout_xywh'][0]-330)*S,(rec['layout_xywh'][1]-180)*S))
        # Original selected square is identical in all five consumers.
        rec=sd[[40,47,56,48,49][selected]];im=compose(assets[7][role],rec,assets[7]['dimensions'])
        canvas.alpha_composite(im,((rec['layout_xywh'][0]-330)*S,(rec['layout_xywh'][1]-180)*S))
        resized=canvas.convert('RGB').resize((600,376),Image.Resampling.LANCZOS)
        row.paste(resized,(10+630*col,42))
        d.text((10+630*col,24),'원본' if col==0 else '한국어',font=font,fill='white')
    menu_rows.append(row)
for n,start in enumerate([0,3],1):
    rows=menu_rows[start:start+3];page=Image.new('RGB',(1260,sum(x.height for x in rows)),'#202d38');y=0
    for row in rows:page.paste(row,(0,y));y+=row.height
    save(page,f'menu-states-{n}.png')

for slot,name,scale in [(7,'sharp-atlas-proof.png',6),(5,'glow-atlas-proof.png',2)]:
    a=assets[slot];rec=next(x for x in m['records'] if x['texture_slot']==slot)
    w,h=rec['logical_size'];panelw=w*scale;panelh=h*scale
    page=Image.new('RGB',(3*(panelw+20),panelh+48),'#202d38');d=ImageDraw.Draw(page)
    for j,role in enumerate(['source-8x','clean-plate','candidate']):
        im=a[role].crop((0,0,w*S,h*S)).resize((panelw,panelh),Image.Resampling.LANCZOS)
        page.paste(plate(im),(j*(panelw+20)+10,36));d.text((j*(panelw+20)+10,7),role,font=font,fill='white')
    save(page,name)

rows=[]
for word in m['labels'][:5]:
    rec=word['glow_consumer'];row=Image.new('RGB',(1560,140),'#202d38');d=ImageDraw.Draw(row)
    d.text((10,3),word['source']+' → '+word['korean']+' | SOURCE / CLEAN PLATE / KOREAN GLOW',font=font,fill='white')
    for j,role in enumerate(['source-8x','clean-plate','candidate']):
        im=compose(assets[5][role],rec,assets[5]['dimensions']).resize((500,88),Image.Resampling.LANCZOS)
        row.paste(plate(im),(10+j*520,38))
    rows.append(row)
page=Image.new('RGB',(1560,700),'#202d38')
for j,row in enumerate(rows):page.paste(row,(0,j*140))
save(page,'glow-regions-proof.png')

page=Image.new('RGB',(1644,312),'#202d38');d=ImageDraw.Draw(page)
for j,role in enumerate(['source-8x','clean-plate','candidate']):
    im=compose(assets[5][role],sd[31],assets[5]['dimensions'])
    page.paste(plate(im),(10+j*548,38));d.text((10+j*548,7),role,font=font,fill='white')
save(page,'start-prompt-proof.png')

c=configparser.ConfigParser(interpolation=None);c.optionxform=str;c.read(Path(m['pack'])/'textures.ini',encoding='utf8')
b=configparser.ConfigParser(interpolation=None);b.optionxform=str
base=R/'workspace/ui-resident-ko-001/pack/PSP/TEXTURES/NPUH10126';b.read(base/'textures.ini',encoding='utf8')
assert len(c['hashes'])==719 and len(b['hashes'])==717
assert dict(c['options'])==dict(b['options'])
for key,rel in b['hashes'].items():assert c['hashes'][key]==rel and sha(Path(m['pack'])/rel)==sha(base/rel)
for rel in c['hashes'].values():assert (Path(m['pack'])/rel).is_file()
assert all(x['translator_model']=='Codex internal' for x in m['labels'])
report=dict(schema='brs-title-ko-static-review/v1',manifest_sha256=sha(O/'manifest.json'),static_status='PASS',asset_count=2,semantic_label_count=6,
    visual_regions=11,protected_checks=checks,protected_check_count=len(checks),baseline_keys_preserved=717,new_exact_keys=2,total_keys=719,
    source_mask_erased=True,outside_owned_pixels='exact',persisted_composite_exact=True,shared_GAME_alias_separated=True,sharp_glow_pairs=5,
    original_right_edge_restored=464,menu_ink_height_native=9.75,consumer_patch_required=m['consumer_patch']['patched_sha256'],
    comparison_pages=pages,visual_review='pending',runtime_verified=False,limitation='Point-sampled static SDO reconstruction; code-driven tint, animation and texture filtering remain unverified.')
(R/'qa/ui_title_ko_002_review.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(json.dumps({'static_checks':'PASS','protected_checks':len(checks),'visual_pages':len(pages),'runtime_verified':False}))
