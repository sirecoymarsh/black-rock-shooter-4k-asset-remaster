"""Retry asphalt hallucination and source-guided fan center correction."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage02-refine-v3';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr_stage02_refine_v3.json'
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={r['group_id']:r for r in cat['groups']};previous=json.loads((R/'qa/local_sr_stage02_rework_v2.json').read_text('utf8'));roads={r['group_id']:r for r in previous['files'] if 'paint_mask' in r}
mr={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-stage02-refine/v3','device':torch.cuda.get_device_name(0),'files':[],'runtime_verified':False,'release_eligible':False,'image_upload':False}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def exists(key):
    row=next((r for r in report['files'] if r['id']==key),None)
    if row:assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256']
    return row is not None
for model_id,name,sigma in [('wdn','realesr-general-wdn-x4v3.pth',.65),('photo','RealESRGAN_x4plus.pth',.4)]:
    m=mr[name];model=sr.load_model(Path(m['path']),m['sha256'])
    for gid in ['BM030','BM089']:
        key=f'{gid}-{model_id}-smooth{sigma}'
        if exists(key):continue
        row=roads[gid];src=Image.open(row['source']).convert('RGBA');assert sr.sha(src.tobytes())==row['source_rgba_sha256'];assert sr.sha(Path(row['input']).read_bytes())==row['input_sha256']
        rgb=np.asarray(Image.open(row['input']).convert('RGB'),dtype=np.float32);rgb=np.rint(gaussian_filter(rgb,(sigma,sigma,0),mode='reflect')).astype('uint8');inp=Image.fromarray(rgb);ip=O/f'{key}-input.png';inp.save(ip)
        t=time.monotonic();native=sr.infer_rgb(model,inp);npth=O/f'{key}-native4x.png';native.save(npth);n=np.asarray(native,dtype=np.float32);offset=rgb.mean((0,1))-n.mean((0,1));im=Image.fromarray(np.rint(np.clip(n+offset,0,255)).astype('uint8')).resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);im.putalpha(255)
        mask=np.asarray(Image.open(row['paint_mask']).resize(im.size,Image.Resampling.NEAREST))>0;arr=np.asarray(im).copy();original=np.asarray(src.resize(im.size,Image.Resampling.NEAREST));arr[mask]=original[mask];im=Image.fromarray(arr);op=O/f'{key}-8x.png';im.save(op)
        report['files'].append({'id':key,'group_id':gid,'source':row['source'],'source_rgba_sha256':row['source_rgba_sha256'],'source_report':'qa/local_sr_stage02_rework_v2.json','paint_mask':row['paint_mask'],'paint_mask_sha256':row['paint_mask_sha256'],'protected_rgba_exact':True,'model':m,'model_id':model_id,'prefilter_sigma':sigma,'new_neural_passes':1,'native_neural_scale':4,'post_scale':'Lanczos2x; protected paint exact original8x','input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'output':str(op),'output_sha256':sr.sha(op.read_bytes()),'output_size':list(im.size),'mean_color_offset_rgb':offset.tolist(),'seconds':time.monotonic()-t,'visual_review':'pending','runtime_verified':False,'release_eligible':False});save();print('CREATED',key,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

gid='BM082';key=gid+'-source-center'
if not exists(key):
    g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256']
    old=json.loads((R/'qa/local_sr_stage02_materials_v1.json').read_text('utf8'));parent=next(r for r in old['files'] if r['group_id']==gid and r['denoise_strength']==0)
    assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];im=Image.open(parent['output']).convert('RGBA');a=np.asarray(im,dtype=np.float32);orig=np.asarray(src.resize(im.size,Image.Resampling.LANCZOS),dtype=np.float32)
    yy,xx=np.mgrid[:im.height,:im.width];dist=np.sqrt(((xx+.5)/8-32)**2+((yy+.5)/8-32)**2);weight=np.clip((4.75-dist)/.75,0,1)
    arr=np.rint(a*(1-weight[:,:,None])+orig*weight[:,:,None]).astype('uint8');out=Image.fromarray(arr);op=O/f'{key}-8x.png';out.save(op)
    mp=O/f'{key}-weight.png';Image.fromarray(np.rint(weight*255).astype('uint8')).save(mp)
    assert np.array_equal(arr[weight==0],np.asarray(im)[weight==0]);assert np.array_equal(arr[weight==1],orig.astype('uint8')[weight==1])
    report['files'].append({'id':key,'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'parent':parent['output'],'parent_sha256':parent['output_sha256'],'new_neural_passes':0,'method':'Measured source center (32,32): source Lanczos RGB within radius4, .75 source-pixel feather to original WDN beyond radius4.75. Source-guided interpolation, not new neural inference or recovered geometry.','source_center':[32,32],'core_radius':4,'outer_radius':4.75,'blend_weight':str(mp),'blend_weight_sha256':sr.sha(mp.read_bytes()),'unprotected_rgba_exact_to_parent':True,'output':str(op),'output_sha256':sr.sha(op.read_bytes()),'output_size':list(out.size),'visual_review':'pending','runtime_verified':False,'release_eligible':False});save();print('CREATED',key,flush=True)

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for gid in ['BM030','BM089','BM082']:
    rows=[r for r in report['files'] if r['group_id']==gid];s=Image.new('RGB',(1536,370*len(rows)+45),'#293440');d=ImageDraw.Draw(s)
    for j,t in enumerate(['원본 단순 확대','이전 후보','재작업 후보']):d.text((j*512+10,5),t,font=font,fill='white')
    for i,row in enumerate(rows):
        src=Image.open(row['source']);prev=row['parent'] if gid=='BM082' else roads[gid]['output'];ims=[src,Image.open(prev),Image.open(row['output'])];scale=min(490/src.width,305/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
        for j,im in enumerate(ims):
            x=j*512+10;y=45+i*370;d.text((x,y),row['id'] if j==2 else gid,font=font,fill='white');s.paste(im.convert('RGB').resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS),(x,y+30))
    p=R/f'outputs/local_sr005_refine_{gid}.png';s.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save()
print(json.dumps({'new_neural_passes':report['new_neural_passes'],'pages':pages}),flush=True)
