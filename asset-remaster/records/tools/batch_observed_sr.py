"""Real local SR for source textures with already observed exact game keys."""
import sys,json,time,gc
from pathlib import Path
import numpy as np,torch
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
sys.stdout.reconfigure(encoding='utf8');torch.set_num_threads(4)
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/observed-v1';O.mkdir(parents=True,exist_ok=True);Q=R/'qa/local_sr_observed_v1.json'
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']};ids=json.loads((R/'qa/local_sr_observed_pending.json').read_text('utf8'))['groups']
mr={r['name']:r for r in json.loads((R/'workspace/local-sr/models/models.json').read_text('utf8'))['records']}
report=json.loads(Q.read_text('utf8')) if Q.exists() else {'schema':'brs-observed-sr/v1','group_ids':ids,'device':torch.cuda.get_device_name(0),'local_inference':True,'image_upload':False,'files':[],'runtime_verified':False,'release_eligible':False}
assert ids==report['group_ids']
done={(r['group_id'],r['model_id']):r for r in report['files']}
def save():Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
def prefilter(src,sigma):
    a=np.asarray(src,dtype=np.float32)/255.;alpha=a[:,:,3];coverage=gaussian_filter(alpha,sigma,mode='nearest') if sigma else alpha.copy()
    pre=gaussian_filter(a[:,:,:3]*alpha[:,:,None],(sigma,sigma,0),mode='nearest') if sigma else a[:,:,:3]*alpha[:,:,None]
    rgb=pre/np.maximum(coverage[:,:,None],1e-6);vis=coverage>1e-6
    if not vis.all():
        near=distance_transform_edt(~vis,return_distances=False,return_indices=True);rgb[~vis]=rgb[near[0][~vis],near[1][~vis]]
    return Image.fromarray(np.rint(np.clip(rgb,0,1)*255).astype('uint8')),Image.fromarray(np.rint(np.clip(coverage,0,1)*255).astype('uint8'))
