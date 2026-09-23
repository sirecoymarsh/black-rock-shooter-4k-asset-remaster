import json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts');O=R/'qa/battle-source-catalog';O.mkdir(exist_ok=True)
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups=cat['groups'];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
pending=[g for g in groups if any('stg01_' in k for k in g['members']) and not g.get('candidate')]
stage2=[g for g in groups if any('stg02_' in k for k in g['members']) and not g.get('local_sr_attempted')]
for name,items,cols,rows,cw,ch in [('stage01-pending',pending,2,2,600,600),('stage02',stage2,4,3,400,360)]:
    for start in range(0,len(items),cols*rows):
        batch=items[start:start+cols*rows];sheet=Image.new('RGB',(cols*cw,rows*ch),'#293440');d=ImageDraw.Draw(sheet)
        for n,g in enumerate(batch):
            src=Image.open(g['representative']['png']).convert('RGBA');assert hashlib.sha256(src.tobytes()).hexdigest()==g['rgba_sha256'];x=(n%cols)*cw+8;y=(n//cols)*ch
            d.text((x,y+6),f"{g['group_id']} {src.width}x{src.height} A{src.getchannel('A').getextrema()}\n{g['representative']['id'].split('::')[-1]}",font=font,fill='white')
            scale=min((cw-16)/src.width,(ch-65)/src.height,12);v=src.resize((round(src.width*scale),round(src.height*scale)),Image.Resampling.NEAREST);bg=Image.new('RGB',v.size,'#89999f');bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+62))
        sheet.save(O/f'{name}-{start//(cols*rows)+1:02d}.png')
print(json.dumps({'stage01_pending':[g['group_id'] for g in pending],'stage02_pending':[{'id':g['group_id'],'size':[g['width'],g['height']],'alpha':[g['representative']['alpha_min'],g['representative']['alpha_max']]} for g in stage2]}))
