"""Fixed facade plane boundaries with local cross-section material, no source blur."""
import hashlib,json
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry002';V=R/'outputs/field-geometry002';Q=R/'qa/field_geometry002_planes_v3.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
one=json.loads((R/'qa/field_geometry002_trials.json').read_text('utf8'));two=json.loads((R/'qa/field_geometry002_rectification.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in one['files']:
 gid=v['group_id'];m=next(z for z in two['files'] if z['group_id']==gid);src=Image.open(v['source']).convert('RGBA');original=np.asarray(Image.open(v['parent']).convert('RGBA'));local=np.asarray(Image.open(m['output']).convert('RGBA'));out=local.copy();profiles={};records=[]
 grain=local[:,:,:3].astype(np.float32)-gaussian_filter(local[:,:,:3].astype(np.float32),(4,4,0),mode='nearest')
 for i,z in enumerate(v['regions'],1):
  x0,y0,x1,y1=z['box'];a,b,c,d=[t*8 for t in z['box']];patch=local[b:d,a:c,:3].astype(np.float32);kind=z['kind'];record={'name':z['name'],'kind':kind,'box':z['box']}
  if kind=='horizontal':
   low,high=z.get('profile_sample_x',[x0,x1]);samples=local[b:d,low*8:high*8,:3].astype(np.float32)
   profile=np.median(samples,axis=1);material=np.broadcast_to(profile[:,None,:],patch.shape).copy();profiles[f'profile_{i}']=profile
   strength=3 if gid=='FM0189' else 6;material+=np.clip(grain[b:d,a:c]*.65,-strength,strength);record.update(profile_axis='horizontal',grain_strength=strength,grain_gain=.65,profile_key=f'profile_{i}')
  elif kind=='vertical':
   samples=patch[16:-16] if d-b>40 else patch
   profile=np.median(samples,axis=0);material=np.broadcast_to(profile[None,:,:],patch.shape).copy();profiles[f'profile_{i}']=profile
   strength=2 if gid=='FM0189' else 4;material+=np.clip(grain[b:d,a:c]*.6,-strength,strength);record.update(profile_axis='vertical',grain_strength=strength,grain_gain=.6,profile_key=f'profile_{i}')
  elif kind=='glass':
   pad=4;inner=patch[pad:-pad,pad:-pad];material=cv2.copyMakeBorder(inner,pad,pad,pad,pad,cv2.BORDER_REFLECT_101)
   material=np.minimum(material,z['glass_ceiling']);record.update(edge_extension_output_px=pad,edge_method='BORDER_REFLECT_101',glass_ceiling=z['glass_ceiling'])
  elif kind=='shutter':
   profile=np.median(patch,axis=1);columns=np.median(patch,axis=0);gain=columns/np.maximum(columns.mean(axis=0),1);gain=cv2.GaussianBlur(gain[None,:,:],(0,0),sigmaX=6,sigmaY=0)[0]
   material=profile[:,None,:]*gain[None,:,:];material+=np.clip(grain[b:d,a:c]*.5,-2,2);profiles[f'profile_{i}']=profile;profiles[f'gain_{i}']=gain;record.update(profile_key=f'profile_{i}',gain_key=f'gain_{i}',grain_gain=.5,grain_strength=2)
  else:
   # Keep local pier material while fixed plane bounds stop curved aperture intrusion.
   material=patch.copy();record['material']='existing rectified local RGB at same coordinates'
  out[b:d,a:c,:3]=np.rint(np.clip(material,0,255)).astype('uint8');records.append(record)
 assert np.all(out[:,:,3]==255)
 pf=O/f'{gid}-material-profiles-v3.npz';np.savez_compressed(pf,**profiles)
 op=O/f'{gid}-fixed-planes-local-profiles-v3-8x.png';Image.fromarray(out,'RGBA').save(op)
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','parent_id','region_classmap','region_classmap_sha256','vector','vector_sha256']},'id':gid+'-fixed-planes-local-profiles-v3','material_parent':m['output'],'material_parent_sha256':m['output_sha256'],'output':str(op),'output_sha256':sha(op),'profiles':str(pf),'profiles_sha256':sha(pf),'regions':records,'method':'Fixed source-plane partition fromv1 with existing local median cross-section profiles fromv2, bounded grain and half-source-pixel reflected glass-edge material.','new_local_passes':0,'external_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 for kind,box in [('whole',(0,0,64,128)),('upper',(0,0,64,57)),('lower',(0,88,64,128))]:
  cw=(box[2]-box[0])*8;ch=(box[3]-box[1])*8;canvas=Image.new('RGB',((cw+16)*3,ch+42),'#26333f');d=ImageDraw.Draw(canvas)
  ims=[src.crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.fromarray(original,'RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out,'RGBA').crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬 · 보류','구조 고정 · 로컬 재질 v3'])):d.text((j*(cw+16)+6,5),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*(cw+16)+6,36))
  path=V/f'{gid}-{kind}-v3.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-facade-plane-local-material/v3','basis':'v2 retained good local material but local-gradient warps alone left rounded corners, header waviness and new seams where X warp started/ended. v3 uses fixed source rectangles and local sharp cross-section material rather than source low-resolution color profiles.','files':files,'pages':pages,'new_local_passes':0,'external_calls':0,'limits':['Profiles constrain major line placement; limited local grain does not prove all visible contours are geometrically perfect.','Glass edge half-source-pixel reflection is material extension, not recovered detail.','Source-coordinate planes and appearance still require direct review, exact recipe checks and eventual runtime/UV proof.'],'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':2,'pages':6}))