for mid,name in [('wdn','realesr-general-wdn-x4v3.pth'),('photo','RealESRGAN_x4plus.pth')]:
    rec=mr[name];model=sr.load_model(Path(rec['path']),rec['sha256'])
    for gid in ids:
        if (gid,mid) in done:
            row=done[(gid,mid)];assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256'];continue
        g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');assert sr.sha(src.tobytes())==g['rgba_sha256'];opaque=src.getchannel('A').getextrema()==(255,255)
        sigma=0. if opaque else (.8 if mid=='wdn' else 1.) if gid in ['BM131','BM148','BM168'] else .35
        boxes=[(0,y,256,y+32) for y in range(0,128,32)] if gid=='BM130' else [(0,0,256,128),(0,128,256,256)] if gid=='BM149' else [(0,0,src.width,src.height)]
        t=time.monotonic();out=Image.new('RGBA',(src.width*8,src.height*8));parts=[];passes=0
        for pi,box in enumerate(boxes):
            part=src.crop(box);inp,alpha=prefilter(part,sigma);tag=f'{gid}-{mid}-p{pi}';ip=O/f'{tag}-rgb-input.png';ap=O/f'{tag}-alpha-input.png';inp.save(ip);alpha.save(ap)
            native=sr.infer_rgb(model,inp);passes+=1;npth=O/f'{tag}-rgb4x.png';native.save(npth);wh=(part.width*8,part.height*8);rgb=np.asarray(native.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32)
            provenance={'source_box':list(box),'input_rgb':str(ip),'input_rgb_sha256':sr.sha(ip.read_bytes()),'input_alpha':str(ap),'input_alpha_sha256':sr.sha(ap.read_bytes()),'rgb_native':str(npth),'rgb_native_sha256':sr.sha(npth.read_bytes())}
            if opaque:av=np.full((wh[1],wh[0]),255,np.float32)
            else:
                an=sr.infer_rgb(model,alpha.convert('RGB')).convert('L');passes+=1;anp=O/f'{tag}-alpha4x.png';an.save(anp);provenance.update({'alpha_native':str(anp),'alpha_native_sha256':sr.sha(anp.read_bytes())})
                pred=np.asarray(an.resize(wh,Image.Resampling.LANCZOS),dtype=np.float32);lin=np.asarray(part.getchannel('A').resize(wh,Image.Resampling.BILINEAR),dtype=np.float32);av=.35*pred+.65*lin
                for _ in range(5):
                    av=np.clip(av*(np.asarray(part.getchannel('A')).mean()/max(av.mean(),1e-6)),0,255);av[lin==0]=0;av[lin==255]=255
            orig=np.asarray(part,dtype=np.float32);oa=orig[:,:,3:4]/255.;wa=av[:,:,None]/255.;offset=(orig[:,:,:3]*oa).sum((0,1))/oa.sum()-(rgb*wa).sum((0,1))/wa.sum();rgb=np.rint(np.clip(rgb+offset,0,255)).astype('uint8');im=Image.fromarray(rgb);im.putalpha(Image.fromarray(np.rint(av).astype('uint8')));out.paste(im,(box[0]*8,box[1]*8));provenance['weighted_mean_rgb_offset']=offset.tolist();parts.append(provenance)
        p=O/f'{gid}-{mid}-rgba8x.png';out.save(p);actual=np.asarray(out);orig=np.asarray(src);lin=np.asarray(src.getchannel('A').resize(out.size,Image.Resampling.BILINEAR));assert not np.any(actual[:,:,3][lin==0]);assert np.all(actual[:,:,3][lin==255]==255)
        reduced=np.asarray(out.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=orig[:,:,3]>=128;pred=reduced>=128;union=(gt|pred).sum()
        row={'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'model_id':mid,'model':rec,'prefilter_sigma':sigma,'parts':parts,'new_neural_passes':passes,'native_neural_scale':4,'post_scale':'Lanczos2x','precision':'float32','alpha_method':'Opaque255 exact' if opaque else '35% inferred alpha plus65% original bilinear alpha, source mean restored and empty/solid support exact; models receive premultiplied-filtered input.','output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'seconds':time.monotonic()-t,'alpha_metrics':{'mass_ratio':float(actual[:,:,3].mean()/orig[:,:,3].mean()),'threshold128_iou':float((gt&pred).sum()/union) if union else 1.,'source_ge16_reduced_below8':int(((orig[:,:,3]>=16)&(reduced<8)).sum()),'forbidden_outside_source_support':0},'visual_review':'pending','runtime_verified':False,'release_eligible':False}
        report['files'].append(row);done[(gid,mid)]=row;save();print('INFERRED',gid,mid,'passes',passes,flush=True)
    del model;gc.collect();torch.cuda.empty_cache()

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);pages=[]
for start in range(0,len(ids),3):
    batch=ids[start:start+3];sheet=Image.new('RGB',(1536,len(batch)*410+45),'#293440');d=ImageDraw.Draw(sheet)
    for j,t in enumerate(['원본 단순 확대','로컬 WDN','로컬 Photo']):d.text((j*512+10,6),t,font=font,fill='white')
    for i,gid in enumerate(batch):
        src=Image.open(groups[gid]['representative']['png']).convert('RGBA');ims=[src]+[Image.open(done[(gid,mid)]['output']).convert('RGBA') for mid in ['wdn','photo']];scale=min(488/src.width,345/src.height,8);wh=(round(src.width*scale),round(src.height*scale))
        for j,im in enumerate(ims):
            x=j*512+10;y=45+i*410;d.text((x,y),gid,font=font,fill='white');v=im.resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(v,(0,0),v);sheet.paste(bg,(x,y+30))
    p=R/f'outputs/local_sr_observed_compare_{start//3+1:02d}.png';sheet.save(p);pages.append(str(p))
report['comparison_sheets']=pages;report['new_neural_passes']=sum(r['new_neural_passes'] for r in report['files']);save();print(json.dumps({'originals':len(ids),'outputs':len(report['files']),'neural_passes':report['new_neural_passes'],'pages':pages}),flush=True)
