"""Korean title menu, including shared GAME UVs and baked selection glows."""
from pathlib import Path
import configparser, hashlib, json, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import font_heritage as style

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf8')
R = Path(__file__).resolve().parents[1]
G = R.parent / 'black-rock-shooter-hd-retexture'
BASE = R / 'workspace/ui-resident-ko-001/pack/PSP/TEXTURES/NPUH10126'
OUT = R / 'workspace/ui-title-ko-001'
PACK = OUT / 'pack/PSP/TEXTURES/NPUH10126'
REVIEW = R / 'outputs/ui-title-ko-001'
PREFIX = 'title.vol::001_if_title.zzz::'
S = 8

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text('utf-8-sig'))
def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf8'))
def cfg(p):
    c = configparser.ConfigParser(interpolation=None); c.optionxform = str
    c.read(p, encoding='utf-8-sig'); return c
def sb(b): return tuple(round(v*S) for v in b)

# LOAD's second sprite reuses GAME inside NEW GAME. Keep that region empty.
# Korean words occupy independent source slots, with a shared screen right edge
# of 417. All consumers, canvas dimensions and non-text chrome stay unchanged.
WORDS = [
    dict(uid='TUI-001/new', source='NEW GAME', korean='새 게임', sharp=32, glow=42, erase=[0,0,12,85]),
    dict(uid='TUI-001/load', source='LOAD GAME', korean='불러오기', sharp=34, glow=43, erase=[34,0,45,45], shared_tail=65),
    dict(uid='TUI-001/gallery', source='GALLERY', korean='갤러리', sharp=53, glow=55, erase=[45,0,56,78]),
    dict(uid='TUI-001/options', source='OPTIONS', korean='설정', sharp=36, glow=44, erase=[12,0,23,72]),
    dict(uid='TUI-001/install', source='INSTALL', korean='설치', sharp=38, glow=45, erase=[23,0,34,71]),
]

def uv_box(rec, size):
    box = [v*size[n%2] for n,v in enumerate(rec['uv_normalized'])]
    assert all(abs(v-round(v))<1e-7 for v in box)
    return [round(v) for v in box]

