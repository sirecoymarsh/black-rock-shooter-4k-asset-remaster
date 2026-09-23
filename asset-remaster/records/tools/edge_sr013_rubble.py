"""Narrow source-derived edge transition without changing its half-coverage contour."""
import json,hashlib
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];Q=R/'qa/local_sr013_rubble_edge.json'
if Q.exists():raise SystemExit('Existing edge revision.')
q=json.loads((R/'qa/local_sr013_rubble_tone.json').read_text('utf8'));r=next(r for r in q['files'] if r['strength']==.8);src=Image.open(r['source']).convert('RGBA');par=Image.open(r['output']).convert('RGBA');ref=np.asarray(par.getchannel('A'),dtype=float);original=np.asarray(src.getchannel('A'));assert np.array_equal(ref,np.asarray(src.getchannel('A').resize(par.size,Image.Resampling.BILINEAR)))
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha(Path(r['output']).read_bytes())==r['output_sha256'];files=[]
for strength in [2.,4.]:
    av=np.rint(np.clip((ref-127.5)*strength+127.5,0,255)).astype('uint8');im=par.copy();im.putalpha(Image.fromarray(av));p=Path(r['output']).parent/f'BM115-tone080-edge{strength:.0f}.png';im.save(p);down=np.asarray(im.getchannel('A').resize(src.size,Image.Resampling.LANCZOS));gt=original>=128;pred=down>=128;cc=cv2.connectedComponents((av>=128).astype('uint8'),8)[0]-1;metric={'source_ge16_reduced_below8':int(((original>=16)&(down<8)).sum()),'source_threshold128_iou':float((gt&pred).sum()/(gt|pred).sum()),'mass_ratio':float(av.mean()/original.mean()),'source_bilinear_half_coverage_exact':bool(np.array_equal(av>=128,ref>=128)),'components_alpha128':cc,'outside_source_bilinear_support':int((av[ref==0]>0).sum()),'opaque_support_preserved':bool(np.all(av[ref==255]==255))}
    assert np.array_equal(np.asarray(im)[:,:,:3],np.asarray(par)[:,:,:3]);files.append({'id':f'BM115-tone080-edge{strength:.0f}','group_id':'BM115','source':r['source'],'source_rgba_sha256':r['source_rgba_sha256'],'parent':r['output'],'parent_sha256':r['output_sha256'],'output':str(p),'output_sha256':sha(p.read_bytes()),'output_size':list(im.size),'method':'Coverage contrast on source bilinear alpha only; half-coverage contour and 0/255 support unchanged; registered repaint RGB byte-exact','alpha_strength':strength,'alpha_formula':'round(clip((source_bilinear_alpha-127.5)*strength+127.5,0,255))','alpha_metrics':metric,'new_neural_passes':0,'new_generative_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17);pages=[]
for label,box in [('connector',(126,15,162,45)),('middle',(64,32,128,64)),('whole',(0,0,256,64))]:
    scale=min(8,510/(box[2]-box[0]));wh=(round((box[2]-box[0])*scale),round((box[3]-box[1])*scale));cw=max(350,wh[0]+20);rh=wh[1]+58;s=Image.new('RGB',(cw*4,rh*2),'#293440');d=ImageDraw.Draw(s);ims=[(src,'원본'),(par,'원본 bilinear 알파')]+[(Image.open(f['output']).convert('RGBA'),f'경계 대비 {f["alpha_strength"]}') for f in files]
    for i,bgc in enumerate(['#111111','#eeeeee']):
        for j,(pic,title) in enumerate(ims):
            x=j*cw+8;y=i*rh+8;d.text((x,y),title,font=font,fill='white');pic=pic.crop(box if j==0 else tuple(z*8 for z in box)).resize(wh,Image.Resampling.NEAREST if j==0 else Image.Resampling.LANCZOS);bg=Image.new('RGB',pic.size,bgc);bg.paste(pic,(0,0),pic);s.paste(bg,(x,y+34))
    p=R/f'outputs/sr013_rubble_edge_{label}.png';s.save(p);pages.append(str(p))
Q.write_text(json.dumps({'schema':'brs-sr013-rubble-edge/v1','files':files,'comparison_sheets':pages,'new_neural_passes':0,'new_generative_calls':0,'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({f['id']:f['alpha_metrics'] for f in files}))
