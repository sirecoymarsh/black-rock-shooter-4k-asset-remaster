"""Localize six previously unmapped resident UI atlases; preserve the working bundle.

Uses the existing PPSSPP 8x normalized-UV replacement contract. No ISO writes,
game input, source texture mutation, external translation, or image inference.
"""
from pathlib import Path
import configparser, hashlib, json, math, shutil, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import font_heritage as style

sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1]
G=R.parent/'black-rock-shooter-hd-retexture'
BASE=G/'checkpoints/booster-working-20260924/PSP/TEXTURES/NPUH10126'
OUT=R/'workspace/ui-resident-ko-001'
PACK=OUT/'pack/PSP/TEXTURES/NPUH10126'
REVIEW=R/'outputs/ui-resident-ko-001'
S=8
PREFIX='system.vol::005_if_rsdsys.lpk::'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text('utf-8-sig'))
def write(p,j):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes((json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def cfg(p):
    c=configparser.ConfigParser(interpolation=None,strict=True);c.optionxform=str
    c.read(p,encoding='utf-8-sig');return c
def item(uid,source,target,erase,slot,records,maximum=10,reason=''):
    return dict(uid=uid,source=source,korean=target,erase_region=erase,target_slot=slot,
                sdo_records=records,maximum=maximum,context=reason)

# Semantic Korean authored by Codex internal. Coordinates are source pixels,
# right/bottom exclusive. The erase region comes from source ink, not Korean width.
SPECS=[
dict(id='RUI-001',asset='000::003',sdo='000::000',slot=0,padded=[128,32],labels=[
    item('RUI-001/information','INFORMATION','안내',[0,0,102,12],[1,1,102,11],[],reason='Shared modal prompt heading; static SDO uses its duplicate atlas RUI-002'),
    item('RUI-001/next','NEXT','다음',[102,0,128,8],[104,1,127,6],[35],6,'Advance the current message'),
    item('RUI-001/no','NO','아니요',[0,12,36,23],[1,12,35,22],[31],10,'Negative modal response; original NO has a wide internal gap'),
    item('RUI-001/yes','YES','예',[36,12,71,23],[36,12,70,22],[30],10,'Affirmative modal response'),
]),
dict(id='RUI-002',asset='000::005',sdo='000::000',slot=2,padded=[128,16],labels=[
    item('RUI-002/information','INFORMATION','안내',[0,0,109,12],[1,1,108,11],[13,24,33],10,'Same shared modal heading as RUI-001'),
]),
dict(id='RUI-003',asset='018::009',sdo='018::000',slot=12,padded=[64,64],labels=[
    item('RUI-003/action','ACTION','행동',[0,0,61,12],[1,1,60,11],[24],10,'Generic context-sensitive field action'),
    item('RUI-003/talk','TALK','대화',[0,12,45,23],[1,12,44,22],[34],10,'Talk to a character'),
    item('RUI-003/check','CHECK','조사',[0,23,56,34],[1,23,55,33],[29],10,'Examine a field object'),
]),
dict(id='RUI-004',asset='018::014',sdo='018::000',slot=18,padded=[256,32],labels=[
    item('RUI-004/critical','CRITICAL','치명타',[170,0,216,8],[171,1,215,7],[45],7,'Critical-hit indicator; preserve all damage digits and bars'),
]),
dict(id='RUI-005',asset='019::003',sdo='019::000',slot=0,padded=[128,128],labels=[
    dict(item('RUI-005/menu','MENU','메뉴',[0,0,84,25],None,[49,50,51,52],18,'Menu title assembled from four overlapping letter sprites'),composite=True),
    item('RUI-005/defense','DEFENSE','방어력',[0,24,82,42],[3,26,79,40],[36],14,'Numeric character defense stat'),
    item('RUI-005/attack','ATTACK','공격력',[0,42,71,59],[3,43,68,57],[35],14,'Numeric character attack stat'),
    item('RUI-005/skill','SKILL','스킬',[0,59,62,75],[2,60,59,74],[37],14,'Skill section of the character menu'),
]),
dict(id='RUI-006',asset='019::004',sdo='019::000',slot=1,padded=[128,64],labels=[
    dict(item('RUI-006/customize','CUSTOM + IZE','커스터마이즈',[0,0,72,12],[1,1,71,11],[8,65],10,'Keep the established destination-screen term; full Korean fits the first sprite'),extra_erase_regions=[[0,34,31,45]]),
    item('RUI-006/exp','EXP','경험치',[72,0,105,12],[72,1,104,11],[44],10,'Current experience value'),
    item('RUI-006/items','ITEMS','아이템',[0,12,53,23],[1,12,52,22],[9],10,'Open the existing item menu'),
    item('RUI-006/next','NEXT','다음 레벨',[53,12,98,23],[53,12,96,22],[45],10,'Experience required for the next level; distinct from modal Next'),
    item('RUI-006/options','OPTIONS','설정',[0,23,78,34],[1,23,77,33],[11],10,'Open game settings'),
    item('RUI-006/level','LEVEL','레벨',[0,45,56,56],[1,45,55,55],[48],10,'Character level label'),
]),
]

def scaled_box(b):return tuple(int(x*S) for x in b)
def on_bg(im,bg):
    out=Image.new('RGBA',im.size,bg);out.alpha_composite(im);return out.convert('RGB')

def build():
    for p in [OUT,PACK,REVIEW]:p.mkdir(parents=True,exist_ok=True)
    inventory=read(R/'qa/ui_inventory_expanded.json')
    textures={x['id']:x for x in inventory['textures']}
    containers={x['id']:x for x in inventory['containers']}
    links=read(R/'qa/ui_expanded_links.json')['assets']
    base=cfg(BASE/'textures.ini');assert len(base['hashes'])==711
    # Re-read the committed checkpoint manifest instead of accepting arbitrary inputs.
    frozen=read(G/'checkpoints/booster-working-20260924/snapshot-manifest.json')
    known={x['path']:x['sha256'] for x in frozen['files']}
    for rel in ['textures.ini',*sorted(set(base['hashes'].values()))]:
        p=BASE/rel;assert sha(p)==known[p.relative_to(G).as_posix()],rel
        target=PACK/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    records=[];new_bindings={};all_wording=[];sheets=[]
    for spec in SPECS:
        ident=PREFIX+spec['asset'];a=textures[ident];consumer=containers[PREFIX+spec['sdo']]
        source=Path(a['source']);assert sha(source)==a['decoded_sha256']
        original=Image.open(a['png']).convert('RGBA')
        assert digest(original.tobytes())==a['rgba_sha256']
        matches=links[ident];assert len(matches)==1,ident
        match=matches[0];key=match['key'];assert key not in base['hashes']
        observed=Path(match['paths'][0]);image=Image.open(observed).convert('RGBA')
        assert image.size==tuple(spec['padded']) and image.crop((0,0,*original.size)).tobytes()==original.tobytes(),ident
        # Verify the captured pixels, not only the logical asset's partial rectangle.
        assert digest(image.tobytes())==match['full_rgba_sha256'] if 'full_rgba_sha256' in match else digest(image.tobytes())==match['rgba_sha256']
        before=image.resize((image.width*S,image.height*S),Image.Resampling.NEAREST)
        clean=np.array(before);source_mask=np.zeros(clean.shape[:2],bool)
        erasures=[]
        for label in spec['labels']:
            style.require_chars(label['korean'])
            for box in [label['erase_region'],*label.get('extra_erase_regions',[])]:
                x,y,x1,y1=scaled_box(box);assert 0<=x<x1<=original.width*S and 0<=y<y1<=original.height*S
                # Transparent source-only glyph atlases. Include every nonzero alpha,
                # including source antialias/shadow pixels, within the source region.
                mask=clean[y:y1,x:x1,3]>0
                source_mask[y:y1,x:x1]|=mask
                erasures.append(dict(uid=label['uid'],box=box,source_ink_pixels=int(mask.sum())))
        assert source_mask.any()
        clean[source_mask]=[255,255,255,0]
        clean_image=Image.fromarray(clean,'RGBA');final=clean_image.copy()
        layer=Image.new('RGBA',final.size,(255,255,255,0));layouts=[]
        sdo=consumer['sdo']['records']
        for label in spec['labels']:
            evidence=[]
            for rid in label['sdo_records']:
                r=sdo[rid];assert r['id']==rid and r['texture_slot']==spec['slot']
                uv=[r['uv_normalized'][i]*image.size[i%2] for i in range(4)]
                assert all(abs(v-round(v))<1e-6 for v in uv)
                evidence.append(dict(record=rid,uv_box=list(map(round,uv)),layout_xywh=r['layout_xywh'],vertices=r['vertices'],vertex_sha256=r['vertex_bytes_sha256']))
            if label.get('composite'):
                pieces=[]
                for e in evidence:
                    v=e['vertices'];xy=[round(e['layout_xywh'][i]+min(p[i+2] for p in v)) for i in [0,1]]
                    uv=e['uv_box'];w,h=uv[2]-uv[0],uv[3]-uv[1]
                    assert [max(p[i+2] for p in v)-min(p[i+2] for p in v) for i in [0,1]]==[w,h]
                    pieces.append((uv,xy,w,h))
                left=min(p[1][0] for p in pieces);top=min(p[1][1] for p in pieces)
                width=max(p[1][0]+p[2] for p in pieces)-left;height=max(p[1][1]+p[3] for p in pieces)-top
                tile,size=style.make_text(label['korean'],width*S,height*S,maximum=label['maximum'],minimum=5,align='center')
                used=np.zeros((height*S,width*S),bool)
                for uv,xy,w,h in pieces:
                    x=(xy[0]-left)*S;y=(xy[1]-top)*S
                    crop=np.array(tile.crop((x,y,x+w*S,y+h*S)));owned=used[y:y+h*S,x:x+w*S]
                    crop[owned,3]=0;layer.alpha_composite(Image.fromarray(crop,'RGBA'),(uv[0]*S,uv[1]*S));used[y:y+h*S,x:x+w*S]=True
                assert np.all(used[np.array(tile)[:,:,3]>0])
                label_layout=dict(composite_box=[left,top,left+width,top+height],overlap_rule='first sprite owns overlap',size_px=size)
            else:
                box=label['target_slot'];x,y,x1,y1=scaled_box(box)
                if evidence:assert box==evidence[0]['uv_box'],(label['uid'],box,evidence[0]['uv_box'])
                tile,size=style.make_text(label['korean'],x1-x,y1-y,maximum=label['maximum'],minimum=4,align='left')
                ink=tile.getchannel('A').getbbox();assert ink and 0<=ink[0]<ink[2]<=tile.width and 0<=ink[1]<ink[3]<=tile.height
                layer.alpha_composite(tile,(x,y));label_layout=dict(slot=box,ink_bounds_output=[x+ink[0],y+ink[1],x+ink[2],y+ink[3]],size_px=size)
            layouts.append(dict(uid=label['uid'],source=label['source'],korean=label['korean'],context=label['context'],consumer_records=evidence,**label_layout))
            all_wording.append(dict(asset_id=ident,**label,translator_model='Codex internal'))
        final.alpha_composite(layer)
        target_mask=np.array(layer)[:,:,3]>0;owned=source_mask|target_mask
        assert np.array_equal(np.array(final)[~owned],np.array(before)[~owned])
        # No visible source may remain in any source-text region on the clean plate.
        for label in spec['labels']:
            for box in [label['erase_region'],*label.get('extra_erase_regions',[])]:
                assert not clean_image.crop(scaled_box(box)).getchannel('A').getbbox(),label['uid']
        p=OUT/'assets'/spec['id'];p.mkdir(parents=True,exist_ok=True)
        files={}
        for name,im in [('source-8x',before),('source-glyph-mask',Image.fromarray(source_mask.astype('uint8')*255)),('clean-plate',clean_image),('korean-layer',layer),('candidate',final),('owned-mask',Image.fromarray(owned.astype('uint8')*255))]:
            dest=p/(name+'.png');im.save(dest,optimize=True);reopened=Image.open(dest)
            assert reopened.size==im.size and reopened.tobytes()==im.tobytes()
            files[name]=dict(path=str(dest),sha256=sha(dest))
        rel='resident-ko-001/'+key+'.png';dest=PACK/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p/'candidate.png',dest)
        new_bindings[key]=rel
        record=dict(id=spec['id'],asset_id=ident,source=str(source),source_sha256=sha(source),source_rgba_sha256=a['rgba_sha256'],source_size=list(original.size),padded_size=list(image.size),output_size=list(final.size),scale=S,observed_path=str(observed),observed_png_sha256=sha(observed),observed_rgba_sha256=digest(image.tobytes()),key=key,replacement=rel,output_sha256=sha(dest),consumer_path=consumer['source'],consumer_sha256=sha(Path(consumer['source'])),texture_slot=spec['slot'],erase_regions=erasures,layouts=layouts,files=files,source_ink_count=int(source_mask.sum()),outside_owned_mask_diff_pixels=0,clean_plate_visible_source_pixels=0,static_checks='PASS',runtime_verified=False,consumer_scope='Listed static SDO records; dynamic animation and code-generated uses require runtime QA')
        records.append(record)
        # Diagnostic pages only. Extra margins never enter the replacement PNG.
        panel_width=max(final.width,640);h=final.height
        sheet=Image.new('RGB',(panel_width+24,(h+38)*3+38),'#202d38');d=ImageDraw.Draw(sheet)
        d.text((12,8),spec['id']+' | SOURCE / CLEAN PLATE / KOREAN | 8x',fill='white')
        for idx,im in enumerate([before,clean_image,final]):
            sheet.paste(on_bg(im,'#283746'),(12,38+idx*(h+38)))
        dest=REVIEW/(spec['id']+'-proof.png');sheet.save(dest);sheets.append(str(dest))
    bindings=dict(base['hashes']);bindings.update(new_bindings);assert len(bindings)==717
    ini='[options]\n'+''.join(k+' = '+v+'\n' for k,v in base['options'].items())+'\n[hashes]\n'+''.join(k+' = '+v+'\n' for k,v in sorted(bindings.items()))
    (PACK/'textures.ini').write_bytes(ini.encode('utf8'))
    for key,rel in base['hashes'].items():assert sha(PACK/rel)==sha(BASE/rel),key
    for key,rel in new_bindings.items():assert (PACK/rel).is_file()
    manifest=dict(schema='brs-resident-ko-001/v1',translator_model='Codex internal',task='brs-hd-ui-fonts',authored_by='active Codex internal model',source_language='English raster UI from the established NPUH10126 Korean-patch baseline',target_language='Korean',replacement_surface='Previously untranslated resident UI texture labels; existing Korean script and font mappings preserved',baseline_iso_sha256='b162f45f10622992a4fd068b8414008cd7f455c7c9b203c1c610554d43de9b21',baseline_tag='booster-working-20260924',delivery='Staged cumulative PPSSPP replacement pack; successful live bundle untouched',geometry_exception='Existing PPSSPP 8x normalized-UV replacement contract: same logical crop, origin, padding and UV layout scaled exactly by 8; no new source rows or columns',font=style.PROFILE,build_script_sha256=sha(Path(__file__)),font_renderer_sha256=sha(R/'tools/font_heritage.py'),asset_count=len(records),label_count=len(all_wording),baseline_keys=711,new_keys=len(new_bindings),total_keys=len(bindings),pack=str(PACK),records=records,preview_sheets=sheets,runtime_verified=False,remaining='Visual review and independent static QA, then runtime acceptance. Whole-game asset localization remains incomplete.')
    write(OUT/'translation-map.json',dict(translator_model='Codex internal',entries=all_wording))
    write(OUT/'manifest.json',manifest)
    write(R/'qa/ui_resident_ko_001.json',manifest)
    print(json.dumps({k:manifest[k] for k in ['asset_count','label_count','new_keys','total_keys','pack','runtime_verified']},ensure_ascii=False))

if __name__=='__main__':build()
