"""Local SR road paint, protected atlas geometry, and material retries."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import distance_transform_edt,gaussian_filter
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/stage02-rework-v2';O.mkdir(parents=True,exist_ok=True)
Q=R/'qa/local_sr_stage02_rework_v2.json'
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
mr={m['name']:m for m in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
prior=json.loads((R/'qa/local_sr_stage02_materials_v1.json').read_text('utf8'));old={r['group_id']:r for r in prior['files'] if r['denoise_strength']==0}
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-stage02-rework/v2','device':torch.cuda.get_device_name(0),'local_inference':True,'image_upload':False,'files':[],'runtime_verified':False,'release_eligible':False}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def source(gid):
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==groups[gid]['rgba_sha256'] and src.getchannel('A').getextrema()==(255,255);return src
def exists(key):
    row=next((r for r in report['files'] if r['id']==key),None)
    if row:
        assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];assert row['source_rgba_sha256']==groups[row['group_id']]['rgba_sha256']
    return row is not None
def record(key,gid,src,im,extra):
    path=O/f'{key}-8x.png';im.save(path)
    row={'id':key,'group_id':gid,'source':groups[gid]['representative']['png'],'source_rgba_sha256':groups[gid]['rgba_sha256'],'source_png_sha256':sr.sha(Path(groups[gid]['representative']['png']).read_bytes()),'output':str(path),'output_sha256':sr.sha(path.read_bytes()),'output_size':list(im.size),'visual_review':'pending','runtime_verified':False,'release_eligible':False,**extra}
    report['files'].append(row);save();print('CREATED',key,flush=True)
def neural_output(key,gid,src,input_rgb,model,model_record):
    ip=O/f'{key}-input.png';input_rgb.save(ip);t=time.monotonic();native=sr.infer_rgb(model,input_rgb);npth=O/f'{key}-native4x.png';native.save(npth)
    n=np.asarray(native,dtype=np.float32);offset=np.asarray(input_rgb,dtype=np.float32).mean((0,1))-n.mean((0,1));im=Image.fromarray(np.rint(np.clip(n+offset,0,255)).astype('uint8')).resize((src.width*8,src.height*8),Image.Resampling.LANCZOS);im.putalpha(255)
    return im,{'new_neural_passes':1,'model':model_record,'precision':'float32','native_neural_scale':4,'post_scale':'Lanczos 2x','input':str(ip),'input_sha256':sr.sha(ip.read_bytes()),'native':str(npth),'native_sha256':sr.sha(npth.read_bytes()),'mean_color_offset_rgb':offset.tolist(),'seconds':time.monotonic()-t}

# Palette gaps and line positions have been inspected against each actual original.
thresholds={'BM006':100,'BM030':100,'BM089':93,'BM090':72,'BM091':42,'BM126':56,'BM127':46}
model_record=mr['realesr-general-wdn-x4v3.pth'];model=sr.load_model(Path(model_record['path']),model_record['sha256'])
for gid,threshold in thresholds.items():
    key=gid+'-paint-aware'
    if exists(key):continue
    src=source(gid);a=np.asarray(src);paint=a[:,:,0]>=threshold
    if gid=='BM090':paint[:,:37]=False;paint[:,187:]=False
    assert paint.any() and not paint.all();near=distance_transform_edt(paint,return_distances=False,return_indices=True);rgb=a[:,:,:3].copy();rgb[paint]=rgb[near[0][paint],near[1][paint]]
    assert np.array_equal(rgb[~paint],a[:,:,:3][~paint]);mask=O/f'{key}-mask.png';Image.fromarray(paint.astype('uint8')*255).save(mask)
    im,extra=neural_output(key,gid,src,Image.fromarray(rgb),model,model_record)
    mask8=np.repeat(np.repeat(paint,8,0),8,1);out=np.asarray(im).copy();orig=np.asarray(src.resize(im.size,Image.Resampling.NEAREST));out[mask8]=orig[mask8];im=Image.fromarray(out)
    assert np.array_equal(out[mask8],orig[mask8]);extra.update({'method':'Actual local neural clean asphalt; exact source RGB and pixel-cell geometry for all protected paint. Protected lettering itself is not neural-redrawn.','paint_mask':str(mask),'paint_mask_sha256':sr.sha(mask.read_bytes()),'paint_pixels':int(paint.sum()),'paint_threshold_red':threshold,'paint_scope_x':[37,187] if gid=='BM090' else [0,src.width],'protected_rgba_exact':True,'metrics':sr.roundtrip_metrics(src,im)})
    record(key,gid,src,im,extra)

# Targeted analytic/source-bound corrections; these reuse a recorded neural parent.
for gid,rect in [('BM076',[64,0,128,64]),('BM083',[51,8,64,16])]:
    key=gid+'-geometry-preserved'
    if exists(key):continue
    src=source(gid);parent=old[gid];assert sr.sha(Path(parent['output']).read_bytes())==parent['output_sha256'];im=Image.open(parent['output']).convert('RGBA');orig=src.resize(im.size,Image.Resampling.NEAREST);a=np.asarray(src);mask=np.zeros((src.height,src.width),bool);x0,y0,x1,y1=rect;mask[y0:y1,x0:x1]=True
    if gid=='BM076':
        # Preserve only the measured white/blue flat panel, not the surrounding concrete.
        rgb=a[:,:,:3].astype(int);mask &= ((rgb[:,:,2]-rgb[:,:,0]>40)|(rgb[:,:,:3].min(2)>=248))
        # Expand one source cell to preserve the original edge antialias/gray transition.
        from scipy.ndimage import binary_dilation
        mask=binary_dilation(mask,iterations=1);mask[64:]=False;mask[:,:64]=False
    mask8=np.repeat(np.repeat(mask,8,0),8,1);arr=np.asarray(im).copy();arr[mask8]=np.asarray(orig)[mask8];im=Image.fromarray(arr)
    mp=O/f'{key}-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
    record(key,gid,src,im,{'new_neural_passes':0,'method':'Recorded WDN neural parent with exact source nearest8x pixels in the explicit protected geometric region. Not a new inference or HD vector redraw.','parent':parent['output'],'parent_sha256':parent['output_sha256'],'protected_mask':str(mp),'protected_mask_sha256':sr.sha(mp.read_bytes()),'protected_source_pixels':int(mask.sum()),'protected_rgba_exact':True,'unprotected_rgba_exact_to_parent':True})

# Retry rounded fan and dark flat panels with source-space prefiltering / model changes.
trials=[('BM082','wdn',.35),('BM114','wdn',.4),('BM114','wdn',.7),('BM082','photo',0.),('BM082','anime',0.)]
for gid,model_id,sigma in trials:
    key=f'{gid}-{model_id}-sigma{sigma}'
    if exists(key):continue
    if model_id!='wdn':
        del model;gc.collect();torch.cuda.empty_cache()
        if model_id=='photo':model_record=mr['RealESRGAN_x4plus.pth']
        else:model_record={'path':'P:/AI/Codex/projects/fate-extra-psp-korean/work/hd-texture-pack/codex-hd-v1/references/realesrgan/RealESRGAN_x4plus_anime_6B.pth','sha256':'f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da','name':'RealESRGAN_x4plus_anime_6B.pth'}
        model=sr.load_model(Path(model_record['path']),model_record['sha256'])
    src=source(gid);rgb=np.asarray(src.convert('RGB'),dtype=np.float32)
    if sigma:rgb=gaussian_filter(rgb,(sigma,sigma,0),mode='reflect')
    inp=Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8'));im,extra=neural_output(key,gid,src,inp,model,model_record)
    extra.update({'model_id':model_id,'prefilter_sigma':sigma,'method':'Source-space RGB prefilter then actual local model inference, source input RGB mean restored.','metrics':sr.roundtrip_metrics(src,im)})
    record(key,gid,src,im,extra)

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for label,ids in [('road1',['BM006','BM030','BM089','BM090']),('road2',['BM091','BM126','BM127']),('geometry',['BM076','BM083']),('fan',['BM082']),('panel',['BM114'])]:
    rows=[]
    for gid in ids:
        entries=[r for r in report['files'] if r['group_id']==gid]
        if label in ['fan','panel']:rows += [(gid,r) for r in entries]
        else:rows.append((gid,entries[0]))
    sheet=Image.new('RGB',(1536,370*len(rows)+40),'#293440');d=ImageDraw.Draw(sheet)
    for j,t in enumerate(['원본 단순 확대','이전 로컬 결과 / 보호 마스크','재작업 후보']):d.text((j*512+10,5),t,font=font,fill='white')
    for i,(gid,row) in enumerate(rows):
        src=source(gid);middle=Image.open(old[gid]['output']) if gid in old else Image.open(row['paint_mask']);ims=[src,middle,Image.open(row['output'])]
        scale=min(490/src.width,305/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
        for j,im in enumerate(ims):
            x=j*512+10;y=i*370+43;d.text((x,y),row['id'] if j==2 else gid,font=font,fill='white');sheet.paste(im.convert('RGB').resize(wh,Image.Resampling.NEAREST if j==0 or (j==1 and gid not in old) else Image.Resampling.LANCZOS),(x,y+30))
    p=R/f'outputs/local_sr005_{label}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save()
print(json.dumps({'outputs':len(report['files']),'new_neural_passes':report['new_neural_passes'],'pages':pages}),flush=True)
