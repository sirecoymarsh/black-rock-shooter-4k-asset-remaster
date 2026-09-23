from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(r'P:\AI\Codex\projects\black-rock-shooter-hd-ui-fonts');G=Path(r'P:\AI\Codex\generated_images\01a0c802-c7cf-7f71-a268-2f12b1fd7bd3');O=R/'outputs/field-foliage008';Q=R/'qa/field_foliage008_gpt_raw.json';assert not Q.exists()
def read(p):return json.loads(Path(p).read_text('utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files={'FM0301':'exec-154d89a4-6be5-4357-aebb-22d86b5ebc10.png','FM0312':'exec-b286ba89-57c3-4442-aee9-b961afd13116.png','FM0320':'exec-52760b87-d47f-41ee-ada3-f2a80c56feab.png'}
local=read(R/'qa/field_foliage006_local.json');font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
report={'schema':'brs-field-foliage008-GPT-raw/v1','tool':'built-in image_gen','actual_external_calls':3,'model_id':'not exposed','files':[],'pages':[],'runtime_verified':False,'release_eligible':False}
for gid,name in files.items():
    folder=R/'workspace/gpt-trials'/(gid+'-foliage008-v1');pr=folder/'provenance.json';p=read(pr);dest=folder/'generated-raw.png';assert not dest.exists();shutil.copy2(G/name,dest)
    s=Image.open(p['source']).convert('RGBA');im=Image.open(dest).convert('RGBA');a=np.asarray(im);sa=np.asarray(s)[:,:,3];alpha=a[:,:,3];small=np.asarray(im.getchannel('A').resize(s.size,Image.Resampling.BOX));sm=sa>=128;om=small>=128
    rgb=a[:,:,:3].astype(int);chroma={}
    for t in [1,64,128,240]:
        opaque=alpha>=t;green=opaque&(rgb[:,:,1]-rgb[:,:,0]>50)&(rgb[:,:,1]-rgb[:,:,2]>30);cyan=opaque&(rgb[:,:,1]-rgb[:,:,0]>70)&(rgb[:,:,2]-rgb[:,:,0]>70);chroma[str(t)]={'green_pixels':int(green.sum()),'cyan_pixels':int(cyan.sum())}
    stats={'source_alpha_mean':float(sa.mean()),'raw_alpha_mean':float(alpha.mean()),'mass_ratio':float(alpha.mean()/sa.mean()),'source_scale_IoU_at128':float((sm&om).sum()/(sm|om).sum()),'source_scale_alpha_mask_disagreements':int((sm!=om).sum()),'raw_alpha_extrema':[int(alpha.min()),int(alpha.max())],'raw_alpha_unique_count':len(np.unique(alpha)),'edge_chroma_by_alpha_threshold':chroma}
    p.update(status='raw_generated_pending_review',generated_store_path=str(G/name),raw_generated_image=str(dest),raw_sha256=sha(dest),raw_generated_image_preserved=True,raw_size=list(im.size),raw_alpha_diagnostics=stats)
    pr.write_text(json.dumps(p,ensure_ascii=False,indent=2),'utf8');report['files'].append(p)
    parent=next(q for q in local['files'] if q['id']==gid+'-photo')
    boxes=[('whole',None),('detail',(12,8,44,40) if gid!='FM0312' else (12,12,44,44))]
    if gid=='FM0301':boxes += [('center',(18,23,48,53)),('top',(10,0,56,26))]
    for tag,box in boxes:
        page=Image.new('RGB',(1050,810),'#25313c');d=ImageDraw.Draw(page)
        for row,(matte,mlabel) in enumerate([('#18222c','어두운 배경'),('#dedede','밝은 배경')]):
            for col,(path,title) in enumerate([(p['source'],'원본 · 단순 확대'),(parent['output'],'로컬 Photo'),(str(dest),'GPT 재작화 · 원시 결과')]):
                pic=Image.open(path).convert('RGBA')
                if box:pic=pic.crop(tuple(round(t*(pic.width/s.width if i%2==0 else pic.height/s.height)) for i,t in enumerate(box)))
                scale=min(320/pic.width,340/pic.height);pic=pic.resize((round(pic.width*scale),round(pic.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);bg=Image.new('RGBA',pic.size,matte);bg.alpha_composite(pic);page.paste(bg.convert('RGB'),(col*350+(350-bg.width)//2,row*405+58+(340-bg.height)//2));d.text((col*350+8,row*405+8),gid+' '+title,font=font,fill='white');d.text((col*350+8,row*405+30),mlabel,font=font,fill='#c7d1da')
        pp=O/(gid+'-GPT-raw-'+tag+'.png');page.save(pp);report['pages'].append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps([{'group':p['group_id'],'size':p['raw_size'],'diagnostics':p['raw_alpha_diagnostics']} for p in report['files']]))
