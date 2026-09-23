"""Build source/model matte comparisons; selections remain provisional until read."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text('utf8'))
q=read('qa/local_sr011_inference.json');retry=read('qa/local_sr011_rework.json')
wdn={204,205,206,219,224,235,248,249,252,257,261,263,265,276,280,283}
choices={gid:('wdn' if int(gid[2:]) in wdn else 'photo') for gid in q['group_ids']}
selected={gid:next(r for r in q['files'] if r['group_id']==gid and r['model_id']==mid) for gid,mid in choices.items()}
for gid in ['BM262','BM264','BM277']:selected[gid]=next(r for r in retry['files'] if r['id']==gid+'-filtered-guided')
assert len(selected)==42
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
pages=[];detail=[];directory=R/'outputs/sr011-mattes';directory.mkdir(exist_ok=True)
items=sorted(selected.items())
for start in range(0,len(items),3):
    batch=items[start:start+3];s=Image.new('RGB',(1320,len(batch)*330+42),'#293440');d=ImageDraw.Draw(s)
    for j,label in enumerate(['원본 · 어두운 배경','후보 · 어두운 배경','원본 · 밝은 배경','후보 · 밝은 배경']):d.text((j*330+10,8),label,font=font,fill='white')
    for i,(gid,row) in enumerate(batch):
        src=Image.open(row['source']).convert('RGBA');out=Image.open(row['output']).convert('RGBA');scale=min(310/src.width,265/src.height,4);wh=(round(src.width*scale),round(src.height*scale))
        for j,im in enumerate([src,out,src,out]):
            x=j*330+10;y=i*330+45;d.text((x,y),f'{gid} 표시 {scale:.2f}배',font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j%2==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#111111' if j<2 else '#eeeeee');bg.paste(v,(0,0),v);s.paste(bg,(x,y+30))
    p=directory/f'matte-{start//3+1:02d}.png';s.save(p);pages.append(str(p))
for gid in ['BM214','BM221','BM224','BM225','BM230','BM234','BM258','BM260']:
    rows=[next(r for r in q['files'] if r['group_id']==gid and r['model_id']==mid) for mid in ['wdn','photo']]
    src=Image.open(rows[0]['source']).convert('RGBA');box=(0,0,min(64,src.width),min(64,src.height))
    if gid=='BM224':box=(src.width//2-32,src.height//2-32,src.width//2+32,src.height//2+32)
    ims=[src.crop(box)]+[Image.open(r['output']).convert('RGBA').crop(tuple(v*8 for v in box)) for r in rows]
    wh=((box[2]-box[0])*8,(box[3]-box[1])*8);s=Image.new('RGB',(1590,1140),'#293440');d=ImageDraw.Draw(s)
    for i,bgcolor in enumerate(['#111111','#eeeeee']):
        for j,im in enumerate(ims):
            x=j*530+8;y=i*570+8;d.text((x,y),f'{gid} {box} '+['원본 8배','WDN','Photo'][j],font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,bgcolor);bg.paste(v,(0,0),v);s.paste(bg,(x,y+30))
    p=directory/f'{gid}-detail.png';s.save(p);detail.append(str(p))
record={'schema':'brs-sr011-proposed-review/v1','selected':{g:{'output':r['output'],'output_sha256':r['output_sha256'],'model_id':r.get('model_id'),'id':r.get('id')} for g,r in selected.items()},'holds':[],'matte_pages':pages,'detail_pages':detail,'review_state':'pending final matte and detail inspection','runtime_verified':False}
(R/'qa/local_sr011_proposed_review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'choices':len(selected),'matte_pages':len(pages),'detail_pages':len(detail)}))
