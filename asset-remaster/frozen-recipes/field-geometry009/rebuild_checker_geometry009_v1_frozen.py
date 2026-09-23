"""Source-owned cells; clipped parent material inside each independently mapped cell."""
from pathlib import Path
import json,hashlib,copy,shutil
import numpy as np,cv2
from scipy.ndimage import gaussian_filter,distance_transform_edt
from PIL import Image,ImageDraw,ImageFont

def build(s,p,patches,coord_scale=1):
 h,w=s.shape[:2];H,W=p.shape[:2];yy,xx=np.mgrid[0:H,0:W].astype('float32');x=(xx+.5)/8;y=(yy+.5)/8;src=s[:,:,:3].astype('float32');parent=p[:,:,:3].astype('float32');out=parent.copy();union=np.zeros((H,W),np.float32);records=[];maps={};vectors=[]
 for i,z in enumerate(patches):
  poly=np.array(z['poly'])*coord_scale;center=np.array(z['center'])*coord_scale;par=np.array(z['source_lattice_parameters']);M=par[:4].reshape(2,2)/coord_scale;inverse=np.linalg.inv(M);phase=par[4:];u=M[0,0]*(x-center[0])+M[0,1]*(y-center[1])+phase[0];v=M[1,0]*(x-center[0])+M[1,1]*(y-center[1])+phase[1];cu=np.floor(u+.5);cv=np.floor(v+.5)
  # Map each output cell into its source interior to remove neural bevel rims.
  margin=.09 if coord_scale==1 else .08;localu=(u-cu)*(1-2*margin);localv=(v-cv)*(1-2*margin);qu=cu+localu-phase[0];qv=cv+localv-phase[1];sx=inverse[0,0]*qu+inverse[0,1]*qv+center[0];sy=inverse[1,0]*qu+inverse[1,1]*qv+center[1]
  sourcecolor=cv2.remap(src,(sx-.5).astype('float32'),(sy-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
  # Restrained local fine detail; no local-generated cell outline or relief.
  high=parent-gaussian_filter(parent,(2.4,2.4,0),mode='nearest');grain=cv2.remap(high,(sx*8-.5).astype('float32'),(sy*8-.5).astype('float32'),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE);grain=np.clip(grain*.4,-2,2)
  target=sourcecolor+grain;mask=np.zeros((H,W),np.uint8);cv2.fillPoly(mask,[np.rint(poly*8*16).astype('int32')],1,shift=4);distance=distance_transform_edt(mask)/8;weight=np.clip(distance/(2.0*coord_scale),0,1).astype('float32')
  out=out*(1-weight[:,:,None])+target*weight[:,:,None];union=np.maximum(union,weight);maps[z['name']+'-mapx']=sx;maps[z['name']+'-mapy']=sy;maps[z['name']+'-weight']=weight
  ids=np.stack([cu.astype('int16'),cv.astype('int16')],2);valid=weight>.5;cellids=np.unique(ids[valid],axis=0);polygons=[]
  for aa,bb in cellids:
   uv=np.array([[aa-.5,bb-.5],[aa+.5,bb-.5],[aa+.5,bb+.5],[aa-.5,bb+.5]]);points=(uv-phase)@inverse.T+center;polygons.append({'cell':[int(aa),int(bb)],'source_quad':points.tolist(),'core_output_pixels':int(((cu==aa)&(cv==bb)&(weight==1)).sum())})
  records.append({'name':z['name'],'source_clip_polygon':poly.tolist(),'source_center':center.tolist(),'lattice_matrix':M.tolist(),'lattice_phase':phase.tolist(),'interior_margin_fraction':margin,'clip_feather_source':2.0*coord_scale,'material_grain_RGB_bound':2,'cells':polygons,'interpretation':'Cell list is the intersection with an authored treatment polygon, not an assertion that every whole cell survives source damage.'});vectors.append((z['name'],poly,polygons))
 assert np.isfinite(out).all();result=np.dstack([np.rint(np.clip(out,0,255)).astype('uint8'),s[:,:,3].repeat(8,0).repeat(8,1)]);assert np.array_equal(result[union==0],p[union==0]);return result,union,maps,records,vectors

def main():
 R=Path(__file__).resolve().parents[1];O=R/'workspace/local-sr/field-geometry009';P=R/'outputs/field-geometry009';Q=R/'qa/field_geometry009_reconstruction_v1.json';assert not Q.exists()
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 audit=json.loads((R/'qa/field_geometry009_lattice_audit.json').read_text('utf8'));sources=json.loads((R/'qa/field_geometry008_source_audit.json').read_text('utf8'))['files'];parents=json.loads((R/'qa/field_geometry008_local.json').read_text('utf8'))['files'];font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);files=[];pages=[]
 for gid in ['FM0394','FM0430','FM0444']:
  sv=next(v for v in sources if v['group_id']==gid);pv=next(v for v in parents if v['id']==gid+'-wdn');z=next(v for v in audit['source_records'] if v['group_id']==('FM0430' if gid=='FM0444' else gid));s=np.asarray(Image.open(sv['source']).convert('RGBA'));p=np.asarray(Image.open(pv['output']).convert('RGBA'));out,weight,maps,records,vectors=build(s,p,z['patches'],.5 if gid=='FM0444' else 1)
  op=O/(gid+'-source-cells-v1-8x.png');Image.fromarray(out).save(op);npth=O/(gid+'-source-cells-v1-maps.npz');np.savez_compressed(npth,union=weight,**maps);mp=O/(gid+'-source-cells-v1-mask.png');Image.fromarray(np.rint(weight*255).astype('uint8')).save(mp)
  svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{out.shape[1]}" height="{out.shape[0]}" viewBox="0 0 {s.shape[1]} {s.shape[0]}">']
  for name,poly,cells in vectors:
   points=' '.join(f'{x},{y}' for x,y in poly);svg.append(f'<defs><clipPath id="{name}"><polygon points="{points}"/></clipPath></defs><g clip-path="url(#{name})">')
   for cell in cells:
    pts=' '.join(f'{x},{y}' for x,y in cell['source_quad']);color='white' if sum(cell['cell'])%2==0 else 'black';svg.append(f'<polygon points="{pts}" fill="{color}"/>')
   svg.append('</g>')
  svg.append('</svg>');vp=O/(gid+'-source-cells-v1.svg');vp.write_text(''.join(svg),'utf8')
  source_scale=np.asarray(Image.fromarray(out).resize((s.shape[1],s.shape[0]),Image.Resampling.LANCZOS));files.append({**{k:sv[k] for k in ['group_id','source','source_ptm','source_ptm_sha256','source_rgba_sha256']},'id':gid+'-source-cells-v1','parent':pv['output'],'parent_sha256':pv['output_sha256'],'output':str(op),'output_sha256':sha(op),'mask':str(mp),'mask_sha256':sha(mp),'maps':str(npth),'maps_sha256':sha(npth),'vector':str(vp),'vector_sha256':sha(vp),'coordinate_scale':.5 if gid=='FM0444' else 1,'lattice_source_group':z['group_id'],'recipe':records,'source_scale_RGB_MAE':float(np.abs(source_scale[:,:,:3].astype(float)-s[:,:,:3]).mean()),'method':'Source-fitted affine checker cells, cell-interior source RGB with bounded reused local grain, polygon-clipped treatment; parent WDN outside. No new local/GPT inference.','runtime_verified':False,'release_eligible':False})
  boxes=[('whole',None),('checker',(38,35,78,75))] if gid=='FM0394' else [('whole',None),('middle',(48,63,76,107)),('upper',(96,8,128,40))] if gid=='FM0430' else [('whole',None),('middle',(24,31,40,55))]
  for tag,box in boxes:
   can=Image.new('RGB',(1050,420),'#25313c');d=ImageDraw.Draw(can)
   for col,(a,title) in enumerate([(s,'원본 · 단순 확대'),(p,'로컬 WDN'),(out,'원본 체크 경계 재구성 v1')]):
    im=Image.fromarray(a)
    if box:im=im.crop(box if col==0 else tuple(t*8 for t in box));scale=min(320/im.width,352/im.height)
    else:scale=min(320/im.width,352/im.height)
    pic=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if col==0 else Image.Resampling.LANCZOS);d.text((col*350+8,8),gid+' '+title,font=font,fill='white');can.paste(pic.convert('RGB'),(col*350+(350-pic.width)//2,50+(352-pic.height)//2))
   pp=P/(gid+'-source-cells-v1-'+tag+'.png');can.save(pp);pages.append({'path':str(pp),'sha256':sha(pp),'group_id':gid,'source_box':box,'review_status':'pending'})
 program=O/'rebuild_checker_geometry009_v1_frozen.py';shutil.copy2(__file__,program);report={'schema':'brs-checker-reconstruction009/v1','lattice_audit_sha256':sha(R/'qa/field_geometry009_lattice_audit.json'),'source_scale_reuse_limit':'FM0444 uses half-sized430 geometry only as a visual registration hypothesis. It does not establish equivalent game consumers, and requires separate source review.','files':files,'pages':pages,'reconstruction_program':str(program),'reconstruction_program_sha256':sha(program),'new_neural_passes':0,'new_external_calls':0,'runtime_verified':False,'release_eligible':False};Q.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print('Three checker geometry trials and7 comparison pages saved.')
if __name__=='__main__':main()
