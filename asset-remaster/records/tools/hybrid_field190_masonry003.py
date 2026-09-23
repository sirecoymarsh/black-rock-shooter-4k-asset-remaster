"""Reuse already-generated masonry grain inside fixed geometry, retaining glass."""
import hashlib,json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry003';O.mkdir(exist_ok=False);V=R/'outputs/field-geometry003';V.mkdir(exist_ok=False);Q=R/'qa/field_geometry003_hybrid.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
v=next(v for v in json.loads((R/'qa/field_geometry002_bevels_v4.json').read_text('utf8'))['files'] if v['group_id']=='FM0190');gpt=json.loads((R/'qa/field_geometry002_gpt190.json').read_text('utf8'))
p=np.asarray(Image.open(v['output']).convert('RGBA'));g=np.asarray(Image.open(gpt['resized_output']).convert('RGBA'));s=Image.open(v['source']).convert('RGBA');assert sha(v['output'])==v['output_sha256'];assert sha(gpt['resized_output'])==gpt['resized_output_sha256']
rects=[[0,0,64,12],[0,46,64,57],[0,91,64,103],[0,124,64,128]];protected=[[28,46,29,47],[60,46,61,47],[28,91,29,92],[60,91,61,92]];mask=np.zeros(p.shape[:2],bool)
for a,b,c,d in rects:mask[b*8:d*8,a*8:c*8]=True
for a,b,c,d in protected:mask[b*8:d*8,a*8:c*8]=False
mp=O/'FM0190-masonry-interior-mask.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
grain=g[:,:,:3].astype('float32')-gaussian_filter(g[:,:,:3].astype('float32'),(6,6,0),mode='nearest');files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for strength,limit in [(.45,8),(.75,12)]:
 out=p.copy();material=np.rint(np.clip(p[:,:,:3].astype('float32')+np.clip(grain*strength,-limit,limit),0,255)).astype('uint8');out[:,:,:3][mask]=material[mask];assert np.array_equal(out[~mask],p[~mask]);assert np.all(out[:,:,3]==255)
 tag=f'{int(strength*100):02d}';op=O/f'FM0190-fixed-geometry-gpt-masonry{tag}-8x.png';Image.fromarray(out,'RGBA').save(op)
 files.append({'id':f'FM0190-fixed-geometry-gpt-masonry{tag}','group_id':'FM0190','source':v['source'],'source_ptm':v['source_ptm'],'source_ptm_sha256':v['source_ptm_sha256'],'source_rgba_sha256':v['source_rgba_sha256'],'parent':v['output'],'parent_sha256':v['output_sha256'],'generated_material':gpt['resized_output'],'generated_material_sha256':gpt['resized_output_sha256'],'generated_report':'qa/field_geometry002_gpt190.json','generated_report_sha256':sha(R/'qa/field_geometry002_gpt190.json'),'mask':str(mp),'mask_sha256':sha(mp),'output':str(op),'output_sha256':sha(op),'masonry_rectangles':rects,'protected_corner_rectangles':protected,'grain_sigma_output':6,'grain_strength':strength,'grain_RGB_bound':limit,'outside_mask_parent_rgba_exact':True,'new_local_passes':0,'new_external_calls':0,'method':'Existing GPT masonry high-frequency material only, clipped inside existing source-fixed cornice planes. Glass, brick piers and dark corner strips unchanged fromv4.','visual_review':'pending','runtime_verified':False,'release_eligible':False})
 for kind,box in [('whole',(0,0,64,128)),('joint',(23,40,40,59)),('lower',(0,88,64,128))]:
  w=(box[2]-box[0])*8;h=(box[3]-box[1])*8;cw=max(w+16,280);canvas=Image.new('RGB',(cw*3,h+42),'#26333f');d=ImageDraw.Draw(canvas)
  ims=[s.crop(box).resize((w,h),Image.Resampling.NEAREST),Image.fromarray(p,'RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out,'RGBA').crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','구조 고정 · v4','구조 유지 · 석재 질감 '+tag])):d.text((j*cw+6,5),title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*cw+6,36))
  path=V/f'FM0190-{kind}-masonry{tag}.png';canvas.save(path);pages.append({'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-constrained-masonry-material/v1','previous_goal_turn_classification':'progress: FIELD-GEOMETRY-002 verified9 derivatives and resolvedFM0189;FM0190 remains held with a rejected whole GPT repaint.','files':files,'pages':pages,'new_local_passes':0,'new_external_calls':0,'limits':['Uses an already externally generated image; it is not an all-local result or a new AI call.','High-frequency subtraction does not establish that every grain feature is faithful; final visual quality remains a separate gate.','Geometry and source corner shading are inherited fromv4; no new consumer/UV/runtime proof.'],'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print('Prepared2 masonry variants,6 comparison pages; no new inference.')
