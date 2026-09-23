"""Avoid Pillow premultiplied-RGBA rounding for constant-alpha checker cells."""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/checker_fidelity_v1.json';q=json.loads(Q.read_text('utf8'));backup=R/'qa/backups/checker-before-alpha-rounding';backup.mkdir(parents=True,exist_ok=False);shutil.copyfile(Q,backup/Q.name)
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for row in q['files']:
    if row['group_id'] not in {'BM200','BM269'}:continue
    src=Image.open(row['source']).convert('RGBA');out=Image.new('RGBA',(src.width*8,src.height*8))
    for cell in row['cells']:
        part=src.crop(tuple(cell['source_box']));tile=part.convert('RGB').resize((part.width*8,part.height*8),Image.Resampling.BILINEAR);tile.putalpha(part.getchannel('A').resize(tile.size,Image.Resampling.NEAREST));out.paste(tile,tuple(cell['output_box'][:2]))
    p=Path(row['output']);shutil.copyfile(p,backup/p.name);out.save(p);row['output_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();row['shading_resample']='Independent RGB channels bilinear; alpha nearest. Avoids constant-alpha premultiplication rounding.'
    s=Image.new('RGB',(740,670),'#293440');d=ImageDraw.Draw(s)
    for i,color in enumerate(['#111111','#eeeeee']):
        for j,im in enumerate([src,out]):
            x=j*370+10;y=i*335+8;d.text((x,y),'원본 단순 확대' if j==0 else row['id'],font=font,fill='white');im=im.resize(out.size,Image.Resampling.NEAREST);bg=Image.new('RGB',im.size,color);bg.paste(im,(0,0),im);s.paste(bg,(x,y+35))
    s.save(R/f"outputs/checker_fidelity_{row['group_id']}.png")
q['shading_correction']='Verifier found minor RGBA premultiplication rounding. Only two geometry outputs were regenerated using independent RGB and exact alpha; no neural inference repeated.'
Q.write_text(json.dumps(q,ensure_ascii=False,indent=2),'utf8');print('2 geometry outputs regenerated; no neural inference')
