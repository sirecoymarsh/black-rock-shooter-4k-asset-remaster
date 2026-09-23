"""Restore source gray/shadow bevel strips that local profiles turned into bright frame."""
import hashlib,json
from pathlib import Path
import numpy as np,cv2
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry002';V=R/'outputs/field-geometry002';Q=R/'qa/field_geometry002_bevels_v4.json';assert not Q.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((R/'qa/field_geometry002_planes_v3.json').read_text('utf8'));files=[];pages=[];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
for v in old['files']:
 gid=v['group_id'];src=Image.open(v['source']).convert('RGBA');s=np.asarray(src);p=np.asarray(Image.open(v['output']).convert('RGBA'));out=p.copy();mask=np.zeros(p.shape[:2],bool);records=[]
 if gid=='FM0189':boxes=[(3,0,4,128),(60,0,62,128),(31,9,32,43),(31,54,32,88)]
 else:boxes=[(28,12,29,47),(60,12,61,47),(28,57,29,92),(60,57,61,92)]
 grain=p[:,:,:3].astype('float32')-gaussian_filter(p[:,:,:3].astype('float32'),(4,4,0),mode='nearest')
 for x0,y0,x1,y1 in boxes:
  a,b,c,d=[t*8 for t in [x0,y0,x1,y1]];source=s[y0:y1,x0:x1,:3].astype('float32');material=np.empty((d-b,c-a,3),np.float32)
  # Each source column remains a separate straight bevel plane; interpolate shading along its height only.
  for x in range(x1-x0):
   profile=source[:,x,:];height=cv2.resize(profile[:,None,:],(1,d-b),interpolation=cv2.INTER_LINEAR)
   material[:,x*8:(x+1)*8,:]=height
  result=np.rint(np.clip(material+np.clip(grain[b:d,a:c]*.4,-2,2),0,255)).astype('uint8');out[b:d,a:c,:3]=result;mask[b:d,a:c]=True
  records.append({'box':[x0,y0,x1,y1],'source_rgb_columns':source.tolist(),'shade_interpolation':'vertical linear only, independent source columns','grain_sigma_output':4,'grain_gain':.4,'grain_bound':2})
 assert np.array_equal(out[~mask],p[~mask]);assert np.all(out[:,:,3]==255)
 op=O/f'{gid}-fixed-planes-source-bevels-v4-8x.png';Image.fromarray(out,'RGBA').save(op);mp=O/f'{gid}-source-bevel-mask-v4.png';Image.fromarray(mask.astype('uint8')*255).save(mp)
 files.append({**{k:v[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256','parent','parent_sha256','parent_id','region_classmap','region_classmap_sha256','vector','vector_sha256']},'id':gid+'-fixed-planes-source-bevels-v4','geometry_parent':v['output'],'geometry_parent_sha256':v['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'bevels':records,'outside_bevel_parent_rgba_exact':True,'method':'v3 source-plane/local-material result with source-gray bevel columns restored; existing white frame width is no longer doubled by the gray side face.','new_local_passes':0,'external_calls':0,'visual_review':'pending','runtime_verified':False,'release_eligible':False})
 for kind,box in [('whole',(0,0,64,128)),('upper',(0,0,64,57)),('lower',(0,88,64,128))]:
  cw=(box[2]-box[0])*8;ch=(box[3]-box[1])*8;canvas=Image.new('RGB',((cw+16)*3,ch+42),'#26333f');d=ImageDraw.Draw(canvas)
  ims=[src.crop(box).resize((cw,ch),Image.Resampling.NEAREST),Image.open(v['parent']).convert('RGBA').crop(tuple(t*8 for t in box)),Image.fromarray(out,'RGBA').crop(tuple(t*8 for t in box))]
  for j,(im,title) in enumerate(zip(ims,['원본 · 단순 확대','기존 로컬 · 보류','직선·직각·창틀 폭 보정'])):d.text((j*(cw+16)+6,5),gid+' '+title,font=font,fill='white');canvas.paste(im.convert('RGB'),(j*(cw+16)+6,36))
  path=V/f'{gid}-{kind}-v4.png';canvas.save(path);pages.append({'group_id':gid,'path':str(path),'sha256':sha(path),'source_box':box,'review_status':'pending'})
Q.write_text(json.dumps({'schema':'brs-facade-bevel-restoration/v4','basis':'v3 FM0189 gray side face atsource x31 had median RGB near250 rather than source129/130/128; this doubled the apparent white frame width. Right shadow x61 was also too bright. Source bevel planes are restored; FM0190 right glass bevel columns28/60 likewise restored.','files':files,'pages':pages,'new_local_passes':0,'external_calls':0,'limits':['Bevel strips use vertically interpolated source shading with existing local grain bounded to2 RGB; this is direct geometry/shading reconstruction, not newly recovered high-resolution detail.','Original source color byte equality is not claimed between texel centers. Existing material/color interpretation elsewhere remains as documented in v3.','No consumer/UV/runtime or deployment proof.'],'runtime_verified':False,'release_eligible':False},ensure_ascii=False,indent=2),'utf8');print(json.dumps({'outputs':2,'pages':6}))
