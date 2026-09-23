import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
R=Path('P:/AI/Codex/projects/black-rock-shooter-hd-ui-fonts');O=R/'workspace/local-sr/linear-foliage-v4'
def read(n):return json.loads((R/n).read_text('utf8'))
cat=read('qa/battle_sr_catalog.json');g={q['group_id']:q for q in cat['groups']}
v3=read('qa/local_sr_soft_alpha_v3.json');v4=read('qa/local_sr_linear_foliage_v4.json')
old=read('qa/local_sr_stage01_alpha_v1.json');old={q['group_id']:q for q in old['files'] if q['alpha_model_id']=='general-wdn'}
cloud=next(q for q in v3['files'] if q['group_id']=='BM027' and q['model_id']=='photo' and q['prefilter_sigma']==1.)
tree=next(q for q in v4['files'] if q['group_id']=='BM057' and q['detail_weight']==.6)
im=Image.open(tree['output']).convert('RGBA');bark=Image.open(old['BM057']['output']).convert('RGBA');im.paste(bark.crop((384,0,512,512)),(384,0));dest=O/'BM057-selected-foliage-photo-bark-wdn-8x.png';im.save(dest)
assert np.array_equal(np.asarray(im)[:,384:],np.asarray(bark)[:,384:])
proposal={'BM027':cloud['output'],'BM039':v4['files'][0]['output'],'BM057':str(dest)}
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
sheet=Image.new('RGB',(1584,1300),'#293440');d=ImageDraw.Draw(sheet)
for row,gid in enumerate(['BM027','BM057']):
    src=Image.open(g[gid]['representative']['png']).convert('RGBA');new=Image.open(proposal[gid]).convert('RGBA');wh=(512,256 if gid=='BM027' else 512);y=0 if row==0 else 605
    for col,(im,bgcolor,title) in enumerate([(src,'#a7b4bc','원본'),(new,'#171b23','후보 · 어두운 배경'),(new,'#eeeeee','후보 · 밝은 배경')]):
        x=col*528+8;d.text((x,y+8),gid+' '+title,font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,bgcolor);bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+40))
        small=im.resize((src.width*2,src.height*2),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);mat=Image.new('RGB',small.size,bgcolor);mat.paste(small,(0,0),small)
        d.text((x,y+wh[1]+46),'2배 표시',font=font,fill='white');sheet.paste(mat,(x+112,y+wh[1]+42))
sheet.save(R/'outputs/local_sr_soft_matte_review_v4.png')
out={'proposed':proposal,'tree_parent':tree,'tree_bark_parent':old['BM057']['output'],'tree_bark_parent_sha256':old['BM057']['output_sha256'],'tree_composite_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'visual_review':'pending'}
(R/'qa/local_sr_soft_review_proposal_v4.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'proposed':proposal}))
