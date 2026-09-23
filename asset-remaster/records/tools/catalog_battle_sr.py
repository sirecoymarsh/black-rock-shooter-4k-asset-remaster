"""Inventory exact pixel-equivalent materials; classifications remain explicit."""
import hashlib, json, math
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts')
inv=json.loads((R/'qa/battle_map_inventory.json').read_text('utf8'))
previous_path=R/'qa/battle_sr_catalog.json'
previous=json.loads(previous_path.read_text('utf8')) if previous_path.exists() else {}
previous_groups={f"{g['width']}x{g['height']}:{g['rgba_sha256']}":g for g in previous.get('groups',[])}
next_id=max([int(g['group_id'][2:]) for g in previous_groups.values()]+[0])+1
groups={}
for t in inv['textures']:
    if not t.get('rgba_sha256'): continue
    k=f"{t['width']}x{t['height']}:{t['rgba_sha256']}"
    if k not in groups:
        if k in previous_groups:
            groups[k]={**previous_groups[k],'representative':t,'members':[]}
        else:
            groups[k]={'group_id':f'BM{next_id:03d}', 'width':t['width'],'height':t['height'],
                   'rgba_sha256':t['rgba_sha256'],'representative':t,'members':[],
                   'classification':'unreviewed','runtime_verified':False,'release_eligible':False}
            next_id+=1
    groups[k]['members'].append(t['id'])
items=list(groups.values())
stage1=[g for g in items if any('stg01_' in i for i in g['members'])]
font=ImageFont.truetype(r'C:\Windows\Fonts\consola.ttf',17)
out=R/'qa/battle-source-catalog';out.mkdir(exist_ok=True)
for start in range(0,len(stage1),16):
    batch=stage1[start:start+16]
    sheet=Image.new('RGB',(1600,4*340),'#293440');d=ImageDraw.Draw(sheet)
    for n,g in enumerate(batch):
        t=g['representative'];src=Image.open(t['png']).convert('RGBA')
        assert hashlib.sha256(src.tobytes()).hexdigest()==g['rgba_sha256']
        x=n%4*400+8;y=n//4*340
        short=t['container'].split('/')[0].replace('map_b_','').replace('.vol','')
        d.text((x,y+5),f"{g['group_id']} {short} tex{t['index']:03d}\n{src.width}x{src.height} A{t['alpha_min']}..{t['alpha_max']} copies={len(g['members'])}",font=font,fill='white')
        scale=min(376/src.width,270/src.height,8)
        im=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.NEAREST)
        sheet.paste(im,(x,y+54),im)
    sheet.save(out/f'stage01-{start//16+1:02d}.png')
report={'schema':'brs-battle-sr-catalog/v1','iso_sha256':inv['iso_sha256'],
        'decoded_asset_count':sum(len(g['members']) for g in items),'unique_rgba_groups':len(items),
        'group_equivalence':'Equal dimensions and SHA256 of raw RGBA; does not equate game consumer or replacement key.',
        'groups':items,'source_decode_failures':inv['failures'],'runtime_verified':False,'all_game_complete':False}
if 'processing_summary' in previous:
    report['processing_summary']=previous['processing_summary']
    report['processing_summary_requires_refresh']=set(previous_groups)!=set(groups)
(R/'qa/battle_sr_catalog.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'decoded':report['decoded_asset_count'],'unique':len(items),'stage1_unique':len(stage1),'source_sheets':math.ceil(len(stage1)/16)}))
