"""Source-constrained structure retries; explicitly postprocessing, no new inference."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont
import local_sr as sr
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr012_structure.json';O=R/'workspace/local-sr/sr012-structure'
if Q.exists():raise SystemExit('Existing retry must not be overwritten.')
O.mkdir(exist_ok=True)
q=json.loads((R/'qa/local_sr012_inference.json').read_text('utf8'));retry=json.loads((R/'qa/local_sr012_rework.json').read_text('utf8'));parents={g:next(r for r in q['files'] if r['group_id']==g and r['model_id']=='wdn') for g in ['BM087','BM110','BM115']}
def source_rgb(src):
    a=np.asarray(src);rgb=a[:,:,:3].copy();visible=a[:,:,3]>0
    if not visible.all():
        near=distance_transform_edt(~visible,return_distances=False,return_indices=True);rgb[~visible]=rgb[near[0][~visible],near[1][~visible]]
    return Image.fromarray(rgb)
files=[];pages=[]
for gid in parents:
    row=parents[gid];src=Image.open(row['source']).convert('RGBA');parent=Image.open(row['output']).convert('RGBA');assert sr.sha(src.tobytes())==row['source_rgba_sha256'];assert sr.sha(Path(row['output']).read_bytes())==row['output_sha256']
    for weight in ([.15,.35] if gid in {'BM087','BM110'} else [.65]):
        out=Image.new('RGBA',parent.size);parts=[]
        for pi,part in enumerate(row['parts']):
            box=part['source_box'];tile=src.crop(box);sub=parent.crop(tuple(v*8 for v in box));v=np.asarray(sub,dtype=np.float32);rgb=source_rgb(tile);guide=np.asarray(rgb.resize(sub.size,Image.Resampling.BICUBIC),dtype=np.float32);a=v[:,:,3:4]/255.;low=gaussian_filter(v[:,:,:3]*a,(4.,4.,0),mode='nearest')/np.maximum(gaussian_filter(a,(4.,4.,0),mode='nearest'),1e-6);corrected=guide+weight*(v[:,:,:3]-low)
            if gid=='BM087':
                # Return to full parent only below the facade; save exact ramp for audit.
                yy=np.arange(sub.height,dtype=np.float32)/8.;mask=np.clip((76.-yy)/16.,0,1)[:,None,None];corrected=corrected*mask+v[:,:,:3]*(1-mask)
            im=Image.fromarray(np.rint(np.clip(corrected,0,255)).astype('uint8')).convert('RGBA');im.putalpha(sub.getchannel('A'));out.paste(im,(box[0]*8,box[1]*8));parts.append({'source_box':box,'residual_sigma_output_px':4.,'guide':'nearest visible RGB fill; independent bicubic8x source guide'})
        ident=f'{gid}-structure-{weight:.2f}';p=O/f'{ident}.png';out.save(p);assert out.getchannel('A').tobytes()==parent.getchannel('A').tobytes()
        files.append({'id':ident,'group_id':gid,'source':row['source'],'source_rgba_sha256':row['source_rgba_sha256'],'model':row['model'],'parent':row['output'],'parent_sha256':row['output_sha256'],'alpha_parent':row['output'],'alpha_parent_sha256':row['output_sha256'],'parts':parts,'detail_weight':weight,'facade_mask_source_y':{'full_to':60,'zero_from':76} if gid=='BM087' else None,'output':str(p),'output_sha256':sr.sha(p.read_bytes()),'output_size':list(out.size),'new_neural_passes':0,'method':'Independent per-panel bicubic source color guide plus attenuated alpha-normalized neural high-frequency residual; existing alpha unchanged','visual_review':'pending','runtime_verified':False,'release_eligible':False})
    ims=[(src,'원본 단순 확대'),(parent,'초기 WDN')]+[(Image.open(r['output']).convert('RGBA'),r['id']) for r in files if r['group_id']==gid]
    if gid=='BM115':ims.append((Image.open(next(r for r in retry['files'] if r['id']=='BM115-filtered-guided')['output']).convert('RGBA'),'앞선 filtered-guided'))
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18);box=(0,0,64,64) if gid=='BM087' else (0,0,64,32) if gid=='BM110' else (64,0,128,64);wh=((box[2]-box[0])*8,(box[3]-box[1])*8);rh=wh[1]+52;s=Image.new('RGB',(1596,rh*2),'#293440');d=ImageDraw.Draw(s)
    for i,(im,label) in enumerate(ims):
        x=i%3*532+8;y=i//3*rh+8;d.text((x,y),label,font=font,fill='white');crop=im.crop(box if i==0 else tuple(v*8 for v in box)).resize(wh,Image.Resampling.NEAREST if i==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',wh,'#72808b');bg.paste(crop,(0,0),crop);s.paste(bg,(x,y+32))
    p=R/f'outputs/sr012_structure_{gid}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr012-structure/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'local_postprocessing':True,'image_upload':False,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('5 source-structure outputs; 0 new neural passes')
