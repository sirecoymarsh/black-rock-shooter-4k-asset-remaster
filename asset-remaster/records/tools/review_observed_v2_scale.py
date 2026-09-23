import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];q=json.loads((R/'qa/local_sr_observed_rework_v2.json').read_text('utf8'));byid={r['id']:r for r in q['files']};old=json.loads((R/'qa/local_sr_observed_v1.json').read_text('utf8'));parents={r['group_id']:r for r in old['files'] if r['model_id']=='wdn'}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);choices={gid:('guided055' if gid in ['BM156','BM163'] else 'prefilter075-guided065') for gid in q['group_ids']}
for start in range(0,len(choices),4):
    batch=list(choices.items())[start:start+4];s=Image.new('RGB',(1450,330*len(batch)+40),'#293440');d=ImageDraw.Draw(s)
    for i,(gid,tag) in enumerate(batch):
        row=byid[gid+'-'+tag];src=Image.open(row['source']).convert('RGBA');ims=[src,Image.open(parents[gid]['output']).convert('RGBA'),Image.open(row['output']).convert('RGBA')]
        for j,im in enumerate(ims):
            x=j*480+10;y=i*330+40;d.text((x,y),gid+' '+['원본','이전 로컬','보정 후보'][j],font=font,fill='white')
            for k,factor in enumerate([1,2]):
                wh=(src.width*factor,src.height*factor)
                if wh[0]>300:wh=(300,round(300*src.height/src.width))
                if wh[1]>260:wh=(round(260*src.width/src.height),260)
                v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#eeeeee' if k else '#111111');bg.paste(v,(0,0),v);s.paste(bg,(x+(src.width+14 if src.width<=128 else 0)*k,y+30+(110 if src.width>128 else 0)*k))
    s.save(R/f'outputs/local_sr_observed_rework_scale_{start//4+1:02d}.png')