def screen_crop(image, rec):
    # These title sprites are exactly a 90-degree rotation, not a guessed UV map.
    size = (image.width//S, image.height//S)
    box = uv_box(rec, size)
    u0,v0,u1,v1 = box
    expected = [[u1,v0,0,0],[u0,v0,0,u1-u0],
                [u1,v1,v1-v0,0],[u0,v1,v1-v0,u1-u0]]
    verts = [[v[0]*size[0],v[1]*size[1],v[2],v[3]] for v in rec['vertices']]
    assert np.allclose(verts, expected), rec['id']
    crop = image.crop(sb(box)).transpose(Image.Transpose.ROTATE_90)
    assert crop.size == (rec['layout_xywh'][2]*S, rec['layout_xywh'][3]*S)
    return crop

def put_screen(layer, rec, tile):
    size = (layer.width//S, layer.height//S)
    box = uv_box(rec, size)
    assert tile.size == (rec['layout_xywh'][2]*S, rec['layout_xywh'][3]*S)
    layer.alpha_composite(tile.transpose(Image.Transpose.ROTATE_270), (box[0]*S,box[1]*S))

def white(alpha):
    out = Image.new('RGBA', alpha.size, (255,255,255,0)); out.putalpha(alpha); return out

def build():
    for p in (OUT, PACK, REVIEW): p.mkdir(parents=True, exist_ok=True)
    inv = read(R/'qa/ui_inventory_expanded.json')
    tex = {x['id']:x for x in inv['textures']}
    container = next(x for x in inv['containers'] if x['id']==PREFIX+'009')
    sdo = container['sdo']['records']
    links = read(R/'qa/ui_expanded_links.json')['assets']
    source_sdo = Path(container['source'])
    accepted = read(R/'qa/ui_resident_ko_001_acceptance.json')
    prior = read(R/'workspace/ui-resident-ko-001/manifest.json')
    assert sha(R/'workspace/ui-resident-ko-001/manifest.json') == accepted['manifest_sha256']
    base = cfg(BASE/'textures.ini'); assert len(base['hashes']) == 717
    frozen = read(G/'checkpoints/booster-working-20260924/snapshot-manifest.json')
    old_hashes = {x['path'].split('/NPUH10126/',1)[1]:x['sha256'] for x in frozen['files'] if '/NPUH10126/' in x['path']}
    expected_hashes = {**old_hashes, **{x['replacement']:x['output_sha256'] for x in prior['records']}}
    for rel in set(base['hashes'].values()):
        assert sha(BASE/rel) == expected_hashes[rel], rel
        dest = PACK/rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(BASE/rel,dest)
    assets = {}
    for aid,slot,padded in [('004',5,(256,512)),('005',7,(64,128))]:
        a = tex[PREFIX+aid]; match, = links[PREFIX+aid]
        source = Path(a['source']); observed = Path(match['paths'][0])
        assert sha(source) == a['decoded_sha256']
        logical = Image.open(a['png']).convert('RGBA')
        assert hashlib.sha256(logical.tobytes()).hexdigest() == a['rgba_sha256']
        image = Image.open(observed).convert('RGBA')
        assert image.size == padded and image.crop((0,0,*logical.size)).tobytes()==logical.tobytes()
        assert hashlib.sha256(image.tobytes()).hexdigest() == match['rgba_sha256']
        assert match['key'] not in base['hashes']
        before = image.resize((padded[0]*S,padded[1]*S),Image.Resampling.NEAREST)
        assets[aid] = dict(source=a,match=match,before=before,clean=np.array(before),
                           source_mask=np.zeros((before.height,before.width),bool),
                           layer=Image.new('RGBA',before.size,(255,255,255,0)),erasures=[],slot=slot)

    def erase(aid,box,uid):
        a = assets[aid]; x,y,x1,y1=sb(box)
        assert 0<=box[0]<box[2]<=a['source']['width'] and 0<=box[1]<box[3]<=a['source']['height']
        ink = a['clean'][y:y1,x:x1,3]>0
        a['source_mask'][y:y1,x:x1] |= ink
        a['clean'][y:y1,x:x1][ink] = [255,255,255,0]
        a['erasures'].append(dict(uid=uid,box=box,source_ink_pixels=int(ink.sum())))

    for w in WORDS: erase('005',w['erase'],w['uid'])
    labels=[]
    for w in WORDS:
        sharp,glow = sdo[w['sharp']],sdo[w['glow']]
        assert sharp['texture_slot']==7 and glow['texture_slot']==5
        sx,sy,sw,sh=sharp['layout_xywh'];gx,gy,gw,gh=glow['layout_xywh']
        width = 417-sx
        # Even for NEW GAME the output ends before the reused GAME sub-crop.
        assert 0<width<=sw and (w['sharp']!=32 or width<=40)
        word,size = style.make_text(w['korean'],width*S,sh*S,maximum=9,minimum=8,align='right')
        tile = Image.new('RGBA',(sw*S,sh*S),(255,255,255,0));tile.alpha_composite(word)
        put_screen(assets['005']['layer'],sharp,tile)
        # Keep the baked selector dot and its first 20 source pixels exactly.
        # The complete old word/halo lies in the remaining text-owned crop.
        u0,v0,u1,v1=uv_box(glow,(256,512))
        erase('004',[u0-1,v0+20,u1+1,v1+1],w['uid']+'/glow')
        glow_source=screen_crop(assets['004']['before'],glow)
        # Pixels before the word are a constant-alpha connector in the source.
        # Preserve its exact RGBA only up to the original word minus the blur guard.
        connector=Image.new('RGBA',glow_source.size,(255,255,255,0))
        connector_arr=np.array(connector)
        original_arr=np.array(glow_source)
        # Source analysis identifies the connector at native rows 13..15.
        # Retain only the continuous alpha-17 run joined to the selector,
        # with a six-pixel guard before source letters. Isolated low-alpha
        # glyph fragments are never accepted merely for being faint.
        for yy in range(13*S,16*S):
            for xx in range(20*S,max(20,sx-gx-6)*S):
                if original_arr[yy,xx,3]!=17: break
                connector_arr[yy,xx]=original_arr[yy,xx]
        connector=Image.fromarray(connector_arr)
        if connector.getchannel('A').getbbox():
            restored=np.array(assets['004']['before'])
            carrier=Image.new('RGBA',assets['004']['before'].size,(255,255,255,0))
            put_screen(carrier,glow,connector)
            cm=np.array(carrier)[:,:,3]>0
            assets['004']['clean'][cm]=restored[cm]
            assets['004']['source_mask'][cm]=False
        glyph=Image.new('RGBA',(gw*S,gh*S),(255,255,255,0))
        glyph.alpha_composite(tile,(round((sx-gx)*S),round((sy-gy)*S)))
        halo=white(glyph.getchannel('A').filter(ImageFilter.GaussianBlur(2*S)))
        # The same target glyph produces both states; no independently guessed glow.
        assert not halo.crop((0,0,20*S,gh*S)).getchannel('A').getbbox()
        put_screen(assets['004']['layer'],glow,halo)
        labels.append(dict(**w,font_size_px=size,screen_right=417,sharp_consumer=sharp,glow_consumer=glow,
                           halo_radius_native=2,translator_model='Codex internal'))

    prompt=sdo[31];u0,v0,u1,v1=uv_box(prompt,(256,512))
    erase('004',[u0-1,v0-1,u1+1,v1+1],'TUI-001/start')
    prompt_tile,size=style.make_text('START 버튼을\n눌러 주세요',66*S,33*S,maximum=9,minimum=8,align='center',spacing=2,edge_margin=3)
    halo=white(prompt_tile.getchannel('A').filter(ImageFilter.GaussianBlur(1.2*S)))
    halo.alpha_composite(prompt_tile);put_screen(assets['004']['layer'],prompt,halo)
    labels.append(dict(uid='TUI-001/start',source='PRESS START',korean='START 버튼을\n눌러 주세요',consumer=prompt,font_size_px=size,translator_model='Codex internal'))
    # Reused GAME must contribute no Korean suffix to LOAD GAME.
    assert not screen_crop(assets['005']['layer'],sdo[65]).getchannel('A').getbbox()

    records=[];bindings=dict(base['hashes'])
    for aid,a in assets.items():
        clean=Image.fromarray(a['clean']);final=clean.copy();final.alpha_composite(a['layer'])
        owned=a['source_mask']|(np.array(a['layer'])[:,:,3]>0)
        assert np.array_equal(np.array(final)[~owned],np.array(a['before'])[~owned])
        assert np.all(np.array(clean)[:,:,3][a['source_mask']]==0)
        p=OUT/'assets'/('TUI-'+aid);p.mkdir(parents=True,exist_ok=True);files={}
        for role,im in [('source-8x',a['before']),('source-glyph-mask',Image.fromarray(a['source_mask'].astype('uint8')*255)),('clean-plate',clean),('korean-layer',a['layer']),('candidate',final),('owned-mask',Image.fromarray(owned.astype('uint8')*255))]:
            dest=p/(role+'.png');im.save(dest,optimize=True)
            assert Image.open(dest).tobytes()==im.tobytes();files[role]=dict(path=str(dest),sha256=sha(dest))
        key=a['match']['key'];rel='title-ko-001/'+key+'.png';dest=PACK/rel
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/'candidate.png',dest);bindings[key]=rel
        records.append(dict(id='TUI-'+aid,asset_id=PREFIX+aid,source=a['source']['source'],source_sha256=sha(Path(a['source']['source'])),source_rgba_sha256=a['source']['rgba_sha256'],
            observed_path=a['match']['paths'][0],observed_png_sha256=sha(Path(a['match']['paths'][0])),padded_size=a['match']['size'],logical_size=[a['source']['width'],a['source']['height']],
            key=key,replacement=rel,output_sha256=sha(dest),files=files,erasures=a['erasures'],texture_slot=a['slot'],outside_owned_mask_diff_pixels=0))
    assert len(bindings)==719
    ini='[options]\n'+''.join(k+' = '+v+'\n' for k,v in base['options'].items())+'\n[hashes]\n'+''.join(k+' = '+v+'\n' for k,v in sorted(bindings.items()))
    (PACK/'textures.ini').write_bytes(ini.encode('utf8'))
    m=dict(schema='brs-title-ko-001/v1',translator_model='Codex internal',task='brs-hd-ui-fonts',font=style.PROFILE,build_script_sha256=sha(Path(__file__)),font_renderer_sha256=sha(R/'tools/font_heritage.py'),
        previous_batch_manifest_sha256=sha(R/'workspace/ui-resident-ko-001/manifest.json'),sdo_source=str(source_sdo),sdo_sha256=sha(source_sdo),pack=str(PACK),
        asset_count=2,semantic_label_count=6,localized_visual_regions=11,baseline_keys=717,new_keys=2,total_keys=719,records=records,labels=labels,
        geometry_exception='Established exact 8x normalized-UV replacement; original canvas, UV, sprite origins, selector icons and legal/logo artwork unchanged.',
        layout_decision='Shared GAME crop is blank. All five Korean menu labels align at screen x=417 inside their original independent slots, rather than the English right edge 464. This avoids incorrect suffixes without patching SDO or ISO.',
        state_closure='Five sharp/menu-glow pairs plus PRESS START; record 65 shared suffix blank and all other static consumers of slots 5/7 protected.',
        runtime_verified=False,live_installation_performed=False,static_review='pending',remaining='Persisted-file verification, static state reconstruction, direct visual review, then in-game acceptance.')
    write(OUT/'manifest.json',m);write(R/'qa/ui_title_ko_001.json',m)
    write(OUT/'translation-map.json',dict(translator_model='Codex internal',entries=[{k:x[k] for k in ['uid','source','korean','translator_model']} for x in labels]))
    print(json.dumps({k:m[k] for k in ['asset_count','semantic_label_count','localized_visual_regions','new_keys','total_keys','runtime_verified']},ensure_ascii=False))

if __name__=='__main__': build()
