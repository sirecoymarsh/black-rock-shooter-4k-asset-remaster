"""Source-constrained geometric repair and postprocessing of actual neural results."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
from scipy.ndimage import label,gaussian_filter
from PIL import Image,ImageDraw,ImageFont
sys.stdout.reconfigure(encoding='utf8')
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/linear-foliage-v4';O.mkdir(parents=True,exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
cat=json.loads((R/'qa/battle_sr_catalog.json').read_text('utf8'));groups={g['group_id']:g for g in cat['groups']}
old=json.loads((R/'qa/local_sr_stage01_alpha_v1.json').read_text('utf8'));old={r['group_id']:r for r in old['files'] if r['alpha_model_id']=='general-wdn'}
v3=json.loads((R/'qa/local_sr_soft_alpha_v3.json').read_text('utf8'));rows=[]

gid='BM039';g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');a=np.asarray(src);labels,n=label(a[:,:,3]>=128)
scale=32;mask=Image.new('L',(src.width*scale,src.height*scale));d=ImageDraw.Draw(mask);fits=[];pending=[]
for component in range(1,n+1):
    ys,xs=np.where(labels==component)
    if len(xs)<8:raise ValueError('Unexpected isolated source marking')
    data=[(y,int(np.where(labels[y]==component)[0].min()),int(np.where(labels[y]==component)[0].max())) for y in sorted(set(ys))]
    yl=ys.min();yh=ys.max()+1
    coeff=[];residuals=[]
    for side in [1,2]:
        samples=np.array([(y+.5,xl if side==1 else xr+1) for y,xl,xr in data if (xl>0 if side==1 else xr<src.width-1)],dtype=float)
        if len(samples)<3:
            coeff.append(None);residuals.append(None);continue
        fit=np.polyfit(samples[:,0],samples[:,1],1);coeff.append(fit)
        residuals.append(float(np.abs(np.polyval(fit,samples[:,0])-samples[:,1]).max()))
    pending.append((component,len(xs),int(yl),int(yh),coeff,residuals))
widths=[np.polyval(c[1],16)-np.polyval(c[0],16) for _,_,_,_,c,_ in pending if all(k is not None for k in c)]
assert widths
reference_width=float(np.median(widths))
for component,count,yl,yh,coeff,residuals in pending:
    inferred=[]
    for side in [0,1]:
        if coeff[side] is None:
            if coeff[1-side] is None:raise ValueError('Both stripe edges are unobserved')
            coeff[side]=coeff[1-side].copy();coeff[side][1]+=reference_width*(1 if side==1 else -1);inferred.append(side)
    polygon=[(np.polyval(coeff[0],yl)*scale,yl*scale),(np.polyval(coeff[1],yl)*scale,yl*scale),(np.polyval(coeff[1],yh)*scale,yh*scale),(np.polyval(coeff[0],yh)*scale,yh*scale)]
    d.polygon(polygon,fill=255)
    fits.append({'component':component,'source_pixels':count,'y_range':[yl,yh],'left_x_of_y':coeff[0].tolist(),'right_x_of_y':coeff[1].tolist(),'edge_max_source_pixel_residual':residuals,'clipped_edge_inferred_from_visible_edge_and_other_bands':inferred,'reference_band_width':reference_width})
mask=mask.resize((src.width*8,src.height*8),Image.Resampling.LANCZOS)
raw=Image.open(old[gid]['output']).convert('RGBA');av=np.asarray(mask,dtype=float)
mean_target=a[:,:,3].mean();av*=mean_target/av.mean();av=np.clip(av,0,255)
raw.putalpha(Image.fromarray(np.rint(av).astype('uint8')));p=O/'BM039-linear-mask-rgb-neural-8x.png';raw.save(p)
back=np.asarray(raw.getchannel('A').resize(src.size,Image.Resampling.BOX));binary=back>=128;source_binary=a[:,:,3]>=128
rows.append({'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'parent_neural':old[gid]['output'],'parent_neural_sha256':old[gid]['output_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'fits':fits,'method':'Source connected stripes; fit separate straight left/right edges from unclipped observations, supersample geometry 32x and downsample to 8x; reuse actual local-neural RGB.','alpha_mass_ratio':float(np.asarray(raw.getchannel('A')).mean()/mean_target),'source_scale_mask_iou':float((binary&source_binary).sum()/(binary|source_binary).sum()),'new_neural_inference':False,'postprocessing_only':True,'visual_review':'pending','runtime_verified':False,'release_eligible':False})

gid='BM057';g=groups[gid];src=Image.open(g['representative']['png']).convert('RGBA');parent=next(r for r in v3['files'] if r['group_id']==gid and r['model_id']=='photo' and r['prefilter_sigma']==.4)
im=Image.open(parent['output']).convert('RGBA');v=np.asarray(im,dtype=float);alpha=v[:,:,3:4]/255.
native=np.asarray(src,dtype=float);na=native[:,:,3:4]/255.
# Work only inside the foliage atlas cell. Preserve bark and all alpha byte-for-byte.
leaf_width=48*8;leaf=v[:,:leaf_width,:3];w=alpha[:,:leaf_width];blur=gaussian_filter(leaf*w,(8.,8.,0))/np.maximum(gaussian_filter(w,(8.,8.,0)),1e-6)
for weight in [.35,.6]:
    adjusted=np.clip(blur+weight*(leaf-blur),0,255)
    result=v.copy();result[:,:leaf_width,:3]=adjusted;out=Image.fromarray(np.rint(result).astype('uint8'),'RGBA')
    assert np.array_equal(np.asarray(out)[:,leaf_width:],np.asarray(im)[:,leaf_width:])
    assert out.getchannel('A').tobytes()==im.getchannel('A').tobytes()
    p=O/f'BM057-photo-detail{weight}-8x.png';out.save(p)
    rows.append({'group_id':gid,'source':g['representative']['png'],'source_rgba_sha256':g['rgba_sha256'],'parent_neural':parent['output'],'parent_neural_sha256':parent['output_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'method':'Alpha-weighted local color base plus reduced neural high-frequency RGB detail in foliage x<48; bark and entire alpha exact to parent.','detail_weight':weight,'new_neural_inference':False,'postprocessing_only':True,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype(r'C:\Windows\Fonts\malgun.ttf',18)
for gid in ['BM039','BM057']:
    src=Image.open(groups[gid]['representative']['png']).convert('RGBA');rr=[r for r in rows if r['group_id']==gid]
    inputs=[src,Image.open(old[gid]['output']).convert('RGBA')]+[Image.open(r['output']).convert('RGBA') for r in rr]
    names=['원본 단순 확대','이전 · 미채택']+(['직선 위치 측정·복원'] if gid=='BM039' else ['잎 질감 강도 35%','잎 질감 강도 60%'])
    wh=(512,256) if gid=='BM039' else (512,512);sheet=Image.new('RGB',((wh[0]+16)*len(inputs),wh[1]+60),'#293440');d=ImageDraw.Draw(sheet)
    for i,(im,name) in enumerate(zip(inputs,names)):
        x=i*(wh[0]+16)+8;d.text((x,8),gid+' '+name,font=font,fill='white')
        im=im.resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#51585e');bg.paste(im,(0,0),im);sheet.paste(bg,(x,42))
    sheet.save(R/f'outputs/local_sr_{gid}_rework_v4.png')
(R/'qa/local_sr_linear_foliage_v4.json').write_text(json.dumps({'schema':'brs-linear-foliage-rework/v4','files':rows,'new_originals':0,'new_neural_inference_passes':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8')
print(json.dumps({'outputs':len(rows),'linear_mask_iou':rows[0]['source_scale_mask_iou'],'stripe_fits':fits}))
